"""
Figure - A real SPX option chain, rendered and annotated column by column.

Free data: Cboe's public delayed-quote API for SPX index options,
https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json , cached to
data/spx_chain.json so the figure is reproducible offline and stable. One
expiry is shown - the standard SPX monthly (AM-settled) nearest to 30 days -
with the strikes around the index level, in the classic layout: calls on the
left, puts on the right, strikes in the middle. Shading marks the in-the-money
half of each side; annotations explain bid/ask/spread and volume vs. open
interest. Snapshot data, reported as-is: no filtering beyond the strike window.

Reproducible:
    python fig_chain_annotated.py     # numpy, matplotlib; stdlib urllib/json
"""
import os, json, socket, urllib.request, datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

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

# --- index the chain: (root, expiry, C/P, strike) -> quote dict -------------
book = {}
expiries = {}
for o in j["data"]["options"]:
    sym = o["option"]                       # e.g. SPX261016C07650000
    root, exp, cp = sym[:-15], sym[-15:-9], sym[-9]
    strike = int(sym[-8:]) / 1000.0
    book[(root, exp, cp, strike)] = o
    expiries.setdefault((root, exp), set()).add(strike)

# --- pick the SPX monthly nearest 30 days to expiry -------------------------
snap_date = dt.date(*[int(x) for x in snap_ts.split()[0].split("-")])
best = None
for (root, exp) in expiries:
    if root != "SPX":
        continue
    d = dt.date(2000 + int(exp[:2]), int(exp[2:4]), int(exp[4:6]))
    dte = (d - snap_date).days
    if dte > 0 and (best is None or abs(dte - 30) < abs(best[2] - 30)):
        best = (exp, d, dte)
EXP, exp_date, DTE = best

# --- strike window: multiples of 25 within +/-125 points of the index -------
lo = 25 * round((spot - 125) / 25.0)
strikes = [lo + 25 * i for i in range(11)]
strikes = [k for k in strikes
           if ("SPX", EXP, "C", float(k)) in book and ("SPX", EXP, "P", float(k)) in book]
atm = min(strikes, key=lambda k: abs(k - spot))

rows = []
for k in strikes:
    c = book[("SPX", EXP, "C", float(k))]
    p = book[("SPX", EXP, "P", float(k))]
    rows.append((k, c, p))

# --- render as a manual grid ------------------------------------------------
INK, GREY = "#17120e", "#666666"
GRN, BLU, HL = "#2f6d4f", "#2b5d80", "#f0ece4"
cols = ["OI", "Vol", "IV", "Bid", "Ask", "Strike", "Bid", "Ask", "IV", "Vol", "OI"]
widths = [0.105, 0.085, 0.075, 0.085, 0.085, 0.10, 0.085, 0.085, 0.075, 0.085, 0.105]
xl = [sum(widths[:i]) for i in range(len(widths))]
xc = [xl[i] + widths[i] / 2 for i in range(len(widths))]

fig, ax = plt.subplots(figsize=(9.8, 6.1))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

TOP, BOT = 0.83, 0.13
nrow = len(rows)
rh = (TOP - BOT) / (nrow + 1)                       # +1 for header
yh = TOP - rh / 2                                   # header center
ycent = [TOP - rh * (i + 1) - rh / 2 for i in range(nrow)]

# shading: ITM half of each side (calls: strikes below spot; puts: above)
for i, (k, c, p) in enumerate(rows):
    ytop = TOP - rh * (i + 1)
    if k < spot:   # calls ITM
        ax.add_patch(Rectangle((xl[0], ytop - rh), sum(widths[:5]), rh,
                               fc=GRN, alpha=0.10, ec="none"))
    if k > spot:   # puts ITM
        ax.add_patch(Rectangle((xl[6], ytop - rh), sum(widths[6:]), rh,
                               fc=BLU, alpha=0.10, ec="none"))
    if k == atm:
        ax.add_patch(Rectangle((0, ytop - rh), 1, rh, fc=HL, alpha=0.9, ec="none", zorder=0))

# group headers + column headers
ax.text(sum(widths[:5]) / 2, yh + rh * 0.95, "CALLS  (right to buy)", fontsize=9.5,
        ha="center", color=GRN, weight="bold")
ax.text(xl[6] + sum(widths[6:]) / 2, yh + rh * 0.95, "PUTS  (right to sell)", fontsize=9.5,
        ha="center", color=BLU, weight="bold")
for x, h in zip(xc, cols):
    ax.text(x, yh, h, fontsize=8.6, ha="center", va="center", color=INK, weight="bold")
ax.plot([0, 1], [TOP - rh, TOP - rh], color=INK, lw=0.9)
ax.plot([0, 1], [TOP, TOP], color=INK, lw=0.9)
ax.plot([0, 1], [BOT, BOT], color=INK, lw=0.9)

