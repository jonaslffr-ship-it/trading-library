#!/usr/bin/env python3
"""End-to-end runner: ingest -> realized -> backtest -> evaluate -> figures.

Two modes:
  * SYNTHETIC (default): generates seed-42 synthetic 1-minute prices so the FULL
    pipeline runs on a fresh clone WITHOUT the licensed MarketTick data. The
    printed numbers are ILLUSTRATIVE (they demonstrate that the code runs, not
    the paper's results).
  * REAL (--raw data/raw): runs the same pipeline on the licensed 1-minute index
    CSVs. The full paper reproduction (9-model ladder, strategies, campaign) is
    driven by analyze.py / strategy_lab.py / walkforward.py / portfolio_combos.py
    (see README) — run.py is the one-command smoke test.

Seed fixed at 42 (PREREGISTRATION.md).

Usage:
    python run.py                    # synthetic smoke test, no data needed
    python run.py --raw data/raw     # real SPX data (licensed, not in repo)
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")

from src.ingest import load_days
from src.realized import daily_features, add_har_lags
from src.synth import synthetic_prices
from src.backtest import run_all
from src.evaluate import qlike, diebold_mariano, clark_west

SEED = 42
FLOOR = 1e-6


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()[:10]
    except Exception:
        return "UNKNOWN"


def qloss(a, p):
    r = a / np.clip(p, FLOOR, None)
    return r - np.log(r) - 1.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=None, help="licensed raw-CSV dir (omit -> synthetic)")
    ap.add_argument("--freq", default="5min")
    ap.add_argument("--first-oos", default=None)
    ap.add_argument("--days", type=int, default=750, help="synthetic trading days")
    args = ap.parse_args()

    real = bool(args.raw) and bool(glob.glob(os.path.join(args.raw, "*.csv")))
    if real:
        print(f"[run] REAL data from {args.raw!r} | seed={SEED} commit={git_commit()}")
        px = load_days(args.raw)
    else:
        if args.raw:
            print(f"[run] no CSVs under {args.raw!r} -> synthetic fallback")
        print(f"[run] SYNTHETIC seed-{SEED} smoke test (no licensed data) | commit={git_commit()}")
        px = synthetic_prices(n_days=args.days, seed=SEED)

    out_dir = ".synth_out"
    os.makedirs(out_dir, exist_ok=True)

    feat = add_har_lags(daily_features(px, freq=args.freq), col="rv")
    feat = feat.dropna(subset=["rv_d", "rv_w", "rv_m"]).sort_index()
    if args.first_oos:
        first_oos = args.first_oos
    elif real:
        first_oos = "2013-01-02"
    else:
        first_oos = feat.index[int(0.6 * len(feat))].strftime("%Y-%m-%d")
    print(f"[run] {len(feat)} RV days {feat.index.min().date()}..{feat.index.max().date()} "
          f"| first OOS {first_oos}")

    res = run_all(feat, first_oos=first_oos)

    idx = None
    for d in res.values():
        idx = d.index if idx is None else idx.intersection(d.index)
    a = res["RW"].loc[idx, "actual"].to_numpy()
    prw = res["RW"].loc[idx, "pred"].to_numpy()
    rows = []
    for name, d in res.items():
        p = np.clip(d.loc[idx, "pred"].to_numpy(), FLOOR, None)
        rows.append({"model": name, "QLIKE": qlike(a, p),
                     "OOS_R2_vs_RW": 1.0 - np.sum((a - p) ** 2) / np.sum((a - prw) ** 2)})
    tab = pd.DataFrame(rows).set_index("model")
    print("\n=== OOS forecast ladder (h=1) ===")
    print(tab.to_string(float_format=lambda x: f"{x:.5f}"))

    p_lh = np.clip(res["log-HAR"].loc[idx, "pred"].to_numpy(), FLOOR, None)
    _, dm_p = diebold_mariano(qloss(a, prw), qloss(a, p_lh))
    _, cw_p = clark_west(a, prw, p_lh)
    print(f"\nlog-HAR vs RW: QLIKE {qlike(a, p_lh):.4f} vs {qlike(a, prw):.4f} | "
          f"DM p={dm_p:.3g} | Clark-West p={cw_p:.3g} | log-HAR better: {qlike(a, p_lh) < qlike(a, prw)}")

    csv = os.path.join(out_dir, "oos_metrics.csv")
    tab.to_csv(csv)
    seg = res["log-HAR"].loc[idx].iloc[-120:]
    av = lambda s: np.sqrt(s * 252) * 100
    ax = av(seg["actual"]).plot(lw=0.9, label="realized", color="#211c18")
    av(seg["pred"]).plot(ax=ax, lw=0.9, label="log-HAR", color="#7c1c2c")
    ax.legend(); ax.set_ylabel("RVol (%)"); ax.set_xlabel("")
    ax.set_title("OOS: log-HAR forecast vs. realized (last 120 days)")
    fig = os.path.join(out_dir, "oos_logHAR.png")
    ax.figure.savefig(fig, dpi=130, bbox_inches="tight")
    print(f"\nsaved: {csv}, {fig}")
    if not real:
        print("[run] NOTE: synthetic numbers are illustrative. Reproduce the paper with the "
              "licensed data: python run.py --raw data/raw  (full ladder: analyze.py).")


if __name__ == "__main__":
    main()
