"""
Figure 3 - A transparent volatility-target reconstruction on the S&P 500.

Free data: daily S&P 500 (^GSPC) closes, cached to data/spx_daily_max.csv
(Yahoo Finance public chart API, range=max). ONE pre-committed, transparent
rule - no tuning, no search:

    target annualized volatility = 10%
    trailing realized vol RV_t   = sqrt(252 * mean(r^2 over last 21 days))
    allocation_t                 = min(1, target / RV_t)   (long-only, no leverage)
    the allocation decided at close t is held on day t+1 (no look-ahead);
    the day-t rebalancing flow    = allocation_t - allocation_{t-1}  (% of NAV)

The figure shows trailing RV, the allocation path, and the implied daily
rebalancing flow, with the Feb-2018 and Mar-2020 deleveraging episodes shaded.
Every quoted number is printed below. The rule is illustrative of the MECHANISM;
real vol-control books differ in target, window, and caps (stated in the text).

Reproducible:
    python fig_voltarget.py     # numpy, matplotlib; data cached locally
"""
import os, csv, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CACHE = os.path.join(DATA, "spx_daily_max.csv")

START = "1990-01-01"          # sample start (burn-in before the plot window)
PLOT_FROM = "2006-01-01"      # plot window start (GFC, Volmageddon, COVID all visible)
TARGET = 0.10                 # 10% annualized target
WIN = 21                      # trailing window, trading days

dates, close = [], []
with open(CACHE) as f:
    for row in csv.DictReader(f):
        if row["date"] >= START:
            dates.append(row["date"]); close.append(float(row["close"]))
close = np.array(close)
ret = np.diff(close) / close[:-1]
rdates = dates[1:]                                   # date of each return

# trailing 21d realized vol (annualized), aligned so RV[t] uses returns up to and incl. t
rv = np.full(len(ret), np.nan)
for i in range(WIN - 1, len(ret)):
    rv[i] = np.sqrt(252.0 * np.mean(ret[i - WIN + 1:i + 1] ** 2))
alloc = np.minimum(1.0, TARGET / rv)                 # allocation decided at close t
dalloc = np.diff(alloc)                              # day-t flow, % of NAV (t >= 1)
fdates = rdates[1:]

ok = ~np.isnan(dalloc)
i_min = np.nanargmin(dalloc)
i_max = np.nanargmax(dalloc)

def ep_sum(d0, d1):
    m = [(d0 <= d <= d1) and not np.isnan(x) for d, x in zip(fdates, dalloc)]
    sel = dalloc[np.array(m)]
    return sel.sum(), sel.min(), len(sel)

feb18 = ep_sum("2018-01-29", "2018-02-14")
mar20 = ep_sum("2020-02-19", "2020-04-07")
oct08 = ep_sum("2008-09-15", "2008-11-28")

# ---- plot ----------------------------------------------------------------
x = np.array([dt.datetime.strptime(d, "%Y-%m-%d") for d in fdates])
p0 = np.searchsorted(fdates, PLOT_FROM)
sh = [("2018-01-29", "2018-02-14", "Feb 2018"), ("2020-02-19", "2020-04-07", "Mar 2020")]

fig, axes = plt.subplots(3, 1, figsize=(7.0, 6.6), sharex=True,
                         gridspec_kw={"height_ratios": [1, 1, 1.15]})
ax = axes[0]
ax.plot(x[p0:], 100 * rv[1:][p0:], color="#17120e", lw=0.9)
ax.axhline(100 * TARGET, color="#2f6d4f", lw=1.0, ls="--")
ax.annotate("target 10%", xy=(x[p0 + 200], 11), fontsize=8, color="#2f6d4f")
ax.set_ylabel("trailing 21d RV\n(% ann.)")
ax.set_yscale("log"); ax.set_yticks([5, 10, 20, 40, 80]); ax.set_yticklabels(["5", "10", "20", "40", "80"])

