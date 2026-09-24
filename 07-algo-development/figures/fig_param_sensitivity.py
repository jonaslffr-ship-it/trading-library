"""
Figure - Parameter instability: the momentum lookback that looks best
in-sample is not the one that wins out-of-sample.

Free data: daily S&P 500 (^GSPC) from Yahoo Finance's public chart API
(range=max), cached to data/spx_daily_max.csv (shared with the other figures
of this paper). The strategy is the identical frozen TSMOM sign rule of
fig_tsmom_haircut.py step (i) - at each month-end, long if the trailing
L-month return is positive, short otherwise; the position earns the next
month's return; gross, decision strictly before outcome - but now the
lookback L is swept over 3..18 months.

Pre-committed, transparent design (no strategy search, no cherry-picking):
  - Evaluation window: the calendar months available for the LONGEST
    lookback (L=18), so every L is scored on the identical set of months.
  - Split: that window is cut in half by count. First half = IN-SAMPLE
    (where one would "select" a lookback); second half = OUT-OF-SAMPLE.
  - For each L in 3..18: annualized Sharpe in-sample and out-of-sample.
  - The POINT (printed): the best in-sample L, and its RANK out-of-sample
    among the 16 candidates, plus the IS-vs-OOS rank correlation. The lesson
    is the instability, whatever the numbers are.

Reproducible:
    python fig_param_sensitivity.py   # numpy, matplotlib; stdlib urllib/json
"""
import os, json, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
CACHE = os.path.join(DATA, "spx_daily_max.csv")


def load_prices():
    if os.path.exists(CACHE):
        dates, close = [], []
        with open(CACHE) as f:
            for row in csv.DictReader(f):
                dates.append(row["date"]); close.append(float(row["close"]))
        return dates, np.array(close)
    socket.setdefaulttimeout(60)
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
           "?range=max&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    j = json.loads(urllib.request.urlopen(req).read())
    r = j["chart"]["result"][0]
    ts, cl = r["timestamp"], r["indicators"]["quote"][0]["close"]
    dates, close = [], []
    for t, c in zip(ts, cl):
        if c is None or c <= 0:
            continue
        dates.append(dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"))
        close.append(float(c))
    with open(CACHE, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "close"])
        for d, c in zip(dates, close):
            w.writerow([d, f"{c:.4f}"])
    return dates, np.array(close)


dates, close = load_prices()
n = len(close)
month = [d[:7] for d in dates]
me = [i for i in range(n - 1) if month[i] != month[i + 1]]
me.append(n - 1)
me = np.array(me)
C = close[me]                                       # month-end closes
mkeys = [month[i] for i in me]
mret = C[1:] / C[:-1] - 1.0                         # mret[j-1]: month j return

LOOKS = list(range(3, 19))                           # 3..18 months
LMAX = max(LOOKS)

ANN = np.sqrt(12.0)
def sharpe(x):
    x = np.asarray(x)
    s = x.std()
    return (x.mean() / s) * ANN if s > 0 else 0.0


def strat_by_month(L):
    """month-key -> gross monthly return for lookback L (decision strictly first)."""
    out = {}
    for j in range(L + 1, len(C)):
        r_l = C[j - 1] / C[j - 1 - L] - 1.0
        s = 1.0 if r_l > 0 else -1.0
        out[mkeys[j]] = s * mret[j - 1]
    return out


series = {L: strat_by_month(L) for L in LOOKS}
# common evaluation window = months present for the LONGEST lookback
common = [k for k in mkeys if k in series[LMAX]]
common.sort()
half = len(common) // 2
is_keys, oos_keys = common[:half], common[half:]

is_sh, oos_sh = {}, {}
for L in LOOKS:
    is_sh[L] = sharpe([series[L][k] for k in is_keys])
    oos_sh[L] = sharpe([series[L][k] for k in oos_keys])

