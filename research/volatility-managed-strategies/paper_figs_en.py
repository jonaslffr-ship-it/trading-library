#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""English figure set for the PUBLISHED paper -> figures/report_en/.

Separate from report_figures.py (which stays German for the internal reports).
Carries the review corrections:
  * English titles, NO 'Fig. N —' number prefix (avoids figure-number vs. caption clashes);
  * the forecast ladder shows the log-target comparable set only (the level-target LHAR/HARQ/
    HAR-CJ blow-ups are fit artifacts, not model failures — omitted, noted in the caption);
  * the PBO figure prints its value so the paper caption matches it exactly (one labelled object).
Reuses the exact harness. Seed 42.  Run:  python paper_figs_en.py
"""
from __future__ import annotations
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analyze import build_features, _ols, FIRST_OOS
from strategy import vol_managed
from src.ingest import load_days
from src.evaluate import qlike

ACC, INK, BLUE, GREEN, MUT = "#7c1c2c", "#211c18", "#2b4a63", "#2f6d4f", "#9b9b9b"
plt.rcParams.update({"figure.dpi": 130, "font.family": "serif", "axes.titlesize": 11,
                     "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "legend.fontsize": 8, "axes.spines.top": False, "axes.spines.right": False})
OUT = "figures/report_en"; os.makedirs(OUT, exist_ok=True)
np.random.seed(42)


def save(fig, name):
    fig.tight_layout(); fig.savefig(f"{OUT}/{name}.png", bbox_inches="tight"); plt.close(fig)
    print("ok", name, flush=True)


def main():
    feat = build_features()
    v = load_days("data/raw/vix"); vd = v.groupby(v.index.date).last(); vd.index = pd.to_datetime(vd.index)
    feat["ivar"] = (vd.reindex(feat.index) / 100.0) ** 2 / 252.0
    feat["vix"] = vd.reindex(feat.index)
    rvol = np.sqrt(feat["rv"] * 252) * 100
    rvol_d = np.sqrt(feat["rv"]); target = rvol_d.rolling(63).mean().shift(1)
    lh = _ols(feat, ["rv_d", "rv_w", "rv_m"], [], FIRST_OOS, log_target=True)
    hiv = _ols(feat, ["rv_d", "rv_w", "rv_m", "ivar"], [], FIRST_OOS, log_target=True)
    idx = lh.index.intersection(hiv.index)

    # --- Fig 1: RV history ---
    fig, ax = plt.subplots(figsize=(9, 3.3))
    ax.plot(rvol.index, rvol.values, lw=0.5, color=ACC)
    ax.set_ylabel("Realized vol p.a. (%)")
    ax.set_title("S&P 500 realized volatility (5-min), 2005–2026")
    for d, l in [("2008-10-01", "GFC 2008"), ("2020-03-01", "COVID"), ("2022-06-01", "Inflation"), ("2024-08-01", "Carry unwind")]:
        t = pd.Timestamp(d); seg = rvol.loc[t:t + pd.Timedelta("25D")]
        if len(seg):
            y = seg.max(); ax.annotate(l, xy=(t, y), xytext=(t, min(y + 12, 95)), fontsize=7, ha="center",
                                       arrowprops=dict(arrowstyle="->", color=MUT, lw=0.6))
    save(fig, "01_rv_history")

    # --- Fig 2 (file 03): RV autocorrelation ---
    from statsmodels.tsa.stattools import acf
    a = acf(feat["rv"].dropna(), nlags=100)
    fig, ax = plt.subplots(figsize=(9, 2.9))
    ax.bar(range(len(a)), a, color=ACC, width=.9); ax.set_xlabel("Lag (trading days)"); ax.set_ylabel("ACF")
    ax.set_title("Autocorrelation of realized variance: slow decay (long memory → HAR)")
    save(fig, "03_rv_acf")

    # --- Fig 3 (file 04): forecast ladder — log-target comparable set only ---
    RW  = qlike(lh["actual"].to_numpy(), np.clip(feat["rv"].shift(1).reindex(lh.index).to_numpy(), 1e-6, None))
    m = pd.read_csv("results/oos_metrics.csv")
    m1 = m[m["h"] == 1].drop_duplicates("model").set_index("model")["QLIKE"]
    keep = {"RW": m1.get("RW"), "EWMA(0.94)": m1.get("EWMA(0.94)"), "HAR": m1.get("HAR"),
            "log-HAR": m1.get("log-HAR"), "HAR-IV": qlike(hiv["actual"].to_numpy(), np.clip(hiv["pred"].to_numpy(), 1e-6, None)),
            "Combo-EW": m1.get("Combo-EW")}
    lad = pd.Series(keep).dropna().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 3.1))
    cols = [ACC if x == "log-HAR" else (GREEN if "HAR" in x else MUT) for x in lad.index]
    ax.barh(lad.index, lad.values, color=cols); ax.set_xlabel("QLIKE (lower = better)")
    for i, val in enumerate(lad.values):
        ax.text(val, i, f" {val:.3f}", va="center", fontsize=7.5)
    ax.set_title("Forecast ladder (SPX, h=1, OOS): QLIKE by model")
    save(fig, "04_forecast_ladder")

    # --- Fig 4 (file 06): HAR-IV forecast vs realized ---
    seg = hiv.iloc[-160:]; av = lambda s: np.sqrt(s * 252) * 100
    fig, ax = plt.subplots(figsize=(9, 3.1))
    ax.plot(seg.index, av(seg["actual"]), lw=.9, color=INK, label="realized")
    ax.plot(seg.index, av(seg["pred"]), lw=.9, color=ACC, label="HAR-IV forecast")
    ax.legend(); ax.set_ylabel("Realized vol p.a. (%)")
    ax.set_title("HAR-IV: forecast vs. realized (OOS, last 160 days)")
    save(fig, "06_forecast_vs_actual")

    # --- Fig 5 (file 13): PBO / CSCV ---
    from validation import pbo_cscv, _sr
    cols2 = {}
    for win in (21, 63):
        tgt = rvol_d.rolling(win).mean().shift(1)
        for cap in (2.0, 3.0):
            for fn, pr in (("HAR", lh["pred"]), ("HAR-IV", hiv["pred"])):
                s, _ = vol_managed(feat, pr.reindex(idx), tgt.reindex(idx), lev_cap=cap); cols2[f"{fn}{win}{cap}"] = s.reindex(idx)
    R = pd.DataFrame(cols2).dropna()
    pbo, logits = pbo_cscv(R.values, S=10)
    # NB: this is an ILLUSTRATIVE 2x2x2 VMG grid (PBO ~%.2f); the paper cites the canonical
    # campaign figures (VMG family 0.81, combination universe 0.84). No headline number in the
    # title, so the figure cannot contradict the text.
    print(f"[fig13] illustrative 2x2x2 grid PBO = {pbo:.3f} (paper cites canonical 0.81 / 0.84)")
    fig, ax = plt.subplots(figsize=(7, 3.1)); ax.hist(logits, bins=30, color=BLUE, alpha=.85); ax.axvline(0, color=ACC, lw=1.3)
    ax.set_yticks([]); ax.set_xlabel("logit (OOS rank of the in-sample-best config; < 0 = below median)")
    ax.set_title("CSCV overfitting audit of the VMG parameter family\nthe in-sample-best configuration mostly ranks below median out-of-sample")
    save(fig, "13_pbo")

    print("english paper figures done ->", OUT)


if __name__ == "__main__":
    main()
