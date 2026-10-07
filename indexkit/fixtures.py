"""Offline synthetic test DB; these observations are never market-data results."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from mdq.ingest import upsert_prices
from mdq.store import connect, init_db

from .data import config


def create_fixture(directory):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    cfg = config(Path(__file__).resolve().parents[1] / "config.yaml")
    database = directory / "fixture.sqlite"
    init_db(str(database))
    days = pd.bdate_range("2021-01-01", periods=420)
    rng = np.random.default_rng(42)
    market = rng.normal(0.0002, 0.006, len(days))
    rows = []
    for i, symbol in enumerate(
        [
            *cfg["universe"],
            "TMPV.NS",
            "^NSEI",
            cfg["multi"]["gold_symbol"],
            cfg["multi"]["us_symbol"],
            cfg["multi"]["fx_symbol"],
        ]
    ):
        returns = market + rng.normal(0.0001, 0.001 + i * 0.0001, len(days))
        values = 100 * np.cumprod(1 + returns)
        if symbol == "TMPV.NS":
            values[100:] *= 1.5  # Explicit excluded-name fault fixture.
        for day, price in zip(days, values):
            rows.append(
                dict(
                    symbol=symbol,
                    date=day.strftime("%Y-%m-%d"),
                    open=price,
                    high=price * 1.01,
                    low=price * 0.99,
                    close=price,
                    adj_close=price,
                    volume=1000,
                )
            )
    with connect(str(database)) as conn:
        upsert_prices(conn, pd.DataFrame(rows), "synthetic-fixture")
    cfg["database"] = str(database)
    cfg["universe_label"] = "Synthetic test fixture; not observed market prices"
    path = directory / "fixture_config.json"
    path.write_text(json.dumps(cfg, indent=2) + "\n")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True)
    args = parser.parse_args()
    print(create_fixture(args.directory))


if __name__ == "__main__":
    main()
