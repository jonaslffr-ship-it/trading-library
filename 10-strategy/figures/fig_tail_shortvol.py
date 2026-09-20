"""
Figure 3 - Why a premium seller needs a wing: the uncapped tail, capped.

Two short-premium books, each shown naked versus married to far-OTM long wings
(the 1-delta options of this paper), as expiry P&L per 100 of index notional:

  (a) Short at-the-money straddle (short 1 call + short 1 put, K = spot).
      Collect a fat premium; the loss is |S_T - K| - premium, unbounded on
      both sides. Adding long far-OTM wings caps it (a long "iron fly").

  (b) Short 10%-OTM strangle SOLD INTO HIGH VOLATILITY (sigma = 40%): sell a
      90 put and a 110 call. Collect a thinner premium; a gap through a strike
      loses many multiples of it. Adding the 1-delta wings makes it an iron
      condor with a known, survivable maximum loss.

Everything is a transparent Black-Scholes computation on stated inputs - no
market data. The point is structural, not a backtest: bounded gain, unbounded
loss is the shape a black swan is built to exploit.

Reproducible:
    python fig_tail_shortvol.py     # numpy, matplotlib; stdlib math only
"""
import os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SQRT2PI = math.sqrt(2.0 * math.pi)


def _nc(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bsm(S, K, T, r, sig, call=True):
    d1 = (math.log(S / K) + (r + 0.5 * sig * sig) * T) / (sig * math.sqrt(T))
    d2 = d1 - sig * math.sqrt(T)
    if call:
        px = S * _nc(d1) - K * math.exp(-r * T) * _nc(d2)
        dlt = _nc(d1)
    else:
        px = K * math.exp(-r * T) * _nc(-d2) - S * _nc(-d1)
        dlt = _nc(d1) - 1.0
    return px, dlt


def strike_for_delta(S, T, r, sig, target, call):
    # monotone in K; bisect for the strike whose BSM delta == target
    lo, hi = (S, 6.0 * S) if call else (0.02 * S, S)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        _, d = bsm(S, mid, T, r, sig, call)
        if call:
            hi, lo = (mid, lo) if d < target else (hi, mid)   # call delta falls toward 0 as K rises
        else:
            lo, hi = (lo, mid) if d < target else (mid, hi)   # put delta falls toward -1 as K rises
    return 0.5 * (lo + hi)


S0, r, T = 100.0, 0.04, 21.0 / 252.0
ST = np.linspace(35.0, 165.0, 1301)

# ---- (a) short ATM straddle at a normal 20% vol ---------------------------
sig_a = 0.20
c0, _ = bsm(S0, S0, T, r, sig_a, True)
p0, _ = bsm(S0, S0, T, r, sig_a, False)
straddle_prem = c0 + p0                                  # collected
# far 1-delta wings to cap it
Kp_w = strike_for_delta(S0, T, r, sig_a, -0.01, False)
Kc_w = strike_for_delta(S0, T, r, sig_a, +0.01, True)
wp, _ = bsm(S0, Kp_w, T, r, sig_a, False)
wc, _ = bsm(S0, Kc_w, T, r, sig_a, True)
wing_cost_a = wp + wc
naked_a = straddle_prem - np.abs(ST - S0)
hedged_a = naked_a + np.maximum(Kp_w - ST, 0.0) + np.maximum(ST - Kc_w, 0.0) - wing_cost_a
maxloss_hedged_a = -hedged_a.max() if False else -(hedged_a.min())

def mult(move):  # loss as a multiple of premium on a -move% straddle outcome
    S_T = S0 * (1 - move)
    loss = abs(S_T - S0) - straddle_prem
    return loss, loss / straddle_prem

l30, m30 = mult(0.30)
l50, m50 = mult(0.50)

# ---- (b) short 10%-OTM strangle sold into HIGH vol (40%) -------------------
sig_b = 0.40
Kp, Kc = 90.0, 110.0
pp, _ = bsm(S0, Kp, T, r, sig_b, False)
pc, _ = bsm(S0, Kc, T, r, sig_b, True)
strangle_prem = pp + pc
Kp_w2 = strike_for_delta(S0, T, r, sig_b, -0.01, False)
Kc_w2 = strike_for_delta(S0, T, r, sig_b, +0.01, True)
wp2, _ = bsm(S0, Kp_w2, T, r, sig_b, False)
wc2, _ = bsm(S0, Kc_w2, T, r, sig_b, True)
wing_cost_b = wp2 + wc2
naked_b = strangle_prem - np.maximum(Kp - ST, 0.0) - np.maximum(ST - Kc, 0.0)
hedged_b = naked_b + np.maximum(Kp_w2 - ST, 0.0) + np.maximum(ST - Kc_w2, 0.0) - wing_cost_b

# strangle loss at a -30% gap, as a multiple of premium collected
ST30 = S0 * 0.70
loss_b30 = max(Kp - ST30, 0.0) - strangle_prem
mult_b30 = loss_b30 / strangle_prem

print(f"(a) ATM straddle @ {sig_a:.0%}: premium {straddle_prem:.2f} of {S0:.0f} "
      f"({100*straddle_prem/S0:.2f}% of spot); 1-delta wings at {Kp_w:.1f}/{Kc_w:.1f} "
      f"cost {wing_cost_a:.2f}")
print(f"    -30% -> loss {l30:.1f} = {m30:.1f}x premium ({100*m30:.0f}% of premium); "
      f"-50% -> loss {l50:.1f} = {m50:.1f}x ({100*m50:.0f}% of premium)")
print(f"    naked max loss over plotted range: {-(naked_a.min()):.1f}; "
      f"hedged max loss capped at: {-(hedged_a.min()):.2f}")
print(f"(b) 10%-OTM strangle @ {sig_b:.0%}: premium {strangle_prem:.2f} "
      f"({100*strangle_prem/S0:.2f}% of spot); 1-delta wings at {Kp_w2:.1f}/{Kc_w2:.1f} "
      f"cost {wing_cost_b:.2f}")
print(f"    -30% gap -> put loss {loss_b30:.1f} = {mult_b30:.1f}x premium "
      f"({100*mult_b30:.0f}% of premium); hedged max loss capped at "
      f"{-(hedged_b.min()):.2f}")

# ---------------- figure ----------------------------------------------------
C_NAKED, C_HEDGED = "#b0473a", "#2f6d4f"
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.5), sharey=False)

