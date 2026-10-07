"""Paired active-return bootstrap, disclosure grids and linked drawdown decomposition."""

import json
import subprocess
from copy import deepcopy
from itertools import product

import numpy as np
import pandas as pd

from .data import ROOT, output_root
from .index_engine import build, metrics


def block_bootstrap(active, cfg):
    active = active.dropna().to_numpy()
    settings = cfg["robustness"]
    n, block = len(active), settings["block_days"]
    if n < block or not np.isfinite(active).all():
        raise ValueError("Insufficient finite paired active returns for bootstrap")
    rng = np.random.default_rng(cfg["seed"])
    starts = rng.integers(0, n, (settings["resamples"], int(np.ceil(n / block))))
    indices = ((starts[:, :, None] + np.arange(block)) % n).reshape(len(starts), -1)[:, :n]
    draws = active[indices].mean(axis=1) * cfg["annual_sessions"]
    lower, upper = np.quantile(draws, [0.025, 0.975])
    return dict(
        mean_annual_active=active.mean() * cfg["annual_sessions"],
        bootstrap_mean=draws.mean(),
        ci_lower=lower,
        ci_upper=upper,
        contains_zero=bool(lower <= 0 <= upper),
        observations=n,
        resamples=len(draws),
        block_days=block,
    )


def defaults_history(cfg):
    path = "index_lab/config.yaml"
    command = ["git", "log", "--reverse", "--format=%H", "--", path]
    try:
        revisions = subprocess.check_output(command, cwd=ROOT.parent, text=True).splitlines()
        rows = []
        current = [
            cfg["indices"]["MOM10"]["n"],
            cfg["indices"]["LVOL10"]["n"],
            cfg["momentum_months"],
            cfg["vol_days"],
            cfg["cost_bps"],
        ]
        for revision in revisions:
            text = subprocess.check_output(
                ["git", "show", f"{revision}:{path}"], cwd=ROOT.parent, text=True
            )
            c = json.loads(text)
            values = [
                c["indices"]["MOM10"]["n"],
                c["indices"]["LVOL10"]["n"],
                c["momentum_months"],
                c["vol_days"],
                c["cost_bps"],
            ]
            rows.append(
                dict(
                    revision=revision,
                    MOM_n=values[0],
                    LVOL_n=values[1],
                    momentum_months=values[2],
                    vol_days=values[3],
                    cost_bps=values[4],
                    matches_current=values == current,
                )
            )
        if not rows:
            raise ValueError("No committed config history")
        return pd.DataFrame(rows)
    except (subprocess.SubprocessError, ValueError, KeyError) as exc:
        return pd.DataFrame([dict(status=f"NOT DONE: default history verification: {exc}")])


def sensitivity(panel, bench, cfg):
    s = cfg["robustness"]
    rows, cache = [], {}
    for n, months, vol_days, cost in product(
        s["top_n"], s["momentum_months"], s["vol_days"], s["cost_bps"]
    ):
        for name in ("MOM10", "LVOL10"):
            key = (name, n, months, vol_days if name == "LVOL10" else None)
            if key not in cache:
                c = deepcopy(cfg)
                c["indices"][name]["n"] = n
                c["momentum_months"], c["vol_days"], c["cost_bps"] = months, vol_days, 0
                cache[key] = build(panel, name, c)
            r = cache[key]
            costs = pd.Series(0.0, index=r.levels.index)
            events = r.turnover.set_index("effective_date").turnover
            costs.loc[events.index] = events * cost / 10000
            net = (1 - costs) * (1 + r.levels.gross_return) - 1
            levels = pd.DataFrame(
                {"return_": net, "level": cfg["base_level"] * (1 + net).cumprod()}
            )
            levels = levels.loc[bench.index.min() :]
            rows.append(
                dict(
                    index=name,
                    top_n=n,
                    momentum_months=months,
                    vol_days=vol_days,
                    cost_bps=cost,
                    start=levels.index[0],
                    end=levels.index[-1],
                    **metrics(levels, bench.return_, cfg),
                )
            )
    return pd.DataFrame(rows)


