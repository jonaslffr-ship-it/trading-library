#!/usr/bin/env python3
"""Paper fills — FORECAST side, FAST part.
  F1  full ladder QLIKE/MSE/R2 (fills HAR-IV MSE/R2) + save per-obs loss matrix
  F2  Model Confidence Set (Hansen-Lunde-Nason) via arch.bootstrap
  F3  Newey-West inference for h=5,22 (overlapping errors)
  F4  Insanity-filter toggle on HARQ/HAR-CJ/LHAR (none / 4x-clip / BPQ-fallback)
  F5  Retransform recursivity + bias-correction sensitivity
"""
from __future__ import annotations
import os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd

from analyze import (build_features, _expanding_ols, _ols, _lag, FIRST_OOS,
                     EPS, MIN_VAR, qloss, metrics, align)
from ml_models import add_ivar
from src.evaluate import qlike, mse, diebold_mariano, clark_west

OUT = {}
feat = add_ivar(build_features())
print("features:", feat.shape, "cols:", list(feat.columns), flush=True)

# ================================================================ F1 ladder
print("\n### F1  ladder QLIKE/MSE/R2", flush=True)
m1 = {
    "RW": _lag(feat, feat["rv"].shift(1), FIRST_OOS),
    "EWMA(0.94)": _lag(feat, feat["rv"].ewm(alpha=0.06, adjust=False).mean().shift(1), FIRST_OOS),
    "AR(1)-logRV": _expanding_ols(feat, ["rv_d"], FIRST_OOS, log=True),
    "HAR": _expanding_ols(feat, ["rv_d", "rv_w", "rv_m"], FIRST_OOS, log=False),
    "log-HAR": _expanding_ols(feat, ["rv_d", "rv_w", "rv_m"], FIRST_OOS, log=True),
    "HAR-CJ": _expanding_ols(feat, ["c", "jump", "rv_w", "rv_m"], FIRST_OOS, log=False),
    "HAR-RS": _ols(feat, [], ["rs_m", "rs_p", "rv_w", "rv_m"], FIRST_OOS, log_target=False),
    "HARQ": _ols(feat, [], ["rv_d", "harq_x", "rv_w", "rv_m"], FIRST_OOS, log_target=False),
    "LHAR": _ols(feat, [], ["rv_d", "rv_w", "rv_m", "ret_neg"], FIRST_OOS, log_target=False),
    "HAR-IV": _ols(feat, ["rv_d", "rv_w", "rv_m", "ivar"], [], FIRST_OOS, log_target=True),
}
m1, idx1 = align(m1)
a1 = m1["RW"]["actual"].to_numpy(); prw1 = m1["RW"]["pred"].to_numpy()
print(f"common OOS obs: {len(idx1)}  {idx1.min().date()}->{idx1.max().date()}")
ladder = {}
for name, dfm in m1.items():
    ladder[name] = metrics(a1, dfm["pred"].to_numpy(), prw1)
OUT["ladder"] = ladder
print(pd.DataFrame(ladder).T.to_string(float_format=lambda x: f"{x:.5f}"))

# per-obs QLIKE loss matrix (for MCS + reuse by ML script)
loss = pd.DataFrame({name: qloss(a1, np.clip(m1[name]["pred"].to_numpy(), MIN_VAR, None))
                     for name in m1}, index=idx1)
loss.to_parquet("results/loss_matrix_classical.parquet")
print("saved results/loss_matrix_classical.parquet", loss.shape)

# ================================================================ F2 MCS
print("\n### F2  Model Confidence Set (HLN)", flush=True)
try:
    from arch.bootstrap import MCS
    mcs = MCS(loss, size=0.10, reps=1000, block_size=10, method="R", seed=42)
    mcs.compute()
    inc = list(mcs.included); exc = list(mcs.excluded)
    pvals = mcs.pvalues["Pvalue"].to_dict()
    OUT["mcs"] = {"included_90": inc, "excluded_90": exc, "pvalues": {k: float(v) for k, v in pvals.items()}}
    print("included (90%):", inc)
    print("excluded (90%):", exc)
    print(mcs.pvalues.to_string())
