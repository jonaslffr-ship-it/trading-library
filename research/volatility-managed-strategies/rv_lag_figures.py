#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figures for the lag / spike-miss diagnostic (paper §Lag).
Panel A: calibration & spike-miss -- realized vs HAR-IV forecast RVol, 45-deg line,
         top-decile up-jump ('spike') days highlighted (they fall below the line).
Panel B: the spike-miss ladder -- mean actual/forecast on spike days, RW -> log-HAR
         -> HAR-IV -> +intraday nowcast. Features+IV cut it from ~4x to 2.5x; the
         morning nowcast only trims it to ~2.4x (an afternoon-emergent floor remains).
Output: figures/report/18_lag_spike.png . Reuses the exact harness + cached panel. Seed 42."""
from __future__ import annotations
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from analyze import _ols, FIRST_OOS, MIN_VAR

ACC, INK, BLUE, GREEN, MUT = "#7c1c2c", "#211c18", "#2b4a63", "#2f6d4f", "#9b9b9b"
plt.rcParams.update({"figure.dpi": 130, "font.family": "serif", "axes.titlesize": 11,
                     "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "legend.fontsize": 8, "axes.spines.top": False, "axes.spines.right": False})
OUT = "figures/report_en"; os.makedirs(OUT, exist_ok=True)  # published-paper figure set (English)

feat = pd.read_parquet("results/_improve_panel.parquet")
mrv = pd.read_parquet("results/_morning_rv.parquet")
feat["op60_now"] = mrv["op60"].reindex(feat.index).shift(-1)

HARIV = ["rv_d", "rv_w", "rv_m", "ivar"]
models = {
    "RW":        pd.DataFrame({"pred": feat["rv"].shift(1), "actual": feat["rv"]}).dropna().loc[lambda d: d.index >= FIRST_OOS],
    "log-HAR":   _ols(feat, ["rv_d", "rv_w", "rv_m"], [], FIRST_OOS, log_target=True),
    "HAR-IV":    _ols(feat, HARIV, [], FIRST_OOS, log_target=True),
    "+Nowcast":  _ols(feat, HARIV, ["op60_now"], FIRST_OOS, log_target=True),
}

def spike_x(df):
    d = df.dropna(); a = d["actual"].to_numpy(); p = np.clip(d["pred"].to_numpy(), MIN_VAR, None)
    r = a[1:] / a[:-1]; m = r >= np.quantile(r, 0.90)
    return float(np.mean(a[1:][m] / p[1:][m])), m

fig, (axA, axB) = plt.subplots(1, 2, figsize=(9.2, 3.7), gridspec_kw={"width_ratios": [1.15, 1]})

# ---- Panel A: calibration / spike-miss (HAR-IV) ----
h = models["HAR-IV"].dropna()
a = h["actual"].to_numpy(); p = np.clip(h["pred"].to_numpy(), MIN_VAR, None)
av = lambda x: np.sqrt(x * 252) * 100        # -> annualized RVol %
ax_, ay_ = av(p), av(a)                       # x = forecast, y = realized
_, sm = spike_x(models["HAR-IV"])
sm_full = np.concatenate([[False], sm])       # align to full arrays
axA.scatter(ax_[~sm_full], ay_[~sm_full], s=5, color=MUT, alpha=.35, edgecolors="none", label="normal days")
axA.scatter(ax_[sm_full], ay_[sm_full], s=9, color=ACC, alpha=.75, edgecolors="none", label="spike days (top-decile up-jump)")
lim = [av(MIN_VAR)*1, max(ay_.max(), ax_.max())*1.05]
axA.plot([4, 130], [4, 130], color=INK, lw=0.9, ls="--", label="perfect (45°)")
axA.set_xscale("log"); axA.set_yscale("log"); axA.set_xlim(6, 130); axA.set_ylim(6, 130)
axA.set_xlabel("HAR-IV forecast RVol p.a. (%)"); axA.set_ylabel("realized RVol p.a. (%)")
axA.set_title("A · Calibrated on average, blind to spikes")
axA.legend(loc="upper left", frameon=False)
axA.annotate("spike days sit ABOVE the line:\nforecast underestimates by ~2.5×",
             xy=(12, 40), xytext=(20, 6.8), fontsize=7.5, color=ACC, ha="left",
             arrowprops=dict(arrowstyle="->", color=ACC, lw=0.7))

# ---- Panel B: the spike-miss ladder ----
order = ["RW", "log-HAR", "HAR-IV", "+Nowcast"]
vals = [spike_x(models[k])[0] for k in order]
cols = [MUT, BLUE, INK, ACC]
bars = axB.bar(order, vals, color=cols, width=0.62)
axB.axhline(1.0, color=GREEN, lw=1.0, ls=":")
axB.text(3.35, 1.06, "no miss (1.0×)", color=GREEN, fontsize=7, ha="right")
for b, v in zip(bars, vals):
    axB.text(b.get_x() + b.get_width()/2, v + 0.06, f"{v:.2f}×", ha="center", fontsize=8.5, color=INK)
axB.set_ylim(0, 4.5); axB.set_ylabel("mean realized / forecast on spike days")
axB.set_title("B · The spike-miss ladder (lower = less lag)")
axB.tick_params(axis="x", labelrotation=0)

fig.suptitle("Lag diagnostics: the forecast is well-calibrated on average; the residual 'lag' is the spike underestimation",
             fontsize=9.5, y=1.02)
fig.tight_layout()
fig.savefig(f"{OUT}/18_lag_spike.png", bbox_inches="tight")
print(f"saved {OUT}/18_lag_spike.png | spike_x:", {k: round(v, 2) for k, v in zip(order, vals)})
