"""
Figure 2 - GARCH(1,1) fitted to S&P 500 daily returns by own maximum likelihood.

Free data: daily S&P 500 (^GSPC) closes from the shared cache data/spx_ohlc.csv
(created by fig_rv_estimators.py from Yahoo's public chart API). A GARCH(1,1)
with Gaussian quasi-likelihood is fitted to demeaned daily log returns with a
self-contained Nelder-Mead optimizer in numpy (no scipy, no packages): the
persistence constraint alpha + beta < 1 is enforced by a softmax
reparameterization. A GJR-GARCH(1,1) is fitted the same way to quantify the
leverage asymmetry. Panel (a): conditional volatility vs |returns|;
panel (b): news-impact curves of the two fits.

Printed: omega, alpha, beta, persistence, half-life, long-run vol, log-lik for
GARCH(1,1); omega, alpha, gamma, beta for GJR; and the likelihood-ratio stat.

Reproducible:
    python fig_garch_fit.py     # numpy, matplotlib only
"""
import os, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "spx_ohlc.csv")

dates, close = [], []
with open(CACHE) as f:
    for row in csv.DictReader(f):
        dates.append(row["date"]); close.append(float(row["close"]))
close = np.array(close)
r = np.diff(np.log(close))
r = r - r.mean()                       # demean once; QMLE on residuals
N = len(r)
s2u = r.var()                          # unconditional variance


def nll_garch(theta, r, gjr=False):
    """Negative Gaussian log-likelihood. Softmax keeps alpha+beta(+gamma/2)<1."""
    if gjr:
        w = np.exp(theta[0])
        e = np.exp(np.array([theta[1], theta[2], theta[3], 0.0]))
        a, g, b = e[0] / e.sum(), e[1] / e.sum(), e[2] / e.sum()
        # persistence a + g/2 + b < 1 automatically since a+g+b < 1
    else:
        w = np.exp(theta[0])
        e = np.exp(np.array([theta[1], theta[2], 0.0]))
        a, b = e[0] / e.sum(), e[1] / e.sum()
        g = 0.0
    s2 = np.empty(len(r)); s2[0] = r.var()
    for t in range(1, len(r)):
        s2[t] = w + (a + g * (r[t - 1] < 0)) * r[t - 1] ** 2 + b * s2[t - 1]
    if np.any(s2 <= 0) or not np.all(np.isfinite(s2)):
        return 1e10
    return 0.5 * np.sum(np.log(2 * np.pi * s2) + r ** 2 / s2)


