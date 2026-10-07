import numpy as np
import pandas as pd
from indexkit.attribution import brinson, contributors
from indexkit.data import ROOT, config, load, prices
from indexkit.index_engine import benchmark, build
from indexkit.stress import betas, composition, historical, hypothetical


def test_reconciles_and_stress():
    c = config()
    f, _ = load(c)
    p = prices(f, c)
    sectors = pd.read_csv(ROOT / "data/sector_map.csv").set_index("symbol").sector.to_dict()
    for name in (n for n in c["indices"] if n != "MULTI"):
        result = build(p, name, c)
        b = benchmark(p, result.levels.index, dict(c, benchmark="equal_weight_sample"))
        a, m, res = brinson(result, p, b, sectors)
        effects = a.groupby("month")[["allocation", "selection", "interaction"]].sum().sum(axis=1)
        np.testing.assert_allclose(effects, m.active_gross, atol=1e-12)
        np.testing.assert_allclose(m.active_gross + m.cost_effect, m.active_net, atol=1e-12)
        assert np.isfinite(res.compounding_residual.iloc[0])
        assert len(contributors(result)) == 10
        beta = betas(p, b, c)
        stock, sector, stat = composition(result, sectors, beta, p)
        np.testing.assert_allclose(stock.weight.sum(), 1)
        np.testing.assert_allclose(sector.weight.sum(), 1)
        assert 0 < stat.HHI.iloc[0] <= 1
        h = historical(p, stock, c)
        assert len(h) == 3
        assert (h.max_drawdown <= 0).all()
        shocks = hypothetical(stock)
        np.testing.assert_allclose(shocks.pnl.iloc[2], -0.2 * stat.beta.iloc[0])


def test_universe_change_removes_entire_sector():
    c = config()
    f, _ = load(c)
    sectors = pd.read_csv(ROOT / "data/sector_map.csv").set_index("symbol").sector.to_dict()
    c["universe"] = [s for s in c["universe"] if sectors[s] != "Energy"]
    p = prices(f, c)
    result = build(p, "MOM10", c)
    b = benchmark(p, result.levels.index, dict(c, benchmark="equal_weight_sample"))
    a, m, bridge = brinson(result, p, b, sectors)
    assert "Energy" not in set(a.sector)
    assert np.isfinite(a.select_dtypes(include="number").to_numpy()).all()
    effects = a.groupby("month")[["allocation", "selection", "interaction"]].sum().sum(axis=1)
    np.testing.assert_allclose(effects, m.active_gross, atol=1e-12)
    assert np.isfinite(bridge.select_dtypes(include="number").to_numpy()).all()
