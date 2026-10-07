"""Rebuild artifacts from existing SQLite; no network calls."""

import argparse
import shutil
import tempfile
from pathlib import Path

from indexkit.atomic import publish
from indexkit.data import ROOT, config, load, output_location, output_root, prices, quality
from indexkit.index_engine import benchmark, build, modification_demo


def run(fast=True, cfg=None, output_dir=None):
    cfg = config() if cfg is None else dict(cfg)
    destination = Path(output_dir or cfg.get("output_dir") or output_root()).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    # Same filesystem: completed snapshots can be renamed into place.
    with tempfile.TemporaryDirectory(prefix=".build-", dir=destination) as temporary:
        stage = Path(temporary)
        (stage / "docs").mkdir()
        generated = {
            "data_inventory.md",
            "index_methodology.md",
            "index_launch_form.md",
            "commentary.md",
            "index_change_note_example.md",
            "index_change_note_template.md",
            "validation_autocall.md",
            "drawdown_commentary.md",
            "monitor_review.md",
        }
        existing_docs = destination / "docs"
        if existing_docs.exists():
            for source in existing_docs.iterdir():
                if source.is_file() and source.name not in generated:
                    shutil.copy2(source, stage / "docs" / source.name)
        for name in ("rebalance_runbook.md", "equity_derivs_flow_primer.md"):
            source = ROOT / "docs" / name
            if source.exists() and not (stage / "docs" / name).exists():
                shutil.copy2(source, stage / "docs" / name)
        with output_location(stage):
            result = _run(fast, cfg)
        publish(stage, destination)
    return result


