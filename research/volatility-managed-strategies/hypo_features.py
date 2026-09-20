#!/usr/bin/env python3
"""Exploratory feature/spec screen for the SPX RV forecast (candidate mini-hypotheses).

Benchmark = HAR-IV (log-target OLS on log[rv_d, rv_w, rv_m, ivar]) — reused verbatim
via analyze._ols so the baseline reproduces results/ml_forecast_metrics.csv (0.2041).
Each candidate adds ONE feature/spec and is judged INCREMENTALLY on the same OOS window:
QLIKE (primary), MSE (fragility check), Clark-West nested p (HAR-IV nested in HAR-IV+X).

H0 per candidate: no incremental OOS improvement. A survivor must lower QLIKE *and* not
blow up MSE *and* have Clark-West p < 0.05/k (Bonferroni over k tested). Nothing here
becomes `supported` — survivors need a pre-registered R-note first (Inv 1). Seed 42.

Data-limited: VIX9D (matched-horizon), CBOE SKEW, VVIX are NOT locally available and FRED
is unreachable here -> reported as needs-data, not tested.

Run:  python hypo_features.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from analyze import build_features, _ols, FIRST_OOS, EPS, MIN_VAR
from ml_models import add_ivar
from src.evaluate import qlike, mse, clark_west

np.random.seed(42)


def _fred(name: str) -> pd.Series:
    df = pd.read_csv(f"data/macro/{name}.csv", parse_dates=["observation_date"],
                     index_col="observation_date")
    return df[name].astype(float)


def build_panel():
    feat = add_ivar(build_features())                       # + ivar (VIX^2/252)
    idx = feat.index

    # H1 · IV term-structure slope: log(VIX3M / VIX) — the SHAPE, ~orthogonal to level
    vix, vxv = _fred("VIXCLS"), _fred("VXVCLS")
    feat["ivslope"] = np.log((vxv / vix).reindex(idx).ffill(limit=5))

    # H3 · Overnight realized variance: (log open_t - log close_{t-1})^2  (RTH-RV ignores it)
    ohlc = pd.read_parquet("data/processed/ohlc_SPX.parquet")
    ret_on = np.log(ohlc["open"]) - np.log(ohlc["close"].shift(1))
    feat["ov"] = (ret_on ** 2).reindex(idx)

    # H5 · Scheduled-vol calendar: OPEX = 3rd Friday. Deterministic -> known ex ante, so
    # store the LEAD (shift -1) to cancel _ols's internal shift(1): predictor value = OPEX_t.
    is_fri = idx.weekday == 4
    dom = idx.day
    opex = pd.Series(((is_fri) & (dom >= 15) & (dom <= 21)).astype(float), index=idx)
    feat["opex"] = opex.shift(-1)

    # H6 · Financial-conditions lead: HY credit OAS + NFCI (credit stress leads equity vol)
    feat["credit"] = _fred("BAMLH0A0HYM2").reindex(idx).ffill(limit=5)
    feat["nfci"] = _fred("NFCI").reindex(idx).ffill(limit=5)

    # H8 · Level-dependent mean-reversion: rv_m interacted with a high-vol state
    #      (vol reverts faster from high levels). Expanding median -> no look-ahead.
    hv = (feat["rv_m"] > feat["rv_m"].expanding(min_periods=250).median()).astype(float)
    feat["rvm_hv"] = feat["rv_m"] * hv

    return feat


def run_ols(feat, logc, linc):
    return _ols(feat, logc, linc, FIRST_OOS, log_target=True)


def glm_hariv(feat):
    """H7 · QLIKE-native estimation: Gamma-GLM(log link) == QLIKE quasi-MLE, level target,
    NO log-retransform/variance-floor (the suspected fragility source). Refit every 21."""
    import statsmodels.api as sm
    cols = ["rv_d", "rv_w", "rv_m", "ivar"]
    d = pd.concat([feat[cols].shift(1), feat["rv"].rename("y")], axis=1).dropna()
    dates = d.index
    X = np.log(np.clip(d[cols].to_numpy(float), EPS, None))
    Xc = np.column_stack([np.ones(len(X)), X])
    y = d["y"].to_numpy(float)
    start = int(dates.searchsorted(pd.Timestamp(FIRST_OOS)))
    preds = np.full(len(d), np.nan)
    fam = sm.families.Gamma(sm.families.links.Log())
    beta = None
    for i in range(start, len(d)):
        if beta is None or (i - start) % 21 == 0:
            try:
                beta = sm.GLM(y[:i], Xc[:i], family=fam).fit(maxiter=100).params
            except Exception:
                beta = np.linalg.lstsq(Xc[:i], np.log(np.clip(y[:i], EPS, None)), rcond=None)[0]
        yhat = float(np.exp(Xc[i] @ beta))
        preds[i] = min(max(yhat, MIN_VAR), 4.0 * float(y[:i].max()))
    return pd.DataFrame({"pred": preds, "actual": y}, index=dates).iloc[start:]


def evalpair(base, cand):
    """Align base & candidate on common index; return metrics + Clark-West nested p."""
    idx = base.index.intersection(cand.index)
    a = base.loc[idx, "actual"].to_numpy()
    pb = np.clip(base.loc[idx, "pred"].to_numpy(), MIN_VAR, None)
    pc = np.clip(cand.loc[idx, "pred"].to_numpy(), MIN_VAR, None)
    _, cw_p = clark_west(a, pb, pc)          # H0: larger (cand) not better
    return {"n": len(idx), "QLIKE": qlike(a, pc), "dQLIKE": qlike(a, pc) - qlike(a, pb),
            "MSE_x1e8": mse(a, pc) * 1e8, "dMSE_x1e8": (mse(a, pc) - mse(a, pb)) * 1e8,
            "CW_p": cw_p}


def main():
    feat = build_panel()
    HARIV = ["rv_d", "rv_w", "rv_m", "ivar"]
    base = run_ols(feat, HARIV, [])
    base_q = qlike(base["actual"].to_numpy(), np.clip(base["pred"].to_numpy(), MIN_VAR, None))
    print(f"baseline HAR-IV: QLIKE {base_q:.4f}  (target 0.2041, n={len(base)})\n")

    specs = [
        ("H1 IV-slope",         lambda: run_ols(feat, HARIV, ["ivslope"])),
        ("H3 Overnight-var",    lambda: run_ols(feat, HARIV + ["ov"], [])),
        ("H5 OPEX-dummy",       lambda: run_ols(feat, HARIV, ["opex"])),
        ("H6 NFCI",             lambda: run_ols(feat, HARIV, ["nfci"])),
        ("H7 QLIKE-native GLM", lambda: glm_hariv(feat)),
        ("H8 Level-dep MR",     lambda: run_ols(feat, HARIV, ["rvm_hv"])),
    ]
    k = len(specs)
    thr = 0.05 / k
    rows = {}
    for name, fn in specs:
        try:
            m = evalpair(base, fn())
            m["verdict"] = ("SURVIVE" if (m["dQLIKE"] < 0 and m["dMSE_x1e8"] < 0 and m["CW_p"] < thr)
                            else ("QLIKE-only" if m["dQLIKE"] < 0 else "no"))
        except Exception as e:
            m = {"n": 0, "QLIKE": np.nan, "dQLIKE": np.nan, "MSE_x1e8": np.nan,
                 "dMSE_x1e8": np.nan, "CW_p": np.nan, "verdict": "ERROR:" + str(e)[:28]}
        rows[name] = m

    tab = pd.DataFrame(rows).T[["n", "QLIKE", "dQLIKE", "MSE_x1e8", "dMSE_x1e8", "CW_p", "verdict"]]
    print(f"=== incremental vs HAR-IV (QLIKE-lower & MSE-lower & CW p<{thr:.4f}=Bonferroni/{k}) ===")
    with pd.option_context("display.width", 160, "display.max_columns", 20):
        print(tab.to_string(float_format=lambda x: f"{x:.4f}"))
    tab.to_csv("results/hypo_features.csv")
    print("\nneeds-data (nicht getestet): H2 VIX9D matched-horizon, H4 CBOE SKEW, H9 VVIX-in-variance,")
    print("  H6-Credit (BAMLH0A0HYM2 nur 2023+ lokal — zu kurz fuer 2013-OOS-Training)")
    print("saved: results/hypo_features.csv")
    print("Hinweis: 'SURVIVE' = Kandidat fuer eine prae-registrierte R-Note, NICHT supported.")


if __name__ == "__main__":
    main()
