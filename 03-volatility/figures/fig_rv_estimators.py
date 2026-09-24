"""
Figure 1 - The realized-volatility estimator zoo on real S&P 500 OHLC data.

Free data: daily S&P 500 (^GSPC) OHLC from Yahoo Finance's public chart API,
cached to data/spx_ohlc.csv so the figure is reproducible offline. Five
estimators of daily variance are computed on a rolling 21-day window:
close-to-close, Parkinson (1980), Garman-Klass (1980), Rogers-Satchell (1994),
and Yang-Zhang (2000). Panel (a) shows the rolling annualized estimates over
the last three years; panel (b) shows the full-sample mean level of each
estimator, which exposes the overnight-gap bias of the pure range estimators.

Printed diagnostics: full-sample mean annualized vol per estimator (and the
ratio to close-to-close), and the lag-1 autocorrelation of the single-day
estimates - a model-free efficiency proxy: true variance is persistent, so a
less noisy estimator shows higher autocorrelation.

Reproducible:
    python fig_rv_estimators.py     # numpy, matplotlib; stdlib urllib/json
"""
import os, json, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
CACHE = os.path.join(DATA, "spx_ohlc.csv")


def load_ohlc():
    if os.path.exists(CACHE):
        dates, o, h, l, c = [], [], [], [], []
        with open(CACHE) as f:
            for row in csv.DictReader(f):
                dates.append(row["date"])
                o.append(float(row["open"])); h.append(float(row["high"]))
                l.append(float(row["low"])); c.append(float(row["close"]))
        return dates, np.array(o), np.array(h), np.array(l), np.array(c)
    socket.setdefaulttimeout(30)
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
           "?range=15y&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    j = json.loads(urllib.request.urlopen(req).read())
    r = j["chart"]["result"][0]
    ts = r["timestamp"]; q = r["indicators"]["quote"][0]
    dates, o, h, l, c = [], [], [], [], []
    for t, oo, hh, ll, cc in zip(ts, q["open"], q["high"], q["low"], q["close"]):
        if None in (oo, hh, ll, cc):
            continue
        dates.append(dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"))
        o.append(float(oo)); h.append(float(hh)); l.append(float(ll)); c.append(float(cc))
    with open(CACHE, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "open", "high", "low", "close"])
        for row in zip(dates, o, h, l, c):
            w.writerow([row[0]] + [f"{x:.4f}" for x in row[1:]])
    return dates, np.array(o), np.array(h), np.array(l), np.array(c)


dates, O, H, L, C = load_ohlc()
n = len(C)

# --- per-day quantities (log), aligned so index t uses day t and close t-1 ---
u = np.log(H[1:] / O[1:])            # high  vs open
d = np.log(L[1:] / O[1:])            # low   vs open
cc = np.log(C[1:] / O[1:])           # close vs open  (intraday return)
o = np.log(O[1:] / C[:-1])           # overnight gap
r = np.log(C[1:] / C[:-1])           # close-to-close return
ddates = dates[1:]
N = len(r)

# --- single-day variance estimates (whole-day scale where defined) ---
est_cc = r ** 2                                          # noisy benchmark
est_p = (u - d) ** 2 / (4.0 * np.log(2.0))               # Parkinson (open-to-close range)
est_gk = 0.5 * (u - d) ** 2 - (2.0 * np.log(2.0) - 1.0) * cc ** 2   # Garman-Klass
est_rs = u * (u - cc) + d * (d - cc)                     # Rogers-Satchell

W = 21
K_YZ = 0.34 / (1.34 + (W + 1) / (W - 1))                 # Yang-Zhang weight for n=21


def roll_mean(x, w):
    out = np.full(len(x), np.nan)
    cs = np.cumsum(np.concatenate([[0.0], x]))
    out[w - 1:] = (cs[w:] - cs[:-w]) / w
    return out


def roll_var(x, w):
    """Rolling unbiased variance (demeaned)."""
    m1 = roll_mean(x, w)
    m2 = roll_mean(x ** 2, w)
    return (m2 - m1 ** 2) * w / (w - 1)


