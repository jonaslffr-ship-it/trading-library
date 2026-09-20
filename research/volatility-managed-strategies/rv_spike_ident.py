#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Identify how much of the spike-miss is a real model defect vs. a mechanical artifact of
selecting on the realized outcome.

The spike_x statistic (mean realized/forecast on top-decile up-jump days) conditions on the
REALIZED jump, so even a perfect conditional-mean forecaster shows spike_x > 1 (regression to
the mean under a right-skewed conditional law). Two clean checks:

  (1) IRREDUCIBLE FLOOR via DGP simulation. Treat the HAR-IV forecast p_t as the true conditional
      mean and draw realized RV from the lognormal implied by the empirical log-error variance
      (E[a]=p_t). Recompute spike_x on the *simulated* series. Its distribution is what a PERFECT
      forecaster mechanically produces. Compare the observed spike_x to it.
  (2) FORECAST-DECILE CALIBRATION. Bin days by the FORECAST (not the outcome); report
      mean(realized)/mean(forecast) per decile — the honest calibration curve, esp. the top bin.

Also: upper-tail coverage — P(realized > forecast's 90th predictive percentile). Seed 42.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from analyze import _ols, FIRST_OOS, MIN_VAR

rng = np.random.RandomState(42)
feat = pd.read_parquet("results/_improve_panel.parquet")
HARIV = ["rv_d", "rv_w", "rv_m", "ivar"]
base = _ols(feat, HARIV, [], FIRST_OOS, log_target=True).dropna()
a = base["actual"].to_numpy(float)
p = np.clip(base["pred"].to_numpy(float), MIN_VAR, None)

def spike_x(actual, pred):
    r = actual[1:] / actual[:-1]
    m = r >= np.quantile(r, 0.90)
    return float(np.mean(actual[1:][m] / pred[1:][m]))

obs = spike_x(a, p)

# --- (1) irreducible floor: simulate realized under a PERFECT conditional-mean forecaster ---
e = np.log(a) - np.log(p)                 # log errors
sig = float(np.std(e))                    # empirical predictive sd on the log scale
# lognormal with E[a_sim]=p_t  =>  a_sim = p * exp(z*sig - sig^2/2)
sims = []
for _ in range(3000):
    z = rng.standard_normal(len(p))
    a_sim = p * np.exp(z * sig - 0.5 * sig ** 2)
    sims.append(spike_x(a_sim, p))
sims = np.array(sims)
lo, hi, mean_sim = np.percentile(sims, 2.5), np.percentile(sims, 97.5), sims.mean()
frac_above = float(np.mean(sims >= obs))

print("=== Spike-miss identification (HAR-IV, OOS) ===")
print(f"observed spike_x                       : {obs:.2f}")
print(f"irreducible floor (perfect forecaster) : {mean_sim:.2f}  [95% {lo:.2f}, {hi:.2f}]")
print(f"P(simulated >= observed)               : {frac_above:.3f}")
excess = obs - mean_sim
print(f"=> real excess over the mechanical floor: {excess:+.2f}  "
      f"({'within noise — mostly mechanical' if lo <= obs <= hi else 'genuine residual under-reaction'})")

# --- (2) calibration by FORECAST decile (not outcome) ---
print("\n=== Calibration by FORECAST decile: mean(realized)/mean(forecast) ===")
dec = pd.qcut(p, 10, labels=False)
rows = []
for d in range(10):
    mm = dec == d
    rows.append((d + 1, np.sqrt(np.mean(p[mm]) * 252) * 100, float(np.mean(a[mm]) / np.mean(p[mm])), int(mm.sum())))
cal = pd.DataFrame(rows, columns=["fc_decile", "fc_RVol%", "real/fc", "n"])
print(cal.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
top = cal.iloc[-1]
print(f"\nTop forecast-decile calibration: E[realized]/forecast = {top['real/fc']:.2f} "
      f"(1.0 = calibrated on the days the model itself calls high-vol)")

# --- (3) upper-tail coverage under the lognormal predictive ---
q90 = p * np.exp(1.2816 * sig - 0.5 * sig ** 2)   # 90th pct of the predictive (approx)
cov = float(np.mean(a > q90))
print(f"\nUpper-tail coverage: realized exceeds the 90th predictive pct on {cov:.1%} of days "
      f"(well-calibrated ~10%; >10% = tail too thin / under-dispersed).")

# --- (4) Mincer-Zarnowitz JOINT unbiasedness test (a=0, b=1), HAC ---
import statsmodels.api as sm
mz = sm.OLS(a, sm.add_constant(p)).fit(cov_type="HAC", cov_kwds={"maxlags": 10})
R = np.array([[1.0, 0.0], [0.0, 1.0]]); q = np.array([0.0, 1.0])   # H0: intercept=0 AND slope=1
w = mz.f_test((R, q))
print(f"\nMincer-Zarnowitz joint test (a=0, b=1): intercept {mz.params[0]:+.5f}, slope {mz.params[1]:.3f}, "
      f"F p={float(w.pvalue):.3f}  ({'not rejected -> unbiased' if float(w.pvalue)>0.05 else 'rejected -> biased'})")
