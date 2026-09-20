#!/usr/bin/env python3
"""Paper fills — ML side (slow): Table 1 MSE/R2 for Lasso/EN/GBRT, Giacomini-White
test (nesting-robust) replacing DM, feature ablation (Appendix B.1), combined MCS."""
from __future__ import annotations
import os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy.stats import norm, chi2

from analyze import build_features, _ols, FIRST_OOS, EPS, MIN_VAR
from ml_models import add_ivar
from src.evaluate import qlike, mse

OUT = {}
feat = add_ivar(build_features())

def mlf(feat, make_model, log_cols, raw_cols, refit=21, purge=1):
    """Expanding ML forecast of RV with custom feature set; log-target + insanity clip."""
    Xp = np.log(np.clip(feat[log_cols].to_numpy(float), EPS, None)) if log_cols else np.empty((len(feat), 0))
    Xr = feat[raw_cols].to_numpy(float) if raw_cols else np.empty((len(feat), 0))
    Xdf = pd.DataFrame(np.column_stack([Xp, Xr]), index=feat.index)
    d = pd.concat([Xdf.shift(1), feat["rv"].rename("y")], axis=1).dropna()
    dates = d.index; X = d.drop(columns="y").to_numpy(float); y = d["y"].to_numpy(float)
    start = int(dates.searchsorted(pd.Timestamp(FIRST_OOS)))
    preds = np.full(len(d), np.nan); model = None; s2 = 0.0
    for i in range(start, len(d)):
        if model is None or (i - start) % refit == 0:
            j = max(1, i - purge)
            yl = np.log(np.clip(y[:j], EPS, None))
            model = make_model(); model.fit(X[:j], yl)
            s2 = float(np.var(yl - model.predict(X[:j])))
        yhat = float(np.exp(model.predict(X[i:i + 1])[0] + 0.5 * s2))
        preds[i] = min(max(yhat, MIN_VAR), 4.0 * float(y[:i].max()))
    return pd.DataFrame({"pred": preds, "actual": y}, index=dates).iloc[start:]

def qloss(a, p):
    r = a / np.clip(p, MIN_VAR, None); return r - np.log(r) - 1.0

def gw_test(loss_a, loss_b):
    """Giacomini-White (2006) conditional predictive ability. Instruments [1, dlag].
    Returns unconditional (HAC t) and conditional (Wald chi2, q=2)."""
    dl = np.asarray(loss_a, float) - np.asarray(loss_b, float)   # a - b ; >0 => a worse
    n = len(dl)
    # unconditional: HAC t-test on mean
    res = sm.OLS(dl, np.ones((n, 1))).fit(cov_type="HAC", cov_kwds={"maxlags": 10})
    t = float(res.params[0] / res.bse[0]); p_unc = float(2 * (1 - norm.cdf(abs(t))))
    # conditional GW: g_t = h_{t-1} * d_t, h=[1, d_{t-1}]
    h = np.column_stack([np.ones(n - 1), dl[:-1]]); g = h * dl[1:, None]
    gbar = g.mean(0)
    gc = g - gbar
    L = 10; om = gc.T @ gc / (n - 1)
    for k in range(1, L + 1):
        G = gc[k:].T @ gc[:-k] / (n - 1)
        om += (1 - k / (L + 1)) * (G + G.T)
    stat = float((n - 1) * gbar @ np.linalg.solve(om, gbar)); p_cond = float(1 - chi2.cdf(stat, 2))
    return {"gw_uncond_t": t, "gw_uncond_p": p_unc, "gw_cond_chi2": stat, "gw_cond_p": p_cond}

# ---------------- models
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LassoCV, ElasticNetCV, RidgeCV, LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor

HAR3 = ["rv_d", "rv_w", "rv_m"]
FULL = ["rv_d", "rv_w", "rv_m", "bv", "rq", "rs_m", "rs_p", "jump", "ivar"]
lasso = lambda: make_pipeline(StandardScaler(), LassoCV(cv=3, alphas=20, max_iter=5000, random_state=42))
enet = lambda: make_pipeline(StandardScaler(), ElasticNetCV(cv=3, l1_ratio=[.3, .6, .9], alphas=20, max_iter=5000, random_state=42))
ridge = lambda: make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-4, 2, 20)))
ols = lambda: make_pipeline(StandardScaler(), LinearRegression())
gbrt = lambda: HistGradientBoostingRegressor(max_iter=250, learning_rate=0.05, max_depth=3, l2_regularization=1.0, random_state=42)

print("### baselines log-HAR / HAR-IV", flush=True)
lh = _ols(feat, HAR3, [], FIRST_OOS, log_target=True)
hiv = _ols(feat, HAR3 + ["ivar"], [], FIRST_OOS, log_target=True)