except Exception as e:
    print("MCS via arch failed, fallback max-t:", e)
    # manual max-t elimination MCS
    def mcs_maxt(L, alpha=0.10, B=1000, block=10, seed=42):
        rng = np.random.RandomState(seed); T, M = L.shape; cols = list(L.columns); Lv = L.values
        nb = int(np.ceil(T/block)); idxs = [np.concatenate([np.arange(s, s+block) for s in rng.randint(0, T-block+1, nb)])[:T] for _ in range(B)]
        alive = list(range(M))
        while len(alive) > 1:
            sub = Lv[:, alive]; dbar = sub.mean(0); dij = dbar[:, None] - dbar[None, :]
            # bootstrap se of pairwise mean diffs
            boot = np.array([sub[ix].mean(0) for ix in idxs])
            var = boot.var(0) + 1e-12
            t = (dbar - dbar.mean()) / np.sqrt(var)  # relative to set mean
            Tmax = t.max()
            bt = (boot - boot.mean(1, keepdims=True)) / np.sqrt(var)
            bmax = bt.max(1); p = (bmax > Tmax).mean()
            if p > alpha: break
            worst = alive[int(np.argmax(t))]; alive.remove(worst)
        return [cols[i] for i in alive]
    inc = mcs_maxt(loss); OUT["mcs"] = {"included_90": inc, "method": "manual-maxt"}
    print("included (90%, manual):", inc)

# ================================================================ F3 Newey-West h=5,22
print("\n### F3  Newey-West inference at h=5,22", flush=True)
nw = {}
for h in (5, 22):
    mh, _ = align({
        "RW": _lag(feat, feat["rv"].shift(h), FIRST_OOS),
        "HAR": _expanding_ols(feat, ["rv_d", "rv_w", "rv_m"], FIRST_OOS, log=False, h=h),
        "log-HAR": _expanding_ols(feat, ["rv_d", "rv_w", "rv_m"], FIRST_OOS, log=True, h=h),
    })
    a = mh["RW"]["actual"].to_numpy(); prw = mh["RW"]["pred"].to_numpy()
    for nm in ("HAR", "log-HAR"):
        p = mh[nm]["pred"].to_numpy()
        # Clark-West with NW lag >= h-1 (clark_west uses maxlags=10; recompute t with explicit lag)
        f_hat = (a - prw) ** 2 - ((a - p) ** 2 - (prw - p) ** 2)
        import statsmodels.api as sm
        res = sm.OLS(f_hat, np.ones((len(f_hat), 1))).fit(cov_type="HAC", cov_kwds={"maxlags": max(h - 1, 10)})
        from scipy.stats import norm
        t = float(res.params[0] / res.bse[0]); pval = float(1 - norm.cdf(t))
        r2 = 1 - np.sum((a - p) ** 2) / np.sum((a - prw) ** 2)
        nw[f"{nm}_h{h}"] = {"CW_t": t, "CW_p_1s": pval, "R2_OOS": float(r2), "nw_lag": max(h - 1, 10), "n": len(a)}
        print(f"  h={h:2d} {nm:8s} CW t={t:5.2f} p={pval:.4f} R2={r2:.3f} (NW lag {max(h-1,10)})")
OUT["nw_horizons"] = nw

