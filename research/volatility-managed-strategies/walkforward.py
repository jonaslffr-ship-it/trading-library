#!/usr/bin/env python3
"""True walk-forward analysis (QR006): per family, pick the config on the TRAIN
window only (Sharpe), trade it in the NEXT test window. No parameter is ever
chosen with knowledge of its own evaluation period.

  train 1260 days -> test 252 days -> step 252 (anchored at panel start, so the
  early windows train on pre-2013 data; reported WFA series is cut to >= 2013 to
  stay comparable with the whole project).

Families: TSMOM, REV, VIXTS, TOM, ON (grids from strategy_lab, pre-registered) and
VMG = vol-managed sizing grid (win x cap on the log-HAR forecast) — the honest
answer to the PBO=0.81 finding on the in-sample-best VM parametrization.

Outputs: results/wfa_{tag}.csv, results/wfa_returns_{tag}.parquet,
         results/wfa_params_{tag}.csv

Run from repo root:  python walkforward.py --raw data/raw --tag SPX
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd

from strategy_lab import (build_panel, campaign_sleeves, run_weights,
                          FIRST_OOS, LEV_CAP)
from metrics_engine import full_report

TRAIN, TEST = 1260, 252
PPY = 252


def _sharpe(s: pd.Series, min_frac: float = 0.6) -> float:
    r = s.dropna()
    if len(r) < min_frac * len(s) or r.std() == 0:
        return np.nan
    return float(r.mean() / r.std() * np.sqrt(PPY))


def all_config_returns(p, pred, cost: float = 1e-4) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Full-history net returns for every pre-registered config, grouped by family."""
    rets = {}
    fam: dict[str, list[str]] = {}
    for name, (w, is_on) in campaign_sleeves(p, pred).items():
        if name == "BH":
            continue
        rets[name] = run_weights(p, w, overnight=is_on, cost=cost)
        if name.startswith("TSMOM"):
            fam.setdefault("TSMOM", []).append(name)
        elif name.startswith("REV|"):
            fam.setdefault("REV", []).append(name)
        elif name.startswith("VIXTS|"):
            fam.setdefault("VIXTS", []).append(name)
        elif name.startswith("TOM|"):
            fam.setdefault("TOM", []).append(name)
        elif name.startswith("ON|"):
            fam.setdefault("ON", []).append(name)
        elif name.startswith("VM"):
            fam.setdefault("VMG", []).append(name)
    # VM sizing grid (win x cap), same grid as validation.py's PBO demo
    rvol = p["rvol"]
    for win in (21, 42, 63, 126):
        target = rvol.rolling(win).mean().shift(1)
        for cap in (1.5, 2.0, 3.0):
            w = (target / np.sqrt(pred.clip(lower=1e-12))).clip(0.0, cap)
            nm = f"VMG|w{win}|c{cap}"
            rets[nm] = run_weights(p, w, cost=cost)
            fam.setdefault("VMG", []).append(nm)
    return pd.DataFrame(rets), fam


def walk_forward(R: pd.DataFrame, cols: list[str]) -> tuple[pd.Series, pd.DataFrame]:
    """WFA over the config columns `cols` of return matrix R."""
    sub = R[cols]
    out, chosen = [], []
    t0 = 0
    while t0 + TRAIN + 1 <= len(sub):
        tr = sub.iloc[t0:t0 + TRAIN]
        te = sub.iloc[t0 + TRAIN:t0 + TRAIN + TEST]
        sr = tr.apply(_sharpe)
        if sr.notna().any():
            best = sr.idxmax()
            out.append(te[best])
            chosen.append({"test_start": te.index[0].date(), "config": best,
                           "train_sharpe": sr[best],
                           "test_sharpe": _sharpe(te[best], min_frac=0.0)})
        t0 += TEST
    if not out:
        return pd.Series(dtype=float), pd.DataFrame()
    return pd.concat(out).sort_index(), pd.DataFrame(chosen)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--tag", default="SPX")
    args = ap.parse_args()

    p, pred = build_panel(args.raw, args.tag)
    R, fam = all_config_returns(p, pred)
    print(f"{args.tag}: config matrix {R.shape[0]} days x {R.shape[1]} configs")

    rows, series, params_all = {}, {}, []
    for name, cols in sorted(fam.items()):
        wfa_ret, chosen = walk_forward(R, cols)
        if wfa_ret.empty:
            print(f"  ! {name}: no WFA windows")
            continue
        oos = wfa_ret[wfa_ret.index >= pd.Timestamp(FIRST_OOS)].dropna()
        rep = full_report(oos)
        n_win = len(chosen)
        rep["WFA_Consistency"] = float((chosen["test_sharpe"] > 0).mean())
        rep["WFA_Windows"] = n_win
        rep["ParamChanges"] = int((chosen["config"] != chosen["config"].shift()).sum() - 1)
        rows[name] = rep
        series[name] = oos
        chosen.insert(0, "family", name)
        params_all.append(chosen)
        print(f"  {name:6s} WFA-Sharpe {rep['Sharpe']:.3f}  consistency "
              f"{rep['WFA_Consistency']:.0%}  windows {n_win}  switches {rep['ParamChanges']}")

    tab = pd.DataFrame(rows).T
    tab.to_csv(f"results/wfa_{args.tag}.csv")
    pd.DataFrame(series).to_parquet(f"results/wfa_returns_{args.tag}.parquet")
    pd.concat(params_all).to_csv(f"results/wfa_params_{args.tag}.csv", index=False)
    print(f"saved: results/wfa_{args.tag}.csv / wfa_returns / wfa_params")


if __name__ == "__main__":
    main()
