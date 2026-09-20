"""
Figure 5 (C3) - The base rate itself drifts: P(up day), S&P 500, by decade.

Free data: daily S&P 500 (^GSPC, range=max) from Yahoo Finance's public chart
API, cached to data/spx_daily_max.csv so the figure is reproducible offline.
ONE pre-committed conditioning - the calendar decade - and nothing else: no
alternative windows, no alternative instruments, no threshold search. An "up
day" is close > previous close (unchanged closes count as not-up). 95%
Wilson confidence intervals; partial decades are marked and reported with n.

Reproducible:
    python fig_baserate_drift.py       # numpy, matplotlib; stdlib urllib/json
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
Z = 1.959963984540054      # 95% two-sided normal quantile


def load_prices():
    if os.path.exists(CACHE):
        dates, close = [], []
        with open(CACHE) as f:
            for row in csv.DictReader(f):
                dates.append(row["date"]); close.append(float(row["close"]))
        return dates, np.array(close)
    socket.setdefaulttimeout(30)
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=max&interval=1d"
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


def wilson_ci(k, n, z=Z):
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return center - half, center + half


dates, close = load_prices()
up = (np.diff(close) > 0).astype(int)          # up[j]: day j+1 vs day j
years = np.array([int(d[:4]) for d in dates[1:]])
decades = sorted(set(years // 10 * 10))

rows = []
for dec in decades:
    m = (years // 10 * 10) == dec
    n, k = int(m.sum()), int(up[m].sum())
    lo, hi = wilson_ci(k, n)
    y_min, y_max = int(years[m].min()), int(years[m].max())
    partial = (y_min % 10 != 0) or (y_max % 10 != 9)
    rows.append((dec, n, k, k / n, lo, hi, partial, y_min, y_max))

n_all, k_all = len(up), int(up.sum())
p_all = k_all / n_all

fig, ax = plt.subplots(figsize=(7.4, 4.2))
xs = np.arange(len(rows))
for i, (dec, n, k, p, lo, hi, partial, y0, y1) in enumerate(rows):
    col = "#17120e" if not partial else "#8a6d3b"
    ax.errorbar(i, p, yerr=[[p - lo], [hi - p]], fmt="o", ms=5.5, color=col,
                ecolor=col, elinewidth=1.2, capsize=3)
ax.axhline(p_all, color="#7c1c2c", lw=1.1, ls="--")
ax.annotate(f"full sample {p_all:.3f}", xy=(len(rows) - 0.55, p_all),
            xytext=(len(rows) - 0.55, p_all - 0.0185), fontsize=9,
            color="#7c1c2c", ha="right")
ax.axhline(0.5, color="#bbbbbb", lw=0.8)
ax.set_xticks(xs)
ax.set_xticklabels([f"{dec}s{'*' if partial else ''}\nn={n}"
                    for dec, n, k, p, lo, hi, partial, y0, y1 in rows], fontsize=8)
ax.set_ylabel("P(close up on the day)")
ax.set_title("The unconditional base rate drifts across decades - S&P 500 up-day frequency",
             fontsize=10.3)
ax.grid(True, axis="y", alpha=0.22)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.text(0.5, -0.03,
         f"Yahoo daily ^GSPC range=max, {dates[0]}–{dates[-1]}, {n_all} return days. "
         f"95% Wilson CIs; * = partial decade (ochre). One pre-committed conditioning "
         f"(calendar decade); up = close > previous close.",
         ha="center", fontsize=7.6, color="#666666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_baserate_drift.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span {dates[0]}..{dates[-1]}  n={n_all}  P(up)={p_all:.4f}")
print("decade  years        n     up    P(up)   95% Wilson CI")
for dec, n, k, p, lo, hi, partial, y0, y1 in rows:
    tag = "*" if partial else " "
    print(f"{dec}s{tag}  {y0}-{y1}  {n:5d}  {k:5d}  {p:.4f}  [{lo:.4f}, {hi:.4f}]")
