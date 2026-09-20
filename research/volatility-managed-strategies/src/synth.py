"""Synthetic 1-minute price generator (seed-fixed).

Lets the FULL pipeline (ingest -> realized -> backtest -> evaluate -> figures) run
on a fresh clone WITHOUT the licensed MarketTick data. The generated series has
stochastic, clustering volatility (a persistent AR(1) log-variance), so realized
variance is forecastable and the HAR family beats the random walk — enough to
smoke-test the code end-to-end.

These numbers are ILLUSTRATIVE, not the paper's results (those require the
licensed 1-minute index data; run.py --raw data/raw or analyze.py).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def synthetic_prices(n_days: int = 750, bars_per_day: int = 390, seed: int = 42,
                     start: str = "2015-01-02", mean_vol: float = 0.11) -> pd.Series:
    """Deterministic synthetic 1-minute close series (UTC), US RTH (13:30-20:00).

    Volatility clusters via an AR(1) daily log-variance (phi=0.97), so RV has the
    long-memory signature the HAR model exploits.
    """
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(start=start, periods=n_days, tz="UTC")

    mu = np.log(mean_vol ** 2 / 252.0)          # target mean daily log-variance
    phi, eta = 0.97, 0.25
    logv = np.empty(n_days)
    logv[0] = mu
    for t in range(1, n_days):
        logv[t] = mu + phi * (logv[t - 1] - mu) + eta * rng.standard_normal()
    daily_var = np.exp(logv)

    idx_parts, px_parts = [], []
    level = 100.0
    for d in range(n_days):
        sig = np.sqrt(daily_var[d] / bars_per_day)
        r = rng.standard_normal(bars_per_day) * sig
        prices = np.exp(np.log(level) + np.cumsum(r))
        level = float(prices[-1])               # carry close -> next open
        t0 = days[d] + pd.Timedelta(hours=13, minutes=30)
        idx_parts.append(t0 + pd.to_timedelta(np.arange(bars_per_day), unit="m"))
        px_parts.append(prices)

    idx = pd.DatetimeIndex(np.concatenate([i.to_numpy() for i in idx_parts]), tz="UTC")
    return pd.Series(np.concatenate(px_parts), index=idx, name="close")