ax = axes[1]
ax.plot(x[p0:], alloc[1:][p0:], color="#3b5b78", lw=0.9)
ax.set_ylabel("allocation\n(fraction of NAV)")
ax.set_ylim(0, 1.05)

ax = axes[2]
ax.bar(x[p0:], 100 * dalloc[p0:], width=1.6, color="#7c1c2c")
ax.set_ylabel("daily rebalancing flow\n(% of NAV)")
ax.axhline(0, color="#999", lw=0.6)

for a in axes:
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.grid(True, axis="y", alpha=0.2)
    for d0, d1, lab in sh:
        a.axvspan(dt.datetime.strptime(d0, "%Y-%m-%d"), dt.datetime.strptime(d1, "%Y-%m-%d"),
                  color="#c9a227", alpha=0.25, lw=0)
axes[0].annotate("Feb 2018", xy=(dt.datetime.strptime("2018-01-25", "%Y-%m-%d"), 60),
                 fontsize=8, color="#8a6d3b", ha="right")
axes[0].annotate("Mar 2020", xy=(dt.datetime.strptime("2020-04-12", "%Y-%m-%d"), 60),
                 fontsize=8, color="#8a6d3b", ha="left")
axes[0].set_title("A 10%-vol-target rule on the S&P 500: the mechanical sell-into-weakness",
                  fontsize=10.2)
fig.text(0.5, -0.01,
         f"Yahoo daily ^GSPC (cached), rule computed {rdates[0]}–{rdates[-1]}, plotted from {PLOT_FROM}. "
         "Allocation = min(1, 10% / trailing-21d RV), traded next day; no tuning.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_voltarget.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# ---- printed numbers (all figures quoted in the text come from here) ------
print(f"sample={rdates[0]}..{rdates[-1]} n_ret={len(ret)}")
print(f"peak_one_day_DELEVERAGING: {fdates[i_min]}  dalloc={100*dalloc[i_min]:+.1f}% of NAV "
      f"(alloc {alloc[i_min]:.3f} -> {alloc[i_min+1]:.3f})")
m18 = np.array([("2018-01-29" <= d <= "2018-02-14") for d in fdates])
i18 = np.where(m18)[0][np.nanargmin(dalloc[m18])]
print(f"Feb2018 worst single day: {fdates[i18]}  dalloc={100*dalloc[i18]:+.1f}% of NAV "
      f"(alloc {alloc[i18]:.3f} -> {alloc[i18+1]:.3f})")
print(f"peak_one_day_RELEVERAGING: {fdates[i_max]}  dalloc={100*dalloc[i_max]:+.1f}% of NAV")
print(f"Feb2018 episode (2018-01-29..2018-02-14): cum={100*feb18[0]:+.1f}% NAV, "
      f"worst day={100*feb18[1]:+.1f}%, days={feb18[2]}")
print(f"Mar2020 episode (2020-02-19..2020-04-07): cum={100*mar20[0]:+.1f}% NAV, "
      f"worst day={100*mar20[1]:+.1f}%, days={mar20[2]}")
print(f"GFC 2008 (2008-09-15..2008-11-28): cum={100*oct08[0]:+.1f}% NAV, "
      f"worst day={100*oct08[1]:+.1f}%, days={oct08[2]}")
print(f"alloc: mean={np.nanmean(alloc):.2f} min={np.nanmin(alloc):.2f} "
      f"(on {rdates[int(np.nanargmin(alloc))]}) last={alloc[-1]:.2f} ({rdates[-1]})")
print(f"mean |dalloc| = {100*np.nanmean(np.abs(dalloc)):.2f}% NAV/day; "
      f"annual one-way turnover ~ {100*np.nanmean(np.abs(dalloc))*252:.0f}% NAV")
print(f"days with |dalloc| > 5% NAV: {int(np.nansum(np.abs(dalloc) > 0.05))}")
