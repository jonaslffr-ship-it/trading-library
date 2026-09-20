#!/usr/bin/env python3
"""SPX realized-volatility OOS forecasting: HAR family vs. benchmarks.

Confirmatory (PREREGISTRATION.md / vault QR002): log-HAR has a LOWER out-of-sample
QLIKE than the Random Walk on SPX, h=1. First OOS 2013-01-02. Exploratory: EWMA / AR /
GARCH(1,1) benchmarks, HAR-CJ, horizons h=5,22. Loss QLIKE (primary) + MSE; tests
Diebold-Mariano and Clark-West (nested). Seed 42.

Run from repo root:  python analyze.py [--garch]
"""
from __future__ import annotations

import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")

from src.ingest import load_days
from src.realized import daily_features, add_har_lags
from src.evaluate import qlike, mse, diebold_mariano, clark_west

FIRST_OOS = "2013-01-02"
FREQ = "5min"
EPS = 1e-12
MIN_VAR = 1e-6  # variance floor (~1.6% annualized) for QLIKE robustness (level models)
HORIZONS = [1, 5, 22]
np.random.seed(42)


def build_features(raw_dir="data/raw"):
    px = load_days(raw_dir)
    feat = daily_features(px, freq=FREQ)
    feat = add_har_lags(feat, col="rv")
    feat["c"] = feat["bv"]
    close = px.groupby(px.index.date).last()
    close.index = pd.to_datetime(close.index)
    feat["close"] = close.reindex(feat.index)
    feat["ret"] = np.log(feat["close"]).diff()
    feat["ret_neg"] = feat["ret"].clip(upper=0.0)                        # leverage term (LHAR)
    feat["harq_x"] = np.sqrt(feat["rq"].clip(lower=0.0)) * feat["rv_d"]  # HARQ interaction
    return feat.dropna(subset=["rv_d", "rv_w", "rv_m"]).sort_index()


def _expanding_ols(feat, cols, first_oos, log=False, h=1):
    """Direct h-step OLS: predict rv[t] from feat[cols] at t-h, expanding refit."""
    d = pd.concat([feat[cols].shift(h), feat["rv"].rename("y")], axis=1).dropna()
    dates = d.index
    Xall = d[cols].to_numpy(float)
    yall = d["y"].to_numpy(float)
    start = int(dates.searchsorted(pd.Timestamp(first_oos)))
    preds = np.full(len(d), np.nan)
    for i in range(start, len(d)):
        Xtr = np.log(np.clip(Xall[:i], EPS, None)) if log else Xall[:i]
        ytr = np.log(np.clip(yall[:i], EPS, None)) if log else yall[:i]
        A = np.column_stack([np.ones(i), Xtr])
        beta, *_ = np.linalg.lstsq(A, ytr, rcond=None)
        xi = np.log(np.clip(Xall[i], EPS, None)) if log else Xall[i]
        yhat = float(np.concatenate([[1.0], xi]) @ beta)
        if log:
            yhat = float(np.exp(yhat + 0.5 * (ytr - A @ beta).var()))
        preds[i] = min(max(yhat, MIN_VAR), 4.0 * float(yall[:i].max()))  # insanity filter (BPQ)
    return pd.DataFrame({"pred": preds, "actual": yall}, index=dates).iloc[start:]


