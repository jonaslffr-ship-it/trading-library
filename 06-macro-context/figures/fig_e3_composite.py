"""
Figure 3 (E3) - A reproducible composite sentiment indicator from free data,
and the multicollinearity it hides.

Three ingredients, one per family of Section 2, weekly on CFTC report dates
(as-of Tuesday; sampled at the Friday release so everything is knowable):

  S_vix = -z(VIX close)                     market-based (fear gauge, inverted)
  S_pc  = -z(equity put/call, 21d MA)       market-based / options demand (inverted)
  S_cot = +z(net non-commercial E-mini S&P 500 position, % of OI)   positioning

Signs are set so that HIGH composite = optimism/bullish positioning. This
figure is DESCRIPTIVE: z-scores use the full 2006-2019 overlap window (the
only window where all three series exist), which is a look-ahead by
construction - the point here is anatomy and the correlation matrix, not a
tradable signal. The honest real-time version (expanding statistics only) is
what Figure 4 tests. Parsed with stdlib csv/zipfile; no pandas.

Reproducible:
    python fig_e3_composite.py     # numpy, matplotlib; stdlib urllib/zipfile/csv
"""
import os, io, csv, socket, sys, zipfile, urllib.request, datetime as dt
try:  # keep stdout stable on legacy (cp1252) Windows consoles
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
COTDIR = os.path.join(DATA, "cot")
os.makedirs(COTDIR, exist_ok=True)


def fetch(url, path):
    if os.path.exists(path):
        return
    socket.setdefaulttimeout(60)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with open(path, "wb") as f:
        f.write(urllib.request.urlopen(req).read())


def load_cot(code="13874A"):
    rows = {}
    for y in range(1998, 2027):
        zp = os.path.join(COTDIR, f"deacot{y}.zip")
        try:
            fetch(f"https://www.cftc.gov/files/dea/history/deacot{y}.zip", zp)
        except Exception:
            continue
        z = zipfile.ZipFile(zp)
        raw = z.read(z.namelist()[0]).decode("latin-1")
        rdr = csv.reader(io.StringIO(raw)); next(rdr)
        for r in rdr:
            if r[3].strip() == code:
                rows[r[2].strip()] = 100.0 * (float(r[8]) - float(r[9])) / float(r[7])
    dates = sorted(rows)
    return dates, np.array([rows[d] for d in dates])


def load_daily_map(path, url, datefmt, datecol, valcol, skip_headerish=True):
    fetch(url, path)
    out = {}
    with open(path) as f:
        for row in csv.reader(f):
            if len(row) <= max(datecol, valcol):
                continue
            try:
                d = dt.datetime.strptime(row[datecol].strip(), datefmt)
                v = float(row[valcol])
            except ValueError:
                continue
            out[d.strftime("%Y-%m-%d")] = v
    return out


vix = load_daily_map(os.path.join(DATA, "vix_history.csv"),
                     "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv",
                     "%m/%d/%Y", 0, 4)
pc_raw = load_daily_map(os.path.join(DATA, "equitypc.csv"),
                        "https://cdn.cboe.com/resources/options/volume_and_call_put_ratios/equitypc.csv",
                        "%m/%d/%Y", 0, 4)

# 21d MA of the P/C ratio, keyed by date
pc_dates = sorted(pc_raw)
pc_vals = np.array([pc_raw[d] for d in pc_dates])
W = 21
pc_ma = {pc_dates[i + W - 1]: float(np.mean(pc_vals[i:i + W])) for i in range(len(pc_vals) - W + 1)}

cot_dates, cot = load_cot()


def last_on_or_before(m, day, maxback=7):
    d = dt.datetime.strptime(day, "%Y-%m-%d")
    for k in range(maxback):
        key = (d - dt.timedelta(days=k)).strftime("%Y-%m-%d")
        if key in m:
            return m[key]
    return None


# assemble weekly rows on the Friday after the as-of Tuesday
rows = []
for d, c in zip(cot_dates, cot):
    friday = (dt.datetime.strptime(d, "%Y-%m-%d") + dt.timedelta(days=3)).strftime("%Y-%m-%d")
    v = last_on_or_before(vix, friday)
    p = last_on_or_before(pc_ma, friday)
    if v is not None and p is not None:
        rows.append((friday, v, p, c))

