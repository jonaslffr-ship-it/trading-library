"""
Figure 4 - The 10y-2y yield-curve slope and its honest recession track record.

Free data (FRED public CSV, cached to data/):
  T10Y2Y - 10-year minus 2-year Treasury constant-maturity spread, daily (1976-)
  USREC  - NBER recession indicator, monthly (shaded bands)

ONE pre-committed episode rule, fixed before looking at the output and stated
here so the reader can audit it: an *inversion episode* starts on the first
day with T10Y2Y < 0 that is preceded by at least 126 consecutive business
days (about six months) of non-negative readings; the episode collects all
subsequent negative days until a new episode starts. Episodes with fewer than
5 negative days total are listed but flagged as blips. For each episode the
script prints the start date, the next NBER recession start (first USREC 0->1
month after the start), and the lag in months - INCLUDING the post-2022
episode, for which no recession had followed by the end of the data. Numbers
are reported as they fall out; nothing is filtered by hand.

Reproducible:
    python fig_e1_yield_curve.py     # numpy, matplotlib; stdlib urllib/csv
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


s_d, s = fred("T10Y2Y")
rec_d, rec = fred("USREC")
spans = [x for x in rec_spans(rec_d, rec) if x[1] >= s_d[0]]
rec_starts = [x[0] for x in rec_spans(rec_d, rec)]

# --- episode detection (rule in the docstring) ------------------------------
episodes = []                       # each: dict(start, end_of_last_neg, n_neg, min)
run_nonneg = 0
current = None
for d, v in zip(s_d, s):
    if v < 0:
        if run_nonneg >= 126 or current is None:
            if current is not None:
                episodes.append(current)
            current = {"start": d, "last": d, "n": 1, "min": v}
        else:
            current["last"] = d
            current["n"] += 1
            current["min"] = min(current["min"], v)
        run_nonneg = 0
    else:
        run_nonneg += 1
if current is not None:
    episodes.append(current)

rows = []
for e in episodes:
    nxt = next((r for r in rec_starts if r > e["start"]), None)
    lag = (nxt.year - e["start"].year) * 12 + (nxt.month - e["start"].month) if nxt else None
    rows.append((e, nxt, lag))

fig, ax = plt.subplots(figsize=(7.2, 4.0))
for s0, s1 in spans:
    ax.axvspan(s0, s1, color="#d9d9d9", alpha=0.55, lw=0)
ax.plot(s_d, s, "-", color=BLUE, lw=0.65)
ax.axhline(0, color=CLARET, lw=1.0, ls="--")
ax.fill_between(s_d, s, 0, where=(s < 0), color=CLARET, alpha=0.35, lw=0)
for e, nxt, lag in rows:
    if e["n"] < 5:
        continue
    ax.annotate(f"{e['start']:%Y}", xy=(e["start"], min(e["min"] - 0.12, -0.28)),
                fontsize=7.4, color=CLARET, ha="center")
ax.set_ylabel("10-year − 2-year Treasury yield, % points", fontsize=8.6)
ax.tick_params(labelsize=7.8)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.grid(True, axis="y", alpha=0.22)
ax.set_title("The 10y−2y slope: every inversion since 1976 marked, recessions shaded — "
             "note the unresolved 2022 case", fontsize=9.8)
fig.text(0.5, -0.02,
         "FRED series T10Y2Y, USREC; shaded bands are NBER recessions; red areas mark "
         "inversion (slope below zero). Episode rule fixed in the script. Cached to "
         "figures/data/.",
         ha="center", fontsize=7.2, color=GREY)
plt.tight_layout()

OUT = os.path.join(HERE, "fig_e1_yield_curve.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# --- the track record, printed as it falls out ------------------------------
print(f"span {s_d[0]:%Y-%m-%d}..{s_d[-1]:%Y-%m-%d}, n={len(s)} daily obs, "
      f"latest {s[-1]:+.2f}")
for e, nxt, lag in rows:
    tag = "blip (<5 neg days)" if e["n"] < 5 else "episode"
    if nxt:
        print(f"{tag}: inversion start {e['start']:%Y-%m-%d} "
              f"(min {e['min']:+.2f}, {e['n']} neg days) -> next recession "
              f"{nxt:%Y-%m} | lag {lag} months")
    else:
        open_m = (s_d[-1].year - e["start"].year) * 12 + (s_d[-1].month - e["start"].month)
        print(f"{tag}: inversion start {e['start']:%Y-%m-%d} "
              f"(min {e['min']:+.2f}, {e['n']} neg days) -> NO recession by data end "
              f"({open_m} months and counting)")
