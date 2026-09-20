"""Forecast evaluation: QLIKE / MSE losses, Diebold-Mariano, Clark-West,
Mincer-Zarnowitz. QLIKE is the primary (proxy-robust) loss (Patton, 2011).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def qlike(actual, pred) -> float:
    """QLIKE = mean( RV/h - ln(RV/h) - 1 ). Robust to RV-proxy noise."""
    a = np.asarray(actual, float)
    p = np.asarray(pred, float)
    r = a / p
    return float(np.mean(r - np.log(r) - 1.0))


def mse(actual, pred) -> float:
    return float(np.mean((np.asarray(actual, float) - np.asarray(pred, float)) ** 2))


def diebold_mariano(loss_a, loss_b):
    """DM test on loss differences with HAC (Newey-West) variance.

    Returns (dm_stat, p_value). For NESTED models use clark_west instead.
    """
    d = np.asarray(loss_a, float) - np.asarray(loss_b, float)
    n = len(d)
    dbar = d.mean()
    # HAC long-run variance of the mean (Bartlett kernel)
    L = int(np.floor(4 * (n / 100) ** (2 / 9)))
    g0 = np.var(d, ddof=0)
    lrv = g0
    for k in range(1, L + 1):
        cov = np.cov(d[k:], d[:-k])[0, 1]
        lrv += 2 * (1 - k / (L + 1)) * cov
    stat = dbar / np.sqrt(lrv / n)
    from scipy.stats import norm
    return float(stat), float(2 * (1 - norm.cdf(abs(stat))))


def clark_west(actual, pred_small, pred_large):
    """Clark-West adjusted test for NESTED models (small nested in large).

    Regress the CW-adjusted term on a constant; one-sided t on the mean.
    """
    a = np.asarray(actual, float)
    f1 = np.asarray(pred_small, float)
    f2 = np.asarray(pred_large, float)
    f_hat = (a - f1) ** 2 - ((a - f2) ** 2 - (f1 - f2) ** 2)
    res = sm.OLS(f_hat, np.ones((len(f_hat), 1))).fit(cov_type="HAC", cov_kwds={"maxlags": 10})
    from scipy.stats import norm
    t = float(res.params[0] / res.bse[0])
    return t, float(1 - norm.cdf(t))  # one-sided: large (nesting) model forecasts better


def mincer_zarnowitz(actual, pred):
    """Regress actual on forecast; joint test a=0, b=1 (unbiasedness)."""
    X = sm.add_constant(np.asarray(pred, float))
    res = sm.OLS(np.asarray(actual, float), X).fit(cov_type="HAC", cov_kwds={"maxlags": 10})
    return res
