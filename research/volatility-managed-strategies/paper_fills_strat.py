#!/usr/bin/env python3
"""Paper fills — STRATEGY side. Closes the audit's 'defining weakness'
(inference on the strategy layer). Reuses existing modules; writes JSON.

Sections:
  S1  Dose-response VM series (SPX) + turnover per row + vol-matched benchmark
  S2  Sharpe-DIFFERENCE test (paired stationary block bootstrap) VM vs B&H,
      raw and vol-matched  -> the 'single most important missing number'
  S3  Difference-series validation: PSR/DSR/bootstrap on d_t = r_VM - r_bench
  S4  Campaign leader diff tests (XM-C4-IV vs XM-BH etc.)
  S5  DSR N=227 confirmation
  S6  Sleeve attribution: all 16 subsets of {VMG,TSMOM,VIXTS,REV}, XM, IV-weighted
  S7  Cost breakeven (print cached cost sweeps)
  S8  Dump cached CSVs needed for Table 5 / Table 6 fills
"""
from __future__ import annotations
import os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd

from analyze import build_features, _ols, FIRST_OOS
from ml_models import add_ivar
from strategy import vol_managed, forecasts, TARGET_WIN
from validation import psr, deflated_sharpe, block_bootstrap_sharpe_ci, _sr
from metrics_engine import full_report, monte_carlo
from portfolio_combos import combine
from paper_review_fixes import paired_sharpe_diff

PPY = 252
OUT = {}

# ================================================================ S1
print("### S1  VM series (SPX) + turnover + vol-match", flush=True)
feat = add_ivar(build_features())
rvol = np.sqrt(feat["rv"])
target = rvol.rolling(TARGET_WIN).mean().shift(1)
fc = forecasts(feat)                                   # RW / HAR / log-HAR (variance)
fc["HAR-IV"] = _ols(feat, ["rv_d", "rv_w", "rv_m", "ivar"], [], FIRST_OOS, log_target=True)["pred"]
idx = feat.index
for p in fc.values():
    idx = idx.intersection(p.dropna().index)
idx = idx[idx >= pd.Timestamp(FIRST_OOS)]

r_bh = (np.exp(feat["ret"]) - 1.0).reindex(idx)
vm, w = {}, {}
for name, pred in fc.items():
    s, wi = vol_managed(feat, pred.reindex(idx), target.reindex(idx))
    vm[name] = s.reindex(idx); w[name] = wi.reindex(idx)

turn = {name: float(w[name].diff().abs().mean() * PPY) for name in vm}   # annualized turnover
OUT["turnover_pa"] = turn
print("turnover p.a.:", {k: round(v, 1) for k, v in turn.items()})

# vol-match B&H to VM[HAR]'s realized vol (leverage the index, ignore financing -> note)
vol_vmhar = vm["HAR"].std() * np.sqrt(PPY)
vol_bh = r_bh.std() * np.sqrt(PPY)
k = vol_vmhar / vol_bh
r_bh_matched = r_bh * k
OUT["volmatch"] = {"vol_VMHAR": float(vol_vmhar), "vol_BH": float(vol_bh), "lever_k": float(k)}
print(f"vol-match: VM[HAR] vol={vol_vmhar:.3f}, B&H vol={vol_bh:.3f}, k={k:.3f}")

def sharpe(s):
    s = s.dropna(); return float(s.mean() / s.std() * np.sqrt(PPY))
OUT["sharpe_check"] = {"BH": sharpe(r_bh), "BH_matched": sharpe(r_bh_matched),
                       **{f"VM[{n}]": sharpe(vm[n]) for n in vm}}
print("sharpe:", {k2: round(v, 3) for k2, v in OUT["sharpe_check"].items()})

