"""
Figure 5 - The Cboe SKEW index, 1990-2026: tail-risk pricing has steepened
secularly, which is why SKEW must be read against its own recent range rather
than against its 1990s levels.

Free data: Cboe's public daily-history CSV
(https://cdn.cboe.com/api/global/us_indices/daily_prices/SKEW_History.csv),
cached to data/.

ONE transparent, pre-committed rule (no threshold search): descriptive
statistics only - full-sample mean and percentiles, decade means, and a
252-day moving average for the plot. All numbers quoted in the paper are
printed below.

Reproducible:
    python fig_skew_history.py     # numpy, matplotlib; stdlib urllib/csv
"""
import os, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/SKEW_History.csv"
path = os.path.join(DATA, "SKEW_History.csv")
if not (os.path.exists(path) and os.path.getsize(path) > 0):
    try:
        socket.setdefaulttimeout(60)
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        raw = urllib.request.urlopen(req).read()
        if not raw:
            raise ValueError("empty response")
        tmp = path + ".part"
        with open(tmp, "wb") as f:
            f.write(raw)
        os.replace(tmp, path)
    except Exception as e:
        print(f"SKIPPED (offline / no cache): {os.path.basename(path)} - "
              f"{type(e).__name__}: {e}")
        raise SystemExit(0)

dates, vals = [], []
with open(path) as f:
    rdr = csv.reader(f)
    next(rdr)
    for row in rdr:
        try:
            v = float(row[1])
        except ValueError:
            continue
        dates.append(dt.datetime.strptime(row[0], "%m/%d/%Y").date())
        vals.append(v)
v = np.array(vals)
x = np.array([dt.datetime(d.year, d.month, d.day) for d in dates])

W = 252
ma = np.convolve(v, np.ones(W) / W, mode="valid")

decades = {}
for d, val in zip(dates, vals):
    dec = f"{d.year // 10 * 10}s"
    decades.setdefault(dec, []).append(val)

p10, p50, p90 = np.percentile(v, [10, 50, 90])
mean_all = v.mean()

fig, ax = plt.subplots(figsize=(7.2, 4.2))
ax.plot(x, v, "-", color="#17120e", lw=0.35, alpha=0.35)
ax.plot(x[W - 1:], ma, "-", color="#7c1c2c", lw=1.6,
        label="252-day moving average")
ax.axhline(mean_all, color="#2f6d4f", lw=1.0, ls="--",
           label=f"full-sample mean {mean_all:.0f}")
ax.set_ylabel("Cboe SKEW index")
ax.set_title("The SKEW index, 1990-2026: tail-risk pricing has drifted "
             "structurally higher", fontsize=10.5)
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.02,
         f"Cboe daily-history CSV, {dates[0]}..{dates[-1]} "
         f"({len(v)} sessions). Thin line: daily closes.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_skew_history.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={dates[0]}..{dates[-1]} n={len(v)}")
print(f"latest={dates[-1]} SKEW={v[-1]:.2f}")
print(f"mean={mean_all:.1f} p10={p10:.1f} median={p50:.1f} p90={p90:.1f} "
      f"min={v.min():.1f} max={v.max():.1f}")
for dec in sorted(decades):
    arr = np.array(decades[dec])
    print(f"decade_mean {dec}: {arr.mean():.1f} (n={len(arr)})")
