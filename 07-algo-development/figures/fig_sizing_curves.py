"""
Figure 1 - Growth and drawdown as a function of the Kelly fraction.

Didactic, fully simulated (no market data). ONE fixed trade distribution is
declared up front: hit rate p = 0.45, payoff b = 1.5 (winners are +1.5 R,
losers are -1 R on the stake), so the per-trade edge is p*b - q = 0.125 per
unit staked and the Kelly fraction is f* = p - q/b = 0.0833 of equity.
A single matrix of win/loss outcomes (seed 42) is reused across all staking
fractions, so every curve sees exactly the same luck and differs only in
sizing. Median terminal growth and the median / 95th-percentile maximum
drawdown are reported against f/f*.

No parameter search: p, b, T, N and the seed are fixed in advance; the point
of the figure is the shape of the curves, not the specific strategy.

Reproducible:
    python fig_sizing_curves.py     # numpy, matplotlib only
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

P, B = 0.45, 1.5                    # hit rate, payoff ratio (fixed in advance)
Q = 1.0 - P
F_STAR = P - Q / B                  # Kelly fraction of equity per trade
T = 1000                            # trades per path
N = 3000                            # Monte-Carlo paths
rng = np.random.default_rng(42)
wins = rng.random((N, T)) < P       # ONE outcome matrix, reused for every f

fracs = np.linspace(0.1, 2.0, 39)   # multiples of Kelly
med_growth, med_dd, p95_dd = [], [], []
for m in fracs:
    f = m * F_STAR
    logret = np.where(wins, np.log1p(B * f), np.log1p(-f))
    cum = np.cumsum(logret, axis=1)
    runmax = np.maximum.accumulate(np.maximum(cum, 0.0), axis=1)
    dd = 1.0 - np.exp(cum - runmax)              # drawdown in equity terms
    maxdd = dd.max(axis=1)
    med_growth.append(np.median(cum[:, -1]))
    med_dd.append(np.median(maxdd))
    p95_dd.append(np.percentile(maxdd, 95))
med_growth = np.array(med_growth); med_dd = np.array(med_dd); p95_dd = np.array(p95_dd)

# theoretical growth rate per trade
g_theory = P * np.log1p(B * fracs * F_STAR) + Q * np.log1p(-fracs * F_STAR)


def stats_at(mult):
    f = mult * F_STAR
    logret = np.where(wins, np.log1p(B * f), np.log1p(-f))
    cum = np.cumsum(logret, axis=1)
    runmax = np.maximum.accumulate(np.maximum(cum, 0.0), axis=1)
    maxdd = (1.0 - np.exp(cum - runmax)).max(axis=1)
    return (np.median(np.exp(cum[:, -1])), np.median(maxdd),
            np.percentile(maxdd, 95), np.mean(np.exp(cum[:, -1]) < 1.0))


full = stats_at(1.0)
half = stats_at(0.5)

fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.9))
ax = axes[0]
ax.plot(fracs, med_growth / T, "-", color="#17120e", lw=1.9,
        label="simulated (median)")
ax.plot(fracs, g_theory, "--", color="#999999", lw=1.2, label="theoretical g(f)")
ax.axvline(1.0, color="#7c1c2c", lw=1.0, ls=":")
ax.axvline(0.5, color="#2f6d4f", lw=1.0, ls=":")
ax.annotate("full Kelly", xy=(1.0, g_theory.max() * 0.25), fontsize=8.5,
            color="#7c1c2c", rotation=90, va="bottom", ha="right")
ax.annotate("half Kelly", xy=(0.5, g_theory.max() * 0.25), fontsize=8.5,
            color="#2f6d4f", rotation=90, va="bottom", ha="right")
ax.axhline(0, color="#999", lw=0.8)
ax.set_xlabel("staking fraction as a multiple of Kelly  (f / f*)")
ax.set_ylabel("log-growth per trade")
ax.set_title("Growth peaks at Kelly - and dies past 2x", fontsize=10)
ax.legend(fontsize=8, frameon=False)
ax = axes[1]
ax.plot(fracs, 100 * med_dd, "-", color="#17120e", lw=1.9, label="median max DD")
ax.plot(fracs, 100 * p95_dd, "-", color="#7c1c2c", lw=1.6, label="p95 max DD")
ax.axvline(1.0, color="#7c1c2c", lw=1.0, ls=":")
ax.axvline(0.5, color="#2f6d4f", lw=1.0, ls=":")
ax.set_xlabel("staking fraction as a multiple of Kelly  (f / f*)")
ax.set_ylabel("maximum drawdown over 1,000 trades (%)")
ax.set_title("Drawdown rises monotonically - no peak to hide behind", fontsize=10)
ax.legend(fontsize=8, frameon=False)
for ax in axes:
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.03,
         f"Simulated: p = {P}, payoff = {B}, Kelly f* = {F_STAR:.4f} of equity; "
         f"{N:,} paths x {T:,} trades, seed 42; identical outcomes across all fractions.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_sizing_curves.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"f_star={F_STAR:.4f} edge_per_unit={P*B-Q:.3f}")
print(f"full Kelly : median terminal multiple x{full[0]:.0f}  medianDD={full[1]*100:.0f}%  "
      f"p95DD={full[2]*100:.0f}%  P(end<start)={full[3]*100:.1f}%")
print(f"half Kelly : median terminal multiple x{half[0]:.0f}  medianDD={half[1]*100:.0f}%  "
      f"p95DD={half[2]*100:.0f}%  P(end<start)={half[3]*100:.1f}%")
g_full = P * np.log1p(B * F_STAR) + Q * np.log1p(-F_STAR)
g_half = P * np.log1p(B * 0.5 * F_STAR) + Q * np.log1p(-0.5 * F_STAR)
print(f"g(full)={g_full:.6f}/trade g(half)={g_half:.6f}/trade "
      f"half/full growth ratio={g_half/g_full*100:.0f}%")
