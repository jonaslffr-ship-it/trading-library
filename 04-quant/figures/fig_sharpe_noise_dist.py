"""
Figure 1 (C3) - The FULL distribution of the best-of-N Sharpe under zero edge.

Extends the C2 figure (which showed only the expected maximum): here the entire
sampling distribution of max{SR_1..SR_N} is drawn for N in {1, 10, 100, 1000}
zero-edge strategies, on two sample lengths (five years and one year of daily
data). Two lessons: (i) the whole distribution shifts right and TIGHTENS as N
grows - the best of many noise backtests is not just biased, it is reliably
impressive; (ii) halving-to-a-fifth the sample length scales every Sharpe by
sqrt(5) - short samples manufacture the biggest heroes.

Reproducible:
    python fig_sharpe_noise_dist.py    # needs numpy, matplotlib; seed 42

Free data only: pure simulation (no market data required).
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
M = 20000                       # Monte-Carlo repetitions
NS = [1, 10, 100, 1000]
SAMPLES = [(1260, "~5 years of daily data (T=1260)"),
           (252, "~1 year of daily data (T=252)")]
COLORS = {1: "#999999", 10: "#3b6b8a", 100: "#8a6d3b", 1000: "#7c1c2c"}

rng = np.random.default_rng(SEED)
grid = np.linspace(-2.5, 5.0, 600)


def kde(x, grid):
    """Plain Gaussian KDE (Silverman bandwidth) - no scipy needed."""
    h = 1.06 * x.std() * len(x) ** (-1 / 5)
    z = (grid[:, None] - x[None, :]) / h
    return np.exp(-0.5 * z * z).sum(axis=1) / (len(x) * h * np.sqrt(2 * np.pi))


fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.9), sharey=True)
report = {}
for ax, (T, label) in zip(axes, SAMPLES):
    sigma_sr = np.sqrt(252.0 / T)          # std of annualized SR estimate, true SR = 0
    draws = rng.normal(0.0, sigma_sr, size=(M, max(NS)))
    runmax = np.maximum.accumulate(draws, axis=1)   # best of the first n trials
    for N in NS:
        mx = runmax[:, N - 1]
        dens = kde(mx, grid)
        ax.plot(grid, dens, "-", lw=1.7, color=COLORS[N],
                label=f"N={N}  (E[max]={mx.mean():.2f})")
        ax.fill_between(grid, dens, color=COLORS[N], alpha=0.10)
        report[(T, N)] = (mx.mean(), np.median(mx),
                          float((mx > 1.0).mean()), float((mx > 2.0).mean()))
    ax.axvline(0, color="#bbbbbb", lw=0.7)
    ax.set_title(label, fontsize=9.8)
    ax.set_xlabel("best in-sample annualized Sharpe ratio")
    ax.grid(True, axis="y", alpha=0.22)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=8.2, loc="upper right")
axes[0].set_ylabel("density")
fig.suptitle("The best of N zero-edge backtests: the full distribution, not just its mean",
             fontsize=10.6, y=1.00)
fig.text(0.5, -0.03,
         f"Every strategy has zero true edge; annualized SR estimate ~ N(0, 252/T). "
         f"{M:,} Monte-Carlo repetitions per panel, seed {SEED}; best-of-N nested within one draw.",
         ha="center", fontsize=7.6, color="#666666")
plt.tight_layout()

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_sharpe_noise_dist.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
for (T, N), (m, med, p1, p2) in sorted(report.items()):
    print(f"T={T:5d} N={N:5d}  E[max]={m:5.2f}  median={med:5.2f}  "
          f"P(max>1)={p1:6.1%}  P(max>2)={p2:6.1%}")
