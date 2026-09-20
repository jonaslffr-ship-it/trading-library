"""
Figure 4 (C3) - Reliability diagram + Murphy decomposition for two forecasters.

Two synthetic probability forecasters face the SAME 800 binary events. Events
have true probabilities drawn from {0.2, 0.35, 0.5, 0.65, 0.8}. Forecaster A
is honest (forecast = true probability + small noise); forecaster B reports A's
forecasts with the log-odds DOUBLED -- a strictly monotone relabeling, so its
resolution is identical to A's by construction and only reliability changes.
Both are scored with the Brier score and its Murphy (1973) decomposition
Brier = Reliability - Resolution + Uncertainty, computed exactly over distinct
forecast values (forecasts are quantized to a 0.05 grid).

Reproducible:
    python fig_reliability.py          # needs numpy, matplotlib; seed 42

Free data only: pure simulation (no market data required).
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
N_EVENTS = 800
LEVELS = np.array([0.20, 0.35, 0.50, 0.65, 0.80])
OVERCONF = 2.0                     # log-odds multiplier of forecaster B

rng = np.random.default_rng(SEED)
p_true = rng.choice(LEVELS, size=N_EVENTS)
y = (rng.random(N_EVENTS) < p_true).astype(float)


def quantize(f):
    return np.clip(np.round(f / 0.05) * 0.05, 0.05, 0.95)


f_a = quantize(p_true + rng.normal(0, 0.04, N_EVENTS))
# Forecaster B reports the SAME events grouped the SAME way as A, but doubles the
# log-odds of each probability label -- a strictly monotone RELABELING of A.
# Resolution depends only on the partition of outcomes, not on the labels, so it
# is invariant under this map: RES(A) == RES(B) exactly. Only reliability moves.
odds = np.clip(f_a, 1e-6, 1 - 1e-6)
f_b = 1.0 / (1.0 + np.exp(-OVERCONF * np.log(odds / (1 - odds))))


def brier_murphy(f, y):
    """Brier + exact Murphy decomposition over distinct forecast values."""
    brier = float(np.mean((f - y) ** 2))
    ybar = float(y.mean())
    rel = res = 0.0
    table = []
    for v in np.unique(f):
        m = f == v
        nk, ok = int(m.sum()), float(y[m].mean())
        rel += nk / len(f) * (v - ok) ** 2
        res += nk / len(f) * (ok - ybar) ** 2
        table.append((float(v), nk, ok))
    unc = ybar * (1 - ybar)
    return brier, rel, res, unc, table


stats = {}
for name, f in (("A (calibrated)", f_a), ("B (overconfident)", f_b)):
    stats[name] = brier_murphy(f, y)

fig, ax = plt.subplots(figsize=(6.6, 5.0))
ax.plot([0, 1], [0, 1], "-", color="#bbbbbb", lw=1.0, zorder=1)
MIN_CELL = 15                      # cells below this are shown hollow (anecdotes)
for (name, f), col in zip((("A (calibrated)", f_a), ("B (overconfident)", f_b)),
                          ("#2f6d4f", "#7c1c2c")):
    _, _, _, _, table = stats[name]
    big = [(v, n, o) for v, n, o in table if n >= MIN_CELL]
    small = [(v, n, o) for v, n, o in table if n < MIN_CELL]
    ax.plot([t[0] for t in big], [t[2] for t in big], "-", color=col,
            lw=1.1, alpha=0.6, zorder=2)
    ax.scatter([t[0] for t in big], [t[2] for t in big],
               s=[8 + t[1] * 0.55 for t in big], color=col, zorder=3,
               label=name, alpha=0.9, edgecolors="none")
    ax.scatter([t[0] for t in small], [t[2] for t in small],
               s=[14 + t[1] * 0.55 for t in small], facecolors="none",
               edgecolors=col, lw=0.9, zorder=3, alpha=0.7)
box = []
for name in stats:
    b, rel, res, unc, _ = stats[name]
    box.append(f"{name}:  Brier {b:.3f} = REL {rel:.3f} − RES {res:.3f} + UNC {unc:.3f}")
ax.text(0.03, 0.97, "\n".join(box), transform=ax.transAxes, fontsize=8.8,
        va="top", ha="left", family="monospace",
        bbox=dict(boxstyle="round,pad=0.45", fc="#f6f4f0", ec="#cccccc", lw=0.6))
ax.set_xlabel("forecast probability")
ax.set_ylabel("realized frequency")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_title("Reliability diagram: the overconfident forecaster bends off the diagonal",
             fontsize=10.3)
ax.legend(frameon=False, fontsize=9, loc="lower right")
ax.grid(True, alpha=0.22)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.text(0.5, -0.02,
         f"{N_EVENTS} shared binary events, true p in {{0.2, 0.35, 0.5, 0.65, 0.8}}; "
         f"B multiplies log-odds by {OVERCONF:.0f}; forecasts on a 0.05 grid; "
         f"marker area ∝ n at that value; hollow = n<{MIN_CELL} (anecdote cells, "
         f"off the line). Seed {SEED}.",
         ha="center", fontsize=7.6, color="#666666")
plt.tight_layout()

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_reliability.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
for name in stats:
    b, rel, res, unc, _ = stats[name]
    print(f"{name}:  Brier={b:.4f}  REL={rel:.4f}  RES={res:.4f}  UNC={unc:.4f}  "
          f"identity check: REL-RES+UNC={rel - res + unc:.4f}")
print(f"base rate of events: {y.mean():.3f}")
