"""Forecasting models: benchmarks (RW, EWMA, AR, GARCH) and the HAR family.

Every model exposes ``fit(train_df) -> model`` and ``forecast(model, hist_df, h) -> float``
so the backtest harness can treat them uniformly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

# ------------------------- benchmarks -------------------------

def rw_forecast(hist: pd.DataFrame, h: int = 1) -> float:
    """Random walk: next RV = last RV."""
    return float(hist["rv"].iloc[-1])


def ewma_forecast(hist: pd.DataFrame, h: int = 1, lam: float = 0.94) -> float:
    """RiskMetrics EWMA on RV."""
    x = hist["rv"].values
    w = lam ** np.arange(len(x))[::-1]
    return float(np.sum(w * x) / np.sum(w))


# ------------------------- HAR family -------------------------

HAR_COLS = ["rv_d", "rv_w", "rv_m"]


def fit_har(train: pd.DataFrame, target: str = "rv", log: bool = True, extra=None):
    """OLS HAR (optionally log-RV, optional extra regressors e.g. ['jump'] or ['vix'])."""
    cols = HAR_COLS + (extra or [])
    y = np.log(train[target].shift(-1)) if log else train[target].shift(-1)
    X = np.log(train[cols].clip(lower=1e-12)) if log else train[cols]
    X = sm.add_constant(X)
    d = pd.concat([y.rename("y"), X], axis=1).dropna()
    model = sm.OLS(d["y"], d.drop(columns="y")).fit(
        cov_type="HAC", cov_kwds={"maxlags": 10}
    )
    model._log = log  # remember transform for forecasting
    model._cols = cols
    return model


def forecast_har(model, hist: pd.DataFrame, h: int = 1) -> float:
    """One-step HAR forecast; retransform with log-normal bias correction."""
    x = hist.iloc[[-1]][model._cols]
    x = np.log(x.clip(lower=1e-12)) if model._log else x
    x = sm.add_constant(x, has_constant="add")
    yhat = float(model.predict(x).iloc[0])
    if model._log:
        yhat = np.exp(yhat + 0.5 * model.scale)  # Hansen-Lunde retransform
    return yhat


# GARCH(1,1) / AR(p): implement via `arch` / statsmodels during the build.
# def fit_garch(train): ...
# def fit_ar(train, p): ...
