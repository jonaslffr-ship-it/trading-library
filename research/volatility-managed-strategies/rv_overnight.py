#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Does overnight variance help predict the day's RV?
Two setups, both vs HAR-IV baseline (nested Clark-West):
  (weak)  day-ahead : overnight_{t-1} -> rv_t   [= screening H3, ~null]
  (strong) nowcast  : overnight_t     -> rv_t   [forecast origin = the OPEN; new info]
Trick: a lin-col shifted -1 cancels _ols's internal shift(1), so overnight_t predicts rv_t
(leakage-free: the gap close_{t-1}->open_t is known at 09:30, before the RTH session).
Also: how much total risk does RTH-only RV throw away? Seed 42."""
from __future__ import annotations
import numpy as np, pandas as pd
from analyze import _ols, FIRST_OOS, MIN_VAR
from src.evaluate import qlike, mse, clark_west

feat = pd.read_parquet("results/_improve_panel.parquet")
ohlc = pd.read_parquet("data/processed/ohlc_SPX.parquet")

# overnight log-return and its variance / down-gap semivariance / abs-gap (less noisy)
ret_on = (np.log(ohlc["open"]) - np.log(ohlc["close"].shift(1))).reindex(feat.index)
feat["ov"]      = ret_on ** 2                       # overnight variance (very noisy: 1 obs)
feat["ov_neg"]  = (ret_on.clip(upper=0.0)) ** 2     # down-gap only (leverage)
feat["ov_abs"]  = ret_on.abs()                       # |gap| (robuster als r^2)
# same-day (nowcast) versions: shift(-1) cancels _ols shift(1) -> value at t
for c in ["ov", "ov_neg", "ov_abs"]:
    feat[c + "_now"] = feat[c].shift(-1)

HARIV = ["rv_d", "rv_w", "rv_m", "ivar"]
base = _ols(feat, HARIV, [], FIRST_OOS, log_target=True)
a0 = base["actual"].to_numpy(); p0 = np.clip(base["pred"].to_numpy(), MIN_VAR, None)
bq = qlike(a0, p0)

def spike_x(df):
    d = df.dropna(); a = d["actual"].to_numpy(); p = np.clip(d["pred"].to_numpy(), MIN_VAR, None)
    r = a[1:] / a[:-1]; m = r >= np.quantile(r, 0.90)
    return float(np.mean(a[1:][m] / p[1:][m]))

def ev(name, cand):
    idx = base.index.intersection(cand.index)
    a = base.loc[idx, "actual"].to_numpy()
    pb = np.clip(base.loc[idx, "pred"].to_numpy(), MIN_VAR, None)
    pc = np.clip(cand.loc[idx, "pred"].to_numpy(), MIN_VAR, None)
    _, cw = clark_west(a, pb, pc)
    return {"model": name, "QLIKE": qlike(a, pc), "dQLIKE%": 100*(qlike(a, pc)-qlike(a, pb))/qlike(a, pb),
            "dMSE_1e8": (mse(a, pc)-mse(a, pb))*1e8, "CW_p": cw, "spike_x": spike_x(cand)}

cands = [
    ("HAR-IV (baseline day-ahead)", base),
    ("+ overnight_{t-1}  (day-ahead, weak)", _ols(feat, HARIV+["ov"], [], FIRST_OOS, log_target=True)),
    ("+ overnight_t      (NOWCAST, var)",    _ols(feat, HARIV, ["ov_now"], FIRST_OOS, log_target=True)),
    ("+ |overnight_t|    (NOWCAST, abs)",    _ols(feat, HARIV, ["ov_abs_now"], FIRST_OOS, log_target=True)),
    ("+ down-gap_t^2     (NOWCAST, lev)",    _ols(feat, HARIV, ["ov_neg_now"], FIRST_OOS, log_target=True)),
    ("+ |gap_t| & down-gap_t (NOWCAST)",     _ols(feat, HARIV, ["ov_abs_now","ov_neg_now"], FIRST_OOS, log_target=True)),
]
rows = [ev(n, c) for n, c in cands]
tab = pd.DataFrame(rows).set_index("model")
print(f"baseline HAR-IV QLIKE {bq:.4f}  |  Bonferroni thr (k=5) = {0.05/5:.4f}\n")
print(tab.to_string(float_format=lambda x: f"{x:.4f}"))

# how much risk does RTH-only RV discard?
d = feat[["rv","ov"]].dropna()
share = d["ov"] / (d["ov"] + d["rv"])
print(f"\nOvernight-Anteil an Gesamtvarianz (ov / (ov+rv)):  Median {share.median():.1%} | Mittel {share.mean():.1%}")
print(f"Anteil Tage, an denen Overnight > 30% der Gesamtvarianz: {(share>0.30).mean():.1%}")
print("Interpretation: RTH-only-RV ignoriert diesen Anteil des echten Tagesrisikos.")
