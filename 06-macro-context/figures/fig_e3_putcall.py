"""
Figure 2 (E3) - Market-based sentiment: the CBOE equity put/call ratio
(2006-2019, discontinued) and the VIX as the long-history gauge (1990-2026).

Free data, with an honest limitation stated up front: CBOE's daily equity
put/call ratio file (equitypc.csv, from the legacy market-statistics
"datahouse") covers 2006-11-01 to 2019-10-04 and was then discontinued as a
free download; the file is still served from the CBOE CDN. For a market-based
sentiment series with real history into the present, the VIX (CBOE, free,
1990-) stands in - the paper states this substitution explicitly.

Top panel: 21-day moving average of the equity P/C ratio with its top/bottom
5% marked (fear / complacency extremes). Bottom panel: VIX (log scale) with
closes above 40 marked. Parsed with stdlib csv; no pandas.

Reproducible:
    python fig_e3_putcall.py     # numpy, matplotlib; stdlib urllib/csv
"""
import os, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)

PC_URL = "https://cdn.cboe.com/resources/options/volume_and_call_put_ratios/equitypc.csv"
VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"


def fetch(url, path):
    """Cache url -> path. Read into memory first, validate non-empty, then
    write atomically via a .part temp, so a failed/offline fetch never leaves
    a 0-byte or partial cache behind (ERRATA cache-poison). Raises on failure."""
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return
    socket.setdefaulttimeout(60)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req).read()
    if not raw:
        raise ValueError("empty response")
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(raw)
    os.replace(tmp, path)


def ensure(url, path):
    """fetch(); on offline failure with no usable cache, SKIP cleanly instead
    of crashing or trusting a poisoned cache."""
    try:
        fetch(url, path)
    except Exception as e:
        if not (os.path.exists(path) and os.path.getsize(path) > 0):
            print(f"SKIPPED (offline / no cache): {os.path.basename(path)} - "
                  f"{type(e).__name__}: {e}")
            raise SystemExit(0)


def load_pc():
    path = os.path.join(DATA, "equitypc.csv")
    ensure(PC_URL, path)
    dates, ratio = [], []
    with open(path) as f:
        for row in csv.reader(f):
            if len(row) < 5 or row[0].strip() == "DATE" or "/" not in row[0]:
                continue
            try:
                d = dt.datetime.strptime(row[0].strip(), "%m/%d/%Y")
                r = float(row[4])
            except ValueError:
                continue
            dates.append(d); ratio.append(r)
    return dates, np.array(ratio)


def load_vix():
    path = os.path.join(DATA, "vix_history.csv")
    ensure(VIX_URL, path)
    dates, close = [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            dates.append(dt.datetime.strptime(row["DATE"], "%m/%d/%Y"))
            close.append(float(row["CLOSE"]))
    return dates, np.array(close)


pc_dates, pc = load_pc()
vix_dates, vix = load_vix()

W = 21
pc_ma = np.convolve(pc, np.ones(W) / W, mode="valid")
pc_ma_dates = pc_dates[W - 1:]
hi_thr, lo_thr = np.percentile(pc_ma, 95), np.percentile(pc_ma, 5)
hi = pc_ma >= hi_thr
lo = pc_ma <= lo_thr

vix_pctile_now = 100.0 * (vix < vix[-1]).mean()
spike = vix >= 40

# correlation between the two gauges on the overlap (monthly-ish preview of §4)
pc_map = {d.strftime("%Y-%m-%d"): v for d, v in zip(pc_ma_dates, pc_ma)}
both = [(v, pc_map[d.strftime("%Y-%m-%d")]) for d, v in zip(vix_dates, vix)
        if d.strftime("%Y-%m-%d") in pc_map]
vv, pp = np.array([b[0] for b in both]), np.array([b[1] for b in both])
corr = np.corrcoef(vv, pp)[0, 1]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.6, 5.6),
                               gridspec_kw={"height_ratios": [1.0, 1.0]})

ax1.plot(pc_ma_dates, pc_ma, "-", color="#17120e", lw=1.1)
ax1.axhline(hi_thr, color="#7c1c2c", lw=0.8, ls="--")
ax1.axhline(lo_thr, color="#2f6d4f", lw=0.8, ls="--")
ax1.plot(np.array(pc_ma_dates)[hi], pc_ma[hi], ".", color="#7c1c2c", ms=3.5)
ax1.plot(np.array(pc_ma_dates)[lo], pc_ma[lo], ".", color="#2f6d4f", ms=3.5)
ax1.annotate(f"fear: top 5% ≥ {hi_thr:.2f}", xy=(pc_ma_dates[-1], hi_thr),
             xytext=(-2, 5), textcoords="offset points", fontsize=8, color="#7c1c2c",
             ha="right")
ax1.annotate(f"complacency: bottom 5% ≤ {lo_thr:.2f}", xy=(pc_ma_dates[-1], lo_thr),
             xytext=(-2, -12), textcoords="offset points", fontsize=8, color="#2f6d4f",
             ha="right")
ax1.set_ylabel("equity P/C, 21d MA")
ax1.set_title("Two market-based sentiment gauges - one dies in 2019, one lives on",
              fontsize=10.2)

ax2.plot(vix_dates, vix, "-", color="#17120e", lw=0.7)
ax2.set_yscale("log")
ax2.set_yticks([10, 20, 40, 80])
ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
ax2.yaxis.set_minor_formatter(mticker.NullFormatter())
ax2.plot(np.array(vix_dates)[spike], vix[spike], ".", color="#7c1c2c", ms=3)
ax2.axhline(40, color="#7c1c2c", lw=0.8, ls="--")
ax2.set_ylabel("VIX (log)")
ax2.plot(vix_dates[-1], vix[-1], "o", color="#17120e", ms=4)
ax2.annotate(f"latest {vix[-1]:.1f} ({vix_pctile_now:.0f}th pctile since 1990)",
             xy=(vix_dates[-1], vix[-1]), xytext=(dt.datetime(1990, 6, 1), 62),
             textcoords="data", fontsize=8.5, color="#17120e",
             arrowprops=dict(arrowstyle="->", color="#666", lw=0.8,
                             connectionstyle="arc3,rad=-0.15"))

for ax in (ax1, ax2):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", alpha=0.25)

fig.text(0.5, -0.015,
         f"CBOE equity put/call ratio {pc_dates[0]:%Y-%m-%d}–{pc_dates[-1]:%Y-%m-%d} "
         f"({len(pc)} sessions, free file discontinued 2019). "
         f"VIX daily closes {vix_dates[0]:%Y-%m-%d}–{vix_dates[-1]:%Y-%m-%d} (CBOE).",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_e3_putcall.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"pc_span={pc_dates[0]:%Y-%m-%d}..{pc_dates[-1]:%Y-%m-%d} n={len(pc)} "
      f"ma_window={W} hi_thr={hi_thr:.3f} lo_thr={lo_thr:.3f}")
print(f"pc_ma_mean={pc_ma.mean():.3f} pc_ma_min={pc_ma.min():.3f} pc_ma_max={pc_ma.max():.3f}")
print(f"vix_span={vix_dates[0]:%Y-%m-%d}..{vix_dates[-1]:%Y-%m-%d} n={len(vix)} "
      f"latest={vix[-1]:.2f} pctile={vix_pctile_now:.1f} n_days_ge40={int(spike.sum())}")
print(f"corr_vix_pcma_overlap={corr:.3f} n_overlap={len(vv)}")
