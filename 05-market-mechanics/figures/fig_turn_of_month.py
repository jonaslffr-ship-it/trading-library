"""
Figure 5 - A pre-committed turn-of-month test on the S&P 500 (~30 years).

Free data: daily S&P 500 (^GSPC) closes, cached to data/spx_daily_max.csv.
The test is PRE-COMMITTED and reported as-is, whatever it shows:

    sample        1996-01-01 .. last cached close  (~30.7 years)
    TOM window    last 4 trading days of the month (-4..-1)
                  + first 3 trading days (+1..+3)      [fixed in advance]
    metric        mean daily close-to-close return, TOM vs. all other days
    split         in-sample  1996-01-01..2015-12-31
                  out-of-sample 2016-01-01..end       [fixed dates, opened once]
    CIs           95%, normal approximation (mean +/- 1.96 * s / sqrt(n))

Two panels: mean daily return by day-in-month position (-6..+6) with 95% CIs,
in-sample and out-of-sample. All cell values and n's are printed.

Reproducible:
    python fig_turn_of_month.py     # numpy, matplotlib; data cached locally
"""
import os, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "spx_daily_max.csv")

START, SPLIT = "1996-01-01", "2016-01-01"

dates, close = [], []
with open(CACHE) as f:
    for row in csv.DictReader(f):
        if row["date"] >= "1995-11-01":            # small lead-in for position labels
            dates.append(row["date"]); close.append(float(row["close"]))
close = np.array(close)
ret = np.diff(close) / close[:-1]
rdates = dates[1:]

# day-in-month position for each trading day: +1..+k from start, -1..-k from end
month = [d[:7] for d in rdates]
pos_from_start = np.zeros(len(rdates), int)
pos_from_end = np.zeros(len(rdates), int)
i = 0
while i < len(rdates):
    j = i
    while j < len(rdates) and month[j] == month[i]:
        j += 1
    for k in range(i, j):
        pos_from_start[k] = k - i + 1
        pos_from_end[k] = -(j - k)
    i = j

sel = np.array([d >= START for d in rdates])
is_ = sel & np.array([d < SPLIT for d in rdates])
oos = sel & np.array([d >= SPLIT for d in rdates])
tom = (pos_from_end >= -4) | (pos_from_start <= 3)


def cell(mask):
    r = ret[mask]
    n = len(r)
    m = r.mean() * 1e4
    ci = 1.96 * r.std(ddof=1) / np.sqrt(n) * 1e4 if n > 1 else np.nan
    return m, ci, n


def tstat(a, b):
    ra, rb = ret[a], ret[b]
    se = np.sqrt(ra.var(ddof=1) / len(ra) + rb.var(ddof=1) / len(rb))
    return (ra.mean() - rb.mean()) / se


POSITIONS = [-6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6]


def by_position(period):
    out = []
    for p in POSITIONS:
        m = period & ((pos_from_end == p) if p < 0 else (pos_from_start == p))
        out.append(cell(m))
    return out


cells_is = by_position(is_)
cells_oos = by_position(oos)

# ---- plot ----------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.7), sharey=True)
xpos = np.arange(len(POSITIONS))
for ax, cells, title in ((axes[0], cells_is, f"in-sample {START[:4]}–2015"),
                         (axes[1], cells_oos, f"out-of-sample 2016–{rdates[-1][:4]}")):
    means = [c[0] for c in cells]
    cis = [c[1] for c in cells]
    intom = [(p >= -4 and p <= -1) or (1 <= p <= 3) for p in POSITIONS]
    cols = ["#2f6d4f" if t else "#b9b3ab" for t in intom]
    ax.bar(xpos, means, yerr=cis, color=cols, width=0.72,
           error_kw=dict(ecolor="#666", lw=0.9, capsize=2))
    ax.axhline(0, color="#999", lw=0.8)
    ax.set_xticks(xpos)
    ax.set_xticklabels([f"{p:+d}" if p > 0 else str(p) for p in POSITIONS], fontsize=7.5)
    ax.set_title(title, fontsize=9.5)
    ax.set_xlabel("trading day relative to month end")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", alpha=0.2)
axes[0].set_ylabel("mean daily return (bps)")
fig.suptitle("Turn-of-month on the S&P 500: pre-committed window (last 4 + first 3 days), 95% CIs",
             fontsize=10.2, y=1.00)
fig.text(0.5, -0.03,
         f"Yahoo daily ^GSPC (cached), {START}–{rdates[-1]}. Green bars = pre-committed TOM window; "
         "CIs are 95%, normal approximation. Split fixed in advance.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_turn_of_month.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# ---- printed numbers ------------------------------------------------------
print(f"sample {START}..{rdates[-1]}  n_days={int(sel.sum())}  "
      f"IS n={int(is_.sum())}  OOS n={int(oos.sum())}")
for name, period in (("IS ", is_), ("OOS", oos)):
    m_t, ci_t, n_t = cell(period & tom)
    m_r, ci_r, n_r = cell(period & ~tom)
    t = tstat(period & tom, period & ~tom)
    ann_gap = (m_t - m_r)  # bps/day
    print(f"{name}: TOM mean={m_t:+.1f}bps (95%CI +/-{ci_t:.1f}, n={n_t}) | "
          f"rest mean={m_r:+.1f}bps (95%CI +/-{ci_r:.1f}, n={n_r}) | "
          f"diff={ann_gap:+.1f}bps/day  t={t:+.2f}")
print("per-position cells (mean bps, 95%CI, n):")
for p, ci_c, co_c in zip(POSITIONS, cells_is, cells_oos):
    print(f"  day {p:+d}:  IS {ci_c[0]:+6.1f} +/-{ci_c[1]:4.1f} (n={ci_c[2]:3d})   "
          f"OOS {co_c[0]:+6.1f} +/-{co_c[1]:4.1f} (n={co_c[2]:3d})")
