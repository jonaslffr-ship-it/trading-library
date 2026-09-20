"""
Section 8 - Worked examples: third-order greeks by central finite difference.

Didactic Black-Scholes-Merton computation, no market data. The robust method
here is to finite-difference the VERIFIED closed-form second-order greeks
(gamma and vomma) by bumping S, sigma and t, and to treat the third-order
closed forms only as a cross-check. For an ATM one-month option
(S=K=100, T=21/252, r=4%, sigma=20%, q=0) this prints, for each of speed,
zomma, color and ultima, the finite-difference value, the closed-form value,
and the relative error, plus the maximum relative error across all four.

Everything uses stdlib math only (no numpy, no scipy).

Reproducible:
    python fig_to_worked_examples.py
"""
import math

SQRT2PI = math.sqrt(2.0 * math.pi)


def npdf(x):
    return math.exp(-0.5 * x * x) / SQRT2PI


def _d1d2(S, K, T, r, sigma, q):
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrtT)
    return d1, d1 - sigma * sqrtT, sqrtT


# --- verified second-order greeks (raw, unscaled), reused as the base ---------
def gamma_raw(S, K, T, r, sigma, q=0.0):
    """d(delta)/dS = d2V/dS2, per unit S. (Matches the greeks paper's gamma.)"""
    d1, _, sqrtT = _d1d2(S, K, T, r, sigma, q)
    return math.exp(-q * T) * npdf(d1) / (S * sigma * sqrtT)


def vomma_raw(S, K, T, r, sigma, q=0.0):
    """d(vega)/dsigma = d2V/dsigma2, per unit vol. (Verified vomma, unscaled.)"""
    d1, d2, sqrtT = _d1d2(S, K, T, r, sigma, q)
    vega = S * math.exp(-q * T) * npdf(d1) * sqrtT       # per unit vol
    return vega * d1 * d2 / sigma


# --- third-order closed forms (cross-check only) ------------------------------
def speed_closed(S, K, T, r, sigma, q=0.0):
    """dGamma/dS, per unit S."""
    d1, _, sqrtT = _d1d2(S, K, T, r, sigma, q)
    g = gamma_raw(S, K, T, r, sigma, q)
    return -(g / S) * (d1 / (sigma * sqrtT) + 1.0)


def zomma_closed(S, K, T, r, sigma, q=0.0):
    """dGamma/dsigma, per unit vol."""
    d1, d2, _ = _d1d2(S, K, T, r, sigma, q)
    g = gamma_raw(S, K, T, r, sigma, q)
    return g * (d1 * d2 - 1.0) / sigma


def color_perday_closed(S, K, T, r, sigma, q=0.0):
    """dGamma/dt as calendar time PASSES (T shrinks), per day.
    Haug's tabulated formula is written as dGamma/dT (per year); it therefore
    carries the opposite sign to the passage of time, so color as time passes
    is -(Haug)/365."""
    d1, d2, sqrtT = _d1d2(S, K, T, r, sigma, q)
    haug_dGamma_dT = -math.exp(-q * T) * npdf(d1) / (2.0 * S * T * sigma * sqrtT) * (
        2.0 * q * T + 1.0
        + (2.0 * (r - q) * T - d2 * sigma * sqrtT) / (sigma * sqrtT) * d1
    )
    return -haug_dGamma_dT / 365.0


def ultima_closed(S, K, T, r, sigma, q=0.0):
    """dVomma/dsigma = d3V/dsigma3, per unit vol cubed (third sigma-derivative)."""
    d1, d2, sqrtT = _d1d2(S, K, T, r, sigma, q)
    vega = S * math.exp(-q * T) * npdf(d1) * sqrtT       # per unit vol
    return (-vega / sigma ** 2) * (d1 * d2 * (1.0 - d1 * d2) + d1 * d1 + d2 * d2)


# --- central finite differences of the verified gamma / vomma -----------------
def central(f, x, h):
    return (f(x + h) - f(x - h)) / (2.0 * h)


def third_order_fd(S, K, T, r, sigma, q=0.0):
    hS, hsig, hT = 1e-2, 1e-5, 1e-6
    speed = central(lambda s: gamma_raw(s, K, T, r, sigma, q), S, hS)
    zomma = central(lambda v: gamma_raw(S, K, T, r, v, q), sigma, hsig)
    # dGamma/dt as time passes = -dGamma/dT; per day = /365
    color = -central(lambda t: gamma_raw(S, K, t, r, sigma, q), T, hT) / 365.0
    ultima = central(lambda v: vomma_raw(S, K, T, r, v, q), sigma, hsig)
    return dict(speed=speed, zomma=zomma, color=color, ultima=ultima)


