"""
Figure 1 - The SPX implied-volatility smile across four maturities (one slice
of the surface per expiry).

Free data: Cboe's public delayed-quotes options chain for ^SPX
(https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json), cached to
data/SPX_options_snapshot.json so the figure is reproducible offline and stable.
The snapshot date is printed and stated in the caption.

ONE transparent, pre-committed selection rule (no tuning, no cherry-picking):
  - out-of-the-money options only (puts with strike <= spot, calls above),
  - Cboe-reported IV > 0 and bid > 0,
  - strike between 75% and 115% of spot,
  - four expiries: the listed dates nearest to 7, 30, 91 and 182 calendar days,
  - where the same (expiry, strike, type) is listed under both the SPX and SPXW
    root, the standard SPX contract is kept.
25-delta reads use the Cboe-reported delta: the put closest to -0.25 and the
call closest to +0.25 per expiry; ATM IV = the option closest to |delta| = 0.50.

Reproducible:
    python fig_iv_surface.py     # numpy, matplotlib; stdlib urllib/json
"""
import os, json, re, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
CACHE = os.path.join(DATA, "SPX_options_snapshot.json")
URL = "https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json"


def load_chain():
    if not os.path.exists(CACHE):
        socket.setdefaulttimeout(60)
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        raw = urllib.request.urlopen(req).read()
        with open(CACHE, "wb") as f:
            f.write(raw)
    with open(CACHE) as f:
        return json.load(f)


j = load_chain()
snap_time = j["timestamp"]                      # e.g. "2026-09-17 22:11:17"
snap_date = dt.datetime.strptime(snap_time[:10], "%Y-%m-%d").date()
spot = float(j["data"]["current_price"])
pat = re.compile(r"^(SPX|SPXW)(\d{6})([CP])(\d{8})$")

# --- collect OTM quotes per expiry, SPX preferred over SPXW on collision ---
book = {}                                        # (exp, K, cp) -> (root, iv, delta)
for o in j["data"]["options"]:
    m = pat.match(o["option"])
    if not m:
        continue
    root, exp, cp, kraw = m.groups()
    K = int(kraw) / 1000.0
    iv, delta, bid = float(o["iv"]), float(o["delta"]), float(o["bid"])
    if iv <= 0 or bid <= 0:
        continue
    if not (0.75 * spot <= K <= 1.15 * spot):
        continue
    if (cp == "P" and K > spot) or (cp == "C" and K <= spot):
        continue                                 # OTM only
    key = (exp, K, cp)
    if key in book and book[key][0] == "SPX":
        continue                                 # keep standard SPX root
    book[key] = (root, iv, delta)

expiries = sorted({k[0] for k in book})
exp_dates = {e: dt.datetime.strptime(e, "%y%m%d").date() for e in expiries}
targets = [7, 30, 91, 182]
chosen = []
for t in targets:
    best = min(expiries, key=lambda e: abs((exp_dates[e] - snap_date).days - t))
    if best not in chosen:
        chosen.append(best)

COLORS = ["#7c1c2c", "#a8762f", "#2f6d4f", "#2f5d7c"]
fig, ax = plt.subplots(figsize=(7.0, 4.4))
stats = []
for e, col in zip(chosen, COLORS):
    rows = sorted([(K, iv, delta) for (exp, K, cp), (root, iv, delta)
                   in book.items() if exp == e])
    K = np.array([r[0] for r in rows])
    iv = np.array([r[1] for r in rows]) * 100.0
    dl = np.array([r[2] for r in rows])
    dte = (exp_dates[e] - snap_date).days
    mono = K / spot * 100.0
    ax.plot(mono, iv, "-", color=col, lw=1.7,
            label=f"{exp_dates[e].isoformat()}  ({dte} d)")
    atm = iv[np.argmin(np.abs(np.abs(dl) - 0.50))]
    p25 = iv[np.argmin(np.abs(dl + 0.25))]        # puts have negative delta
    c25 = iv[np.argmin(np.abs(dl - 0.25))]
    stats.append((exp_dates[e].isoformat(), dte, len(rows), atm, p25, c25,
                  c25 - p25))

ax.axvline(100.0, color="#999", lw=0.8, ls=":")
ax.annotate("spot", xy=(100.0, ax.get_ylim()[1]), xytext=(100.4, ax.get_ylim()[1] * 0.97),
            fontsize=8, color="#666")
ax.set_xlabel("strike as % of spot")
ax.set_ylabel("implied volatility (%, Cboe-reported)")
ax.set_title("SPX implied-volatility smile by maturity: the equity-index skew",
             fontsize=10.5)
ax.legend(frameon=False, fontsize=8.5, title="expiry", title_fontsize=8.5)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.02,
         f"Cboe delayed quotes ^SPX, snapshot {snap_time} ET, spot {spot:.0f}. "
         "OTM mid-quote IVs as reported by Cboe; strikes 75%-115% of spot.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_iv_surface.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"snapshot={snap_time} spot={spot:.2f}")
for (d, dte, n, atm, p25, c25, rr) in stats:
    print(f"expiry={d} dte={dte} n_otm={n} atm_iv={atm:.2f} "
          f"put25d_iv={p25:.2f} call25d_iv={c25:.2f} rr25d={rr:+.2f}")
