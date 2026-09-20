"""
Figure 1 - Speed across moneyness at three maturities.

Didactic Black-Scholes-Merton computation, no market data: speed (the third
derivative of value in spot, dGamma/dS) for a European call across moneyness
S/K at three maturities (1 week, 1 month, 3 months). K = 100, sigma = 20%,
r = 4%, q = 0. Speed changes sign across the strike - gamma is rising on one
side of the money and falling on the other - and its amplitude blows up as
expiry approaches, which is why a large move leaves a near-expiry gamma
estimate stale.

Closed form (cross-checked against a finite difference of gamma in
fig_to_worked_examples.py):
    speed = dGamma/dS = -(gamma/S) * (d1/(sigma sqrt(T)) + 1)

Reproducible:
    python fig_to_speed.py     # numpy, matplotlib, stdlib math
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


def gamma_speed(S, K, T, r, sig, q=0.0):
    sqrtT = np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sig ** 2) * T) / (sig * sqrtT)
    gamma = np.exp(-q * T) * npdf(d1) / (S * sig * sqrtT)
    speed = -(gamma / S) * (d1 / (sig * sqrtT) + 1.0)
    return gamma, speed


K, SIG, R = 100.0, 0.20, 0.04
S = np.linspace(85.0, 115.0, 601)
mats = [(5 / 252, "1 week", "#7c1c2c"), (21 / 252, "1 month", "#2f6d4f"),
        (63 / 252, "3 months", "#17120e")]

fig, ax = plt.subplots(figsize=(7.6, 4.4))
for T, lab, col in mats:
    _, speed = gamma_speed(S, K, T, R, SIG)
    ax.plot(S / K, speed, color=col, lw=1.8, label=lab)
ax.axhline(0.0, color="#555", lw=0.8)
ax.axvline(1.0, color="#999", lw=0.7, ls=":")
ax.set_title("Speed (dGamma/dS): gamma's own slope in spot flips sign across the strike and sharpens near expiry",
             fontsize=9.6)
ax.set_xlabel("moneyness S/K", fontsize=9)
ax.set_ylabel("speed  (change in gamma per index point)", fontsize=9)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, alpha=0.22)
ax.tick_params(labelsize=8.4)
ax.legend(fontsize=8.4, frameon=False, loc="upper right")
fig.text(0.5, -0.02,
         "Black-Scholes-Merton, K=100, sigma=20%, r=4%, q=0; maturities 5, 21, 63 trading days (/252). "
         "Didactic model computation, no market data.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_to_speed.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# numbers quoted in the text
for T, lab, _ in mats:
    _, sp = gamma_speed(np.array([100.0]), K, T, R, SIG)
    _, sp95 = gamma_speed(np.array([95.0]), K, T, R, SIG)
    _, sp105 = gamma_speed(np.array([105.0]), K, T, R, SIG)
    print(f"{lab:9s}: speed ATM={sp[0]:+.5f}  S/K=0.95={sp95[0]:+.5f}  S/K=1.05={sp105[0]:+.5f}")
# location of the sign change (zero of speed) for the 1-month curve
for T, lab, _ in mats:
    _, sp = gamma_speed(S, K, T, R, SIG)
    idx = np.where(np.sign(sp[:-1]) != np.sign(sp[1:]))[0]
    xs = [f"{(S/K)[i]:.3f}" for i in idx]
    print(f"{lab:9s}: speed sign change(s) at S/K = {', '.join(xs) if xs else 'none in range'}; "
          f"peak |speed| = {np.max(np.abs(sp)):.5f}")
