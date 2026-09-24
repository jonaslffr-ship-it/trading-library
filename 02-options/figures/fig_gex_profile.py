"""
Figure - SPX strike-level gamma exposure (GEX) profile from the free CBOE
delayed-quotes chain, under the standard dealer-positioning assumption
(dealers long the call book, short the put book).

Free data: https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json
(CBOE public delayed-quotes API; User-Agent header required). The raw JSON is
cached to data/spx_chain_snapshot.json on first run so the figure is stable
and reproducible offline; the snapshot date is printed and shown in-figure.

Construction (fixed in advance, no tuning):
  - per contract: dollar gamma per 1% spot move = Gamma * OI * M * S^2 * 0.01,
    with multiplier M = 100 and Gamma as provided by CBOE;
  - sign: +1 for calls, -1 for puts (the standard assumption; see paper text
    for what this assumes and when it breaks);
  - contracts expiring on the snapshot date itself are excluded from the
    exposure aggregation (already settled at an end-of-day snapshot);
  - top panel: net GEX per strike within +/-10% of spot;
  - bottom panel: total GEX re-evaluated at shifted spot levels (Black-Scholes
    gamma at each contract's own IV, T fixed), whose zero crossing is the
    "gamma flip"; r=0.04, q=0.01 (gamma is insensitive to both).

Reproducible:
    python fig_gex_profile.py     # numpy, matplotlib; stdlib urllib/json/math
"""
import os, json, re, math, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
CACHE = os.path.join(DATA, "spx_chain_snapshot.json")
URL = "https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json"
MULT = 100.0
R, Q = 0.04, 0.01


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


def parse(chain):
    d = chain["data"]
    spot = float(d["current_price"])
    snap_date = dt.date.fromisoformat(chain["timestamp"][:10])
    pat = re.compile(r"^(SPXW?)(\d{6})([CP])(\d{8})$")
    rows = []  # strike, dte, iscall, oi, vol, gamma, iv, delta
    for o in d["options"]:
        m = pat.match(o["option"])
        if not m:
            continue
        _, ymd, cp, k = m.groups()
        exp = dt.date(2000 + int(ymd[:2]), int(ymd[2:4]), int(ymd[4:6]))
        dte = (exp - snap_date).days
        rows.append((float(k) / 1000.0, dte, 1.0 if cp == "C" else 0.0,
                     float(o["open_interest"]), float(o["volume"]),
                     float(o["gamma"]), float(o["iv"]), float(o["delta"])))
    a = np.array(rows)
    return spot, snap_date, a


def norm_pdf(x):
    return np.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def bs_gamma(S, K, T, sig):
    d1 = (np.log(S / K) + (R - Q + 0.5 * sig ** 2) * T) / (sig * np.sqrt(T))
    return np.exp(-Q * T) * norm_pdf(d1) / (S * sig * np.sqrt(T))


chain = load_chain()
spot, snap, a = parse(chain)
K, dte, iscall, oi, vol, gam, iv, delta = (a[:, i] for i in range(8))
live = dte >= 1                       # exclude the already-settled same-day expiry
sign = np.where(iscall == 1.0, 1.0, -1.0)

# --- per-strike net GEX at the actual spot (CBOE-provided gamma) -------------
gex_c = sign * gam * oi * MULT * spot ** 2 * 0.01          # $ per 1% move
strikes = np.unique(K[live])
net = np.array([gex_c[live & (K == s)].sum() for s in strikes])
total = gex_c[live].sum()

win = (strikes >= spot * 0.90) & (strikes <= spot * 1.10)
ks, ns = strikes[win], net[win]
call_wall = ks[np.argmax(ns)]
put_wall = ks[np.argmin(ns)]

# --- GEX as a function of spot (BSM gamma, per-contract IV) ------------------
m = live & (iv > 0.01) & (oi > 0)
Km, Tm, sm, om = K[m], np.maximum(dte[m], 1.0) / 365.0, sign[m], oi[m]
ivm = iv[m]
grid = np.linspace(spot * 0.94, spot * 1.06, 241)
gex_S = np.array([(sm * bs_gamma(S, Km, Tm, ivm) * om * MULT * S ** 2 * 0.01).sum()
                  for S in grid])
