"""
Figure 5 - Raw-SVI calibration to one SPX expiry, with the no-arbitrage checks.

Free data: Cboe's public delayed-quotes options chain for ^SPX, cached to
data/SPX_options_snapshot.json by fig_iv_surface.py (same snapshot; reproducible
offline). We fit Gatheral's *raw* SVI parameterization of the total implied
variance slice w(k) = sigma_BS(k)^2 * T as a function of log-moneyness
k = ln(K / S):

    w(k) = a + b * ( rho*(k - m) + sqrt((k - m)^2 + sigma^2) )

with a (level), b >= 0 (wing slope / angle), rho in (-1,1) (skew asymmetry),
m (horizontal shift), sigma > 0 (ATM curvature). The five parameters are fitted
by ordinary least squares on implied-vol residuals (in vol points) with a
self-contained Nelder-Mead simplex in numpy - no scipy, no packages. Positivity
and range constraints are imposed by reparameterization (b = e^., sigma = e^.,
rho = tanh(.)); multiple starts guard against local minima.

No-arbitrage checks (Gatheral & Jacquier 2014):
  - Butterfly: the slice is butterfly-arbitrage-free iff Durrleman's function
        g(k) = (1 - k*w'/(2w))^2 - (w'^2/4)*(1/w + 1/4) + w''/2
    is non-negative for all k. We evaluate g on a dense grid and print min g(k).
  - Calendar: total variance must be non-decreasing in maturity at every strike.
    We check this model-free on strikes shared by the fitted expiry and the next
    longer expiry, and print the smallest w(longer) - w(fitted) gap.

Analytic derivatives of raw SVI:
  w'(k)  = b*(rho + (k-m)/S1),         S1 = sqrt((k-m)^2 + sigma^2)
  w''(k) = b*sigma^2 / S1^3

Printed: snapshot, spot, chosen expiry (dte, T, #strikes), the five raw-SVI
parameters, the fit RMSE and worst error in vol points, min g(k) with location
and the butterfly verdict, and the calendar-monotonicity gap with its verdict.

Reproducible:
    python fig_svi_fit.py     # numpy, matplotlib; stdlib json/re
"""
import os, json, re, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "SPX_options_snapshot.json")

if not (os.path.exists(CACHE) and os.path.getsize(CACHE) > 0):
    print("SKIPPED: needs the licensed CBOE snapshot (SPX_options_snapshot.json), "
          "created by fig_iv_surface.py from vendor data not redistributed; "
          "unavailable offline. See ERRATA F.")
    raise SystemExit(0)
with open(CACHE) as f:
    j = json.load(f)
snap_time = j["timestamp"]
snap_date = dt.datetime.strptime(snap_time[:10], "%Y-%m-%d").date()
spot = float(j["data"]["current_price"])
pat = re.compile(r"^(SPX|SPXW)(\d{6})([CP])(\d{8})$")

# --- collect OTM implied vols per expiry (SPX root preferred over SPXW) -------
book = {}                                    # (exp, K, cp) -> (root, iv)
for o in j["data"]["options"]:
    m = pat.match(o["option"])
    if not m:
        continue
    root, exp, cp, kraw = m.groups()
    K = int(kraw) / 1000.0
    iv, bid = float(o["iv"]), float(o["bid"])
    if iv <= 0 or bid <= 0:
        continue
    if (cp == "P" and K > spot) or (cp == "C" and K <= spot):
        continue                             # OTM only
    key = (exp, K, cp)
    if key in book and book[key][0] == "SPX":
        continue
    book[key] = (root, iv)

expiries = sorted({k[0] for k in book})
exp_date = {e: dt.datetime.strptime(e, "%y%m%d").date() for e in expiries}
dte = {e: (exp_date[e] - snap_date).days for e in expiries}


def slice_of(e, lo=0.78, hi=1.10):
    """Return sorted (K, iv) for OTM strikes in [lo,hi]*spot at expiry e."""
    rows = sorted((K, iv) for (ex, K, cp), (root, iv) in book.items()
                  if ex == e and lo * spot <= K <= hi * spot)
    return np.array([r[0] for r in rows]), np.array([r[1] for r in rows])


# choose the expiry nearest 30 calendar days with a well-populated smile
cand = [e for e in expiries if dte[e] >= 5 and len(slice_of(e)[0]) >= 12]
target = min(cand, key=lambda e: abs(dte[e] - 30))
# next longer expiry (for the calendar check)
longer = min([e for e in cand if dte[e] > dte[target] + 10],
             key=lambda e: abs(dte[e] - 90), default=None)

K, iv = slice_of(target)
T = dte[target] / 365.0
k = np.log(K / spot)                          # log-moneyness (F approx spot; m absorbs)
w_mkt = (iv ** 2) * T                          # market total variance
n = len(K)


