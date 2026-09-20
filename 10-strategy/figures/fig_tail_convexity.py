"""
Figure 1 - Why a cheap "1-delta" put explodes: the two convexities.

A "1-delta" option is desk shorthand for delta = 0.01 (delta quoted in percent):
a deeply out-of-the-money option that costs almost nothing and is almost pure
convexity. This figure isolates the two sources of that convexity on a single
fixed contract, with a pure Black-Scholes-Merton computation and no market data.

Setup (fixed in advance): spot S0 = 100, r = 2%, q = 0, maturity T = 21/252
(one month), base implied vol sigma0 = 15%. We solve for the strike K whose
BSM put delta equals exactly -0.01 at the base state - that is the "1-delta"
put - and then measure its value as a MULTIPLE of its base premium under:
  (a) implied vol rising at UNCHANGED spot  (the vega / vanna / volga channel);
  (b) a joint crash path where spot falls 0..20% AND implied vol rises 15..55%
      together, decomposed into spot-only, vol-only, and joint effects.

Panel (a) shows the "extremely expensive when volatility rises" property that
makes the contract a crash hedge; panel (b) shows that early in a crash the
value multiple is driven mostly by the vol jump, and only later by spot.

Reproducible:
    python fig_tail_convexity.py     # numpy, matplotlib, stdlib math
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


def d1d2(S, K, T, r, sig, q=0.0):
    d1 = (np.log(S / K) + (r - q + 0.5 * sig ** 2) * T) / (sig * np.sqrt(T))
    return d1, d1 - sig * np.sqrt(T)


def put_price(S, K, T, r, sig, q=0.0):
    d1, d2 = d1d2(S, K, T, r, sig, q)
    return K * np.exp(-r * T) * ncdf(-d2) - S * np.exp(-q * T) * ncdf(-d1)


def put_delta(S, K, T, r, sig, q=0.0):
    d1, _ = d1d2(S, K, T, r, sig, q)
    return np.exp(-q * T) * (ncdf(d1) - 1.0)   # negative


S0, R, Q, T, SIG0 = 100.0, 0.02, 0.0, 21.0 / 252.0, 0.15

# --- solve K such that put delta = -0.01 at the base state (bisection) --------
target = -0.01
# put delta is a decreasing function of K: near-zero for deep-OTM (small K),
# toward -0.5 at the money. Root-find the K whose delta = -0.01.
lo, hi = 50.0, 99.9
for _ in range(200):
    mid = 0.5 * (lo + hi)
    if put_delta(S0, mid, T, R, SIG0) > target:   # delta too close to 0 -> K too low
        lo = mid
    else:
        hi = mid
K = 0.5 * (lo + hi)
base = float(put_price(np.array([S0]), K, T, R, SIG0)[0])
otm = 100.0 * (S0 - K) / S0
print(f"1-delta strike K={K:.2f}  ({otm:.1f}% OTM)   base premium={base:.4f} "
      f"(= {100*base/S0:.3f}% of spot)   base delta={float(put_delta(np.array([S0]),K,T,R,SIG0)[0]):.4f}")

# ---------------- panel (a): value multiple vs implied vol, spot fixed -------
ivs = np.linspace(0.10, 0.80, 351)
va = put_price(np.array([S0]), K, T, R, ivs) / base

# ---------------- panel (b): joint crash path --------------------------------
dd = np.linspace(0.0, 0.20, 201)                 # spot drawdown 0..20%
u = dd / 0.20                                     # crash severity 0..1
iv_path = SIG0 + (0.55 - SIG0) * u                # 15% -> 55%
spot = S0 * (1.0 - dd)
spot_only = put_price(spot, K, T, R, SIG0) / base
vol_only = put_price(np.array([S0]), K, T, R, iv_path) / base
joint = put_price(spot, K, T, R, iv_path) / base

for probe in (0.05, 0.10, 0.15, 0.20):
    i = int(round(probe / 0.20 * 200))
    print(f"  drawdown {100*dd[i]:4.1f}% (iv {100*iv_path[i]:.0f}%): "
          f"spot-only x{spot_only[i]:5.1f}  vol-only x{vol_only[i]:5.1f}  joint x{joint[i]:6.1f}")
print(f"  value multiple at unchanged spot, iv 15->45%: x{float(put_price(np.array([S0]),K,T,R,np.array([0.45]))[0]/base):.1f}")

# ---------------- figure ------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.6, 3.9))

ax1.plot(100 * ivs, va, color="#7c1c2c", lw=1.9)
ax1.axvline(100 * SIG0, color="#999", lw=0.8, ls=":")
ax1.annotate("base = 15% IV\n(premium = 1x)", xy=(15, 1.0), xytext=(26, 4.0),
             fontsize=8, color="#555",
             arrowprops=dict(arrowstyle="->", color="#999", lw=0.8))
ax1.set_title("(a)  Same contract, unchanged spot: value vs implied vol",
              fontsize=9.6, loc="left")
ax1.set_xlabel("implied volatility (%)", fontsize=8.6)
ax1.set_ylabel("value as multiple of base premium", fontsize=8.6)
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)
ax1.grid(True, alpha=0.22)
ax1.tick_params(labelsize=8)

ax2.plot(100 * dd, joint, color="#7c1c2c", lw=2.0, label="joint (spot down + IV up)")
ax2.plot(100 * dd, spot_only, color="#31536e", lw=1.6, ls="--", label="spot only (IV fixed 15%)")
ax2.plot(100 * dd, vol_only, color="#2f6d4f", lw=1.6, ls="-.", label="IV only (spot fixed)")
ax2.set_yscale("log")
ax2.set_title("(b)  A crash path: the vol jump leads, spot follows", fontsize=9.6, loc="left")
ax2.set_xlabel("spot drawdown (%)  [IV rises 15% to 55% jointly]", fontsize=8.6)
ax2.set_ylabel("value multiple (log scale)", fontsize=8.6)
ax2.legend(fontsize=7.8, frameon=False, loc="upper left")
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
ax2.grid(True, alpha=0.22)
ax2.tick_params(labelsize=8)

fig.text(0.5, -0.02,
         f"BSM put, S0=100, r=2%, q=0, T=21/252; strike K={K:.1f} ({otm:.0f}% OTM) chosen so base put delta = -0.01 "
         "(a '1-delta' put). Model computation, no market data.",
         ha="center", fontsize=7.5, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_tail_convexity.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