flip = None
for i in range(1, len(grid)):
    if gex_S[i - 1] * gex_S[i] < 0:
        flip = grid[i - 1] + (grid[i] - grid[i - 1]) * (
            gex_S[i - 1] / (gex_S[i - 1] - gex_S[i]))
        break

# sanity: CBOE-provided vs recomputed BSM gamma near the money
nm = m & (np.abs(K / spot - 1) < 0.02) & (gam > 0)
ratio = np.median(bs_gamma(spot, K[nm], np.maximum(dte[nm], 1.0) / 365.0, iv[nm])
                  / gam[nm])

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.9, 6.4), height_ratios=[1.5, 1])
colors = np.where(ns >= 0, "#2f6d4f", "#7c1c2c")
ax1.bar(ks, ns / 1e9, width=8.5, color=colors, alpha=0.85)
ax1.axvline(spot, color="#17120e", lw=1.1, ls="-")
ax1.annotate(f"spot {spot:,.0f}", xy=(spot, ax1.get_ylim()[1]),
             xytext=(spot - 620, np.max(ns / 1e9) * 0.92), fontsize=8.5,
             color="#17120e")
ax1.annotate(f"call wall {call_wall:,.0f}", xy=(call_wall, np.max(ns) / 1e9),
             xytext=(call_wall + 60, np.max(ns) / 1e9 * 0.75), fontsize=8.5,
             color="#2f6d4f",
             arrowprops=dict(arrowstyle="->", color="#2f6d4f", lw=0.8))
ax1.annotate(f"put wall {put_wall:,.0f}", xy=(put_wall, np.min(ns) / 1e9),
             xytext=(put_wall - 640, np.min(ns) / 1e9 * 0.8), fontsize=8.5,
             color="#7c1c2c",
             arrowprops=dict(arrowstyle="->", color="#7c1c2c", lw=0.8))
ax1.set_ylabel("net GEX per strike ($bn per 1% move)")
ax1.set_title(f"SPX strike-level GEX, standard sign assumption - "
              f"CBOE delayed chain, {snap}", fontsize=10.2)
ax1.grid(True, axis="y", alpha=0.25)

ax2.plot(grid, gex_S / 1e9, "-", color="#17120e", lw=1.9)
ax2.axhline(0, color="#999", lw=0.8)
ax2.axvline(spot, color="#17120e", lw=1.0, ls=":")
if flip is not None:
    ax2.axvline(flip, color="#7c1c2c", lw=1.2, ls="--")
    ax2.annotate(f"gamma flip ~ {flip:,.0f}  ({(flip / spot - 1) * 100:+.1f}%)",
                 xy=(flip, 0), xytext=(flip - spot * 0.045, np.min(gex_S) / 1e9 * 0.55),
                 fontsize=9, color="#7c1c2c",
                 arrowprops=dict(arrowstyle="->", color="#7c1c2c", lw=0.8))
ax2.set_xlabel("hypothetical spot level")
ax2.set_ylabel("total GEX ($bn per 1%)")
ax2.grid(True, axis="y", alpha=0.25)
for ax in (ax1, ax2):
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
fig.text(0.5, -0.01,
         f"CBOE delayed quotes {snap}; {int(live.sum())} live contracts, "
         f"same-day expiry excluded from exposure; signs: calls +, puts - "
         f"(standard assumption); r={R}, q={Q}.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_gex_profile.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"snapshot={snap} spot={spot:.2f} live_contracts={int(live.sum())} "
      f"total_GEX_bn={total/1e9:.2f} flip={flip:.0f} "
      f"flip_pct={(flip/spot-1)*100:+.2f}% call_wall={call_wall:.0f} "
      f"put_wall={put_wall:.0f} bsm_vs_cboe_gamma_median_ratio={ratio:.3f}")
print(f"OI_total={oi[live].sum():,.0f} expiry_18th_OI={oi[live & (dte==1)].sum():,.0f}")
