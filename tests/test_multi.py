import numpy as np
import pandas as pd
from indexkit.attribution import brinson
from indexkit.data import config, load, prices
from indexkit.index_engine import build
from indexkit.multi_asset import fixed_benchmark, sleeves


def test_multi_conversion_fill_drift_and_no_future():
    c = config()
    f, _ = load(c)
    p = prices(f, c)
    symbol = c["multi"]["us_symbol"]
    day = p.index[300]
    # A fixture holiday: no quote. It must be carried and flagged, never fabricated.
    f = f[~((f.symbol == symbol) & (f.date == day))]
    panel, flags = sleeves(f, p, c)
    assert ((flags.symbol == symbol) & (flags.date > day)).any()
    calc = p.index[302]
    us = f[(f.symbol == symbol) & (f.date < calc)].iloc[-1].adj_close
    fx = f[(f.symbol == c["multi"]["fx_symbol"]) & (f.date < calc)].iloc[-1].adj_close
    assert panel.loc[calc, "NVDA_INR"] == us * fx
    result = build(panel, "MULTI", c)
    np.testing.assert_allclose(result.weights.sum(axis=1), 1, atol=1e-12)
    effective = result.turnover.effective_date.iloc[0]
    altered = panel.copy()
    altered.loc[effective:, "NVDA_INR"] *= 1.05
    future = build(altered, "MULTI", c)
    pd.testing.assert_series_equal(result.weights.loc[effective], future.weights.loc[effective])
    for event in result.turnover.itertuples():
        np.testing.assert_allclose(
            result.weights.loc[event.effective_date],
            pd.Series(c["multi"]["targets"]).reindex(panel.columns),
        )
    b = fixed_benchmark(panel, c)
    a, m, _ = brinson(
        result, panel, b, {s: s for s in panel}, c["multi"]["targets"], b.attrs["label"]
    )
    effect = a.groupby("month")[["allocation", "selection", "interaction"]].sum().sum(axis=1)
    np.testing.assert_allclose(effect, m.active_gross, atol=1e-12)