def _ols(feat, log_cols, lin_cols, first_oos, log_target=False, h=1):
    """Expanding-OLS forecaster: log_cols enter as log(.), lin_cols raw; target log or level."""
    cols = list(log_cols) + list(lin_cols)
    d = pd.concat([feat[cols].shift(h), feat["rv"].rename("y")], axis=1).dropna()
    dates = d.index
    nlog = len(log_cols)
    X = d[cols].to_numpy(float)
    y = d["y"].to_numpy(float)
    start = int(dates.searchsorted(pd.Timestamp(first_oos)))
    preds = np.full(len(d), np.nan)
    for i in range(start, len(d)):
        Xl = np.log(np.clip(X[:i, :nlog], EPS, None)) if nlog else np.empty((i, 0))
        A = np.column_stack([np.ones(i), Xl, X[:i, nlog:]])
        yt = np.log(np.clip(y[:i], EPS, None)) if log_target else y[:i]
        beta, *_ = np.linalg.lstsq(A, yt, rcond=None)
        xl = np.log(np.clip(X[i, :nlog], EPS, None)) if nlog else np.empty(0)
        yhat = float(np.concatenate([[1.0], xl, X[i, nlog:]]) @ beta)
        if log_target:
            yhat = float(np.exp(yhat + 0.5 * (yt - A @ beta).var()))
        preds[i] = min(max(yhat, MIN_VAR), 4.0 * float(y[:i].max()))  # insanity filter (BPQ)
    return pd.DataFrame({"pred": preds, "actual": y}, index=dates).iloc[start:]


def _lag(feat, pred, first_oos):
    d = pd.DataFrame({"pred": pred, "actual": feat["rv"]}).dropna()
    return d[d.index >= pd.Timestamp(first_oos)]


def garch(feat, first_oos):
    """GARCH(1,1) on daily returns -> 1-step conditional-variance forecast (expanding)."""
    from arch import arch_model
    r = (feat["ret"] * 100.0).dropna()      # scaled for numerical stability
    dates = r.index
    start = int(dates.searchsorted(pd.Timestamp(first_oos)))
    preds = pd.Series(np.nan, index=dates)
    for i in range(start, len(dates)):
        res = arch_model(r.iloc[:i], mean="Constant", vol="GARCH", p=1, q=1,
                         rescale=False).fit(disp="off", show_warning=False)
        preds.iloc[i] = res.forecast(horizon=1, reindex=False).variance.values[-1, 0] / 1e4
    d = pd.DataFrame({"pred": preds, "actual": feat["rv"].reindex(dates)}).dropna()
    return d[d.index >= pd.Timestamp(first_oos)]


def qloss(a, f):
    r = a / np.clip(f, MIN_VAR, None)
    return r - np.log(r) - 1.0


def metrics(a, p, prw):
    return {"QLIKE": qlike(a, np.clip(p, MIN_VAR, None)),
            "MSE_x1e8": mse(a, p) * 1e8,
            "OOS_R2_vs_RW": 1 - np.sum((a - p) ** 2) / np.sum((a - prw) ** 2)}


