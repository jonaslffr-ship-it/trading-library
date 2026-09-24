"""
Figure 1 - The best of N backtests on pure noise.

Shows the expected maximum in-sample annualized Sharpe ratio across N
independently backtested strategies that ALL have zero true edge, as a
function of N: a Monte-Carlo estimate against the sqrt(2 ln N) "noise
ceiling". It visualizes why selecting the best of many backtests manufactures
an impressive Sharpe out of pure noise (Bailey et al. 2014).

Reproducible:
    python fig_multiple_testing.py        # needs numpy, matplotlib; seed 42

Free data only: this figure is a pure simulation (no market data required).
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
T = 1260                       # ~5 years of daily returns per strategy
M = 20000                      # Monte-Carlo repetitions per N
rng = np.random.default_rng(SEED)

# Std of the ANNUALIZED Sharpe estimate under the null (true SR = 0):
# daily Sharpe estimate ~ N(0, 1/T), annualized by sqrt(252).
sigma_sr = np.sqrt(252.0 / T)

Ns = np.array([1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 1000])

mc = np.empty(len(Ns))
for k, N in enumerate(Ns):
    draws = rng.normal(0.0, sigma_sr, size=(M, int(N)))
    mc[k] = draws.max(axis=1).mean()

theory = sigma_sr * np.sqrt(2.0 * np.log(Ns))

fig, ax = plt.subplots(figsize=(6.6, 4.0))
ax.plot(Ns, theory, "-", color="#7c1c2c", lw=1.8,
        label=r"$\sigma_{SR}\,\sqrt{2\ln N}$  (noise ceiling)")
ax.plot(Ns, mc, "o", color="#17120e", ms=4.5,
        label=f"Monte Carlo ({M:,} reps)")
ax.set_xscale("log")
ax.set_xlabel("Number of independently backtested strategies, N (log scale)")
ax.set_ylabel("Expected best in-sample\nannualized Sharpe ratio")
ax.axhline(0, color="#999", lw=0.6)
ax.annotate(f"best of 1000 ≈ {mc[-1]:.2f}", xy=(1000, mc[-1]),
            xytext=(90, mc[-1] - 0.38), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="#555", lw=0.8))
ax.set_title("Selecting the best of N zero-edge backtests manufactures Sharpe from noise",
             fontsize=10.3)
ax.legend(frameon=False, fontsize=9, loc="upper left")
ax.grid(True, which="both", axis="y", alpha=0.25)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.text(0.5, -0.02,
         f"Every strategy has zero true edge. Daily sample T={T} (~5y); "
         r"$\sigma_{SR}=\sqrt{252/T}=$" + f"{sigma_sr:.2f}. Seed {SEED}.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_multiple_testing.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print("MC best-of-N:", dict(zip(Ns.tolist(), np.round(mc, 3).tolist())))