# ================================================================ F4 insanity toggle
print("\n### F4  insanity-filter toggle (HARQ / HAR-CJ / LHAR)", flush=True)
def ols_clip(feat, log_cols, lin_cols, first_oos, log_target, mode, h=1):
    cols = list(log_cols) + list(lin_cols)
    d = pd.concat([feat[cols].shift(h), feat["rv"].rename("y")], axis=1).dropna()
    dates = d.index; nlog = len(log_cols)
    X = d[cols].to_numpy(float); y = d["y"].to_numpy(float)
    start = int(dates.searchsorted(pd.Timestamp(first_oos))); preds = np.full(len(d), np.nan)
    for i in range(start, len(d)):
        Xl = np.log(np.clip(X[:i, :nlog], EPS, None)) if nlog else np.empty((i, 0))
        A = np.column_stack([np.ones(i), Xl, X[:i, nlog:]])
        yt = np.log(np.clip(y[:i], EPS, None)) if log_target else y[:i]
        beta, *_ = np.linalg.lstsq(A, yt, rcond=None)
        xl = np.log(np.clip(X[i, :nlog], EPS, None)) if nlog else np.empty(0)
        yhat = float(np.concatenate([[1.0], xl, X[i, nlog:]]) @ beta)
        if log_target:
            yhat = float(np.exp(yhat + 0.5 * (yt - A @ beta).var()))
        if mode == "none":
            pass
        elif mode == "bpq4x":
            yhat = min(max(yhat, MIN_VAR), 4.0 * float(y[:i].max()))
        elif mode == "fallback":
            hi = 4.0 * float(np.median(y[:i]))                      # BPQ: implausible -> fallback
            if not (MIN_VAR <= yhat <= hi):
                yhat = float(y[i - 1])                              # fallback to RW (last obs)
        preds[i] = yhat
    return pd.DataFrame({"pred": preds, "actual": y}, index=dates).iloc[start:]

flt = {}
specs = {"HARQ": ([], ["rv_d", "harq_x", "rv_w", "rv_m"]),
         "HAR-CJ": ([], ["c", "jump", "rv_w", "rv_m"]),
         "LHAR": ([], ["rv_d", "rv_w", "rv_m", "ret_neg"])}
for nm, (lc, rc) in specs.items():
    flt[nm] = {}
    for mode in ("none", "bpq4x", "fallback"):
        dfm = ols_clip(feat, lc, rc, FIRST_OOS, False, mode)
        dd = dfm.dropna()
        flt[nm][mode] = float(qlike(dd["actual"].to_numpy(), np.clip(dd["pred"].to_numpy(), MIN_VAR, None)))
    print(f"  {nm:7s} QLIKE  none={flt[nm]['none']:.3f}  4xclip={flt[nm]['bpq4x']:.3f}  fallback={flt[nm]['fallback']:.3f}")
OUT["insanity_toggle"] = flt

# ================================================================ F5 retransform sensitivity
print("\n### F5  retransform bias-correction sensitivity", flush=True)
def logHAR_qlike(bias):
    cols = ["rv_d", "rv_w", "rv_m"]
    d = pd.concat([feat[cols].shift(1), feat["rv"].rename("y")], axis=1).dropna()
    dates = d.index; X = d[cols].to_numpy(float); y = d["y"].to_numpy(float)
    start = int(dates.searchsorted(pd.Timestamp(FIRST_OOS))); preds = np.full(len(d), np.nan)
    for i in range(start, len(d)):
        A = np.column_stack([np.ones(i), np.log(np.clip(X[:i], EPS, None))])
        yt = np.log(np.clip(y[:i], EPS, None))
        beta, *_ = np.linalg.lstsq(A, yt, rcond=None)
        s2 = (yt - A @ beta).var() if bias else 0.0     # recursive (train-window) residual var
        yhat = float(np.exp(np.concatenate([[1.0], np.log(np.clip(X[i], EPS, None))]) @ beta + 0.5 * s2))
        preds[i] = min(max(yhat, MIN_VAR), 4.0 * float(y[:i].max()))
    dd = pd.DataFrame({"pred": preds, "actual": y}, index=dates).iloc[start:].dropna()
    return float(qlike(dd["actual"].to_numpy(), dd["pred"].to_numpy()))
q_bias = logHAR_qlike(True); q_nobias = logHAR_qlike(False)
OUT["retransform"] = {"logHAR_QLIKE_with_bias": q_bias, "logHAR_QLIKE_no_bias": q_nobias,
                      "recursive": True, "note": "sigma^2 from (ytr - A@beta) on [:i] = training window only"}
print(f"  log-HAR QLIKE  with bias corr={q_bias:.4f}  without={q_nobias:.4f}  (recursive, train-window sigma^2)")

with open("results/paper_fills_fc.json", "w", encoding="utf-8") as fh:
    json.dump(OUT, fh, indent=2, default=float)
print("\nsaved results/paper_fills_fc.json")