best_is_L = max(LOOKS, key=lambda L: is_sh[L])
best_oos_L = max(LOOKS, key=lambda L: oos_sh[L])
# OOS rank of the best-in-sample lookback (1 = best out-of-sample)
oos_order = sorted(LOOKS, key=lambda L: oos_sh[L], reverse=True)
oos_rank_of_best_is = oos_order.index(best_is_L) + 1

# rank correlation (Spearman) between IS and OOS Sharpe across lookbacks
def rankvec(d):
    order = sorted(LOOKS, key=lambda L: d[L])
    rk = {L: i for i, L in enumerate(order)}
    return np.array([rk[L] for L in LOOKS], float)
ris, ros = rankvec(is_sh), rankvec(oos_sh)
rho = np.corrcoef(ris, ros)[0, 1]

# ---- figure ----
fig, ax = plt.subplots(figsize=(7.6, 4.2))
xs = np.array(LOOKS)
ax.plot(xs, [is_sh[L] for L in LOOKS], "-o", color="#17120e", lw=1.5, ms=4.5,
        label="in-sample (first half)")
ax.plot(xs, [oos_sh[L] for L in LOOKS], "-o", color="#7c1c2c", lw=1.5, ms=4.5,
        label="out-of-sample (second half)")
ax.axhline(0, color="#999", lw=0.8)
# mark the best in-sample lookback and where it lands OOS
ax.scatter([best_is_L], [is_sh[best_is_L]], s=120, facecolors="none",
           edgecolors="#17120e", lw=1.8, zorder=5)
ax.scatter([best_is_L], [oos_sh[best_is_L]], s=120, facecolors="none",
           edgecolors="#7c1c2c", lw=1.8, zorder=5)
ax.annotate(f"best in-sample: L={best_is_L} mo\n(SR {is_sh[best_is_L]:.2f})",
            xy=(best_is_L, is_sh[best_is_L]), xytext=(best_is_L + 0.3, is_sh[best_is_L] + 0.10),
            fontsize=8.2, color="#17120e")
ax.annotate(f"same L out-of-sample:\nrank {oos_rank_of_best_is} of {len(LOOKS)} (SR {oos_sh[best_is_L]:.2f})",
            xy=(best_is_L, oos_sh[best_is_L]),
            xytext=(best_is_L - 5.6, oos_sh[best_is_L] - 0.24),
            fontsize=8.2, color="#7c1c2c",
            arrowprops=dict(arrowstyle="->", color="#7c1c2c", lw=0.9))
ax.set_xlabel("momentum lookback L (months)")
ax.set_ylabel("annualized Sharpe ratio")
ax.set_title("The best in-sample lookback is not the best out-of-sample",
             fontsize=10.4)
ax.set_xticks(xs)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
ax.legend(fontsize=8.2, frameon=False, loc="upper right")
fig.text(0.5, -0.02,
         f"Yahoo daily ^GSPC (range=max), {dates[0]} to {dates[-1]}; TSMOM sign rule, gross, "
         f"decision strictly first; {len(common)} common months split in half "
         f"(IS n={len(is_keys)}, OOS n={len(oos_keys)}); IS-vs-OOS rank corr = {rho:.2f}.",
         ha="center", fontsize=7.4, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_param_sensitivity.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={dates[0]}..{dates[-1]} common_months={len(common)} "
      f"IS_n={len(is_keys)} OOS_n={len(oos_keys)}")
for L in LOOKS:
    tag = "  <- best IS" if L == best_is_L else ("  <- best OOS" if L == best_oos_L else "")
    print(f"  L={L:2d}mo  IS Sharpe={is_sh[L]:+.3f}  OOS Sharpe={oos_sh[L]:+.3f}{tag}")
print(f"best in-sample L={best_is_L}mo (IS {is_sh[best_is_L]:.3f}); "
      f"its OOS Sharpe={oos_sh[best_is_L]:.3f}, OOS rank {oos_rank_of_best_is}/{len(LOOKS)}")
print(f"best out-of-sample L={best_oos_L}mo (OOS {oos_sh[best_oos_L]:.3f})")
print(f"IS-vs-OOS Spearman rank corr across lookbacks = {rho:.3f}")
