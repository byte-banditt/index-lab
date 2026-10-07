"""Frozen current-position historical replay and historical-beta shock estimates."""

import numpy as np
import pandas as pd


def betas(panel, bench, cfg):
    r = panel.pct_change(fill_method=None).reindex(bench.index).iloc[1:]
    b = bench.return_.iloc[1:]

    def estimate(stock):
        pairs = pd.concat([stock, b], axis=1).dropna()
        variance = pairs.iloc[:, 1].var(ddof=1)
        if len(pairs) < 2 or not np.isfinite(variance) or variance <= 0:
            raise ValueError("Benchmark paired variance must be positive")
        return pairs.iloc[:, 0].cov(pairs.iloc[:, 1]) / variance

    output = r.apply(estimate)
    output.attrs["benchmark"] = bench.attrs.get("label", cfg["benchmark"])
    return output


def composition(result, sectors, beta, panel):
    day = result.weights.index[-1]
    w = result.weights.loc[day]
    r = panel.pct_change(fill_method=None).loc[day]
    w = w * (1 + r) / (1 + (w * r).sum())
    stocks = pd.DataFrame(
        {
            "symbol": w.index,
            "weight": w.values,
            "sector": [sectors[s] for s in w.index],
            "beta": beta.reindex(w.index).values,
        }
    )
    stocks["index"] = result.name
    stocks["beta_benchmark"] = beta.attrs.get("benchmark", "unverified")
    sector = stocks.groupby("sector").weight.sum().reset_index()
    sector["index"] = result.name
    stats = pd.DataFrame(
        [
            dict(
                index=result.name,
                asof=day,
                top3=w.nlargest(3).sum(),
                HHI=(w * w).sum(),
                beta=(w * beta).sum(),
            )
        ]
    )
    return stocks, sector, stats


def historical(panel, result, cfg):
    r = panel.pct_change(fill_method=None).reindex(result.weights.index)
    proxy = r.mean(axis=1)
    if r.index.min() <= pd.Timestamp("2020-02-01") and r.index.max() >= pd.Timestamp("2020-03-31"):
        windows = [("2020_Feb_Mar", r.loc["2020-02-01":"2020-03-31"])]
    else:
        worst = (1 + proxy).rolling(20).apply(np.prod, raw=True) - 1
        candidates = worst.dropna().sort_values()
        selected = []
        for day in candidates.index:
            pos = r.index.get_loc(day)
            if all(abs(pos - other) >= 20 for other in selected):
                selected.append(pos)
            if len(selected) == 3:
                break
        windows = [(f"worst20_{j + 1}", r.iloc[i - 19 : i + 1]) for j, i in enumerate(selected)]
    rows = []
    for label, window in windows:
        # Use the beginning weights actually held on every historical session.
        held_returns = (window * result.weights.reindex(window.index)).sum(axis=1)
        level = (1 + held_returns).cumprod()
        with_base = pd.concat([pd.Series([1.0]), level.reset_index(drop=True)], ignore_index=True)
        daily = with_base.pct_change().iloc[1:]
        rows.append(
            dict(
                index=result.name,
                exposure="actual historical daily weights; gross",
                scenario=label,
                start=window.index.min(),
                end=window.index.max(),
                pnl=level.iloc[-1] - 1,
                max_drawdown=(with_base / with_base.cummax() - 1).min(),
                worst_day=daily.min(),
            )
        )
    return pd.DataFrame(rows)


def hypothetical(stocks):
    rows = []
    for shock in [-0.05, -0.10, -0.20]:
        rows.append(
            dict(
                index=stocks["index"].iloc[0],
                scenario=f"market_{shock:.0%}",
                pnl=(stocks.weight * stocks.beta * shock).sum(),
            )
        )
    for sector in stocks.sector.unique():
        rows.append(
            dict(
                index=stocks["index"].iloc[0],
                scenario=f"{sector}_-15%",
                pnl=-0.15 * stocks.loc[stocks.sector == sector, "weight"].sum(),
            )
        )
    return pd.DataFrame(rows)
