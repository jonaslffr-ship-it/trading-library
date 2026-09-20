"""
Figure (expected move scored) - ONE pre-committed rule, no tuning:

    daily expected move EM(t) = close(t) x (VIX(t)/100) / sqrt(252)

For every day t in ~15 years of overlapping free SPX and VIX data, the next
session's absolute move |close(t+1) - close(t)| is compared against EM(t). If
the VIX were an unbiased, normally-distributed forecast of the next day, about
68.3% of days would land inside +-1 EM. The script prints the actual overall
hit share (and the +-2 EM share against the naive 95.4%), plus a fully worked
example on the most recent overlapping session, and plots the rolling 1-year
hit share. Whatever the numbers show is reported as-is.

Free data: daily S&P 500 (^GSPC) from Yahoo Finance's public chart API and
daily VIX closes from FRED (VIXCLS), cached to data/.

Reproducible:
    python fig_expected_move.py     # numpy, matplotlib; stdlib urllib/csv
"""
import os, json, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
SPX_CACHE = os.path.join(DATA, "spx_daily.csv")
VIX_CACHE = os.path.join(DATA, "vixcls.csv")


def load_spx():
    if os.path.exists(SPX_CACHE):
        dates, close = [], []
        with open(SPX_CACHE) as f:
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
    with open(SPX_CACHE, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "close"])
        for d, c in zip(dates, close):
            w.writerow([d, f"{c:.4f}"])
    return dates, np.array(close)


def load_vix():
    if not os.path.exists(VIX_CACHE):
        socket.setdefaulttimeout(60)
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with open(VIX_CACHE, "wb") as f:
            f.write(urllib.request.urlopen(req).read())
    vd, vv = [], []
    with open(VIX_CACHE) as f:
        for row in csv.DictReader(f):
            val = row.get("VIXCLS", "").strip()
            if val in ("", "."):
                continue
            vd.append(row["observation_date"]); vv.append(float(val))
    return vd, np.array(vv)


sdates, close = load_spx()
vdates, vix = load_vix()
vmap = dict(zip(vdates, vix))
ANN = np.sqrt(252.0)

# build (t, t+1) pairs over consecutive SPX sessions with a VIX close on day t
ex_dates, em_pct, mv_pct = [], [], []
for i in range(len(sdates) - 1):
    d = sdates[i]
    if d not in vmap:
        continue
    em = vmap[d] / ANN                                  # EM as % of close(t)
    mv = abs(close[i + 1] / close[i] - 1.0) * 100.0     # realized |move| in %
    ex_dates.append(sdates[i + 1]); em_pct.append(em); mv_pct.append(mv)
em_pct, mv_pct = np.array(em_pct), np.array(mv_pct)
hit1 = mv_pct <= em_pct
hit2 = mv_pct <= 2 * em_pct
n = len(hit1)
print(f"span={ex_dates[0]}..{ex_dates[-1]} n_days={n}")
print(f"inside_1EM={hit1.mean() * 100:.1f}%  (naive normal expectation 68.3%)")
print(f"inside_2EM={hit2.mean() * 100:.1f}%  (naive normal expectation 95.4%)")

# rolling 1-year (252-day) hit share
W = 252
roll_x, roll_y = [], []
csum = np.cumsum(np.concatenate([[0], hit1.astype(float)]))
for i in range(W - 1, n):
    roll_y.append((csum[i + 1] - csum[i + 1 - W]) / W * 100)
    roll_x.append(i)
roll_y = np.array(roll_y)
jmin, jmax = int(roll_y.argmin()), int(roll_y.argmax())
print(f"rolling_1y_share: min={roll_y[jmin]:.1f}% ({ex_dates[roll_x[jmin]]})  "
      f"max={roll_y[jmax]:.1f}% ({ex_dates[roll_x[jmax]]})")

# worked example: most recent overlapping session
i_last = max(i for i in range(len(sdates) - 1) if sdates[i] in vmap)
d0, d1 = sdates[i_last], sdates[i_last + 1]
c0, c1, v0 = close[i_last], close[i_last + 1], vmap[sdates[i_last]]
em_l = v0 / ANN
em_pts = c0 * em_l / 100
mv_l = (c1 / c0 - 1.0) * 100.0
print(f"worked_example: t={d0} close={c0:.2f} VIX={v0:.2f} -> daily_sigma={em_l:.3f}% "
      f"= {em_pts:.1f} pts")
print(f"  ladder_pts: 0.25sig={0.25 * em_pts:.1f}  0.5sig={0.5 * em_pts:.1f}  1sig={em_pts:.1f}  "
      f"band=({c0 - em_pts:.0f}, {c0 + em_pts:.0f})")
print(f"  next_session {d1}: close={c1:.2f} move={mv_l:+.3f}% "
      f"({c1 - c0:+.1f} pts) = {abs(mv_l) / em_l:.2f} sigma -> "
      f"{'INSIDE' if abs(mv_l) <= em_l else 'OUTSIDE'} the 1-sigma band")

# ---- figure ----
fig, ax = plt.subplots(figsize=(6.8, 3.9))
ax.plot(roll_x, roll_y, color="#17120e", lw=1.1)
ax.axhline(68.3, color="#7c1c2c", lw=1.1, ls="--")
ax.annotate("68.3% — naive normal expectation", xy=(roll_x[0], 68.3),
            xytext=(roll_x[0] + n * 0.01, 66.6), fontsize=8.6, color="#7c1c2c")
ax.axhline(hit1.mean() * 100, color="#2f6d4f", lw=1.1, ls=":")
ax.annotate(f"actual average {hit1.mean() * 100:.1f}%", xy=(roll_x[-1], hit1.mean() * 100),
            xytext=(n * 0.62, hit1.mean() * 100 + 1.6), fontsize=8.6, color="#2f6d4f")
years = [i for i in range(1, n) if ex_dates[i][:4] != ex_dates[i - 1][:4]]
ax.set_xticks(years[::2])
ax.set_xticklabels([ex_dates[i][:4] for i in years][::2], fontsize=8)
ax.set_ylim(65, 94)
ax.set_ylabel("share of days inside ±1 EM (%)\nrolling 1-year window")
ax.set_title("The index stays inside the VIX-implied ±1σ band far more often than 68%",
             fontsize=10.0)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.03,
         f"EM(t) = close·(VIX/100)/√252, scored on the next session. Yahoo ^GSPC + FRED VIXCLS, "
         f"{ex_dates[0]}–{ex_dates[-1]}, {n} days. Rule fixed in advance, reported as-is.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_expected_move.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
