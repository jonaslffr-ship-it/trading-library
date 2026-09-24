"""
Figure 4 (Statistics for Traders) - One pre-committed base-rate table.

Free data: daily S&P 500 (^GSPC) from Yahoo Finance's public chart API, cached
to data/spx_daily.csv (shared with the Track C2 figures). ONE conditional table,
fixed in advance - no condition shopping, no threshold search after seeing the
data. The outcome is always "day t closes up" (return > 0); every condition
uses ONLY information available at the close of day t-1 (no look-ahead):

  - unconditional P(up day)
  - prior day up / prior day down (sign of day t-1's return)
  - close of day t-1 above / at-or-below its own 200-day moving average
  - the four cross cells (prior sign x 200-day side)
  - two deliberately extreme rows, pre-committed to demonstrate the
    small-sample rule of section 5: prior day <= -3%, prior day <= -5%.

Every cell is reported with its n; any cell with n < 15 is flagged as a story,
not a statistic, exactly as the paper preaches. Seeded bootstrap 90% confidence
intervals (10,000 resamples) are drawn for every row. All numbers are printed
and reported honestly, whatever they show.

Reproducible:
    python fig_base_rates.py     # numpy, matplotlib; stdlib urllib/json, seed 42
"""
import os, sys, json, csv, socket, urllib.request, datetime as dt
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
CACHE = os.path.join(DATA, "spx_daily.csv")
rng = np.random.default_rng(42)
N_BOOT = 10_000
MIN_N = 15


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
ret = np.diff(close) / close[:-1]               # ret[i] is the return of day i+1

# 200-day moving average of the close, defined from index 199 onward.
MA = 200
ma = np.convolve(close, np.ones(MA) / MA, mode="valid")   # ma[j] = MA of close[j..j+199]

# Evaluation sample: days t (as return index i, day t = i+1) where BOTH
# yesterday's return and yesterday's 200-day MA exist.
# Return index i needs: prior return i-1 (i >= 1) and MA at close index i
# (close index of yesterday = i, MA defined when i >= MA-1).
start = MA - 1                                   # first usable return index
up = (ret[start:] > 0)                           # outcome: day t up?
prior = ret[start - 1:-1]                        # yesterday's return, aligned
above = close[start:-1] > ma[:len(up)]           # yesterday's close vs its 200d MA
assert len(up) == len(prior) == len(above)

rows = [
    ("unconditional",                np.ones(len(up), bool)),
    ("prior day up",                 prior > 0),
    ("prior day down",               prior < 0),
    ("above 200-day average",        above),
    ("at/below 200-day average",     ~above),
    ("prior up  & above 200d",       (prior > 0) & above),
    ("prior up  & below 200d",       (prior > 0) & ~above),
    ("prior down & above 200d",      (prior < 0) & above),
    ("prior down & below 200d",      (prior < 0) & ~above),
    ("prior day ≤ −3%",    prior <= -0.03),
    ("prior day ≤ −5%",    prior <= -0.05),
]

table = []
for name, mask in rows:
    x = up[mask].astype(float)
    nn = len(x)
    if nn == 0:
        table.append((name, 0, 0, np.nan, np.nan, np.nan)); continue
    p = x.mean()
    idx = rng.integers(0, nn, size=(N_BOOT, nn))
    means = x[idx].mean(axis=1)
    lo, hi = np.percentile(means, [5, 95])
    table.append((name, nn, int(x.sum()), p, lo, hi))

uncond_p = table[0][3]

print(f"span={dates[0]}..{dates[-1]} eval_days={len(up)} (first {start} of "
      f"{len(ret)} returns dropped: 200-day average needs history)")
print(f"{'condition':<28}{'n':>6}{'n_up':>7}{'P(up)':>8}{'90% CI':>18}  flag")
for name, nn, nu, p, lo, hi in table:
    flag = "  <-- n<15: story, not statistic" if nn < MIN_N else ""
    ci = f"[{lo:.3f},{hi:.3f}]" if nn else "     -"
    print(f"{name:<28}{nn:>6}{nu:>7}{p:>8.3f}{ci:>18}{flag}")

# ---- figure: horizontal bars with bootstrap CIs, n per cell -----------------
fig, ax = plt.subplots(figsize=(6.8, 4.6))
names = [t[0] for t in table][::-1]
ps = np.array([t[3] for t in table])[::-1]
los = np.array([t[4] for t in table])[::-1]
his = np.array([t[5] for t in table])[::-1]
ns = [t[1] for t in table][::-1]
y = np.arange(len(names))
colors = ["#7c1c2c" if nn < MIN_N else "#4a6d8c" for nn in ns]
ax.barh(y, ps, color=colors, alpha=0.85, height=0.62)
ax.errorbar(ps, y, xerr=[ps - los, his - ps], fmt="none",
            ecolor="#17120e", elinewidth=0.9, capsize=2.5)
ax.axvline(uncond_p, color="#999", lw=1.0, ls="--")
ax.text(uncond_p + 0.004, len(names) - 0.35, f"unconditional {uncond_p:.2f}",
        fontsize=7.4, color="#666")
for yi, (p, nn) in enumerate(zip(ps, ns)):
    tag = f"n={nn}" + ("  n<15 — story, not statistic" if nn < MIN_N else "")
    ax.text(0.012, yi, tag, va="center", fontsize=7.2,
            color="white" if p > 0.10 else "#17120e")
ax.set_yticks(y); ax.set_yticklabels(names, fontsize=8)
ax.set_xlabel("P(next day closes up), with seeded bootstrap 90% CI")
ax.set_xlim(0, 1.0)
ax.set_title("Base rates: one pre-committed table, every cell with its n",
             fontsize=10.2)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="x", alpha=0.25)
fig.text(0.5, -0.015,
         f"Yahoo daily ^GSPC, {dates[0]}–{dates[-1]}, {len(up)} evaluation days. "
         f"Conditions use only day t−1 information (no look-ahead); table fixed "
         f"before computation; red = cell below the n=15 minimum.",
         ha="center", fontsize=7.4, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_base_rates.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
