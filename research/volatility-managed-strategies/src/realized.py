"""Realized measures: RV, bipower variation, jumps, realized semivariance,
plus the HAR lag features (daily / weekly / monthly).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def daily_features(price: pd.Series, freq: str = "5min", min_bars: int = 20) -> pd.DataFrame:
    """Per-day realized measures from an intraday price series.

    Returns columns: rv, bv, jump, rs_p, rs_m, n  (index = date).
    RV_t = sum r^2 ; BV_t = (pi/2) sum |r_{i-1}||r_i| ; jump = max(RV-BV, 0).
    """
    px = price.resample(freq).last().dropna()
    rows = []
    for day, g in px.groupby(px.index.date):
        r = np.log(g.values)
        r = np.diff(r)
        if len(r) < min_bars:
            continue
        rv = float(np.sum(r ** 2))
        bv = float((np.pi / 2) * np.sum(np.abs(r[1:]) * np.abs(r[:-1])))
        jump = max(rv - bv, 0.0)
        rs_p = float(np.sum(r[r > 0] ** 2))
        rs_m = float(np.sum(r[r < 0] ** 2))
        rq = float((len(r) / 3.0) * np.sum(r ** 4))   # realized quarticity (for HARQ)
        rows.append((day, rv, bv, jump, rs_p, rs_m, rq, len(r)))
    df = pd.DataFrame(rows, columns=["date", "rv", "bv", "jump", "rs_p", "rs_m", "rq", "n"])
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")


def add_har_lags(df: pd.DataFrame, col: str = "rv") -> pd.DataFrame:
    """Add HAR components: daily (t), weekly (t-5:t), monthly (t-22:t).

    Strictly backward-looking (no look-ahead): uses only information up to t.
    """
    out = df.copy()
    out["rv_d"] = out[col]
    out["rv_w"] = out[col].rolling(5).mean()
    out["rv_m"] = out[col].rolling(22).mean()
    return out
