"""
Figure 2 - Maturity dependence of ATM vega and ATM rho (term structure).

Didactic Black-Scholes-Merton computation, no market data: at-the-money vega
(per vol point) and at-the-money rho (per 1% rate) are plotted as functions of
time to expiry, from 1 week to 2 years, for a call with S = K = 100,
sigma = 20%, r = 4%, q = 0. Both grow with maturity; vega tracks the square
root of time closely, rho grows a little faster than linearly. A dashed
reference curve proportional to sqrt(T), anchored at the 1-year vega, makes the
sqrt(T) growth of vega visible.

Reproducible:
    python fig_fo_term_structure.py     # numpy, matplotlib, stdlib math
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
    """Verified BSM greeks. vega per vol POINT; rho per 1% rate."""
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    dq, dr = math.exp(-q * T), math.exp(-r * T)
    s = 1.0 if call else -1.0
    vega = S * dq * npdf(d1) * sqrtT / 100.0
    rho = s * K * T * dr * ncdf(s * d2) / 100.0
    return dict(vega=vega, rho=rho)


K, SIG, R = 100.0, 0.20, 0.04
T = np.linspace(1 / 52.0, 2.0, 400)
vega = np.array([bsm_greeks(100.0, K, t, R, SIG)["vega"] for t in T])
rho = np.array([bsm_greeks(100.0, K, t, R, SIG)["rho"] for t in T])

# sqrt(T) reference for vega, anchored at T = 1 year
vega_1y = bsm_greeks(100.0, K, 1.0, R, SIG)["vega"]
sqrt_ref = vega_1y * np.sqrt(T / 1.0)

fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.9))

ax = axes[0]
ax.plot(T, vega, color="#2f6d4f", lw=1.9, label="ATM vega")
ax.plot(T, sqrt_ref, color="#999", lw=1.2, ls="--", label=r"$\propto\sqrt{T}$ (anchored at 1y)")
ax.set_title("ATM vega grows like the square root of time", fontsize=9.8)
ax.set_xlabel("time to expiry (years)", fontsize=9)
ax.set_ylabel("vega (per vol point)", fontsize=9)
ax.legend(fontsize=8, frameon=False, loc="upper left")

ax = axes[1]
ax.plot(T, rho, color="#7c1c2c", lw=1.9, label="ATM rho")
ax.set_title("ATM rho grows with maturity", fontsize=9.8)
ax.set_xlabel("time to expiry (years)", fontsize=9)
ax.set_ylabel("rho (per 1% rate)", fontsize=9)
ax.legend(fontsize=8, frameon=False, loc="upper left")

for ax in axes:
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(True, alpha=0.22)
    ax.tick_params(labelsize=8.2)
    ax.set_xlim(0, 2.0)

fig.suptitle("Vega and rho are the maturity greeks: both scale up with time to expiry",
             fontsize=10.4, y=1.00)
fig.text(0.5, -0.03,
         "Black-Scholes-Merton, ATM call S=K=100, sigma=20%, r=4%, q=0. "
         "Didactic model computation, no market data.",
         ha="center", fontsize=7.5, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_fo_term_structure.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# ---------------------------------------------------------------- printed numbers
labels = [(1 / 52.0, "1 week"), (1 / 12.0, "1 month"), (0.25, "3 months"),
          (0.5, "6 months"), (1.0, "1 year"), (2.0, "2 years")]
for t, lab in labels:
    g = bsm_greeks(100.0, K, t, R, SIG)
    print(f"ATM {lab:9s} (T={t:.4f}): vega/pt={g['vega']:.3f} rho/1%={g['rho']:.3f}")
# sqrt(T) sanity: vega(1y)/vega(1w) vs sqrt(52)
v1w = bsm_greeks(100.0, K, 1 / 52.0, R, SIG)["vega"]
v1y = bsm_greeks(100.0, K, 1.0, R, SIG)["vega"]
print(f"vega ratio 1y/1w = {v1y / v1w:.2f}  (sqrt(52) = {math.sqrt(52.0):.2f})")
