"""
Figure 3 - Option elasticity (lambda) across moneyness for a 1-month call.

Didactic Black-Scholes-Merton computation, no market data: lambda, the option's
elasticity, Lambda = delta * S / price, is plotted against moneyness S/K for a
1-month European call (K = 100, sigma = 20%, r = 4%, q = 0). Lambda is the
percentage change in the option's value per one-percent change in the
underlying - the built-in leverage. It is smallest deep in the money (where the
option behaves almost like the stock, lambda -> 1) and rises without bound
toward the out-of-the-money wing, where a cheap option controls a large
share-equivalent exposure. Delta is drawn on a twin axis to show that the
leverage spike happens exactly where delta is collapsing but price is
collapsing faster.

Reproducible:
    python fig_fo_leverage.py     # numpy, matplotlib, stdlib math
"""
import os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SQRT2PI = math.sqrt(2.0 * math.pi)


def npdf(x):
    return math.exp(-0.5 * x * x) / SQRT2PI


def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bsm_greeks(S, K, T, r, sigma, q=0.0, call=True):
    """Verified BSM price, delta and elasticity lambda = delta * S / price."""
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    dq, dr = math.exp(-q * T), math.exp(-r * T)
    s = 1.0 if call else -1.0
    price = s * (S * dq * ncdf(s * d1) - K * dr * ncdf(s * d2))
    delta = s * dq * ncdf(s * d1)
    lam = delta * S / price if price != 0.0 else float("nan")
    return dict(price=price, delta=delta, lam=lam)


K, SIG, R, T = 100.0, 0.20, 0.04, 21 / 252.0
S = np.linspace(85.0, 115.0, 601)
lam = np.array([bsm_greeks(s, K, T, R, SIG)["lam"] for s in S])
delta = np.array([bsm_greeks(s, K, T, R, SIG)["delta"] for s in S])

fig, ax = plt.subplots(figsize=(7.6, 4.4))
ax.plot(S / K, lam, color="#7c1c2c", lw=2.0, label="elasticity  $\\Lambda = \\Delta\\,S/V$")
ax.axvline(1.0, color="#999", lw=0.7, ls=":")
ax.axhline(1.0, color="#bbb", lw=0.7, ls="--")
ax.set_xlabel("moneyness S/K", fontsize=9.4)
ax.set_ylabel("elasticity  $\\Lambda$  (leverage)", fontsize=9.4, color="#7c1c2c")
ax.tick_params(axis="y", labelcolor="#7c1c2c", labelsize=8.4)
ax.tick_params(axis="x", labelsize=8.4)
ax.set_ylim(0, max(lam) * 1.05)
for sp in ("top",):
    ax.spines[sp].set_visible(False)
ax.grid(True, alpha=0.22)

ax2 = ax.twinx()
ax2.plot(S / K, delta, color="#2f6d4f", lw=1.4, ls="-.", label="call delta (right axis)")
ax2.set_ylabel("call delta", fontsize=9.4, color="#2f6d4f")
ax2.tick_params(axis="y", labelcolor="#2f6d4f", labelsize=8.4)
ax2.set_ylim(0, 1.05)
ax2.spines["top"].set_visible(False)

lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, fontsize=8, frameon=False, loc="upper right")

fig.suptitle("Elasticity is the option's built-in leverage: highest far out of the money",
             fontsize=10.4, y=0.98)
fig.text(0.5, -0.02,
         "Black-Scholes-Merton, 1-month call, K=100, sigma=20%, r=4%, q=0. "
         "Lambda = delta*S/price. Didactic model computation, no market data.",
         ha="center", fontsize=7.5, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_fo_leverage.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# ---------------------------------------------------------------- printed numbers
for m in (0.90, 0.95, 1.00, 1.05, 1.10):
    g = bsm_greeks(m * K, K, T, R, SIG)
    print(f"1-month S/K={m:.2f}: price={g['price']:.3f} delta={g['delta']:.4f} lambda={g['lam']:.2f}")
# a deep-OTM anchor for the "far-OTM leverage" sentence
g = bsm_greeks(0.90 * K, K, T, R, SIG)
print(f"far-OTM check S/K=0.90: 1% underlying move ~= {g['lam']:.1f}% option move")
