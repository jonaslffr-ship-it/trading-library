"""
Figure 1 - A schematic limit order book (DOM view), drawn, not screenshotted.

Pure didactic diagram: a ten-level book for a fictitious stock trading near
$100.00 with a one-cent tick. Bids (buy limit orders) accumulate below the
market on the left, asks (sell limit orders) above it on the right; the gap
between the best bid and the best ask is the spread. A 700-share marketable
buy order is shown walking the ask side: it consumes the 300 shares at 100.01
and 400 of the 500 shares at 100.02, so its average fill is worse than the
quoted best ask - the price of immediacy, made visible.

All numbers are chosen for arithmetic clarity, not taken from a feed; the
figure is a diagram of mechanics (the empirical figures of this paper are
Figures 3). No data download.

Reproducible:
    python fig_orderbook_schematic.py     # numpy, matplotlib only
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- the book (price -> resting size) ---------------------------------------
bids = [(100.00, 400), (99.99, 550), (99.98, 700), (99.97, 350), (99.96, 900)]
asks = [(100.01, 300), (100.02, 500), (100.03, 450), (100.04, 650), (100.05, 1000)]
TICK = 0.01
best_bid, best_ask = bids[0][0], asks[0][0]
mid = (best_bid + best_ask) / 2

# ---- a 700-share marketable buy walks the ask side --------------------------
order = 700
take1 = min(order, asks[0][1])            # 300 @ 100.01
take2 = order - take1                     # 400 @ 100.02
avg_fill = (take1 * asks[0][0] + take2 * asks[1][0]) / order
slip_ticks = (avg_fill - mid) / TICK
left_at_10002 = asks[1][1] - take2        # 100 shares remain at 100.02

C_BID, C_ASK, C_INK, C_ACC = "#2f6d4f", "#7c1c2c", "#17120e", "#8a6d3b"

fig, ax = plt.subplots(figsize=(6.8, 4.4))
SC = 1 / 1000.0                                       # shares -> bar length

for p, q in bids:
    ax.barh(p, -q * SC, height=TICK * 0.72, color=C_BID, alpha=0.75, zorder=2)
    ax.text(-q * SC - 0.04, p, f"{q}", va="center", ha="right",
            fontsize=7.6, color=C_BID)
for p, q in asks:
    ax.barh(p, q * SC, height=TICK * 0.72, color=C_ASK, alpha=0.75, zorder=2)
    ax.text(q * SC + 0.04, p, f"{q}", va="center", ha="left",
            fontsize=7.6, color=C_ASK)

# price labels down the middle
for p, _ in bids + asks:
    ax.text(0, p, f"{p:.2f}", va="center", ha="center", fontsize=7.6,
            color=C_INK, zorder=4,
            bbox=dict(boxstyle="round,pad=0.14", fc="white", ec="none"))

# spread band
ax.axhspan(best_bid + TICK * 0.36, best_ask - TICK * 0.36,
           color=C_ACC, alpha=0.18, zorder=1)
ax.annotate("the spread: one tick of\n“nobody agrees yet”",
            xy=(0.72, (best_bid + best_ask) / 2), xytext=(1.05, 99.988),
            fontsize=8, color=C_ACC,
            arrowprops=dict(arrowstyle="->", color=C_ACC, lw=0.9))

ax.annotate("best bid 100.00\n(highest price any buyer\nwill pay right now)",
            xy=(-bids[0][1] * SC - 0.1, best_bid), xytext=(-1.62, 99.985),
            fontsize=7.8, color=C_BID,
            arrowprops=dict(arrowstyle="->", color=C_BID, lw=0.9))
ax.annotate("best ask 100.01\n(lowest price any seller\nwill accept right now)",
            xy=(asks[0][1] * SC + 0.1, best_ask), xytext=(0.82, 100.028),
            fontsize=7.8, color=C_ASK,
            arrowprops=dict(arrowstyle="->", color=C_ASK, lw=0.9))

# the marketable buy order walking the book
ax.annotate("", xy=(asks[1][1] * SC * 0.55, asks[1][0] + 0.001),
            xytext=(-0.62, 100.036),
            arrowprops=dict(arrowstyle="-|>", color=C_INK, lw=1.5,
                            connectionstyle="arc3,rad=0.3"))
ax.text(-1.62, 100.047,
        f"market buy {order} shares:\ntakes {take1} @ {asks[0][0]:.2f} + "
        f"{take2} @ {asks[1][0]:.2f}\naverage fill {avg_fill:.4f} "
        f"(≈ {slip_ticks:.1f} ticks above mid)",
        fontsize=7.8, color=C_INK, ha="left", va="top")

ax.text(-1.6, 100.064, "BIDS — resting buy limit orders",
        fontsize=8.4, color=C_BID, ha="left")
ax.text(1.6, 100.064, "ASKS — resting sell limit orders",
        fontsize=8.4, color=C_ASK, ha="right")

ax.set_xlim(-1.65, 1.65)
ax.set_ylim(99.952, 100.070)
ax.set_yticks([])
ax.set_xticks([])
for s in ax.spines.values():
    s.set_visible(False)
ax.set_title("The order book: two queues of unexecuted intentions, "
             "meeting at the spread", fontsize=10.2)
fig.text(0.5, -0.015,
         "Didactic schematic (fictitious stock, $0.01 tick); sizes chosen for "
         "arithmetic clarity. Bar length ∝ resting shares.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_orderbook_schematic.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"best_bid={best_bid:.2f} best_ask={best_ask:.2f} mid={mid:.3f} "
      f"spread_ticks={(best_ask-best_bid)/TICK:.0f}")
print(f"depth_bid_total={sum(q for _, q in bids)} "
      f"depth_ask_total={sum(q for _, q in asks)}")
print(f"order={order} take1={take1}@{asks[0][0]:.2f} take2={take2}@{asks[1][0]:.2f} "
      f"avg_fill={avg_fill:.4f} slippage_vs_mid_ticks={slip_ticks:.2f} "
      f"left_at_100.02={left_at_10002} new_best_ask={asks[1][0]:.2f} "
      f"new_spread_ticks={(asks[1][0]-best_bid)/TICK:.0f}")
