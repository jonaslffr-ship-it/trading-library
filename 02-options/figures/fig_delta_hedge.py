"""
Figure 2 - Delta-hedging a short SPX call, step by step, on one real month.

Free data: daily S&P 500 closes (Yahoo ^GSPC, cached to data/spx_daily.csv) and
the CBOE VIX index from FRED (VIXCLS, cached to data/vixcls.csv; Yahoo ^VIX as
fallback). ONE pre-committed rule, fixed before looking at the outcome:

  * the trade window is the most recent 21 completed sessions in the cache;
  * at the first session (t0) a 1-month ATM call is sold: strike = spot at t0
    rounded to the nearest 5 index points (the SPX listing increment), expiry =
    the 21st session, T = 20/252;
  * sigma = VIXCLS at t0 / 100 (implied-vol proxy), r = 4%, q = 0, multiplier 100;
  * the short call is delta-hedged long shares at five pre-committed weekly
    rebalances: sessions 0, 5, 10, 15 and settlement at session 20;
  * interest on the premium and hedge cash is ignored (flagged in the text).

The full rebalance table (spot, delta, shares traded, cumulative P&L
decomposition) is printed and quoted verbatim in the paper.

Reproducible:
    python fig_delta_hedge.py     # numpy, matplotlib, stdlib urllib/csv/math
"""
import os, csv, math, socket, json, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
SPX_CACHE = os.path.join(DATA, "spx_daily.csv")
VIX_CACHE = os.path.join(DATA, "vixcls.csv")

SQRT2PI = math.sqrt(2.0 * math.pi)


def npdf(x):
    return math.exp(-0.5 * x * x) / SQRT2PI


def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bsm_call(S, K, T, r, sig):
    if T <= 0:
        return max(S - K, 0.0), (1.0 if S > K else 0.0)
    d1 = (math.log(S / K) + (r + 0.5 * sig ** 2) * T) / (sig * math.sqrt(T))
    d2 = d1 - sig * math.sqrt(T)
    return S * ncdf(d1) - K * math.exp(-r * T) * ncdf(d2), ncdf(d1)


def load_spx():
    dates, close = [], []
    with open(SPX_CACHE) as f:
        for row in csv.DictReader(f):
            dates.append(row["date"]); close.append(float(row["close"]))
    return dates, np.array(close)


def load_vix():
    if os.path.exists(VIX_CACHE):
        out = {}
        with open(VIX_CACHE) as f:
            for row in csv.DictReader(f):
                out[row["date"]] = float(row["vix"])
        return out
    socket.setdefaulttimeout(30)
    out = {}
    try:  # FRED first
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        txt = urllib.request.urlopen(req).read().decode()
        for line in txt.splitlines()[1:]:
            d, v = line.split(",")
            if v not in (".", ""):
                out[d] = float(v)
    except Exception:  # Yahoo fallback
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?range=2y&interval=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        j = json.loads(urllib.request.urlopen(req).read())
        r = j["chart"]["result"][0]
        for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]):
            if c is not None:
                out[dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")] = float(c)
    with open(VIX_CACHE, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "vix"])
        for d in sorted(out):
            w.writerow([d, f"{out[d]:.2f}"])
    return out


dates, close = load_spx()
vix = load_vix()

# --- pre-committed window: most recent 21 completed sessions ---
d21, s21 = dates[-21:], close[-21:]
t0_date, S0 = d21[0], s21[0]
K = 5.0 * round(S0 / 5.0)                      # nearest 5 pts (SPX increment)
SIG = vix[t0_date] / 100.0                     # implied proxy: VIXCLS at t0
R, MULT = 0.04, 100.0
REB = [0, 5, 10, 15, 20]                       # weekly rebalances, fixed

prem0, _ = bsm_call(S0, K, 20 / 252, R, SIG)

