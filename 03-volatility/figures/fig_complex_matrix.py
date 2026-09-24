"""
Figure 3 - Correlation structure of the Cboe volatility-index complex: daily
LEVELS versus daily CHANGES, on one common sample.

Free data: Cboe's public daily-history CSVs
(https://cdn.cboe.com/api/global/us_indices/daily_prices/<TICKER>_History.csv),
cached to data/. Members: VIX, VIX3M, VXN, VVIX, SKEW, COR1M. (FRED mirrors
VIX/VIX3M/VXN as VIXCLS/VXVCLS/VXNCLS but timed out at build time; VVIX, SKEW
and COR1M are Cboe-only anyway, so the Cboe originals are used throughout.)
The common sample is fixed by the shortest history (VIX3M, from 2009-09-18).

ONE transparent, pre-committed rule (no selection, no search): Pearson
correlation on the intersection of all six series' dates, computed twice -
once on closing levels, once on one-day differences. Both matrices are printed
in full and reported as-is.

Reproducible:
    python fig_complex_matrix.py     # numpy, matplotlib; stdlib urllib/csv
"""
import os, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
BASE = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{}_History.csv"
TICKERS = ["VIX", "VIX3M", "VXN", "VVIX", "SKEW", "COR1M"]


def load(ticker):
    path = os.path.join(DATA, f"{ticker}_History.csv")
    if not (os.path.exists(path) and os.path.getsize(path) > 0):
        try:
            socket.setdefaulttimeout(60)
            req = urllib.request.Request(BASE.format(ticker),
                                         headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req).read()
            if not raw:
                raise ValueError("empty response")
            tmp = path + ".part"
            with open(tmp, "wb") as f:
                f.write(raw)
            os.replace(tmp, path)
        except Exception as e:
            print(f"SKIPPED (offline / no cache): {os.path.basename(path)} - "
                  f"{type(e).__name__}: {e}")
            raise SystemExit(0)
    out = {}
    with open(path) as f:
        rdr = csv.reader(f)
        head = next(rdr)
        col = len(head) - 1                      # CLOSE (OHLC files) or value col
        for row in rdr:
            d = dt.datetime.strptime(row[0], "%m/%d/%Y").date()
            try:
                out[d] = float(row[col])
            except ValueError:
                pass
    return out


series = {t: load(t) for t in TICKERS}
days = sorted(set.intersection(*[set(s) for s in series.values()]))
X = np.array([[series[t][d] for d in days] for t in TICKERS])   # 6 x n
D = np.diff(X, axis=1)
C_lvl = np.corrcoef(X)
C_chg = np.corrcoef(D)

fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.6))
for ax, C, title in [(axes[0], C_lvl, "daily levels"),
                     (axes[1], C_chg, "daily changes")]:
    im = ax.imshow(C, vmin=-1, vmax=1, cmap="RdBu_r", alpha=0.85)
    ax.set_xticks(range(len(TICKERS)))
    ax.set_yticks(range(len(TICKERS)))
    ax.set_xticklabels(TICKERS, fontsize=8, rotation=45, ha="right")
    ax.set_yticklabels(TICKERS, fontsize=8)
    ax.set_title(f"Pearson correlation, {title}", fontsize=9.5)
    for i in range(len(TICKERS)):
        for j in range(len(TICKERS)):
            ax.text(j, i, f"{C[i, j]:.2f}", ha="center", va="center",
                    fontsize=7.4,
                    color="white" if abs(C[i, j]) > 0.65 else "#17120e")
    for s in ax.spines.values():
        s.set_visible(False)
fig.colorbar(im, ax=axes, shrink=0.75, label="correlation")
fig.suptitle("The Cboe volatility complex: one tight VIX-family block, "
             "with SKEW as the orthogonal axis", fontsize=10.5, y=0.99)
fig.text(0.5, -0.02,
         f"Cboe daily-history CSVs, common sample {days[0]}..{days[-1]} "
         f"({len(days)} sessions, fixed by the shortest history, VIX3M).",
         ha="center", fontsize=7.6, color="#666")
OUT = os.path.join(HERE, "fig_complex_matrix.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"common sample {days[0]}..{days[-1]} n={len(days)}")


def show(C, name):
    print(name)
    print("        " + "".join(f"{t:>8}" for t in TICKERS))
    for i, t in enumerate(TICKERS):
        print(f"{t:>7} " + "".join(f"{C[i, j]:8.3f}" for j in range(len(TICKERS))))


show(C_lvl, "levels:")
show(C_chg, "changes:")

# descriptive ranges on the same common sample (quoted in the paper's Sec. 6)
print("ranges (common sample):")
for i, t in enumerate(TICKERS):
    s = X[i]
    p10, p50, p90 = np.percentile(s, [10, 50, 90])
    print(f"  {t:>6}: p10={p10:.1f} median={p50:.1f} p90={p90:.1f} "
          f"min={s.min():.1f} max={s.max():.1f} latest({days[-1]})={s[-1]:.2f}")
r = X[TICKERS.index("VXN")] / X[TICKERS.index("VIX")]
p10, p50, p90 = np.percentile(r, [10, 50, 90])
print(f"  VXN/VIX ratio: p10={p10:.3f} median={p50:.3f} p90={p90:.3f} "
      f"min={r.min():.3f} max={r.max():.3f} latest={r[-1]:.3f} "
      f"pct_days_VXN_above_VIX={100.0 * np.mean(r > 1):.1f}")
