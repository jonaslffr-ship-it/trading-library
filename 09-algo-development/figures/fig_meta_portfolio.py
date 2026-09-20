"""
Figure - When a portfolio of low-correlation edges beats any single algo.

Didactic, fully simulated (no market data). Three strategies are declared up
front, chosen to resemble the three real families in the author's own work
(an intraday mean-reversion, an overnight breakout, a volatility
mean-reversion). Each has a modest standalone Sharpe; their pairwise
correlations are LOW and fixed (0.15 / 0.10 / 0.20). Daily returns are drawn as
correlated Gaussians (Cholesky, seed 42) with per-strategy means/vols set so
each targets its declared annualized Sharpe.

The headline Sharpes are the EXACT population (analytic) values, not one noisy
sample: over any finite window a Sharpe estimate has a large standard error, so
reporting a single realized draw would let luck, not diversification, tell the
story. The plotted equity curves are one representative 6-year draw for visual
flavour; the legend carries the analytic Sharpes.

The combination is an equal-risk (inverse-volatility) blend with constant
weights. Because the edges are weakly correlated, the blend's population Sharpe
exceeds every single leg's - diversification, not leverage, does the work.

No search over correlations, weights, or Sharpe targets - all fixed in advance.

Reproducible:
    python fig_meta_portfolio.py     # numpy, matplotlib only
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

NAMES = ["intraday reversion", "overnight breakout", "vol mean-reversion"]
SR_TARGET = np.array([0.90, 0.80, 1.00])      # annualized Sharpe per leg (fixed)
ANN_VOL = np.array([0.10, 0.12, 0.09])        # annualized vol per leg (fixed)
CORR = np.array([[1.00, 0.15, 0.10],
                 [0.15, 1.00, 0.20],
                 [0.10, 0.20, 1.00]])
DAYS = 252 * 6
rng = np.random.default_rng(42)

mu_d = SR_TARGET * ANN_VOL / 252.0            # daily mean per leg
sd_d = ANN_VOL / np.sqrt(252.0)               # daily vol per leg

# equal-risk (inverse-vol) weights, fixed and constant
w = (1.0 / ANN_VOL) / np.sum(1.0 / ANN_VOL)

# --- EXACT population Sharpes (no sampling noise) ---
cov_d = CORR * np.outer(sd_d, sd_d)
mu_b = float(w @ mu_d)
var_b = float(w @ cov_d @ w)
sr_legs_pop = SR_TARGET.copy()                # exact by construction
sr_blend_pop = mu_b / np.sqrt(var_b) * np.sqrt(252.0)
# diversification ratio = weighted-average leg vol / blend vol
dr = float(w @ sd_d) / np.sqrt(var_b)

# --- one representative path for the plot ---
L = np.linalg.cholesky(CORR)
z = rng.standard_normal((DAYS, 3)) @ L.T
rets = mu_d + sd_d * z
blend = rets @ w
eq = np.vstack([np.cumprod(1 + rets[:, i]) for i in range(3)] +
               [np.cumprod(1 + blend)])
x = np.arange(DAYS) / 252.0

fig, ax = plt.subplots(figsize=(9.2, 4.2))
cols = ["#b8a894", "#9a7b6b", "#7c8a6d"]
for i in range(3):
    ax.plot(x, eq[i], color=cols[i], lw=1.3,
            label=f"{NAMES[i]} (Sharpe {sr_legs_pop[i]:.2f})")
ax.plot(x, eq[3], color="#17120e", lw=2.2,
        label=f"equal-risk blend (Sharpe {sr_blend_pop:.2f})")
ax.set_xlabel("years (one representative simulated path)")
ax.set_ylabel("growth of 1 unit (compounded)")
ax.set_title("The blend outruns every leg on risk-adjusted terms", fontsize=10)
ax.legend(fontsize=8, frameon=False, loc="upper left")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.22)
fig.text(0.5, -0.02,
         "Simulated: 3 weakly-correlated edges (rho 0.10-0.20), inverse-vol weights; "
         f"Sharpes are exact population values; diversification ratio {dr:.2f}.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_meta_portfolio.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
for i in range(3):
    print(f"{NAMES[i]:22s} population Sharpe = {sr_legs_pop[i]:.3f}")
print(f"{'equal-risk blend':22s} population Sharpe = {sr_blend_pop:.3f}")
print(f"best single leg = {sr_legs_pop.max():.3f}; blend uplift = {sr_blend_pop - sr_legs_pop.max():+.3f}")
print(f"diversification ratio = {dr:.3f}")
