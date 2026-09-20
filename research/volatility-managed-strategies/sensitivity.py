#!/usr/bin/env python3
"""Robustness add-ons for the campaign (QR006):

1. COST sensitivity: rebuild every config at {1,2,5} bp and walk-forward each
   family -> does the edge survive realistic slippage?
2. LEVERED variants: top combos run at low vol; scale to a 15% vol target with a
   t-1 rolling estimate (cap 3x). k multiplies net returns (costs scale along;
   k-turnover itself is small and noted as approximation).
3. SUB-PERIOD stability: 2013-2019 vs 2020-2026 for the ranking's top rows.

Run from repo root after portfolio_combos.py:  python sensitivity.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from strategy_lab import build_panel, FIRST_OOS
from walkforward import all_config_returns, walk_forward
from metrics_engine import perf_daily, PPY
from validation import _sr

MARKETS = {"SPX": "data/raw"}  # SPX-only public rescope (Wasserfest); NDX/DAX raus
FAMILIES = ["VMG", "TSMOM", "VIXTS", "REV", "TOM", "ON"]
COSTS = [1e-4, 2e-4, 5e-4]
TARGET_VOL = 0.15


def sharpe(r: pd.Series) -> float:
    r = r.dropna()
    return float(r.mean() / r.std() * np.sqrt(PPY)) if len(r) and r.std() > 0 else np.nan


def main():
    # ---- 1 · cost sensitivity via full WFA rebuild per cost level
    rows = []
    xm_store: dict[float, dict[str, pd.Series]] = {c: {} for c in COSTS}
    for tag, raw in MARKETS.items():
        p, pred = build_panel(raw, tag)
        for cost in COSTS:
            R, fam = all_config_returns(p, pred, cost=cost)
            for f in FAMILIES:
                if f not in fam:
                    continue
                wfa_ret, _ = walk_forward(R, fam[f])
                oos = wfa_ret[wfa_ret.index >= pd.Timestamp(FIRST_OOS)].dropna()
                rows.append({"market": tag, "family": f, "cost_bp": cost * 1e4,
                             "Sharpe": sharpe(oos)})
                xm_store[cost].setdefault(f, []).append(oos)
        print(f"{tag}: cost grid done")

    cs = pd.DataFrame(rows).pivot_table(index=["family"], columns=["market", "cost_bp"],
                                        values="Sharpe")
    cs.to_csv("results/sensitivity_costs.csv")
    print("\n=== WFA family Sharpe vs cost (bp) ===")
    print(cs.round(3).to_string())

    # C4-IV / C2-EW cost analog on SPX (families IV/EW-combined per cost level)
    from portfolio_combos import combine
    xm_rows = {}
    for cost in COSTS:
        XM = pd.DataFrame({f: pd.concat(s, axis=1, sort=False).mean(axis=1)
                           for f, s in xm_store[cost].items() if len(s) == len(MARKETS)})
        c4 = combine(XM[["VMG", "TSMOM", "VIXTS", "REV"]], "IV")
        c2 = combine(XM[["VMG", "VIXTS"]], "EW")
        xm_rows[f"{cost*1e4:.0f}bp"] = {"C4-IV-SPX": sharpe(c4), "C2-EW-SPX": sharpe(c2)}
    xt = pd.DataFrame(xm_rows)
    xt.to_csv("results/sensitivity_xm_costs.csv")
    print("\n=== top combos vs cost ===")
    print(xt.round(3).to_string())

    # ---- 2 & 3 · levered variants + sub-periods from stored candidate series
    cand = pd.read_parquet("results/campaign_returns.parquet")
    rank = pd.read_csv("results/campaign_ranking.csv", index_col=0)
    top = [i for i in rank.index if rank.loc[i, "kind"] != "benchmark"][:8]
    lev_rows, sub_rows = {}, {}
    for nm in top + ["BH-SPX"]:
        if nm not in cand:
            continue
        r = cand[nm].dropna()
        vol = r.rolling(63).std().shift(1) * np.sqrt(PPY)
        k = (TARGET_VOL / vol.clip(lower=1e-4)).clip(0.0, 3.0)
        rl = (k * r).dropna()
        rep = perf_daily(rl)
        rep["avg_leverage"] = float(k.reindex(rl.index).mean())
        lev_rows[nm] = rep
        s1 = r[r.index < "2020-01-01"]; s2 = r[r.index >= "2020-01-01"]
        sub_rows[nm] = {"Sharpe_13_19": sharpe(s1), "Sharpe_20_26": sharpe(s2),
                        "Calmar_13_19": perf_daily(s1).get("Calmar", np.nan),
                        "Calmar_20_26": perf_daily(s2).get("Calmar", np.nan)}
    lev = pd.DataFrame(lev_rows).T
    lev.to_csv("results/top_levered.csv")
    sub = pd.DataFrame(sub_rows).T
    sub.to_csv("results/top_subperiods.csv")
    print("\n=== levered to 15% vol (net, cap 3x) ===")
    print(lev[["CAGR", "Vol", "Sharpe", "MaxDD", "Calmar", "NetProfit_EUR",
               "avg_leverage"]].round(3).to_string())
    print("\n=== sub-period stability ===")
    print(sub.round(3).to_string())


if __name__ == "__main__":
    main()
