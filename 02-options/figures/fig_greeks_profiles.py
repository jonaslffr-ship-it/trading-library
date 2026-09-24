"""
Figure 1 - First-order greek profiles across moneyness at three maturities.

Didactic Black-Scholes-Merton computation, no market data needed: call delta,
gamma, per-day theta and per-point vega are plotted against moneyness S/K for
a fixed strike K = 100, sigma = 20%, r = 4%, q = 0, at three maturities
(1 week, 1 month, 3 months). Everything is computed from scratch with
math.erf (no scipy).

Reproducible:
    python fig_greeks_profiles.py     # numpy, matplotlib, stdlib math
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


def ncdf(x):
    return 0.5 * (1.0 + np.vectorize(math.erf)(x / math.sqrt(2.0)))


def d1d2(S, K, T, r, sig):
    d1 = (np.log(S / K) + (r + 0.5 * sig ** 2) * T) / (sig * np.sqrt(T))
    return d1, d1 - sig * np.sqrt(T)


def call_delta(S, K, T, r, sig):
    d1, _ = d1d2(S, K, T, r, sig)
    return ncdf(d1)


def gamma(S, K, T, r, sig):
    d1, _ = d1d2(S, K, T, r, sig)
    return npdf(d1) / (S * sig * np.sqrt(T))


def call_theta_day(S, K, T, r, sig):
    d1, d2 = d1d2(S, K, T, r, sig)
    th_year = -S * npdf(d1) * sig / (2.0 * np.sqrt(T)) - r * K * np.exp(-r * T) * ncdf(d2)
    return th_year / 365.0


def vega_point(S, K, T, r, sig):
    d1, _ = d1d2(S, K, T, r, sig)
    return S * npdf(d1) * np.sqrt(T) / 100.0


K, SIG, R = 100.0, 0.20, 0.04
S = np.linspace(80.0, 120.0, 401)
mats = [(5 / 252, "1 week", "#7c1c2c"), (21 / 252, "1 month", "#2f6d4f"), (63 / 252, "3 months", "#17120e")]

fig, axes = plt.subplots(2, 2, figsize=(8.4, 6.2))
panels = [
    ("Call delta", call_delta, axes[0, 0]),
    ("Gamma", gamma, axes[0, 1]),
    ("Call theta (per calendar day)", call_theta_day, axes[1, 0]),
    ("Vega (per vol point)", vega_point, axes[1, 1]),
]
for name, fn, ax in panels:
    for T, lab, col in mats:
        ax.plot(S / K, fn(S, K, T, R, SIG), color=col, lw=1.7, label=lab)
    ax.axvline(1.0, color="#999", lw=0.7, ls=":")
    ax.set_title(name, fontsize=9.8)
    ax.set_xlabel("moneyness S/K", fontsize=8.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, alpha=0.22)
    ax.tick_params(labelsize=8)
axes[0, 0].legend(fontsize=8, frameon=False, loc="upper left")
fig.suptitle("BSM first-order greeks across moneyness: shorter maturity sharpens everything around ATM",
             fontsize=10.6, y=0.995)
fig.text(0.5, -0.015,
         "Black-Scholes-Merton, K=100, sigma=20%, r=4%, q=0; maturities 5, 21, 63 trading days (/252). "
         "Didactic model computation, no market data.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_greeks_profiles.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# ATM numbers quoted in the text
S0 = np.array([100.0])
for T, lab, _ in mats:
    print(f"ATM {lab:8s}: delta={call_delta(S0, K, T, R, SIG)[0]:.3f} "
          f"gamma={gamma(S0, K, T, R, SIG)[0]:.4f} "
          f"theta/day={call_theta_day(S0, K, T, R, SIG)[0]:.3f} "
          f"vega/pt={vega_point(S0, K, T, R, SIG)[0]:.3f}")
# extra numbers for the text: 10%-OTM call delta at 1w vs 3m
for T, lab, _ in mats:
    print(f"S=90 (10% OTM) {lab:8s}: delta={call_delta(np.array([90.0]), K, T, R, SIG)[0]:.4f} "
          f"gamma={gamma(np.array([90.0]), K, T, R, SIG)[0]:.5f}")
