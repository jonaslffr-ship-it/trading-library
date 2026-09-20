"""
Figure 2 (E2) - Mean monthly asset returns per growth x inflation quadrant.

Uses EXACTLY the classification written by fig_e2_quadrant.py
(data/quadrant_labels.csv) - one pre-committed rule, no relabeling. Two
alignments are computed and BOTH are printed:

  contemporaneous - month t's return matched with month t's quadrant label
                    (descriptive: what each regime looked like while it was on;
                    NOT tradable, because month t's label uses month t's data,
                    which is published in month t+1)
  lagged (t-2)    - month t's return matched with the label of month t-2,
                    the freshest label actually computable at the start of
                    month t given the ~1-month publication lag of INDPRO/CPI
                    (implementable, still ignoring revisions)

The figure shows the contemporaneous table (with 95% CIs and n per cell); the
lagged table is printed for the text. Cells with n<15 are flagged.

Data: SPX = Yahoo ^GSPC daily (cached spx_daily_max.csv, 1927->). TLT, GLD =
Yahoo daily range=max (TLT from 2002, GLD from 2004), cached. Monthly return =
month-end close over previous month-end close.

Reproducible:
    python fig_e2_quadrant.py          # writes data/quadrant_labels.csv first
    python fig_e2_quadrant_assets.py
"""
import os, csv, json, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
LBL = os.path.join(DATA, "quadrant_labels.csv")
if not os.path.exists(LBL):
    raise SystemExit("run fig_e2_quadrant.py first (it writes data/quadrant_labels.csv)")

label = {}
with open(LBL) as f:
    for row in csv.DictReader(f):
        label[row["ym"]] = row["quadrant"]


def yahoo_daily(symbol, cache_name):
    cache = os.path.join(DATA, cache_name)
    if os.path.exists(cache):
        dates, close = [], []
        with open(cache) as f:
            for row in csv.DictReader(f):
                dates.append(row["date"]); close.append(float(row["close"]))
        return dates, np.array(close)
    socket.setdefaulttimeout(60)
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           "?range=max&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    j = json.loads(urllib.request.urlopen(req).read())
    r = j["chart"]["result"][0]
    ts, cl = r["timestamp"], r["indicators"]["quote"][0]["close"]
    dates, close = [], []
    for t, c in zip(ts, cl):
        if c is None:
            continue
        dates.append(dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"))
        close.append(float(c))
    with open(cache, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "close"])
        for d, c in zip(dates, close):
            w.writerow([d, f"{c:.4f}"])
    return dates, np.array(close)


def monthly_returns(dates, close):
    """month-end close per 'YYYY-MM' -> {ym: monthly return}"""
    last = {}
    for d, c in zip(dates, close):
        last[d[:7]] = c                       # dates ascending -> ends at month end
    yms = sorted(last)
    return {b: last[b] / last[a] - 1.0 for a, b in zip(yms[:-1], yms[1:])}


sp_d, sp_c = yahoo_daily("%5EGSPC", "spx_daily_max.csv")
tl_d, tl_c = yahoo_daily("TLT", "tlt_daily.csv")
gl_d, gl_c = yahoo_daily("GLD", "gld_daily.csv")
rets = {"SPX": monthly_returns(sp_d, sp_c),
        "TLT": monthly_returns(tl_d, tl_c),
        "GLD": monthly_returns(gl_d, gl_c)}


def shift(m, k):
    y, mo = int(m[:4]), int(m[5:7])
    t = y * 12 + (mo - 1) + k
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


QUAD = ["Reflation", "Goldilocks", "Stagflation", "Deflation"]
ACOL = {"SPX": "#17120e", "TLT": "#31607e", "GLD": "#b07d2b"}


def table(lag):
    out = {}
    for a, r in rets.items():
        for q in QUAD:
            xs = [r[m] for m in r if shift(m, -lag) in label
                  and label[shift(m, -lag)] == q]
            xs = np.array(xs)
            n = len(xs)
            mu = xs.mean() if n else np.nan
            ci = 1.96 * xs.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
            out[(a, q)] = (mu, ci, n)
    return out


for lag, name in [(0, "CONTEMPORANEOUS (descriptive, not tradable)"),
                  (2, "LAGGED t-2 (implementable label, revisions ignored)")]:
    t = table(lag)
    print(f"\n== {name} == mean monthly return % (95% CI), n")
    for a in rets:
        row = "  ".join(
            f"{q[:6]}: {t[(a,q)][0]*100:+.2f}±{t[(a,q)][1]*100:.2f} (n={t[(a,q)][2]})"
            f"{' <n15!>' if t[(a,q)][2] < 15 else ''}"
            for q in QUAD)
        print(f"{a}: {row}")

t0 = table(0)

fig, ax = plt.subplots(figsize=(8.6, 4.4))
w = 0.24
xs = np.arange(len(QUAD))
for k, a in enumerate(rets):
    mus = [t0[(a, q)][0] * 100 for q in QUAD]
    cis = [t0[(a, q)][1] * 100 for q in QUAD]
    ax.bar(xs + (k - 1) * w, mus, w * 0.9, yerr=cis, capsize=3,
           color=ACOL[a], alpha=0.85, label=a,
           error_kw=dict(ecolor="#555", lw=0.9))
    for i, q in enumerate(QUAD):
        ax.annotate(f"n={t0[(a,q)][2]}", xy=(xs[i] + (k - 1) * w, -1.32),
                    ha="center", fontsize=6.6, color="#666")
ax.axhline(0, color="#999", lw=0.8)
ax.set_xticks(xs); ax.set_xticklabels(QUAD)
ax.set_ylabel("mean monthly total-price return (%)")
ax.set_ylim(-1.45, 1.9)
ax.set_title("Mean monthly return by quadrant, 95% CI - contemporaneous labels (descriptive)",
             fontsize=10.2)
ax.legend(frameon=False, fontsize=9, loc="upper right")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.03,
         "Quadrants: FRED INDPRO/CPIAUCSL momentum rule (fig_e2_quadrant). Prices: Yahoo daily - "
         f"^GSPC {sp_d[0][:7]}.., TLT {tl_d[0][:7]}.., GLD {gl_d[0][:7]}... Price returns only (no dividends); "
         "CIs assume i.i.d. months; labels use final-vintage data.",
         ha="center", fontsize=7.4, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_e2_quadrant_assets.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("\nwrote", OUT)
print(f"SPX months={len(rets['SPX'])} ({sp_d[0]}..{sp_d[-1]}), "
      f"TLT months={len(rets['TLT'])}, GLD months={len(rets['GLD'])}")
