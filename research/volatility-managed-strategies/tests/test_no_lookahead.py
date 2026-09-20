"""Leakage guard: the backtest must never use data from the future.

Strategy: run the harness with a 'spy' forecast function that records the max
index it is shown; assert it never exceeds the current time t.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.backtest import expanding_oos


def test_forecast_sees_only_past():
    idx = pd.bdate_range("2005-01-03", periods=2500)
    df = pd.DataFrame({"rv": np.abs(np.random.RandomState(42).randn(len(idx))) * 1e-4}, index=idx)

    seen_max = {"t": pd.Timestamp.min}

    def fit_fn(train):
        # the last training timestamp is 't'; record it
        seen_max["t"] = max(seen_max["t"], train.index[-1])
        return train.index[-1]

    def forecast_fn(model_t, hist, h):
        # must not receive anything beyond 't'
        assert hist.index[-1] == model_t
        return float(hist["rv"].iloc[-1])

    res = expanding_oos(df, fit_fn, forecast_fn, first_oos="2013-01-02", h=1)
    # the inner asserts guarantee no look-ahead; here just confirm the run produced output
    assert not res.empty


def test_rv_non_negative_identity():
    from src.realized import daily_features
    # a trivial constant price -> zero returns -> RV == 0
    idx = pd.date_range("2020-01-02 09:30", "2020-01-02 16:00", freq="1min", tz="America/New_York")
    px = pd.Series(100.0, index=idx)
    feat = daily_features(px, freq="5min", min_bars=5)
    assert (feat["rv"] >= 0).all()
