"""
Figure 5 - The two risk mountains: gamma and vega across strike and maturity.

Didactic Black-Scholes-Merton surfaces, no market data: gamma and per-point
vega for a fixed spot S = 100 across strikes 80-120 and maturities from one
week to one year (sigma = 20%, r = 4%, q = 0). The point the two shapes make
together: gamma piles up at the money and EXPLODES as expiry approaches, vega
peaks at the money but GROWS with maturity - short-dated books are gamma
books, long-dated books are vega books.

Reproducible:
    python fig_greeks_surface.py     # numpy, matplotlib, stdlib math
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


S0, SIG, R = 100.0, 0.20, 0.04
strikes = np.linspace(80, 120, 121)
mats = np.linspace(5 / 252, 1.0, 120)          # 1 week .. 1 year
Kg, Tg = np.meshgrid(strikes, mats)

d1 = (np.log(S0 / Kg) + (R + 0.5 * SIG ** 2) * Tg) / (SIG * np.sqrt(Tg))
gamma = npdf(d1) / (S0 * SIG * np.sqrt(Tg))
vega = S0 * npdf(d1) * np.sqrt(Tg) / 100.0

fig = plt.figure(figsize=(8.8, 4.1))
for k, (Z, name, zl) in enumerate([
    (gamma, "Gamma", "gamma"),
    (vega, "Vega (per vol point)", "vega / pt"),
]):
    ax = fig.add_subplot(1, 2, k + 1, projection="3d")
    ax.plot_surface(Kg, Tg * 12, Z, cmap="cividis", linewidth=0, antialiased=True,
                    rstride=2, cstride=2)
    ax.set_xlabel("strike", fontsize=8, labelpad=1)
    ax.set_ylabel("maturity (months)", fontsize=8, labelpad=1)
    ax.set_zlabel(zl, fontsize=8, labelpad=1)
    ax.set_title(name, fontsize=10)
    ax.tick_params(labelsize=7, pad=0)
    ax.view_init(elev=24, azim=-58)
fig.suptitle("Gamma concentrates at the money and near expiry; vega sits at the money and grows with maturity",
             fontsize=10.2, y=0.99)
fig.text(0.5, 0.015,
         "Black-Scholes-Merton, S=100, sigma=20%, r=4%, q=0; strikes 80-120, maturities 1 week to 1 year. "
         "Didactic model computation, no market data.",
         ha="center", fontsize=7.5, color="#666")
plt.tight_layout(rect=(0, 0.04, 1, 0.97))
OUT = os.path.join(HERE, "fig_greeks_surface.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# numbers quoted in the text: ATM gamma & vega at 1w / 1m / 6m / 12m


def atm(T):
    d1_ = (math.log(1.0) + (R + 0.5 * SIG ** 2) * T) / (SIG * math.sqrt(T))
    ph = math.exp(-0.5 * d1_ ** 2) / SQRT2PI
    return ph / (S0 * SIG * math.sqrt(T)), S0 * ph * math.sqrt(T) / 100.0


for T, lab in [(5 / 252, "1w"), (21 / 252, "1m"), (0.5, "6m"), (1.0, "12m")]:
    g, v = atm(T)
    print(f"ATM {lab:3s}: gamma={g:.4f} vega/pt={v:.4f}")
