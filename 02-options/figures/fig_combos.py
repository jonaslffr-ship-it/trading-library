"""
Figure - Three first combinations: bull call spread, straddle, strangle.

Didactic payoff diagrams at expiry (no market data needed), built from the four
primitives of fig_payoff_primitives.py with the same style of didactic premiums
(stated in the footnote). One panel per combination, break-evens annotated.
The lesson: combinations do not create new payoffs out of nothing - they add
hockey sticks, trading away profit in one region to lower cost or risk in
another.

Reproducible:
    python fig_combos.py     # numpy, matplotlib only
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
S = np.linspace(75, 125, 501)

call = lambda K: np.maximum(S - K, 0)
put = lambda K: np.maximum(K - S, 0)

# didactic premiums (same family as fig_payoff_primitives)
C100, P100, C110, P95, C105 = 5.0, 4.0, 2.0, 2.0, 2.5

spread = call(100) - call(110) - (C100 - C110)          # bull call spread, debit 3
straddle = call(100) + put(100) - (C100 + P100)         # long straddle, debit 9
strangle = call(105) + put(95) - (C105 + P95)           # long strangle, debit 4.5

GREEN, RED, INK, GREY = "#2f6d4f", "#7c1c2c", "#17120e", "#666666"
panels = [
    ("Bull call spread\nlong 100-call, short 110-call", spread,
     [100 + (C100 - C110)], f"cost {C100 - C110:.0f} · max gain {10 - (C100 - C110):.0f}"),
    ("Long straddle\nlong 100-call + long 100-put", straddle,
     [100 - (C100 + P100), 100 + (C100 + P100)], f"cost {C100 + P100:.0f} · needs a big move"),
    ("Long strangle\nlong 95-put + long 105-call", strangle,
     [95 - (C105 + P95), 105 + (C105 + P95)], f"cost {C105 + P95:.1f} · cheaper, needs more"),
]

fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.4), sharey=True)
for ax, (title, y, bes, note) in zip(axes, panels):
    ax.axhline(0, color="#999999", lw=0.8)
    ax.fill_between(S, y, 0, where=(y > 0), color=GREEN, alpha=0.12, lw=0)
    ax.fill_between(S, y, 0, where=(y < 0), color=RED, alpha=0.10, lw=0)
    ax.plot(S, y, color=INK, lw=2.0)
    for be in bes:
        ax.plot(be, 0, "o", color=INK, ms=4.5, zorder=5)
        ax.annotate(f"{be:.1f}".rstrip("0").rstrip("."), xy=(be, 0), xytext=(be, -5.5),
                    fontsize=8.0, color=INK, ha="center")
    ax.set_title(title, fontsize=9.2)
    ax.text(0.5, 0.92, note, transform=ax.transAxes, fontsize=8.0, color=GREY, ha="center")
    ax.set_xlabel("stock price at expiry")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.set_ylim(-14, 16)
    ax.grid(True, axis="y", alpha=0.18)
axes[0].set_ylabel("profit / loss per share")
fig.text(0.5, -0.03,
         f"Didactic premiums as in Figure 1's example family: 100-call = {C100:.0f}, "
         f"100-put = {P100:.0f}, 110-call = {C110:.0f}, 95-put = {P95:.0f}, "
         f"105-call = {C105:.1f}; payoff at expiry, per share, before fees.",
         ha="center", fontsize=7.6, color=GREY)
plt.tight_layout()

OUT = os.path.join(HERE, "fig_combos.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"spread: debit={C100 - C110:.1f} BE={100 + C100 - C110:.1f} max_gain={10 - (C100 - C110):.1f} "
      f"| straddle: debit={C100 + P100:.1f} BEs={100 - C100 - P100:.1f}/{100 + C100 + P100:.1f} "
      f"| strangle: debit={C105 + P95:.1f} BEs={95 - C105 - P95:.1f}/{105 + C105 + P95:.1f}")
