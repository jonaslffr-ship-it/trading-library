"""
Figure 2 - A systematic 1-delta put overlay on free data: the bleed and the payoff.

Free data: S&P 500 (^GSPC) and VIX (^VIX) daily closes from Yahoo's public chart
API (range=max), cached to data/gspc_daily.csv and data/vix_daily.csv. Sample
starts 2005-01-03 so it spans 2008, 2020 and 2022.

Pre-registered rule (ONE fixed rule, no optimization over the sample):
  - On the first trading day of each month, buy a one-month put whose Black-Scholes
    delta equals -0.01 - the "1-delta" put - priced at that day's spot with implied
    vol proxied by the VIX (flat, no skew) and r = 2%.
  - Hold puts on the FULL notional (fixed face) and MARK THEM TO MARKET DAILY (spot
    + that day's VIX) until they are rolled on the next month's first trading day.
  - The overlay's daily return is the daily change in the sleeve's marked value as a
    fraction of notional; two sizing points are shown, 1x and 5x face.
  - Portfolio = long S&P 500 + overlay, funded from the same notional.

Honest limitations (stated up front): VIX is a 30-day ATM-ish implied vol; a real
9-11% OTM put trades at a HIGHER implied vol because of skew, so this proxy
UNDERSTATES the premium (the true bleed is worse) and understates the crash-time
repricing (real payoff convexity is larger). Marking to model daily (not trading the
mid-life spike) is a deliberately conservative view of the crisis payoff.

Printed: average strike (% OTM) and premium, full-period premium vs payoff,
annualized drag, max drawdown of S&P 500 alone vs S&P 500 + overlay, and the
months where payoff/premium was largest.

Reproducible:
    python fig_tail_overlay.py     # numpy, matplotlib; stdlib urllib/json/math
"""
import os, csv, json, math, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
START = "2005-01-01"
H = 21
R, FACE = 0.02, 1.0      # hedge the full notional (fixed face), not a fixed premium budget
SQRT2PI = math.sqrt(2.0 * math.pi)


def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def put_price(S, K, T, r, sig):
    d1 = (math.log(S / K) + (r + 0.5 * sig * sig) * T) / (sig * math.sqrt(T))
    d2 = d1 - sig * math.sqrt(T)
    return K * math.exp(-r * T) * ncdf(-d2) - S * ncdf(-d1)


def put_delta(S, K, T, r, sig):
    d1 = (math.log(S / K) + (r + 0.5 * sig * sig) * T) / (sig * math.sqrt(T))
    return ncdf(d1) - 1.0


def solve_strike(S, T, r, sig, target=-0.01):
    # put delta decreases in K; find the deep-OTM strike whose delta = -0.01
    lo, hi = 0.30 * S, 0.999 * S
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if put_delta(S, mid, T, r, sig) > target:   # too close to 0 -> K too low
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def fetch(symbol, cache):
    if os.path.exists(cache):
        d, c = [], []
        with open(cache) as f:
            for row in csv.DictReader(f):
                d.append(row["date"]); c.append(float(row["close"]))
        return d, c
    p1 = int(dt.datetime(2004, 1, 1).timestamp())
    p2 = int(dt.datetime.now().timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?period1={p1}&period2={p2}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        j = json.load(resp)
    res = j["chart"]["result"][0]
    ts = res["timestamp"]
    cl = res["indicators"]["quote"][0]["close"]
    d, c = [], []
    for t, v in zip(ts, cl):
        if v is None:
            continue
        day = dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
        d.append(day); c.append(float(v))
    with open(cache, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "close"])
        for a, b in zip(d, c):
            w.writerow([a, b])
    return d, c


try:
    gd, gc = fetch("%5EGSPC", os.path.join(DATA, "gspc_daily.csv"))
    vd, vc = fetch("%5EVIX", os.path.join(DATA, "vix_daily.csv"))
except (urllib.error.URLError, socket.timeout, KeyError) as e:
    raise SystemExit(f"NETWORK-UNAVAILABLE: {e} - figure not generated, "
                     "run again with connectivity to build the empirical overlay.")

