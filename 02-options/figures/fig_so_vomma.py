"""
Figure 3 - Vomma (volga) across moneyness at several volatilities.

Didactic Black-Scholes-Merton computation, no market data: vomma - the
convexity of the option in volatility, vega * d1 * d2 / sigma - plotted across
moneyness S/K at three implied vols (15%, 20%, 30%) for a fixed 60-day option.
Vomma is near zero at the money (where vega peaks and is locally flat in vol)
and rises to a peak in each wing. K = 100, r = 4%, q = 0. Units: change in
per-point vega per +1 vol point (i.e. vega * d1 d2 / sigma / 10000).

A central finite-difference self-check of vomma and veta against dVega/dsigma
and dVega/dt is printed to stdout.

Reproducible:
    python fig_so_vomma.py     # numpy, matplotlib, stdlib math
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


K, R, Q = 100.0, 0.04, 0.0
TDAYS = 60.0
T = TDAYS / 365.0
S = np.linspace(75.0, 125.0, 501)
vols = [(0.15, "sigma = 15%", "#7c1c2c"), (0.20, "sigma = 20%", "#2f6d4f"),
        (0.30, "sigma = 30%", "#17120e")]


def vomma_grid(S, K, T, r, sig):
    d1 = (np.log(S / K) + (r + 0.5 * sig ** 2) * T) / (sig * np.sqrt(T))
    d2 = d1 - sig * np.sqrt(T)
    vega = S * npdf(d1) * np.sqrt(T) / 100.0          # per vol point
    return vega * d1 * d2 / sig / 100.0               # change in per-point vega per +1 vol point


fig, ax = plt.subplots(figsize=(7.2, 4.4))
for sig, lab, col in vols:
    ax.plot(S / K, vomma_grid(S, K, T, R, sig), color=col, lw=1.8, label=lab)
ax.axvline(1.0, color="#999", lw=0.7, ls=":")
ax.axhline(0.0, color="#999", lw=0.7, ls=":")
ax.set_title("Vomma is near zero at the money and peaks in the wings", fontsize=10.2)
ax.set_xlabel("moneyness S/K", fontsize=9.2)
ax.set_ylabel("vomma (per-point vega change per +1 vol point)", fontsize=9.2)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.grid(True, alpha=0.22)
ax.tick_params(labelsize=8.4)
ax.legend(fontsize=8.6, frameon=False, loc="upper center")
fig.text(0.5, -0.02,
         "Black-Scholes-Merton, K=100, r=4%, q=0, 60 days to expiry. "
         "Didactic model computation, no market data.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_so_vomma.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)


# --- numbers quoted in the text --------------------------------------------
def vomma_at(mny_v, sig):
    j = np.argmin(np.abs(S / K - mny_v))
    return vomma_grid(S, K, T, R, sig)[j]


print("\n[vomma at 60 days, per-point vega change per +1 vol point]")
for sig, lab, _ in vols:
    print(f"  {lab}: ATM={vomma_at(1.00, sig):+.5f}  "
          f"S/K=0.90={vomma_at(0.90, sig):+.5f}  S/K=1.10={vomma_at(1.10, sig):+.5f}")
# location of the peak in the right wing at sigma=20%
v20 = vomma_grid(S, K, T, R, 0.20)
jpk = np.argmax(v20)
print(f"  sigma=20% right-wing peak at S/K={S[jpk]/K:.3f}, vomma={v20[jpk]:+.5f}")


# --- finite-difference self-check (natural units) --------------------------
def vega_nat(S, K, T, r, sig):                 # per unit vol
    d1 = (math.log(S / K) + (r + 0.5 * sig ** 2) * T) / (sig * math.sqrt(T))
    return S * (math.exp(-0.5 * d1 * d1) / SQRT2PI) * math.sqrt(T)


def vomma_cf(S, K, T, r, sig):                 # per unit vol (dVega_nat/dsigma)
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sig ** 2) * T) / (sig * sqrtT)
    d2 = d1 - sig * sqrtT
    return vega_nat(S, K, T, r, sig) * d1 * d2 / sig


def veta_cf(S, K, T, r, sig):                  # per year, per unit vol (dVega_nat/dt)
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sig ** 2) * T) / (sig * sqrtT)
    d2 = d1 - sig * sqrtT
    # no leading minus: d(vega)/dt (calendar), matching the theta/charm sign
    # convention and the central finite difference below.
    return S * (math.exp(-0.5 * d1 * d1) / SQRT2PI) * sqrtT * (
        R * d1 / (sig * sqrtT) - (1 + d1 * d2) / (2 * T))     # q = 0


hV, hT = 1e-4, 1e-5
e_vomma = e_veta = 0.0
for m in (0.90, 0.95, 1.05, 1.10):
    for Td in (30 / 365, 90 / 365):
        Sx, sig = m * 100.0, 0.20
        cf = vomma_cf(Sx, K, Td, R, sig)
        fd = (vega_nat(Sx, K, Td, R, sig + hV) - vega_nat(Sx, K, Td, R, sig - hV)) / (2 * hV)
        e_vomma = max(e_vomma, abs(fd - cf) / abs(cf))
        cf = veta_cf(Sx, K, Td, R, sig)
        fd = -(vega_nat(Sx, K, Td + hT, R, sig) - vega_nat(Sx, K, Td - hT, R, sig)) / (2 * hT)
        e_veta = max(e_veta, abs(fd - cf) / abs(cf))
print("\n[self-check: max relative error vs central finite difference]")
print(f"  vomma  {e_vomma:.2e}")
print(f"  veta   {e_veta:.2e}")
print(f"  OVERALL max rel err = {max(e_vomma, e_veta):.2e}")
