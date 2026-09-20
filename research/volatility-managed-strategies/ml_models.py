#!/usr/bin/env python3
"""ML forecasters for RV (Lasso / ElasticNet / Gradient Boosting) vs HAR-IV.

Expanding refit with a purge gap; log-target; insanity filter. Feature set = log of
{rv_d,rv_w,rv_m,bv,rq,rs_m,rs_p,jump,ivar} + raw ret_neg. Compared to HAR-IV via QLIKE
and Diebold-Mariano (non-nested). Honest prior (Liu-Patton-Sheppard + our null battery):
very hard to beat 5-min HAR -> this is a breadth/robustness check, not an expected winner.

Run:  python ml_models.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from analyze import build_features, _ols, FIRST_OOS, EPS, MIN_VAR
from src.ingest import load_days
from src.evaluate import qlike, diebold_mariano

LOGF = ["rv_d", "rv_w", "rv_m", "bv", "rq", "rs_m", "rs_p", "jump", "ivar"]


def add_ivar(feat):
    v = load_days("data/raw/vix")
    d = v.groupby(v.index.date).last(); d.index = pd.to_datetime(d.index)
    feat = feat.copy()
    feat["ivar"] = (d.reindex(feat.index) / 100.0) ** 2 / 252.0
    return feat


def build_X(feat):
    Xp = np.log(np.clip(feat[LOGF].to_numpy(float), EPS, None))
    Xr = feat[["ret_neg"]].to_numpy(float)
    return pd.DataFrame(np.column_stack([Xp, Xr]), index=feat.index)


def ml_forecast(feat, make_model, first_oos, refit=21, purge=1):
    """Expanding-window ML forecast of RV; refit every `refit` steps with a purge gap."""
    Xdf = build_X(feat)
    d = pd.concat([Xdf.shift(1), feat["rv"].rename("y")], axis=1).dropna()
    dates = d.index
    X = d.drop(columns="y").to_numpy(float); y = d["y"].to_numpy(float)
    start = int(dates.searchsorted(pd.Timestamp(first_oos)))
    preds = np.full(len(d), np.nan); model = None; s2 = 0.0
    for i in range(start, len(d)):
        if model is None or (i - start) % refit == 0:
            j = max(1, i - purge)                                  # purge gap (no leak)
            yl = np.log(np.clip(y[:j], EPS, None))
            model = make_model(); model.fit(X[:j], yl)
            s2 = float(np.var(yl - model.predict(X[:j])))
        yhat = float(np.exp(model.predict(X[i:i + 1])[0] + 0.5 * s2))
        preds[i] = min(max(yhat, MIN_VAR), 4.0 * float(y[:i].max()))  # insanity filter
    return pd.DataFrame({"pred": preds, "actual": y}, index=dates).iloc[start:]


def main():
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LassoCV, ElasticNetCV, LinearRegression, RidgeCV
    from sklearn.ensemble import HistGradientBoostingRegressor

    feat = add_ivar(build_features())
    mk = {
        # OLS / Ridge on the SAME feature set: isolates whether the ML gain is
        # rich FEATURES (OLS already captures it) or REGULARIZATION/nonlinearity.
        "OLS": lambda: make_pipeline(StandardScaler(), LinearRegression()),
        "Ridge": lambda: make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-4, 2, 25))),
        "Lasso": lambda: make_pipeline(StandardScaler(), LassoCV(cv=3, alphas=20, max_iter=5000, random_state=42)),
        "ElasticNet": lambda: make_pipeline(StandardScaler(), ElasticNetCV(cv=3, l1_ratio=[.3, .6, .9], alphas=20, max_iter=5000, random_state=42)),
        "GBRT": lambda: HistGradientBoostingRegressor(max_iter=250, learning_rate=0.05, max_depth=3, l2_regularization=1.0, random_state=42),
    }
    lh = _ols(feat, ["rv_d", "rv_w", "rv_m"], [], FIRST_OOS, log_target=True)
    hiv = _ols(feat, ["rv_d", "rv_w", "rv_m", "ivar"], [], FIRST_OOS, log_target=True)
    preds = {"log-HAR": lh, "HAR-IV": hiv}
    for name, f in mk.items():
        print(f"fitting {name} (expanding refit, ~min) ...", flush=True)
        preds[name] = ml_forecast(feat, f, FIRST_OOS)

    idx = None
    for p in preds.values():
        idx = p.index if idx is None else idx.intersection(p.index)
    a = hiv.loc[idx, "actual"].to_numpy()

    def ql(f):
        r = a / np.clip(f, MIN_VAR, None)
        return r - np.log(r) - 1.0

    rows = []
    for name, p in preds.items():
        pv = p.loc[idx, "pred"].to_numpy()
        dmp = np.nan if name == "HAR-IV" else diebold_mariano(ql(hiv.loc[idx, "pred"].to_numpy()), ql(pv))[1]
        rows.append({"model": name, "QLIKE": qlike(a, pv), "vs_HARIV_DM_p": dmp})
    res = pd.DataFrame(rows).set_index("model")
    print(f"\n=== ML vs HAR-IV (SPX RV-Forecast, OOS, {len(idx)} Tage) ===")
    print(res.to_string(float_format=lambda x: f"{x:.4f}"))
    res.to_csv("results/ml_forecast_metrics.csv")
    print("\nDM p<0.05 & QLIKE<HAR-IV -> ML schlaegt HAR-IV; sonst bleibt HAR-IV der beste.")


if __name__ == "__main__":
    main()
