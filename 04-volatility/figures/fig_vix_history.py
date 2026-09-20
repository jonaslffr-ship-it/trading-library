"""
Figure (VIX history) - the full daily VIX close history from FRED (series
VIXCLS, from 1990), with the practitioner reading bands 12 / 16 / 20 / 30 / 40
drawn in and the major volatility episodes labeled. The share of days spent in
each band is printed so the paper can quote the base rates.

Free data: FRED VIXCLS, cached to data/vixcls.csv so the figure is
reproducible offline and stable. The band edges (12, 16, 20, 30, 40) are the
conventional practitioner levels, fixed in advance - no threshold search.

Reproducible:
    python fig_vix_history.py     # numpy, matplotlib; stdlib urllib/csv
"""
import os, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
VIX_CACHE = os.path.join(DATA, "vixcls.csv")


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


dates, vix = load_vix()
n = len(vix)
num = np.array([dt.datetime.strptime(d, "%Y-%m-%d").toordinal() for d in dates])

# band shares (closed on the left)
edges = [0, 12, 16, 20, 30, 40, 1000]
names = ["<12", "12–16", "16–20", "20–30", "30–40", ">=40"]
shares = []
for lo, hi, nm in zip(edges[:-1], edges[1:], names):
    s = np.mean((vix >= lo) & (vix < hi)) * 100
    shares.append(s)
    print(f"band {nm:>6}: {s:5.1f}% of days")
print(f"span={dates[0]}..{dates[-1]} n={n} median={np.median(vix):.2f} mean={vix.mean():.2f} "
      f"min={vix.min():.2f} ({dates[int(vix.argmin())]}) max={vix.max():.2f} ({dates[int(vix.argmax())]})")

# major episodes: peak close inside a fixed window around each event
# (short label drawn in the plot, label_y = staggered text height to avoid overlap)
episodes = [
    ("1998-08-01", "1998-11-30", "LTCM / Russia 1998", "LTCM 1998", 60),
    ("2001-09-01", "2001-10-15", "9/11 2001", "9/11", 50),
    ("2002-07-01", "2002-08-15", "dot-com bottom 2002", "2002", 57),
    ("2008-09-01", "2008-12-31", "Lehman 2008", "Lehman 2008", 85),
    ("2011-08-01", "2011-10-15", "US downgrade 2011", "2011", 54),
    ("2015-08-15", "2015-09-15", "China deval 2015", "2015", 46),
    ("2018-02-01", "2018-02-15", "Volmageddon 2018", "2018", 42),
    ("2020-02-15", "2020-04-15", "COVID-19 2020", "COVID 2020", 87),
    ("2024-07-25", "2024-08-15", "yen carry 2024", "2024", 43),
    ("2025-04-01", "2025-04-30", "tariff shock 2025", "2025", 57),
]
marks = []
for lo, hi, label, short, label_y in episodes:
    idx = [i for i, d in enumerate(dates) if lo <= d <= hi]
    if not idx:
        continue
    j = idx[int(np.argmax(vix[idx]))]
    marks.append((j, short, label_y))
    print(f"episode {label}: peak close {vix[j]:.2f} on {dates[j]}")

fig, ax = plt.subplots(figsize=(6.9, 4.3))
band_cols = ["#e8efe9", "#f2f0e8", "#f5ece2", "#f3e4de", "#eed9d5", "#e7cdc8"]
for lo, hi, colr in zip(edges[:-1], edges[1:], band_cols):
    ax.axhspan(lo, min(hi, 90), color=colr, zorder=0)
for lv in [12, 16, 20, 30, 40]:
    ax.axhline(lv, color="#bbb", lw=0.6, zorder=1)
ax.plot(num, vix, color="#17120e", lw=0.5, zorder=2)

for j, short, label_y in marks:
    ax.annotate(short, xy=(num[j], vix[j]), xytext=(num[j], label_y),
                fontsize=7.4, color="#7c1c2c", ha="center", va="bottom",
                arrowprops=dict(arrowstyle="-", color="#7c1c2c", lw=0.6, alpha=0.7))

yticks = [dt.date(y, 1, 1).toordinal() for y in range(1990, 2027, 4)]
ax.set_xticks(yticks)
ax.set_xticklabels([str(y) for y in range(1990, 2027, 4)], fontsize=8)
ax.set_yticks([12, 16, 20, 30, 40, 60, 80])
ax.set_ylim(5, 92)
ax.set_ylabel("VIX close (band edges as ticks)")
ax.set_title("Three decades of the VIX: long stretches in the teens, rare spikes past 40",
             fontsize=10.2)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.text(0.5, -0.03,
         f"FRED series VIXCLS (daily close), {dates[0]}–{dates[-1]}, {n} observations. "
         f"Bands at 12/16/20/30/40 are conventional practitioner levels.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_vix_history.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
