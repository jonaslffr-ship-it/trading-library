"""
Figure 1 (Statistics for Traders) - What daily returns actually look like.

Free data: the full available daily history of the S&P 500 (^GSPC) from Yahoo
Finance's public chart API (range=max reaches back to the late 1920s), cached to
data/spx_daily_max.csv so the figure is reproducible offline and stable. The
figure shows the histogram of daily simple returns on a LOG count scale with the
best-fitting normal distribution (same mean, same standard deviation) overlaid.
On a log scale, single-day bins far out in the tails stay visible - which is the
whole point: 1987-10-19, the worst day of October 2008, and the worst day of
March 2020 are marked individually, and the normal curve collapses to
(effectively) zero long before it reaches them.

Printed to stdout: sample span and size, mean/std, skewness, excess kurtosis,
the three marked dates with their returns, and the count of |r| > 4 sigma days
against the count a normal distribution would predict for a sample this size.

No strategy, no tuning - purely descriptive statistics of one public series.

Reproducible:
    python fig_return_histogram.py     # numpy, matplotlib; stdlib urllib/json
"""
import os, json, csv, math, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
CACHE = os.path.join(DATA, "spx_daily_max.csv")


def load_prices():
    if os.path.exists(CACHE):
        dates, close = [], []
        with open(CACHE) as f:
            for row in csv.DictReader(f):
                dates.append(row["date"]); close.append(float(row["close"]))
        return dates, np.array(close)
    socket.setdefaulttimeout(60)
    # NOTE: "range=max&interval=1d" silently degrades to coarse (3-month) bars;
    # explicit epoch bounds keep daily granularity over the full history.
    p2 = int(dt.datetime.now().timestamp())
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
           f"?period1=-2208988800&period2={p2}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    j = json.loads(urllib.request.urlopen(req).read())
    r = j["chart"]["result"][0]
    ts, cl = r["timestamp"], r["indicators"]["quote"][0]["close"]
    dates, close = [], []
    epoch = dt.datetime(1970, 1, 1)
    for t, c in zip(ts, cl):
        if c is None:
            continue
        # timedelta arithmetic instead of utcfromtimestamp: Windows rejects
        # negative epochs, and pre-1970 history needs them.
        dates.append((epoch + dt.timedelta(seconds=int(t))).strftime("%Y-%m-%d"))
        close.append(float(c))
    with open(CACHE, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "close"])
        for d, c in zip(dates, close):
            w.writerow([d, f"{c:.4f}"])
    return dates, np.array(close)


dates, close = load_prices()
ret = np.diff(close) / close[:-1]               # daily simple returns
rdates = dates[1:]                              # date of each return
r_pct = ret * 100.0
n = len(ret)

mu, sd = r_pct.mean(), r_pct.std()
z = (r_pct - mu) / sd
skew = float((z ** 3).mean())
exkurt = float((z ** 4).mean() - 3.0)

# The three marked days: 1987-10-19, worst day of 2008-10, worst day of 2020-03.
def worst_in(prefix):
    idx = [i for i, d in enumerate(rdates) if d.startswith(prefix)]
    i = min(idx, key=lambda k: r_pct[k])
    return rdates[i], r_pct[i]

marks = []
i87 = rdates.index("1987-10-19")
marks.append(("1987-10-19", r_pct[i87]))
marks.append(worst_in("2008-10"))
marks.append(worst_in("2020-03"))

# Tail count: |r| beyond 4 standard deviations, vs. the normal expectation.
n_4s = int((np.abs(z) > 4).sum())
p_4s = math.erfc(4 / math.sqrt(2))              # two-sided normal tail beyond 4 sigma
exp_4s = n * p_4s

fig, ax = plt.subplots(figsize=(6.8, 4.2))
bins = np.arange(math.floor(r_pct.min()) - 0.5, math.ceil(r_pct.max()) + 0.75, 0.25)
cnt, edges, _ = ax.hist(r_pct, bins=bins, color="#4a6d8c", alpha=0.85,
                        edgecolor="white", linewidth=0.2, label="observed daily returns")
xg = np.linspace(edges[0], edges[-1], 800)
pdf = np.exp(-0.5 * ((xg - mu) / sd) ** 2) / (sd * math.sqrt(2 * math.pi))
ax.plot(xg, pdf * n * 0.25, "-", color="#7c1c2c", lw=1.7,
        label=f"normal with the same mean and SD")
ax.set_yscale("log")
ax.set_ylim(0.5, cnt.max() * 2.5)
for (d, r), dy in zip(marks, (7.5, 2.6, 4.5)):
    ax.annotate(f"{d}\n{r:.1f}%", xy=(r, 1.0), xytext=(r - 0.6, dy),
                fontsize=7.6, color="#17120e", ha="center",
                arrowprops=dict(arrowstyle="->", color="#17120e", lw=0.8))
ax.set_xlabel("daily return (%)")
ax.set_ylabel("number of days (log scale)")
ax.set_title("S&P 500 daily returns vs. the normal curve: the tails are where history lives",
             fontsize=10.2)
ax.legend(fontsize=8, loc="upper left", frameon=False)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.text(0.5, -0.02,
         f"Yahoo daily ^GSPC, {dates[0]}–{dates[-1]}, {n:,} daily returns. "
         f"Skew {skew:.2f}, excess kurtosis {exkurt:.1f}; {n_4s} days beyond 4σ vs. "
         f"{exp_4s:.1f} expected if returns were normal.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_return_histogram.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={dates[0]}..{dates[-1]} n_returns={n} mean_pct={mu:.4f} sd_pct={sd:.4f}")
print(f"skew={skew:.3f} excess_kurtosis={exkurt:.2f}")
for d, r in marks:
    print(f"marked {d}: {r:.2f}%  ({(r - mu) / sd:+.1f} sigma)")
print(f"days_beyond_4sigma={n_4s} normal_expectation={exp_4s:.2f} ratio={n_4s / exp_4s:.0f}x")
