"""
Figure - PROXY study for gamma-regime conditioning (this is NOT a GEX study).

Free historical strike-level open interest is not available in this paper's
pipeline, so dealer gamma cannot be reconstructed historically here. This
figure conditions on the VIX level instead - an observable, free variable
that correlates with (but does not identify) the dealer-gamma regime. The
paper text is explicit about why this is only a proxy.

Pre-committed design (fixed before the data were examined, no variants tried):
  - data: SPX daily closes (data/spx_daily.csv, Yahoo ^GSPC, 2011-2026) and
    VIX daily closes (data/vix_daily.csv, Yahoo ^VIX; FRED VIXCLS is the
    documented alternative);
  - regime: tercile of the VIX close on day t; breakpoints estimated on the
    IN-SAMPLE period only (dates <= 2021-12-31) and applied unchanged
    out-of-sample (>= 2022-01-01);
  - metrics, both strictly after the conditioning day: (a) mean absolute
    next-day return |r(t+1)|; (b) first-order autocorrelation measured as the
    Pearson correlation of the pair (r(t+1), r(t+2)) across days t in the cell;
  - 95% CIs: normal approximation for the mean, Fisher z for the correlation;
  - report every cell, whatever it shows.

Reproducible:
    python fig_regime_proxy.py     # numpy, matplotlib; stdlib csv
"""
import os, csv, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SPLIT = "2021-12-31"          # in-sample <= SPLIT < out-of-sample


def read_csv(name):
    dates, close = [], []
    with open(os.path.join(DATA, name)) as f:
        for row in csv.DictReader(f):
            dates.append(row["date"]); close.append(float(row["close"]))
    return dates, np.array(close)


sd, sc = read_csv("spx_daily.csv")
vd, vc = read_csv("vix_daily.csv")
vix = dict(zip(vd, vc))
dates, close, vixv = [], [], []
for d_, c_ in zip(sd, sc):
    if d_ in vix:
        dates.append(d_); close.append(c_); vixv.append(vix[d_])
close, vixv = np.array(close), np.array(vixv)
ret = np.diff(close) / close[:-1]          # ret[i] = return on dates[i+1]

# day index t runs over positions where r(t+1) and r(t+2) exist:
# t = 0 .. len(dates)-3 ; r(t+1) = ret[t], r(t+2) = ret[t+1]
tmax = len(dates) - 3
tidx = np.arange(tmax + 1)
day = np.array(dates)[tidx]
v_t = vixv[tidx]
r1 = ret[tidx]           # next-day return after conditioning day t
r2 = ret[tidx + 1]       # the day after that

is_mask = day <= SPLIT
q1, q2 = np.quantile(v_t[is_mask], [1 / 3, 2 / 3])
terc = np.digitize(v_t, [q1, q2])          # 0 low, 1 mid, 2 high


def cell(mask):
    a, b = r1[mask], r2[mask]
    n = mask.sum()
    m_abs = np.abs(a).mean()
    ci_abs = 1.96 * np.abs(a).std(ddof=1) / math.sqrt(n)
    rho = np.corrcoef(a, b)[0, 1]
    z = 0.5 * math.log((1 + rho) / (1 - rho))
    zlo, zhi = z - 1.96 / math.sqrt(n - 3), z + 1.96 / math.sqrt(n - 3)
    lo, hi = math.tanh(zlo), math.tanh(zhi)
    return n, m_abs, ci_abs, rho, lo, hi


labels = ["low VIX", "mid VIX", "high VIX"]
res = {}
for pname, pmask in (("IS", is_mask), ("OOS", ~is_mask)):
    for k in range(3):
        res[(pname, k)] = cell(pmask & (terc == k))

x = np.arange(3)
w = 0.36
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.4, 3.9))
for ax, mi, ei_lo, ei_hi, title, ylab in (
        (ax1, 3, 4, 5, "lag-1 autocorrelation of returns",
         "corr( r(t+1), r(t+2) )"),
        (ax2, 1, None, None, "mean absolute next-day return",
         "mean |r(t+1)| (%)")):
    for off, pname, colr in ((-w / 2, "IS", "#17120e"), (w / 2, "OOS", "#b0713a")):
        vals, los, his = [], [], []
        for k in range(3):
            c = res[(pname, k)]
            if mi == 3:
                vals.append(c[3]); los.append(c[3] - c[4]); his.append(c[5] - c[3])
            else:
                vals.append(c[1] * 100)
                los.append(c[2] * 100); his.append(c[2] * 100)
        ax.bar(x + off, vals, w, color=colr, alpha=0.88,
               label=f"{pname}" if ax is ax1 else None,
               yerr=[los, his], capsize=3,
               error_kw=dict(lw=0.9, ecolor="#666"))
    ax.axhline(0, color="#999", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_title(title, fontsize=9.8)
    ax.set_ylabel(ylab, fontsize=9)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.grid(True, axis="y", alpha=0.25)
ax1.legend(fontsize=8.6, frameon=False, loc="lower left")
fig.suptitle("PROXY for regime conditioning: SPX daily dynamics by prior-day "
             "VIX tercile (this is not a GEX series)", fontsize=10.2, y=1.02)
fig.text(0.5, -0.04,
         f"Yahoo ^GSPC x ^VIX, {dates[0]} to {dates[-1]}; in-sample <= {SPLIT} "
         f"(tercile breakpoints {q1:.1f} / {q2:.1f} estimated in-sample only), "
         f"out-of-sample 2022-2026. Error bars: 95% CIs (Fisher z / normal).",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_regime_proxy.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={dates[0]}..{dates[-1]} n_days={len(dates)} split={SPLIT} "
      f"breakpoints=({q1:.2f},{q2:.2f})")
for pname in ("IS", "OOS"):
    for k in range(3):
        n, m_abs, ci_abs, rho, lo, hi = res[(pname, k)]
        print(f"{pname:>3} {labels[k]:>8}: n={n:4d}  mean|r+1|={m_abs*100:.3f}% "
              f"(+/-{ci_abs*100:.3f})  rho1={rho:+.3f} [{lo:+.3f},{hi:+.3f}]")
