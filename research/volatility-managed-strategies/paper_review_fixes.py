#!/usr/bin/env python3
"""Review fixes for the paper (both language versions):

1. Paired block-bootstrap test of the Sharpe DIFFERENCE (same resampled blocks
   applied to both series) — the significance statement the paper was missing:
     S3 (XM-C4-IV) vs. XM buy-and-hold, and WFA-VMG-SPX vs. B&H-SPX.
2. Annual turnover for S1/S2 (implementation section).
3. Figure eq_s123.png: equity of exactly the paper's strategies (S1 instance,
   S2 instance, S3) vs. XM buy-and-hold — replaces the confusing top-5 chart.

Run from repo root:  python paper_review_fixes.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, RED, BLUE, GREEN, GRAY = "#211c18", "#7c1c2c", "#2b4a63", "#2f6d4f", "#9b9b9b"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRAY, "axes.labelcolor": INK,
                     "text.color": INK, "xtick.color": INK, "ytick.color": INK})
PPY = 252


def paired_sharpe_diff(a: pd.Series, b: pd.Series, n_boot=5000, block=21, seed=42):
    """P(Sharpe_a > Sharpe_b) under a paired stationary block bootstrap."""
    df = pd.concat([a, b], axis=1).dropna()
    x, y = df.iloc[:, 0].to_numpy(), df.iloc[:, 1].to_numpy()
    T = len(x)
    rng = np.random.RandomState(seed)
    nb = int(np.ceil(T / block))
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        starts = rng.randint(0, T - block + 1, nb)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:T]
        xs, ys = x[idx], y[idx]
        sa = xs.mean() / xs.std(ddof=1) * np.sqrt(PPY)
        sb = ys.mean() / ys.std(ddof=1) * np.sqrt(PPY)
        diffs[i] = sa - sb
    obs = (x.mean() / x.std(ddof=1) - y.mean() / y.std(ddof=1)) * np.sqrt(PPY)
    return {"obs_diff": float(obs), "P_gt0": float((diffs > 0).mean()),
            "ci_lo": float(np.percentile(diffs, 2.5)),
            "ci_hi": float(np.percentile(diffs, 97.5)), "T": T}


def main():
    cand = pd.read_parquet("results/campaign_returns.parquet")
    wfa_spx = pd.read_parquet("results/wfa_returns_SPX.parquet")

    print("=== paired block-bootstrap Sharpe differences ===")
    r1 = paired_sharpe_diff(cand["XM-C4-IV"], cand["XM-BH"])
    print(f"S3 vs XM-B&H : dSharpe={r1['obs_diff']:+.3f}  P(d>0)={r1['P_gt0']:.1%}  "
          f"95%CI [{r1['ci_lo']:+.3f}, {r1['ci_hi']:+.3f}]  T={r1['T']}")
    r2 = paired_sharpe_diff(wfa_spx["VMG"], cand["BH-SPX"])
    print(f"S1 vs B&H-SPX: dSharpe={r2['obs_diff']:+.3f}  P(d>0)={r2['P_gt0']:.1%}  "
          f"95%CI [{r2['ci_lo']:+.3f}, {r2['ci_hi']:+.3f}]  T={r2['T']}")
    r3 = paired_sharpe_diff(wfa_spx["VIXTS"], cand["BH-SPX"])
    print(f"S2 vs B&H-SPX: dSharpe={r3['obs_diff']:+.3f}  P(d>0)={r3['P_gt0']:.1%}  "
          f"95%CI [{r3['ci_lo']:+.3f}, {r3['ci_hi']:+.3f}]  T={r3['T']}")

    print("\n=== annual turnover (mean |dw| * 252) ===")
    w = pd.read_parquet("results/sleeve_weights_SPX.parquet")
    for col in ("VM[logHAR]", "VIXTS|d1.0|w0.3", "TSMOM252|LF|VT"):
        to = w[col].diff().abs().mean() * PPY
        print(f"{col:18s} turnover {to:6.1f}x p.a.")

    # figure: exactly the paper's strategies
    sel = {"XM-C4-IV (S3)": ("XM-C4-IV", BLUE), "VMG-NDX (S1)": ("VMG-NDX", RED),
           "VIXTS-NDX (S2)": ("VIXTS-NDX", GREEN), "XM Buy&Hold": ("XM-BH", GRAY)}
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    yoff = {"XM-C4-IV (S3)": 0, "VMG-NDX (S1)": 6, "VIXTS-NDX (S2)": 0,
            "XM Buy&Hold": -8}   # separate the two ~730k endpoint labels
    for label, (col, color) in sel.items():
        eq = 100_000 * (1 + cand[col].dropna()).cumprod()
        ls = "--" if "Buy" in label else "-"
        ax.plot(eq.index, eq.values, lw=1.3 if ls == "-" else 1.0, ls=ls,
                color=color, label=label)
        ax.annotate(f"{eq.iloc[-1]/1000:,.0f}k", (eq.index[-1], eq.iloc[-1]),
                    xytext=(4, yoff[label]), textcoords="offset points", fontsize=7,
                    color=color)
    ax.set_yscale("log")
    ax.set_ylabel("Kapital (EUR, log)")
    ax.grid(alpha=0.25, lw=0.5)
    ax.legend(fontsize=8, loc="upper left")
    ax.set_title("S1 / S2 / S3 vs. Cross-Market-Buy&Hold — 100.000 EUR, netto, walk-forward")
    fig.savefig("figures/paper/eq_s123.png", dpi=140, bbox_inches="tight")
    print("\nsaved: figures/paper/eq_s123.png")


if __name__ == "__main__":
    main()