def drawdown(result, sectors, bench):
    levels = result.levels.level
    depths = levels / levels.cummax() - 1
    trough = depths.idxmin()
    peak = levels.loc[:trough].idxmax()
    dates = levels.index[(levels.index > peak) & (levels.index <= trough)]
    net = result.levels.loc[dates, "return_"]
    wealth = (1 + net).cumprod().shift(fill_value=1)
    costs = result.levels.loc[dates, "cost"]
    linked = result.contributions.loc[dates].mul((1 - costs) * wealth, axis=0).sum()
    constituents = linked.rename("contribution").rename_axis("symbol").reset_index()
    constituents["sector"] = constituents.symbol.map(sectors)
    constituents["index"] = result.name
    constituents["rank"] = constituents.contribution.rank(method="first")
    sector = constituents.groupby("sector").contribution.sum().reset_index()
    sector["index"] = result.name
    cost_effect = -(costs * wealth).sum()
    benchmark_window = (
        bench.level.reindex([peak, trough]).iloc[-1] / bench.level.reindex([peak, trough]).iloc[0]
        - 1
    )
    valid_benchmark = bench.level.dropna()
    benchmark_depths = valid_benchmark / valid_benchmark.cummax() - 1
    benchmark_trough = benchmark_depths.idxmin()
    benchmark_peak = valid_benchmark.loc[:benchmark_trough].idxmax()
    benchmark_dd = benchmark_depths.loc[benchmark_trough]
    summary = dict(
        index=result.name,
        peak=peak,
        trough=trough,
        drawdown=depths.loc[trough],
        cost_effect=cost_effect,
        stock_effect=linked.sum(),
        benchmark_same_window=benchmark_window,
        benchmark_max_drawdown=benchmark_dd,
        benchmark_peak=benchmark_peak,
        benchmark_trough=benchmark_trough,
        active_in_drawdown_window=depths.loc[trough] - benchmark_window,
        stock_vs_benchmark_window=linked.sum() - benchmark_window,
    )
    if not np.isclose(linked.sum() + cost_effect, summary["drawdown"], atol=1e-12):
        raise ValueError("Drawdown contribution reconciliation failed")
    return summary, constituents.sort_values("contribution"), sector.sort_values("contribution")


def artifacts(results, panels, bench, cfg, sectors):
    boot, summaries, stocks, groups, prose = [], [], [], [], []
    for name, result in results.items():
        for mode, col in [("gross", "gross_return"), ("net", "return_")]:
            active = result.levels[col].iloc[1:] - bench.return_.reindex(result.levels.index[1:])
            boot.append(
                dict(
                    index=name,
                    mode=mode,
                    benchmark=bench.attrs["label"],
                    **block_bootstrap(active, cfg),
                )
            )
        mapping = sectors if name != "MULTI" else {s: s for s in panels[name]}
        summary, constituents, sector = drawdown(result, mapping, bench)
        summaries.append(summary)
        stocks.append(constituents)
        groups.append(sector)
        worst = constituents.iloc[0]
        sector_worst = sector.iloc[0]
        prose.append(
            f"{name}: worst net drawdown {summary['drawdown']:.4%} from "
            f"{summary['peak'].date()} to {summary['trough'].date()}. "
            f"Largest detractor {worst.symbol} contributed {worst.contribution:.4%}; "
            f"largest sector/sleeve detractor {sector_worst.sector} contributed "
            f"{sector_worst.contribution:.4%}. Costs contributed {summary['cost_effect']:.4%}. "
            f"Benchmark return in this window was {summary['benchmark_same_window']:.4%}; "
            f"its independent maximum drawdown was {summary['benchmark_max_drawdown']:.4%} "
            f"over {summary['benchmark_peak'].date()} to {summary['benchmark_trough'].date()}. "
            f"Same-window active return {summary['active_in_drawdown_window']:.4%} equals "
            f"linked stock/sleeve effect less benchmark return "
            f"{summary['stock_vs_benchmark_window']:.4%} plus cost effect "
            f"{summary['cost_effect']:.4%}. "
            "These are holdings/cost decompositions and windows with distinct endpoints; "
            "they do not establish a causal market narrative."
        )
    pd.DataFrame(boot).to_csv(output_root() / "reports/bootstrap.csv", index=False)
    pd.DataFrame(summaries).to_csv(output_root() / "reports/drawdown.csv", index=False)
    all_stocks = pd.concat(stocks)
    all_stocks.to_csv(output_root() / "reports/drawdown_constituents.csv", index=False)
    all_stocks.groupby("index").head(5).to_csv(
        output_root() / "reports/drawdown_top5.csv", index=False
    )
    pd.concat(groups).to_csv(output_root() / "reports/drawdown_sectors.csv", index=False)
    grid = sensitivity(panels["MOM10"], bench, cfg)
    grid.to_csv(output_root() / "reports/parameter_sensitivity.csv", index=False)
    defaults_history(cfg).to_csv(output_root() / "reports/default_history.csv", index=False)
    (output_root() / "docs/drawdown_commentary.md").write_text("\n\n".join(prose) + "\n")
    return grid
