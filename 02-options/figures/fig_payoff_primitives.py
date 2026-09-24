"""
Figure - The four option primitives: long/short call, long/short put.

Didactic payoff diagram (no market data needed): profit and loss AT EXPIRY per
share, for one option on a stock, strike K = 100, premium = 5 (call) / 4 (put).
Break-evens, maximum loss and maximum gain are annotated. The point of the 2x2
layout: the two rows are mirror images (buyer vs. seller of the same contract),
and money only changes sides - option trading is zero-sum before costs.

Reproducible:
    python fig_payoff_primitives.py     # numpy, matplotlib only
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

K = 100.0          # strike
CP = 5.0           # call premium
PP = 4.0           # put premium
S = np.linspace(75, 125, 501)   # stock price at expiry

long_call = np.maximum(S - K, 0) - CP
short_call = -long_call
long_put = np.maximum(K - S, 0) - PP
short_put = -long_put

GREEN, RED, INK, GREY = "#2f6d4f", "#7c1c2c", "#17120e", "#666666"

panels = [
    ("Long call — right to buy at K", long_call, K + CP,
     f"max loss = premium ({CP:.0f})", "unlimited upside"),
    ("Long put — right to sell at K", long_put, K - PP,
     f"max loss = premium ({PP:.0f})", f"max gain = {K - PP:.0f}"),
    ("Short call — obligation to sell at K", short_call, K + CP,
     f"max gain = premium ({CP:.0f})", "unlimited risk"),
    ("Short put — obligation to buy at K", short_put, K - PP,
     f"max gain = premium ({PP:.0f})", f"max loss = {K - PP:.0f}"),
]

fig, axes = plt.subplots(2, 2, figsize=(8.6, 6.4), sharex=True, sharey=True)
for ax, (title, y, be, note_flat, note_slope) in zip(axes.flat, panels):
    ax.axhline(0, color="#999999", lw=0.8)
    ax.axvline(K, color="#bbbbbb", lw=0.8, ls=":")
    ax.fill_between(S, y, 0, where=(y > 0), color=GREEN, alpha=0.12, lw=0)
    ax.fill_between(S, y, 0, where=(y < 0), color=RED, alpha=0.10, lw=0)
    ax.plot(S, y, color=INK, lw=2.0)
    ax.plot(be, 0, "o", color=INK, ms=5, zorder=5)
    ax.annotate(f"break-even {be:.0f}", xy=(be, 0), xytext=(be - 1, 9 if y[-1] > 0 else -11),
                fontsize=8.2, color=INK, ha="right" if y[-1] > 0 else "left",
                arrowprops=dict(arrowstyle="->", color=INK, lw=0.7))
    ax.text(K, ax.get_ylim()[1] * 0 + 21, "K", fontsize=8.5, color="#999999", ha="center")
    ax.set_title(title, fontsize=9.6)
    ax.text(0.03, 0.06, note_flat, transform=ax.transAxes, fontsize=8.0, color=GREY)
    ax.text(0.97, 0.94, note_slope, transform=ax.transAxes, fontsize=8.0, color=GREY,
            ha="right", va="top")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.set_ylim(-25, 25)
    ax.grid(True, axis="y", alpha=0.18)
for ax in axes[1]:
    ax.set_xlabel("stock price at expiry")
for ax in axes[:, 0]:
    ax.set_ylabel("profit / loss per share")
fig.text(0.5, -0.015,
         f"Didactic example: strike K = {K:.0f}, call premium = {CP:.0f}, put premium = {PP:.0f}, "
         "payoff at expiry, per share, before fees. Top row: buyers. Bottom row: sellers (mirror images).",
         ha="center", fontsize=7.6, color=GREY)
plt.tight_layout()

OUT = os.path.join(HERE, "fig_payoff_primitives.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"K={K:.0f} call_premium={CP:.0f} put_premium={PP:.0f} "
      f"BE_call={K + CP:.0f} BE_put={K - PP:.0f} "
      f"max_loss_long_call={CP:.0f} max_loss_short_put={K - PP:.0f}")
