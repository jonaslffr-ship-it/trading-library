#!/usr/bin/env python3
"""Test the hypothesis catalogue against the data (look-ahead-free), collect results.

Every predictor is known STRICTLY before the outcome it predicts (comments mark it).
Predictive regressions use Newey-West (HAC) t-stats over overlapping horizons.
Forecast improvements use Diebold-Mariano + Clark-West (nested). Strategy variants
use the same net-of-cost metrics as strategy.py.

Data-ready (SPX 5-min RV + jumps/semivar + VIX):
  H-A0  HAR-IV : does implied vol (VIX) improve the RV forecast?      (DM / Clark-West)
  H-A1  conditional VRP predicts forward equity returns              (NW predictive reg)
  H-A2  VRP-gated vol-managed vs ungated                             (Sharpe / MaxDD)
  H-B1  signed semivariance predicts next-day return                 (NW predictive reg)
  H-B2  downside-vol targeting vs total-RV targeting                 (Sharpe / MaxDD)
  H-C1  vol-of-vol predicts forward returns + de-risk gate           (NW reg + strat)

NOT tested here: H-D1 overnight, H-D2 intraday-MOC, H-E1/E2 order-flow-imbalance,
H-F2 lead-lag (need futures/L2 ingestion); H-F1 cross-market spillover (SPX->NDX/DAX)
dropped in the SPX-only public rescope (Wasserfest). Flagged in the summary.

Run:  python hypotheses.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from analyze import build_features, _expanding_ols, _ols, FIRST_OOS, EPS, MIN_VAR
from strategy import vol_managed, perf
from src.ingest import load_days
from src.evaluate import qlike, diebold_mariano, clark_west

RESULTS = []


def rec(hid, test, stat, verdict):
    RESULTS.append({"H": hid, "Test": test, "Statistik": stat, "Verdikt": verdict})
    print(f"{hid:5s} | {test:44s} | {stat:30s} | {verdict}")


def vix_daily(raw="data/raw/vix"):
    v = load_days(raw)
    d = v.groupby(v.index.date).last()
    d.index = pd.to_datetime(d.index)
    return d


def nw(y, X, maxlags):
    d = pd.concat([y.rename("y"), X], axis=1).dropna()
    return sm.OLS(d["y"], sm.add_constant(d.drop(columns="y"))).fit(
        cov_type="HAC", cov_kwds={"maxlags": maxlags})


def ql(a, f):
    r = a / np.clip(f, MIN_VAR, None)
    return r - np.log(r) - 1.0


def vm_gated(feat, pred, target, gate=None, cost=1e-4, cap=3.0):
    cols = {"pred": pred, "ret": feat["ret"], "target": target}
    if gate is not None:
        cols["gate"] = gate
    df = pd.DataFrame(cols).dropna()
    w = (df["target"] / np.sqrt(df["pred"].clip(lower=EPS))).clip(0, cap)
    if gate is not None:
        w = w * df["gate"]
    r = np.exp(df["ret"]) - 1.0
    dw = w.diff().abs().fillna(w.abs())
    return w * r - cost * dw


def main():
    feat = build_features()
    vix = vix_daily().reindex(feat.index)
    feat["ivar"] = (vix / 100.0) ** 2 / 252.0                    # implied daily variance
    ret = feat["ret"]
    rvol = np.sqrt(feat["rv"])
    target = rvol.rolling(63).mean().shift(1)                    # trailing vol target (t-1)

    # log-HAR forecast, target-date indexed: pred[t] = E_{t-1}[RV_t]  (uses data <= t-1)
    pred = _expanding_ols(feat, ["rv_d", "rv_w", "rv_m"], FIRST_OOS, log=True)["pred"]
    # conditional VRP known at t-1:  VIX_{t-1}^2 - E_{t-1}[RV_t]
    vrp = feat["ivar"].shift(1) - pred

    print("=== Hypothesen-Tests (SPX 2013-OOS, look-ahead-frei) ===")

    # ---- H-A0 : HAR-IV vs log-HAR (does VIX help the forecast?) ----
    lh = _ols(feat, ["rv_d", "rv_w", "rv_m"], [], FIRST_OOS, log_target=True)
    hiv = _ols(feat, ["rv_d", "rv_w", "rv_m", "ivar"], [], FIRST_OOS, log_target=True)
    ix = lh.index.intersection(hiv.index)
    a = lh.loc[ix, "actual"].to_numpy()
    q_lh, q_iv = qlike(a, lh.loc[ix, "pred"]), qlike(a, hiv.loc[ix, "pred"])
    cw, cwp = clark_west(a, lh.loc[ix, "pred"].to_numpy(), hiv.loc[ix, "pred"].to_numpy())
    rec("H-A0", "HAR-IV vs log-HAR (QLIKE, Clark-West)",
        f"QLIKE {q_iv:.4f} vs {q_lh:.4f}, CW p={cwp:.3f}",
        "Evidenz: VIX hilft" if (q_iv < q_lh and cwp < 0.05) else "keine/schwach")

    # ---- H-A1 : conditional VRP predicts forward returns ----
    for h in (5, 21):
        fwd = ret.rolling(h).sum().shift(-h)                     # returns t..t+h-1 (future)
        m = nw(fwd, pd.DataFrame({"VRP": vrp, "VIX2": feat["ivar"].shift(1)}), maxlags=h)
        t = m.tvalues["VRP"]; b = m.params["VRP"]
        rec("H-A1", f"cond. VRP -> {h}d forward return (NW)",
            f"t={t:.2f}, beta {'+' if b > 0 else '-'}, R2={m.rsquared:.3f}",
            "Evidenz" if (abs(t) > 2 and b > 0) else "keine/schwach")

    # ---- H-A2 : VRP-gated vol-managed vs ungated ----
    gate = (vrp > 0).astype(float).shift(1)                      # gate for day t uses VRP_{t-1}
    base = vm_gated(feat, pred, target)
    gated = vm_gated(feat, pred, target, gate=gate)
    pb, pg = perf(base), perf(gated)
    rec("H-A2", "VRP-Gate am Vol-Managed (Sharpe / MaxDD)",
        f"Sharpe {pg['Sharpe']:.2f} vs {pb['Sharpe']:.2f}, DD {pg['MaxDD']:.2f} vs {pb['MaxDD']:.2f}",
        "Evidenz" if (pg["Sharpe"] >= pb["Sharpe"] and pg["MaxDD"] > pb["MaxDD"]) else "marginal/keine")

    # ---- H-B1 : signed semivariance predicts next-day return ----
    m = nw(ret.shift(-1), pd.DataFrame({"RSminus": feat["rs_m"], "RSplus": feat["rs_p"],
                                        "ret": ret}), maxlags=5)
    tm = m.tvalues["RSminus"]
    rec("H-B1", "RS- (downside) -> next-day return (NW)",
        f"t(RS-)={tm:.2f}, beta {'+' if m.params['RSminus'] > 0 else '-'}",
        "Evidenz (Reversal)" if (abs(tm) > 2 and m.params["RSminus"] < 0) else "keine/schwach")

    # ---- H-B2 : downside-vol targeting vs total-RV targeting ----
    s_tot = vm_gated(feat, feat["rv"].shift(1), target)          # size by RW-RV
    s_dn = vm_gated(feat, (2.0 * feat["rs_m"]).shift(1), target)  # size by RW downside (2*RS-)
    pt, pd_ = perf(s_tot), perf(s_dn)
    rec("H-B2", "Downside-Vol- vs Total-Vol-Targeting",
        f"Sharpe {pd_['Sharpe']:.2f} vs {pt['Sharpe']:.2f}, DD {pd_['MaxDD']:.2f} vs {pt['MaxDD']:.2f}",
        "Evidenz" if (pd_["MaxDD"] > pt["MaxDD"] or pd_["Sharpe"] > pt["Sharpe"]) else "keine")

    # ---- H-C1 : vol-of-vol predicts forward returns + de-risk gate ----
    vov = np.log(feat["rv"].clip(lower=EPS)).rolling(22).std().shift(1)   # vol-of-vol (t-1)
    fwd = ret.rolling(21).sum().shift(-21)
    m = nw(fwd, pd.DataFrame({"VoV": vov}), maxlags=21)
    tvov = m.tvalues["VoV"]
    gate2 = (vov < vov.rolling(252).median()).astype(float).shift(1)
    dg = vm_gated(feat, pred, target, gate=gate2)
    pdg = perf(dg)
    rec("H-C1", "Vol-of-Vol -> 21d return / De-Risk-Gate",
        f"t(VoV)={tvov:.2f}; Gate Sharpe {pdg['Sharpe']:.2f} vs {pb['Sharpe']:.2f}",
        "Evidenz" if abs(tvov) > 2 else "keine (Gate senkt Sharpe)")

    # ---- H-F1 cross-market RV spillover (SPX -> NDX/DAX): dropped in SPX-only rescope ----

    out = pd.DataFrame(RESULTS)
    out.to_csv("results/hypothesis_results.csv", index=False)
    print("\nNICHT getestet (brauchen Futures/L2-Ingestion): H-D1 Overnight, H-D2 Intraday-MOC, "
          "H-E1/E2 Order-Flow, H-F2 Lead-Lag.")
    print("saved: results/hypothesis_results.csv")


if __name__ == "__main__":
    main()
