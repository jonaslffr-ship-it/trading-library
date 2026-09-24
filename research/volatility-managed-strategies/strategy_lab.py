#!/usr/bin/env python3
"""Strategy campaign (QR006): pre-registered sleeve families, honestly costed.

Sleeves (grids FIXED in note QR006 before the first run):
  BH            buy & hold benchmark
  VM            volatility-managed on log-HAR forecast (existing Q007 baseline)
  TSMOM         time-series momentum, lookback {63,126,252} x {L/S, L/F} x voltgt {0,1}
  REV           short-term reversal: z(5d)<-thr above SMA200, hold {1,3,5}
  VIXTS         VIX term-structure sizing from FRED VXV/VIX ratio (discrete + continuous)
  TOM           turn-of-month window, last {3,4,5} + first {2,3} trading days
  ON            overnight-only (close->open), optional VIX<25 gate; pays 2x cost daily

NO LOOK-AHEAD: every weight for day t uses information <= t-1 (signals .shift(1);
FRED series are reindexed to trading days, ffilled max 5d, then shifted).
Costs: COST per unit |dw| (close-close sleeves); overnight pays 2*COST*|w| per day.

Outputs per market: results/sleeves_{tag}.csv (full metric suite),
results/sleeve_returns_{tag}.parquet + sleeve_weights_{tag}.parquet (for WFA/combos/MC).

Run from repo root:
  python strategy_lab.py --raw data/raw --tag SPX [--mc]
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd

from src.ingest import COLS, TYPE_LAST
from metrics_engine import full_report

FIRST_OOS = "2013-01-02"
COST = 1e-4
LEV_CAP = 3.0
PROC = "data/processed"


# ---------------------------------------------------------------- data layer
def _load_ohlc(raw_dir: str, tag: str) -> pd.DataFrame:
    """Per-day open (first bar) and close (last bar) from MarketTick 1-min CSVs, cached."""
    cache = os.path.join(PROC, f"ohlc_{tag}.parquet")
    if os.path.exists(cache):
        return pd.read_parquet(cache)
    import glob as _glob
    rows = []
    for f in sorted(_glob.glob(os.path.join(raw_dir, "*.csv"))):
        base = os.path.basename(f)[:8]
        if not base.isdigit():
            continue
        df = pd.read_csv(f, sep=";", header=None, names=COLS)
        df = df[(df["type"] == TYPE_LAST) & (df["close"] > 0)]
        if df.empty:
            continue
        rows.append((pd.Timestamp(base), float(df["open"].iloc[0]), float(df["close"].iloc[-1])))
    out = pd.DataFrame(rows, columns=["date", "open", "close"]).set_index("date").sort_index()
    os.makedirs(PROC, exist_ok=True)
    out.to_parquet(cache)
    return out


def _load_feat(raw_dir: str, tag: str) -> pd.DataFrame:
    """RV features (rv, HAR lags) via analyze.build_features, cached."""
    cache = os.path.join(PROC, f"feat_{tag}.parquet")
    if os.path.exists(cache):
        return pd.read_parquet(cache)
    from analyze import build_features
    feat = build_features(raw_dir)[["rv", "rv_d", "rv_w", "rv_m", "close", "ret"]]
    feat.to_parquet(cache)
    return feat


def _vm_pred(feat: pd.DataFrame, tag: str) -> pd.Series:
    """log-HAR expanding OOS variance forecast, cached."""
    cache = os.path.join(PROC, f"vmpred_{tag}.parquet")
    if os.path.exists(cache):
        return pd.read_parquet(cache)["pred"]
    from analyze import _expanding_ols
    pred = _expanding_ols(feat, ["rv_d", "rv_w", "rv_m"], FIRST_OOS, log=True)["pred"]
    pred.to_frame("pred").to_parquet(cache)
    return pred


def _fred(name: str) -> pd.Series:
    df = pd.read_csv(f"data/macro/{name}.csv", parse_dates=["observation_date"],
                     index_col="observation_date")
    return df[name].astype(float)


def build_panel(raw_dir: str, tag: str) -> tuple[pd.DataFrame, pd.Series]:
    ohlc = _load_ohlc(raw_dir, tag)
    feat = _load_feat(raw_dir, tag)
    idx = feat.index.intersection(ohlc.index)
    p = pd.DataFrame(index=idx)
    p["open"], p["close"] = ohlc["open"].reindex(idx), ohlc["close"].reindex(idx)
    p["ret"] = np.log(p["close"]).diff()                       # close->close log
    p["ret_on"] = np.log(p["open"]) - np.log(p["close"].shift(1))   # overnight log
    p["ret_id"] = np.log(p["close"]) - np.log(p["open"])            # intraday log
    p["rv"] = feat["rv"].reindex(idx)
    p["rvol"] = np.sqrt(p["rv"])
    # FRED series -> trading days, information as of t-1
    vix, vxv = _fred("VIXCLS"), _fred("VXVCLS")
    p["vix_l1"] = vix.reindex(idx).ffill(limit=5).shift(1)
    p["ts_ratio_l1"] = (vxv / vix).reindex(idx).ffill(limit=5).shift(1)
    pred = _vm_pred(feat, tag).reindex(idx)
    return p, pred


# ---------------------------------------------------------------- execution
def run_weights(p: pd.DataFrame, w: pd.Series, overnight: bool = False,
                cost: float = COST) -> pd.Series:
    """Net daily simple strategy returns for weight series w (set at t-1)."""
    if overnight:
        r_asset = np.exp(p["ret_on"]) - 1.0
        cost_t = cost * 2.0 * w.abs()          # enter at close t-1, exit at open t
    else:
        r_asset = np.exp(p["ret"]) - 1.0
        dw = w.diff().abs().fillna(w.abs())
        cost_t = cost * dw
    return (w * r_asset - cost_t).rename("strat")


# ---------------------------------------------------------------- sleeves
def sleeve_bh(p):
    return pd.Series(1.0, index=p.index)


def sleeve_vm(p, pred):
    target = p["rvol"].rolling(63).mean().shift(1)
    sd_hat = np.sqrt(pred.clip(lower=1e-12))
    return (target / sd_hat).clip(0.0, LEV_CAP)


def sleeve_tsmom(p, lookback: int, long_short: bool, voltgt: bool):
    mom = p["ret"].rolling(lookback).sum().shift(1)
    direction = np.sign(mom) if long_short else (mom > 0).astype(float)
    if voltgt:
        tau = p["rvol"].rolling(63).mean().shift(1)
        sd_hat = p["rvol"].rolling(21).mean().shift(1)
        scale = (tau / sd_hat).clip(0.0, LEV_CAP)
    else:
        scale = 1.0
    return (direction * scale).where(mom.notna())


def sleeve_reversal(p, thr: float, hold: int):
    ret5 = p["ret"].rolling(5).sum()
    z = ((ret5 - ret5.rolling(252).mean()) / ret5.rolling(252).std()).shift(1)
    uptrend = (p["close"] > p["close"].rolling(200).mean()).shift(1)
    sig = ((z < -thr) & uptrend.fillna(False)).astype(float)
    return sig.rolling(hold, min_periods=1).max().where(z.notna())


def sleeve_vixts_disc(p, thr: float, w_low: float):
    r = p["ts_ratio_l1"]
    return pd.Series(np.where(r > thr, 1.0, w_low), index=p.index).where(r.notna())


def sleeve_vixts_cont(p, a: float):
    r = p["ts_ratio_l1"]
    return (a * (r - 0.9)).clip(0.0, 1.5).where(r.notna())


def sleeve_tom(p, n_last: int, n_first: int):
    per = p.index.to_period("M")
    rank = pd.Series(np.arange(len(p)), index=p.index).groupby(per).cumcount()
    mlen = per.value_counts().sort_index()
    month_len = pd.Series(per.map(mlen).to_numpy(), index=p.index)
    w = ((rank < n_first) | (rank >= month_len - n_last)).astype(float)
    return w


def sleeve_overnight(p, vix_gate: float | None):
    w = pd.Series(1.0, index=p.index)
    if vix_gate is not None:
        w = w.where(p["vix_l1"] < vix_gate, 0.0).where(p["vix_l1"].notna())
    return w


# ---------------------------------------------------------------- campaign
def campaign_sleeves(p: pd.DataFrame, pred: pd.Series) -> dict[str, tuple[pd.Series, bool]]:
    """name -> (weights, overnight_flag). Grids exactly as pre-registered (QR006)."""
    s: dict[str, tuple[pd.Series, bool]] = {
        "BH": (sleeve_bh(p), False),
        "VM[logHAR]": (sleeve_vm(p, pred), False),
    }
    for lb in (63, 126, 252):
        for ls in (True, False):
            for vt in (True, False):
                tag = f"TSMOM{lb}|{'LS' if ls else 'LF'}|{'VT' if vt else 'raw'}"
                s[tag] = (sleeve_tsmom(p, lb, ls, vt), False)
    for thr in (0.75, 1.0, 1.5):
        for hold in (1, 3, 5):
            s[f"REV|z{thr}|h{hold}"] = (sleeve_reversal(p, thr, hold), False)
    for thr in (1.00, 1.05):
        for wl in (0.0, 0.3):
            s[f"VIXTS|d{thr}|w{wl}"] = (sleeve_vixts_disc(p, thr, wl), False)
    for a in (1.5, 2.0):
        s[f"VIXTS|c{a}"] = (sleeve_vixts_cont(p, a), False)
    for nl in (3, 4, 5):
        for nf in (2, 3):
            s[f"TOM|l{nl}f{nf}"] = (sleeve_tom(p, nl, nf), False)
    s["ON|base"] = (sleeve_overnight(p, None), True)
    s["ON|vix25"] = (sleeve_overnight(p, 25.0), True)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--tag", default="SPX")
    ap.add_argument("--mc", action="store_true", help="add Monte-Carlo per sleeve (slow)")
    args = ap.parse_args()

    p, pred = build_panel(args.raw, args.tag)
    print(f"{args.tag}: panel {p.index.min().date()} -> {p.index.max().date()} ({len(p)} days)")

    # honest overnight-vs-intraday decomposition (gross, diagnostic for Q013)
    oos = p[p.index >= pd.Timestamp(FIRST_OOS)]
    gross_on = (np.exp(oos["ret_on"]) - 1.0).mean() * 252
    gross_id = (np.exp(oos["ret_id"]) - 1.0).mean() * 252
    print(f"  gross ann. mean OOS: overnight {gross_on:+.2%}  intraday {gross_id:+.2%}")

    sleeves = campaign_sleeves(p, pred)
    rets, wts, rows = {}, {}, {}
    for name, (w, is_on) in sleeves.items():
        strat = run_weights(p, w, overnight=is_on)
        strat = strat[strat.index >= pd.Timestamp(FIRST_OOS)].dropna()
        if len(strat) < 500:
            print(f"  ! {name}: only {len(strat)} OOS days, skipped")
            continue
        rets[name] = strat
        wts[name] = w.reindex(strat.index)
        rows[name] = full_report(strat, wts[name], mc=args.mc)

    tab = pd.DataFrame(rows).T
    front = ["CAGR", "Vol", "Sharpe", "Sortino", "MaxDD", "Calmar", "ProfitFactor",
             "WinRate_d", "Trades", "WinRate_t", "CRV", "Expectancy_EUR",
             "NetProfit_EUR", "N_days"]
    tab = tab[[c for c in front if c in tab.columns] +
              [c for c in tab.columns if c not in front]]
    os.makedirs("results", exist_ok=True)
    tab.to_csv(f"results/sleeves_{args.tag}.csv")
    pd.DataFrame(rets).to_parquet(f"results/sleeve_returns_{args.tag}.parquet")
    pd.DataFrame(wts).to_parquet(f"results/sleeve_weights_{args.tag}.parquet")

    show = tab[["Sharpe", "Sortino", "MaxDD", "Calmar", "ProfitFactor", "Trades",
                "NetProfit_EUR"]].sort_values("Sharpe", ascending=False)
    print(f"\n=== {args.tag} sleeves (net, OOS {FIRST_OOS}+, cost {COST*1e4:.0f}bp) ===")
    print(show.to_string(float_format=lambda x: f"{x:,.3f}"))
    print(f"\nconfigs run: {len(rows)}  -> results/sleeves_{args.tag}.csv")


if __name__ == "__main__":
    main()
