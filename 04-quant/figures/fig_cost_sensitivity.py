"""
Figure 2 - How transaction costs kill an apparent edge.

Free data: daily S&P 500 (^GSPC) from Yahoo Finance's public chart API, cached
to data/spx_daily.csv so the figure is reproducible offline and stable. ONE
transparent, pre-committed strategy is scored - a 1-day reversal (hold a long
after a down day, a short after an up day; the classic short-horizon reversal).
It is scored gross, then net of a sweep of per-trade costs; annualized Sharpe is
plotted against one-way cost. The break-even cost is where the apparent edge dies.

No strategy search, no threshold tuning: the rule is fixed in advance and reported
as-is (this figure is about costs, not about finding an edge).

Reproducible:
    python fig_cost_sensitivity.py     # numpy, matplotlib; stdlib urllib/json
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


dates, close = load_prices()
ret = np.diff(close) / close[:-1]              # daily simple returns; ret[j] ~ day j+1
sig = -np.sign(ret[:-1])                        # position on day j+1, decided at close of day j
g = sig * ret[1:]                               # gross strategy return (no look-ahead)
dpos = np.abs(np.diff(np.concatenate([[0.0], sig])))   # |change in position| = turnover units
ANN = np.sqrt(252.0)


def sharpe(x):
    s = x.std()
    return (x.mean() / s) * ANN if s > 0 else 0.0


costs = np.linspace(0, 6, 61)                   # one-way cost per unit turnover, bps
sh = np.array([sharpe(g - (c / 1e4) * dpos) for c in costs])
gross = sharpe(g)

be = None
for i in range(1, len(costs)):
    if sh[i - 1] > 0 and sh[i] <= 0:
        be = costs[i - 1] + (costs[i] - costs[i - 1]) * (sh[i - 1] / (sh[i - 1] - sh[i]))
        break
rt_per_year = dpos.mean() / 2 * 252             # round trips per year (a flip trades 2 units)

fig, ax = plt.subplots(figsize=(6.6, 4.0))
ax.plot(costs, sh, "-", color="#17120e", lw=1.9)
ax.axhline(0, color="#999", lw=0.8)
ax.plot(0, gross, "o", color="#2f6d4f", ms=6)
ax.annotate(f"gross Sharpe {gross:.2f}", xy=(0, gross), xytext=(0.35, gross + 0.04),
            fontsize=9, color="#2f6d4f")
if be is not None:
    ax.axvline(be, color="#7c1c2c", lw=1.2, ls="--")
    ax.annotate(f"break-even ≈ {be:.1f} bps", xy=(be, 0),
                xytext=(be + 0.25, max(gross * 0.45, 0.12)), fontsize=9, color="#7c1c2c",
                arrowprops=dict(arrowstyle="->", color="#7c1c2c", lw=0.8))
ax.set_xlabel("one-way transaction cost per unit turnover (bps)")
ax.set_ylabel("annualized Sharpe ratio (net)")
ax.set_title("A textbook 1-day reversal on the S&P 500 dies within a few bps of cost",
             fontsize=10.2)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.02,
         f"Yahoo daily ^GSPC, {dates[0]}–{dates[-1]}, {len(close)} sessions. "
         f"~{rt_per_year:.0f} round trips/yr; signal uses only day t−1 (no look-ahead).",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_cost_sensitivity.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={dates[0]}..{dates[-1]} n={len(close)} gross_Sharpe={gross:.3f} "
      f"break_even_bps={be} rt_per_year={rt_per_year:.0f} "
      f"net@1bps={sharpe(g-(1/1e4)*dpos):.3f} net@2bps={sharpe(g-(2/1e4)*dpos):.3f}")
