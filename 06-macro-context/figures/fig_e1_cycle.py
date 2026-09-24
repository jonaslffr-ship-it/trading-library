"""
Figure 2 - The business cycle as data: a coincident gauge and a leading gauge.

Free data (FRED public CSV, cached to data/):
  INDPRO  - industrial production index, monthly -> plotted as YoY % change
            (a classic *coincident* indicator: it turns with the cycle)
  T10Y3M  - 10-year minus 3-month Treasury spread, daily (a classic *leading*
            indicator: it has tended to turn negative before recessions)
  USREC   - NBER recession indicator, monthly (the shaded bands)

Nothing is fitted: the figure shows the two series with recessions shaded, so
the reader can check the lead/lag claim - including where it is messy - by eye.
The script prints, for each recession start in the span, whether T10Y3M was
negative at any point in the prior 18 months, and the IP YoY value at the
recession start (was the coincident gauge already weak?).

Reproducible:
    python fig_e1_cycle.py     # numpy, matplotlib; stdlib urllib/csv
"""
import os, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)

INK, GREEN, CLARET, BLUE, GREY = "#17120e", "#2f6d4f", "#7c1c2c", "#2b4a6f", "#666"


def fred(series):
    path = os.path.join(DATA, series + ".csv")
    if not os.path.exists(path):
        socket.setdefaulttimeout(60)
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + series
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with open(path, "wb") as f:
            f.write(urllib.request.urlopen(req).read())
    dates, vals = [], []
    with open(path) as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if len(row) < 2 or row[1] in (".", ""):
                continue
            dates.append(dt.datetime.strptime(row[0], "%Y-%m-%d"))
            vals.append(float(row[1]))
    return dates, np.array(vals)


def yoy_calendar(dates, vals):
    """Calendar-based YoY: compare each month with the SAME calendar month one
    year earlier, not the 12th prior observation, so a gap in the series does
    not shift the comparison base (ERRATA / audit K9)."""
    lut = {(d.year, d.month): v for d, v in zip(dates, vals)}
    out_d, out_v = [], []
    for d, v in zip(dates, vals):
        prev = lut.get((d.year - 1, d.month))
        if prev is not None and prev != 0:
            out_d.append(d)
            out_v.append(100.0 * (v / prev - 1.0))
    return np.array(out_v), out_d


def rec_spans(rd, rv):
    spans, start = [], None
    for d, v in zip(rd, rv):
        if v == 1 and start is None:
            start = d
        elif v == 0 and start is not None:
            spans.append((start, d)); start = None
    if start is not None:
        spans.append((start, rd[-1]))
    return spans


ip_d, ip = fred("INDPRO")
sl_d, sl = fred("T10Y3M")                 # daily, starts 1982-01
rec_d, rec = fred("USREC")

ip_yoy, ip_yoy_d = yoy_calendar(ip_d, ip)

START = dt.datetime(1982, 1, 1)           # limited by T10Y3M's start
spans = [s for s in rec_spans(rec_d, rec) if s[1] >= START]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.0, 4.8), sharex=True,
                               gridspec_kw={"height_ratios": [1.15, 1.0]})
mi = [i for i, d in enumerate(ip_yoy_d) if d >= START]
ms = [i for i, d in enumerate(sl_d) if d >= START]

for ax in (ax1, ax2):
    for s0, s1 in spans:
        ax.axvspan(s0, s1, color="#d9d9d9", alpha=0.55, lw=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", alpha=0.25)
    ax.tick_params(labelsize=7.8)

ax1.plot([ip_yoy_d[i] for i in mi], ip_yoy[mi], "-", color=GREEN, lw=1.0)
ax1.axhline(0, color="#999", lw=0.7)
ax1.set_ylabel("IP, % YoY", fontsize=8.4)
ax1.set_title("Coincident: industrial production turns with the cycle …",
              fontsize=9.2, loc="left")
ax1.set_ylim(-19, 12)

ax2.plot([sl_d[i] for i in ms], sl[ms], "-", color=BLUE, lw=0.8)
ax2.axhline(0, color=CLARET, lw=0.9, ls="--")
ax2.set_ylabel("10y−3m, % pts", fontsize=8.4)
ax2.set_title("… leading: the 10y−3m Treasury spread tends to go negative first "
              "(but see 2022–24)", fontsize=9.2, loc="left")

fig.text(0.5, -0.018,
         "FRED series INDPRO (YoY computed), T10Y3M, USREC; shaded bands are NBER "
         "recessions. Span limited by T10Y3M start (1982). Cached to figures/data/.",
         ha="center", fontsize=7.2, color=GREY)
plt.tight_layout()

OUT = os.path.join(HERE, "fig_e1_cycle.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# --- printed checks quoted in the paper ------------------------------------
sl_dates = np.array([dt.datetime.toordinal(d) for d in sl_d])
for s0, _ in spans:
    o = dt.datetime.toordinal(s0)
    win = (sl_dates >= o - 548) & (sl_dates < o)          # prior 18 months
    neg = sl[win] < 0
    first_neg = None
    if neg.any():
        first_neg = sl_d[int(np.where(win)[0][int(np.argmax(neg))])]
    j = min(range(len(ip_yoy_d)), key=lambda k: abs((ip_yoy_d[k] - s0).days))
    print(f"recession start {s0:%Y-%m}: T10Y3M negative in prior 18m: "
          f"{bool(neg.any())}"
          + (f" (first {first_neg:%Y-%m})" if first_neg else "")
          + f" | IP YoY at start: {ip_yoy[j]:+.1f}%")
# the honest 2022+ case: most recent inversion without a recession (so far)
last_neg = [d for d, v in zip(sl_d, sl) if v < 0]
print(f"T10Y3M last negative day: {last_neg[-1]:%Y-%m-%d}; "
      f"data end {sl_d[-1]:%Y-%m-%d}; latest value {sl[-1]:+.2f}")
print(f"IP YoY latest {ip_yoy[-1]:+.1f}% ({ip_yoy_d[-1]:%Y-%m}); "
      f"recessions in span: {len(spans)}")
