"""
Figure - A long call's P&L before expiry vs. at expiry.

Didactic Black-Scholes-Merton curves (no market data needed): buy a 30-day
at-the-money call (S = K = 100, sigma = 20% annualized, r = 4%, no dividends),
pay the model premium, then mark the position to model value with 30, 10 and 1
day(s) remaining, and at expiry (the hockey stick). Two lessons in one picture:
before expiry the P&L curve is smooth and BENT (the kink only appears at the
end), and the whole curve sags toward the hockey stick as days pass - time
decay, paid by the buyer.

Reproducible:
    python fig_payoff_before_expiry.py     # numpy, matplotlib only (stdlib erf)
"""
import os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

K, SIG, R = 100.0, 0.20, 0.04
DAYS0 = 30                      # days to expiry at purchase


def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bsm_call(S, K, sig, r, T):
    """Black-Scholes-Merton European call, T in years; handles T -> 0."""
    S = np.asarray(S, dtype=float)
    if T <= 0:
        return np.maximum(S - K, 0.0)
    d1 = (np.log(S / K) + (r + 0.5 * sig**2) * T) / (sig * math.sqrt(T))
    d2 = d1 - sig * math.sqrt(T)
    Nd1 = np.vectorize(ncdf)(d1)
    Nd2 = np.vectorize(ncdf)(d2)
    return S * Nd1 - K * math.exp(-r * T) * Nd2


C0 = float(bsm_call(np.array([100.0]), K, SIG, R, DAYS0 / 365.0)[0])   # premium paid
S = np.linspace(88, 112, 481)

INK, GREY = "#17120e", "#666666"
shades = ["#9dbcd4", "#5b87a8", "#2b5d80"]          # 30 -> 10 -> 1 days (darker = closer)
fig, ax = plt.subplots(figsize=(6.8, 4.3))
ax.axhline(0, color="#999999", lw=0.8)
ax.axvline(K, color="#bbbbbb", lw=0.8, ls=":")

atm_vals = {}
for days, col in zip([30, 10, 1], shades):
    pnl = bsm_call(S, K, SIG, R, days / 365.0) - C0
    ax.plot(S, pnl, color=col, lw=1.7, label=f"{days} day{'s' if days > 1 else ''} left")
    atm_vals[days] = float(bsm_call(np.array([100.0]), K, SIG, R, days / 365.0)[0]) - C0
pnl_exp = np.maximum(S - K, 0.0) - C0
ax.plot(S, pnl_exp, color=INK, lw=2.1, label="at expiry (hockey stick)")

be = K + C0
ax.plot(be, 0, "o", color=INK, ms=5, zorder=5)
ax.annotate(f"break-even at expiry = {be:.2f}", xy=(be, 0), xytext=(be + 1.0, -2.6),
            fontsize=8.4, color=INK, arrowprops=dict(arrowstyle="->", color=INK, lw=0.8))
ax.annotate("same stock price,\nless time = less value", xy=(100, atm_vals[1]),
            xytext=(90.0, 3.2), fontsize=8.4, color="#2b5d80",
            arrowprops=dict(arrowstyle="->", color="#2b5d80", lw=0.8))
ax.set_xlabel("stock price")
ax.set_ylabel("profit / loss per share")
ax.set_title("A long call before expiry: the curve is smooth, and it sinks day by day",
             fontsize=10.2)
ax.legend(fontsize=8.2, frameon=False, loc="upper left")
for s_ in ("top", "right"):
    ax.spines[s_].set_visible(False)
ax.grid(True, axis="y", alpha=0.18)
fig.text(0.5, -0.02,
         f"Black-Scholes-Merton model values: K = {K:.0f}, sigma = {SIG:.0%} annualized, r = {R:.0%}, "
         f"no dividends; premium paid = {C0:.2f} (30-day at-the-money call at S = 100).",
         ha="center", fontsize=7.6, color=GREY)
plt.tight_layout()

OUT = os.path.join(HERE, "fig_payoff_before_expiry.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"premium_paid_C0={C0:.3f} BE_expiry={be:.2f} "
      f"ATM_pnl_30d={atm_vals[30]:.3f} ATM_pnl_10d={atm_vals[10]:.3f} ATM_pnl_1d={atm_vals[1]:.3f}")
