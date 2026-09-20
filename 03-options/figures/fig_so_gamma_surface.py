"""
Figure 1 - Gamma across strike, maturity and moneyness.

Didactic Black-Scholes-Merton computation, no market data. Left: gamma as a
surface over strike (80-120) and maturity (1 week to 1 year) for a fixed spot
S = 100. Right: gamma across moneyness S/K at three maturities (1 week, 1
month, 3 months). Both panels show the same two facts - gamma concentrates at
the money and spikes as expiry approaches. K/spot = 100, sigma = 20%, r = 4%,
q = 0. Everything is computed from scratch with math.erf (no scipy).

This script also carries the reusable `bsm_greeks` (extended with veta) that
the paper's Section 9 prints, and runs a central finite-difference self-check
of every second-order greek against the corresponding first-order closed form,
printing the maximum relative error to stdout.

Reproducible:
    python fig_so_gamma_surface.py     # numpy, matplotlib, stdlib math
"""
import os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SQRT2PI = math.sqrt(2.0 * math.pi)


# ---- scalar reference implementation (reused across the fig_so_ scripts) -----
def npdf_s(x):
    return math.exp(-0.5 * x * x) / SQRT2PI


def ncdf_s(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bsm_greeks(S, K, T, r, sigma, q=0.0, call=True):
    """Black-Scholes-Merton price and greeks. vega/vanna/vomma per vol POINT;
    theta and charm per CALENDAR DAY; rho per 1% rate; veta per vol point per
    YEAR. sign=+1 call, -1 put."""
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    dq, dr = math.exp(-q * T), math.exp(-r * T)
    s = 1.0 if call else -1.0
    price = s * (S * dq * ncdf_s(s * d1) - K * dr * ncdf_s(s * d2))
    delta = s * dq * ncdf_s(s * d1)
    gamma = dq * npdf_s(d1) / (S * sigma * sqrtT)
    vega  = S * dq * npdf_s(d1) * sqrtT / 100.0
    theta = (-S * dq * npdf_s(d1) * sigma / (2 * sqrtT)
             - s * r * K * dr * ncdf_s(s * d2)
             + s * q * S * dq * ncdf_s(s * d1)) / 365.0
    rho   = s * K * T * dr * ncdf_s(s * d2) / 100.0
    vanna = -dq * npdf_s(d1) * d2 / sigma / 100.0
    charm = (q * s * dq * ncdf_s(s * d1)
             - dq * npdf_s(d1) * (2 * (r - q) * T - d2 * sigma * sqrtT)
             / (2 * T * sigma * sqrtT)) / 365.0
    vomma = S * dq * npdf_s(d1) * sqrtT * d1 * d2 / sigma / 10000.0
    # veta = d(vega)/dt (calendar time, per year). The finite-difference check
    # below fixes the sign: with a leading minus the expression is d(vega)/dT
    # (time-to-expiry), the opposite of the theta/charm calendar convention.
    veta  = (S * dq * npdf_s(d1) * sqrtT
             * (q + (r - q) * d1 / (sigma * sqrtT) - (1 + d1 * d2) / (2 * T))) / 100.0
    return dict(price=price, delta=delta, gamma=gamma, vega=vega, theta=theta,
                rho=rho, vanna=vanna, charm=charm, vomma=vomma, veta=veta)


# ---- vectorized helpers for the figure ------------------------------------
def npdf(x):
    return np.exp(-0.5 * x * x) / SQRT2PI


def gamma_grid(S, K, T, r, sig):
    d1 = (np.log(S / K) + (r + 0.5 * sig ** 2) * T) / (sig * np.sqrt(T))
    return npdf(d1) / (S * sig * np.sqrt(T))


# ---------------------------------------------------------------------------
K, SIG, R = 100.0, 0.20, 0.04
S0 = 100.0

# left panel: surface over strike x maturity, fixed spot
strikes = np.linspace(80, 120, 121)
mats = np.linspace(5 / 252, 1.0, 120)
Kg, Tg = np.meshgrid(strikes, mats)
gamma_surf = gamma_grid(S0, Kg, Tg, R, SIG)

# right panel: gamma across moneyness at three maturities, fixed strike
S = np.linspace(80.0, 120.0, 401)
prof_mats = [(5 / 252, "1 week", "#7c1c2c"), (21 / 252, "1 month", "#2f6d4f"),
             (63 / 252, "3 months", "#17120e")]

fig = plt.figure(figsize=(9.0, 4.0))
ax0 = fig.add_subplot(1, 2, 1, projection="3d")
ax0.plot_surface(Kg, Tg * 12, gamma_surf, cmap="cividis", linewidth=0,
                 antialiased=True, rstride=2, cstride=2)
ax0.set_xlabel("strike", fontsize=8, labelpad=1)
ax0.set_ylabel("maturity (months)", fontsize=8, labelpad=1)
ax0.set_zlabel("gamma", fontsize=8, labelpad=1)
ax0.set_title("Gamma surface (spot fixed at 100)", fontsize=9.6)
ax0.tick_params(labelsize=7, pad=0)
ax0.view_init(elev=24, azim=-58)

ax1 = fig.add_subplot(1, 2, 2)
for T, lab, col in prof_mats:
    ax1.plot(S / K, gamma_grid(S, K, T, R, SIG), color=col, lw=1.7, label=lab)
ax1.axvline(1.0, color="#999", lw=0.7, ls=":")
ax1.set_title("Gamma across moneyness", fontsize=9.6)
ax1.set_xlabel("moneyness S/K", fontsize=9)
ax1.set_ylabel("gamma", fontsize=9)
for sp in ("top", "right"):
    ax1.spines[sp].set_visible(False)
ax1.grid(True, alpha=0.22)
ax1.tick_params(labelsize=8)
ax1.legend(fontsize=8, frameon=False, loc="upper right")

fig.suptitle("Gamma piles up at the money and spikes into expiry",
             fontsize=10.6, y=1.00)
fig.text(0.5, -0.02,
         "Black-Scholes-Merton, K/spot=100, sigma=20%, r=4%, q=0; strikes 80-120, "
         "maturities 1 week to 1 year. Didactic model computation, no market data.",
         ha="center", fontsize=7.5, color="#666")
plt.tight_layout(rect=(0, 0.03, 1, 0.97))
OUT = os.path.join(HERE, "fig_so_gamma_surface.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# --- numbers quoted in the text --------------------------------------------
print("\n[gamma across maturity, ATM]")
for T, lab in [(5 / 252, "1 week"), (21 / 252, "1 month"), (63 / 252, "3 months"),
               (0.5, "6 months"), (1.0, "1 year")]:
    g = bsm_greeks(S=100, K=100, T=T, r=R, sigma=SIG, call=True)
    print(f"  ATM {lab:9s}: gamma={g['gamma']:.4f}")
g1w = bsm_greeks(100, 100, 5 / 252, R, SIG)['gamma']
g1y = bsm_greeks(100, 100, 1.0, R, SIG)['gamma']
print(f"  1-week / 1-year gamma ratio = {g1w / g1y:.1f}x")
g2d = bsm_greeks(100, 100, 2 / 365, R, SIG)['gamma']
print(f"  ATM 2 days   : gamma={g2d:.4f}  (near-expiry spike)")

MULT = 100.0
gm = bsm_greeks(100, 100, 21 / 252, R, SIG)['gamma']
dollar_gamma = gm * S0 ** 2 * MULT / 100.0
print(f"\n[dollar gamma, ATM 1-month, multiplier {MULT:.0f}]")
print(f"  gamma={gm:.4f} -> dollar gamma = gamma*S^2*mult/100 = ${dollar_gamma:,.0f} per 1% move")

# --- Section 9 worked example: full greek vector for the 1-month ATM call ---
print("\n[Section 9 worked example: 1-month ATM call, S=K=100, r=4%, sigma=20%]")
g = bsm_greeks(S=100, K=100, T=21 / 252, r=0.04, sigma=0.20, call=True)
for name in ("price", "delta", "gamma", "vega", "theta", "rho",
             "vanna", "charm", "vomma", "veta"):
    print(f"  {name:6s} {g[name]:+.5f}")


# --- central finite-difference self-check of every second-order greek -------
def self_check():
    """Verify each second-order greek against a central finite difference of the
    corresponding first-order closed form, in natural units (per unit vol, per
    year). Returns the max relative error over a grid away from sign flips."""
    hS, hV, hT = 1e-3, 1e-4, 1e-5
    errs = {"gamma": 0.0, "vanna": 0.0, "charm": 0.0, "vomma": 0.0, "veta": 0.0}

    def delta(S, K, T, r, sig, q=0.0, call=True):
        return bsm_greeks(S, K, T, r, sig, q, call)["delta"]

    def vega_nat(S, K, T, r, sig, q=0.0, call=True):        # per unit vol
        return bsm_greeks(S, K, T, r, sig, q, call)["vega"] * 100.0

    for mny in (0.90, 0.95, 1.05, 1.10):
        for T in (30 / 365, 90 / 365):
            for call in (True, False):
                S, K, r, sig = mny * 100.0, 100.0, R, SIG
                g = bsm_greeks(S, K, T, r, sig, call=call)
                # gamma = dDelta/dS
                fd = (delta(S + hS, K, T, r, sig, call=call)
                      - delta(S - hS, K, T, r, sig, call=call)) / (2 * hS)
                errs["gamma"] = max(errs["gamma"], abs(fd - g["gamma"]) / abs(g["gamma"]))
                # vanna = dDelta/dsigma  (per unit vol)
                cf = g["vanna"] * 100.0
                fd = (delta(S, K, T, r, sig + hV, call=call)
                      - delta(S, K, T, r, sig - hV, call=call)) / (2 * hV)
                errs["vanna"] = max(errs["vanna"], abs(fd - cf) / abs(cf))
                # charm = dDelta/dt = -dDelta/dT  (per year)
                cf = g["charm"] * 365.0
                fd = -(delta(S, K, T + hT, r, sig, call=call)
                       - delta(S, K, T - hT, r, sig, call=call)) / (2 * hT)
                errs["charm"] = max(errs["charm"], abs(fd - cf) / abs(cf))
                # vomma = dVega/dsigma  (per unit vol)
                cf = g["vomma"] * 10000.0
                fd = (vega_nat(S, K, T, r, sig + hV, call=call)
                      - vega_nat(S, K, T, r, sig - hV, call=call)) / (2 * hV)
                errs["vomma"] = max(errs["vomma"], abs(fd - cf) / abs(cf))
                # veta = dVega/dt = -dVega/dT  (per year, per unit vol)
                cf = g["veta"] * 100.0
                fd = -(vega_nat(S, K, T + hT, r, sig, call=call)
                       - vega_nat(S, K, T - hT, r, sig, call=call)) / (2 * hT)
                errs["veta"] = max(errs["veta"], abs(fd - cf) / abs(cf))
    return errs


errs = self_check()
print("\n[self-check: max relative error vs central finite difference]")
for k in ("gamma", "vanna", "charm", "vomma", "veta"):
    print(f"  {k:6s} {errs[k]:.2e}")
print(f"  OVERALL max rel err = {max(errs.values()):.2e}")
