"""
Figure 1 - The flow taxonomy: trigger (rows) x price elasticity (columns).

Didactic diagram, no data. Rows answer "what pulls the trigger?" (information,
price moves, volatility moves, clock & calendar); the horizontal position
answers the organizing question of the paper: HOW FREE is the trader to walk
away from the trade if the price is bad? Far right = must trade regardless of
price (price-inelastic, mechanical); far left = trades only when the price is
attractive (price-elastic, discretionary).

Reproducible:
    python fig_flow_taxonomy.py     # matplotlib only
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))

ROWS = [
    ("information &\nvaluation", "#8a6d3b"),
    ("price moves", "#3b5b78"),
    ("volatility moves", "#7c1c2c"),
    ("clock & calendar", "#2f6d4f"),
]

# (row, x-center in 0..1 elasticity coordinates, width, label)
BOXES = [
    (0, 0.13, 0.22, "discretionary\nfundamental buyers/sellers"),
    (0, 0.40, 0.16, "quant value /\nfactor rebalancing"),
    (1, 0.16, 0.20, "market makers & HFT\n(quote, mean-revert inventory)"),
    (1, 0.52, 0.20, "CTA / trend followers\n(rule-bound, some discretion\nin execution)"),
    (1, 0.83, 0.24, "dealer gamma hedging\n(short-gamma books:\nbuy rallies, sell breaks)"),
    (2, 0.55, 0.22, "risk parity / target-vol\nfunds (deleverage as\nrealized vol rises)"),
    (2, 0.84, 0.22, "dealer vanna hedging\n(delta shifts as IV moves)"),
    (3, 0.30, 0.20, "buyback programs\n(price-limited, windowed)"),
    (3, 0.60, 0.21, "pension & month-end\nrebalancing (to policy\nweights, dated)"),
    (3, 0.86, 0.22, "index rebalances, passive\ncreations, dealer charm\n(expiry-dated)"),
]

fig, ax = plt.subplots(figsize=(7.8, 5.4))
ax.set_xlim(0, 1.0)
ax.set_ylim(-0.9, 4.05)
ax.axis("off")

for r, (label, col) in enumerate(ROWS):
    y = 3 - r
    ax.text(-0.015, y, label, ha="right", va="center", fontsize=8.6, color=col,
            fontweight="bold", transform=ax.transData)
    ax.axhline(y - 0.5, color="#ddd", lw=0.7, zorder=0)

for r, xc, w, label in BOXES:
    y = 3 - r
    col = ROWS[r][1]
    box = FancyBboxPatch((xc - w / 2, y - 0.36), w, 0.72,
                         boxstyle="round,pad=0.012,rounding_size=0.02",
                         linewidth=1.1, edgecolor=col, facecolor=col, alpha=0.14)
    ax.add_patch(box)
    box2 = FancyBboxPatch((xc - w / 2, y - 0.36), w, 0.72,
                          boxstyle="round,pad=0.012,rounding_size=0.02",
                          linewidth=1.1, edgecolor=col, facecolor="none")
    ax.add_patch(box2)
    ax.text(xc, y, label, ha="center", va="center", fontsize=7.4, color="#17120e")

arrow = FancyArrowPatch((0.02, -0.55), (0.98, -0.55), arrowstyle="-|>",
                        mutation_scale=16, lw=1.4, color="#17120e")
ax.add_patch(arrow)
ax.text(0.02, -0.76, "price-elastic: trades only at attractive prices",
        fontsize=8.2, color="#666", ha="left")
ax.text(0.98, -0.76, "price-inelastic: must trade, regardless of price",
        fontsize=8.2, color="#17120e", ha="right", fontweight="bold")
ax.text(0.5, -0.47, "how free is the trader to walk away?",
        fontsize=8.6, color="#444", ha="center", style="italic")
ax.set_title("A taxonomy of flows: what pulls the trigger (rows) x who must trade (axis)",
             fontsize=10.4)
fig.text(0.5, 0.005,
         "Positions on the axis are qualitative orderings, not measurements; "
         "each family is treated in the section given in the text.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_flow_taxonomy.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
