"""
Figure 4 - The participant map: who is on the other side, and how free they are
to walk away.

Didactic diagram (no data download). Each box is one participant family,
placed by its typical holding horizon (x, log scale from seconds to a decade)
and by how price-sensitive its trading is (y): at the top, participants who
trade only when the price suits them; at the bottom, participants whose
mandates, rules, or risk limits force them to trade *regardless* of price.
The shaded band at the bottom is the core idea of the whole track: this is
where predictable flow comes from.

Reproducible:
    python fig_participant_map.py     # numpy, matplotlib only
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))

MIN, HOUR, DAY = 60, 3600, 86400
WEEK, MONTH, YEAR = 7 * 86400, 30 * 86400, 365 * 86400

# name, x (typical horizon, s), y (price sensitivity 0..1), motive, constraint, color
P = [
    ("Market makers", 45, 0.50,
     "earn the spread on\nthousands of tiny trades",
     "must end the day ~flat —\ninventory forces trades", "#2f6d4f"),
    ("Hedgers (dealers,\ncorporates)", DAY, 0.10,
     "shed a risk they\nnever wanted",
     "must trade when exposure\nchanges — at any price", "#7c1c2c"),
    ("Systematic funds\n(CTA, vol-target)", MONTH, 0.42,
     "follow tested rules\nacross many markets",
     "rule triggers force\nentries and exits", "#31567c"),
    ("Retail traders", 12 * HOUR, 0.80,
     "profit, saving, sometimes\nentertainment",
     "small size; pays the\nspread; erratic timing", "#8a6d3b"),
    ("Discretionary\nmanagers", YEAR, 0.86,
     "profit from a\nresearched view",
     "risk limits and client\nredemptions force exits", "#555555"),
    ("Passive / index\nfunds", 8 * YEAR, 0.10,
     "track the benchmark\nas cheaply as possible",
     "must trade inflows and\nrebalances — at the close", "#6d4f2f"),
]

fig, ax = plt.subplots(figsize=(8.4, 4.9))
ax.set_xscale("log")
ax.set_xlim(8, 100 * YEAR)
ax.set_ylim(-0.06, 1.10)

# the price-insensitive band — the core idea
ax.axhspan(-0.06, 0.36, color="#8a6d3b", alpha=0.12, zorder=0)
ax.text(11, 0.30,
        "PRICE-INSENSITIVE ZONE —\nthese participants must trade\n"
        "regardless of price; predictable\nflow originates here\n"
        "(the subject of Track D3)",
        fontsize=7.6, color="#6d4f2f", va="top")

for name, x, y, motive, constraint, c in P:
    txt = (f"{name.upper()}\n"
           f"motive — {motive}\n"
           f"constraint — {constraint}")
    ax.annotate(txt, xy=(x, y), fontsize=6.8, ha="center", va="center",
                color="#17120e", linespacing=1.35,
                bbox=dict(boxstyle="round,pad=0.4", fc="white",
                          ec=c, lw=1.4, alpha=0.95), zorder=3)

ticks = [(60, "1 min"), (HOUR, "1 hour"), (DAY, "1 day"), (WEEK, "1 week"),
         (MONTH, "1 month"), (YEAR, "1 year"), (10 * YEAR, "10 years")]
ax.set_xticks([t for t, _ in ticks])
ax.set_xticklabels([l for _, l in ticks], fontsize=8)
ax.xaxis.set_minor_locator(plt.NullLocator())
ax.set_yticks([0.05, 0.95])
ax.set_yticklabels(["must trade\n(price-taker\nby mandate)",
                    "trades only at\na price they like"], fontsize=8)
ax.set_xlabel("typical holding horizon (log scale)")
ax.set_ylabel("price sensitivity of their trading")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.set_title("The participant map: motive × constraint × horizon — and where "
             "forced flow lives", fontsize=10.4)
fig.text(0.5, -0.015,
         "Didactic schematic; placements are typical orders of magnitude, not "
         "measurements. Every participant can act out of character.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_participant_map.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
for name, x, y, motive, constraint, _ in P:
    print(f"{name.replace(chr(10), ' ')}: horizon~{x}s  sensitivity={y}  "
          f"motive={motive.replace(chr(10), ' ')}  "
          f"constraint={constraint.replace(chr(10), ' ')}")
