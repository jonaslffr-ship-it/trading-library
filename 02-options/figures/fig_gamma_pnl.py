"""
Figure 3 - What long gamma actually earns: hedged-straddle P&L versus
(realized - implied) volatility.

Didactic seeded simulation, no market data: 800 GBM paths of 21 trading days
are drawn, each with its own true volatility (uniform between 8% and 36%).
On every path a 1-month ATM straddle (S0 = K = 100, r = 0, q = 0) is BOUGHT
at a fixed implied volatility of 20% and delta-hedged once per day at that
same implied vol - the textbook long-gamma book. Final P&L per straddle is
plotted against the vol the path actually realized minus the vol that was
paid. The regression slope is printed and compared with the straddle's
initial vega - the theoretical exchange rate between vol points and P&L.

Reproducible (seed 42):
    python fig_gamma_pnl.py     # numpy, matplotlib, stdlib math
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


def straddle_val_delta(S, K, T, sig):
    """r = q = 0. Returns (value, delta) of call+put; T > 0."""
    d1 = (np.log(S / K) + 0.5 * sig ** 2 * T) / (sig * np.sqrt(T))
    d2 = d1 - sig * np.sqrt(T)
    call = S * ncdf(d1) - K * ncdf(d2)
    put = call + K - S                      # put-call parity, r = 0
    return call + put, 2.0 * ncdf(d1) - 1.0


S0 = K = 100.0
IV = 0.20
N_DAYS, DT = 21, 1.0 / 252.0
N_PATHS = 800
rng = np.random.default_rng(42)
sig_true = rng.uniform(0.08, 0.36, N_PATHS)

# simulate GBM paths (zero drift)
z = rng.standard_normal((N_PATHS, N_DAYS))
logret = (-0.5 * sig_true[:, None] ** 2) * DT + sig_true[:, None] * math.sqrt(DT) * z
S = S0 * np.exp(np.cumsum(logret, axis=1))
S = np.concatenate([np.full((N_PATHS, 1), S0), S], axis=1)   # S[:,0] = S0

# daily delta-hedged LONG straddle, hedged at the implied vol
T0 = N_DAYS / 252.0
V0, delta = straddle_val_delta(np.full(N_PATHS, S0), K, T0, IV)
cash = -V0 - (-delta) * S0        # buy straddle, short delta*S in shares
shares = -delta                   # hedge of a long straddle: short its delta
for i in range(1, N_DAYS + 1):
    T = (N_DAYS - i) / 252.0
    Si = S[:, i]
    if T > 0:
        Vi, di = straddle_val_delta(Si, K, T, IV)
        cash += (shares - (-di)) * Si    # rebalance to new hedge
        shares = -di
    else:
        Vi = np.abs(Si - K)              # settlement value of the straddle
pnl = Vi + shares * S[:, -1] + cash      # mark option + shares + cash (r = 0)

rv = np.std(np.diff(np.log(S), axis=1), axis=1, ddof=1) * math.sqrt(252)
x = (rv - IV) * 100.0                    # vol points actually realized minus paid

slope, intercept = np.polyfit(x, pnl, 1)
resid = pnl - (slope * x + intercept)
r2 = 1.0 - resid.var() / pnl.var()
d1_0 = (0.5 * IV ** 2 * T0) / (IV * math.sqrt(T0))
vega_straddle = 2.0 * S0 * float(npdf(np.array([d1_0]))[0]) * math.sqrt(T0) / 100.0
print(f"paths={N_PATHS} seed=42 slope_per_volpt={slope:.4f} intercept={intercept:.4f} "
      f"R2={r2:.3f} straddle_vega_per_pt={vega_straddle:.4f}")
print(f"share_of_paths_profitable_when_rv_gt_iv="
      f"{np.mean(pnl[x > 0] > 0) * 100:.1f}%  when_rv_lt_iv={np.mean(pnl[x < 0] > 0) * 100:.1f}%")

fig, ax = plt.subplots(figsize=(6.6, 4.2))
ax.scatter(x, pnl, s=7, alpha=0.35, color="#2f6d4f", edgecolors="none")
xx = np.linspace(x.min(), x.max(), 100)
ax.plot(xx, slope * xx + intercept, "-", color="#17120e", lw=1.8,
        label=f"fit: {slope:.3f} $ per vol point (R² = {r2:.2f})")
ax.axvline(0, color="#7c1c2c", lw=1.0, ls="--")
ax.axhline(0, color="#999", lw=0.8)
ax.annotate("paid 20% implied", xy=(0, ax.get_ylim()[1] * 0.9), fontsize=8.4,
            color="#7c1c2c", ha="left", xytext=(0.3, ax.get_ylim()[1] * 0.88))
ax.set_xlabel("realized vol − implied vol (vol points)")
ax.set_ylabel("P&L of the daily-hedged long straddle ($)")
ax.set_title("Long gamma is a bet that realized vol beats the implied vol you paid",
             fontsize=10.2)
ax.legend(fontsize=8.4, frameon=False, loc="lower right")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, alpha=0.22)
fig.text(0.5, -0.02,
         "Seeded GBM simulation (seed 42): 800 paths x 21 days, true vol uniform 8-36%; long ATM straddle "
         "(S0=K=100, r=q=0) bought at 20% implied, delta-hedged daily at that vol. Didactic model computation.",
         ha="center", fontsize=7.4, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_gamma_pnl.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
