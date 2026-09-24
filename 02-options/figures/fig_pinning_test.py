"""
Figure - pre-committed OPEX pinning test on free SPX daily closes.

The classic pinning result (Ni, Pearson & Poteshman 2005) is a SINGLE-STOCK,
physically-settled phenomenon: on expiration Fridays the underlying is pulled
toward the strike with the most open interest. SPX is cash-settled and cannot
be held, so the mechanism is far weaker or absent. This figure asks the
question honestly of the free data, with ONE rule fixed in advance - no grid
search, no threshold tuning.

Pre-committed design (frozen before the data were examined):
  - data: SPX daily closes (data/spx_daily.csv, Yahoo ^GSPC, 2011-2026);
  - grid: SPX listed-strike grid, multiples of 25 index points;
  - pinning distance d(t) = | close(t) - 25 * round(close(t)/25) |, in index
    points, bounded in [0, 12.5]; under NO pinning d is ~Uniform(0, 12.5) with
    expected value 6.25;
  - groups: monthly-OPEX Fridays (the third Friday of the month: a Friday whose
    day-of-month is 15-21) vs. all OTHER Fridays (the control);
  - directional hypothesis (sign committed in advance): if index pinning is
    real, mean d is LOWER on OPEX Fridays than on other Fridays;
  - test: Welch two-sample z on the means, one-sided (H1: OPEX < other);
    normal-approx p-value via math.erf. Report the number whatever it shows.

Reproducible:
    python fig_pinning_test.py     # numpy, matplotlib; stdlib csv/math/datetime
"""
import os, csv, math, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
GRID = 25.0                       # SPX round-strike spacing, fixed in advance
HALF = GRID / 2.0                 # 12.5: max distance, mean under no pinning


def read_csv(name):
    dates, close = [], []
    with open(os.path.join(DATA, name)) as f:
        for row in csv.DictReader(f):
            dates.append(row["date"]); close.append(float(row["close"]))
    return dates, np.array(close)


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


sd, sc = read_csv("spx_daily.csv")
is_fri, is_opex = [], []
for s in sd:
    d = dt.date.fromisoformat(s)
    fri = d.weekday() == 4
    is_fri.append(fri)
    is_opex.append(fri and 15 <= d.day <= 21)     # third Friday of the month
is_fri = np.array(is_fri); is_opex = np.array(is_opex)

dist = np.abs(sc - GRID * np.round(sc / GRID))     # index points, [0, 12.5]
opex = dist[is_opex]
other = dist[is_fri & ~is_opex]

n1, n2 = len(opex), len(other)
m1, m2 = opex.mean(), other.mean()
s1, s2 = opex.std(ddof=1), other.std(ddof=1)
se1, se2 = s1 / math.sqrt(n1), s2 / math.sqrt(n2)
diff = m1 - m2
se_diff = math.sqrt(se1 ** 2 + se2 ** 2)
z = diff / se_diff
p_one = norm_cdf(z)               # one-sided: P(OPEX mean < other mean)

fig, ax = plt.subplots(figsize=(6.4, 4.1))
labels = [f"OPEX Fridays\n(n={n1})", f"other Fridays\n(n={n2})"]
means = [m1, m2]
errs = [1.96 * se1, 1.96 * se2]
colors = ["#b0713a", "#17120e"]
ax.bar([0, 1], means, 0.55, color=colors, alpha=0.9,
       yerr=errs, capsize=4, error_kw=dict(lw=1.0, ecolor="#666"))
ax.axhline(HALF / 2, color="#2a5d8f", lw=1.1, ls="--")
ax.annotate("no-pinning expectation 6.25\n(uniform over the $25 grid)",
            xy=(1.35, HALF / 2), fontsize=8.2, color="#2a5d8f", va="center")
for xi, mv in zip([0, 1], means):
    ax.text(xi, mv + 0.12, f"{mv:.2f}", ha="center", fontsize=9.5, color="#17120e")
ax.set_xticks([0, 1]); ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel("mean distance of close to nearest 25-strike (index pts)")
ax.set_ylim(0, 7.2)
ax.set_title("Pre-committed OPEX pinning test on cash-settled SPX", fontsize=10.4)
for s_ in ("top", "right"):
    ax.spines[s_].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.02,
         f"Yahoo ^GSPC daily closes {sd[0]} to {sd[-1]}; one fixed rule (25-pt "
         f"grid, third-Friday OPEX). One-sided Welch z={z:+.2f}, p={p_one:.3f} "
         f"for H1: OPEX distance < other. Error bars 95% CI.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_pinning_test.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={sd[0]}..{sd[-1]} n_fridays={int(is_fri.sum())} "
      f"n_opex={n1} n_other={n2}")
print(f"mean_dist_opex={m1:.3f}  mean_dist_other={m2:.3f}  "
      f"no_pin_expectation={HALF/2:.3f}")
print(f"median_opex={np.median(opex):.3f}  median_other={np.median(other):.3f}")
print(f"diff(opex-other)={diff:+.3f}  se_diff={se_diff:.3f}  "
      f"z={z:+.3f}  p_one_sided(OPEX<other)={p_one:.4f}")
