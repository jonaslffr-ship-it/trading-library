"""
Figure - The paper-to-reality haircut on a time-series-momentum replication.

Free data: daily S&P 500 (^GSPC) from Yahoo Finance's public chart API
(range=max, from 1927), cached to data/spx_daily_max.csv so the figure is
reproducible offline and stable. ONE pre-committed specification is scored
(frozen in the paper text BEFORE these results were computed):

  Signal   : at each month-end t, r12 = C[t]/C[t-12] - 1 on month-end closes.
             Long (+1) if r12 > 0, short (-1) otherwise.  (Moskowitz-Ooi-
             Pedersen 2012 sign rule, single asset, no vol scaling.)
  Step (i) : paper-faithful gross - position in force for every trading day
             of month t+1, no costs.
  Step (ii): + transaction costs - 10 bps one-way per unit of turnover
             (a full flip long->short trades 2 units = 20 bps).
  Step(iii): + 1-day implementation lag - the new position is only in force
             from the close of the FIRST trading day after the month-end
             (the old position earns the gap day). Costs still applied.
  Step (iv): post-publication sub-period - step (iii) evaluated on months
             from 2012-01 onward (MOP published in JFE 2012).

Metrics: Sharpe (monthly returns, x sqrt(12)) and CAGR per step, plus
buy-and-hold on the identical window as the reference. Every quoted number
is printed. No parameter was tuned; the point is the ladder of haircuts,
not the strategy.

Reproducible:
    python fig_tsmom_haircut.py     # numpy, matplotlib; stdlib urllib/json
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
r = np.zeros(n)                                   # r[i]: close[i-1] -> close[i]
r[1:] = close[1:] / close[:-1] - 1.0
month = [d[:7] for d in dates]

# month-end indices (last trading day of each calendar month)
me = [i for i in range(n - 1) if month[i] != month[i + 1]]  # exclude running month? keep last full
me.append(n - 1)                                  # treat final day as last month-end
me = np.array(me)

LOOKBACK = 12
# signal decided at month-end me[j], defined from j >= LOOKBACK
sig = np.zeros(len(me))
valid = np.zeros(len(me), dtype=bool)
for j in range(LOOKBACK, len(me)):
    r12 = close[me[j]] / close[me[j - LOOKBACK]] - 1.0
    sig[j] = 1.0 if r12 > 0 else -1.0
    valid[j] = True
first_j = LOOKBACK                                # first month-end with a signal


def daily_position(lag):
    """pos[i] = position in force for return day i (held from close i-1 to close i).
    Signal from month-end me[j] is in force for return days i with me[j] + lag <= i - 1."""
    pos = np.zeros(n)
    for j in range(first_j, len(me)):
        start = me[j] + lag + 1                   # first return day earning sig[j]
        end = me[j + 1] + lag + 1 if j + 1 < len(me) else n
        if start >= n:
            break
        pos[start:min(end, n)] = sig[j]
    return pos


def monthly_agg(x, start_i):
    """compound daily returns x into calendar-month returns, from index start_i."""
    out, keys = [], []
    cur_m, acc = None, 1.0
    for i in range(start_i, n):
        m = month[i]
        if cur_m is None:
            cur_m = m
        if m != cur_m:
            out.append(acc - 1.0); keys.append(cur_m)
            cur_m, acc = m, 1.0
        acc *= (1.0 + x[i])
    out.append(acc - 1.0); keys.append(cur_m)
    return keys, np.array(out)


def stats(mr):
    s = mr.std()
    sh = (mr.mean() / s) * np.sqrt(12.0) if s > 0 else 0.0
    growth = np.prod(1.0 + mr)
    cagr = growth ** (12.0 / len(mr)) - 1.0
    return sh, cagr


COST_BPS = 10.0
start_i = me[first_j] + 1                          # first day the strategy can be in the market

def strategy(lag, cost_bps):
    pos = daily_position(lag)
    dpos = np.abs(np.diff(np.concatenate([[0.0], pos])))
    ret = pos * r - (cost_bps / 1e4) * dpos
    return monthly_agg(ret, start_i)

keys_g, m_gross = strategy(0, 0.0)                 # (i)  paper-faithful gross
keys_c, m_cost = strategy(0, COST_BPS)             # (ii) + costs
keys_l, m_lag = strategy(1, COST_BPS)              # (iii)+ 1-day lag
post_mask = np.array([k >= "2012-01" for k in keys_l])
m_post = m_lag[post_mask]                          # (iv) post-publication, net+lag
keys_bh, m_bh = monthly_agg(r, start_i)            # buy-and-hold, identical window
m_bh_post = m_bh[np.array([k >= "2012-01" for k in keys_bh])]

sh_g, cagr_g = stats(m_gross)
sh_c, cagr_c = stats(m_cost)
sh_l, cagr_l = stats(m_lag)
sh_p, cagr_p = stats(m_post)
sh_bh, cagr_bh = stats(m_bh)
sh_bhp, cagr_bhp = stats(m_bh_post)

flips = np.abs(np.diff(sig[first_j:])).sum() / 2.0
years = len(m_gross) / 12.0
flips_py = flips / years

# ---- figure: cumulative wealth (log) + Sharpe ladder ----
fig, (axL, axR) = plt.subplots(
    1, 2, figsize=(9.6, 4.1), gridspec_kw={"width_ratios": [1.55, 1.0]})

x = np.arange(len(m_gross))
yrs = np.array([int(k[:4]) + (int(k[5:7]) - 0.5) / 12.0 for k in keys_g])
axL.plot(yrs, np.cumprod(1 + m_gross), color="#17120e", lw=1.5,
         label=f"(i) gross  SR {sh_g:.2f}")
axL.plot(yrs, np.cumprod(1 + m_cost), color="#2f6d4f", lw=1.3,
         label=f"(ii) +{COST_BPS:.0f} bps costs  SR {sh_c:.2f}")
axL.plot(yrs, np.cumprod(1 + m_lag), color="#7c1c2c", lw=1.3,
         label=f"(iii) +1-day lag  SR {sh_l:.2f}")
axL.plot(yrs, np.cumprod(1 + m_bh), color="#999999", lw=1.0, ls=":",
         label=f"buy & hold  SR {sh_bh:.2f}")
axL.axvline(2012.0, color="#8a6d3b", lw=1.0, ls="--")
axL.annotate("MOP published (2012)", xy=(2012.0, axL.get_ylim()[0]),
             xytext=(1979.5, 2e2), fontsize=8, color="#8a6d3b")
axL.set_yscale("log")
axL.set_xlabel("year")
axL.set_ylabel("growth of $1 (log scale)")
axL.set_title("12-month sign rule on the S&P 500: each realism step", fontsize=10)
axL.legend(fontsize=7.6, frameon=False, loc="upper left")
for s in ("top", "right"):
    axL.spines[s].set_visible(False)
axL.grid(True, axis="y", alpha=0.25)

labels = ["(i)\ngross", f"(ii)\n+costs", "(iii)\n+lag", "(iv)\npost-2012\nnet+lag"]
vals = [sh_g, sh_c, sh_l, sh_p]
cols = ["#17120e", "#2f6d4f", "#7c1c2c", "#8a6d3b"]
bars = axR.bar(labels, vals, color=cols, width=0.62)
axR.axhline(0, color="#999", lw=0.8)
axR.axhline(sh_bh, color="#999999", lw=1.0, ls=":")
axR.annotate(f"buy & hold {sh_bh:.2f} (full sample)",
             xy=(0.02, sh_bh + 0.012), fontsize=7.4, color="#777")
for b, v in zip(bars, vals):
    axR.annotate(f"{v:.2f}", xy=(b.get_x() + b.get_width() / 2, v),
                 xytext=(0, 4 if v >= 0 else -11), textcoords="offset points",
                 ha="center", fontsize=8.4)
axR.set_ylabel("annualized Sharpe ratio")
axR.set_title("The haircut ladder", fontsize=10)
for s in ("top", "right"):
    axR.spines[s].set_visible(False)
axR.grid(True, axis="y", alpha=0.25)
axR.tick_params(axis="x", labelsize=7.6)

fig.text(0.5, -0.03,
         f"Yahoo daily ^GSPC (range=max), {dates[0]} to {dates[-1]}, {n} sessions, "
         f"{len(m_gross)} strategy months. One frozen spec, no tuning; "
         f"~{flips_py:.1f} position flips/yr; costs {COST_BPS:.0f} bps one-way per unit turnover.",
         ha="center", fontsize=7.4, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_tsmom_haircut.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={dates[0]}..{dates[-1]} n_days={n} n_months={len(m_gross)} flips_per_year={flips_py:.2f}")
print(f"(i)   gross      : Sharpe={sh_g:.3f} CAGR={cagr_g*100:.2f}%")
print(f"(ii)  +costs     : Sharpe={sh_c:.3f} CAGR={cagr_c*100:.2f}%")
print(f"(iii) +lag       : Sharpe={sh_l:.3f} CAGR={cagr_l*100:.2f}%")
print(f"(iv)  post-2012  : Sharpe={sh_p:.3f} CAGR={cagr_p*100:.2f}%  n_months={post_mask.sum()}")
print(f"buy&hold full    : Sharpe={sh_bh:.3f} CAGR={cagr_bh*100:.2f}%")
print(f"buy&hold post-12 : Sharpe={sh_bhp:.3f} CAGR={cagr_bhp*100:.2f}%")
