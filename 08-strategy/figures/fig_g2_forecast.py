"""
Figure 1 (G2) - Forecasting next-month volatility: is the VIX beatable?

Free data: S&P 500 (^GSPC) and VIX (^VIX) daily closes from Yahoo, cached to
data/gspc_daily.csv and data/vix_daily.csv (shared with the G1 figures).

Target (fixed in advance): the mean daily variance over the NEXT 21 trading days,
RV_fwd_t = mean_{k=1..21} r_{t+k}^2, with r = daily log return. Three forecasts
are compared as predictors of RV_fwd:
  - RW  : last month's mean daily variance (random walk in variance).
  - VIX : implied daily variance (VIX/100)^2 / 252.
  - HAR : Corsi's heterogeneous-AR regression of RV_fwd on daily / weekly (5d) /
          monthly (22d) trailing mean daily variance, fitted IN-SAMPLE only.

Split (opened once): out-of-sample = 2020-01-02 onward.
Score: QLIKE = mean(a/p - log(a/p) - 1), lower is better (a=actual, p=forecast);
robust to the heteroskedasticity of variance. Printed in-sample and OOS.

Honest question the figure answers: after decades of academic effort, can a
free-data forecast beat the market's own implied volatility out of sample? The
answer here is "barely, and not reliably" - which is the whole motivation for a
strategy that trades the IV-RV gap rather than a naive vol forecast.

Reproducible:
    python fig_g2_forecast.py     # numpy, matplotlib; stdlib
"""
import os, csv, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OOS_START = "2020-01-02"
H = 21


def load(cache):
    d, c = [], []
    with open(os.path.join(DATA, cache)) as f:
        for row in csv.DictReader(f):
            d.append(row["date"]); c.append(float(row["close"]))
    return d, np.array(c)


gd, gc = load("gspc_daily.csv")
vd, vc = load("vix_daily.csv")
vix = dict(zip(vd, vc))
dates, close, vv = [], [], []
for d, c in zip(gd, gc):
    if d in vix:
        dates.append(d); close.append(c); vv.append(vix[d])
close = np.array(close); vv = np.array(vv)
r = np.concatenate([[0.0], np.diff(np.log(close))])       # daily log return
rv = r ** 2                                                # daily variance proxy
N = len(dates)

# trailing predictors (use info up to and including day t)
def trail_mean(x, w):
    out = np.full(N, np.nan)
    cs = np.concatenate([[0.0], np.cumsum(x)])
    for t in range(N):
        if t + 1 >= w:
            out[t] = (cs[t + 1] - cs[t + 1 - w]) / w
    return out

rv_d = trail_mean(rv, 1)     # ~ yesterday (noisy)
rv_w = trail_mean(rv, 5)
rv_m = trail_mean(rv, 22)

# forward target: mean daily variance over next H days
rv_fwd = np.full(N, np.nan)
cs = np.concatenate([[0.0], np.cumsum(rv)])
for t in range(N - H):
    rv_fwd[t] = (cs[t + 1 + H] - cs[t + 1]) / H

iv_daily = (vv / 100.0) ** 2 / 252.0                       # implied daily variance

ok = ~np.isnan(rv_fwd) & ~np.isnan(rv_m) & (rv_fwd > 0)
idx = np.where(ok)[0]
d_ok = [dates[i] for i in idx]
split = next(k for k, dd in enumerate(d_ok) if dd >= OOS_START)

y = rv_fwd[idx]
Xd, Xw, Xm = rv_d[idx], rv_w[idx], rv_m[idx]
iv = iv_daily[idx]

# HAR fitted IN-SAMPLE only
A_in = np.column_stack([np.ones(split), Xd[:split], Xw[:split], Xm[:split]])
coef, *_ = np.linalg.lstsq(A_in, y[:split], rcond=None)
A_all = np.column_stack([np.ones(len(y)), Xd, Xw, Xm])
har = A_all @ coef
har = np.clip(har, 1e-9, None)

preds = {"RW (last-month var)": np.clip(Xm, 1e-9, None),
         "VIX (implied)": np.clip(iv, 1e-9, None),
         "HAR (free-data model)": har}


def qlike(a, p):
    z = a / p
    return float(np.mean(z - np.log(z) - 1.0))


print(f"sample {d_ok[0]}..{d_ok[-1]}  n={len(y)}  OOS from {OOS_START} (n_oos={len(y)-split})")
print(f"HAR coef [const, daily, weekly, monthly] = {np.round(coef, 4)}")
print(f"{'predictor':22s} {'QLIKE in':>10s} {'QLIKE OOS':>10s}")
scores = {}
for name, p in preds.items():
    qi, qo = qlike(y[:split], p[:split]), qlike(y[split:], p[split:])
    scores[name] = (qi, qo)
    print(f"{name:22s} {qi:10.4f} {qo:10.4f}")
print(f"mean implied vol {np.sqrt(252*iv).mean()*100:.1f}%  "
      f"mean subsequent realized vol {np.sqrt(252*y).mean()*100:.1f}% (annualized)")

# ---------------- figure ------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.8, 3.9),
                               gridspec_kw={"width_ratios": [1.7, 1.0]})
xs = np.arange(len(y))
ax1.plot(xs, np.sqrt(252 * preds["VIX (implied)"]) * 100, lw=0.6, color="#31536e",
         label="VIX (implied, annualized %)")
ax1.plot(xs, np.sqrt(252 * y) * 100, lw=0.6, color="#b0473a", alpha=0.8,
         label="subsequent 21d realized vol (%)")
ax1.axvline(split, color="#999", lw=0.8, ls=":")
ax1.text(split, ax1.get_ylim()[1] * 0.92, " OOS", fontsize=7.5, color="#666")
ax1.set_ylabel("annualized volatility (%)", fontsize=8.6)
ax1.set_title("(a)  Implied vol leads the realized vol that follows it", fontsize=9.5, loc="left")
ax1.legend(fontsize=7.6, frameon=False)
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)
ax1.grid(True, axis="y", alpha=0.25)
yr = [i for i in range(1, len(y)) if d_ok[i][:4] != d_ok[i - 1][:4] and int(d_ok[i][:4]) % 3 == 0]
ax1.set_xticks(yr); ax1.set_xticklabels([d_ok[i][:4] for i in yr], fontsize=8)

names = list(preds.keys())
qoos = [scores[n][1] for n in names]
cols = ["#8a8f98", "#31536e", "#2f6d4f"]
ax2.bar(range(len(names)), qoos, color=cols, width=0.62)
ax2.set_xticks(range(len(names)))
ax2.set_xticklabels(["RW", "VIX", "HAR"], fontsize=8.5)
ax2.set_ylabel("QLIKE, out-of-sample (lower = better)", fontsize=8.2)
ax2.set_title("(b)  OOS forecast error", fontsize=9.5, loc="left")
for i, v in enumerate(qoos):
    ax2.text(i, v, f"{v:.3f}", ha="center", va="bottom", fontsize=7.8)
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
ax2.grid(True, axis="y", alpha=0.25)

fig.text(0.5, -0.02,
         f"Yahoo ^GSPC + ^VIX, {d_ok[0]} to {d_ok[-1]}; target = mean daily variance over next 21 trading days. "
         "HAR fitted in-sample (pre-2020) only; QLIKE scored out-of-sample. (Emp)",
         ha="center", fontsize=7.4, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_g2_forecast.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