print("### ablation specs (B.1) — expanding refit, ~min each", flush=True)
specs = {
    "L1 Lasso HAR-lags": (lasso, HAR3, []),
    "L2 +ivar":          (lasso, HAR3 + ["ivar"], []),
    "L3 +semivar":       (lasso, HAR3 + ["ivar", "rs_m", "rs_p"], []),
    "L4 Lasso full":     (lasso, FULL, ["ret_neg"]),
    "Ridge full":        (ridge, FULL, ["ret_neg"]),
    "OLS full":          (ols, FULL, ["ret_neg"]),
    "GBRT full":         (gbrt, FULL, ["ret_neg"]),
    "ElasticNet full":   (enet, FULL, ["ret_neg"]),
}
preds = {"log-HAR": lh, "HAR-IV": hiv}
for nm, (mk, lc, rc) in specs.items():
    print(f"  fitting {nm} ...", flush=True)
    preds[nm] = mlf(feat, mk, lc, rc)

# common index
idx = None
for p in preds.values():
    idx = p.index if idx is None else idx.intersection(p.index)
a = hiv.loc[idx, "actual"].to_numpy()
prw = feat["rv"].shift(1).reindex(idx).to_numpy()

def m3(name):
    p = preds[name].loc[idx, "pred"].to_numpy()
    return {"QLIKE": qlike(a, p), "MSE_x1e8": mse(a, p) * 1e8,
            "R2_OOS": float(1 - np.sum((a - p) ** 2) / np.sum((a - prw) ** 2))}

print("\n### Table-1 metrics (ML + baselines)", flush=True)
tab = {nm: m3(nm) for nm in ["log-HAR", "HAR-IV", "L4 Lasso full", "ElasticNet full", "GBRT full"]}
OUT["ml_table1"] = tab
print(pd.DataFrame(tab).T.to_string(float_format=lambda x: f"{x:.5f}"))

print("\n### Giacomini-White: HAR-IV vs Lasso(full) [replaces DM]", flush=True)
gw = gw_test(qloss(a, preds["HAR-IV"].loc[idx, "pred"].to_numpy()),
             qloss(a, preds["L4 Lasso full"].loc[idx, "pred"].to_numpy()))
OUT["gw_hariv_vs_lasso"] = gw
print("  ", {k: round(v, 4) for k, v in gw.items()})

print("\n### Feature ablation (QLIKE + GW vs row above)", flush=True)
order = ["L1 Lasso HAR-lags", "L2 +ivar", "L3 +semivar", "L4 Lasso full", "Ridge full", "OLS full", "GBRT full"]
abl = {}
prev = None
for nm in order:
    p = preds[nm].loc[idx, "pred"].to_numpy(); q = qlike(a, p)
    row = {"QLIKE": float(q), "R2_OOS": float(1 - np.sum((a - p) ** 2) / np.sum((a - prw) ** 2))}
    if prev is not None:
        g = gw_test(qloss(a, preds[prev].loc[idx, "pred"].to_numpy()), qloss(a, p))
        row["GW_p_vs_prev"] = g["gw_uncond_p"]; row["vs"] = prev
    abl[nm] = row; prev = nm
OUT["ablation"] = abl
print(pd.DataFrame(abl).T.to_string())

print("\n### combined MCS (classical + ML)", flush=True)
try:
    from arch.bootstrap import MCS
    Lc = pd.read_parquet("results/loss_matrix_classical.parquet")
    add = pd.DataFrame({
        "Lasso": qloss(a, preds["L4 Lasso full"].loc[idx, "pred"].to_numpy()),
        "ElasticNet": qloss(a, preds["ElasticNet full"].loc[idx, "pred"].to_numpy()),
        "GBRT": qloss(a, preds["GBRT full"].loc[idx, "pred"].to_numpy()),
    }, index=idx)
    Lall = Lc.reindex(idx).join(add).dropna()
    mcs = MCS(Lall, size=0.10, reps=1000, block_size=10, method="R", seed=42); mcs.compute()
    OUT["mcs_combined"] = {"included_90": list(mcs.included), "excluded_90": list(mcs.excluded),
                           "pvalues": {k: float(v) for k, v in mcs.pvalues["Pvalue"].to_dict().items()}}
    print("included (90%):", list(mcs.included))
    print(mcs.pvalues.to_string())
except Exception as e:
    print("combined MCS failed:", e)

with open("results/paper_fills_ml.json", "w", encoding="utf-8") as fh:
    json.dump(OUT, fh, indent=2, default=float)
print("\nsaved results/paper_fills_ml.json")