fmt_i = lambda v: f"{int(v):,}"
for (k, c, p), y in zip(rows, ycent):
    vals = [fmt_i(c["open_interest"]), fmt_i(c["volume"]), f"{c['iv']:.2f}",
            f"{c['bid']:.2f}", f"{c['ask']:.2f}", f"{int(k):,}",
            f"{p['bid']:.2f}", f"{p['ask']:.2f}", f"{p['iv']:.2f}",
            fmt_i(p["volume"]), fmt_i(p["open_interest"])]
    for x, v, cidx in zip(xc, vals, range(11)):
        w = "bold" if cidx == 5 else "normal"
        ax.text(x, y, v, fontsize=8.4, ha="center", va="center", color=INK, weight=w)

# the index level between two strike rows
for i, (k, c, p) in enumerate(rows[:-1]):
    if k < spot < rows[i + 1][0]:
        yline = TOP - rh * (i + 2)
        ax.plot([0, 1], [yline, yline], color="#7c1c2c", lw=1.1, ls="--")
        ax.text(1.005, yline, f"SPX = {spot:,.2f}", fontsize=8.4, color="#7c1c2c",
                va="center", ha="left")

# annotations
ac = book[("SPX", EXP, "C", float(atm))]
mid = (ac["bid"] + ac["ask"]) / 2
spread = ac["ask"] - ac["bid"]
iat = strikes.index(atm)
ax.annotate("bid / ask: what you get / what you pay.\n"
            f"ATM call: {ac['bid']:.2f} / {ac['ask']:.2f} -> mid {mid:.2f}, "
            f"spread {spread:.2f} pts",
            xy=(xc[3] + 0.02, ycent[iat] + 0.012), xytext=(0.06, 0.965),
            fontsize=8.2, color=INK, ha="left", va="top",
            arrowprops=dict(arrowstyle="->", color=INK, lw=0.8))
ax.annotate("open interest: positions outstanding\n(the stock, updated overnight)",
            xy=(xc[10], BOT - 0.005), xytext=(0.99, 0.055), fontsize=8.2, color=INK,
            ha="right", va="top",
            arrowprops=dict(arrowstyle="->", color=INK, lw=0.8))
ax.annotate("volume: contracts traded this day\n(the flow, resets every day)",
            xy=(xc[1], BOT - 0.005), xytext=(0.01, 0.055), fontsize=8.2, color=INK,
            ha="left", va="top",
            arrowprops=dict(arrowstyle="->", color=INK, lw=0.8))
ax.annotate("at the money:\nstrike nearest the index",
            xy=(xc[5] - 0.038, ycent[iat]), xytext=(0.60, 0.965), fontsize=8.2,
            color=INK, ha="left", va="top",
            arrowprops=dict(arrowstyle="->", color=INK, lw=0.8))
ax.set_title(f"SPX option chain, {exp_date.strftime('%b %d, %Y')} monthly expiry "
             f"({DTE} days out) — delayed Cboe snapshot", fontsize=10.4, pad=30)
fig.text(0.5, 0.015,
         f"Cboe delayed quotes, snapshot {snap_ts} ET; SPX = {spot:,.2f}; shaded cells are "
         "in the money (calls: strikes below the index; puts: strikes above). "
         "IV in decimal form (0.14 = 14%). Contract multiplier: $100 per index point.",
         ha="center", fontsize=7.6, color=GREY)

OUT = os.path.join(HERE, "fig_chain_annotated.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
tot_oi = sum(int(c["open_interest"]) + int(p["open_interest"]) for _, c, p in rows)
tot_vol = sum(int(c["volume"]) + int(p["volume"]) for _, c, p in rows)
ap = book[("SPX", EXP, "P", float(atm))]
pmid = (ap["bid"] + ap["ask"]) / 2
print(f"snapshot={snap_ts} spot={spot:.2f} expiry={exp_date} dte={DTE} "
      f"strikes={strikes[0]:.0f}..{strikes[-1]:.0f} n={len(strikes)} atm={atm:.0f}")
print(f"atm_call bid={ac['bid']:.2f} ask={ac['ask']:.2f} mid={mid:.2f} "
      f"spread={spread:.2f} spread_pct_of_mid={100 * spread / mid:.1f}% iv={ac['iv']:.3f} "
      f"oi={int(ac['open_interest'])} vol={int(ac['volume'])}")
print(f"atm_put  bid={ap['bid']:.2f} ask={ap['ask']:.2f} mid={pmid:.2f} iv={ap['iv']:.3f} "
      f"oi={int(ap['open_interest'])} vol={int(ap['volume'])}")
print(f"shown_rows_total_oi={tot_oi:,} shown_rows_total_vol={tot_vol:,} "
      f"atm_straddle_mid={mid + pmid:.2f}")
