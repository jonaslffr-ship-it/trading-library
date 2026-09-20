"""
Figure 3 - One-day-ahead volatility forecasts, strict out-of-sample horse race.

Free data: daily S&P 500 (^GSPC) OHLC from the shared cache data/spx_ohlc.csv.
Daily realized-variance proxy: RV_t = (overnight log gap)^2 + Garman-Klass
open-to-close variance (whole-day scale, conditionally unbiased under the GK
assumptions; negative GK days floored at zero and counted).

Pre-committed protocol (fixed BEFORE looking at any out-of-sample number):
  - Models: random walk (RV_t), GARCH(1,1) on daily returns (own QMLE,
    re-estimated each January on an expanding window), log-HAR with daily /
    weekly / monthly cascade (expanding OLS, re-fit every day, lognormal
    bias correction exp(s^2/2)).
  - Split: out-of-sample = 2020-01-02 onward, opened once. No variants tried.
  - Primary loss: QLIKE (Patton 2011). Secondary: MSE on variance.
  - Tests: Diebold-Mariano on the QLIKE loss differential (Newey-West, 5 lags),
    Clark-West for the nested log-HAR vs random-walk comparison (MSE-based).
  - Mincer-Zarnowitz levels regression RV = a + b*F per model, OOS only.

Printed: every number quoted in the paper.

Reproducible:
    python fig_har_oos.py     # numpy, matplotlib; math.erf for p-values
"""
import os, csv, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "spx_ohlc.csv")
OOS_START = "2020-01-02"

dates, O, H, L, C = [], [], [], [], []
with open(CACHE) as f:
    for row in csv.DictReader(f):
        dates.append(row["date"])
        O.append(float(row["open"])); H.append(float(row["high"]))
        L.append(float(row["low"])); C.append(float(row["close"]))
O, H, L, C = map(np.array, (O, H, L, C))

u = np.log(H[1:] / O[1:]); d = np.log(L[1:] / O[1:]); c = np.log(C[1:] / O[1:])
on = np.log(O[1:] / C[:-1]); r = np.log(C[1:] / C[:-1])
gk = 0.5 * (u - d) ** 2 - (2 * np.log(2) - 1) * c ** 2
n_neg = int((gk < 0).sum())
RV = on ** 2 + np.maximum(gk, 0.0)
RV = np.maximum(RV, 1e-10)
ddates = dates[1:]
N = len(RV)
print(f"proxy: RV = overnight^2 + max(GK,0); negative-GK days floored: {n_neg}/{N}")

# ---------------- helpers ----------------------------------------------------
def roll_mean_past(x, w):
    """mean of x[t-w+1..t] at index t (uses only info up to t)."""
    cs = np.cumsum(np.concatenate([[0.0], x]))
    out = np.full(len(x), np.nan)
    out[w - 1:] = (cs[w:] - cs[:-w]) / w
    return out


lRV = np.log(RV)
l_d = lRV
l_w = roll_mean_past(lRV, 5)
l_m = roll_mean_past(lRV, 22)

i0 = ddates.index(OOS_START)          # first OOS target index
print(f"split: in-sample {ddates[0]}..{ddates[i0-1]} ({i0} obs) | "
      f"OOS {ddates[i0]}..{ddates[-1]} ({N - i0} obs)")

# ---------------- random walk ------------------------------------------------
F_rw = RV[i0 - 1:N - 1]               # forecast for t = RV_{t-1}

# ---------------- log-HAR, expanding OLS refit daily -------------------------
F_har = np.empty(N - i0)
X_all = np.column_stack([np.ones(N), l_d, l_w, l_m])   # regressors known at t
beta_last = None
for t in range(i0, N):                # forecast target RV_t
    # training pairs: predict lRV[s] from X[s-1], s = 22..t-1
    Xtr = X_all[21:t - 1]; ytr = lRV[22:t]
    XtX = Xtr.T @ Xtr; Xty = Xtr.T @ ytr
    beta = np.linalg.solve(XtX, Xty)
    resid = ytr - Xtr @ beta
    s2 = resid.var()
    F_har[t - i0] = math.exp(float(X_all[t - 1] @ beta) + 0.5 * s2)
    beta_last = (beta, s2)