def _run(fast, cfg):
    cfg["fast"] = fast
    (output_root() / "reports").mkdir(parents=True, exist_ok=True)
    (output_root() / "docs").mkdir(parents=True, exist_ok=True)
    if fast:
        for stale in ["autocallable.csv", "autocall_probabilities.csv", "autocall_delta.png"]:
            (output_root() / "reports" / stale).unlink(missing_ok=True)
    frame, audit = load(cfg)
    cfg["source_start"] = str(frame.date.min().date())
    cfg["source_end"] = str(frame.date.max().date())
    print(audit)
    (output_root() / "docs" / "data_inventory.md").write_text(
        "# Actual mdq inventory\n```\n" + audit + "\n```\n"
    )
    if cfg.get("start"):
        frame = frame[frame.date >= cfg["start"]]
    if cfg.get("end"):
        frame = frame[frame.date <= cfg["end"]]
    quality(frame, cfg).to_csv(output_root() / "reports" / "source_dq.csv", index=False)
    panel = prices(frame, cfg)
    results = {
        name: build(panel, name, cfg)
        for name, rule in cfg["indices"].items()
        if rule["rule"] != "multi_asset"
    }
    panels = {name: panel for name in results}
    fill_flags = None
    cfg["not_done"] = []
    if "MULTI" in cfg["indices"]:
        from indexkit.multi_asset import sleeves

        try:
            multi_panel, fill_flags = sleeves(frame, panel, cfg)
            results["MULTI"] = build(multi_panel, "MULTI", cfg)
            panels["MULTI"] = multi_panel
        except ValueError as exc:
            cfg["not_done"].append(f"NOT DONE: MULTI real-data calculation: {exc}")
            print(cfg["not_done"][-1])
    for name, result in results.items():
        for attr in ("levels", "weights", "turnover", "changes", "contributions"):
            getattr(result, attr).to_csv(
                output_root() / "reports" / f"{name}_{attr}.csv",
                index=attr not in ("turnover", "changes"),
            )
        if name == "MULTI":
            continue
        modification_demo(panel, name, cfg).to_csv(
            output_root() / "reports" / f"{name}_modifications.csv", index=False
        )
    dates = next(iter(results.values())).levels.index
    bench = benchmark(panel, dates, cfg, frame)
    proxy = benchmark(panel, dates, dict(cfg, benchmark="equal_weight_sample"))
    proxy.to_csv(output_root() / "reports/proxy_benchmark.csv")
    bench.to_csv(output_root() / "reports" / "benchmark.csv")
    from indexkit.monitor import exception_explanations, monitor, rebalance_report

    log = monitor(frame, panel, {n: r for n, r in results.items() if n != "MULTI"}, cfg)
    if "MULTI" in results:
        import pandas as pd

        multi_frame = (
            panels["MULTI"]
            .rename_axis("date")
            .reset_index()
            .melt(id_vars="date", var_name="symbol", value_name=cfg["price_field"])
        )
        for column in ("open", "high", "low", "close"):
            multi_frame[column] = multi_frame[cfg["price_field"]]
        multi_frame["volume"] = 0
        multi_cfg = dict(cfg, universe=list(panels["MULTI"].columns))
        multi_cfg["thresholds"] = dict(
            cfg["thresholds"], weight_cap=max(cfg["multi"]["targets"].values())
        )
        multi_log = monitor(multi_frame, panels["MULTI"], {"MULTI": results["MULTI"]}, multi_cfg)
        log = pd.concat([log, multi_log, fill_flags], ignore_index=True).drop_duplicates()
    log.to_csv(output_root() / "reports" / "monitor_log.csv", index=False)
    exception_explanations(log, results, cfg).to_csv(
        output_root() / "reports/monitor_explanations.csv", index=False
    )
    log.groupby(["check_name", "severity"]).size().rename("count").to_csv(
        output_root() / "reports" / "monitor_summary.csv"
    )
    for name, result in results.items():
        rebalance_report(result, panels[name], cfg if name != "MULTI" else multi_cfg, log).to_csv(
            output_root() / "reports" / f"{name}_rebalance_report.csv", index=False
        )
    import pandas as pd

    from indexkit.attribution import brinson, contributors
    from indexkit.stress import betas, composition, historical, hypothetical

    sectors = pd.read_csv(ROOT / cfg["sector_inputs"]).set_index("symbol").sector.to_dict()
    for name, result in results.items():
        local_panel = panels[name]
        local_sectors = sectors
        local_bench = proxy
        targets = None
        if name == "MULTI":
            from indexkit.multi_asset import fixed_benchmark

            local_sectors = {s: s for s in local_panel.columns}
            local_bench = fixed_benchmark(local_panel, cfg)
            targets = cfg["multi"]["targets"]
        a, m, res = brinson(
            result, local_panel, local_bench, local_sectors, targets, local_bench.attrs["label"]
        )
        stocks, sector, stats = composition(
            result, local_sectors, betas(local_panel, bench, cfg), local_panel
        )
        outputs = {
            "attribution": a,
            "monthly": m,
            "compounding_bridge": res,
            "contributors": contributors(result),
            "composition": stocks,
            "sector_weights": sector,
            "concentration": stats,
            "historical_stress": historical(local_panel, result, cfg),
            "hypothetical_stress": hypothetical(stocks),
        }
        for label, table in outputs.items():
            table.to_csv(output_root() / "reports" / f"{name}_{label}.csv", index=False)
    from indexkit.options import artifacts

    artifacts(cfg)
    from indexkit.rates import pricing_sheet

    pricing_sheet(cfg, fast)
    from indexkit.structured import artifacts as structured_artifacts

    structured_artifacts(cfg, fast)
    if not fast:
        from indexkit.validation import studies

        studies(cfg)
    from indexkit.reporting import generate
    from indexkit.robustness import artifacts as robustness_artifacts

    robustness_artifacts(results, panels, bench, cfg, sectors)
    generate(results, bench, cfg, log, proxy)
    from indexkit.drafts import generate as note_drafts

    note_drafts(cfg)
    if not fast:
        import json

        from indexkit.crosschecks import equity_checks, languages

        equity_checks(cfg)
        statuses = languages(results["MOM10"], cfg)
        manifest_path = output_root() / "reports/run_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["language_crosschecks"] = statuses
        manifest["not_done"].extend(
            value for value in statuses.values() if value.startswith("NOT DONE")
        )
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return cfg, frame, panel, results, bench


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--fast", action="store_true")
    mode.add_argument("--full", action="store_true")
    parser.add_argument("--config")
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    run(not args.full, config(args.config), args.output_dir)
