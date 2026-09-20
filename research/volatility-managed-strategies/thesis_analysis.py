#!/usr/bin/env python3
"""Thesis analysis — SPX & NDX realized vs implied volatility (VIX / VXN).

Symmetric, look-ahead-free pipeline for the bachelor thesis. For each index it:
  - builds 5-min realized volatility (RV) and HAR lag features,
  - loads the index's implied-vol index (VIX for SPX, VXN for NDX; FRED daily close),
  - forecasts RV out-of-sample: RW, log-HAR, HAR-IV; scores QLIKE + Clark-West,
  - measures the variance risk premium (IV^2 - RV),
  - runs a volatility-managed strategy (log-HAR / HAR-IV) vs Buy&Hold,
  - stress-tests the strategy with PBO/CSCV + Deflated Sharpe.
Figures -> figures/thesis/, tables -> results/thesis_*.csv.  Run: python thesis_analysis.py
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import norm

from analyze import build_features, _ols, FIRST_OOS, EPS, MIN_VAR
from strategy import vol_managed, perf
from validation import pbo_cscv, deflated_sharpe, _sr

ACC, INK, BLUE, GREEN, MUT, ORANGE = "#7c1c2c", "#211c18", "#2b4a63", "#2f6d4f", "#9b9b9b", "#b8860b"
OUT = "figures/thesis"; os.makedirs(OUT, exist_ok=True); os.makedirs("results", exist_ok=True)
PPY = 252
plt.rcParams.update({"figure.dpi": 130, "font.family": "serif", "axes.titlesize": 11,
                     "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "legend.fontsize": 8, "axes.spines.top": False, "axes.spines.right": False})

MARKETS = {"SPX": ("data/raw", "VIXCLS"), "NDX": ("data/raw/ndx", "VXNCLS")}


def fred(name):
    df = pd.read_csv(f"data/macro/{name}.csv", na_values="."); df.columns = ["d", name]
    df["d"] = pd.to_datetime(df["d"]); return df.set_index("d")[name].astype(float)


def qlike(a, f):
    x = (a / np.clip(f, MIN_VAR, None)).replace([np.inf, -np.inf], np.nan).dropna()
    return float((x - np.log(x) - 1).mean())


def r2(a, f):
    a, f = np.asarray(a), np.asarray(f); return 1 - np.sum((a - f) ** 2) / np.sum((a - a.mean()) ** 2)


def nw_t(x, lag=5):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x); mu = x.mean(); e = x - mu
    g0 = np.mean(e * e); s = g0
    for k in range(1, lag + 1):
        gk = np.mean(e[k:] * e[:-k]); s += 2 * (1 - k / (lag + 1)) * gk
    se = np.sqrt(s / n); return mu / se if se > 0 else np.nan


def clark_west(a, p_restr, p_unrestr):
    f = (a - p_restr) ** 2 - (a - p_unrestr) ** 2 + (p_restr - p_unrestr) ** 2
    t = nw_t(f); return t, float(1 - norm.cdf(t))


def analyse(tag, rawdir, ivid):
    feat = build_features(rawdir)
    iv = fred(ivid).reindex(feat.index).ffill()
    feat["ivar"] = (iv / 100.0) ** 2 / 252.0
    feat["iv"] = iv
    rw = feat["rv"].shift(1)
    lhar = _ols(feat, ["rv_d", "rv_w", "rv_m"], [], FIRST_OOS, log_target=True)["pred"]
    hariv = _ols(feat, ["rv_d", "rv_w", "rv_m", "ivar"], [], FIRST_OOS, log_target=True)["pred"]
    idx = hariv.dropna().index; idx = idx[idx >= pd.Timestamp(FIRST_OOS)]
    for s in (rw, lhar):
        idx = idx.intersection(s.dropna().index)
    a = feat["rv"].reindex(idx)
    preds = {"RW": rw.reindex(idx), "log-HAR": lhar.reindex(idx), "HAR-IV": hariv.reindex(idx)}
    rows = []
    for name, p in preds.items():
        cw_t, cw_p = clark_west(a.values, preds["RW"].values, p.values) if name != "RW" else (np.nan, np.nan)
        rows.append({"market": tag, "model": name, "QLIKE": qlike(a, p), "OOS_R2": r2(a, p) if name != "RW" else 0.0, "CW_p_vs_RW": cw_p})
    # HAR-IV vs log-HAR
    t_iv, p_iv = clark_west(a.values, preds["log-HAR"].values, preds["HAR-IV"].values)

    # variance risk premium
    vrp = (feat["ivar"] - feat["rv"]).reindex(idx)

    # vol-managed strategy on HAR-IV forecast
    rvol = np.sqrt(feat["rv"]); target = rvol.rolling(63).mean().shift(1)
    strat = {}
    bh = (np.exp(feat["ret"]) - 1.0).reindex(idx); strat["Buy&Hold"] = bh
    for fn, p in [("log-HAR", lhar), ("HAR-IV", hariv)]:
        s, _ = vol_managed(feat, p.reindex(idx), target.reindex(idx)); strat[f"VM[{fn}]"] = s.reindex(idx)
    perf_rows = []
    for k, s in strat.items():
        pf = perf(s); perf_rows.append({"market": tag, "strategy": k, **{m: pf[m] for m in ["CAGR", "Vol", "Sharpe", "Sortino", "MaxDD", "Calmar"]}})

    # PBO over a vol-managed config grid (HAR-IV forecast, vary target window + leverage cap)
    grid = {}
    for win in (21, 42, 63, 126):
        tg = rvol.rolling(win).mean().shift(1)
        for cap in (1.5, 2.0, 3.0):
            s, _ = vol_managed(feat, hariv.reindex(idx), tg.reindex(idx), lev_cap=cap)
            grid[f"w{win}L{cap}"] = s.reindex(idx)
    G = pd.DataFrame(grid).dropna(); pbo, _ = pbo_cscv(G.values, S=10)
    srs = G.apply(lambda c: _sr(c.values)) * np.sqrt(PPY)
    dsr = deflated_sharpe(G[srs.idxmax()].values, (srs / np.sqrt(PPY)).std(), G.shape[1])

    return dict(tag=tag, feat=feat, idx=idx, a=a, preds=preds, iv=feat["iv"].reindex(idx),
                iv_vs_rv_t=(t_iv, p_iv), vrp=vrp, strat=strat, rows=rows, perf_rows=perf_rows,
                pbo=pbo, dsr=dsr, grid_sr=srs, bh=bh)


def main():
    R = {tag: analyse(tag, d, v) for tag, (d, v) in MARKETS.items()}
    fc = pd.DataFrame([r for m in R.values() for r in m["rows"]])
    st = pd.DataFrame([r for m in R.values() for r in m["perf_rows"]])
    print("=== Forecasting (QLIKE, OOS-R2, Clark-West p vs RW) ===")
    print(fc.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    for tag in R:
        t, p = R[tag]["iv_vs_rv_t"]; print(f"  {tag}: HAR-IV vs log-HAR Clark-West t={t:.2f}, p={p:.4f} | PBO={R[tag]['pbo']:.3f}, DSR={R[tag]['dsr']:.3f}")
    print("\n=== Vol-managed strategy vs Buy&Hold ===")
    print(st.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    fc.to_csv("results/thesis_forecast.csv", index=False); st.to_csv("results/thesis_strategy.csv", index=False)
    pd.DataFrame([{"market": t, "PBO": R[t]["pbo"], "DSR": R[t]["dsr"],
                   "HARIV_vs_logHAR_CW_p": R[t]["iv_vs_rv_t"][1]} for t in R]).to_csv("results/thesis_validation.csv", index=False)

    col = {"SPX": ACC, "NDX": BLUE}
    # 1 RV history both markets
    fig, ax = plt.subplots(2, 1, figsize=(9, 4.6), sharex=True)
    for k, (tag) in enumerate(R):
        rvol = np.sqrt(R[tag]["feat"]["rv"]) * np.sqrt(252) * 100
        ax[k].plot(rvol.index, rvol.values, lw=.6, color=col[tag]); ax[k].set_ylabel(f"{tag} RVol (%)")
        ax[k].set_ylim(0, min(90, rvol.max() * 1.05))
    ax[0].set_title("Abb. — Realisierte Volatilität (5-min, annualisiert): SPX (oben) & NDX (unten)")
    fig.tight_layout(); fig.savefig(f"{OUT}/rv_history.png", bbox_inches="tight"); plt.close(fig)

    # 2 IV vs RV (VRP) both markets
    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.4))
    for k, tag in enumerate(R):
        rvann = np.sqrt(R[tag]["a"]) * np.sqrt(252) * 100; ivv = R[tag]["iv"]
        ax[k].scatter(rvann, ivv, s=4, alpha=.15, color=col[tag])
        lim = [0, float(np.nanpercentile(np.r_[rvann, ivv], 99))]
        ax[k].plot(lim, lim, color=INK, lw=.8, ls="--"); ax[k].set_xlim(lim); ax[k].set_ylim(lim)
        ax[k].set_xlabel("realisierte Vol (%)"); ax[k].set_ylabel("implizite Vol (%)")
        ax[k].set_title(f"{tag}: {MARKETS[tag][1][:3]} vs RV")
    fig.suptitle("Abb. — Implizite über realisierter Volatilität: die Varianz-Risikoprämie", y=1.03)
    fig.tight_layout(); fig.savefig(f"{OUT}/iv_vs_rv.png", bbox_inches="tight"); plt.close(fig)

    # 3 forecast QLIKE ladder
    fig, ax = plt.subplots(figsize=(8, 3.3)); models = ["RW", "log-HAR", "HAR-IV"]; x = np.arange(len(models)); w = 0.36
    for k, tag in enumerate(R):
        q = [next(r["QLIKE"] for r in R[tag]["rows"] if r["model"] == mo) for mo in models]
        ax.bar(x + (k - .5) * w, q, w, color=col[tag], label=tag)
    ax.set_xticks(x); ax.set_xticklabels(models); ax.set_ylabel("QLIKE (niedriger = besser)"); ax.legend()
    ax.set_ylim(0.15, 0.36); ax.set_title("Abb. — OOS-Prognosegüte (QLIKE): RW → log-HAR → HAR-IV")
    fig.tight_layout(); fig.savefig(f"{OUT}/forecast_ladder.png", bbox_inches="tight"); plt.close(fig)

    # 4 HAR-IV forecast vs realized (SPX, last 500)
    tag = "SPX"; sl = slice(-500, None); ann = np.sqrt(252) * 100
    fig, ax = plt.subplots(figsize=(9, 3.1))
    ax.plot(R[tag]["idx"][sl], (np.sqrt(R[tag]["a"]) * ann).values[sl], color=INK, lw=.6, alpha=.7, label="realisiert")
    ax.plot(R[tag]["idx"][sl], (np.sqrt(R[tag]["preds"]["HAR-IV"].clip(lower=EPS)) * ann).values[sl], color=ACC, lw=1, label="HAR-IV-Prognose")
    ax.set_ylabel("annual. Vol (%)"); ax.legend(); ax.set_title("Abb. — HAR-IV-Prognose vs. realisierte Volatilität (SPX, letzte 500 Tage)")
    fig.tight_layout(); fig.savefig(f"{OUT}/hariv_forecast.png", bbox_inches="tight"); plt.close(fig)

    # 5 strategy equity both markets
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    for k, tag in enumerate(R):
        for key, c in [("Buy&Hold", INK), ("VM[HAR-IV]", ACC)]:
            eq = (1 + R[tag]["strat"][key].dropna()).cumprod(); ax[k].plot(eq.index, eq.values, lw=1, color=c, label=key)
        ax[k].set_yscale("log"); ax[k].set_title(f"{tag}"); ax[k].legend()
    fig.suptitle("Abb. — Volatilitätsgesteuerte Strategie (HAR-IV) vs. Buy&Hold", y=1.03)
    fig.tight_layout(); fig.savefig(f"{OUT}/strategy_equity.png", bbox_inches="tight"); plt.close(fig)

    # 6 strategy metrics
    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.2))
    for k, mkey in enumerate(["Sharpe", "Calmar"]):
        piv = st.pivot(index="strategy", columns="market", values=mkey).reindex(["Buy&Hold", "VM[log-HAR]", "VM[HAR-IV]"])
        piv.plot.barh(ax=ax[k], color=[ACC, BLUE], legend=(k == 0)); ax[k].set_title(mkey); ax[k].set_ylabel("")
    fig.suptitle("Abb. — Risiko-adjustierte Kennzahlen je Strategie und Markt", y=1.03)
    fig.tight_layout(); fig.savefig(f"{OUT}/strategy_metrics.png", bbox_inches="tight"); plt.close(fig)

    # 7 PBO
    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.1))
    for k, tag in enumerate(R):
        ax[k].hist(R[tag]["grid_sr"].values, bins=10, color=col[tag], alpha=.8)
        ax[k].set_title(f"{tag}: PBO={R[tag]['pbo']:.2f}, DSR={R[tag]['dsr']:.2f}"); ax[k].set_xlabel("Sharpe je Config"); ax[k].set_yticks([])
    fig.suptitle("Abb. — Overfitting-Audit (PBO/CSCV) über das Strategie-Config-Gitter", y=1.03)
    fig.tight_layout(); fig.savefig(f"{OUT}/pbo.png", bbox_inches="tight"); plt.close(fig)

    print("\nfigures ->", OUT)


if __name__ == "__main__":
    main()