rows = []                      # the printed rebalance table
shares = 0.0                   # index units held (delta * MULT)
hedge_pnl = 0.0                # cumulative hedge-leg P&L ($)
prev_S = S0
prev_V = prem0
opt_pnl = 0.0                  # cumulative option-leg P&L for the short ($)
net_path = []                  # (session idx, net hedged, net naked)
for i in REB:
    S, T = s21[i], (20 - i) / 252
    V, delta = bsm_call(S, K, T, R, SIG)
    hedge_pnl += shares * (S - prev_S)
    opt_pnl = -(V - prem0) * MULT
    target = delta * MULT if i < 20 else 0.0
    traded = target - shares
    rows.append((d21[i], S, 20 - i, V, delta, target, traded,
                 hedge_pnl, opt_pnl, hedge_pnl + opt_pnl))
    shares = target
    prev_S = S
    net_path.append((i, hedge_pnl + opt_pnl, -(V - prem0) * MULT))

hedged_final = rows[-1][9]
naked_final = rows[-1][8] * 0 + rows[-1][8]  # placeholder, recompute below
naked_final = -(max(s21[20] - K, 0.0) - prem0) * MULT

hdr = f"{'session':10s} {'spot':>9s} {'days':>4s} {'call':>8s} {'delta':>6s} {'held':>7s} {'traded':>8s} {'hedgePnL':>9s} {'optPnL':>9s} {'netPnL':>9s}"
print(hdr)
for d, S, days, V, delta, held, traded, hp, op, np_ in rows:
    print(f"{d:10s} {S:9.2f} {days:4d} {V:8.2f} {delta:6.3f} {held:7.1f} {traded:+8.1f} {hp:+9.0f} {op:+9.0f} {np_:+9.0f}")
print(f"t0={t0_date} S0={S0:.2f} K={K:.0f} sigma(VIXCLS@t0)={SIG*100:.2f} premium={prem0:.2f} "
      f"premium$={prem0*MULT:.0f}")
print(f"expiry={d21[20]} S_T={s21[20]:.2f} intrinsic={max(s21[20]-K,0.0):.2f} "
      f"naked_short_pnl={naked_final:+.0f} hedged_pnl={hedged_final:+.0f} "
      f"hedged_vs_premium={hedged_final/(prem0*MULT)*100:+.1f}%")

# realized vol over the window (annualized, close-to-close) for the text
lr = np.diff(np.log(s21))
rv = lr.std(ddof=1) * math.sqrt(252) * 100
print(f"realized_vol_window={rv:.2f} implied_used={SIG*100:.2f}")

# --- figure: price path with rebalances + P&L comparison ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.8, 5.6), sharex=True,
                               gridspec_kw={"height_ratios": [1.25, 1.0]})
x = np.arange(21)
ax1.plot(x, s21, "-", color="#17120e", lw=1.6)
ax1.axhline(K, color="#7c1c2c", lw=1.0, ls="--")
ax1.annotate(f"strike {K:.0f}", xy=(0.3, K), fontsize=8.6, color="#7c1c2c",
             va="bottom")
for i in REB:
    ax1.plot(i, s21[i], "o", color="#2f6d4f", ms=6, zorder=5)
ax1.set_ylabel("S&P 500 close", fontsize=9)
ax1.set_title("One real month: short 1 ATM SPX call, hedged at five weekly rebalances (dots)",
              fontsize=10.0)
xs = [p[0] for p in net_path]
ax2.plot(xs, [p[2] for p in net_path], "s--", color="#7c1c2c", lw=1.3, ms=4.5,
         label="naked short call (option leg only)")
ax2.plot(xs, [p[1] for p in net_path], "o-", color="#2f6d4f", lw=1.6, ms=5,
         label="delta-hedged (option + shares)")
ax2.axhline(0, color="#999", lw=0.8)
ax2.set_ylabel("cumulative P&L ($)", fontsize=9)
ax2.set_xlabel("session in window", fontsize=9)
ax2.legend(fontsize=8.2, frameon=False, loc="best")
for ax in (ax1, ax2):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, alpha=0.22)
    ax.tick_params(labelsize=8.2)
fig.text(0.5, -0.015,
         f"Yahoo daily ^GSPC {d21[0]}..{d21[20]} (21 sessions, cached); sigma = CBOE VIX close at t0 "
         f"= {SIG*100:.2f}% (VIXCLS series; FRED first, Yahoo ^VIX fallback). r = 4%, q = 0, multiplier 100. "
         f"Rule fixed before the outcome was seen.",
         ha="center", fontsize=7.4, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_delta_hedge.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
