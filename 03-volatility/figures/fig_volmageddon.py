"""
Figure 4 - February 2018 ("Volmageddon"): the VIX spike of 5 February 2018 and
the overnight collapse of an inverse-volatility ETP (SVXY), the canonical case
of a structural flow feeding back into the index it tracks.

Free data: Yahoo Finance public chart API (^VIX and SVXY, daily, Oct 2017 -
Jun 2018), cached to data/yahoo_vix_2018.json and data/yahoo_svxy_2018.json;
plus Cboe's full VIX daily history (data/VIX_History.csv) used only to rank the
5 Feb 2018 one-day percentage change against all VIX history since 1990.

ONE transparent, pre-committed rule: no signal is computed at all - the figure
is a dated event study. SVXY is shown as total price indexed to 100 at
2018-01-02 (Yahoo split-adjusted closes), so the percentage collapse is
readable directly; all quoted numbers are printed below.

Reproducible:
    python fig_volmageddon.py     # numpy, matplotlib; stdlib urllib/json/csv
"""
import os, json, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
P1, P2 = 1506816000, 1530316800                  # 2017-10-01 .. 2018-06-30 UTC


def load_yahoo(symbol, fname):
    path = os.path.join(DATA, fname)
    if not (os.path.exists(path) and os.path.getsize(path) > 0):
        try:
            socket.setdefaulttimeout(60)
            url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                   f"?period1={P1}&period2={P2}&interval=1d")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req).read()
            json.loads(raw)                      # validate JSON before caching
            tmp = path + ".part"
            with open(tmp, "wb") as f:
                f.write(raw)
            os.replace(tmp, path)
        except Exception as e:
            print(f"SKIPPED (offline / no cache): {fname} - "
                  f"{type(e).__name__}: {e}")
            raise SystemExit(0)
    with open(path) as f:
        r = json.load(f)["chart"]["result"][0]
    ts = r["timestamp"]
    cl = r["indicators"]["quote"][0]["close"]
    dates, close = [], []
    for t, c in zip(ts, cl):
        if c is None:
            continue
        dates.append(dt.datetime.utcfromtimestamp(t).date())
        close.append(float(c))
    return dates, np.array(close)


vd, vc = load_yahoo("%5EVIX", "yahoo_vix_2018.json")
sd, sc = load_yahoo("SVXY", "yahoo_svxy_2018.json")

base = sd.index(dt.date(2018, 1, 2))
s_idx = sc / sc[base] * 100.0

feb2, feb5, feb6 = dt.date(2018, 2, 2), dt.date(2018, 2, 5), dt.date(2018, 2, 6)
v2, v5 = vc[vd.index(feb2)], vc[vd.index(feb5)]
s2, s5, s6 = (s_idx[sd.index(feb2)], s_idx[sd.index(feb5)], s_idx[sd.index(feb6)])
vix_jump = 100.0 * (v5 / v2 - 1.0)
svxy_dd = 100.0 * (s6 / s5 - 1.0)

# rank the 5 Feb 2018 one-day % change in all Cboe VIX history since 1990
hist = {}
with open(os.path.join(DATA, "VIX_History.csv")) as f:
    rdr = csv.reader(f)
    next(rdr)
    for row in rdr:
        hist[dt.datetime.strptime(row[0], "%m/%d/%Y").date()] = float(row[4])
hd = sorted(hist)
hv = np.array([hist[d] for d in hd])
pchg = 100.0 * (hv[1:] / hv[:-1] - 1.0)
rank = int(np.sum(pchg > pchg[hd.index(feb5) - 1])) + 1
print(f"vix_1d_pct_change_2018_02_05={pchg[hd.index(feb5) - 1]:+.1f}% "
      f"rank_in_history_since_1990={rank} of {len(pchg)} days")

x0, x1 = dt.date(2017, 11, 1), dt.date(2018, 4, 30)
mask_v = [(x0 <= d <= x1) for d in vd]
mask_s = [(x0 <= d <= x1) for d in sd]
xv = [d for d, m in zip(vd, mask_v) if m]
yv = vc[np.array(mask_v)]
xs = [d for d, m in zip(sd, mask_s) if m]
ys = s_idx[np.array(mask_s)]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.2, 5.6), sharex=True)
ax1.plot(xv, yv, "-", color="#7c1c2c", lw=1.3)
ax1.set_ylabel("VIX close")
ax1.axvline(feb5, color="#999", lw=0.8, ls=":")
ax1.annotate(f"5 Feb 2018: VIX {v2:.1f} → {v5:.1f}  ({vix_jump:+.0f}% in one day,\n"
             f"the largest one-day % rise since 1990)",
             xy=(feb5, v5), xytext=(dt.date(2018, 2, 20), v5 * 0.86),
             fontsize=8.2, color="#7c1c2c",
             arrowprops=dict(arrowstyle="->", color="#7c1c2c", lw=0.8))
ax1.set_title("Volmageddon, February 2018: a structural flow turns a sell-off "
              "into a vol event", fontsize=10.5)
ax2.plot(xs, ys, "-", color="#17120e", lw=1.3)
ax2.set_ylabel("SVXY (2018-01-02 = 100)")
ax2.axvline(feb5, color="#999", lw=0.8, ls=":")
ax2.annotate(f"6 Feb 2018: {svxy_dd:.0f}% vs. prior close -\n"
             f"the short-vol ETP is destroyed overnight",
             xy=(feb6, s6), xytext=(dt.date(2018, 2, 24), 55),
             fontsize=8.2, color="#17120e",
             arrowprops=dict(arrowstyle="->", color="#17120e", lw=0.8))
ax2.text(dt.date(2017, 11, 6), 26,
         "the loop: VIX futures rise → inverse ETPs must BUY futures to "
         "rebalance\n→ buying pushes futures further up → more "
         "rebalancing demand → spiral",
         fontsize=7.8, color="#666",
         bbox=dict(boxstyle="round,pad=0.4", fc="#f5f2ee", ec="#ccc", lw=0.6))
for ax in (ax1, ax2):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.015,
         "Yahoo Finance daily closes, ^VIX and SVXY (split-adjusted), "
         "Nov 2017 - Apr 2018; rank vs. Cboe VIX history 1990-2026.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_volmageddon.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"VIX close 2018-02-02={v2:.2f} 2018-02-05={v5:.2f} jump={vix_jump:+.1f}%")
print(f"SVXY indexed (2018-01-02=100): 02-02={s2:.1f} 02-05={s5:.1f} "
      f"02-06={s6:.1f} overnight={svxy_dd:.1f}%")
print(f"SVXY peak-to-06Feb drawdown="
      f"{100.0 * (s6 / s_idx[:sd.index(feb6)].max() - 1.0):.1f}%")
