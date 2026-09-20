"""
Figure - Post-publication decay on one series: rolling Sharpe of the TSMOM
sign rule on the S&P 500, with the publication year (2012) marked.

Free data: daily S&P 500 (^GSPC) from Yahoo Finance's public chart API
(range=max), cached to data/spx_daily_max.csv (shared with the other figures
of this paper). The strategy is the identical frozen specification of
fig_tsmom_haircut.py, step (i): at each month-end, long if the trailing
12-month return is positive, short otherwise; the position earns the next
month's return; gross, no costs, no lag - deliberately the PAPER-FAITHFUL
version, so that the pre/post split isolates the sample period and nothing
else.

This is ONE series and therefore an illustration of the McLean-Pontiff
post-publication-decay shape, not a cross-sectional test; the caption in the
paper says so. Printed: full-sample, pre-2012 and post-2012 Sharpe, and the
rolling-window minimum/maximum after publication.

Reproducible:
    python fig_decay_split.py     # numpy, matplotlib; stdlib urllib/json
"""
import os, json, csv, socket, urllib.request, datetime as dt
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
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
           "?range=max&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    j = json.loads(urllib.request.urlopen(req).read())
    r = j["chart"]["result"][0]
    ts, cl = r["timestamp"], r["indicators"]["quote"][0]["close"]
    dates, close = [], []
    for t, c in zip(ts, cl):
        if c is None or c <= 0:
            continue
        dates.append(dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"))
        close.append(float(c))
    with open(CACHE, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "close"])
        for d, c in zip(dates, close):
            w.writerow([d, f"{c:.4f}"])
    return dates, np.array(close)


dates, close = load_prices()
n = len(close)
month = [d[:7] for d in dates]
me = [i for i in range(n - 1) if month[i] != month[i + 1]]
me.append(n - 1)
me = np.array(me)
C = close[me]                                       # month-end closes
mkeys = [month[i] for i in me]

LOOKBACK = 12
# strategy month j earns sig(j-1) * monthly return j (decision strictly first)
mret = C[1:] / C[:-1] - 1.0                         # mret[j-1]: month j return
strat, skeys = [], []
for j in range(LOOKBACK + 1, len(C)):
    r12 = C[j - 1] / C[j - 1 - LOOKBACK] - 1.0
    s = 1.0 if r12 > 0 else -1.0
    strat.append(s * mret[j - 1])
    skeys.append(mkeys[j])
strat = np.array(strat)
yrs = np.array([int(k[:4]) + (int(k[5:7]) - 0.5) / 12.0 for k in skeys])

ANN = np.sqrt(12.0)
def sharpe(x):
    s = x.std()
    return (x.mean() / s) * ANN if s > 0 else 0.0

WIN = 60                                            # rolling 5 years
roll = np.full(len(strat), np.nan)
for j in range(WIN - 1, len(strat)):
    roll[j] = sharpe(strat[j - WIN + 1:j + 1])

PUB = 2012.0
pre = strat[yrs < PUB]
post = strat[yrs >= PUB]
sh_full, sh_pre, sh_post = sharpe(strat), sharpe(pre), sharpe(post)
post_roll = roll[(yrs >= PUB) & ~np.isnan(roll)]

fig, ax = plt.subplots(figsize=(7.4, 4.0))
ax.plot(yrs, roll, color="#17120e", lw=1.4)
ax.axhline(0, color="#999", lw=0.8)
ax.axvline(PUB, color="#7c1c2c", lw=1.2, ls="--")
ax.annotate("Moskowitz-Ooi-Pedersen\npublished (2012)", xy=(PUB, ax.get_ylim()[1]),
            xytext=(PUB - 24.5, 2.55), fontsize=8.4, color="#7c1c2c")
ax.axhline(sh_pre, xmax=(PUB - yrs[0]) / (yrs[-1] - yrs[0]),
           color="#2f6d4f", lw=1.1, ls=":")
ax.axhline(sh_post, xmin=(PUB - yrs[0]) / (yrs[-1] - yrs[0]),
           color="#8a6d3b", lw=1.1, ls=":")
ax.annotate(f"pre-2012 Sharpe {sh_pre:.2f}", xy=(yrs[0] + 2, sh_pre + 0.07),
            fontsize=8.6, color="#2f6d4f")
ax.annotate(f"post-2012 Sharpe {sh_post:.2f}", xy=(PUB + 1.0, sh_post + 0.07),
            fontsize=8.6, color="#8a6d3b")
ax.set_xlabel("year")
ax.set_ylabel(f"rolling {WIN // 12}-year annualized Sharpe ratio")
ax.set_title("TSMOM sign rule on the S&P 500, gross: before and after publication",
             fontsize=10.2)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.02,
         f"Yahoo daily ^GSPC (range=max), {dates[0]} to {dates[-1]}; monthly, gross, no costs/lag; "
         f"{len(strat)} strategy months. One series - an illustration of the decay shape, "
         f"not a cross-sectional test.",
         ha="center", fontsize=7.4, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_decay_split.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={dates[0]}..{dates[-1]} n_strategy_months={len(strat)}")
print(f"Sharpe full={sh_full:.3f} pre2012={sh_pre:.3f} post2012={sh_post:.3f} "
      f"(pre n={len(pre)}, post n={len(post)})")
print(f"rolling5y post-2012: min={np.nanmin(post_roll):.3f} max={np.nanmax(post_roll):.3f} "
      f"last={roll[-1]:.3f}")
