"""
Figure 2 - The square-root impact law versus the linear intuition (didactic).

No market data needed: the figure draws the two candidate impact laws that the
literature compares. The square-root law

    impact  =  Y * sigma_daily * sqrt(Q / V)

with Y of order 0.5-1 (Toth et al. 2011; Almgren et al. 2005 estimate a power
close to 0.6; Bouchaud, Farmer & Lillo 2009 survey) against a LINEAR benchmark
calibrated to agree with the square-root law at 16% participation - which makes
the disagreement at small sizes visible: for small orders the square-root law
predicts far MORE impact per unit size than linear intuition suggests.

Parameters used here (didactic, mid-range of the literature):
    sigma_daily = 1.0% (typical index-level daily vol), Y = 0.7, band Y in [0.5, 1].

Every quoted number is printed below.

Reproducible:
    python fig_sqrt_impact.py     # numpy, matplotlib only
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

SIGMA_BPS = 100.0        # 1% daily vol in bps
Y = 0.7                  # mid-range prefactor
Y_LO, Y_HI = 0.5, 1.0    # literature band
CAL = 0.16               # linear line calibrated to match sqrt at 16% participation

phi = np.linspace(0.0, 0.20, 400)
sqrt_mid = Y * SIGMA_BPS * np.sqrt(phi)
sqrt_lo = Y_LO * SIGMA_BPS * np.sqrt(phi)
sqrt_hi = Y_HI * SIGMA_BPS * np.sqrt(phi)
lin_slope = (Y * SIGMA_BPS * np.sqrt(CAL)) / CAL
linear = lin_slope * phi

fig, ax = plt.subplots(figsize=(6.6, 4.1))
ax.fill_between(phi * 100, sqrt_lo, sqrt_hi, color="#2f6d4f", alpha=0.15, lw=0)
ax.plot(phi * 100, sqrt_mid, color="#2f6d4f", lw=2.0,
        label=r"square root:  $Y\,\sigma\,\sqrt{Q/V}$   (Y = 0.7, band 0.5–1)")
ax.plot(phi * 100, linear, color="#7c1c2c", lw=1.6, ls="--",
        label="linear benchmark (matched at 16% participation)")
for p in (0.01, 0.05):
    i_s = Y * SIGMA_BPS * np.sqrt(p)
    i_l = lin_slope * p
    ax.plot([p * 100, p * 100], [i_l, i_s], color="#666", lw=0.8)
    ax.plot(p * 100, i_s, "o", color="#2f6d4f", ms=4)
    ax.plot(p * 100, i_l, "o", color="#7c1c2c", ms=4)
ax.annotate("at 1% of daily volume the square-root law\npredicts ~4x the linear estimate",
            xy=(1.0, Y * SIGMA_BPS * np.sqrt(0.01)), xytext=(2.6, 24),
            fontsize=8.5, color="#17120e",
            arrowprops=dict(arrowstyle="->", color="#666", lw=0.8))
ax.set_xlabel("participation  Q / V  (order size as % of daily volume)")
ax.set_ylabel("expected impact (bps)")
ax.set_title("Concave impact: small flows punch above their weight", fontsize=10.2)
ax.legend(fontsize=8, frameon=False, loc="upper left")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.02,
         "Didactic drawing, parameters mid-range of the empirical literature "
         "(Toth et al. 2011; Almgren et al. 2005): sigma_daily = 1%, Y = 0.7.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_sqrt_impact.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# ---- printed numbers ------------------------------------------------------
for p in (0.001, 0.01, 0.05, 0.10, 0.20):
    print(f"participation {100*p:5.1f}%:  sqrt(Y=0.7) = {Y*SIGMA_BPS*np.sqrt(p):5.1f} bps   "
          f"(band {Y_LO*SIGMA_BPS*np.sqrt(p):.1f}–{Y_HI*SIGMA_BPS*np.sqrt(p):.1f})   "
          f"linear = {lin_slope*p:5.1f} bps")
print(f"linear slope (matched at {100*CAL:.0f}%): {lin_slope:.0f} bps per unit participation")
print(f"ratio sqrt/linear at 1%: {(Y*SIGMA_BPS*np.sqrt(0.01))/(lin_slope*0.01):.1f}x")
