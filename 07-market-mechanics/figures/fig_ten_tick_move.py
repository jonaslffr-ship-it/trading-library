"""
Figure 2 - The same ten-tick move, produced by two different mechanisms.

Didactic before/after book diagram for the worked example in Section 4. One
fictitious stock near $100.00, one-cent tick, ten resting ask levels. The
LEFT panel is the starting book. The MIDDLE panel shows mechanism (a),
liquidity TAKING: buyers send market orders that consume every ask from
100.01 through 100.09 (3,400 shares) plus 100 shares of the 800 resting at
100.10 - 3,500 shares trade and the last price rises ten ticks. The RIGHT
panel shows mechanism (b), liquidity VANISHING: the same nine levels are
cancelled by their owners - no trade occurs - and a single 100-share market
buy then prints at 100.10. Same ten-tick move; 35 times less volume.

All numbers are chosen for arithmetic clarity (diagram of mechanics, not a
data plot). No data download.

Reproducible:
    python fig_ten_tick_move.py     # numpy, matplotlib only
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

TICK = 0.01
bids = [(100.00, 400), (99.99, 550), (99.98, 700)]
asks = [(100.01, 300), (100.02, 500), (100.03, 450), (100.04, 600),
        (100.05, 200), (100.06, 350), (100.07, 450), (100.08, 300),
        (100.09, 250), (100.10, 800)]

taken_below_top = sum(q for p, q in asks if p < 100.10)      # 3,400
extra_at_top = 100
shares_a = taken_below_top + extra_at_top                     # 3,500
shares_b = 100
ratio = shares_a / shares_b
move_ticks = round((100.10 - 100.00) / TICK)

C_BID, C_ASK, C_INK, C_ACC = "#2f6d4f", "#7c1c2c", "#17120e", "#8a6d3b"
SC = 1 / 1000.0

fig, axes = plt.subplots(1, 3, figsize=(9.4, 4.4), sharey=True)
titles = ["before\nlast trade 100.00",
          "(a) liquidity taken\n3,500 shares bought",
          "(b) liquidity vanished\n9 levels cancelled, 100 shares trade"]


def draw_book(ax, bid_rows, ask_rows, ghost_asks=(), ghost_label=None):
    for p, q in bid_rows:
        ax.barh(p, -q * SC, height=TICK * 0.68, color=C_BID, alpha=0.75)
    for p, q in ask_rows:
        ax.barh(p, q * SC, height=TICK * 0.68, color=C_ASK, alpha=0.75)
    for p, q in ghost_asks:
        ax.barh(p, q * SC, height=TICK * 0.68, fill=False,
                edgecolor=C_ASK, lw=0.8, ls=(0, (2, 2)), alpha=0.55)
    for p in [b[0] for b in bids] + [a[0] for a in asks]:
        ax.text(0, p, f"{p:.2f}", va="center", ha="center", fontsize=6.6,
                color=C_INK, zorder=4,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"))
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(99.972, 100.112)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


# --- panel 1: before ---------------------------------------------------------
draw_book(axes[0], bids, asks)
axes[0].annotate("3,400 shares rest\nbetween 100.01\nand 100.09",
                 xy=(0.62, 100.05), xytext=(0.5, 99.994), fontsize=7.4,
                 color=C_ASK,
                 arrowprops=dict(arrowstyle="->", color=C_ASK, lw=0.8))

# --- panel 2: aggressive buying consumes the book ----------------------------
draw_book(axes[1], bids, [(100.10, 800 - extra_at_top)],
          ghost_asks=[(p, q) for p, q in asks if p < 100.10])
axes[1].annotate("every level up to\n100.09 was traded\nthrough (filled)",
                 xy=(0.42, 100.05), xytext=(0.42, 99.998), fontsize=7.4,
                 color=C_ASK,
                 arrowprops=dict(arrowstyle="->", color=C_ASK, lw=0.8))
axes[1].plot(0.86, 100.10, marker="*", ms=9, color=C_ACC)
axes[1].text(0.86, 100.104, "last trade\n100.10", fontsize=7.0,
             color=C_ACC, ha="center", va="bottom")

# --- panel 3: quotes pulled, one tiny trade ----------------------------------
draw_book(axes[2], bids, [(100.10, 800 - shares_b)],
          ghost_asks=[(p, q) for p, q in asks if p < 100.10])
axes[2].annotate("same nine levels —\ncancelled, never traded",
                 xy=(0.42, 100.05), xytext=(0.40, 99.998), fontsize=7.4,
                 color=C_ASK,
                 arrowprops=dict(arrowstyle="->", color=C_ASK, lw=0.8))
axes[2].plot(0.86, 100.10, marker="*", ms=9, color=C_ACC)
axes[2].text(0.86, 100.104, "last trade\n100.10", fontsize=7.0,
             color=C_ACC, ha="center", va="bottom")

for ax, t in zip(axes, titles):
    ax.set_title(t, fontsize=8.8)

fig.suptitle("One ten-tick move, two mechanisms: taking liquidity vs. "
             "liquidity withdrawing", fontsize=10.4, y=1.0)
fig.text(0.5, -0.02,
         "Didactic schematic (fictitious stock, $0.01 tick). Solid bars = resting "
         "orders; dashed outlines = where orders used to be. "
         f"(a) {shares_a:,} shares traded; (b) {shares_b} shares traded — "
         f"a {ratio:.0f}:1 volume ratio for the same move.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_ten_tick_move.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"move_ticks={move_ticks} shares_mechanism_a={shares_a} "
      f"shares_mechanism_b={shares_b} volume_ratio={ratio:.0f}")
print(f"resting_100.01_to_100.09={taken_below_top} extra_at_100.10={extra_at_top} "
      f"left_at_100.10_a={800 - extra_at_top} left_at_100.10_b={800 - shares_b}")