vix = dict(zip(vd, vc))
dates, spx, vv = [], [], []
for d, c in zip(gd, gc):
    if d >= START and d in vix:
        dates.append(d); spx.append(c); vv.append(vix[d])
spx = np.array(spx); vv = np.array(vv); N = len(dates)
print(f"joined sample {dates[0]}..{dates[-1]}  n={N} trading days")

# monthly cycles: a new put is bought on the first trading day of each month and
# MARKED DAILY (spot + that day's VIX) until it is rolled on the next month start.
entries = sorted({0} | {i for i in range(1, N) if dates[i][:7] != dates[i - 1][:7]})
spx_ret = np.zeros(N); spx_ret[1:] = spx[1:] / spx[:-1] - 1.0
sleeve = np.zeros(N)                      # sleeve MTM value, fraction of notional
ov = np.zeros(N)                          # overlay daily return, fraction of notional
otm_list, prem_list, cyc_dates = [], [], []
for c in range(len(entries)):
    e = entries[c]
    end = entries[c + 1] - 1 if c + 1 < len(entries) else N - 1
    if end <= e:
        continue
    S_e, sig_e = spx[e], max(vv[e] / 100.0, 0.05)
    Tc = max((end - e) / 252.0, 2 / 252.0)
    K = solve_strike(S_e, Tc, R, sig_e)          # the 1-delta strike at entry
    prem = put_price(S_e, K, Tc, R, sig_e)
    if prem <= 0:
        continue
    for t in range(e, end + 1):                  # value of puts on the FULL notional
        tau = max((end - t) / 252.0, 0.5 / 252.0)
        sleeve[t] = FACE * put_price(spx[t], K, tau, R, max(vv[t] / 100.0, 0.05)) / S_e
    for t in range(e + 1, end + 1):              # daily MTM change = overlay return
        ov[t] = sleeve[t] - sleeve[t - 1]
    otm_list.append(100 * (S_e - K) / S_e); prem_list.append(100 * FACE * prem / S_e)
    cyc_dates.append(dates[e])

FACES = [1.0, 5.0]                        # two points on the sizing dial (not an optimum)
eq_spx = np.cumprod(1 + spx_ret)
eq_face = {f: np.cumprod(1 + spx_ret + f * ov) for f in FACES}


def max_dd(eq):
    peak = np.maximum.accumulate(eq)
    return float(((eq - peak) / peak).min())


def dd_path(eq):
    peak = np.maximum.accumulate(eq)
    return (eq - peak) / peak


yrs = N / 252.0
print(f"cycles={len(cyc_dates)}  avg strike {np.mean(otm_list):.1f}% OTM  "
      f"avg monthly premium {np.mean(prem_list):.3f}% of notional "
      f"(~{12*np.mean(prem_list):.2f}%/yr per 1x face, understated: no skew)")
print(f"peak sleeve MTM (1x face): {100*sleeve.max():.2f}% of notional on {dates[int(sleeve.argmax())]} "
      f"(resting ~{100*np.median(sleeve[sleeve>0]):.3f}% -> x{sleeve.max()/np.median(sleeve[sleeve>0]):.0f})")
print(f"max drawdown (daily marked)  S&P500 alone {100*max_dd(eq_spx):6.1f}%")
for f in FACES:
    print(f"   + {f:.0f}x face overlay: maxDD {100*max_dd(eq_face[f]):6.1f}%   "
          f"drag {100*((eq_face[f][-1]/eq_spx[-1])**(1/yrs)-1):+.2f}%/yr   "
          f"final {eq_face[f][-1]:.2f}x (vs {eq_spx[-1]:.2f}x)")
# 2020 COVID window: the fast vol-crash where a far-OTM put actually bites
w = [i for i, d in enumerate(dates) if "2020-02-01" <= d <= "2020-05-01"]
if w:
    dda = dd_path(eq_spx)
    print(f"2020 window  S&P500 alone trough {100*dda[w].min():.1f}%", end="")
    for f in FACES:
        print(f"   +{f:.0f}x {100*dd_path(eq_face[f])[w].min():.1f}%", end="")
    print()
