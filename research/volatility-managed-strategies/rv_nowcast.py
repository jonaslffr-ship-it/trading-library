#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Intraday nowcast: does 'RV so far' (first 30/60 min of the session) predict the
FULL RTH realized variance of the SAME day, and does it fix the spike-lag (the 2.5x
underestimation of top-decile up-jump days that day-ahead HAR-IV leaves on the table)?

Forecast origin = 10:00 / 10:30 ET (after the first 30 / 60 one-minute bars).
Leakage-free: the morning-RV of day t uses ONLY bars inside [open, open+30/60min];
the target is the full-session 5-min RV of day t. Same shift(-1) trick as rv_overnight.py
(cancels _ols's internal shift(1) -> a same-day value at t).

Everything else identical to the paper harness. Baseline = HAR-IV (day-ahead). Seed 42.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from analyze import _ols, FIRST_OOS, MIN_VAR
from src.ingest import load_days
from src.evaluate import qlike, mse, clark_west

# ---- 1) daily panel (rv, HAR-IV features, ivar) from the cached improvement panel ----
feat = pd.read_parquet("results/_improve_panel.parquet")

# ---- 2) morning 'RV so far' from raw 1-minute bars (first 30 / 60 minutes) ----
def morning_rv(raw_dir="data/raw", n_list=(30, 60)):
    """Per-day realized variance of the first N one-minute returns (RV-so-far)."""
    px = load_days(raw_dir)                    # UTC-indexed 1-min close series, RTH only
    out = {f"op{n}": {} for n in n_list}
    ncov = {f"op{n}": {} for n in n_list}      # #returns actually used (coverage guard)
    for day, g in px.groupby(px.index.date):
        c = g.sort_index().to_numpy(float)
        lr = np.diff(np.log(c))                # one-minute log returns, in session order
        for n in n_list:
            seg = lr[:n]
            out[f"op{n}"][day] = float(np.sum(seg ** 2)) if len(seg) >= max(10, n // 2) else np.nan
            ncov[f"op{n}"][day] = len(seg)
    df = pd.DataFrame(out)
    df.index = pd.to_datetime(df.index)
    return df.sort_index()

import os
_CACHE = "results/_morning_rv.parquet"
if os.path.exists(_CACHE):
    mrv = pd.read_parquet(_CACHE)
else:
    mrv = morning_rv()
    mrv.to_parquet(_CACHE)
# align onto the panel's daily index, then apply the same-day (nowcast) shift(-1) trick
for c in ["op30", "op60"]:
    s = mrv[c].reindex(feat.index)
    feat[c + "_now"] = s.shift(-1)             # value at t, placed so _ols's shift(1) recovers t

# overnight |gap| nowcast column (mirror rv_overnight.py), for the combo row
ohlc = pd.read_parquet("data/processed/ohlc_SPX.parquet")
ret_on = (np.log(ohlc["open"]) - np.log(ohlc["close"].shift(1))).reindex(feat.index)
feat["ov_abs_now"] = ret_on.abs().shift(-1)

# ---- 3) evaluate: HAR-IV baseline + intraday-so-far nowcasts (nested Clark-West) ----
HARIV = ["rv_d", "rv_w", "rv_m", "ivar"]
base = _ols(feat, HARIV, [], FIRST_OOS, log_target=True)

def spike_mask_ratio(a):
    r = a[1:] / a[:-1]
    return r >= np.quantile(r, 0.90)

def spike_x(df):
    d = df.dropna(); a = d["actual"].to_numpy(); p = np.clip(d["pred"].to_numpy(), MIN_VAR, None)
    m = spike_mask_ratio(a)
    return float(np.mean(a[1:][m] / p[1:][m]))

def ev(name, cand):
    idx = base.index.intersection(cand.index)
    a  = base.loc[idx, "actual"].to_numpy()
    pb = np.clip(base.loc[idx, "pred"].to_numpy(), MIN_VAR, None)
    pc = np.clip(cand.loc[idx, "pred"].to_numpy(), MIN_VAR, None)
    _, cw = clark_west(a, pb, pc)
    return {"model": name, "QLIKE": qlike(a, pc),
            "dQLIKE%": 100 * (qlike(a, pc) - qlike(a, pb)) / qlike(a, pb),
            "CW_p": cw, "spike_x": spike_x(cand.loc[idx])}

cands = [
    ("HAR-IV (baseline, day-ahead)",          base),
    ("+ RV-so-far 30min  (NOWCAST)",          _ols(feat, HARIV, ["op30_now"], FIRST_OOS, log_target=True)),
    ("+ RV-so-far 60min  (NOWCAST)",          _ols(feat, HARIV, ["op60_now"], FIRST_OOS, log_target=True)),
    ("+ RV-so-far 60min + |gap| (NOWCAST)",   _ols(feat, HARIV, ["op60_now", "ov_abs_now"], FIRST_OOS, log_target=True)),
]

rows = [ev(n, c) for n, c in cands]
tab = pd.DataFrame(rows).set_index("model")
bq = qlike(base["actual"].to_numpy(), np.clip(base["pred"].to_numpy(), MIN_VAR, None))
print(f"baseline HAR-IV QLIKE {bq:.4f}  |  Bonferroni thr (k=3) = {0.05/3:.4f}\n")
print(tab.to_string(float_format=lambda x: f"{x:.4f}"))

# ---- 4) WHY: is the spike already visible in the morning? (the reviewer's hypothesis) ----
d = feat[["rv", "op30_now", "op60_now"]].dropna()
d = d[d.index >= pd.Timestamp(FIRST_OOS)]
a = d["rv"].to_numpy()
m = spike_mask_ratio(a)                                   # top-decile up-jump days (t vs t-1)
print("\n--- Nowcast signal on the FULL sample (OOS) ---")
print(f"corr(log op60_morning, log full-day RV):            {np.corrcoef(np.log(d['op60_now']), np.log(a))[0,1]:.3f}")
print(f"corr(log op30_morning, log full-day RV):            {np.corrcoef(np.log(d['op30_now']), np.log(a))[0,1]:.3f}")
print("\n--- On the spike days (the 2.5x lag) ---")
op60 = d["op60_now"].to_numpy()
# scale-free: percentile rank of each day's morning RV within the OOS sample (0..1)
pct = pd.Series(op60).rank(pct=True).to_numpy()
op60_sp = op60[1:][m]; rv_sp = a[1:][m]; rv_prev = a[:-1][m]
print(f"spike days: n={m.sum()}")
print(f"  mean full-day RV / prev-day RV (the jump):        {np.mean(rv_sp / rv_prev):.2f}x")
print(f"  median morning-RV percentile on spike days:       {np.median(pct[1:][m]):.2f}   (0.50 = typical; >0.5 => morning already hot)")
print(f"  share of spike days whose morning is BELOW median: {np.mean(pct[1:][m] < 0.5):.0%}")
print(f"  corr(log morning60, log full-day RV) on spikes:   {np.corrcoef(np.log(op60_sp), np.log(rv_sp))[0,1]:.3f}")
print("""
Reading:
 If '+RV-so-far' lowers spike_x a lot AND morning-RV is already elevated on spike days,
 intraday nowcasting is the real lag-killer (reviewer's claim). If spike_x barely moves,
 the worst spikes emerge AFTER the first hour -> not even a nowcast catches them.
""")
