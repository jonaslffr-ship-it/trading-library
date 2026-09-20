#!/usr/bin/env python3
"""Can we sharpen the SPX 1-day RV forecast beyond HAR-IV / the rich-linear winner?

Reuses the EXACT paper harness (analyze._ols, log-target, daily expanding refit,
insanity filter) and evaluation (src.evaluate). No new baseline degrees of freedom.
Panel is pre-built by _build_panel.py (results/_improve_panel.parquet).

Gap being tested: the paper's beyond-HAR realized measures (RQ/semivar/jump/leverage)
were only ever fitted LEVEL-target -> catastrophic QLIKE. The winning family is
LOG-target. And the one real feature candidate (H1 IV-slope, QLIKE 0.1963) was only
tried on top of plain HAR-IV, never on top of the rich log-target feature set.
So the untested cell is: rich log-target features UNION IV term-structure slope,
plus a QLIKE-native (Gamma-GLM) estimator that removes the log-retransform fragility.

Gates (honest, same spirit as hypo_features.py): QLIKE lower AND MSE not worse AND
nested Clark-West p < 0.05/K, AND -- the decider both write-ups flagged -- QLIKE must
improve in BOTH sub-periods (2013-19 and 2020-26), else it is a single-regime artifact.
Nothing here becomes `supported` (Inv 1): survivors earn a pre-registered R-note only.

Run:  python rv_improve.py
"""
from __future__ import annotations
import numpy as np, pandas as pd

from analyze import _ols, FIRST_OOS, EPS, MIN_VAR
from src.evaluate import qlike, mse, clark_west, diebold_mariano

np.random.seed(42)
PANEL = "results/_improve_panel.parquet"
SUB1 = ("2013-01-01", "2019-12-31")   # pre-COVID
SUB2 = ("2020-01-01", "2027-01-01")   # COVID + post

LOGF = ["rv_d", "rv_w", "rv_m", "bv", "rq", "rs_m", "rs_p", "jump", "ivar"]  # rich set (paper)


def qloss(a, f):
    r = a / np.clip(f, MIN_VAR, None)
    return r - np.log(r) - 1.0


def glm(feat, log_cols, lin_cols, refit=21):
    """QLIKE-native estimator: Gamma-GLM(log link) on LEVEL rv target, expanding refit.
    No log-retransform / no variance floor bias (the suspected MSE-fragility source)."""
    import statsmodels.api as sm
    cols = list(log_cols) + list(lin_cols)
    d = pd.concat([feat[cols].shift(1), feat["rv"].rename("y")], axis=1).dropna()
    dates = d.index
    nlog = len(log_cols)
    X = d[cols].to_numpy(float)
    Xl = np.log(np.clip(X[:, :nlog], EPS, None))
    Xd = np.column_stack([np.ones(len(X)), Xl, X[:, nlog:]])
    y = d["y"].to_numpy(float)
    start = int(dates.searchsorted(pd.Timestamp(FIRST_OOS)))
    preds = np.full(len(d), np.nan)
    fam = sm.families.Gamma(sm.families.links.Log())
    beta = None
    for i in range(start, len(d)):
        if beta is None or (i - start) % refit == 0:
            try:
                beta = sm.GLM(y[:i], Xd[:i], family=fam).fit(maxiter=100).params
            except Exception:
                beta = np.linalg.lstsq(Xd[:i], np.log(np.clip(y[:i], EPS, None)), rcond=None)[0]
        yhat = float(np.exp(Xd[i] @ beta))
        preds[i] = min(max(yhat, MIN_VAR), 4.0 * float(y[:i].max()))
    return pd.DataFrame({"pred": preds, "actual": y}, index=dates).iloc[start:]


def sub_qlike(df, lo, hi):
    s = df[(df.index >= pd.Timestamp(lo)) & (df.index <= pd.Timestamp(hi))]
    a = s["actual"].to_numpy(); p = np.clip(s["pred"].to_numpy(), MIN_VAR, None)
    return qlike(a, p), len(s)


