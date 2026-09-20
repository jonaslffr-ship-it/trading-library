"""
Figure 3 - Zomma and ultima across moneyness at a few vols.

Didactic Black-Scholes-Merton computation, no market data. Two panels for a
European call, K = 100, r = 4%, q = 0, one-month maturity (T = 21/252),
plotted across moneyness S/K at three implied-vol levels (15%, 20%, 30%):

  left  - zomma (dGamma/dsigma, per vol point): how gamma reacts to implied
          vol. Negative near the money (a vol rise flattens the gamma peak)
          and positive out in the wings, so gamma-vs-vol sensitivity lives on
          the shoulders of the strike.
  right - ultima (dVomma/dsigma = d3V/dsigma3, per unit vol): third-order vol
          convexity. Near zero at the money, large and negative just off it,
          i.e. the vol-of-vol sensitivity lives in the wings, exactly where a
          vega book carries its convexity.

Closed forms (cross-checked against finite differences of gamma and vomma in
fig_to_worked_examples.py):
    zomma  = dGamma/dsigma = gamma * (d1 d2 - 1) / sigma
    ultima = dVomma/dsigma = (-vega/sigma^2) * (d1 d2 (1 - d1 d2) + d1^2 + d2^2)

Reproducible:
    python fig_to_zomma_ultima.py     # numpy, matplotlib, stdlib math
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


def zomma_ultima(S, K, T, r, sig, q=0.0):
    sqrtT = np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sig ** 2) * T) / (sig * sqrtT)
    d2 = d1 - sig * sqrtT
    gamma = np.exp(-q * T) * npdf(d1) / (S * sig * sqrtT)
    vega = S * np.exp(-q * T) * npdf(d1) * sqrtT          # per unit vol
    zomma_pt = gamma * (d1 * d2 - 1.0) / sig / 100.0        # per vol point
    ultima = (-vega / sig ** 2) * (d1 * d2 * (1.0 - d1 * d2) + d1 * d1 + d2 * d2)
    return zomma_pt, ultima


K, R, T = 100.0, 0.04, 21.0 / 252.0
S = np.linspace(85.0, 115.0, 601)
vols = [(0.15, "sigma 15%", "#7c1c2c"), (0.20, "sigma 20%", "#2f6d4f"),
        (0.30, "sigma 30%", "#17120e")]

fig, axes = plt.subplots(1, 2, figsize=(8.8, 4.1))
for sig, lab, col in vols:
    z, u = zomma_ultima(S, K, T, R, sig)
    axes[0].plot(S / K, z, color=col, lw=1.7, label=lab)
    axes[1].plot(S / K, u, color=col, lw=1.7, label=lab)
titles = ["Zomma (dGamma/dsigma, per vol point)", "Ultima (dVomma/dsigma, per unit vol)"]
ylabs = ["zomma  (change in gamma per vol point)", "ultima  (change in vomma per unit vol)"]
for ax, ttl, yl in zip(axes, titles, ylabs):
    ax.axhline(0.0, color="#555", lw=0.8)
    ax.axvline(1.0, color="#999", lw=0.7, ls=":")
    ax.set_title(ttl, fontsize=9.4)
    ax.set_xlabel("moneyness S/K", fontsize=9)
    ax.set_ylabel(yl, fontsize=8.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, alpha=0.22)
    ax.tick_params(labelsize=8.2)
axes[0].legend(fontsize=8.2, frameon=False, loc="lower right")
fig.suptitle("Where gamma-vs-vol (zomma) and vomma-vs-vol (ultima) sensitivities live: near-the-money vs the wings",
             fontsize=10.0, y=1.0)
fig.text(0.5, -0.03,
         "Black-Scholes-Merton, K=100, r=4%, q=0, one-month maturity (21/252), vols 15/20/30%. "
         "Didactic model computation, no market data.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_to_zomma_ultima.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# numbers quoted in the text
for sig, lab, _ in vols:
    z, u = zomma_ultima(np.array([100.0]), K, T, R, sig)
    z95, u95 = zomma_ultima(np.array([95.0]), K, T, R, sig)
    z105, u105 = zomma_ultima(np.array([105.0]), K, T, R, sig)
    print(f"{lab:10s}: zomma/pt ATM={z[0]:+.6f} S/K=0.95={z95[0]:+.6f} S/K=1.05={z105[0]:+.6f} | "
          f"ultima ATM={u[0]:+.3f} S/K=0.95={u95[0]:+.3f} S/K=1.05={u105[0]:+.3f}")
