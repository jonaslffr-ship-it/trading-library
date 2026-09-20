"""Expanding-window pseudo-out-of-sample backtest.

Invariant (tested): at time t we use ONLY data with index <= t to produce the
forecast for t+h. First OOS date is frozen in PREREGISTRATION.md (2013-01-02).
"""
from __future__ import annotations

import pandas as pd


def expanding_oos(df: pd.DataFrame, fit_fn, forecast_fn, first_oos="2013-01-02", h: int = 1):
    """Run one model over the OOS period.

    fit_fn(train_df) -> model ; forecast_fn(model, hist_df, h) -> float
    Returns a DataFrame indexed by the target date with columns [pred, actual].
    """
    idx = df.index
    start = idx.searchsorted(pd.Timestamp(first_oos))
    preds, actuals, dates = [], [], []
    for k in range(start, len(idx) - h):
        train = df.iloc[: k + 1]                 # only info up to t == idx[k]
        model = fit_fn(train)
        preds.append(forecast_fn(model, train, h))
        actuals.append(float(df["rv"].iloc[k + h]))
        dates.append(idx[k + h])
    return pd.DataFrame({"pred": preds, "actual": actuals}, index=pd.DatetimeIndex(dates))


def run_all(df: pd.DataFrame, first_oos="2013-01-02", h: int = 1) -> dict:
    """Run the core forecast ladder (RW / EWMA / HAR / log-HAR) through the
    leakage-free expanding-window harness.

    ``df`` must carry the realized measures + HAR lags (src.realized.daily_features
    then add_har_lags): columns rv, rv_d, rv_w, rv_m. Returns
    {model_name: DataFrame[pred, actual]}. GARCH/AR live in analyze.py (they need
    the ``arch`` refit loop and are exploratory, not part of the smoke test).
    """
    from .models import rw_forecast, ewma_forecast, fit_har, forecast_har

    registry = {
        "RW":      (lambda tr: None,                    lambda m, hist, hh: rw_forecast(hist, hh)),
        "EWMA":    (lambda tr: None,                    lambda m, hist, hh: ewma_forecast(hist, hh)),
        "HAR":     (lambda tr: fit_har(tr, log=False),  forecast_har),
        "log-HAR": (lambda tr: fit_har(tr, log=True),   forecast_har),
    }
    return {name: expanding_oos(df, fit_fn, fc_fn, first_oos=first_oos, h=h)
            for name, (fit_fn, fc_fn) in registry.items()}
