"""
Figure 2 (G3) - The validation gate: why the best of many models is a lie.

When you search over many model configurations and keep the best in-sample
Sharpe, you are guaranteed a good-looking number even if NONE of the models has
any real edge - because the maximum of many noisy estimates is large by chance.
This is the multiple-testing problem, and it is the reason a machine-learning
search needs a deflation step (the Deflated Sharpe Ratio, DSR) before any result
is believed.

We demonstrate it on real S&P 500 returns with strategies that have NO edge by
construction: each "model" is a random daily long/short signal (a fair coin),
scored on the same in-sample S&P 500 returns. We run M such trials, keep the
best in-sample Sharpe, and then show (a) the distribution of best-in-sample
Sharpe you can manufacture from pure noise, against the naive single-test
significance line and the expected maximum under the null, and (b) that the
in-sample Sharpe of a config tells you essentially nothing about its
out-of-sample Sharpe.

Free data: ^GSPC daily closes (cached).

Reproducible:
    python fig_g3_dsr.py     # numpy, matplotlib; stdlib
"""
import os, csv, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OOS_START = "2018-01-01"
M = 2000
rng = np.random.default_rng(1)


def load(cache):
    d, c = [], []
    with open(os.path.join(DATA, cache)) as f:
        for row in csv.DictReader(f):
            d.append(row["date"]); c.append(float(row["close"]))
    return d, np.array(c)


dates, close = load("gspc_daily.csv")
r = np.concatenate([[0.0], np.diff(np.log(close))])
split = next(k for k, dd in enumerate(dates) if dd >= OOS_START)
r_in, r_oos = r[1:split], r[split:]
n_in = len(r_in)


def sharpe(sig, ret):
    s = sig * ret
    return s.mean() / s.std() * math.sqrt(252) if s.std() > 0 else 0.0


sr_in = np.empty(M); sr_oos = np.empty(M)
for m in range(M):
    sig = rng.choice([-1.0, 1.0], size=len(r) - 1)
    sr_in[m] = sharpe(sig[:split - 1], r_in)
    sr_oos[m] = sharpe(sig[split - 1:], r_oos)

best = int(np.argmax(sr_in))
# expected maximum of M ~N(0, sd) in-sample Sharpes under the null.
# The crude leading-order sd*sqrt(2 ln M) overstates the maximum for finite M;
# use the Bailey-Lopez de Prado (2014) estimate -- the same estimator the
# deflated-Sharpe library in the overfitting-control paper uses -- accurate to ~1%.
from statistics import NormalDist
_zppf = NormalDist().inv_cdf
_euler = 0.5772156649015329
sd_null = math.sqrt(252.0 / n_in)                     # sd of an annualized Sharpe under no edge
exp_max = (sd_null * ((1 - _euler) * _zppf(1 - 1.0 / M)
                      + _euler * _zppf(1 - 1.0 / (M * math.e)))) if M > 1 else 0.0
naive_95 = 1.645 * sd_null                            # one-sided 5% single-test line

print(f"in-sample days={n_in}, OOS days={len(r_oos)}, trials M={M}")
print(f"best in-sample Sharpe = {sr_in[best]:.2f}  ->  its OUT-of-sample Sharpe = {sr_oos[best]:.2f}")
print(f"naive single-test 5% line = {naive_95:.2f}   expected max under null (M trials) = {exp_max:.2f}")
print(f"corr(in-sample, OOS Sharpe) across trials = {np.corrcoef(sr_in, sr_oos)[0,1]:+.3f}")
print(f"fraction of trials beating the naive line in-sample = {100*(sr_in>naive_95).mean():.0f}%")

# ---------------- figure ------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.8, 3.9))

ax1.hist(sr_in, bins=44, color="#8a8f98", alpha=0.85, edgecolor="white", linewidth=0.3)
ax1.axvline(naive_95, color="#2f6d4f", lw=1.6, ls="--", label=f"naive 5% line ({naive_95:.2f})")
ax1.axvline(exp_max, color="#c2571f", lw=1.6, label=f"expected max, M={M} ({exp_max:.2f})")
ax1.axvline(sr_in[best], color="#7c1c2c", lw=1.8, label=f"best of M ({sr_in[best]:.2f})")
ax1.set_xlabel("in-sample Sharpe (no-edge random strategies)", fontsize=8.6)
ax1.set_ylabel("number of trials", fontsize=8.6)
ax1.set_title("(a)  Pure noise manufactures a 'winner'", fontsize=9.5, loc="left")
ax1.legend(fontsize=7.2, frameon=False)
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)

ax2.scatter(sr_in, sr_oos, s=7, color="#31536e", alpha=0.35, edgecolors="none")
ax2.scatter([sr_in[best]], [sr_oos[best]], s=60, color="#7c1c2c", zorder=5,
            label=f"best in-sample -> OOS {sr_oos[best]:+.2f}")
ax2.axhline(0, color="#666", lw=0.6); ax2.axvline(0, color="#666", lw=0.6)
ax2.set_xlabel("in-sample Sharpe", fontsize=8.6)
ax2.set_ylabel("out-of-sample Sharpe", fontsize=8.6)
ax2.set_title(f"(b)  In-sample tells you nothing (corr {np.corrcoef(sr_in, sr_oos)[0,1]:+.2f})",
              fontsize=9.5, loc="left")
ax2.legend(fontsize=7.4, frameon=False, loc="upper left")
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
ax2.grid(True, alpha=0.2)

fig.text(0.5, -0.02,
         f"{M} random long/short strategies (no edge by construction) on Yahoo ^GSPC daily, "
         f"in-sample to {OOS_START}. The best in-sample Sharpe is an artefact of the search, not a signal. (Emp)",
         ha="center", fontsize=7.5, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_g3_dsr.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
