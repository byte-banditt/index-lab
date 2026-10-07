import shutil
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
from indexkit.crosschecks import equity_checks, languages
from indexkit.data import ROOT, config, load, output_root, prices
from indexkit.index_engine import build
from indexkit.options import digital, monte_carlo, vanilla


def test_full_equity_and_language_checks():
    c = config()
    (output_root() / "reports").mkdir(parents=True)
    assert equity_checks(c).passed.all()
    f, _ = load(c)
    result = build(prices(f, c), "MOM10", c)
    statuses = languages(result, c)
    if shutil.which("javac") and shutil.which("java"):
        assert "passed: 5" in statuses["java"]
    if not shutil.which("Rscript"):
        assert statuses["R"].startswith("NOT DONE: Rscript unavailable")


def test_explain_day_cli():
    c = config()
    f, _ = load(c)
    r = build(prices(f, c), "MOM10", c)
    directory = output_root() / "reports"
    directory.mkdir(parents=True)
    for name in ("weights", "contributions", "levels"):
        getattr(r, name).to_csv(directory / f"MOM10_{name}.csv")
    pd.DataFrame(columns=["date", "symbol", "check_name"]).to_csv(
        directory / "monitor_log.csv", index=False
    )
    day = r.weights.index[5].date().isoformat()
    command = [
        sys.executable,
        str(ROOT / "scripts/explain_day.py"),
        "--index",
        "MOM10",
        "--date",
        day,
        "--output-dir",
        str(output_root()),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    assert "contribution" in result.stdout and "gross_return" in result.stdout
    assert r.weights.columns[0] in result.stdout


@pytest.mark.parametrize("offset", range(5))
def test_repeat_seed_equity_mc(offset):
    c = config()
    p = c["options"]
    args = (p["spot"], p["strike"], p["expiry"], p["rate"], p["vol"], p["q"])
    for digital_payoff in (False, True):
        price, se = monte_carlo(
            *args, paths=100000, seed=c["seed"] + offset, digital_payoff=digital_payoff
        )
        exact = (digital if digital_payoff else vanilla)(*args)["price"]
        assert abs(price - exact) <= 3 * se
        assert np.isfinite(price)


@pytest.mark.parametrize("offset", range(5))
def test_repeat_seed_spread_and_range(offset):
    from indexkit.rates import margrabe, range_accrual, spread_mc

    seed = config()["seed"] + offset
    price, se = spread_mc(100, 95, 0, 1, 0.05, 0.2, 0.25, 0.3, paths=100000, seed=seed)
    assert abs(price - margrabe(100, 95, 1, 0.2, 0.25, 0.3)) <= 3 * se
    result = range_accrual(100, 80, 120, 1, 0.05, 0.2, 0.01, paths=100000, seed=seed)
    assert abs(result["price"] - result["digital_strip"]) <= 3 * result["se"]