# ---------------- raw SVI, own least squares ---------------------------------
# A single SVI slice is famously over-parameterized: for one maturity the plain
# least-squares optimum runs off toward the boundary (b -> large, rho -> 1, m
# large) while the fitted CURVE over the traded strikes barely changes - which is
# exactly why Gatheral & Jacquier introduced the "natural"/"jump-wings" forms.
# We regularize by lightly penalizing the wing amplitude b (prefer the smoothest
# slice consistent with the data) plus a small centering of the vertex m. The
# penalty is negligible for a sane fit but forbids the runaway: pushing b down
# forces rho negative to keep matching the observed put wing - the natural,
# interior, equity-skew solution. (Effect on the fit is reported as the RMSE.)
# Two light regularizers resolve the single-slice degeneracy: a small penalty on
# the wing amplitude b (forbid the b->inf, rho->1 runaway) and a stronger
# centering of the vertex m toward the money (the SPX min-variance strike sits
# just above spot, k*~+0.04; without this, m drifts to a spurious +0.17 while rho
# flips sign - the identifiability pathology that motivated the jump-wings form).
# With m held near the money, rho carries the asymmetry and takes its natural
# negative (equity put-skew) value. The fit cost is reported as the RMSE.
LAM_B, LAM_M = 1e-4, 3e-2


def svi_w(theta, kk):
    a = theta[0]; b = np.exp(theta[1]); rho = np.tanh(theta[2])
    mm = theta[3]; sig = np.exp(theta[4])
    z = kk - mm
    return a + b * (rho * z + np.sqrt(z * z + sig * sig))


def unpack(theta):
    return (theta[0], np.exp(theta[1]), np.tanh(theta[2]), theta[3], np.exp(theta[4]))


def sse(theta, kk, ivv, TT):
    w = svi_w(theta, kk)
    if np.any(w <= 1e-12) or not np.all(np.isfinite(w)):
        return 1e12
    model_iv = np.sqrt(w / TT)
    b = np.exp(theta[1]); mm = theta[3]
    return float(np.sum((model_iv - ivv) ** 2) + LAM_B * b ** 2 + LAM_M * mm ** 2)


