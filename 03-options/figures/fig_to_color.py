"""
Figure 2 - Color across moneyness into expiry.

Didactic Black-Scholes-Merton computation, no market data: color (dGamma/dt,
the change in gamma as one calendar day passes) for a European call across
moneyness S/K at three short maturities (1 week, 2 weeks, 1 month). K = 100,
sigma = 20%, r = 4%, q = 0. At the money color is positive and grows sharply
as expiry approaches - gamma is building into expiry, so a hedged book's
gamma drifts up overnight even with the spot pinned - while just off the
money color turns negative as the gamma peak narrows. This is the overnight
gamma drift of a delta-hedged book.

Sign convention: color is quoted as dGamma/dt (calendar time passing, so
time-to-maturity T shrinks). Haug's tabulated formula is written as dGamma/dT
and carries the opposite sign; color as time passes is -(Haug)/365 per day.
Cross-checked against a finite difference of gamma in fig_to_worked_examples.py.

Reproducible:
    python fig_to_color.py     # numpy, matplotlib, stdlib math
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


def color_perday(S, K, T, r, sig, q=0.0):
    """dGamma/dt per calendar day, positive as gamma builds into expiry."""
    sqrtT = np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sig ** 2) * T) / (sig * sqrtT)
    d2 = d1 - sig * sqrtT
    # Haug dGamma/dT (per year); color as time passes = -(Haug)/365
    haug = -np.exp(-q * T) * npdf(d1) / (2.0 * S * T * sig * sqrtT) * (
        2.0 * q * T + 1.0
        + (2.0 * (r - q) * T - d2 * sig * sqrtT) / (sig * sqrtT) * d1
    )
    return -haug / 365.0


K, SIG, R = 100.0, 0.20, 0.04
S = np.linspace(85.0, 115.0, 601)
mats = [(5 / 252, "1 week", "#7c1c2c"), (10 / 252, "2 weeks", "#c06a2c"),
        (21 / 252, "1 month", "#2f6d4f")]

fig, ax = plt.subplots(figsize=(7.6, 4.4))
for T, lab, col in mats:
    ax.plot(S / K, color_perday(S, K, T, R, SIG), color=col, lw=1.8, label=lab)
ax.axhline(0.0, color="#555", lw=0.8)
ax.axvline(1.0, color="#999", lw=0.7, ls=":")
ax.set_title("Color (dGamma/dt): at the money gamma builds into expiry; just off it, gamma decays",
             fontsize=9.6)
ax.set_xlabel("moneyness S/K", fontsize=9)
ax.set_ylabel("color  (change in gamma per calendar day)", fontsize=9)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, alpha=0.22)
ax.tick_params(labelsize=8.4)
ax.legend(fontsize=8.4, frameon=False, loc="upper right")
fig.text(0.5, -0.02,
         "Black-Scholes-Merton, K=100, sigma=20%, r=4%, q=0; maturities 5, 10, 21 trading days (/252). "
         "Color = dGamma/dt as time passes. Didactic model computation, no market data.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_to_color.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# numbers quoted in the text
for T, lab, _ in mats:
    c = color_perday(np.array([100.0]), K, T, R, SIG)[0]
    c95 = color_perday(np.array([95.0]), K, T, R, SIG)[0]
    c105 = color_perday(np.array([105.0]), K, T, R, SIG)[0]
    print(f"{lab:8s}: color/day ATM={c:+.6f}  S/K=0.95={c95:+.6f}  S/K=1.05={c105:+.6f}")
for T, lab, _ in mats:
    c = color_perday(S, K, T, R, SIG)
    idx = np.where(np.sign(c[:-1]) != np.sign(c[1:]))[0]
    xs = [f"{(S/K)[i]:.3f}" for i in idx]
    print(f"{lab:8s}: color sign change(s) at S/K = {', '.join(xs) if xs else 'none in range'}")
