#!/usr/bin/env python3
"""Authoritative MCS on the insanity-FILTERED classical ladder + HAR-IV (fast)."""
from __future__ import annotations
import os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from analyze import build_features, _expanding_ols, _lag, FIRST_OOS, EPS, MIN_VAR, qloss, align
from ml_models import add_ivar
from src.evaluate import qlike

feat = add_ivar(build_features())

def ols_clip(feat, log_cols, lin_cols, log_target, mode="fallback", h=1):
    cols = list(log_cols) + list(lin_cols)
    d = pd.concat([feat[cols].shift(h), feat["rv"].rename("y")], axis=1).dropna()
    dates = d.index; nlog = len(log_cols); X = d[cols].to_numpy(float); y = d["y"].to_numpy(float)
    start = int(dates.searchsorted(pd.Timestamp(FIRST_OOS))); preds = np.full(len(d), np.nan)
    for i in range(start, len(d)):
        Xl = np.log(np.clip(X[:i, :nlog], EPS, None)) if nlog else np.empty((i, 0))
        A = np.column_stack([np.ones(i), Xl, X[:i, nlog:]])
        yt = np.log(np.clip(y[:i], EPS, None)) if log_target else y[:i]
        beta, *_ = np.linalg.lstsq(A, yt, rcond=None)
        xl = np.log(np.clip(X[i, :nlog], EPS, None)) if nlog else np.empty(0)
        yhat = float(np.concatenate([[1.0], xl, X[i, nlog:]]) @ beta)
        if log_target:
            yhat = float(np.exp(yhat + 0.5 * (yt - A @ beta).var()))
        hi = 4.0 * float(np.median(y[:i]))
        if not (MIN_VAR <= yhat <= hi):
            yhat = float(y[i - 1])            # BPQ fallback -> RW
        preds[i] = yhat
    return pd.DataFrame({"pred": preds, "actual": y}, index=dates).iloc[start:]

m = {
    "RW": _lag(feat, feat["rv"].shift(1), FIRST_OOS),
    "EWMA(0.94)": _lag(feat, feat["rv"].ewm(alpha=0.06, adjust=False).mean().shift(1), FIRST_OOS),
    "AR(1)-logRV": _expanding_ols(feat, ["rv_d"], FIRST_OOS, log=True),
    "log-HAR": _expanding_ols(feat, ["rv_d", "rv_w", "rv_m"], FIRST_OOS, log=True),
    "HAR-IV": ols_clip(feat, ["rv_d", "rv_w", "rv_m", "ivar"], [], True),
    "HAR": ols_clip(feat, [], ["rv_d", "rv_w", "rv_m"], False),
    "HAR-CJ": ols_clip(feat, [], ["c", "jump", "rv_w", "rv_m"], False),
    "HAR-RS": ols_clip(feat, [], ["rs_m", "rs_p", "rv_w", "rv_m"], False),
    "HARQ": ols_clip(feat, [], ["rv_d", "harq_x", "rv_w", "rv_m"], False),
    "LHAR": ols_clip(feat, [], ["rv_d", "rv_w", "rv_m", "ret_neg"], False),
}
m, idx = align(m)
a = m["RW"]["actual"].to_numpy()
ql = {k: qlike(a, np.clip(v["pred"].to_numpy(), MIN_VAR, None)) for k, v in m.items()}
print("filtered ladder QLIKE:")
for k, v in sorted(ql.items(), key=lambda kv: kv[1]):
    print(f"  {k:12s} {v:.4f}")
loss = pd.DataFrame({k: qloss(a, np.clip(m[k]["pred"].to_numpy(), MIN_VAR, None)) for k in m}, index=idx)
from arch.bootstrap import MCS
mcs = MCS(loss, size=0.10, reps=1000, block_size=10, method="R", seed=42); mcs.compute()
out = {"filtered_qlike": ql, "mcs_included_90": list(mcs.included),
       "mcs_pvalues": {k: float(v) for k, v in mcs.pvalues["Pvalue"].to_dict().items()}}
print("\nMCS included (90%, filtered ladder):", list(mcs.included))
print(mcs.pvalues.to_string())
json.dump(out, open("results/paper_fills_mcs.json", "w"), indent=2, default=float)
print("saved results/paper_fills_mcs.json")
