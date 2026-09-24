"""
Figure - one day, one option chain, three gamma-flip answers.

Same cached CBOE delayed SPX chain as fig_gex_profile.py (data/
spx_chain_snapshot.json). Three GEX estimators, all fully specified in
advance, differing ONLY in how dealer positioning is inferred from the
observable chain:

  E1  OI-weighted, standard signs      w_i = OI_i,          calls +, puts -
  E2  volume-weighted, standard signs  w_i = volume_i,      calls +, puts -
  E3  delta-adjusted OI                w_i = OI_i*(1-|d_i|), calls +, puts -
      (contracts are discounted the deeper in the money they are, because the
      canonical customer-flow stories - protective put buying, covered-call
      overwriting - live at and out of the money; |d_i| = CBOE delta at the
      snapshot. One transparent member of a family, not an endorsement.)

Additionally printed (no curve): E4, the "customers long everything"
convention (calls -, puts -, OI-weighted), under which aggregate dealer
gamma has no zero crossing at all.

Total GEX is re-evaluated on a spot grid via Black-Scholes gamma at each
contract's own IV (T fixed, r=0.04, q=0.01); the zero crossing of each curve
is that estimator's "gamma flip". Same-day (settled) expiry excluded.

Reproducible:
    python fig_gex_estimators.py     # numpy, matplotlib; stdlib json/math
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


def norm_pdf(x):
    return np.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def bs_gamma(S, K, T, sig):
    d1 = (np.log(S / K) + (R - Q + 0.5 * sig ** 2) * T) / (sig * np.sqrt(T))
    return np.exp(-Q * T) * norm_pdf(d1) / (S * sig * np.sqrt(T))


chain = load_chain()
d = chain["data"]
spot = float(d["current_price"])
snap = dt.date.fromisoformat(chain["timestamp"][:10])
pat = re.compile(r"^(SPXW?)(\d{6})([CP])(\d{8})$")
rows = []
for o in d["options"]:
    m = pat.match(o["option"])
    if not m:
        continue
    _, ymd, cp, k = m.groups()
    exp = dt.date(2000 + int(ymd[:2]), int(ymd[2:4]), int(ymd[4:6]))
    rows.append((float(k) / 1000.0, (exp - snap).days, 1.0 if cp == "C" else 0.0,
                 float(o["open_interest"]), float(o["volume"]),
                 float(o["iv"]), float(o["delta"])))
a = np.array(rows)
K, dte, iscall, oi, vol, iv, delta = (a[:, i] for i in range(7))
m = (dte >= 1) & (iv > 0.01)
K, T, iscall, oi, vol, iv, delta = (K[m], np.maximum(dte[m], 1.0) / 365.0,
                                    iscall[m], oi[m], vol[m], iv[m], delta[m])
sgn_std = np.where(iscall == 1.0, 1.0, -1.0)

ESTIMATORS = {
    "E1 OI-weighted (standard)":   (sgn_std, oi),
    "E2 volume-weighted":          (sgn_std, vol),
    "E3 delta-adjusted OI":        (sgn_std, oi * (1.0 - np.abs(delta))),
    "E4 customers-long-everything": (-np.ones_like(sgn_std), oi),
}

grid = np.linspace(spot * 0.94, spot * 1.06, 241)


def curve(sgn, w):
    return np.array([(sgn * bs_gamma(S, K, T, iv) * w * MULT * S ** 2 * 0.01).sum()
                     for S in grid])


def zero_cross(y):
    for i in range(1, len(grid)):
        if y[i - 1] * y[i] < 0:
            return grid[i - 1] + (grid[i] - grid[i - 1]) * (y[i - 1] / (y[i - 1] - y[i]))
    return None


COLORS = ["#17120e", "#2a5d8f", "#b0713a"]
fig, ax = plt.subplots(figsize=(6.9, 4.4))
results = {}
for (name, (sgn, w)), c in zip(list(ESTIMATORS.items())[:3], COLORS):
    y = curve(sgn, w)
    f = zero_cross(y)
    results[name] = (f, y[np.argmin(np.abs(grid - spot))])
    scale = np.max(np.abs(y))
    ax.plot(grid, y / scale, "-", lw=1.8, color=c,
            label=f"{name}  -  flip {f:,.0f}" if f else f"{name}  -  no flip")
    if f is not None:
        ax.plot(f, 0, "o", ms=6, color=c)

# E4: printed only
sgn4, w4 = ESTIMATORS["E4 customers-long-everything"]
y4 = curve(sgn4, w4)
results["E4 customers-long-everything"] = (zero_cross(y4),
                                           y4[np.argmin(np.abs(grid - spot))])

ax.axhline(0, color="#999", lw=0.8)
ax.axvline(spot, color="#666", lw=1.0, ls=":")
ax.annotate(f"spot {spot:,.0f}", xy=(spot, 0.9), xytext=(spot - 240, 0.92),
            fontsize=8.5, color="#666")
ax.set_xlabel("hypothetical spot level")
ax.set_ylabel("total GEX (each curve scaled to its own max)")
ax.set_title("Three pre-specified GEX estimators, one chain, three flip points",
             fontsize=10.2)
ax.legend(fontsize=8.2, loc="lower right", frameon=False)
for s_ in ("top", "right"):
    ax.spines[s_].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.03,
         f"CBOE delayed quotes {snap}, {len(K)} live contracts; same-day expiry "
         f"excluded; BSM gamma at per-contract IV, r={R}, q={Q}. Curves scaled "
         f"to unit max for comparability; flips are scale-invariant.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_gex_estimators.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
for name, (f, at_spot) in results.items():
    fs = f"{f:,.1f} ({(f/spot-1)*100:+.2f}% vs spot)" if f else "NO ZERO CROSSING in +/-6%"
    print(f"{name}: flip={fs}  GEX_at_spot={at_spot/1e9:+,.1f}bn/1%")
print(f"snapshot={snap} spot={spot:.2f}")
