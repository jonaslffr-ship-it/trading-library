"""
Figure 4 - The variance risk premium on free data.

Free data: VIX daily closes from FRED (VIXCLS, cached to data/vixcls.csv by the
companion Level-1/2 papers) and S&P 500 daily closes from Yahoo's public chart
API (cached to data/spx_daily.csv by fig_rv_estimators / the companion papers).
Series are inner-joined on date; the common daily span (SPX daily cache begins
2011) sets the sample, printed at run time.

Units (stated in advance): monthly percentage variance. Implied leg
IV2_t = VIX_t^2 / 12; realized leg RV_t = sum of squared daily percentage log
returns over the NEXT 21 trading days. VRP_t = IV2_t - RV_t.

Pre-registered protocol (fixed before computing anything):
  - H0: mean VRP <= 0. H1: mean VRP > 0 (variance sells at a premium).
  - Primary metric: mean VRP in monthly %^2 with a Newey-West t-statistic
    (21 lags, overlapping windows); secondary: share of days with VRP > 0.
  - Split: out-of-sample = 2020-01-02 onward (same single split date used
    throughout the paper), opened once.

Printed: full-sample / in-sample / OOS mean premium, NW t-stats, hit shares,
the five deepest inversions, and mean implied vs realized vol in vol points.

Reproducible:
    python fig_vrp.py     # numpy, matplotlib; stdlib urllib/json; math.erf
"""
import os, csv, json, math, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
SPX_CACHE = os.path.join(DATA, "spx_daily.csv")
VIX_CACHE = os.path.join(DATA, "vixcls.csv")
OOS_START = "2020-01-02"
H = 21


def load_spx():
    """Daily SPX closes from the shared cache (columns: date, close)."""
    d, c = [], []
    with open(SPX_CACHE) as f:
        for row in csv.DictReader(f):
            d.append(row["date"]); c.append(float(row["close"]))
    return d, np.array(c)


spx_d, spx_c = load_spx()
vix = {}
with open(VIX_CACHE) as f:
    for row in csv.DictReader(f):
        v = row["VIXCLS"]
        if v not in ("", "."):
            vix[row["observation_date"]] = float(v)

# inner join
dates, close, vixv = [], [], []
for d, c in zip(spx_d, spx_c):
    if d in vix:
        dates.append(d); close.append(c); vixv.append(vix[d])
close = np.array(close); vixv = np.array(vixv)
r = 100.0 * np.diff(np.log(close))          # daily % log returns; r[i] = day i+1
N = len(dates)

# realized monthly variance over NEXT 21 trading days, at day t (index into dates)
cs = np.concatenate([[0.0], np.cumsum(r ** 2)])
rv_fwd = np.full(N, np.nan)
for t in range(N - H):
    rv_fwd[t] = cs[t + H] - cs[t]           # sum of r^2 for days t+1 .. t+21
iv2 = vixv ** 2 / 12.0
ok = ~np.isnan(rv_fwd)
vrp = iv2 - rv_fwd

idx = np.array([i for i in range(N) if ok[i]])
d_ok = [dates[i] for i in idx]
vrp_ok = vrp[idx]; iv2_ok = iv2[idx]; rv_ok = rv_fwd[idx]


def nw_t(x, lags):
    xm = x.mean(); xd = x - xm; n = len(x)
    s = np.sum(xd * xd) / n
    for k in range(1, lags + 1):
        s += 2 * (1 - k / (lags + 1)) * np.sum(xd[k:] * xd[:-k]) / n
    return xm / math.sqrt(s / n)


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


split = next(i for i, d in enumerate(d_ok) if d >= OOS_START)
segs = {"full": np.arange(len(vrp_ok)), "in-sample (pre-2020)": np.arange(split),
        "OOS (2020-)": np.arange(split, len(vrp_ok))}
print(f"joined sample {d_ok[0]}..{d_ok[-1]}  n={len(vrp_ok)} overlapping 21d windows")
for k, ii in segs.items():
    x = vrp_ok[ii]
    t = nw_t(x, H)
    print(f"  {k:22s} mean VRP={x.mean():7.2f} %^2/mo  NW t={t:5.2f} "
          f"(one-sided p={1 - phi(t):.1e})  hit share={100 * (x > 0).mean():.1f}%")
print(f"  mean implied vol {vixv[idx].mean():.2f}%  "
      f"mean subsequent realized vol {np.sqrt(12 * rv_ok).mean():.2f}% (vol points)")
worst = np.argsort(vrp_ok)[:5]
print("  deepest inversions:", [(d_ok[i], round(float(vrp_ok[i]), 1)) for i in sorted(worst)])
neg_share = 100 * (vrp_ok < 0).mean()
print(f"  share of days with VRP<0: {neg_share:.1f}%")

# ---------------- figure ------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(6.9, 5.8), sharex=True, gridspec_kw={"height_ratios": [1.4, 1.0]})
xs = np.arange(len(d_ok))
ax1.plot(xs, vixv[idx], lw=0.5, color="#31536e", label="VIX (implied, annualized %)")
ax1.plot(xs, np.sqrt(12 * rv_ok), lw=0.5, color="#b0473a", alpha=0.75,
         label="subsequent 21d realized vol (annualized %)")
ax1.set_ylabel("volatility (%)")
ax1.legend(fontsize=7.5, frameon=False)
ax1.set_title("(a)  Implied vol and the realized vol that followed it", fontsize=9.5,
              loc="left")
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)
ax1.grid(True, axis="y", alpha=0.25)

ax2.fill_between(xs, np.clip(vrp_ok, 0, None), 0, color="#2f6d4f", alpha=0.55,
                 lw=0, label="VRP > 0 (premium earned)")
ax2.fill_between(xs, np.clip(vrp_ok, None, 0), 0, color="#7c1c2c", alpha=0.75,
                 lw=0, label="VRP < 0 (inversion)")
ax2.axhline(0, color="#666", lw=0.7)
ax2.set_ylabel("VRP (monthly %$^2$)")
ax2.set_ylim(-350, 150)
ax2.legend(fontsize=7.5, frameon=False, loc="lower left")
ax2.set_title("(b)  The premium is small, steady, and occasionally violently negative",
              fontsize=9.5, loc="left")
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
ax2.grid(True, axis="y", alpha=0.25)
years = [i for i in range(1, len(d_ok)) if d_ok[i][:4] != d_ok[i - 1][:4]
         and int(d_ok[i][:4]) % 4 == 2]
ax2.set_xticks(years); ax2.set_xticklabels([d_ok[i][:4] for i in years], fontsize=8)

fig.text(0.5, -0.015,
         f"FRED VIXCLS + Yahoo ^GSPC (inner join), {d_ok[0]} to {d_ok[-1]}. "
         "VRP = VIX$^2$/12 minus next-21-day realized variance; overlapping windows; "
         "panel (b) clipped at -350 (the 2020 crash reaches further).",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_vrp.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
