#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quantify the 'lagging forecast' impression: Mincer-Zarnowitz slope, error
autocorrelation, lead-lag phase, underreaction test, and spike miss-ratio.
Reuses the exact harness. Panel from _build_panel.py. Seed 42."""
from __future__ import annotations
import numpy as np, pandas as pd, statsmodels.api as sm
from analyze import _ols, FIRST_OOS, MIN_VAR

feat = pd.read_parquet("results/_improve_panel.parquet")
HARIV = ["rv_d", "rv_w", "rv_m", "ivar"]
mods = {
    "RW": pd.DataFrame({"pred": feat["rv"].shift(1), "actual": feat["rv"]}).dropna().loc[lambda d: d.index >= FIRST_OOS],
    "log-HAR": _ols(feat, ["rv_d", "rv_w", "rv_m"], [], FIRST_OOS, log_target=True),
    "HAR-IV": _ols(feat, HARIV, [], FIRST_OOS, log_target=True),
    "C4 GLM+slope": None,  # filled below (needs glm) -> skip, use C2 proxy
    "C2 Rich+slope": _ols(feat, ["rv_d","rv_w","rv_m","bv","rq","rs_m","rs_p","jump","ivar"], ["ret_neg","ivslope"], FIRST_OOS, log_target=True),
}
mods.pop("C4 GLM+slope")

print(f"{'model':16s} {'MZ_b':>6s} {'err_AC1':>8s} {'corr_t0':>8s} {'corr_t1':>8s} {'under_t':>8s} {'spike_x':>8s}")
print("-"*68)
for name, df in mods.items():
    d = df.dropna()
    a = d["actual"].to_numpy(float)
    p = np.clip(d["pred"].to_numpy(float), MIN_VAR, None)
    # 1) Mincer-Zarnowitz slope: actual = a0 + b*pred  (b<1 => damped/too smooth)
    mz = sm.OLS(a, sm.add_constant(p)).fit(cov_type="HAC", cov_kwds={"maxlags": 10})
    b = mz.params[1]
    # 2) error autocorrelation lag-1 (log scale, robust); >0 => persistent misses
    e = np.log(a) - np.log(p)
    ac1 = np.corrcoef(e[1:], e[:-1])[0, 1]
    # 3) lead-lag phase: corr(pred_t, actual_t) vs corr(pred_t, actual_{t-1})  (log)
    la = np.log(a); lp = np.log(p)
    c0 = np.corrcoef(lp, la)[0, 1]                   # contemporaneous (what it predicts)
    c1 = np.corrcoef(lp[1:], la[:-1])[0, 1]          # pred_t vs actual_{t-1} (yesterday)
    # 4) underreaction: today's log-error on YESTERDAY's log-RV change (properly lagged)
    dlag = la[1:-1] - la[:-2]                         # d log RV_{t-1}
    et = e[2:]                                        # error at t
    ur = sm.OLS(et, sm.add_constant(dlag)).fit(cov_type="HAC", cov_kwds={"maxlags": 10})
    ut = ur.params[1] / ur.bse[1]
    # 5) spike miss: on top-decile up-jump days (actual/actual_{t-1}), mean actual/pred
    ratio = a[1:] / a[:-1]
    mask = ratio >= np.quantile(ratio, 0.90)
    spike_x = float(np.mean(a[1:][mask] / p[1:][mask]))
    print(f"{name:16s} {b:6.2f} {ac1:8.3f} {c0:8.3f} {c1:8.3f} {ut:8.2f} {spike_x:8.2f}")

print("""
Legende:
 MZ_b     Mincer-Zarnowitz-Steigung (actual~pred). 1.0=ideal, <1=Prognose zu gedaempft.
 err_AC1  Autokorrelation der log-Fehler (Lag 1). ~0=effizient, >0=systematische Nachlauf-Misses.
 phase    Womit korreliert die Prognose staerker: actual_t (t-0) oder actual_{t-1} (t-1=Nachlauf).
 under_t  t-Stat: sagt gestrige RV-Aenderung den heutigen Fehler voraus? >2 = Unterreaktion/Lag.
 spike_x  Mittleres actual/pred an Top-10%-Aufwaerts-Sprungtagen. >>1 = Spike massiv unterschaetzt.
""")