if __name__ == "__main__":
    S = K = 100.0
    T = 21.0 / 252.0
    r, sigma, q = 0.04, 0.20, 0.0

    d1, d2, sqrtT = _d1d2(S, K, T, r, sigma, q)
    print("ATM one-month option  S=K=100  T=21/252  r=4%  sigma=20%  q=0")
    print(f"  d1={d1:+.5f}  d2={d2:+.5f}  gamma={gamma_raw(S,K,T,r,sigma,q):.6f}  "
          f"vomma={vomma_raw(S,K,T,r,sigma,q):+.5f}")
    print()

    fd = third_order_fd(S, K, T, r, sigma, q)
    cf = dict(
        speed=speed_closed(S, K, T, r, sigma, q),
        zomma=zomma_closed(S, K, T, r, sigma, q),
        color=color_perday_closed(S, K, T, r, sigma, q),
        ultima=ultima_closed(S, K, T, r, sigma, q),
    )
    units = dict(speed="per index point", zomma="per unit vol",
                 color="per calendar day", ultima="per unit vol cubed")

    print(f"{'greek':7s} {'finite diff':>14s} {'closed form':>14s} "
          f"{'rel.err':>10s}   units")
    max_rel = 0.0
    for name in ("speed", "zomma", "color", "ultima"):
        rel = abs(fd[name] - cf[name]) / abs(cf[name])
        max_rel = max(max_rel, rel)
        print(f"{name:7s} {fd[name]:>14.8f} {cf[name]:>14.8f} "
              f"{rel:>10.2e}   {units[name]}")
    print()
    print(f"max relative error (finite diff vs closed form): {max_rel:.2e}")
    print()

    # friendly-unit conversions quoted in the text
    print("friendly units (ATM one-month):")
    print(f"  speed  = {cf['speed']:+.5f}  per index point")
    print(f"  zomma  = {cf['zomma']:+.5f}  per unit vol  "
          f"(= {cf['zomma']/100.0:+.6f} per vol point)")
    print(f"  color  = {cf['color']:+.6f}  per calendar day  "
          f"(gamma builds into expiry at the money)")
    print(f"  ultima = {cf['ultima']:+.4f}  per unit vol cubed  "
          f"(= {cf['ultima']/1e6:+.3e} per vol point cubed)")
    print()

    # values used in the prose / figures: away from the money and near expiry
    print("moneyness / maturity samples (closed form):")
    for lab, Tm in (("1 month", 21/252), ("1 week", 5/252)):
        for m in (0.95, 1.00, 1.05):
            Sv = m * K
            print(f"  {lab:8s} S/K={m:.2f}: "
                  f"speed={speed_closed(Sv,K,Tm,r,sigma,q):+.6f}  "
                  f"zomma/pt={zomma_closed(Sv,K,Tm,r,sigma,q)/100:+.6f}  "
                  f"color/day={color_perday_closed(Sv,K,Tm,r,sigma,q):+.6f}  "
                  f"ultima={ultima_closed(Sv,K,Tm,r,sigma,q):+.3f}")
    print()

    # --- Section 7 scenario: a near-expiry ATM delta-hedged book ---------------
    print("Section 7 scenario: one-week ATM book (K=100, sigma=20%, r=4%, q=0)")
    Tw = 5.0 / 252.0
    g_atm = gamma_raw(100.0, K, Tw, r, sigma, q)
    col_atm = color_perday_closed(100.0, K, Tw, r, sigma, q)
    sp_atm = speed_closed(100.0, K, Tw, r, sigma, q)
    g_next = g_atm + col_atm            # gamma one calendar day later (from color)
    print(f"  ATM gamma today            = {g_atm:.5f}")
    print(f"  color (per day)            = {col_atm:+.5f}  "
          f"-> ATM gamma tomorrow ~ {g_next:.5f}  ({100*col_atm/g_atm:+.1f}% from time alone)")
    print(f"  speed at ATM               = {sp_atm:+.5f}  (per index point)")
    # gamma after intraday moves of +/-1% and +/-3% (actual vs linear speed estimate)
    for mv in (0.01, 0.03):
        g_up = gamma_raw(100.0 * (1 + mv), K, Tw, r, sigma, q)
        g_dn = gamma_raw(100.0 * (1 - mv), K, Tw, r, sigma, q)
        lin_up = g_atm + sp_atm * (100.0 * mv)   # first-order (speed) estimate
        print(f"  gamma after {int(mv*100):+d}% move   = {g_up:.5f} "
              f"({100*(g_up-g_atm)/g_atm:+.1f}%)   after {-int(mv*100):+d}% = {g_dn:.5f} "
              f"({100*(g_dn-g_atm)/g_atm:+.1f}%)   [speed-linear +move: {lin_up:.5f}]")
    # book-level dollar figure: short 2,000 contracts x100 multiplier
    ncontr, mult = 2000, 100
    dollar_per_pct_open = ncontr * mult * g_atm * (100.0 * 0.01)   # delta change per +1% at open gamma
    dollar_per_pct_close = ncontr * mult * g_next * (100.0 * 0.01)
    print(f"  book: short {ncontr} contracts x{mult}: re-hedge per +1% move "
          f"= {dollar_per_pct_open:,.0f} vs {dollar_per_pct_close:,.0f} index-delta "
          f"(open vs one day later): mis-size {100*(dollar_per_pct_close/dollar_per_pct_open-1):+.1f}%")