for ax, naked, hedged, title, sub in [
    (ax1, naked_a, hedged_a,
     "(a)  Short ATM straddle (20% vol)",
     f"premium {100*straddle_prem/S0:.1f}% of spot; a -30% gap loses {m30:.0f}x it"),
    (ax2, naked_b, hedged_b,
     "(b)  Short 10%-OTM strangle sold into 40% vol",
     f"premium {100*strangle_prem/S0:.1f}% of spot; a -30% gap loses {mult_b30:.0f}x it"),
]:
    ax.axhline(0, color="#999", lw=0.8)
    ax.plot(ST, naked, color=C_NAKED, lw=1.5, label="naked short (no wings)")
    ax.plot(ST, hedged, color=C_HEDGED, lw=1.5, label="+ far-OTM 1-delta wings")
    ax.set_title(title + "\n" + sub, fontsize=8.4, loc="left")
    ax.set_xlabel("index level at expiry")
    ax.grid(True, alpha=0.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
ax1.set_ylabel("P&L at expiry (per 100 notional)")
ax1.legend(fontsize=7.2, frameon=False, loc="lower center")

fig.text(0.5, -0.03,
         "Black-Scholes expiry P&L, S=100, r=4%, T=21/252, no market data. The naked short's loss is "
         "unbounded (bounded gain, unbounded loss); the far-OTM long wings turn it into a known, "
         "survivable maximum. One transparent computation, no optimization.",
         ha="center", fontsize=7.0, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_tail_shortvol.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
