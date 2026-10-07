import numpy as np
import pandas as pd
import pytest
from indexkit.data import config, load, prices
from indexkit.index_engine import benchmark, build
from indexkit.robustness import block_bootstrap, defaults_history, drawdown, sensitivity
from indexkit.stress import historical


def test_bootstrap_and_defaults():
    c = config()
    a = pd.Series(np.full(100, 0.001))
    b = block_bootstrap(a, c)
    assert b["ci_lower"] == pytest.approx(c["annual_sessions"] * 0.001)
    assert b["ci_upper"] == pytest.approx(c["annual_sessions"] * 0.001)
    assert not b["contains_zero"]
    assert block_bootstrap(pd.Series(np.zeros(100)), c)["contains_zero"]
    h = defaults_history(c)
    assert h.matches_current.all()


def test_drawdown_and_historical_weights():
    c = config()
    f, _ = load(c)
    p = prices(f, c)
    r = build(p, "LVOL10", c)
    b = benchmark(p, r.levels.index, c, f)
    mapping = {s: "test_sector" for s in p}
    summary, stocks, sectors = drawdown(r, mapping, b)
    np.testing.assert_allclose(
        stocks.contribution.sum() + summary["cost_effect"], summary["drawdown"]
    )
    np.testing.assert_allclose(sectors.contribution.sum(), stocks.contribution.sum())
    h = historical(p, r, c)
    for row in h.itertuples():
        held = r.levels.loc[row.start : row.end, "gross_return"]
        np.testing.assert_allclose(row.pnl, (1 + held).prod() - 1)
    grid = sensitivity(p, b, c)
    assert len(grid) == 2 * np.prod(
        [len(c["robustness"][k]) for k in ["top_n", "momentum_months", "vol_days", "cost_bps"]]
    )
    assert c["cost_bps"] == 10
