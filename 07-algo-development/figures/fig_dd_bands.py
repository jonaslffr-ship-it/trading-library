"""
Figure - Monte-Carlo drawdown bands for a KNOWN edge.

Didactic, fully simulated (no market data). ONE per-trade R-distribution is
declared up front and frozen: a win probability p = 0.40 paying +2R and a loss
paying -1R, so the expectancy is 0.40*2 - 0.60*1 = +0.20 R per trade (a real,
positive, unremarkable edge). Question the figure answers: if that edge is
GENUINELY present, how deep a drawdown should its owner expect to sit through
before concluding anything is wrong?

We simulate N independent equity paths of T trades (seed 42) and, at every
trade index, take the cross-path quantiles of the running maximum drawdown
(peak-to-trough, measured in R). The p50/p95/p99 envelope is the "this is still
normal" region for a healthy edge; a live drawdown that pierces the p99 line is
the first quantitative hint that the edge itself may have changed.

No parameter search: p, payoff, T, N and the seed are all fixed in advance; the
figure reports whatever the fixed edge produces.

Reproducible:
    python fig_dd_bands.py     # numpy, matplotlib only
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

P, WIN_R, LOSS_R = 0.40, 2.0, -1.0        # fixed per-trade R-distribution
EXP_R = P * WIN_R + (1 - P) * LOSS_R      # expectancy per trade (= +0.20 R)
T = 400                                   # trades per path
N = 40000                                 # Monte-Carlo paths
rng = np.random.default_rng(42)

wins = rng.random((N, T)) < P
step = np.where(wins, WIN_R, LOSS_R)      # per-trade R
equity = np.cumsum(step, axis=1)          # cumulative R (starts near 0)
equity = np.concatenate([np.zeros((N, 1)), equity], axis=1)   # prepend 0
runmax = np.maximum.accumulate(equity, axis=1)
dd = runmax - equity                      # drawdown in R at each trade
running_maxdd = np.maximum.accumulate(dd, axis=1)   # worst DD seen so far

x = np.arange(T + 1)
q50 = np.percentile(running_maxdd, 50, axis=0)
q95 = np.percentile(running_maxdd, 95, axis=0)
q99 = np.percentile(running_maxdd, 99, axis=0)

final_maxdd = running_maxdd[:, -1]
p50_f, p95_f, p99_f = np.percentile(final_maxdd, [50, 95, 99])

fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.9))
ax = axes[0]
ax.fill_between(x, 0, q99, color="#7c1c2c", alpha=0.10, label="up to p99")
ax.fill_between(x, 0, q95, color="#7c1c2c", alpha=0.16, label="up to p95")
ax.fill_between(x, 0, q50, color="#2f6d4f", alpha=0.22, label="up to median")
ax.plot(x, q50, color="#2f6d4f", lw=1.6)
ax.plot(x, q95, color="#7c1c2c", lw=1.5)
ax.plot(x, q99, color="#17120e", lw=1.3, ls="--")
ax.set_xlabel("trade number")
ax.set_ylabel("worst drawdown so far (R)")
ax.set_title("Drawdown a healthy edge still produces", fontsize=10)
ax.legend(fontsize=7.5, frameon=False, loc="upper left")
ax = axes[1]
ax.hist(final_maxdd, bins=60, color="#c9bfb4", edgecolor="#8a8178", lw=0.3)
for v, c, lab in ((p50_f, "#2f6d4f", "median"), (p95_f, "#7c1c2c", "p95"),
                  (p99_f, "#17120e", "p99")):
    ax.axvline(v, color=c, lw=1.3, ls=":")
    ax.annotate(f"{lab}\n{v:.0f}R", xy=(v, 0), xytext=(v, ax.get_ylim()[1] * 0.0),
                fontsize=7.5, color=c, ha="center", va="bottom")
ax.set_xlabel("maximum drawdown over 400 trades (R)")
ax.set_ylabel("paths")
ax.set_title("Distribution of the worst drawdown", fontsize=10)
for ax in axes:
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", alpha=0.22)
fig.text(0.5, -0.03,
         f"Simulated: p = {P}, payoff +{WIN_R:g}R / {LOSS_R:g}R, expectancy "
         f"{EXP_R:+.2f} R/trade; {N:,} paths x {T:,} trades, seed 42.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_dd_bands.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"expectancy={EXP_R:+.3f} R/trade over T={T} trades, N={N} paths")
print(f"max drawdown (R): median={p50_f:.1f}  p95={p95_f:.1f}  p99={p99_f:.1f}")
print(f"as multiple of expected terminal gain ({EXP_R*T:.0f}R): "
      f"p95 DD = {p95_f/(EXP_R*T):.2f}x")