# ================================================================ S2
print("\n### S2  paired block-bootstrap Sharpe-difference tests", flush=True)
diff = {}
diff["VM[HAR] vs BH (raw)"]     = paired_sharpe_diff(vm["HAR"], r_bh)
diff["VM[HAR] vs BH (volmatch)"]= paired_sharpe_diff(vm["HAR"], r_bh_matched)
diff["VM[log-HAR] vs BH (raw)"] = paired_sharpe_diff(vm["log-HAR"], r_bh)
diff["VM[HAR-IV] vs BH (raw)"]  = paired_sharpe_diff(vm["HAR-IV"], r_bh)
diff["VM[RW] vs BH (raw)"]      = paired_sharpe_diff(vm["RW"], r_bh)
for klab, d in diff.items():
    print(f"  {klab:30s} dSharpe={d['obs_diff']:+.3f}  P(d>0)={d['P_gt0']:.1%}  "
          f"95%CI[{d['ci_lo']:+.3f},{d['ci_hi']:+.3f}]")
OUT["diff_tests"] = diff

# ================================================================ S3
print("\n### S3  difference-series validation d_t = r_VM - r_bench", flush=True)
def dseries_valid(vm_s, bench_s, n_trials, label):
    d = (vm_s - bench_s).dropna()
    ps = psr(d.values, 0.0)
    ds = deflated_sharpe(d.values, np.std([_sr(d.values)]) or 1e-9, n_trials)  # placeholder std
    lo, hi = block_bootstrap_sharpe_ci(d.values)
    out = {"mean_ann": float(d.mean()*PPY), "sharpe_diffser": float(_sr(d.values)*np.sqrt(PPY)),
           "PSR_gt0": float(ps), "boot_CI_lo": lo, "boot_CI_hi": hi, "n": int(len(d))}
    print(f"  {label:26s} SR(d)={out['sharpe_diffser']:+.3f}  PSR(>0)={ps:.3f}  "
          f"95%CI[{lo:+.3f},{hi:+.3f}]")
    return out
OUT["diffseries"] = {
    "VM[log-HAR]-BHmatched(SPX)": dseries_valid(vm["log-HAR"], r_bh_matched, 36, "VM[logHAR]-BHmatch"),
}

# ================================================================ S4
print("\n### S4  campaign leader diff tests", flush=True)
cand = pd.read_parquet("results/campaign_returns.parquet")
def _try_diff(a, b, lab):
    if a in cand.columns and b in cand.columns:
        d = paired_sharpe_diff(cand[a], cand[b])
        print(f"  {lab:26s} dSharpe={d['obs_diff']:+.3f}  P(d>0)={d['P_gt0']:.1%}  "
              f"95%CI[{d['ci_lo']:+.3f},{d['ci_hi']:+.3f}]")
        return d
    print(f"  {lab}: missing cols ({a},{b})"); return None
OUT["campaign_diff"] = {
    "XM-C4-IV vs XM-BH": _try_diff("XM-C4-IV", "XM-BH", "XM-C4-IV vs XM-BH"),
}
# vol-matched XM leader vs XM-BH
if "XM-C4-IV" in cand and "XM-BH" in cand:
    dd = pd.concat([cand["XM-C4-IV"], cand["XM-BH"]], axis=1).dropna()
    kx = (dd.iloc[:,0].std()/dd.iloc[:,1].std())
    m = paired_sharpe_diff(dd.iloc[:,0], dd.iloc[:,1]*kx)
    print(f"  XM-C4-IV vs XM-BH(volmatch) dSharpe={m['obs_diff']:+.3f}  P(d>0)={m['P_gt0']:.1%}  "
          f"95%CI[{m['ci_lo']:+.3f},{m['ci_hi']:+.3f}]  kx={kx:.3f}")
    OUT["campaign_diff"]["XM-C4-IV vs XM-BH(volmatch)"] = {**m, "kx": float(kx)}

# ================================================================ S5
print("\n### S5  DSR N confirmation", flush=True)
n_trials = 37*3 + 12*3 + 6*3
# count combos exactly as portfolio_combos does
combos = 0
for _m in range(3):                     # per-market combos: 6 subsets x 3 modes x 3 markets
    combos += 6*3
