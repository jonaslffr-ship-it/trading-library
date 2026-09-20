"""
Figure 3 (C3) - Probability of Backtest Overfitting via CSCV.

Combinatorially symmetric cross-validation (Bailey, Borwein, Lopez de Prado &
Zhu 2017) on seeded strategy batteries of N=50 daily return series
(T=1248, mildly correlated through a common factor):

  A) all 50 strategies have zero true edge (pure noise battery);
  B) the same battery, but strategy 0 gets a true annualized Sharpe of 1.0
     (an edge that is REAL but drowns among 49 noise competitors);
  C) the same battery, strategy 0 with a true annualized Sharpe of 2.0
     (an edge strong enough for the selection process to find it).

The sample is cut into S=16 equal blocks; for each of the C(16,8)=12,870
half/half splits the in-sample-best strategy is found and its OUT-of-sample
relative rank among all 50 is recorded as a logit. PBO = share of splits in
which the in-sample winner ends at or below the out-of-sample median.

Reproducible:
    python fig_pbo_cscv.py             # needs numpy, matplotlib; seed 42

Free data only: pure simulation (no market data required).
"""
import os
import math
import itertools
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
T, N, S = 1248, 50, 16            # 16 blocks x 78 days
RHO = 0.3                          # common-factor correlation between strategies

rng = np.random.default_rng(SEED)
f = rng.normal(size=T)
e = rng.normal(size=(T, N))
noise = 0.01 * (math.sqrt(RHO) * f[:, None] + math.sqrt(1 - RHO) * e)


def with_edge(sr_ann):
    edge = np.zeros((T, N))
    edge[:, 0] = 0.01 * sr_ann / math.sqrt(252.0)    # daily mean for given ann SR
    return noise + edge


BATTERIES = {"A: 50 x zero edge": noise,
             "B: + one true SR 1.0": with_edge(1.0),
             "C: + one true SR 2.0": with_edge(2.0)}


def pbo_cscv(returns, s_blocks):
    """PBO via CSCV. Returns (pbo, logits, sel_counts, oos_sr_of_selected)."""
    t, n = returns.shape
    b = t // s_blocks
    r = returns[:b * s_blocks].reshape(s_blocks, b, n)
    bs, bq = r.sum(axis=1), (r ** 2).sum(axis=1)      # per-block sum / sum of squares
    half = s_blocks // 2
    n_half = half * b
    tot_s, tot_q = bs.sum(axis=0), bq.sum(axis=0)
    logits, sel, oos_sr_sel = [], np.zeros(n, dtype=int), []
    for combo in itertools.combinations(range(s_blocks), half):
        idx = list(combo)
        s1, q1 = bs[idx].sum(axis=0), bq[idx].sum(axis=0)
        s2, q2 = tot_s - s1, tot_q - q1
        m1, m2 = s1 / n_half, s2 / n_half
        v1 = (q1 - n_half * m1 ** 2) / (n_half - 1)
        v2 = (q2 - n_half * m2 ** 2) / (n_half - 1)
        sr1, sr2 = m1 / np.sqrt(v1), m2 / np.sqrt(v2)
        j = int(np.argmax(sr1))
        sel[j] += 1
        oos_sr_sel.append(sr2[j])
        rank = int((sr2 < sr2[j]).sum()) + 1          # 1 = worst OOS
        w = rank / (n + 1.0)
        logits.append(math.log(w / (1.0 - w)))
    logits = np.array(logits)
    return float((logits <= 0).mean()), logits, sel, np.array(oos_sr_sel)


fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.7), sharey=True)
results = {}
for ax, (name, r), col in zip(axes, BATTERIES.items(),
                              ("#7c1c2c", "#8a6d3b", "#2f6d4f")):
    pbo, logits, sel, oos_sr = pbo_cscv(r, S)
    results[name] = (pbo, sel, oos_sr)
    ax.hist(logits, bins=41, color=col, alpha=0.75, edgecolor="none", density=True)
    ax.axvline(0, color="#17120e", lw=1.0, ls="--")
    ax.set_title(f"{name}\nPBO = {pbo:.2f}", fontsize=9.6)
    ax.set_xlabel("OOS rank of IS winner (logit)", fontsize=8.6)
    ax.grid(True, axis="y", alpha=0.22)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
axes[0].set_ylabel("density")
fig.suptitle("CSCV: where does the in-sample winner land out of sample?",
             fontsize=10.6, y=1.00)
fig.text(0.5, -0.03,
         f"N={N} daily strategies, T={T} (~5y), common-factor corr {RHO}; S={S} blocks, "
         f"C(16,8)=12,870 symmetric splits; logit<0 = IS winner below OOS median. Seed {SEED}.",
         ha="center", fontsize=7.6, color="#666666")
plt.tight_layout()

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_pbo_cscv.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
for name, (pbo, sel, oos_sr) in results.items():
    top = int(np.argmax(sel))
    print(f"{name}:  PBO={pbo:.3f}  most-selected strategy #{top} "
          f"({sel[top] / sel.sum():.1%} of splits)  "
          f"injected #0 selected in {sel[0] / sel.sum():.1%} of splits  "
          f"mean OOS ann SR of IS winner={oos_sr.mean() * math.sqrt(252):.2f}")
