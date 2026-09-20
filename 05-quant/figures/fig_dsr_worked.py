"""
Figure 2 (C3) - The Deflated Sharpe Ratio applied to a best-of-20 selection.

A simulation that mirrors the STRUCTURE of the C2 case study (a gate parameter
chosen as the best of ~20 variants on a ~4-year sample), with the truth known:
all 20 variants have ZERO true edge and are 50%-correlated (they share most of
their trades, as gate variants do). The best variant is selected by in-sample
Sharpe; the naive PSR treats it as a single pre-registered trial, the DSR
deflates it by the expected maximum of 20 correlated noise trials (Bailey &
Lopez de Prado 2014). Same number, different history, different verdict.

Reproducible:
    python fig_dsr_worked.py           # needs numpy, matplotlib; seed 42

Free data only: pure simulation (no market data required).
"""
import os
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
T = 1005          # ~4 years of daily P&L observations (2022-09..2026-09 shape)
N = 20            # variants tried
RHO = 0.5         # correlation between variants (shared trades)
ANN = math.sqrt(252.0)
EULER = 0.5772156649015329

rng = np.random.default_rng(SEED)


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(p):
    """Acklam's rational approximation to the inverse normal CDF (|err| < 1e-9)."""
    a = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00)
    if p < 0.02425:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > 1 - 0.02425:
        return -norm_ppf(1 - p)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def psr(sr_hat, sr_star, t, skew, kurt):
    """Probabilistic Sharpe Ratio: P(true SR > sr_star). Per-period units."""
    den = math.sqrt(max(1e-12, 1.0 - skew * sr_hat + (kurt - 1.0) / 4.0 * sr_hat ** 2))
    return norm_cdf((sr_hat - sr_star) * math.sqrt(t - 1.0) / den)


def expected_max_sr(n_trials, var_trials):
    """E[max of n_trials zero-mean SR estimates], Bailey & Lopez de Prado (2014)."""
    return math.sqrt(var_trials) * ((1 - EULER) * norm_ppf(1 - 1.0 / n_trials)
                                    + EULER * norm_ppf(1 - 1.0 / (n_trials * math.e)))


# --- simulate 20 correlated zero-edge variants with a negatively skewed factor
z = rng.normal(size=T)
shock = rng.random(T) < 0.015
f = np.where(shock, z - 4.0, z)                 # common market-shock factor
f = (f - f.mean()) / f.std()
e = rng.normal(size=(T, N))
r = 0.01 * (math.sqrt(RHO) * f[:, None] + math.sqrt(1 - RHO) * e)   # zero true edge

sr_all = r.mean(axis=0) / r.std(axis=0, ddof=1)  # per-period SR estimates
i_star = int(np.argmax(sr_all))
x = r[:, i_star]
sr_hat = float(sr_all[i_star])
skew = float(((x - x.mean()) ** 3).mean() / x.std() ** 3)
kurt = float(((x - x.mean()) ** 4).mean() / x.std() ** 4)
pf = float(x[x > 0].sum() / -x[x < 0].sum())

v_trials = float(np.var(sr_all, ddof=1))
sr_star = expected_max_sr(N, v_trials)
psr_naive = psr(sr_hat, 0.0, T, skew, kurt)      # as if it were 1 pre-registered trial
dsr = psr(sr_hat, sr_star, T, skew, kurt)        # deflated for 20 trials

# minimum SR that would clear DSR = 0.95 with these moments / N / T
sr_need = sr_hat
for _ in range(50):
    den = math.sqrt(1.0 - skew * sr_need + (kurt - 1.0) / 4.0 * sr_need ** 2)
    sr_need = sr_star + norm_ppf(0.95) * den / math.sqrt(T - 1.0)

# --- figure: the 20 trials, the selection, and the null distribution of the max
null_max = (rng.normal(0.0, math.sqrt(v_trials), size=(20000, N))).max(axis=1) * ANN

fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.9))
ax = axes[0]
order = np.argsort(sr_all)
ax.plot(np.arange(1, N + 1), sr_all[order] * ANN, "o", ms=5, color="#17120e")
sel_rank = int(np.where(order == i_star)[0][0]) + 1
ax.plot(sel_rank, sr_hat * ANN, "o", ms=7.5, color="#7c1c2c")
ax.annotate(f"selected: SR {sr_hat * ANN:.2f} (ann.)", xy=(sel_rank, sr_hat * ANN),
            xytext=(11.8, 0.22), fontsize=9, color="#7c1c2c",
            arrowprops=dict(arrowstyle="->", color="#7c1c2c", lw=0.8))
ax.axhline(sr_star * ANN, color="#8a6d3b", lw=1.2, ls="--")
ax.annotate(f"expected max of 20 noise trials: {sr_star * ANN:.2f}",
            xy=(1.0, sr_star * ANN), xytext=(0.7, sr_star * ANN - 0.17),
            fontsize=8.6, color="#8a6d3b")
ax.axhline(0, color="#999999", lw=0.6)
ax.set_xlabel("variant (sorted by in-sample Sharpe)")
ax.set_ylabel("annualized Sharpe ratio")
ax.set_title("20 zero-edge variants and the one that gets published", fontsize=9.9)

ax = axes[1]
ax.hist(null_max, bins=60, color="#c9c2b8", edgecolor="none", density=True)
ax.axvline(sr_hat * ANN, color="#7c1c2c", lw=1.6)
ax.annotate(f"observed max {sr_hat * ANN:.2f}", xy=(sr_hat * ANN + 0.01, 1.30),
            xytext=(sr_hat * ANN + 0.55, 1.58), fontsize=9, color="#7c1c2c",
            arrowprops=dict(arrowstyle="->", color="#7c1c2c", lw=0.8))
ax.axvline(sr_star * ANN, color="#8a6d3b", lw=1.2, ls="--")
ax.set_xlabel("max annualized Sharpe of 20 zero-edge trials (null distribution)")
ax.set_ylabel("density")
ax.set_title(f"naive PSR {psr_naive:.2f}  vs.  DSR {dsr:.2f}", fontsize=9.9)
for a in axes:
    a.grid(True, axis="y", alpha=0.22)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
fig.text(0.5, -0.03,
         f"T={T} daily P&L obs (~4y), N={N} variants, pairwise corr {RHO}, zero true edge; "
         f"selected variant: skew {skew:.2f}, kurtosis {kurt:.1f}, gross PF {pf:.2f}. "
         f"Seed {SEED}, 20,000 null draws.",
         ha="center", fontsize=7.6, color="#666666")
plt.tight_layout()

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_dsr_worked.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"selected variant: ann SR={sr_hat * ANN:.3f}  PF={pf:.3f}  skew={skew:.3f}  kurt={kurt:.2f}")
print(f"trials N={N}  sqrt(V[SR]) ann={math.sqrt(v_trials) * ANN:.3f}  "
      f"SR* (expected max) ann={sr_star * ANN:.3f}")
print(f"PSR (naive, benchmark 0) = {psr_naive:.4f}")
print(f"DSR (deflated, N={N})    = {dsr:.4f}")
print(f"ann SR needed for DSR>=0.95 at N={N}, T={T}: {sr_need * ANN:.3f}")
print("verdict:", "DISCOVERY (DSR >= 0.95)" if dsr >= 0.95 else
      "NOT a discovery - consistent with the best of 20 noise trials")
