import pandas as pd
import pytest

from indexkit.data import config, load, prices
from indexkit.index_engine import build
from indexkit.monitor import monitor, rebalance_report


@pytest.fixture
def state():
    c = config()
    f, _ = load(c)
    p = prices(f, c)
    r = build(p, "MOM10", c)
    return c, f, p, r


@pytest.mark.parametrize(
    "fault,check",
    [
        ("zero", "non_positive_price"),
        ("duplicate", "duplicate_rows"),
        ("missing", "missing_constituent_price"),
        ("jump", "overnight_jump"),
    ],
)
def test_faults(state, fault, check):
    c, f, p, r = state
    day = r.weights.index[10]
    symbol = r.weights.loc[day].idxmax()
    i = f.index[(f.symbol == symbol) & (f.date == day)][0]
    bad = f.copy()
    if fault == "zero":
        bad.loc[i, ["open", "close", "adj_close"]] = 0
    if fault == "duplicate":
        bad = pd.concat([bad, bad.loc[[i]]], ignore_index=True)
    if fault == "missing":
        bad = bad.drop(i)
    if fault == "jump":
        bad.loc[i, "adj_close"] *= 1.5
    log = monitor(bad, p, {"MOM10": r}, c)
    assert check in set(log.check_name)
    with pytest.raises(ValueError):
        prices(bad, c)


def test_rebalance(state):
    c, f, p, r = state
    log = monitor(f, p, {"MOM10": r}, c)
    proposal = rebalance_report(r, p, c, log)
    assert proposal.groupby("effective_date").after.sum().eq(1).all()
    assert len(proposal) == len(r.turnover) * len(p.columns)
    assert proposal.groupby("effective_date").trade.apply(
        lambda x: x.abs().sum()
    ).to_numpy() == pytest.approx(r.turnover.turnover.to_numpy())


def test_proposal_sanity_review(state):
    from copy import deepcopy

    c, f, p, r = state
    c = deepcopy(c)
    c["thresholds"]["turnover"] = 0.01
    log = monitor(f, p, {"MOM10": r}, c)
    proposal = rebalance_report(r, p, c, log)
    assert "rebalance_turnover" in proposal.checks.iloc[0]


def test_nan_unheld_weight_is_flagged(state):
    c, f, p, r = state
    day = r.weights.index[10]
    unheld = r.weights.loc[day].index[r.weights.loc[day] == 0][0]
    r.weights.loc[day, unheld] = float("nan")
    log = monitor(f, p, {"MOM10": r}, c)
    assert ((log.date == day) & (log.check_name == "weight_sum")).any()


def test_exception_explanations_use_observed_data(state):
    from copy import deepcopy

    from indexkit.monitor import exception_explanations

    c, f, p, r = state
    c = deepcopy(c)
    c["thresholds"]["index_sigma"] = 0.1
    c["thresholds"]["turnover"] = 0.01
    log = monitor(f, p, {"MOM10": r}, c)
    explanations = exception_explanations(log, {"MOM10": r}, c)
    assert set(explanations.check_name) == {"index_return_outlier", "rebalance_turnover"}
    for row in explanations.itertuples():
        if row.check_name == "index_return_outlier":
            assert row.observed == pytest.approx(r.levels.loc[row.date, "return_"])
        else:
            event = r.turnover.set_index("effective_date").loc[row.date]
            assert row.observed == pytest.approx(event.turnover)
            assert row.threshold == c["thresholds"]["turnover"]