dates = [r[0] for r in rows]
V = np.array([r[1] for r in rows]); P = np.array([r[2] for r in rows]); C = np.array([r[3] for r in rows])


def z(x):
    return (x - x.mean()) / x.std()


S_vix, S_pc, S_cot = -z(V), -z(P), z(C)
comp = (S_vix + S_pc + S_cot) / 3.0
M = np.vstack([S_vix, S_pc, S_cot, comp])
corr = np.corrcoef(M)
labels = ["−z(VIX)", "−z(P/C)", "+z(COT)", "composite"]

x = [dt.datetime.strptime(d, "%Y-%m-%d") for d in dates]
fig = plt.figure(figsize=(6.6, 5.6))
gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1.0], width_ratios=[1.35, 1.0],
                      hspace=0.34, wspace=0.30)
ax = fig.add_subplot(gs[0, :])
ax.plot(x, S_vix, "-", color="#7c1c2c", lw=0.7, alpha=0.75, label="−z(VIX)")
ax.plot(x, S_pc, "-", color="#2f6d4f", lw=0.7, alpha=0.75, label="−z(P/C 21d)")
ax.plot(x, S_cot, "-", color="#b08a3e", lw=0.7, alpha=0.85, label="+z(COT net specs)")
ax.plot(x, comp, "-", color="#17120e", lw=1.6, label="composite (mean)")
ax.axhline(0, color="#999", lw=0.8)
ax.legend(loc="lower right", fontsize=7.2, frameon=False, ncol=2)
ax.set_ylabel("z-score (optimism →)")
ax.set_title("A three-family sentiment composite on free data, 2006–2019",
             fontsize=10.2)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)

axm = fig.add_subplot(gs[1, 0])
im = axm.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r", alpha=0.85)
axm.set_xticks(range(4)); axm.set_yticks(range(4))
axm.set_xticklabels(labels, fontsize=7.2, rotation=20)
axm.set_yticklabels(labels, fontsize=7.2)
for i in range(4):
    for j in range(4):
        axm.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center", fontsize=7.8,
                 color="#17120e")
axm.set_title("correlation matrix (weekly)", fontsize=8.8)

axh = fig.add_subplot(gs[1, 1])
axh.hist(comp, bins=40, color="#17120e", alpha=0.75)
axh.axvline(np.percentile(comp, 10), color="#7c1c2c", lw=1.0, ls="--")
axh.axvline(np.percentile(comp, 90), color="#2f6d4f", lw=1.0, ls="--")
axh.set_title("composite distribution,\ndecile cutoffs dashed", fontsize=8.8)
axh.set_xlabel("composite z", fontsize=8)
for s in ("top", "right"):
    axh.spines[s].set_visible(False)

fig.text(0.5, -0.015,
         f"Weekly on CFTC report dates sampled at the Friday release, {dates[0]}–{dates[-1]}, "
         f"n={len(dates)}. VIX & equity P/C: CBOE; COT: CFTC legacy (13874A). "
         f"Full-window z-scores: descriptive only (look-ahead); the tested version is Figure 4.",
         ha="center", fontsize=7.4, color="#666")

OUT = os.path.join(HERE, "fig_e3_composite.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={dates[0]}..{dates[-1]} n_weeks={len(dates)}")
print("corr matrix rows (" + " | ".join(labels) + "):")
for lab, row in zip(labels, corr):
    print("  " + lab.ljust(10) + "  " + "  ".join(f"{v:+.3f}" for v in row))
print(f"decile cutoffs: p10={np.percentile(comp, 10):+.3f} p90={np.percentile(comp, 90):+.3f}")
print(f"corr(VIXcomp, PCcomp)={corr[0,1]:+.3f}  corr(VIXcomp, COTcomp)={corr[0,2]:+.3f}  "
      f"corr(PCcomp, COTcomp)={corr[1,2]:+.3f}")
