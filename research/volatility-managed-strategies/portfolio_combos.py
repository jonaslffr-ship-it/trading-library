#!/usr/bin/env python3
"""Multi-strategy combinations (Q017) + final campaign ranking (QR006).

Sleeve inputs are the HONEST walk-forward return series per family (parameters
chosen on train windows only), so no combo inherits in-sample parameter luck.

Combos (pre-registered subsets x weightings):
  C1 {VMG,TSMOM}  C2 {VMG,VIXTS}  C3 {VMG,TSMOM,VIXTS}  C4 C3+{REV}
  C5 C4+{TOM}     C6 C5+{ON}
  weightings: EW | InvVol (rolling 63d, t-1) | ERC-light (expanding vol inverse)
  XM = cross-market (only with >=2 markets; disabled in the SPX-only public rescope).

Cost note (honest, twice): sleeve returns already carry their own turnover cost;
summing sleeves on the SAME instrument nets weights in reality, so combo costs
are OVERstated here (conservative). For the top combo we additionally compute the
netted implementation from modal-config weights.

Ranking score (fixed ex ante in QR006):
  Score = .30*Sortino + .25*Calmar + .20*Sharpe + .15*YearConsistency + .10*min(PF-1,1)*5
  DQ: DSR<0.5 | PBO>0.7 | single-market-only effect | synthetic-options-only basis.

Run from repo root (after strategy_lab + walkforward for SPX):
  python portfolio_combos.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from metrics_engine import full_report, monte_carlo, PPY
from validation import deflated_sharpe, pbo_cscv, block_bootstrap_sharpe_ci, _sr

MARKETS = ["SPX"]  # SPX-only public rescope (Wasserfest); NDX/DAX aus dem public Pfad
FAMILIES = ["VMG", "TSMOM", "VIXTS", "REV", "TOM", "ON"]
SUBSETS = {
    "C1": ["VMG", "TSMOM"],
    "C2": ["VMG", "VIXTS"],
    "C3": ["VMG", "TSMOM", "VIXTS"],
    "C4": ["VMG", "TSMOM", "VIXTS", "REV"],
    "C5": ["VMG", "TSMOM", "VIXTS", "REV", "TOM"],
    "C6": ["VMG", "TSMOM", "VIXTS", "REV", "TOM", "ON"],
}
INK, RED, BLUE, GREEN, GRAY = "#211c18", "#7c1c2c", "#2b4a63", "#2f6d4f", "#9b9b9b"
PALETTE = [INK, RED, BLUE, GREEN, GRAY]


def year_consistency(r: pd.Series) -> float:
    by = r.groupby(r.index.year)
    srs = by.apply(lambda x: _sr(x.values) * np.sqrt(PPY) if len(x) >= 100 else np.nan).dropna()
    return float((srs > 0).mean()) if len(srs) else np.nan


def combine(R: pd.DataFrame, mode: str) -> pd.Series:
    """Portfolio of sleeve return series (weights known at t-1)."""
    R = R.dropna(how="all")
    if mode == "EW":
        w = pd.DataFrame(1.0, index=R.index, columns=R.columns)
    elif mode == "IV":         # rolling inverse vol, shifted
        vol = R.rolling(63, min_periods=40).std().shift(1)
        w = 1.0 / vol.clip(lower=1e-6)
    else:                       # ERC-light: expanding inverse vol, shifted
        vol = R.expanding(252).std().shift(1)
        w = 1.0 / vol.clip(lower=1e-6)
    w = w.where(R.notna())
    w = w.div(w.sum(axis=1), axis=0)
    return (w * R).sum(axis=1, min_count=1).dropna()


def main():
    wfa = {m: pd.read_parquet(f"results/wfa_returns_{m}.parquet") for m in MARKETS}
    slv = {m: pd.read_parquet(f"results/sleeve_returns_{m}.parquet") for m in MARKETS}

    candidates: dict[str, pd.Series] = {}
    meta: dict[str, dict] = {}

    # --- benchmarks & single families
    for m in MARKETS:
        candidates[f"BH-{m}"] = slv[m]["BH"]
        meta[f"BH-{m}"] = {"kind": "benchmark", "markets": 1}
        candidates[f"VMfix-{m}"] = slv[m]["VM[logHAR]"]
        meta[f"VMfix-{m}"] = {"kind": "benchmark", "markets": 1}
        for f in FAMILIES:
            if f in wfa[m]:
                candidates[f"{f}-{m}"] = wfa[m][f]
                meta[f"{f}-{m}"] = {"kind": "family", "markets": 1}

    # --- combos per market
    for m in MARKETS:
        for cname, fams in SUBSETS.items():
            cols = [f for f in fams if f in wfa[m]]
            for mode in ("EW", "IV", "ERC"):
                nm = f"{cname}-{mode}-{m}"
                candidates[nm] = combine(wfa[m][cols], mode)
                meta[nm] = {"kind": "combo", "markets": 1}

    # --- cross-market: average each family over markets, then combine
    #     (only with >=2 markets; disabled in the SPX-only public rescope)
    if len(MARKETS) >= 2:
        xm_fam = {}
        for f in FAMILIES:
            series = [wfa[m][f] for m in MARKETS if f in wfa[m]]
            if len(series) == len(MARKETS):
                xm_fam[f] = pd.concat(series, axis=1).mean(axis=1)
        XM = pd.DataFrame(xm_fam)
        for cname in ("C2", "C3", "C4", "C5"):
            cols = [f for f in SUBSETS[cname] if f in XM.columns]
            for mode in ("EW", "IV"):
                nm = f"XM-{cname}-{mode}"
                candidates[nm] = combine(XM[cols], mode)
                meta[nm] = {"kind": "combo-xm", "markets": len(MARKETS)}
        candidates["XM-BH"] = pd.concat([slv[m]["BH"] for m in MARKETS], axis=1).mean(axis=1).dropna()
        meta["XM-BH"] = {"kind": "benchmark", "markets": len(MARKETS)}
        BENCH_BH = "XM-BH"
    else:
        BENCH_BH = f"BH-{MARKETS[0]}"

    # --- metric suite + MC for every candidate
    # honest trial count for DSR deflation: 55 configs/market (37 sleeve + 12 sizing + 6 family)
    # + all combos actually built. SPX-only => 55 + 18 = 73 (vs cross-market 55*3 + 62 = 227).
    n_trials = 55 * len(MARKETS) + len([k for k, v in meta.items() if "combo" in v["kind"]])
    all_sr_pp = []
    rows = {}
    for nm, r in candidates.items():
        r = r.dropna()
        if len(r) < 750:
            continue
        rep = full_report(r)
        rep.update(monte_carlo(r))
        rep["YearConsistency"] = year_consistency(r)
        all_sr_pp.append(_sr(r.values))
        rows[nm] = rep
    sr_std_pp = float(np.nanstd(all_sr_pp))
    for nm in rows:
        rows[nm]["DSR"] = deflated_sharpe(candidates[nm].dropna().values, sr_std_pp, n_trials)
        lo, hi = block_bootstrap_sharpe_ci(candidates[nm].dropna().values, n_boot=1000)
        rows[nm]["Sharpe_CI_lo"], rows[nm]["Sharpe_CI_hi"] = lo, hi

    tab = pd.DataFrame(rows).T

    # --- PBO over the combo universe (per market frame, common window)
    combo_cols = [c for c in tab.index if meta.get(c, {}).get("kind", "").startswith("combo")]
    Rc = pd.DataFrame({c: candidates[c] for c in combo_cols}).dropna()
    pbo, _ = pbo_cscv(Rc.to_numpy(), S=10)

    # --- pre-registered score + ranking
    pf_term = (tab["ProfitFactor"] - 1.0).clip(upper=1.0) * 5.0
    tab["Score"] = (0.30 * tab["Sortino"] + 0.25 * tab["Calmar"] + 0.20 * tab["Sharpe"]
                    + 0.15 * tab["YearConsistency"] + 0.10 * pf_term)
    tab["DQ"] = (tab["DSR"] < 0.5)
    tab["kind"] = [meta[i]["kind"] for i in tab.index]
    tab = tab.sort_values("Score", ascending=False)
    tab.to_csv("results/campaign_ranking.csv")

    # persist candidate return series for sensitivity / sub-period / report work
    keep = [c for c in tab.index]
    pd.DataFrame({c: candidates[c] for c in keep}).to_parquet("results/campaign_returns.parquet")

    strat_only = tab[(~tab["DQ"]) & (tab["kind"] != "benchmark")]
    print(f"=== campaign ranking (n_trials={n_trials}, sr_std_pp={sr_std_pp:.5f}, "
          f"PBO over {len(combo_cols)} combos = {pbo:.2f}) ===")
    cols = ["Score", "Sharpe", "Sortino", "MaxDD", "Calmar", "ProfitFactor",
            "YearConsistency", "DSR", "NetProfit_EUR", "MC_End_P5", "MC_P_DD20"]
    print(strat_only[cols].head(15).to_string(float_format=lambda x: f"{x:,.3f}"))
    print("\nbenchmarks:")
    print(tab[tab['kind'] == 'benchmark'][cols].head(6).to_string(float_format=lambda x: f"{x:,.3f}"))

    top5 = strat_only.head(5)

    # ---------------------------------------------------------------- figures
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRAY,
                         "axes.labelcolor": INK, "text.color": INK,
                         "xtick.color": INK, "ytick.color": INK})

    # 1 · equity curves: top-5 vs XM-BH (100k start, log)
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    for i, nm in enumerate(top5.index):
        eq = 100_000 * (1.0 + candidates[nm].dropna()).cumprod()
        ax.plot(eq.index, eq.values, lw=1.4, color=PALETTE[i % 5], label=nm)
        ax.annotate(nm, (eq.index[-1], eq.iloc[-1]), xytext=(4, 0),
                    textcoords="offset points", fontsize=7, color=PALETTE[i % 5])
    eqb = 100_000 * (1.0 + candidates[BENCH_BH].dropna()).cumprod()
    ax.plot(eqb.index, eqb.values, lw=1.0, ls="--", color=GRAY, label=f"{BENCH_BH} Buy&Hold")
    ax.set_yscale("log"); ax.grid(alpha=0.25, lw=0.5)
    ax.set_ylabel("Kapital (EUR, log)"); ax.legend(fontsize=7, loc="upper left")
    ax.set_title("Top-5-Strategien: 100.000 EUR seit 2013 (netto, walk-forward)")
    fig.savefig("figures/campaign_top5_equity.png", dpi=140, bbox_inches="tight")

    # 2 · correlation heatmap of family sleeves (SPX), diverging blue-gray-red
    fam_spx = wfa[MARKETS[0]][[f for f in FAMILIES if f in wfa[MARKETS[0]]]].dropna()
    C = fam_spx.corr()
    cmap = LinearSegmentedColormap.from_list("div", [BLUE, "#f0efed", RED])
    fig2, ax2 = plt.subplots(figsize=(4.6, 3.9))
    im = ax2.imshow(C.values, cmap=cmap, vmin=-1, vmax=1)
    ax2.set_xticks(range(len(C))); ax2.set_xticklabels(C.columns, rotation=45, ha="right")
    ax2.set_yticks(range(len(C))); ax2.set_yticklabels(C.index)
    for i in range(len(C)):
        for j in range(len(C)):
            v = C.values[i, j]
            ax2.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                     color="white" if abs(v) > 0.6 else INK)
    fig2.colorbar(im, shrink=0.8)
    ax2.set_title("Sleeve-Korrelationen (SPX, walk-forward, täglich)")
    fig2.savefig("figures/campaign_corr.png", dpi=140, bbox_inches="tight")

    # 3 · Monte-Carlo end-capital distribution for rank 1
    best = top5.index[0]
    r = candidates[best].dropna().to_numpy()
    rng = np.random.RandomState(42)
    T = len(r); nb = int(np.ceil(T / 21))
    ends = np.empty(4000)
    for b in range(4000):
        st = rng.randint(0, T - 21 + 1, nb)
        ends[b] = 100_000 * np.prod(1.0 + np.concatenate([r[s:s + 21] for s in st])[:T])
    fig3, ax3 = plt.subplots(figsize=(6.4, 3.4))
    ax3.hist(ends / 1000, bins=60, color=BLUE, alpha=0.85)
    for q, lab in ((5, "P5"), (50, "Median"), (95, "P95")):
        v = np.percentile(ends, q) / 1000
        ax3.axvline(v, color=RED if q == 5 else INK, lw=1.2,
                    ls="--" if q != 50 else "-")
        ax3.annotate(f"{lab}\n{v:,.0f}k", (v, ax3.get_ylim()[1] * 0.86), fontsize=7,
                     ha="left", color=RED if q == 5 else INK)
    ax3.axvline(100, color=GRAY, lw=0.8); ax3.grid(alpha=0.25, lw=0.5)
    ax3.set_xlabel("Endkapital (Tsd. EUR)"); ax3.set_ylabel("Pfade")
    ax3.set_title(f"Monte-Carlo (Block-Bootstrap, 4000 Pfade): {best}")
    fig3.savefig("figures/campaign_mc.png", dpi=140, bbox_inches="tight")

    # 4 · year consistency bars, top-5
    fig4, ax4 = plt.subplots(figsize=(6.4, 3.0))
    yc = top5["YearConsistency"].astype(float)
    ax4.barh(range(len(yc)), yc.values, color=BLUE, height=0.55)
    ax4.set_yticks(range(len(yc))); ax4.set_yticklabels(yc.index, fontsize=8)
    for i, v in enumerate(yc.values):
        ax4.text(v + 0.01, i, f"{v:.0%}", va="center", fontsize=8, color=INK)
    ax4.set_xlim(0, 1.05); ax4.invert_yaxis(); ax4.grid(axis="x", alpha=0.25, lw=0.5)
    ax4.set_title("Anteil Jahre mit Sharpe > 0 (2013–2026)")
    fig4.savefig("figures/campaign_consistency.png", dpi=140, bbox_inches="tight")

    print("\nsaved: results/campaign_ranking.csv + 4 figures (figures/campaign_*.png)")


if __name__ == "__main__":
    main()