print("log-HAR final betas [const, d, w, m]:",
      np.round(beta_last[0], 3), " resid var", round(beta_last[1], 4))

# ---------------- GARCH(1,1), own QMLE, re-estimated each January ------------
def nll_garch(theta, rr):
    w = np.exp(theta[0])
    e = np.exp(np.array([theta[1], theta[2], 0.0]))
    a, b = e[0] / e.sum(), e[1] / e.sum()
    s2 = np.empty(len(rr)); s2[0] = rr.var()
    for t in range(1, len(rr)):
        s2[t] = w + a * rr[t - 1] ** 2 + b * s2[t - 1]
    if np.any(s2 <= 0) or not np.all(np.isfinite(s2)):
        return 1e10
    return 0.5 * np.sum(np.log(2 * np.pi * s2) + rr ** 2 / s2)


def nelder_mead(f, x0, args=(), maxit=1500, tol=1e-9):
    n = len(x0); sim = [np.array(x0, float)]
    for i in range(n):
        x = np.array(x0, float); x[i] += 0.25 if x[i] == 0 else 0.15 * abs(x[i]) + 0.1
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
                for i in range(1, n + 1):
                    sim[i] = sim[0] + 0.5 * (sim[i] - sim[0])
                    fv[i] = f(sim[i], *args)
    i = int(np.argmin(fv)); return sim[i], fv[i]


F_g = np.empty(N - i0)
params = None
for t in range(i0, N):
    refit = params is None or (ddates[t][:4] != ddates[t - 1][:4])
    if refit:
        mu = r[:t].mean()                 # training-window mean only (no look-ahead)
        rr = r[:t] - mu
        s2u = rr.var(); rest = 1 - 0.08 - 0.90
        th, _ = nelder_mead(nll_garch, [np.log(s2u * rest), np.log(0.08 / rest),
                                        np.log(0.90 / rest)], args=(rr,))
        w = np.exp(th[0]); e = np.exp(np.array([th[1], th[2], 0.0]))
        a, b = e[0] / e.sum(), e[1] / e.sum()
        params = (w, a, b, mu)
        # rebuild the variance recursion through day t-1 -> forecast for day t
        s2_state = rr.var()
        for s in range(1, t + 1):
            s2_state = w + a * (r[s - 1] - mu) ** 2 + b * s2_state
    else:
        w, a, b, mu = params
        s2_state = w + a * (r[t - 1] - mu) ** 2 + b * s2_state
    F_g[t - i0] = s2_state

y = RV[i0:]
models = {"random walk": F_rw, "GARCH(1,1)": F_g, "log-HAR": F_har}

# ---------------- losses & tests ---------------------------------------------
def qlike(yy, ff):
    z = yy / ff
    return z - np.log(z) - 1.0


def nw_se(x, lags=5):
    x = x - x.mean(); n = len(x)
    g0 = np.sum(x * x) / n
    s = g0
    for k in range(1, lags + 1):
        gk = np.sum(x[k:] * x[:-k]) / n
        s += 2 * (1 - k / (lags + 1)) * gk
    return math.sqrt(s / n)


def phi(z):                      # standard normal CDF via erf
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


print("\nOOS losses (lower = better):")
for k, F in models.items():
    ql = qlike(y, F).mean(); mse = np.mean((y - F) ** 2)
    print(f"  {k:12s} QLIKE={ql:.4f}  MSE={mse:.3e}")

