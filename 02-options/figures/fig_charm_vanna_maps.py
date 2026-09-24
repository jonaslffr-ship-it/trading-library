"""
Figure - Black-Scholes-Merton charm and vanna maps across moneyness and time
to expiry (didactic; no market data).

charm = dDelta/dt (delta drift per calendar day, all else equal)
vanna = dDelta/dsigma (delta shift per +1 vol point, i.e. +0.01 in sigma)

Both are evaluated for a European call under BSM with sigma=0.18, r=0.04,
q=0.012; for these parameters the put maps are visually identical (the
call-put difference is O(q)). The zero contour is drawn in black: it sits
near d2=0, slightly above the at-the-money strike. Values are clipped at the
2nd/98th percentile so the near-expiry explosion does not saturate the map.

Reproducible:
    python fig_charm_vanna_maps.py     # numpy, matplotlib; math.erf for Phi
"""
import os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

HERE = os.path.dirname(os.path.abspath(__file__))
SIG, R, Q = 0.18, 0.04, 0.012

CMAP = LinearSegmentedColormap.from_list(
    "muted_div", ["#2a5d8f", "#f4f1ec", "#7c1c2c"])


def norm_pdf(x):
    return np.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def norm_cdf(x):
    return 0.5 * (1.0 + np.vectorize(math.erf)(x / math.sqrt(2.0)))


mny = np.linspace(0.90, 1.10, 241)          # K / S
dte = np.linspace(0.5, 30.0, 241)           # calendar days
KS, D = np.meshgrid(mny, dte)
T = D / 365.0
S = 1.0
K = KS
d1 = (np.log(S / K) + (R - Q + 0.5 * SIG ** 2) * T) / (SIG * np.sqrt(T))
d2 = d1 - SIG * np.sqrt(T)

# call charm per calendar day; put charm = this - q*exp(-qT) (visually identical)
charm = (Q * np.exp(-Q * T) * norm_cdf(d1)
         - np.exp(-Q * T) * norm_pdf(d1)
         * (2 * (R - Q) * T - d2 * SIG * np.sqrt(T)) / (2 * T * SIG * np.sqrt(T))
         ) / 365.0
# vanna per +1 vol point (dsigma = 0.01); identical for calls and puts
vanna = -np.exp(-Q * T) * norm_pdf(d1) * d2 / SIG * 0.01

fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.9), sharey=True)
for ax, Z, name, unit in (
        (axes[0], charm, "charm", "delta drift per day"),
        (axes[1], vanna, "vanna", "delta shift per +1 vol pt")):
    lo, hi = np.percentile(Z, 2), np.percentile(Z, 98)
    lim = max(abs(lo), abs(hi))
    pm = ax.pcolormesh(mny, dte, np.clip(Z, -lim, lim), cmap=CMAP,
                       norm=TwoSlopeNorm(vcenter=0.0, vmin=-lim, vmax=lim),
                       shading="auto", rasterized=True)
    cs = ax.contour(mny, dte, Z, levels=[0.0], colors="#17120e", linewidths=1.2)
    ax.axvline(1.0, color="#666", lw=0.8, ls=":")
    ax.set_xlabel("moneyness K / S")
    ax.set_title(f"{name}  ({unit})", fontsize=10)
    cb = fig.colorbar(pm, ax=ax, shrink=0.9, pad=0.02)
    cb.ax.tick_params(labelsize=7)
axes[0].set_ylabel("days to expiry")
axes[0].annotate("ITM deltas\ngrow to 1", xy=(0.925, 20), fontsize=8,
                 color="#5c1520", ha="center")
axes[0].annotate("OTM deltas\ndecay to 0", xy=(1.075, 20), fontsize=8,
                 color="#1e4266", ha="center")
axes[1].annotate("ITM: vanna < 0", xy=(0.925, 20), fontsize=8,
                 color="#1e4266", ha="center")
axes[1].annotate("OTM: vanna > 0", xy=(1.075, 20), fontsize=8,
                 color="#5c1520", ha="center")
fig.suptitle("BSM charm and vanna for a call: sign flips at the zero contour "
             "near d2 = 0, magnitude explodes into expiry", fontsize=10.2, y=1.0)
fig.text(0.5, -0.03,
         f"BSM, sigma={SIG}, r={R}, q={Q}; values clipped at the 2nd/98th "
         f"percentile; put maps are visually identical (difference O(q)).",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_charm_vanna_maps.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
i = np.argmin(np.abs(dte - 1.0))
j_itm = np.argmin(np.abs(mny - 0.99))
j_otm = np.argmin(np.abs(mny - 1.01))
i30 = np.argmin(np.abs(dte - 30.0))
print(f"charm/day at 1 DTE, K/S=0.99: {charm[i, j_itm]:+.3f}  K/S=1.01: {charm[i, j_otm]:+.3f}")
print(f"charm/day at 30 DTE, K/S=0.99: {charm[i30, j_itm]:+.4f}  K/S=1.01: {charm[i30, j_otm]:+.4f}")
print(f"vanna/volpt at 1 DTE, K/S=0.99: {vanna[i, j_itm]:+.4f}  K/S=1.01: {vanna[i, j_otm]:+.4f}")
print(f"vanna/volpt at 30 DTE, K/S=0.99: {vanna[i30, j_itm]:+.4f}  K/S=1.01: {vanna[i30, j_otm]:+.4f}")
