"""Write mdq ingestion inputs; never download data or open the DB."""

import argparse
from pathlib import Path

import yaml

from indexkit.data import ROOT, config


def write_config(cfg, output):
    symbols = list(dict.fromkeys([
        *cfg["universe"], cfg["benchmark"],
        cfg["multi"]["gold_symbol"], cfg["multi"]["us_symbol"], cfg["multi"]["fx_symbol"],
    ]))
    settings = cfg["ingestion"]
    inputs = dict(
        database=cfg["database"], start_date=settings["start_date"], end_date=cfg["end"],
        overlap_days=settings["overlap_days"], symbols=symbols,
        checks=dict(stale_sessions=cfg["thresholds"]["stale_sessions"],
                    return_outlier_robust_z=settings["return_outlier_robust_z"]),
    )
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(inputs, sort_keys=False))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config")
    parser.add_argument("--output", default=str(ROOT / "data/mdq_ingestion.yaml"))
    args = parser.parse_args()
    print(write_config(config(args.config), args.output))


if __name__ == "__main__":
    main()