print("\nMincer-Zarnowitz (OOS): RV = a + b*F")
for k, F in models.items():
    X = np.column_stack([np.ones_like(F), F])
    bhat = np.linalg.solve(X.T @ X, X.T @ y)
    res = y - X @ bhat
    R2 = 1 - res.var() / y.var()
    print(f"  {k:12s} a={bhat[0]:.3e}  b={bhat[1]:.3f}  R2={R2:.3f}")

dlq = qlike(y, models["random walk"]) - qlike(y, models["log-HAR"])
dm = dlq.mean() / nw_se(dlq)
print(f"\nDM (QLIKE, HAR vs RW): mean diff={dlq.mean():.4f}  DM={dm:.2f}  "
      f"one-sided p={1 - phi(dm):.2e}")
dlg = qlike(y, models["random walk"]) - qlike(y, models["GARCH(1,1)"])
dmg = dlg.mean() / nw_se(dlg)
print(f"DM (QLIKE, GARCH vs RW): mean diff={dlg.mean():.4f}  DM={dmg:.2f}  "
      f"one-sided p={1 - phi(dmg) if dmg > 0 else phi(dmg):.2e}")

f_cw = (y - F_rw) ** 2 - ((y - F_har) ** 2 - (F_rw - F_har) ** 2)
cw = f_cw.mean() / nw_se(f_cw)
print(f"Clark-West (HAR vs RW, nested): CW={cw:.2f}  one-sided p={1 - phi(cw):.2e}")

# ---------------- figure ------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(6.9, 5.8), gridspec_kw={"height_ratios": [2.1, 1.0]})

xs = np.arange(N - i0)
ax1.plot(xs, np.sqrt(252 * y) * 100, lw=0.55, color="#b8b0a4", label="realized (proxy)")
ax1.plot(xs, np.sqrt(252 * F_har) * 100, lw=0.9, color="#7c1c2c", label="log-HAR forecast")
ax1.plot(xs, np.sqrt(252 * F_g) * 100, lw=0.7, color="#31536e", alpha=0.8,
         label="GARCH(1,1) forecast")
tick = [i for i in range(1, N - i0) if ddates[i0 + i][:4] != ddates[i0 + i - 1][:4]]
ax1.set_xticks(tick); ax1.set_xticklabels([ddates[i0 + i][:4] for i in tick], fontsize=8)
ax1.set_ylabel("annualized volatility (%)")
ax1.set_yscale("log"); ax1.set_yticks([5, 10, 20, 40, 80]); ax1.set_yticklabels([5, 10, 20, 40, 80])
ax1.legend(fontsize=7.5, frameon=False, ncol=3)
ax1.set_title("(a)  Out-of-sample one-day-ahead forecasts, 2020-2026 (log scale)",
              fontsize=9.5, loc="left")
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)
ax1.grid(True, axis="y", alpha=0.25)

names = list(models)
qls = [qlike(y, models[k]).mean() for k in names]
cols = {"random walk": "#8a8a8a", "GARCH(1,1)": "#31536e", "log-HAR": "#7c1c2c"}
ax2.barh(range(len(names)), qls, color=[cols[k] for k in names], alpha=0.9, height=0.6)
for i, v in enumerate(qls):
    ax2.text(v + 0.005, i, f"{v:.3f}", va="center", fontsize=8.5)
ax2.set_yticks(range(len(names))); ax2.set_yticklabels(names, fontsize=8.5)
ax2.invert_yaxis(); ax2.set_xlim(0, max(qls) * 1.2)
ax2.set_xlabel("mean OOS QLIKE (lower = better)", fontsize=8.5)
ax2.set_title("(b)  Primary loss, pre-committed: QLIKE", fontsize=9.5, loc="left")
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)

fig.text(0.5, -0.015,
         f"Yahoo daily ^GSPC OHLC. OOS = {ddates[i0]} to {ddates[-1]} ({N - i0} days), "
         "opened once; models re-estimated on expanding windows with data strictly prior "
         "to each forecast.", ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_har_oos.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
