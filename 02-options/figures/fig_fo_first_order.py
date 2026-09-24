"""
Figure 1 - First-order greek profiles across moneyness at three maturities.

Didactic Black-Scholes-Merton computation, no market data needed: call delta,
per-calendar-day theta, per-vol-point vega and per-1%-rate rho are plotted
against moneyness S/K for a fixed strike K = 100, sigma = 20%, r = 4%, q = 0,
at three maturities (1 week, 1 month, 3 months). Everything is computed from
the closed forms verified against a central finite difference of the BSM price
(bump S, t, sigma, r); the self-check prints the worst relative error to stdout.

Reproducible:
    python fig_fo_first_order.py     # numpy, matplotlib, stdlib math
"""
import os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SQRT2PI = math.sqrt(2.0 * math.pi)


def npdf(x):
    return math.exp(-0.5 * x * x) / SQRT2PI            # standard normal pdf


def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))  # standard normal cdf


def bsm_price(S, K, T, r, sigma, q=0.0, call=True):
    """Black-Scholes-Merton European price (scalar)."""
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    dq, dr = math.exp(-q * T), math.exp(-r * T)
    s = 1.0 if call else -1.0
    return s * (S * dq * ncdf(s * d1) - K * dr * ncdf(s * d2))


def bsm_greeks(S, K, T, r, sigma, q=0.0, call=True):
    """Verified BSM price and greeks (same closed forms as the greeks-and-hedging
    figures). vega per vol POINT; theta per CALENDAR DAY; rho per 1% rate."""
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    dq, dr = math.exp(-q * T), math.exp(-r * T)
    s = 1.0 if call else -1.0
    price = s * (S * dq * ncdf(s * d1) - K * dr * ncdf(s * d2))
    delta = s * dq * ncdf(s * d1)
    vega = S * dq * npdf(d1) * sqrtT / 100.0
    theta = (-S * dq * npdf(d1) * sigma / (2.0 * sqrtT)
             - s * r * K * dr * ncdf(s * d2)
             + s * q * S * dq * ncdf(s * d1)) / 365.0
    rho = s * K * T * dr * ncdf(s * d2) / 100.0
    dual_delta = -s * dr * ncdf(s * d2)                # call -Dr N(d2); put +Dr N(-d2)
    lam = delta * S / price if price != 0.0 else float("nan")
    return dict(price=price, delta=delta, vega=vega, theta=theta, rho=rho,
                dual_delta=dual_delta, lam=lam, d1=d1, d2=d2,
                Nd1=ncdf(d1), Nd2=ncdf(d2))


# ---------------------------------------------------------------- self-check
def self_check():
    """Central finite difference of the price vs the closed-form greeks."""
    worst = 0.0
    for S in (90.0, 100.0, 110.0):
        for T in (1 / 52.0, 1 / 12.0, 0.25):
            base = dict(S=S, K=100.0, T=T, r=0.04, sigma=0.20, q=0.0, call=True)
            g = bsm_greeks(**base)
            # delta = dV/dS
            h = 1e-3
            fd = (bsm_price(**{**base, "S": S + h}) - bsm_price(**{**base, "S": S - h})) / (2 * h)
            worst = max(worst, abs(fd - g["delta"]) / abs(g["delta"]))
            # vega per point = dV/dsigma / 100
            h = 1e-5
            fd = (bsm_price(**{**base, "sigma": 0.20 + h}) - bsm_price(**{**base, "sigma": 0.20 - h})) / (2 * h) / 100.0
            worst = max(worst, abs(fd - g["vega"]) / abs(g["vega"]))
            # rho per 1% = dV/dr / 100
            h = 1e-6
            fd = (bsm_price(**{**base, "r": 0.04 + h}) - bsm_price(**{**base, "r": 0.04 - h})) / (2 * h) / 100.0
            worst = max(worst, abs(fd - g["rho"]) / abs(g["rho"]))
            # theta per day = -(dV/dT) / 365
            h = 1e-6
            dVdT = (bsm_price(**{**base, "T": T + h}) - bsm_price(**{**base, "T": T - h})) / (2 * h)
            fd = -dVdT / 365.0
            worst = max(worst, abs(fd - g["theta"]) / abs(g["theta"]))
    print(f"self-check (central FD vs closed form, bump S/t/sigma/r): max rel err {worst:.2e}")
    return worst


# ---------------------------------------------------------------- figure
K, SIG, R = 100.0, 0.20, 0.04
S = np.linspace(80.0, 120.0, 401)
mats = [(5 / 252, "1 week", "#7c1c2c"), (21 / 252, "1 month", "#2f6d4f"), (63 / 252, "3 months", "#17120e")]

vg = np.vectorize(lambda s, T, key: bsm_greeks(s, K, T, R, SIG)[key])

fig, axes = plt.subplots(2, 2, figsize=(8.4, 6.2))
panels = [
    ("Call delta", "delta", axes[0, 0]),
    ("Call theta (per calendar day)", "theta", axes[0, 1]),
    ("Vega (per vol point)", "vega", axes[1, 0]),
    ("Call rho (per 1% rate)", "rho", axes[1, 1]),
]
for name, key, ax in panels:
    for T, lab, col in mats:
        ax.plot(S / K, vg(S, T, key), color=col, lw=1.7, label=lab)
    ax.axvline(1.0, color="#999", lw=0.7, ls=":")
    ax.set_title(name, fontsize=9.8)
    ax.set_xlabel("moneyness S/K", fontsize=8.6)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(True, alpha=0.22)
    ax.tick_params(labelsize=8)
axes[0, 0].legend(fontsize=8, frameon=False, loc="upper left")
fig.suptitle("BSM first-order greeks across moneyness: shorter maturity sharpens delta and theta around ATM",
             fontsize=10.4, y=0.995)
fig.text(0.5, -0.015,
         "Black-Scholes-Merton, K=100, sigma=20%, r=4%, q=0; maturities 5, 21, 63 trading days (/252). "
         "Didactic model computation, no market data.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_fo_first_order.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# ---------------------------------------------------------------- printed numbers
self_check()
for T, lab, _ in mats:
    g = bsm_greeks(100.0, K, T, R, SIG)
    print(f"ATM {lab:8s}: delta={g['delta']:.3f} theta/day={g['theta']:.3f} "
          f"vega/pt={g['vega']:.3f} rho/1%={g['rho']:.3f}")
# 10%-OTM call delta across maturities (the carry-and-time story)
for T, lab, _ in mats:
    g = bsm_greeks(90.0, K, T, R, SIG)
    print(f"S=90 (10% OTM) {lab:8s}: delta={g['delta']:.4f}")
# delta vs risk-neutral P(ITM) gap for the 1-month ATM call
g = bsm_greeks(100.0, K, 21 / 252, R, SIG)
print(f"1-month ATM: d1={g['d1']:.4f} d2={g['d2']:.4f} "
      f"N(d1)=delta={g['Nd1']:.4f} N(d2)=P(ITM,RN)={g['Nd2']:.4f} "
      f"gap={g['Nd1'] - g['Nd2']:.4f} dual_delta={g['dual_delta']:.4f}")
# gap on a 1-year 30% vol call (where the folklore breaks)
g = bsm_greeks(100.0, K, 1.0, R, 0.30)
print(f"1-year 30%vol ATM: N(d1)=delta={g['Nd1']:.4f} N(d2)={g['Nd2']:.4f} "
      f"gap={g['Nd1'] - g['Nd2']:.4f}")
