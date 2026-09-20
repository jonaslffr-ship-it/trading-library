"""
Figure 2 (Statistics for Traders) - Hit rate is not edge: expectancy decides.

Didactic, fully seeded simulation - no market data. Two toy strategies, both
completely transparent, both fixed in advance:

  A: wins 70% of trades, but the average win is +0.5 R and the average
     loss is -1.5 R (cut winners fast, let losers run).
     Expectancy = 0.70 x 0.5 - 0.30 x 1.5 = -0.10 R per trade.
  B: wins only 40% of trades, but wins pay +2.5 R against -1.0 R losses.
     Expectancy = 0.40 x 2.5 - 0.60 x 1.0 = +0.40 R per trade.

The figure draws 30 independent 250-trade equity paths per strategy (thin lines)
plus the average path (bold), in cumulative R-multiples. Printed to stdout: the
theoretical expectancies, the realized mean R per trade across all simulated
trades, and - for section 6 of the paper - seeded bootstrap 90% confidence
intervals for the estimated expectancy after 50 trades and after 250 trades,
showing how slowly the uncertainty shrinks.

Reproducible:
    python fig_expectancy.py     # numpy + matplotlib only, seed 42
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(42)

N_PATHS, N_TRADES, N_BOOT = 30, 250, 10_000

def simulate(p_win, win_r, loss_r):
    """(N_PATHS, N_TRADES) array of per-trade outcomes in R-multiples."""
    wins = rng.random((N_PATHS, N_TRADES)) < p_win
    return np.where(wins, win_r, -loss_r)

A = simulate(0.70, 0.5, 1.5)      # high hit rate, poor payoff
B = simulate(0.40, 2.5, 1.0)      # low hit rate, strong payoff

exp_A_theory = 0.70 * 0.5 - 0.30 * 1.5
exp_B_theory = 0.40 * 2.5 - 0.60 * 1.0


def boot_ci(x, level=0.90):
    """Seeded bootstrap CI for the mean of a 1-D outcome sample."""
    idx = rng.integers(0, len(x), size=(N_BOOT, len(x)))
    means = x[idx].mean(axis=1)
    lo, hi = np.percentile(means, [(1 - level) / 2 * 100, (1 + level) / 2 * 100])
    return lo, hi

# One representative path per strategy for the bootstrap illustration (path 0).
ciA50 = boot_ci(A[0, :50]);  ciA250 = boot_ci(A[0])
ciB50 = boot_ci(B[0, :50]);  ciB250 = boot_ci(B[0])

fig, ax = plt.subplots(figsize=(6.8, 4.2))
x = np.arange(1, N_TRADES + 1)
for row in A.cumsum(axis=1):
    ax.plot(x, row, color="#7c1c2c", lw=0.5, alpha=0.22)
for row in B.cumsum(axis=1):
    ax.plot(x, row, color="#2f6d4f", lw=0.5, alpha=0.22)
ax.plot(x, A.cumsum(axis=1).mean(axis=0), color="#7c1c2c", lw=2.0,
        label=f"A: 70% hit rate, +0.5R / −1.5R  (expectancy −0.10R)")
ax.plot(x, B.cumsum(axis=1).mean(axis=0), color="#2f6d4f", lw=2.0,
        label=f"B: 40% hit rate, +2.5R / −1.0R  (expectancy +0.40R)")
ax.axhline(0, color="#999", lw=0.8)
ax.set_xlabel("trade number")
ax.set_ylabel("cumulative profit (R-multiples)")
ax.set_title("A 70%-win strategy loses; a 40%-win strategy earns: expectancy, not hit rate",
             fontsize=10.2)
ax.legend(fontsize=8, loc="upper left", frameon=False)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.02,
         "Seeded simulation (numpy seed 42), 30 paths of 250 trades per strategy; "
         "thin lines are single paths, bold lines the average path. No market data.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_expectancy.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"expectancy_theory A={exp_A_theory:+.3f}R  B={exp_B_theory:+.3f}R")
print(f"expectancy_realized A={A.mean():+.3f}R  B={B.mean():+.3f}R  "
      f"(all {N_PATHS * N_TRADES} simulated trades each)")
print(f"A path0: mean50={A[0,:50].mean():+.3f}R CI90_50=[{ciA50[0]:+.3f},{ciA50[1]:+.3f}]  "
      f"mean250={A[0].mean():+.3f}R CI90_250=[{ciA250[0]:+.3f},{ciA250[1]:+.3f}]")
print(f"B path0: mean50={B[0,:50].mean():+.3f}R CI90_50=[{ciB50[0]:+.3f},{ciB50[1]:+.3f}]  "
      f"mean250={B[0].mean():+.3f}R CI90_250=[{ciB250[0]:+.3f},{ciB250[1]:+.3f}]")
print(f"share of A paths positive after 50 trades: "
      f"{(A[:, :50].sum(axis=1) > 0).mean():.2f}")
