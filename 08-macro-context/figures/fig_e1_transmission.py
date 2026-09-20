"""
Figure 6 - Cross-asset transmission: the standard linkages, drawn honestly.

A didactic schematic (no data): how a change in policy rates / rate
expectations propagates - in the textbook direction - to bonds, equities,
credit, FX and commodities, and where growth/inflation data enter the loop.
The bottom banner carries the caveat that belongs in the picture itself:
every coupling is loose and regime-dependent.

Reproducible:
    python fig_e1_transmission.py     # matplotlib only
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
INK, GREEN, CLARET, BLUE, GREY = "#17120e", "#2f6d4f", "#7c1c2c", "#2b4a6f", "#666"
PAPER = "#f7f4ef"

fig, ax = plt.subplots(figsize=(7.4, 5.0))
ax.set_xlim(0, 10); ax.set_ylim(0, 7); ax.axis("off")


def box(x, y, w, h, text, fc, ec, fs=8.6, tc=None):
    ax.add_patch(plt.Rectangle((x - w / 2, y - h / 2), w, h, fc=fc, ec=ec,
                               lw=1.1, zorder=3, joinstyle="round"))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs,
            color=tc or ec, zorder=4, linespacing=1.25)


def arrow(x0, y0, x1, y1, label=None, lx=0.0, ly=0.0, color=GREY, fs=6.9):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2,
                                shrinkA=2, shrinkB=2), zorder=2)
    if label:
        ax.text((x0 + x1) / 2 + lx, (y0 + y1) / 2 + ly, label, fontsize=fs,
                color=color, ha="center", va="center", zorder=5,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))


# top row: data -> central bank
box(2.1, 6.15, 3.4, 0.95, "Growth & inflation data\n(NFP, CPI, PMIs …)", PAPER, GREEN)
box(7.6, 6.15, 3.6, 0.95, "Central bank:\npolicy rate & expectations", PAPER, BLUE)
arrow(3.8, 6.15, 5.8, 6.15, "reaction function", 0, 0.22, BLUE)

# hub: interest rates
box(5.0, 4.45, 4.4, 0.95, "Interest rates across maturities\n(the discount rate; "
    "the price of credit)", "#eef1f5", BLUE, 8.8)
arrow(7.6, 5.68, 5.6, 4.95, "sets the short end;\nguidance moves the rest", 1.25,
      0.25, BLUE)

# asset row
box(1.45, 2.55, 2.35, 1.0, "Equities\nfuture earnings,\ndiscounted", PAPER, INK, 7.8)
box(3.85, 2.55, 2.1, 1.0, "Credit\nspreads over\nTreasuries", PAPER, INK, 7.8)
box(6.15, 2.55, 2.1, 1.0, "FX\nrate differentials\nmove capital", PAPER, INK, 7.8)
box(8.55, 2.55, 2.35, 1.0, "Commodities\nglobal demand;\npriced in USD", PAPER, INK, 7.8)

arrow(3.6, 3.98, 1.75, 3.07, "higher rates ⇒ lower\npresent value*", -0.75, 0.12, CLARET)
arrow(4.6, 3.98, 4.0, 3.07, "funding costs;\ndefault risk", 0.72, 0.12, GREY)
arrow(5.6, 3.98, 6.05, 3.07, "carry &\ncapital flows", 0.72, 0.1, GREY)
arrow(6.6, 3.98, 8.3, 3.07, "USD strength\npressures prices*", 0.85, 0.22, GREY)
arrow(2.1, 5.68, 1.35, 3.07, "growth surprises hit\nearnings directly", -0.62, 0.55, GREEN)

# feedback
arrow(9.35, 3.07, 9.35, 5.9, None, 0, 0, "#b8b0a4")
ax.text(9.62, 4.5, "asset prices &\nfinancial conditions\nfeed back", fontsize=6.6,
        color="#8a8177", ha="center", rotation=90)

ax.text(5.0, 0.9, "* Textbook direction, all else equal — every coupling here is loose "
        "and regime-dependent.\nCounterexample: in 2022 equities and bonds fell "
        "together; in 2020–21 rising rates coexisted with rising equities.",
        ha="center", fontsize=7.6, color=CLARET)
ax.set_title("Cross-asset transmission: the textbook map (to be trusted only loosely)",
             fontsize=10.4)
plt.tight_layout()

OUT = os.path.join(HERE, "fig_e1_transmission.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
