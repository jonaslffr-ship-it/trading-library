"""
Figure - Put-call parity checked on a real SPX chain snapshot.

Free data: the same cached Cboe delayed SPX chain as fig_chain_annotated.py
(data/spx_chain.json). For the SPX monthly nearest 30 days we compute, at every
strike with a live two-sided quote on both the call and the put, the mid-quote
difference C - P and compare it with the textbook line S - K*exp(-rT). The
short rate r is recovered from the chain itself (parity says the slope of
C - P against K must be -exp(-rT); we read r off a least-squares fit and state
it). Top panel: the dots against the line. Bottom panel: the deviation in index
points. The near-constant small gap is the present value of S&P 500 dividends,
which the no-dividend textbook formula ignores; the scatter AROUND the
dividend-adjusted fit is the honest measure of "tradable" parity violations.

Reproducible:
    python fig_parity_check.py     # numpy, matplotlib; stdlib urllib/json
"""
import os, json, math, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
CACHE = os.path.join(DATA, "spx_chain.json")
URL = "https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json"


def load_chain():
    """Robust cached loader (ERRATA F1/F3): validate before writing, write
    atomically, and SKIP cleanly when the licensed snapshot is unavailable
    offline instead of poisoning the cache with a 0-byte file."""
    if os.path.exists(CACHE) and os.path.getsize(CACHE) > 0:
        try:
            with open(CACHE) as f:
                return json.load(f)
        except (ValueError, OSError):
            pass
    try:
        socket.setdefaulttimeout(60)
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        raw = urllib.request.urlopen(req).read()
        obj = json.loads(raw)
        tmp = CACHE + ".part"
        with open(tmp, "wb") as f:
            f.write(raw)
        os.replace(tmp, CACHE)
        return obj
    except Exception as e:
        print("SKIPPED: needs the licensed CBOE option-chain snapshot "
              f"({os.path.basename(CACHE)}), not redistributed; offline fetch "
              f"failed ({type(e).__name__}). See ERRATA F.")
        raise SystemExit(0)


j = load_chain()
snap_ts = j["timestamp"]
spot = float(j["data"]["current_price"])
snap_date = dt.date(*[int(x) for x in snap_ts.split()[0].split("-")])

book = {}
expiries = {}
for o in j["data"]["options"]:
    sym = o["option"]
    root, exp, cp = sym[:-15], sym[-15:-9], sym[-9]
    strike = int(sym[-8:]) / 1000.0
    book[(root, exp, cp, strike)] = o
    expiries.setdefault((root, exp), set()).add(strike)

best = None
for (root, exp) in expiries:
    if root != "SPX":
        continue
    d = dt.date(2000 + int(exp[:2]), int(exp[2:4]), int(exp[4:6]))
    dte = (d - snap_date).days
    if dte > 0 and (best is None or abs(dte - 30) < abs(best[2] - 30)):
        best = (exp, d, dte)
EXP, exp_date, DTE = best
T = DTE / 365.0

# --- collect strikes with live two-sided quotes on BOTH legs ----------------
K, CMID, PMID = [], [], []
for k in sorted(expiries[("SPX", EXP)]):
    c = book.get(("SPX", EXP, "C", k))
    p = book.get(("SPX", EXP, "P", k))
    if not c or not p:
        continue
    if min(c["bid"], c["ask"], p["bid"], p["ask"]) <= 0:
        continue
    K.append(k); CMID.append((c["bid"] + c["ask"]) / 2); PMID.append((p["bid"] + p["ask"]) / 2)
K = np.array(K); D = np.array(CMID) - np.array(PMID)

# --- recover r and the implied forward from the parity line -----------------
slope, intercept = np.polyfit(K, D, 1)
r_imp = -math.log(-slope) / T                    # slope = -exp(-rT)
F_imp = intercept / (-slope)                     # intercept = exp(-rT)*F
pv_div = spot - F_imp * math.exp(-r_imp * T)     # gap to the no-dividend forward

naive = spot - K * np.exp(-r_imp * T)            # textbook line, no dividends
resid_naive = D - naive
fitted = intercept + slope * K
resid_fit = D - fitted
mad_naive = float(np.median(np.abs(resid_naive)))
mad_fit = float(np.median(np.abs(resid_fit)))
max_fit = float(np.max(np.abs(resid_fit)))

INK, GREY, RED, BLU = "#17120e", "#666666", "#7c1c2c", "#2b5d80"
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.9, 5.6), sharex=True,
                               gridspec_kw={"height_ratios": [2.4, 1.0]})
ax1.plot(K, naive, "-", color=RED, lw=1.5,
         label=r"textbook line  S − K·e$^{-rT}$  (no dividends)")
ax1.plot(K, D, ".", color=INK, ms=3.2, label="C − P from mid quotes (one dot per strike)")
ax1.set_ylabel("C − P  (index points)")
ax1.legend(fontsize=8.2, frameon=False, loc="upper right")
ax1.set_title(f"Put-call parity on SPX, {exp_date.strftime('%b %d, %Y')} expiry "
              f"({DTE} days): {len(K)} strikes on one straight line", fontsize=10.2)
for s_ in ("top", "right"):
    ax1.spines[s_].set_visible(False)
ax1.grid(True, axis="y", alpha=0.18)

ax2.axhline(0, color="#999999", lw=0.8)
ax2.plot(K, resid_naive, ".", color=RED, ms=2.8,
         label=f"vs. textbook line (median gap {mad_naive:.1f} pts ≈ PV of dividends)")
ax2.plot(K, resid_fit, ".", color=BLU, ms=2.8,
         label=f"vs. dividend-adjusted fit (median {mad_fit:.2f} pts)")
ax2.set_xlabel("strike K")
ax2.set_ylabel("deviation (pts)")
ax2.legend(fontsize=7.8, frameon=False, loc="center left", bbox_to_anchor=(0.01, 0.42))
for s_ in ("top", "right"):
    ax2.spines[s_].set_visible(False)
ax2.grid(True, axis="y", alpha=0.18)

fig.text(0.5, -0.015,
         f"Cboe delayed quotes, snapshot {snap_ts} ET; SPX = {spot:,.2f}; r = {r_imp:.2%} recovered "
         f"from the parity slope; implied forward = {F_imp:,.1f}; strikes with two-sided quotes on "
         "both legs. SPX options are European-style, so parity applies as an equality.",
         ha="center", fontsize=7.6, color=GREY)
plt.tight_layout()

OUT = os.path.join(HERE, "fig_parity_check.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"snapshot={snap_ts} spot={spot:.2f} expiry={exp_date} dte={DTE} n_strikes={len(K)} "
      f"K_range={K.min():.0f}..{K.max():.0f}")
print(f"implied_r={r_imp:.4f} implied_forward={F_imp:.2f} pv_dividends_proxy={pv_div:.2f}")
print(f"MAD_vs_textbook_pts={mad_naive:.3f} MAD_vs_fitted_pts={mad_fit:.3f} "
      f"max_abs_dev_vs_fitted_pts={max_fit:.3f}")
