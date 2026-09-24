"""
Figure 1 (E2) - The growth x inflation quadrant, computed from public data.

ONE pre-committed classification, stated in advance and never relabeled:
  growth signal    = INDPRO YoY minus its own value 3 months earlier  (>0 = accelerating)
  inflation signal = CPIAUCSL YoY minus its own value 3 months earlier (>0 = accelerating)
  Reflation    = growth accelerating, inflation accelerating
  Goldilocks   = growth accelerating, inflation decelerating
  Stagflation  = growth decelerating, inflation accelerating
  Deflation    = growth decelerating, inflation decelerating
Ties (exactly 0) fall into the "decelerating" branch; with float YoY values this
is essentially never binding.

Data: FRED CSV endpoint (INDPRO, CPIAUCSL), cached to data/ so the figure is
reproducible offline. The classification is also written to
data/quadrant_labels.csv so that fig_e2_quadrant_assets.py uses EXACTLY this
labeling (single source of truth, no relabeling).

Reproducible:
    python fig_e2_quadrant.py     # numpy, matplotlib; stdlib urllib/csv
"""
import os, csv, socket, urllib.request
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)


def fred(series):
    """Monthly FRED series -> (list of 'YYYY-MM', np.array values). Cached."""
    cache = os.path.join(DATA, f"fred_{series}.csv")
    if not (os.path.exists(cache) and os.path.getsize(cache) > 0):
        try:
            socket.setdefaulttimeout(60)
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req).read()
            if not raw:
                raise ValueError("empty response")
            tmp = cache + ".part"
            with open(tmp, "wb") as f:
                f.write(raw)
            os.replace(tmp, cache)
        except Exception as e:
            print(f"SKIPPED (offline / no cache): {os.path.basename(cache)} - "
                  f"{type(e).__name__}: {e}")
            raise SystemExit(0)
    ym, val = [], []
    with open(cache) as f:
        rdr = csv.reader(f)
        next(rdr)                                   # header (observation_date,SERIES)
        for row in rdr:
            if len(row) < 2 or row[1] in (".", ""):
                continue
            ym.append(row[0][:7]); val.append(float(row[1]))
    return ym, np.array(val)


ip_ym, ip = fred("INDPRO")
cpi_ym, cpi = fred("CPIAUCSL")


def yoy(ym, v):
    d = {m: x for m, x in zip(ym, v)}
    out = {}
    for m, x in zip(ym, v):
        y, mo = int(m[:4]), int(m[5:7])
        prev = f"{y-1:04d}-{mo:02d}"
        if prev in d:
            out[m] = x / d[prev] - 1.0
    return out


def mom3(yy):
    """YoY momentum: YoY minus YoY three months earlier."""
    keys = sorted(yy)
    out = {}
    for i, m in enumerate(keys):
        if i >= 3 and keys[i - 3] == shift(m, -3):
            out[m] = yy[m] - yy[keys[i - 3]]
    return out


def shift(m, k):
    y, mo = int(m[:4]), int(m[5:7])
    t = y * 12 + (mo - 1) + k
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


g_mom = mom3(yoy(ip_ym, ip))
i_mom = mom3(yoy(cpi_ym, cpi))
months = sorted(set(g_mom) & set(i_mom))

QUAD = ["Reflation", "Goldilocks", "Stagflation", "Deflation"]
COL = {"Reflation": "#b07d2b", "Goldilocks": "#2f6d4f",
       "Stagflation": "#7c1c2c", "Deflation": "#31607e"}


def label(g, i):
    if g > 0 and i > 0:
        return "Reflation"
    if g > 0:
        return "Goldilocks"
    if i > 0:
        return "Stagflation"
    return "Deflation"


labels = [label(g_mom[m], i_mom[m]) for m in months]

with open(os.path.join(DATA, "quadrant_labels.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["ym", "g_mom", "i_mom", "quadrant"])
    for m, l in zip(months, labels):
        w.writerow([m, f"{g_mom[m]:.6f}", f"{i_mom[m]:.6f}", l])

n = len(months)
share = {q: labels.count(q) / n for q in QUAD}
# persistence: P(same quadrant next month) and spell lengths
same = sum(1 for a, b in zip(labels[:-1], labels[1:]) if a == b)
runs, cur = [], 1
for a, b in zip(labels[:-1], labels[1:]):
    if a == b:
        cur += 1
    else:
        runs.append(cur); cur = 1
runs.append(cur)

# ---- plot: barcode strip on top, the two momentum series below -------------
x = np.array([int(m[:4]) + (int(m[5:7]) - 0.5) / 12 for m in months])
qidx = np.array([QUAD.index(l) for l in labels])

fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(9.2, 4.6), sharex=True,
                               gridspec_kw={"height_ratios": [1, 2.6]})
cmap = ListedColormap([COL[q] for q in QUAD])
ax0.imshow(qidx[None, :], aspect="auto", cmap=cmap, vmin=-0.5, vmax=3.5,
           extent=[x[0], x[-1], 0, 1], interpolation="nearest")
ax0.set_yticks([])
ax0.set_title("Growth x inflation quadrant, one month at a time (pre-committed rule, no relabeling)",
              fontsize=10.2)
for q in QUAD:
    ax0.plot([], [], "s", color=COL[q], label=f"{q} {share[q]*100:.0f}%")
ax0.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=4,
           frameon=False, fontsize=8)

ax1.plot(x, [g_mom[m] * 100 for m in months], color="#17120e", lw=0.7,
         label="INDPRO YoY momentum (3m change of YoY, pp)")
ax1.plot(x, [i_mom[m] * 100 for m in months], color="#7c1c2c", lw=0.7, alpha=0.85,
         label="CPI YoY momentum (3m change of YoY, pp)")
ax1.axhline(0, color="#999", lw=0.8)
ax1.set_ylabel("percentage points")
ax1.set_ylim(-8, 8)
ax1.legend(loc="lower left", frameon=False, fontsize=8)
for s in ("top", "right"):
    ax0.spines[s].set_visible(False); ax1.spines[s].set_visible(False)
ax1.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.02,
         f"FRED INDPRO & CPIAUCSL, monthly, {months[0]}..{months[-1]} ({n} months). "
         "Rule fixed in advance: sign of the 3-month change in the YoY rate; final-vintage data (see the vintage caveat in the text).",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_e2_quadrant.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={months[0]}..{months[-1]} n_months={n}")
for q in QUAD:
    print(f"share {q}: {share[q]*100:.1f}%  (n={labels.count(q)})")
print(f"persistence P(same next month)={same/(n-1)*100:.1f}%")
print(f"spell length: mean={np.mean(runs):.2f} months, median={np.median(runs):.0f}, max={max(runs)}")
print(f"current month {months[-1]}: {labels[-1]}  (g_mom={g_mom[months[-1]]*100:+.2f}pp, i_mom={i_mom[months[-1]]*100:+.2f}pp)")
