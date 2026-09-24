"""
Figure (RV walkthrough) - close-to-close realized volatility, computed by hand
on the last ~21 S&P 500 sessions.

Free data: daily S&P 500 (^GSPC) closes from Yahoo Finance's public chart API,
cached to data/spx_daily.csv so the figure is reproducible offline and stable.
The script takes the most recent 22 closes (-> 21 daily returns, roughly one
trading month), computes each day's simple percent return, the mean return,
each day's deviation from the mean, the squared deviations, the average squared
deviation (variance), the daily volatility (its square root), and the
annualized realized volatility (x sqrt(252)). The FULL day-by-day table is
printed so the paper can reproduce it verbatim.

No estimator search, no window tuning: 21 returns (one trading month) was fixed
in advance as the standard textbook window.

Reproducible:
    python fig_rv_walkthrough.py     # numpy, matplotlib; stdlib urllib/json
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
N = 21                                   # returns in the window (fixed in advance)
d = dates[-(N + 1):]                     # 22 closes -> 21 returns
c = close[-(N + 1):]
r = (c[1:] / c[:-1] - 1.0) * 100.0       # simple percent returns

mean = r.mean()
dev = r - mean
dev2 = dev ** 2
var = dev2.mean()                        # average squared deviation (population)
daily_vol = np.sqrt(var)                 # percent per day
ANN = np.sqrt(252.0)
ann_vol = daily_vol * ANN                # percent per year

# ---- full table for the paper ----
print("day | date | close | return_% | dev_from_mean | dev_squared")
for i in range(N):
    print(f"{i+1:2d} | {d[i+1]} | {c[i+1]:9.2f} | {r[i]:+7.3f} | {dev[i]:+7.3f} | {dev2[i]:7.4f}")
print(f"mean_return_pct={mean:+.4f}")
print(f"sum_dev2={dev2.sum():.4f}  avg_dev2(variance)={var:.4f}")
print(f"daily_vol_pct={daily_vol:.4f}  sqrt252={ANN:.4f}  annualized_RV_pct={ann_vol:.2f}")
print(f"window={d[1]}..{d[-1]}  first_close={c[0]:.2f} ({d[0]})")

# ---- figure ----
fig, ax = plt.subplots(figsize=(6.8, 3.9))
x = np.arange(N)
colors = ["#2f6d4f" if v >= 0 else "#7c1c2c" for v in r]
ax.bar(x, r, color=colors, width=0.62)
ax.axhline(0, color="#999", lw=0.8)
ax.axhline(mean + daily_vol, color="#17120e", lw=1.0, ls="--")
ax.axhline(mean - daily_vol, color="#17120e", lw=1.0, ls="--")
ax.annotate(f"+1 daily σ = {mean + daily_vol:+.2f}%", xy=(0.1, mean + daily_vol),
            xytext=(0.1, mean + daily_vol + 0.10), fontsize=8.6, color="#17120e")
ax.annotate(f"−1 daily σ = {mean - daily_vol:+.2f}%", xy=(0.1, mean - daily_vol),
            xytext=(0.1, mean - daily_vol - 0.22), fontsize=8.6, color="#17120e")
step = 3
ax.set_xticks(x[::step])
ax.set_xticklabels([d[1:][i][5:] for i in range(0, N, step)], fontsize=8)
ax.set_xlabel("session (month-day)")
ax.set_ylabel("daily return (%)")
ax.set_title(f"21 S&P 500 daily returns → daily vol {daily_vol:.2f}% → annualized RV {ann_vol:.1f}%",
             fontsize=10.2)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.03,
         f"Yahoo daily ^GSPC closes, {d[1]}–{d[-1]} (last {N} sessions of the cached series). "
         f"Dashed lines: mean return ± one daily standard deviation.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_rv_walkthrough.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
