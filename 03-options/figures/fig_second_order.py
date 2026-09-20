"""
Figure 4 - Sign maps of the two delta-drift greeks: vanna and charm.

Didactic Black-Scholes-Merton heatmaps, no market data: call vanna (change in
delta per +1 vol point of implied vol) and call charm (change in delta per one
calendar day passing) across moneyness S/K (0.85-1.15) and days to expiry
(2-90). K = 100, sigma = 20%, r = 4%, q = 0. A diverging colormap is centered
at zero so the SIGN structure - which side of the strike makes the dealer buy
or sell tomorrow - is the visible object.

Closed forms used (q = 0):
    vanna = -phi(d1) * d2 / sigma            (per unit vol; /100 per point)
    charm = -phi(d1) * (2 r T - d2 sigma sqrt(T)) / (2 T sigma sqrt(T))
                                             (per year, as calendar time passes;
                                              /365 per day)

Reproducible:
    python fig_second_order.py     # numpy, matplotlib, stdlib math
"""
import os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SQRT2PI = math.sqrt(2.0 * math.pi)


def npdf(x):
    return np.exp(-0.5 * x * x) / SQRT2PI


K, SIG, R = 100.0, 0.20, 0.04
mny = np.linspace(0.85, 1.15, 241)            # S/K
days = np.linspace(2, 90, 240)                # days to expiry
M, D = np.meshgrid(mny, days)
S = M * K
T = D / 365.0

d1 = (np.log(S / K) + (R + 0.5 * SIG ** 2) * T) / (SIG * np.sqrt(T))
d2 = d1 - SIG * np.sqrt(T)
vanna = -npdf(d1) * d2 / SIG / 100.0                                    # per vol point
charm = -npdf(d1) * (2 * R * T - d2 * SIG * np.sqrt(T)) / (2 * T * SIG * np.sqrt(T)) / 365.0  # per day

fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.9), sharey=True)
for ax, Z, name, unit in [
    (axes[0], vanna, "Call vanna", "Δ-change per +1 vol point"),
    (axes[1], charm, "Call charm", "Δ-change per calendar day"),
]:
    lim = np.percentile(np.abs(Z), 99)
    pc = ax.pcolormesh(mny, days, Z, cmap="RdBu_r", vmin=-lim, vmax=lim,
                       shading="auto", rasterized=True)
    ax.contour(mny, days, Z, levels=[0.0], colors="#17120e", linewidths=1.1)
    ax.axvline(1.0, color="#555", lw=0.7, ls=":")
    ax.set_title(f"{name} ({unit})", fontsize=9.8)
    ax.set_xlabel("moneyness S/K", fontsize=9)
    cb = fig.colorbar(pc, ax=ax, shrink=0.92)
    cb.ax.tick_params(labelsize=7.5)
    ax.tick_params(labelsize=8.2)
axes[0].set_ylabel("days to expiry", fontsize=9)
fig.suptitle("Where tomorrow's forced delta adjustments come from: sign maps of vanna and charm",
             fontsize=10.4, y=1.00)
fig.text(0.5, -0.03,
         "Black-Scholes-Merton, K=100, sigma=20%, r=4%, q=0. Solid line = zero contour; blue = negative, "
         "red = positive. Didactic model computation, no market data.",
         ha="center", fontsize=7.5, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_second_order.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# numbers quoted in the text: sample values at 30 days
def at(mny_v, d_v, Z):
    i = np.argmin(np.abs(days - d_v)); j = np.argmin(np.abs(mny - mny_v))
    return Z[i, j]

for m in (0.95, 1.00, 1.05):
    print(f"30d S/K={m:.2f}: vanna/pt={at(m, 30, vanna):+.5f} charm/day={at(m, 30, charm):+.5f}")
for m in (0.97, 1.03):
    print(f"7d  S/K={m:.2f}: vanna/pt={at(m, 7, vanna):+.5f} charm/day={at(m, 7, charm):+.5f}")
