"""
Figure 3 (Statistics for Traders) - Returns don't remember; volatility does.

Free data: daily S&P 500 (^GSPC) from Yahoo Finance's public chart API, cached
to data/spx_daily.csv (shared with the Track C2 figures) so the figure is
reproducible offline and stable. Two autocorrelation functions are computed on
the same series, lags 1-20:

  - autocorrelation of the daily returns themselves (does today's return
    predict tomorrow's?), and
  - autocorrelation of the ABSOLUTE daily returns (does today's SIZE of move
    predict tomorrow's size?).

An approximate two-sided 95% noise band (+-1.96/sqrt(N)) shows what pure
noise would produce. Printed to stdout: sample size, the lag-1 values for
both series, and how many of the 20 |return| lags clear the noise band.

Purely descriptive - no strategy, no tuning, no threshold search.

Reproducible:
    python fig_autocorrelation.py     # numpy, matplotlib; stdlib urllib/json
"""
import os, json, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
CACHE = os.path.join(DATA, "spx_daily.csv")


def load_prices():
    if os.path.exists(CACHE):
        dates, close = [], []
        with open(CACHE) as f:
            for row in csv.DictReader(f):
                dates.append(row["date"]); close.append(float(row["close"]))
        return dates, np.array(close)
    socket.setdefaulttimeout(30)
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=15y&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    j = json.loads(urllib.request.urlopen(req).read())
    r = j["chart"]["result"][0]
    ts, cl = r["timestamp"], r["indicators"]["quote"][0]["close"]
    dates, close = [], []
    for t, c in zip(ts, cl):
        if c is None:
            continue
        dates.append(dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"))
        close.append(float(c))
    with open(CACHE, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "close"])
        for d, c in zip(dates, close):
            w.writerow([d, f"{c:.4f}"])
    return dates, np.array(close)


def acf(x, max_lag):
    x = x - x.mean()
    denom = (x * x).sum()
    return np.array([(x[k:] * x[:-k]).sum() / denom for k in range(1, max_lag + 1)])


dates, close = load_prices()
ret = np.diff(close) / close[:-1]
n = len(ret)
LAGS = 20
a_ret = acf(ret, LAGS)
a_abs = acf(np.abs(ret), LAGS)
band = 1.96 / np.sqrt(n)
sig_abs = int((np.abs(a_abs) > band).sum())
sig_ret = int((np.abs(a_ret) > band).sum())

fig, ax = plt.subplots(figsize=(6.8, 4.0))
k = np.arange(1, LAGS + 1)
w = 0.38
ax.bar(k - w / 2, a_ret, width=w, color="#4a6d8c", label="daily returns")
ax.bar(k + w / 2, a_abs, width=w, color="#b0713a", label="absolute daily returns")
ax.axhspan(-band, band, color="#999", alpha=0.18,
           label="approx. 95% band for pure noise")
ax.axhline(0, color="#999", lw=0.8)
ax.set_xlabel("lag (trading days)")
ax.set_ylabel("autocorrelation")
ax.set_xticks(k[1::2])
ax.set_title("Direction is near-unpredictable; the size of moves clusters for weeks",
             fontsize=10.2)
ax.legend(fontsize=8, loc="upper right", frameon=False)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.02,
         f"Yahoo daily ^GSPC, {dates[0]}–{dates[-1]}, {n:,} daily returns. "
         f"Lag-1 autocorrelation: returns {a_ret[0]:+.3f}, absolute returns {a_abs[0]:+.3f}.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_autocorrelation.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={dates[0]}..{dates[-1]} n_returns={n} noise_band=+-{band:.4f}")
print(f"lag1_returns={a_ret[0]:+.4f} lag1_abs_returns={a_abs[0]:+.4f}")
print(f"lags_beyond_band_returns={sig_ret}/20 lags_beyond_band_abs={sig_abs}/20")
print("acf_abs lags 1-5:", np.round(a_abs[:5], 3).tolist())
print("acf_ret lags 1-5:", np.round(a_ret[:5], 3).tolist())