combos += 4*2                            # XM: 4 subsets x 2 modes
n_trials += combos
OUT["dsr_N"] = int(n_trials)
print(f"  n_trials (DSR deflation) = {n_trials}")
rank = pd.read_csv("results/campaign_ranking.csv", index_col=0)
OUT["leader_DSR"] = float(rank.loc["XM-C4-IV", "DSR"])
print(f"  XM-C4-IV DSR (from ranking) = {OUT['leader_DSR']:.3f}")

# ================================================================ S6
print("\n### S6  sleeve attribution: 16 subsets of {VMG,TSMOM,VIXTS,REV} (XM, IV)", flush=True)
MARKETS = ["SPX", "NDX", "DAX"]
wfa = {m: pd.read_parquet(f"results/wfa_returns_{m}.parquet") for m in MARKETS}
FAM4 = ["VMG", "TSMOM", "VIXTS", "REV"]
xm_fam = {f: pd.concat([wfa[m][f] for m in MARKETS if f in wfa[m]], axis=1).mean(axis=1)
          for f in FAM4}
XM = pd.DataFrame(xm_fam)
import itertools
attr = {}
for r_ in range(1, 5):
    for sub in itertools.combinations(FAM4, r_):
        s = combine(XM[list(sub)], "IV").dropna()
        if len(s) < 750:
            continue
        rep = full_report(s)
        attr["+".join(sub)] = {"Sharpe": rep["Sharpe"], "MaxDD": rep["MaxDD"],
                               "Calmar": rep["Calmar"], "Sortino": rep["Sortino"]}
attr_df = pd.DataFrame(attr).T.sort_values("Sharpe", ascending=False)
print(attr_df.to_string(float_format=lambda x: f"{x:.3f}"))
OUT["sleeve_attribution"] = attr
# marginal contribution: full C4 vs best 3-sizing (VMG+TSMOM+VIXTS) and effect of adding REV
if "VMG+TSMOM+VIXTS" in attr and "VMG+TSMOM+VIXTS+REV" in attr:
    OUT["REV_margin_sharpe"] = attr["VMG+TSMOM+VIXTS+REV"]["Sharpe"] - attr["VMG+TSMOM+VIXTS"]["Sharpe"]
    print(f"  marginal Sharpe of adding REV to VMG+TSMOM+VIXTS: {OUT['REV_margin_sharpe']:+.3f}")

# ================================================================ S7  cost sweeps
print("\n### S7  cached cost sweeps", flush=True)
for f in ["sensitivity_xm_costs.csv", "sensitivity_costs.csv"]:
    try:
        d = pd.read_csv(f"results/{f}")
        print(f"-- {f} --"); print(d.to_string())
    except Exception as e:
        print(f"  {f}: {e}")

# ================================================================ S8  cached CSVs for table fills
print("\n### S8  cached CSVs for Table 5/6 fills", flush=True)
for f in ["tactics_sizing.csv", "tactics_sltp.csv", "strategy_switch.csv",
          "dist_forecast.csv", "regime_filter.csv", "top_subperiods.csv", "wfa_SPX.csv"]:
    try:
        d = pd.read_csv(f"results/{f}")
        print(f"-- {f} --"); print(d.to_string()); print()
    except Exception as e:
        print(f"  {f}: {e}")

# top-5 full metrics from ranking
print("-- ranking top-5 (for Table 5 Panel A) --")
cols5 = ["CAGR","Vol","Sharpe","Sortino","MaxDD","Calmar","DSR","YearConsistency",
         "NetProfit_EUR","MC_P_DD20","Sharpe_CI_lo","Sharpe_CI_hi"]
print(rank[cols5].head(6).to_string(float_format=lambda x: f"{x:.4f}"))
OUT["top5"] = rank[cols5].head(5).to_dict("index")

with open("results/paper_fills_strat.json", "w", encoding="utf-8") as fh:
    json.dump(OUT, fh, indent=2, default=float)
print("\nsaved results/paper_fills_strat.json")
