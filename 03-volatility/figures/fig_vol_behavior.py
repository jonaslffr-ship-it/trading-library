"""
Figure (how volatility behaves) - three stylized facts on ~15 years of free
S&P 500 and VIX data: (a) volatility clustering (absolute daily returns),
(b) volatility regimes (rolling 21-day realized volatility, annualized),
(c) the leverage effect (scatter of the SPX daily return against the same-day
change in VIX, with the correlation printed).

Free data: daily S&P 500 (^GSPC) from Yahoo Finance's public chart API and
daily VIX closes from FRED (series VIXCLS), both cached to data/ so the figure
is reproducible offline and stable. No parameter search: the 21-day window is
the standard trading-month convention, fixed in advance.

Reproducible:
    python fig_vol_behavior.py     # numpy, matplotlib; stdlib urllib/csv
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
    if not (os.path.exists(SPX_CACHE) and os.path.getsize(SPX_CACHE) > 0):
        try:
            socket.setdefaulttimeout(30)
            url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=15y&interval=1d"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req).read()
        except Exception as e:
            print(f"SKIPPED (offline / no cache): {os.path.basename(SPX_CACHE)} - "
                  f"{type(e).__name__}: {e}")
            raise SystemExit(0)
        j = json.loads(raw)
        r = j["chart"]["result"][0]
        ts, cl = r["timestamp"], r["indicators"]["quote"][0]["close"]
        dates, close = [], []
        for t, c in zip(ts, cl):
            if c is None:
                continue
            dates.append(dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"))
            close.append(float(c))
        tmp = SPX_CACHE + ".part"
        with open(tmp, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["date", "close"])
            for d, c in zip(dates, close):
                w.writerow([d, f"{c:.4f}"])
        os.replace(tmp, SPX_CACHE)
        return dates, np.array(close)
    dates, close = [], []
    with open(SPX_CACHE) as f:
        for row in csv.DictReader(f):
            dates.append(row["date"]); close.append(float(row["close"]))
    return dates, np.array(close)


def load_vix():
    if not (os.path.exists(VIX_CACHE) and os.path.getsize(VIX_CACHE) > 0):
        try:
            socket.setdefaulttimeout(60)
            url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req).read()
            if not raw:
                raise ValueError("empty response")
            tmp = VIX_CACHE + ".part"
            with open(tmp, "wb") as f:
                f.write(raw)
            os.replace(tmp, VIX_CACHE)
        except Exception as e:
            print(f"SKIPPED (offline / no cache): {os.path.basename(VIX_CACHE)} - "
                  f"{type(e).__name__}: {e}")
            raise SystemExit(0)
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
ret = (close[1:] / close[:-1] - 1.0) * 100.0          # ret[i] belongs to sdates[i+1]
rdates = sdates[1:]
n = len(ret)

# (b) rolling 21-day realized volatility, annualized (%)
W = 21
ANN = np.sqrt(252.0)
rv_dates, rv = [], []
for i in range(W - 1, n):
    w = ret[i - W + 1:i + 1]
    rv.append(w.std() * ANN)             # population std of the window, annualized
    rv_dates.append(rdates[i])
rv = np.array(rv)

# (c) leverage effect: SPX daily return vs same-day VIX change
vmap = dict(zip(vdates, vix))
lx, ly = [], []
for i in range(1, n):                     # need VIX on day i and day i-1
    d0, d1 = rdates[i - 1], rdates[i]
    if d0 in vmap and d1 in vmap:
        lx.append(ret[i]); ly.append(vmap[d1] - vmap[d0])
lx, ly = np.array(lx), np.array(ly)
corr = np.corrcoef(lx, ly)[0, 1]

# clustering stats: size is sticky, sign is not
ac_abs = np.corrcoef(np.abs(ret[1:]), np.abs(ret[:-1]))[0, 1]
ac_ret = np.corrcoef(ret[1:], ret[:-1])[0, 1]

imax = int(rv.argmax()); imin = int(rv.argmin())
print(f"span={rdates[0]}..{rdates[-1]} n_returns={n} n_scatter={len(lx)}")
print(f"corr_ret_dVIX={corr:.3f}")
print(f"autocorr_absret_lag1={ac_abs:.3f}  autocorr_ret_lag1={ac_ret:.3f}")
print(f"rollingRV: median={np.median(rv):.2f}%  min={rv[imin]:.2f}% ({rv_dates[imin]})  "
      f"max={rv[imax]:.2f}% ({rv_dates[imax]})")
print(f"share_days_RV_below_10={np.mean(rv < 10) * 100:.1f}%  "
      f"share_days_RV_above_30={np.mean(rv > 30) * 100:.1f}%")
big = np.abs(ret) > 2.0
nb = int(big[:-1].sum())
follow = np.abs(ret[1:])[big[:-1]].mean() if nb else float("nan")
base = np.abs(ret[1:]).mean()
print(f"avg_absret_after_big_day={follow:.2f}%  unconditional_avg_absret={base:.2f}%  n_big_days={nb}")

# ---- figure: three stacked panels ----
xi = np.arange(n)
years = [i for i in range(n) if rdates[i][5:10] == "01-0" or (i > 0 and rdates[i][:4] != rdates[i - 1][:4])]
ylabels = [rdates[i][:4] for i in years]

fig, axes = plt.subplots(3, 1, figsize=(6.8, 8.6))

axA = axes[0]
axA.plot(xi, np.abs(ret), color="#17120e", lw=0.45)
axA.set_ylabel("|daily return| (%)")
axA.set_title("(a) Clustering — big moves bunch together in time", fontsize=10.0)
axA.set_xticks(years); axA.set_xticklabels(ylabels, fontsize=7.4, rotation=0)

axB = axes[1]
xb = np.arange(len(rv)) + (W - 1)
axB.plot(xb, rv, color="#17120e", lw=0.9)
axB.axhline(np.median(rv), color="#2f6d4f", lw=1.0, ls="--")
axB.annotate(f"median {np.median(rv):.1f}%", xy=(len(ret) * 0.012, np.median(rv) + 2),
             fontsize=8.4, color="#2f6d4f")
axB.annotate(f"{rv_dates[imax][:7]}: {rv[imax]:.0f}%", xy=(xb[imax], rv[imax]),
             xytext=(xb[imax] + n * 0.04, rv[imax] * 0.88), fontsize=8.4, color="#7c1c2c",
             arrowprops=dict(arrowstyle="->", color="#7c1c2c", lw=0.8))
axB.set_ylabel("21-day RV, annualized (%)")
axB.set_title("(b) Regimes — long calm stretches, short violent ones", fontsize=10.0)
axB.set_xticks(years); axB.set_xticklabels(ylabels, fontsize=7.4)

axC = axes[2]
axC.scatter(lx, ly, s=4, color="#17120e", alpha=0.28, linewidths=0)
b = np.polyfit(lx, ly, 1)
xg = np.linspace(lx.min(), lx.max(), 50)
axC.plot(xg, np.polyval(b, xg), color="#7c1c2c", lw=1.3)
axC.annotate(f"correlation = {corr:.2f}", xy=(0.03, 0.06), xycoords="axes fraction",
             fontsize=9.2, color="#7c1c2c")
axC.axhline(0, color="#999", lw=0.7); axC.axvline(0, color="#999", lw=0.7)
axC.set_xlabel("S&P 500 daily return (%)")
axC.set_ylabel("same-day change in VIX (pts)")
axC.set_title("(c) Leverage effect — the index falls, the VIX jumps", fontsize=10.0)

for ax in axes:
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", alpha=0.25)

fig.text(0.5, -0.012,
         f"Yahoo daily ^GSPC {rdates[0]}–{rdates[-1]} ({n} returns); VIX from FRED (VIXCLS), "
         f"{len(lx)} overlapping days in panel (c). 21-day window fixed in advance.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_vol_behavior.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