def align(models):
    idx = None
    for m in models.values():
        idx = m.index if idx is None else idx.intersection(m.index)
    return {k: v.loc[idx] for k, v in models.items()}, idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--garch", action="store_true", help="add GARCH(1,1) benchmark (slow)")
    ap.add_argument("--raw", default="data/raw", help="raw daily-CSV directory")
    ap.add_argument("--tag", default="SPX", help="market label for output filenames")
    args = ap.parse_args()

    feat = build_features(args.raw)
    print(args.tag, "RV days:", len(feat), "|", feat.index.min().date(), "->", feat.index.max().date())

    m1 = {
        "RW": _lag(feat, feat["rv"].shift(1), FIRST_OOS),
        "EWMA(0.94)": _lag(feat, feat["rv"].ewm(alpha=0.06, adjust=False).mean().shift(1), FIRST_OOS),
        "AR(1)-logRV": _expanding_ols(feat, ["rv_d"], FIRST_OOS, log=True),
        "HAR": _expanding_ols(feat, ["rv_d", "rv_w", "rv_m"], FIRST_OOS, log=False),
        "log-HAR": _expanding_ols(feat, ["rv_d", "rv_w", "rv_m"], FIRST_OOS, log=True),
        "HAR-CJ": _expanding_ols(feat, ["c", "jump", "rv_w", "rv_m"], FIRST_OOS, log=False),
        "HAR-RS": _ols(feat, [], ["rs_m", "rs_p", "rv_w", "rv_m"], FIRST_OOS, log_target=False),
        "HARQ": _ols(feat, [], ["rv_d", "harq_x", "rv_w", "rv_m"], FIRST_OOS, log_target=False),
        "LHAR": _ols(feat, [], ["rv_d", "rv_w", "rv_m", "ret_neg"], FIRST_OOS, log_target=False),
    }
    if args.garch:
        print("fitting GARCH(1,1) with expanding refit (~minutes)...")
        m1["GARCH(1,1)"] = garch(feat, FIRST_OOS)
    m1, idx1 = align(m1)
    a1 = m1["RW"]["actual"].to_numpy()
    prw1 = m1["RW"]["pred"].to_numpy()
    combo_members = ["log-HAR", "HARQ", "HAR-RS", "LHAR"]
    m1["Combo-EW"] = pd.DataFrame(
        {"pred": np.mean([m1[k]["pred"].to_numpy() for k in combo_members], axis=0), "actual": a1},
        index=idx1)
    print("common OOS obs (h=1):", len(idx1), "|", idx1.min().date(), "->", idx1.max().date())

    rows = []
    for name, dfm in m1.items():
        r = metrics(a1, dfm["pred"].to_numpy(), prw1)
        r.update(model=name, h=1)
        rows.append(r)

    p_lh = m1["log-HAR"]["pred"].to_numpy()
    dm_stat, dm_p = diebold_mariano(qloss(a1, prw1), qloss(a1, p_lh))
    cw_stat, cw_p = clark_west(a1, prw1, p_lh)
    print(f"\n=== h=1 metrics ({args.tag}, OOS from {FIRST_OOS}) ===")
    print(pd.DataFrame(rows).set_index("model")[["QLIKE", "MSE_x1e8", "OOS_R2_vs_RW"]]
          .to_string(float_format=lambda x: f"{x:.5f}"))
    print("\nConfirmatory log-HAR vs RW: QLIKE %.4f vs %.4f | DM p=%.3g | Clark-West p=%.4g | dir=%s"
          % (qlike(a1, p_lh), qlike(a1, prw1), dm_p, cw_p, bool(qlike(a1, p_lh) < qlike(a1, prw1))))

    print("\n=== multi-horizon (RW / HAR / log-HAR) ===")
    for h in HORIZONS:
        mh, _ = align({
            "RW": _lag(feat, feat["rv"].shift(h), FIRST_OOS),
            "HAR": _expanding_ols(feat, ["rv_d", "rv_w", "rv_m"], FIRST_OOS, log=False, h=h),
            "log-HAR": _expanding_ols(feat, ["rv_d", "rv_w", "rv_m"], FIRST_OOS, log=True, h=h),
        })
        a = mh["RW"]["actual"].to_numpy(); prw = mh["RW"]["pred"].to_numpy()
        for name, dfm in mh.items():
            r = metrics(a, dfm["pred"].to_numpy(), prw)
            r.update(model=name, h=h)
            rows.append(r)
            if name != "RW":
                print(f"  h={h:2d} {name:8s} QLIKE={r['QLIKE']:.4f}  OOS-R2={r['OOS_R2_vs_RW']:.3f}")

    tag = args.tag
    csv_path = "results/oos_metrics.csv" if tag == "SPX" else f"results/oos_metrics_{tag}.csv"
    fig_path = "figures/oos_logHAR_vs_actual.png" if tag == "SPX" else f"figures/oos_{tag}_logHAR.png"
    pd.DataFrame(rows).set_index(["h", "model"]).sort_index().to_csv(csv_path)
    seg = m1["log-HAR"].iloc[-120:]
    av = lambda s: np.sqrt(s * 252) * 100
    ax = av(seg["actual"]).plot(lw=0.9, label="realized", color="#211c18")
    av(seg["pred"]).plot(ax=ax, lw=0.9, label="log-HAR forecast", color="#7c1c2c")
    ax.legend(); ax.set_ylabel("RVol (%)"); ax.set_xlabel("")
    ax.set_title(f"{tag} OOS: log-HAR forecast vs. realized (last 120 days)")
    ax.figure.savefig(fig_path, dpi=130, bbox_inches="tight")
    print(f"\nsaved: {csv_path}, {fig_path}")


if __name__ == "__main__":
    main()