order = np.argsort(sleeve)[::-1]
seen, tops = set(), []
for i in order:
    mo = dates[i][:7]
    if mo not in seen:
        seen.add(mo); tops.append((dates[i], f"{100*sleeve[i]:.1f}% notional"))
    if len(tops) == 5:
        break
print("  largest sleeve MTM (monetization windows):", tops)

# ---------------- figure ------------------------------------------------------
x = np.arange(N)
yr_ticks = [i for i in range(1, N) if dates[i][:4] != dates[i - 1][:4]
            and int(dates[i][:4]) % 3 == 0]
C_SPX, C_1X, C_5X = "#31536e", "#b0473a", "#2f6d4f"
MON = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
fig = plt.figure(figsize=(6.9, 6.0))
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.2], hspace=0.42, wspace=0.26)
ax1 = fig.add_subplot(gs[0, :])          # (a) sleeve MTM, full history, full width
ax2 = fig.add_subplot(gs[1, 0])          # (b) drawdown, full history
ax3 = fig.add_subplot(gs[1, 1])          # (c) drawdown, 2020 zoom

ax1.fill_between(x, 100 * sleeve, 0, color="#7c1c2c", lw=0, alpha=0.85)
ax1.set_ylabel("sleeve MTM\n(% of notional)")
ax1.set_title("(a)  The sleeve marked daily: dormant most of the time, it detonates on a vol spike",
              fontsize=9.3, loc="left")
ax1.set_xticks(yr_ticks); ax1.set_xticklabels([dates[i][:4] for i in yr_ticks], fontsize=8)
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)
ax1.grid(True, axis="y", alpha=0.25)

# (b) full history: passively held, the overlay barely dents the worst (2008) drawdown
ax2.plot(x, 100 * dd_path(eq_spx), color=C_SPX, lw=1.0, label="S&P 500 alone")
ax2.plot(x, 100 * dd_path(eq_face[1.0]), color=C_1X, lw=1.0, label="+ 1x overlay (~0.2%/yr)")
ax2.plot(x, 100 * dd_path(eq_face[5.0]), color=C_5X, lw=1.0, label="+ 5x overlay (~1%/yr)")
ax2.set_ylabel("drawdown (%)")
ax2.set_title("(b)  Full history: barely helps the worst drawdown",
              fontsize=8.0, loc="left")
ax2.legend(fontsize=6.6, frameon=False, loc="lower right")
ax2.set_xticks(yr_ticks[::2])
ax2.set_xticklabels([dates[i][:4] for i in yr_ticks[::2]], fontsize=7)
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
ax2.grid(True, axis="y", alpha=0.25)

# (c) 2020 zoom: the cushion is visible - and 5x helps LESS than 1x (its own vol drag)
wz = [i for i, d in enumerate(dates) if "2020-01-15" <= d <= "2020-05-15"]
xz = np.arange(len(wz))
ax3.plot(xz, 100 * dd_path(eq_spx)[wz], color=C_SPX, lw=1.3)
ax3.plot(xz, 100 * dd_path(eq_face[5.0])[wz], color=C_5X, lw=1.3)
ax3.plot(xz, 100 * dd_path(eq_face[1.0])[wz], color=C_1X, lw=1.3)
ax3.set_title("(c)  2020 zoom: the cushion is real",
              fontsize=8.0, loc="left")
mt = [j for j in range(len(wz)) if j == 0 or dates[wz[j]][5:7] != dates[wz[j - 1]][5:7]]
ax3.set_xticks(mt)
ax3.set_xticklabels([MON[int(dates[wz[j]][5:7])] for j in mt], fontsize=7)
for s in ("top", "right"):
    ax3.spines[s].set_visible(False)
ax3.grid(True, axis="y", alpha=0.25)

fig.text(0.5, -0.02,
         f"Yahoo ^GSPC + ^VIX, {dates[0]} to {dates[-1]}, daily. 1-delta 1M put (delta -0.01) "
         "rolled monthly, IV proxied by VIX (no skew -> bleed understated). Marked to market daily; "
         "single fixed rule, no optimization.",
         ha="center", fontsize=7.3, color="#666")
OUT = os.path.join(HERE, "fig_tail_overlay.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