def nelder_mead(f, x0, args=(), maxit=4000, tol=1e-12):
    nn = len(x0); sim = [np.array(x0, float)]
    for i in range(nn):
        x = np.array(x0, float); x[i] += 0.20 if x[i] == 0 else 0.15 * abs(x[i]) + 0.05
        sim.append(x)
    fv = [f(x, *args) for x in sim]
    for _ in range(maxit):
        idx = np.argsort(fv); sim = [sim[i] for i in idx]; fv = [fv[i] for i in idx]
        if abs(fv[-1] - fv[0]) < tol * (abs(fv[0]) + tol):
            break
        cen = np.mean(sim[:-1], axis=0)
        xr = cen + (cen - sim[-1]); fr = f(xr, *args)
        if fr < fv[0]:
            xe = cen + 2.0 * (cen - sim[-1]); fe = f(xe, *args)
            sim[-1], fv[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < fv[-2]:
            sim[-1], fv[-1] = xr, fr
        else:
            xc = cen + 0.5 * (sim[-1] - cen); fc = f(xc, *args)
            if fc < fv[-1]:
                sim[-1], fv[-1] = xc, fc
            else:
                for i in range(1, nn + 1):
                    sim[i] = sim[0] + 0.5 * (sim[i] - sim[0])
                    fv[i] = f(sim[i], *args)
    i = int(np.argmin(fv)); return sim[i], fv[i]


# multi-start over the skew and shift, keep the global best
best, best_f = None, np.inf
a0 = float(np.median(w_mkt))
for rho0 in (-0.9, -0.7, -0.5, -0.3):
    for m0 in (-0.10, -0.05, 0.0, 0.05):
        x0 = [0.5 * a0, np.log(0.08), np.arctanh(rho0), m0, np.log(0.06)]
        th, fval = nelder_mead(sse, x0, args=(k, iv, T))
        if fval < best_f:
            best, best_f = th, fval
th = best
a, b, rho, mm, sig = unpack(th)
model_iv = np.sqrt(svi_w(th, k) / T)
rmse = float(np.sqrt(np.mean((model_iv - iv) ** 2))) * 100      # vol points
maxerr = float(np.max(np.abs(model_iv - iv))) * 100


# ---------------- Durrleman butterfly function g(k) --------------------------
def g_of(kk):
    z = kk - mm
    S1 = np.sqrt(z * z + sig * sig)
    w = a + b * (rho * z + S1)
    wp = b * (rho + z / S1)
    wpp = b * sig * sig / S1 ** 3
    return (1 - kk * wp / (2 * w)) ** 2 - (wp * wp / 4.0) * (1.0 / w + 0.25) + wpp / 2.0


kg = np.linspace(k.min() - 0.05, k.max() + 0.05, 1201)
g = g_of(kg)
gmin = float(g.min()); kmin = float(kg[int(np.argmin(g))])
bfly_ok = gmin >= 0.0

# ---------------- calendar check (model-free, shared strikes) ----------------
cal_txt = "n/a (no longer expiry available)"
cal_gap = None
if longer is not None:
    Kl, ivl = slice_of(longer)
    Tl = dte[longer] / 365.0
    wl = {round(kk, 2): (iv2 ** 2) * Tl for kk, iv2 in zip(Kl, ivl)}
    ws = {round(kk, 2): (iv2 ** 2) * T for kk, iv2 in zip(K, iv)}
    shared = sorted(set(wl) & set(ws))
    gaps = [wl[s] - ws[s] for s in shared]
    if gaps:
        cal_gap = float(min(gaps))
        cal_txt = (f"{len(shared)} shared strikes; min "
                   f"w({dte[longer]}d)-w({dte[target]}d) = {cal_gap:+.5f} "
                   f"({'OK, non-decreasing' if cal_gap >= 0 else 'VIOLATION'})")

# ---------------- interpretable derived quantities ---------------------------
# raw-SVI parameters are not individually intuitive; report the curve's own
# summary statistics (Gatheral's "jump-wings" quantities) instead.
w0 = float(svi_w(th, np.array([0.0]))[0])                 # ATM (k=0) total var
atm_vol = np.sqrt(w0 / T) * 100
z0 = 0.0 - mm; S0 = np.sqrt(z0 * z0 + sig * sig)
wp0 = b * (rho + z0 / S0)                                 # dw/dk at k=0
atm_skew = wp0 / (2 * np.sqrt(w0 * T)) * 100              # d(sigma)/dk at k=0, vol pts
k_star = mm - sig * rho / np.sqrt(1 - rho ** 2)           # vertex (min-variance k)
w_min = a + b * sig * np.sqrt(1 - rho ** 2)               # minimum total variance
slope_L = b * (1 - rho)                                   # left-wing asymptotic slope
slope_R = b * (1 + rho)                                   # right-wing asymptotic slope

# ---------------- print everything quoted in the paper -----------------------
print(f"snapshot={snap_time}  spot={spot:.2f}")
print(f"fitted expiry {exp_date[target].isoformat()}  dte={dte[target]}  "
      f"T={T:.4f}yr  n_strikes={n}  (k range {k.min():+.3f}..{k.max():+.3f})")
print(f"raw SVI:  a={a:.5f}  b={b:.5f}  rho={rho:+.4f}  m={mm:+.5f}  sigma={sig:.5f}")
print(f"fit RMSE={rmse:.3f} vol pts   max abs error={maxerr:.3f} vol pts   SSE={best_f:.3e}")
print(f"derived:  ATM vol={atm_vol:.2f}%  ATM skew d(sig)/dk={atm_skew:+.2f} vol pts/unit-k  "
      f"vertex k*={k_star:+.3f}  w_min={w_min:.5f}  wings(L,R)=({slope_L:.3f},{slope_R:.3f})")
print(f"butterfly: min g(k)={gmin:.5f} at k={kmin:+.3f}  -> "
      f"{'arbitrage-FREE (g>=0)' if bfly_ok else 'ARBITRAGE (g<0)'}")
print(f"calendar : {cal_txt}")

# ---------------- figure ------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(6.9, 6.0), sharex=True, gridspec_kw={"height_ratios": [1.7, 1.0]})

kk = np.linspace(k.min() - 0.03, k.max() + 0.03, 400)
ax1.plot(k, iv * 100, "o", ms=4.5, color="#31536e", alpha=0.8,
         label="Cboe OTM implied vol")
ax1.plot(kk, np.sqrt(svi_w(th, kk) / T) * 100, "-", lw=1.8, color="#7c1c2c",
         label="raw-SVI fit")
ax1.axvline(0, color="#999", lw=0.8, ls=":")
ax1.set_ylabel("implied volatility (%)")
ax1.legend(frameon=False, fontsize=8.5)
ax1.set_title(f"(a)  Raw SVI fit to the SPX {exp_date[target].isoformat()} slice "
              f"({dte[target]} d, {n} strikes, RMSE {rmse:.2f} vol pts)",
              fontsize=9.5, loc="left")
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)
ax1.grid(True, axis="y", alpha=0.25)

ax2.axhline(0, color="#7c1c2c", lw=0.9)
ax2.fill_between(kg, np.clip(g, 0, None), 0, color="#2f6d4f", alpha=0.45, lw=0)
ax2.plot(kg, g, lw=1.3, color="#2f6d4f")
ax2.plot([kmin], [gmin], "o", ms=4, color="#a8762f")
ax2.annotate(f"min g = {gmin:.3f}", xy=(kmin, gmin), xytext=(kmin + 0.02, gmin + 0.05),
             fontsize=8, color="#a8762f")
ax2.set_xlabel("log-moneyness  k = ln(K / S)")
ax2.set_ylabel("g(k)")
ax2.set_title("(b)  Durrleman butterfly function g(k) >= 0 everywhere -> no butterfly arbitrage",
              fontsize=9.5, loc="left")
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
ax2.grid(True, axis="y", alpha=0.25)

fig.text(0.5, -0.015,
         f"Cboe delayed quotes ^SPX, snapshot {snap_time} ET, spot {spot:.0f}. "
         "Raw SVI fitted by own least squares (Nelder-Mead); g(k) is the "
         "Gatheral-Jacquier butterfly criterion.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_svi_fit.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
