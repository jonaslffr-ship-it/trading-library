"""
Figure - A health monitor catching a decaying edge (rolling expectancy + CUSUM).

Didactic, fully simulated (no market data). The strategy has a symmetric +1R /
-1R payoff (target equals stop), so its edge lives entirely in the hit rate: a
60% hit rate for the first 700 trades gives expectancy +0.20 R per trade; then,
at a known CHANGEPOINT, the hit rate decays over 100 trades to 40% and stays
there, flipping the edge to an equal-and-opposite -0.20 R bleed.

Two monitors run on the live R-stream, both fixed in advance:
  * a 100-trade rolling expectancy (the human-readable line - noisy and slow);
  * a one-sided lower CUSUM on the STANDARDIZED result z_t = (x_t - mu0)/sigma0,
    with in-control mean mu0 = 0.20 R and in-control sd sigma0 ~ 0.98 R. The
    reference k = 0.20 sigma is half the standardized shift to be detected and
    the threshold h = 14 sigma targets an in-control run length near 3300; both are
    fixed BEFORE the run, not tuned to the outcome. The detection lag reported
    is whatever those fixed settings give.

Even with a clean ~0.4 sigma shift the honest lesson stands: a correct monitor
still needs dozens of trades of a dead edge before it can be sure, which is why
retirement criteria must be pre-committed rather than reacted to.

Reproducible:
    python fig_monitoring.py     # numpy, matplotlib only
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

T = 1400
CP = 700                 # changepoint (edge starts decaying here)
DECAY = 100              # trades over which the edge fades
MU0, MU1 = 0.20, -0.20   # in-control and post-decay expectancy (R)
WIN_R, LOSS_R = 1.0, -1.0   # symmetric payoff: edge is in the hit rate
WIN = 100                # rolling-expectancy window
K = 0.20                 # CUSUM reference in sigma units (fixed in advance)
H = 14.0                 # CUSUM threshold in sigma units (in-control ARL ~3300)

# in-control sd of the R-distribution (analytic, from MU0)
P0 = (MU0 - LOSS_R) / (WIN_R - LOSS_R)
SIGMA0 = np.sqrt(P0 * (WIN_R - MU0) ** 2 + (1 - P0) * (LOSS_R - MU0) ** 2)

t = np.arange(T)
mu = np.where(t < CP, MU0,
              np.where(t < CP + DECAY,
                       MU0 + (MU1 - MU0) * (t - CP) / DECAY, MU1))
p = (mu - LOSS_R) / (WIN_R - LOSS_R)


def cusum_alarm(x):
    """Standardized one-sided lower CUSUM; return statistic and first alarm."""
    z = (x - MU0) / SIGMA0
    c = np.zeros(len(x) + 1)
    alarm = None
    for i in range(len(x)):
        c[i + 1] = max(0.0, c[i] + (-z[i] - K))   # grows when x_i < mu0
        if alarm is None and c[i + 1] > H:
            alarm = i
    return c[1:], alarm


# --- one illustrated path (seed 42) ---
rng = np.random.default_rng(42)
r = np.where(rng.random(T) < p, WIN_R, LOSS_R).astype(float)
roll = np.convolve(r, np.ones(WIN) / WIN, mode="valid")
roll_x = np.arange(WIN - 1, T)
cstat, alarm = cusum_alarm(r)
lag = None if alarm is None else alarm - CP

# --- median lag and false-alarm rate over many independent paths ---
M = 5000
rng2 = np.random.default_rng(7)
lags, false_alarms, detected = [], 0, 0
for _ in range(M):
    rr = np.where(rng2.random(T) < p, WIN_R, LOSS_R).astype(float)
    _, a = cusum_alarm(rr)
    if a is None:
        continue
    if a < CP:
        false_alarms += 1
    else:
        detected += 1
        lags.append(a - CP)
med_lag = int(np.median(lags)) if lags else None
p90_lag = int(np.percentile(lags, 90)) if lags else None

fig, axes = plt.subplots(2, 1, figsize=(9.2, 5.2), sharex=True)
ax = axes[0]
ax.plot(roll_x, roll, color="#17120e", lw=1.4, label=f"{WIN}-trade rolling expectancy")
ax.plot(t, mu, color="#2f6d4f", lw=1.5, ls="--", label="true expectancy (hidden)")
ax.axhline(0, color="#999", lw=0.8)
ax.axvline(CP, color="#666", lw=1.0, ls=":")
ax.annotate("edge starts\ndecaying", xy=(CP, MU0), xytext=(CP - 240, MU0 + 0.30),
            fontsize=8, color="#666")
if alarm is not None:
    ax.axvline(alarm, color="#7c1c2c", lw=1.2)
ax.set_ylabel("expectancy (R/trade)")
ax.set_title("Rolling expectancy is noisy and slow", fontsize=10)
ax.legend(fontsize=8, frameon=False, loc="upper right")
ax = axes[1]
ax.plot(t, cstat, color="#17120e", lw=1.4, label="standardized lower CUSUM")
ax.axhline(H, color="#7c1c2c", lw=1.2, ls="--", label=f"alarm threshold h = {H:g}")
ax.axvline(CP, color="#666", lw=1.0, ls=":")
if alarm is not None:
    ax.axvline(alarm, color="#7c1c2c", lw=1.2)
    ax.annotate(f"alarm at trade {alarm}\nlag = {lag} trades",
                xy=(alarm, H), xytext=(alarm + 25, H + 0.6),
                fontsize=8, color="#7c1c2c")
ax.set_xlabel("trade number")
ax.set_ylabel("CUSUM (sigma)")
ax.set_title("CUSUM crosses its pre-set line and fires", fontsize=10)
ax.legend(fontsize=8, frameon=False, loc="upper left")
for ax in axes:
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", alpha=0.22)
fig.text(0.5, -0.02,
         f"Simulated: expectancy {MU0:+.2f} R -> {MU1:+.2f} R after trade {CP}; "
         f"CUSUM k = {K:g}, h = {H:g} (sigma units), fixed in advance; sigma0 = {SIGMA0:.2f} R; seed 42.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_monitoring.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"in-control sigma0 = {SIGMA0:.3f} R; shift to detect = {(MU0-MU1)/SIGMA0:.2f} sigma")
print(f"changepoint at trade {CP}")
print(f"illustrated path (seed 42): alarm at trade {alarm}, detection lag = {lag} trades")
print(f"over {M} paths: median lag = {med_lag} trades, p90 lag = {p90_lag}; "
      f"detected after CP {detected/M*100:.1f}%, false alarm before CP {false_alarms/M*100:.1f}%")
