"""
Figure 2 - VIX vs. VIX3M and the term-structure slope: contango is the normal
state, backwardation is the stress state.

Free data: Cboe's public daily-history CSVs
(https://cdn.cboe.com/api/global/us_indices/daily_prices/<TICKER>_History.csv),
cached to data/ so the figure is reproducible offline and stable. FRED mirrors
the same two series as VIXCLS/VXVCLS but timed out at build time, so the Cboe
originals are used; Cboe's VIX3M history starts 2009-09-18, which fixes the
common sample.

ONE transparent, pre-committed rule (no threshold search): the slope is the
ratio VIX/VIX3M on closes; ratio < 1 = contango, ratio > 1 = backwardation.
Everything printed below is descriptive - shares of days, episode counts,
current values - not a fitted signal.

Also prints the front-end curve (VIX1D, VIX9D) on the latest common date and a
hand-checkable forward-vol computation between the 30-day and 93-day points,
both quoted in the paper.

Reproducible:
    python fig_term_structure.py     # numpy, matplotlib; stdlib urllib/csv
"""
import os, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
BASE = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{}_History.csv"


def load(ticker):
    path = os.path.join(DATA, f"{ticker}_History.csv")
    if not (os.path.exists(path) and os.path.getsize(path) > 0):
        try:
            socket.setdefaulttimeout(60)
            req = urllib.request.Request(BASE.format(ticker),
                                         headers={"User-Agent": "Mozilla/5.0"})
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
    out = {}
    with open(path) as f:
        rdr = csv.reader(f)
        head = next(rdr)
        col = len(head) - 1                      # CLOSE is last (or single value col)
        for row in rdr:
            d = dt.datetime.strptime(row[0], "%m/%d/%Y").date()
            try:
                out[d] = float(row[col])
            except ValueError:
                pass
    return out


vix, vix3m = load("VIX"), load("VIX3M")
vix9d, vix1d = load("VIX9D"), load("VIX1D")
days = sorted(set(vix) & set(vix3m))
v = np.array([vix[d] for d in days])
v3 = np.array([vix3m[d] for d in days])
ratio = v / v3
x = np.array([dt.datetime(d.year, d.month, d.day) for d in days])

pct_contango = 100.0 * np.mean(ratio < 1.0)
pct_backward = 100.0 * np.mean(ratio > 1.0)
# backwardation episodes: maximal runs of consecutive days with ratio > 1
bw = ratio > 1.0
starts = np.where(bw & ~np.roll(bw, 1))[0]
if bw[0]:
    starts = np.unique(np.concatenate([[0], starts]))
episodes = []
for s in starts:
    e = s
    while e + 1 < len(bw) and bw[e + 1]:
        e += 1
    episodes.append((days[s], days[e], e - s + 1, ratio[s:e + 1].max()))
long_eps = [ep for ep in episodes if ep[2] >= 5]

med_vix_ct = np.median(v[~bw])
med_vix_bw = np.median(v[bw])

# forward vol between the 30d and 93d points, latest close (variance is additive)
T1, T2 = 30.0, 93.0
fwd_var = (v3[-1] ** 2 * T2 - v[-1] ** 2 * T1) / (T2 - T1)
fwd_vol = np.sqrt(fwd_var)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.2, 5.4), sharex=True,
                               gridspec_kw={"height_ratios": [2.0, 1.15]})
ax1.plot(x, v, "-", color="#7c1c2c", lw=0.7, label="VIX (30-day)")
ax1.plot(x, v3, "-", color="#2f5d7c", lw=0.7, label="VIX3M (93-day)")
ax1.set_ylabel("index level (vol points)")
ax1.legend(frameon=False, fontsize=8.5, loc="upper right")
ax1.set_title("VIX vs. VIX3M and the slope VIX/VIX3M: contango rules, "
              "backwardation is the exception", fontsize=10.5)
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)
ax1.grid(True, axis="y", alpha=0.25)

ax2.plot(x, ratio, "-", color="#17120e", lw=0.6)
ax2.axhline(1.0, color="#7c1c2c", lw=1.0, ls="--")
ax2.fill_between(x, 1.0, ratio, where=ratio > 1.0, color="#7c1c2c", alpha=0.35,
                 lw=0)
ax2.set_ylabel("VIX / VIX3M")
ax2.set_ylim(0.55, max(1.75, ratio.max() + 0.05))
ax2.annotate(f"backwardation (ratio > 1): {pct_backward:.1f}% of days",
             xy=(x[len(x) // 3], 1.45), fontsize=8.2, color="#7c1c2c")
ax2.annotate(f"contango (ratio < 1): {pct_contango:.1f}% of days",
             xy=(x[len(x) // 3], 0.63), fontsize=8.2, color="#2f6d4f")
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
ax2.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.015,
         f"Cboe daily-history CSVs, closes {days[0]}..{days[-1]} "
         f"({len(days)} common sessions; VIX3M history starts 2009-09-18). "
         "Shaded: ratio > 1.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_term_structure.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={days[0]}..{days[-1]} n={len(days)}")
print(f"pct_contango={pct_contango:.1f} pct_backwardation={pct_backward:.1f} "
      f"pct_flat={100 - pct_contango - pct_backward:.1f}")
print(f"latest date={days[-1]} VIX={v[-1]:.2f} VIX3M={v3[-1]:.2f} "
      f"ratio={ratio[-1]:.3f}")
d9 = max(set(vix9d) & set(vix))
d1 = max(set(vix1d) & set(vix))
print(f"front_end VIX1D({d1})={vix1d[d1]:.2f} VIX9D({d9})={vix9d[d9]:.2f}")
print(f"median_VIX_contango={med_vix_ct:.2f} median_VIX_backwardation={med_vix_bw:.2f}")
print(f"n_backwardation_episodes={len(episodes)} (>=5d: {len(long_eps)})")
print(f"longest_episodes={sorted(episodes, key=lambda e: -e[2])[:5]}")
print(f"max_ratio={ratio.max():.3f} on {days[int(np.argmax(ratio))]}")
print(f"forward_vol_30_93: sqrt(({v3[-1]:.2f}^2*93 - {v[-1]:.2f}^2*30)/63) "
      f"= {fwd_vol:.2f}")
