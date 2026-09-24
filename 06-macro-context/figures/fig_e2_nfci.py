"""
Figure 4 (E2) - Chicago Fed NFCI vs. subsequent 21-trading-day S&P 500 returns.

Pre-committed split, chosen before looking at returns: loose = NFCI < 0,
tight = NFCI >= 0. Zero is the index's own historical average by construction,
so the threshold is not fitted to this sample.

Timing (implementable): the NFCI for the week ending Friday d is published the
following Wednesday, so entry is the first SPX trading day at least 5 calendar
days after d; the forward return is close[t+21]/close[t]-1. Windows overlap
across adjacent weeks, so naive CIs overstate precision - a non-overlapping
subsample (every 5th week) is also reported. Extreme-tightness tail (NFCI > 1)
reported separately as the honest counterexample.

Data: FRED NFCI (weekly, 1971->), Yahoo ^GSPC daily (cached), both in data/.

Reproducible:
    python fig_e2_nfci.py    # numpy, matplotlib; stdlib urllib/csv
"""
import os, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)

cache = os.path.join(DATA, "fred_NFCI.csv")
if not (os.path.exists(cache) and os.path.getsize(cache) > 0):
    try:
        socket.setdefaulttimeout(60)
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NFCI"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        raw = urllib.request.urlopen(req).read()
        if not raw:
            raise ValueError("empty response")
        tmp = cache + ".part"
        with open(tmp, "wb") as f:
            f.write(raw)
        os.replace(tmp, cache)
    except Exception as e:
        print(f"SKIPPED (offline / no cache): fred_NFCI.csv - "
              f"{type(e).__name__}: {e}")
        raise SystemExit(0)
nf_d, nf_v = [], []
with open(cache) as f:
    rdr = csv.reader(f)
    next(rdr)
    for row in rdr:
        if len(row) < 2 or row[1] in (".", ""):
            continue
        nf_d.append(row[0]); nf_v.append(float(row[1]))
nf_v = np.array(nf_v)

sp_dates, sp_close = [], []
with open(os.path.join(DATA, "spx_daily_max.csv")) as f:
    for row in csv.DictReader(f):
        sp_dates.append(row["date"]); sp_close.append(float(row["close"]))
sp_close = np.array(sp_close)
sp_ord = np.array([dt.date.fromisoformat(d).toordinal() for d in sp_dates])

H = 21          # forward horizon in trading days
LAG = 5         # calendar days from week-ending Friday to the Wednesday release
xs, ys = [], []
for d, v in zip(nf_d, nf_v):
    entry_ord = dt.date.fromisoformat(d).toordinal() + LAG
    i = np.searchsorted(sp_ord, entry_ord)
    if i + H >= len(sp_close):
        continue
    xs.append(v); ys.append(sp_close[i + H] / sp_close[i] - 1.0)
xs = np.array(xs); ys = np.array(ys)


def stats(mask, stride=1):
    idx = np.where(mask)[0][::stride]
    z = ys[idx]
    n = len(z)
    mu = z.mean() * 100
    ci = 1.96 * z.std(ddof=1) / np.sqrt(n) * 100 if n > 1 else np.nan
    return mu, ci, n


loose, tight, extreme = xs < 0, xs >= 0, xs > 1
mu_l, ci_l, n_l = stats(loose)
mu_t, ci_t, n_t = stats(tight)
# non-overlapping: stride the WHOLE weekly series by 5 first, then split
sub = np.zeros(len(xs), bool); sub[::5] = True
mu_l5, ci_l5, n_l5 = stats(loose & sub)
mu_t5, ci_t5, n_t5 = stats(tight & sub)
mu_e, ci_e, n_e = stats(extreme)

fig, ax = plt.subplots(figsize=(8.6, 4.4))
ax.plot(xs, ys * 100, ".", color="#888", ms=2.4, alpha=0.28, rasterized=True)
ax.axvline(0, color="#999", lw=0.9)
ax.axhline(0, color="#999", lw=0.8)
for mu, ci, xpos, col, lbl in [
        (mu_l, ci_l, xs[loose].mean(), "#2f6d4f", f"loose: {mu_l:+.2f}%"),
        (mu_t, ci_t, xs[tight].mean(), "#7c1c2c", f"tight: {mu_t:+.2f}%")]:
    ax.errorbar([xpos], [mu], yerr=[ci], fmt="o", color=col, ms=7,
                capsize=4, lw=1.6, zorder=5)
    ax.annotate(lbl, xy=(xpos, mu), xytext=(xpos + 0.16, mu + 3.2),
                fontsize=9, color=col)
ax.errorbar([xs[extreme].mean()], [mu_e], yerr=[ci_e], fmt="s", color="#31607e",
            ms=6, capsize=4, lw=1.4, zorder=5)
ax.annotate(f"NFCI > 1: {mu_e:+.2f}%", xy=(xs[extreme].mean(), mu_e),
            xytext=(xs[extreme].mean() - 0.4, mu_e - 6.5), fontsize=8.6,
            color="#31607e")
ax.set_xlabel("NFCI (0 = historical average; positive = tighter than average)")
ax.set_ylabel("next 21-trading-day SPX return (%)")
ax.set_title("Financial conditions and forward equity returns: loose beats tight on average - "
             "except at the crisis extreme", fontsize=10)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.03,
         f"FRED NFCI weekly {nf_d[0]}..{nf_d[-1]} (n={len(xs)} usable weeks) x Yahoo ^GSPC daily. "
         "Entry lagged 5 calendar days (Wednesday release); overlapping windows - see non-overlapping CIs in text.",
         ha="center", fontsize=7.4, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_e2_nfci.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"weeks used={len(xs)} span={nf_d[0]}..{nf_d[-1]}")
print(f"loose (NFCI<0):  mean={mu_l:+.3f}% CI±{ci_l:.3f} n={n_l}   "
      f"non-overlap: {mu_l5:+.3f}% CI±{ci_l5:.3f} n={n_l5}")
print(f"tight (NFCI>=0): mean={mu_t:+.3f}% CI±{ci_t:.3f} n={n_t}   "
      f"non-overlap: {mu_t5:+.3f}% CI±{ci_t5:.3f} n={n_t5}")
print(f"extreme (NFCI>1): mean={mu_e:+.3f}% CI±{ci_e:.3f} n={n_e}")
print(f"spread loose-tight = {mu_l-mu_t:+.3f}pp per 21td")
print(f"corr(NFCI level, fwd 21td ret) = {np.corrcoef(xs, ys)[0,1]:+.3f}")
print(f"share of weeks loose = {loose.mean()*100:.1f}%")