def nelder_mead(f, x0, args=(), maxit=2000, tol=1e-9):
    """Minimal Nelder-Mead simplex (standard coefficients)."""
    n = len(x0)
    sim = [np.array(x0, float)]
    for i in range(n):
        x = np.array(x0, float); x[i] += 0.25 if x[i] == 0 else 0.15 * abs(x[i]) + 0.1
        sim.append(x)
    fv = [f(x, *args) for x in sim]
    for _ in range(maxit):
        idx = np.argsort(fv); sim = [sim[i] for i in idx]; fv = [fv[i] for i in idx]
        if abs(fv[-1] - fv[0]) < tol * (abs(fv[0]) + tol):
            break
        cen = np.mean(sim[:-1], axis=0)
        xr = cen + (cen - sim[-1]); fr = f(xr, *args)          # reflect
        if fr < fv[0]:
            xe = cen + 2.0 * (cen - sim[-1]); fe = f(xe, *args)  # expand
            sim[-1], fv[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < fv[-2]:
            sim[-1], fv[-1] = xr, fr
        else:
            xc = cen + 0.5 * (sim[-1] - cen); fc = f(xc, *args)  # contract
            if fc < fv[-1]:
                sim[-1], fv[-1] = xc, fc
            else:                                                 # shrink
                for i in range(1, n + 1):
                    sim[i] = sim[0] + 0.5 * (sim[i] - sim[0])
                    fv[i] = f(sim[i], *args)
    i = int(np.argmin(fv))
    return sim[i], fv[i]


# --- fit GARCH(1,1); start at variance targeting (alpha .08, beta .90) -------
def start(a, b, g=None):
    if g is None:
        rest = 1 - a - b
        return [np.log(s2u * rest), np.log(a / rest), np.log(b / rest)]
    rest = 1 - a - b - g
    return [np.log(s2u * rest), np.log(a / rest), np.log(g / rest), np.log(b / rest)]


th, nll = nelder_mead(nll_garch, start(0.08, 0.90), args=(r,))
w = np.exp(th[0]); e = np.exp(np.array([th[1], th[2], 0.0]))
a, b = e[0] / e.sum(), e[1] / e.sum()
pers = a + b
lrv = np.sqrt(252 * w / (1 - pers))
half = np.log(0.5) / np.log(pers)
print(f"GARCH(1,1): omega={w:.3e} alpha={a:.4f} beta={b:.4f} "
      f"persistence={pers:.4f} half-life={half:.1f}d long-run vol={lrv*100:.2f}% "
      f"logL={-nll:.1f}  N={N}")

thg, nllg = nelder_mead(nll_garch, start(0.02, 0.85, 0.10), args=(r, True))
wg = np.exp(thg[0]); eg = np.exp(np.array([thg[1], thg[2], thg[3], 0.0]))
ag, gg, bg = eg[0] / eg.sum(), eg[1] / eg.sum(), eg[2] / eg.sum()
persg = ag + gg / 2 + bg
print(f"GJR-GARCH : omega={wg:.3e} alpha={ag:.4f} gamma={gg:.4f} beta={bg:.4f} "
      f"persistence={persg:.4f} logL={-nllg:.1f}  LR stat={2 * (nll - nllg):.1f}")

# --- conditional vol path (GARCH) -------------------------------------------
s2 = np.empty(N); s2[0] = r.var()
for t in range(1, N):
    s2[t] = w + a * r[t - 1] ** 2 + b * s2[t - 1]
cvol = np.sqrt(252 * s2) * 100

# --- figure ---
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(6.9, 5.8), gridspec_kw={"height_ratios": [2.2, 1.0]})

x = np.arange(N)
ax1.plot(x, np.abs(r) * np.sqrt(252) * 100, lw=0.4, color="#c9c2b8",
         label="|daily return| (annualized)")
ax1.plot(x, cvol, lw=1.0, color="#7c1c2c", label="GARCH(1,1) conditional vol")
ticks = [i for i in range(1, N) if dates[i][:4] != dates[i - 1][:4] and int(dates[i][:4]) % 2 == 0]
ax1.set_xticks(ticks); ax1.set_xticklabels([dates[i][:4] for i in ticks], fontsize=8)
ax1.set_ylabel("annualized volatility (%)")
ax1.set_ylim(0, 130)
ax1.legend(fontsize=8, frameon=False)
ax1.set_title("(a)  Conditional volatility tracks clusters, then decays geometrically",
              fontsize=9.5, loc="left")
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)
ax1.grid(True, axis="y", alpha=0.25)

eps = np.linspace(-0.04, 0.04, 401)
nic_g = w + a * eps ** 2 + b * s2u
nic_gjr = wg + (ag + gg * (eps < 0)) * eps ** 2 + bg * s2u
ax2.plot(eps * 100, np.sqrt(252 * nic_g) * 100, lw=1.4, color="#31536e",
         label="GARCH(1,1): symmetric")
ax2.plot(eps * 100, np.sqrt(252 * nic_gjr) * 100, lw=1.4, color="#a8763e",
         label="GJR: negative returns hit harder")
ax2.set_xlabel("yesterday's return (%)"); ax2.set_ylabel("next-day vol (%)")
ax2.legend(fontsize=8, frameon=False)
ax2.set_title("(b)  News-impact curves (evaluated at unconditional variance)",
              fontsize=9.5, loc="left")
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
ax2.grid(True, axis="y", alpha=0.25)

fig.text(0.5, -0.015,
         f"Yahoo daily ^GSPC, {dates[1]}-{dates[-1]}, {N} returns. Own Gaussian QMLE "
         "(Nelder-Mead, softmax constraint); no packages beyond numpy/matplotlib.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_garch_fit.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
