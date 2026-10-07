"""INR sleeves on the India calendar; foreign closing quotes lag one calendar day."""

import numpy as np
import pandas as pd

from .index_engine import benchmark, build


def sleeves(frame, equity_panel, cfg):
    settings = cfg["multi"]
    dates = equity_panel.index
    rows = []

    def align(symbol, lag):
        source = frame.loc[frame.symbol == symbol, ["date", cfg["price_field"]]].dropna()
        if source.empty or source.date.duplicated().any():
            raise ValueError(f"Missing/duplicate source for {symbol}")
        source = source.sort_values("date").rename(columns={cfg["price_field"]: "quote"})
        source["available"] = source.date + pd.Timedelta(days=lag)
        aligned = pd.merge_asof(
            pd.DataFrame({"date": dates}),
            source.rename(columns={"date": "source_date"}),
            left_on="date",
            right_on="available",
        )
        age = (aligned.date - aligned.available).dt.days
        valid = age.between(0, settings["max_fill_days"])
        for row in aligned.loc[valid & (age > 0)].itertuples():
            rows.append(
                dict(
                    date=row.date,
                    symbol=symbol,
                    check_name="holiday_forward_fill",
                    severity="warning",
                    detail=f"Quote {row.source_date.date()}; "
                    f"available {row.available.date()}; carry age "
                    f"{(row.date - row.available).days} calendar days",
                )
            )
        return pd.Series(aligned.quote.where(valid).values, index=dates)

    gold = align(settings["gold_symbol"], 0)
    us = align(settings["us_symbol"], 1)
    fx = align(settings["fx_symbol"], 1)
    equity = benchmark(equity_panel, dates, dict(cfg, benchmark="equal_weight_sample"))
    panel = pd.DataFrame({"EQUITY": equity.level, "GOLD": gold, "NVDA_INR": us * fx})
    # Leading unavailable observations cannot be filled backwards.
    complete = panel.notna().all(axis=1)
    if not complete.any():
        raise ValueError("No common multi-asset history within fill limit")
    panel = panel.loc[complete.idxmax() :]
    if not np.isfinite(panel.to_numpy()).all() or (panel <= 0).any().any():
        raise ValueError("Multi-asset gap exceeds configured fill limit")
    flags = pd.DataFrame(rows, columns=["date", "symbol", "check_name", "severity", "detail"])
    return panel, flags[flags.date.isin(panel.index)]


def fixed_benchmark(panel, cfg):
    gross = build(panel, "MULTI", dict(cfg, net=False))
    result = gross.levels[["gross_return", "gross_level"]].rename(
        columns={"gross_return": "return_", "gross_level": "level"}
    )
    result.attrs["label"] = "Fixed-weight INR asset-sleeve benchmark"
    return result
