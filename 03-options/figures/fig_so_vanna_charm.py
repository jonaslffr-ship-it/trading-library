"""
Figure 2 - Sign maps of the two delta-drift greeks: vanna and charm.

Didactic Black-Scholes-Merton heatmaps, no market data. Left: call vanna
(change in delta per +1 vol point of implied vol). Right: call charm (change
in delta per one calendar day passing). Both are drawn across moneyness S/K
(0.85-1.15) and days to expiry (2-90) with a diverging colormap centered at
zero, so the SIGN structure - which side of the strike forces tomorrow's buy
or sell - is the visible object. K = 100, sigma = 20%, r = 4%, q = 0.

Closed forms (q = 0):
    vanna = -phi(d1) * d2 / sigma / 100                    (per +1 vol point)
    charm = -phi(d1) * (2 r T - d2 sigma sqrt(T))
            / (2 T sigma sqrt(T)) / 365                     (per calendar day)

A central finite-difference self-check of vanna and charm against dDelta/dsigma
and dDelta/dt is printed to stdout.

Reproducible:
    python fig_so_vanna_charm.py     # numpy, matplotlib, stdlib math
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


def ncdf_s(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


K, SIG, R = 100.0, 0.20, 0.04
mny = np.linspace(0.85, 1.15, 241)            # S/K
days = np.linspace(2, 90, 240)                # days to expiry
M, D = np.meshgrid(mny, days)
S = M * K
T = D / 365.0

d1 = (np.log(S / K) + (R + 0.5 * SIG ** 2) * T) / (SIG * np.sqrt(T))
d2 = d1 - SIG * np.sqrt(T)
vanna = -npdf(d1) * d2 / SIG / 100.0                                                   # per vol point
charm = -npdf(d1) * (2 * R * T - d2 * SIG * np.sqrt(T)) / (2 * T * SIG * np.sqrt(T)) / 365.0  # per day

fig, axes = plt.subplots(1, 2, figsize=(8.8, 4.0), sharey=True)
for ax, Z, name, unit in [
    (axes[0], vanna, "Call vanna", "delta change per +1 vol point"),
    (axes[1], charm, "Call charm", "delta change per calendar day"),
]:
    lim = np.percentile(np.abs(Z), 99)
    pc = ax.pcolormesh(mny, days, Z, cmap="RdBu_r", vmin=-lim, vmax=lim,
                       shading="auto", rasterized=True)
    ax.contour(mny, days, Z, levels=[0.0], colors="#17120e", linewidths=1.1)
    ax.axvline(1.0, color="#555", lw=0.7, ls=":")
    ax.set_title(f"{name} ({unit})", fontsize=9.6)
    ax.set_xlabel("moneyness S/K", fontsize=9)
    cb = fig.colorbar(pc, ax=ax, shrink=0.92)
    cb.ax.tick_params(labelsize=7.5)
    ax.tick_params(labelsize=8.2)
axes[0].set_ylabel("days to expiry", fontsize=9)
fig.suptitle("Where tomorrow's forced delta adjustments come from: vanna and charm sign maps",
             fontsize=10.4, y=1.00)
fig.text(0.5, -0.03,
         "Black-Scholes-Merton, K=100, sigma=20%, r=4%, q=0. Solid line = zero contour; "
         "red = positive, blue = negative. Didactic model computation, no market data.",
         ha="center", fontsize=7.5, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_so_vanna_charm.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)


# --- numbers quoted in the text --------------------------------------------
def at(mny_v, d_v, Z):
    i = np.argmin(np.abs(days - d_v)); j = np.argmin(np.abs(mny - mny_v))
    return Z[i, j]


print("\n[vanna & charm at 30 days]")
for m in (0.95, 1.00, 1.05):
    print(f"  S/K={m:.2f}: vanna/pt={at(m, 30, vanna):+.5f}  charm/day={at(m, 30, charm):+.5f}")
print("[vanna & charm at 7 days]")
for m in (0.95, 1.05):
    print(f"  S/K={m:.2f}: vanna/pt={at(m, 7, vanna):+.5f}  charm/day={at(m, 7, charm):+.5f}")
c30 = at(0.95, 30, charm); c7 = at(0.95, 7, charm)
print(f"  OTM charm growth 30d->7d: {c30:+.5f} -> {c7:+.5f}  ({abs(c7 / c30):.1f}x)")
print("[charm growth into expiry, S/K=0.97]")
cvals = [(d, at(0.97, d, charm)) for d in (30, 14, 7, 3)]
for d, c in cvals:
    print(f"  {d:2d}d: charm/day={c:+.5f}")
print(f"  30d -> 3d magnitude ratio: {abs(cvals[-1][1] / cvals[0][1]):.1f}x")


# --- finite-difference self-check (natural units) --------------------------
def delta_s(S, K, T, r, sig):
    d1 = (math.log(S / K) + (r + 0.5 * sig ** 2) * T) / (sig * math.sqrt(T))
    return ncdf_s(d1)


def vanna_cf(S, K, T, r, sig):                # per unit vol
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sig ** 2) * T) / (sig * sqrtT)
    d2 = d1 - sig * sqrtT
    return -math.exp(-0.5 * d1 * d1) / SQRT2PI * d2 / sig


def charm_cf(S, K, T, r, sig):                # per year
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sig ** 2) * T) / (sig * sqrtT)
    d2 = d1 - sig * sqrtT
    return -math.exp(-0.5 * d1 * d1) / SQRT2PI * (2 * R * T - d2 * sig * sqrtT) / (2 * T * sig * sqrtT)


hV, hT = 1e-4, 1e-5
e_vanna = e_charm = 0.0
for m in (0.90, 0.95, 1.05, 1.10):
    for Td in (30 / 365, 90 / 365):
        Sx, r, sig = m * 100.0, R, SIG
        cf = vanna_cf(Sx, K, Td, r, sig)
        fd = (delta_s(Sx, K, Td, r, sig + hV) - delta_s(Sx, K, Td, r, sig - hV)) / (2 * hV)
        e_vanna = max(e_vanna, abs(fd - cf) / abs(cf))
        cf = charm_cf(Sx, K, Td, r, sig)
        fd = -(delta_s(Sx, K, Td + hT, r, sig) - delta_s(Sx, K, Td - hT, r, sig)) / (2 * hT)
        e_charm = max(e_charm, abs(fd - cf) / abs(cf))
print("\n[self-check: max relative error vs central finite difference]")
print(f"  vanna  {e_vanna:.2e}")
print(f"  charm  {e_charm:.2e}")
print(f"  OVERALL max rel err = {max(e_vanna, e_charm):.2e}")