ANN = 252.0
v_cc = roll_var(r, W) * ANN
v_p = roll_mean(est_p, W) * ANN
v_gk = roll_mean(est_gk, W) * ANN
v_rs = roll_mean(est_rs, W) * ANN
v_yz = (roll_var(o, W) + K_YZ * roll_var(cc, W) + (1 - K_YZ) * roll_mean(est_rs, W)) * ANN

series = {
    "close-to-close": v_cc, "Parkinson": v_p, "Garman-Klass": v_gk,
    "Rogers-Satchell": v_rs, "Yang-Zhang": v_yz,
}
daily = {
    "close-to-close": est_cc, "Parkinson": est_p,
    "Garman-Klass": est_gk, "Rogers-Satchell": est_rs,
}

# --- diagnostics ---
valid = ~np.isnan(v_cc)
print("span", ddates[0], "..", ddates[-1], " sessions:", N)
mean_cc = np.nanmean(np.sqrt(v_cc))
for k, v in series.items():
    mv = np.nanmean(np.sqrt(v))
    print(f"mean 21d ann. vol  {k:16s} {mv*100:6.2f}%   ratio vs CC {mv/mean_cc:5.3f}")


def ac1(x):
    x = x - x.mean()
    return float(np.sum(x[1:] * x[:-1]) / np.sum(x * x))


for k, v in daily.items():
    print(f"lag-1 autocorr of single-day estimate  {k:16s} {ac1(v):5.3f}")

# --- figure ---
COL = {"close-to-close": "#8a8a8a", "Parkinson": "#a8763e",
       "Garman-Klass": "#31536e", "Rogers-Satchell": "#6d8a5b",
       "Yang-Zhang": "#7c1c2c"}
x = np.arange(N)
zoom = ddates.index([d0 for d0 in ddates if d0 >= "2023-09-01"][0])

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(6.9, 5.6), gridspec_kw={"height_ratios": [2.4, 1.0]})

for k in ["close-to-close", "Parkinson", "Garman-Klass", "Rogers-Satchell"]:
    ax1.plot(x[zoom:], 100 * np.sqrt(series[k][zoom:]), lw=0.9, color=COL[k],
             alpha=0.75, label=k)
ax1.plot(x[zoom:], 100 * np.sqrt(v_yz[zoom:]), lw=1.5, color=COL["Yang-Zhang"],
         label="Yang-Zhang")
ticks = [i for i in range(zoom, N) if ddates[i][5:7] in ("01", "07") and ddates[i - 1][5:7] not in ("01", "07")]
ax1.set_xticks(ticks); ax1.set_xticklabels([ddates[i][:7] for i in ticks], fontsize=8)
ax1.set_ylabel("annualized volatility (%), 21-day window")
ax1.legend(fontsize=7.5, ncol=2, frameon=False)
ax1.set_title("(a)  Five estimators of the same object, rolling 21-day window", fontsize=9.5, loc="left")
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)
ax1.grid(True, axis="y", alpha=0.25)

names = list(series.keys())
means = [np.nanmean(np.sqrt(series[k])) * 100 for k in names]
bars = ax2.barh(np.arange(len(names)), means,
                color=[COL[k] for k in names], alpha=0.85, height=0.62)
ax2.set_yticks(np.arange(len(names))); ax2.set_yticklabels(names, fontsize=8)
ax2.invert_yaxis()
for i, m in enumerate(means):
    ax2.text(m + 0.12, i, f"{m:.1f}%", va="center", fontsize=8)
ax2.set_xlim(0, max(means) * 1.18)
ax2.set_xlabel("full-sample mean of rolling 21-day annualized vol (%)", fontsize=8.5)
ax2.set_title("(b)  Mean level - pure range estimators miss the overnight gap", fontsize=9.5, loc="left")
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)

fig.text(0.5, -0.015,
         f"Yahoo daily ^GSPC OHLC, {ddates[0]}-{ddates[-1]}, {N} sessions. "
         "Panel (a) shows 2023-09 onward for readability; statistics use the full sample.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_rv_estimators.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
