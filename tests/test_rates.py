import numpy as np
import pytest

from indexkit.rates import (
    DiscountCurve,
    cap_floor,
    dv01,
    margrabe,
    par_swap_rate,
    range_accrual,
    spread_mc,
    swap,
    swaption,
)


def curve():
    return DiscountCurve([0.5, 1, 2, 5, 10], [0.04, 0.045, 0.047, 0.05, 0.051])


def test_curve_swap_and_parities():
    c = curve()
    assert c.df(0) == 1
    assert c.df(0.75) == pytest.approx(np.sqrt(c.df(0.5) * c.df(1)))
    with pytest.raises(ValueError):
        c.df(11)
    k = par_swap_rate(c, 0, 5)
    assert swap(c, k)["price"] == pytest.approx(0.0, abs=1e-14)
    assert dv01(c, k) > 0
    for strike in [0.03, k, 0.07]:
        cap = cap_floor(c, strike, vol=0.2)
        floor = cap_floor(c, strike, vol=0.2, kind="put")
        assert cap - floor == pytest.approx(swap(c, strike)["price"], abs=1e-13)
        payer = swaption(c, strike)
        receiver = swaption(c, strike, kind="receiver")
        assert payer - receiver == pytest.approx(
            swap(c, strike, start=1, end=5)["price"], abs=1e-13
        )


def test_spread_mc():
    p, se = spread_mc(100, 95, 0, 1, 0.05, 0.2, 0.25, 0.3, paths=100000, seed=42)
    assert abs(p - margrabe(100, 95, 1, 0.2, 0.25, 0.3)) < 3 * se
    assert spread_mc(100, 95, 5, 1, 0.05, 0.2, 0.25, 0.3)[0] < p


def test_range_strip():
    result = range_accrual(100, 80, 120, 1, 0.05, 0.2, 0.01, paths=100000, seed=42)
    assert abs(result["price"] - result["digital_strip"]) < 3 * result["se"]


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
@pytest.mark.parametrize("field", ["forward", "strike", "expiry", "vol", "discount"])
def test_black76_rejects_nonfinite(field, bad):
    from indexkit.rates import black76

    inputs = dict(forward=0.05, strike=0.05, expiry=1, vol=0.2, discount=0.95)
    inputs[field] = bad
    with pytest.raises(ValueError):
        black76(**inputs)


def test_rate_digital_boundaries():
    from indexkit.rates import rate_digital

    c = curve()
    assert rate_digital(c, 0.06, 0.05, 0, 1, 0.2) == pytest.approx(c.df(1))
    assert rate_digital(c, 0.04, 0.05, 0, 1, 0.2, "put") == pytest.approx(c.df(1))
    assert rate_digital(c, 0.05, 0.05, 0, 0, 0.2) == 0
    assert rate_digital(c, 0.06, 0.05, 1, 1, 0) == pytest.approx(c.df(1))
    for field in ["forward", "strike", "expiry", "payment", "vol", "cash"]:
        args = dict(forward=0.05, strike=0.05, expiry=1, payment=1, vol=0.2, cash=1)
        args[field] = np.nan
        with pytest.raises(ValueError):
            rate_digital(c, **args)
    with pytest.raises(ValueError):
        rate_digital(c, 0.05, 0.05, 1, 0.5, 0.2)
    with pytest.raises(ValueError):
        rate_digital(c, 0.05, 0.05, -1, 1, 0.2)