def evalrow(name, cand, base, nested):
    idx = base.index.intersection(cand.index)
    a = base.loc[idx, "actual"].to_numpy()
    pb = np.clip(base.loc[idx, "pred"].to_numpy(), MIN_VAR, None)
    pc = np.clip(cand.loc[idx, "pred"].to_numpy(), MIN_VAR, None)
    qc, qb = qlike(a, pc), qlike(a, pb)
    if nested:
        _, p = clark_west(a, pb, pc)          # H0: nesting (cand) not better
        ptype = "CW"
    else:
        _, p = diebold_mariano(qloss(a, pb), qloss(a, pc)); ptype = "DM"
    q1, n1 = sub_qlike(cand, *SUB1); q2, n2 = sub_qlike(cand, *SUB2)
    qb1, _ = sub_qlike(base, *SUB1); qb2, _ = sub_qlike(base, *SUB2)
    return {"model": name, "n": len(idx), "QLIKE": qc, "dQLIKE": qc - qb,
            "MSE_1e8": mse(a, pc) * 1e8, "dMSE_1e8": (mse(a, pc) - mse(a, pb)) * 1e8,
            f"{ptype}_p": p, "Q_13_19": q1, "dQ_13_19": q1 - qb1,
            "Q_20_26": q2, "dQ_20_26": q2 - qb2}


def main():
    feat = pd.read_parquet(PANEL)
    print("panel:", feat.shape, feat.index.min().date(), "->", feat.index.max().date())

    HARIV = ["rv_d", "rv_w", "rv_m", "ivar"]
    base = _ols(feat, HARIV, [], FIRST_OOS, log_target=True)
    bq = qlike(base["actual"].to_numpy(), np.clip(base["pred"].to_numpy(), MIN_VAR, None))
    print(f"BASELINE HAR-IV (log-target): QLIKE {bq:.4f}  (paper 0.2041, n={len(base)})")
    q1, _ = sub_qlike(base, *SUB1); q2, _ = sub_qlike(base, *SUB2)
    print(f"   sub-periods: 2013-19 {q1:.4f} | 2020-26 {q2:.4f}\n")

    # candidate ladder -- (name, forecaster, nested-in-HARIV?)
    cands = [
        ("Rich-log-OLS",        lambda: _ols(feat, LOGF, ["ret_neg"], FIRST_OOS, log_target=True), True),
        ("C1 HAR-IV+slope",     lambda: _ols(feat, HARIV, ["ivslope"], FIRST_OOS, log_target=True), True),
        ("C2 Rich+slope",       lambda: _ols(feat, LOGF, ["ret_neg", "ivslope"], FIRST_OOS, log_target=True), True),
        ("C3 Parsi(IV+slope+rs_m)", lambda: _ols(feat, HARIV + ["rs_m"], ["ivslope"], FIRST_OOS, log_target=True), True),
        ("C4 GLM(HAR-IV+slope)", lambda: glm(feat, HARIV, ["ivslope"]), False),
        ("C5 GLM(Rich+slope)",  lambda: glm(feat, LOGF, ["ret_neg", "ivslope"]), False),
    ]
    fc = {}
    rows = []
    for name, fn, nested in cands:
        df = fn(); fc[name] = df
        rows.append(evalrow(name, df, base, nested))

    # C6 log-space ensemble (geometric mean) of the strong log-target members
    members = ["C1 HAR-IV+slope", "C2 Rich+slope", "Rich-log-OLS"]
    idx = base.index
    for m in members:
        idx = idx.intersection(fc[m].index)
    lp = np.mean([np.log(np.clip(fc[m].loc[idx, "pred"].to_numpy(), MIN_VAR, None)) for m in members], axis=0)
    ens = pd.DataFrame({"pred": np.exp(lp), "actual": base.loc[idx, "actual"].to_numpy()}, index=idx)
    fc["C6 log-ensemble"] = ens
    rows.append(evalrow("C6 log-ensemble", ens, base, False))

    K = len(cands)  # confirmatory Bonferroni over the nested candidate count
    thr = 0.05 / K
    tab = pd.DataFrame(rows).set_index("model")
    pd.set_option("display.width", 200, "display.max_columns", 30)
    print(f"=== incremental vs HAR-IV (log-target harness, n_OOS={len(base)}) ===")
    show = ["n", "QLIKE", "dQLIKE", "MSE_1e8", "dMSE_1e8", "CW_p", "DM_p",
            "Q_13_19", "dQ_13_19", "Q_20_26", "dQ_20_26"]
    show = [c for c in show if c in tab.columns]
    print(tab[show].to_string(float_format=lambda x: f"{x:.4f}"))
    print(f"\nBonferroni threshold (nested CW): p < 0.05/{K} = {thr:.4f}")
    print("Decider: QLIKE lower AND MSE not worse AND CW p<thr AND dQLIKE<0 in BOTH sub-periods.")
    tab.to_csv("results/rv_improve.csv")
    print("saved: results/rv_improve.csv")


if __name__ == "__main__":
    main()
