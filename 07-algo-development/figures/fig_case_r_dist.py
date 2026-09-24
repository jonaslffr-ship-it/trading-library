"""
Figure - R-multiple distribution of the real ES intraday case study (Case A).

NOT didactic: this reads a PRIVATE per-trade export (an intraday reversion
strategy on E-mini S&P 500 futures; not redistributed) and computes the
trade-level R-multiple distribution.
The file is NOT redistributed; only aggregate, risk-normalized statistics are
reported here and nothing in absolute currency is printed or plotted.

R-multiple definition. The export carries a clean per-trade P&L but no per-trade
frozen-stop distance, and (see the paper) the intended R-ladder exits never
filled, so R cannot be read off the exit tags. We therefore normalize each
trade's P&L by the fixed per-trade risk budget the position sizer targets -
which is 1R by construction (the sizer floors contracts to that risk). This is
an approximation for trades where a contract floor forces slightly more than one
risk unit; it is stated as such. Profit factor and hit rate are invariant to the
normalization; only the R location/scale depends on it.

Prints n, hit rate, expectancy in R, and profit factor, and cross-checks the PF
against the value reported in the C2 backtesting paper (1.32).

Reproducible only with the private trade list: set the TRADE_LIST_CSV
environment variable to its path. Otherwise this figure skips cleanly.
"""
import os
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
# The private per-trade export is not redistributed and no path or filename is
# hard-coded. Point TRADE_LIST_CSV at it locally to reproduce this one figure.
CSV = os.environ.get("TRADE_LIST_CSV", "")

RISK_UNIT = 500.0   # fixed per-trade risk budget the sizer targets = 1R (parameter, not shown)

if not os.path.exists(CSV):
    # This is the ONE figure in the series that is not reproducible from free
    # data: it reads the author's private per-trade export, which is not
    # redistributed. Skip cleanly (exit 0, do NOT overwrite the committed PNG)
    # so a reader's `make figures` completes; the disclosed aggregates stand.
    print("SKIPPED fig_case_r_dist: needs the private ES trade list (not "
          "redistributed; set TRADE_LIST_CSV to reproduce). Committed PNG kept; "
          "reported aggregates: n=2284, hit 28.2%, expectancy +0.165R, PF 1.32.")
    raise SystemExit(0)

pnl, win, is_oos = [], [], []
with open(CSV, newline="") as f:
    for row in csv.DictReader(f):
        pnl.append(float(row["pnl"]))
        win.append(int(row["win"]))
        is_oos.append(row["is_oos"])
pnl = np.array(pnl)
win = np.array(win)
is_oos = np.array(is_oos)

R = pnl / RISK_UNIT
n = len(R)
hit = win.mean()
exp_R = R.mean()
gp = R[R > 0].sum()
gl = -R[R < 0].sum()
pf = gp / gl

exp_is = R[is_oos == "IS"].mean()
exp_oos = R[is_oos == "OOS"].mean()

# display clip (a few extreme runner trades sit far to the right)
LO, HI = -2.5, 8.0
clipped = np.clip(R, LO, HI)
over = int((R > HI).sum())

fig, ax = plt.subplots(figsize=(9.2, 4.0))
bins = np.linspace(LO, HI, 64)
ax.hist(clipped[win == 0], bins=bins, color="#c9a9a2", edgecolor="#9a7b6b",
        lw=0.25, label=f"losers ({(1-hit)*100:.0f}%)")
ax.hist(clipped[win == 1], bins=bins, color="#8fa07d", edgecolor="#5f6d4f",
        lw=0.25, label=f"winners ({hit*100:.0f}%)", alpha=0.9)
ax.axvline(0, color="#999", lw=0.8)
ax.axvline(exp_R, color="#17120e", lw=1.6, ls="--",
           label=f"expectancy {exp_R:+.2f}R")
ax.axvline(-1.0, color="#7c1c2c", lw=1.0, ls=":")
ax.annotate("full stop\n~ -1R", xy=(-1.0, ax.get_ylim()[1] * 0.62),
            fontsize=7.5, color="#7c1c2c", ha="center")
ax.annotate(f"{over} runner trades > {HI:g}R\n(clipped; max {R.max():.0f}R)",
            xy=(HI, ax.get_ylim()[1] * 0.5), xytext=(HI - 2.6, ax.get_ylim()[1] * 0.72),
            fontsize=7.5, color="#666",
            arrowprops=dict(arrowstyle="->", color="#999", lw=0.8))
ax.set_xlabel("trade result (R-multiples, risk-normalized)")
ax.set_ylabel("number of trades")
ax.set_title(f"n = {n:,} trades  |  hit rate {hit*100:.1f}%  |  "
             f"expectancy {exp_R:+.3f}R  |  PF {pf:.2f}", fontsize=10)
ax.legend(fontsize=8, frameon=False, loc="upper right")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.22)
fig.text(0.5, -0.02,
         "Private ES intraday trade list (not redistributed); gross of costs. "
         "R = P&L / fixed per-trade risk budget (1R by construction).",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_case_r_dist.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"n={n}  hit_rate={hit*100:.2f}%  expectancy={exp_R:+.4f}R  PF={pf:.4f}")
print(f"median R={np.median(R):+.3f}  min={R.min():.2f}R  max={R.max():.2f}R  runners>{HI:g}R: {over}")
print(f"expectancy IS={exp_is:+.4f}R (n={int((is_oos=='IS').sum())})  "
      f"OOS={exp_oos:+.4f}R (n={int((is_oos=='OOS').sum())})")
print(f"cross-check vs C2 backtesting paper: PF {pf:.2f} vs reported 1.32  ->  "
      f"{'MATCH' if abs(pf-1.32)<0.02 else 'CHECK'}")
