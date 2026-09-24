#!/usr/bin/env python3
"""Volatility-managed trading strategy on RV forecasts (Moreira-Muir 2017 style).

Idea: scale exposure to the index INVERSELY to the *forecasted* daily volatility,
targeting a slowly-moving vol level. A better volatility forecast should yield a
better risk-adjusted strategy. We compare the same algo on several forecasts
(RW / HAR / log-HAR / Combo) against buy-and-hold, net of transaction costs.

NO LOOK-AHEAD (audited):
  - forecast pred_t of RV on day t is produced from data <= t-1 (expanding OOS).
  - target vol tau_t = trailing 63d mean realized vol, shifted 1 -> known at t-1.
  - weight w_t = clip(tau_t / sqrt(pred_t), 0, LEV_CAP) is set at close of t-1.
  - strategy return over day t = w_t * r_t - cost*|w_t - w_{t-1}|.
So every quantity used to size day t is known strictly before day t.

Run from repo root:  python strategy.py [--raw data/raw/ndx --tag NDX]
"""
from __future__ import annotations

import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analyze import build_features, _expanding_ols, _lag, EPS, FIRST_OOS

LEV_CAP = 3.0        # max leverage (realistic futures cap)
COST = 1e-4          # 1 bp per unit turnover (round-trip-ish for liquid futures)
TARGET_WIN = 63      # trailing window (days) for the vol target
PPY = 252


def forecasts(feat):
    """OOS variance forecasts per model, aligned to target dates."""
    return {
        "RW": _lag(feat, feat["rv"].shift(1), FIRST_OOS)["pred"],
        "HAR": _expanding_ols(feat, ["rv_d", "rv_w", "rv_m"], FIRST_OOS, log=False)["pred"],
        "log-HAR": _expanding_ols(feat, ["rv_d", "rv_w", "rv_m"], FIRST_OOS, log=True)["pred"],
    }


def vol_managed(feat, pred, target, cost=COST, lev_cap=LEV_CAP):
    """Return (net daily simple returns, weights) for the vol-managed strategy."""
    df = pd.DataFrame({"pred": pred, "ret": feat["ret"], "target": target}).dropna()
    sd_hat = np.sqrt(df["pred"].clip(lower=EPS))          # forecasted daily vol
    w = (df["target"] / sd_hat).clip(0.0, lev_cap)         # exposure set at t-1
    r_simple = np.exp(df["ret"]) - 1.0                     # asset simple return, day t
    dw = w.diff().abs().fillna(w.abs())
    strat = w * r_simple - cost * dw                       # net of turnover cost
    return strat, w


def perf(ret):
    """Full performance suite on daily simple returns."""
    ret = ret.dropna()
    n = len(ret)
    eq = (1.0 + ret).cumprod()
    cagr = eq.iloc[-1] ** (PPY / n) - 1.0
    vol = ret.std() * np.sqrt(PPY)
    sharpe = ret.mean() / ret.std() * np.sqrt(PPY) if ret.std() > 0 else np.nan
    dn = ret[ret < 0].std()
    sortino = ret.mean() / dn * np.sqrt(PPY) if dn and dn > 0 else np.nan
    dd = (eq / eq.cummax() - 1.0).min()
    calmar = cagr / abs(dd) if dd < 0 else np.nan
    neg = ret[ret < 0].sum()
    pf = ret[ret > 0].sum() / abs(neg) if neg != 0 else np.nan
    win = (ret > 0).mean()
    return {"CAGR": cagr, "Vol": vol, "Sharpe": sharpe, "Sortino": sortino,
            "MaxDD": dd, "Calmar": calmar, "ProfitFactor": pf, "WinRate": win, "N": n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--tag", default="SPX")
    args = ap.parse_args()

    feat = build_features(args.raw)
    rvol = np.sqrt(feat["rv"])
    target = rvol.rolling(TARGET_WIN).mean().shift(1)      # trailing vol target, no look-ahead

    fc = forecasts(feat)
    fc["Combo"] = pd.concat([fc["HAR"], fc["log-HAR"]], axis=1).mean(axis=1)

    # common OOS window
    idx = feat.index
    for p in fc.values():
        idx = idx.intersection(p.dropna().index)
    idx = idx[idx >= pd.Timestamp(FIRST_OOS)]

    strategies = {}
    weights = {}
    # buy & hold benchmark
    r_bh = (np.exp(feat["ret"]) - 1.0).reindex(idx)
    strategies["Buy&Hold"] = r_bh
    for name, pred in fc.items():
        s, w = vol_managed(feat, pred.reindex(idx), target.reindex(idx))
        strategies[f"VM[{name}]"] = s.reindex(idx)
        weights[name] = w

    rows = {name: perf(s) for name, s in strategies.items()}
    tab = pd.DataFrame(rows).T[["CAGR", "Vol", "Sharpe", "Sortino", "MaxDD",
                                "Calmar", "ProfitFactor", "WinRate", "N"]]
    print(f"\n=== {args.tag} vol-managed strategy ({idx.min().date()} -> {idx.max().date()}, "
          f"cost {COST*1e4:.0f}bp, lev cap {LEV_CAP:g}) ===")
    print(tab.to_string(float_format=lambda x: f"{x:.3f}"))
    print(f"\nturnover (avg |dw|/day): " +
          ", ".join(f"{k}={weights[k].diff().abs().mean():.3f}" for k in weights))

    tab.to_csv(f"results/strategy_metrics_{args.tag}.csv")

    # equity curves (log scale)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    order = ["Buy&Hold", "VM[RW]", "VM[HAR]", "VM[log-HAR]", "VM[Combo]"]
    colors = {"Buy&Hold": "#211c18", "VM[RW]": "#9b9b9b", "VM[HAR]": "#2b4a63",
              "VM[log-HAR]": "#7c1c2c", "VM[Combo]": "#2f6d4f"}
    for name in order:
        eq = (1.0 + strategies[name].dropna()).cumprod()
        ax.plot(eq.index, eq.values, lw=1.0, label=name, color=colors.get(name))
    ax.set_yscale("log"); ax.set_ylabel("Wachstum von 1 (log)"); ax.legend(fontsize=8)
    ax.set_title(f"{args.tag}: Volatility-Managed vs. Buy-&-Hold (netto, OOS)")
    fig.savefig(f"figures/strategy_equity_{args.tag}.png", dpi=130, bbox_inches="tight")
    print(f"\nsaved: results/strategy_metrics_{args.tag}.csv, figures/strategy_equity_{args.tag}.png")


if __name__ == "__main__":
    main()
