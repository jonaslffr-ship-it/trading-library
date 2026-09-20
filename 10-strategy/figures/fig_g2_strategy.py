"""
Figure 2 (G2) - Trading the IV-RV gap: a pre-registered short-variance rule.

A delta-hedged short option position earns implied variance and pays realized
variance; over a month its P&L is approximately proportional to
(sigma_implied^2 - sigma_realized^2). We harvest exactly that, monthly, on free
data, and ask the honest question: does CONDITIONING on a volatility forecast
improve on just selling variance unconditionally?

Free data: ^GSPC + ^VIX daily closes (cached, shared with G1).

Pre-registered rule (fixed in advance, no optimization over the sample):
  - Each month t (first trading day), the short-variance P&L over the next 21
    trading days is  pnl_t = (VIX_t/100)^2 - RV_ann_t - cost,  where RV_ann_t is
    the annualized realized variance of daily log returns over those 21 days and
    cost = 0.0015 annualized-variance points is a stylized round-trip friction.
  - UNCONDITIONAL: take the short every month.
  - CONDITIONAL: take the short only when a HAR forecast (fitted in-sample only)
    predicts realized variance BELOW implied - i.e. only when vol looks rich.
  - Split opened once: out-of-sample = 2020-01-02 onward.

Reported: annualized Sharpe of the monthly P&L (mean/sd * sqrt(12)), hit rate,
worst month, and the same split in-sample vs OOS, for both variants. The honest
expected finding: the unconditional variance premium is the bulk of the return,
the forecast conditioning trims a little tail risk and adds little edge - which
is exactly the paper's thesis about beating implied vol.

Reproducible:
    python fig_g2_strategy.py     # numpy, matplotlib; stdlib
"""
import os, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OOS_START = "2020-01-02"
H, COST = 21, 0.0015


def load(cache):
    d, c = [], []
    with open(os.path.join(DATA, cache)) as f:
        for row in csv.DictReader(f):
            d.append(row["date"]); c.append(float(row["close"]))
    return d, np.array(c)


gd, gc = load("gspc_daily.csv")
vd, vc = load("vix_daily.csv")
vix = dict(zip(vd, vc))
dates, close, vv = [], [], []
for d, c in zip(gd, gc):
    if d in vix:
        dates.append(d); close.append(c); vv.append(vix[d])
close = np.array(close); vv = np.array(vv)
r = np.concatenate([[0.0], np.diff(np.log(close))])
rv = r ** 2
N = len(dates)


def trail_mean(x, w):
    out = np.full(N, np.nan); cs = np.concatenate([[0.0], np.cumsum(x)])
    for t in range(N):
        if t + 1 >= w:
            out[t] = (cs[t + 1] - cs[t + 1 - w]) / w
    return out


rv_d, rv_w, rv_m = trail_mean(rv, 1), trail_mean(rv, 5), trail_mean(rv, 22)
cs = np.concatenate([[0.0], np.cumsum(rv)])

# monthly entries
entries = [i for i in range(1, N) if dates[i][:7] != dates[i - 1][:7] and i + H < N and not np.isnan(rv_m[i])]
m_dates, iv2, rv2, Xd, Xw, Xm = [], [], [], [], [], []
for e in entries:
    rvf = (cs[e + 1 + H] - cs[e + 1]) / H * 252.0          # annualized realized var, next 21d
    m_dates.append(dates[e]); iv2.append((vv[e] / 100.0) ** 2)
    rv2.append(rvf); Xd.append(rv_d[e] * 252); Xw.append(rv_w[e] * 252); Xm.append(rv_m[e] * 252)
iv2 = np.array(iv2); rv2 = np.array(rv2)
Xd, Xw, Xm = np.array(Xd), np.array(Xw), np.array(Xm)
M = len(m_dates)
split = next(k for k, dd in enumerate(m_dates) if dd >= OOS_START)

# HAR forecast of annualized realized variance, fitted in-sample only
A = np.column_stack([np.ones(M), Xd, Xw, Xm])
coef, *_ = np.linalg.lstsq(A[:split], rv2[:split], rcond=None)
har = np.clip(A @ coef, 1e-9, None)

pnl_uncond = iv2 - rv2 - COST
take = har < iv2                                            # forecast says vol is rich
pnl_cond = np.where(take, iv2 - rv2 - COST, 0.0)


def stats(p, lo, hi):
    x = p[lo:hi]; x = x[~np.isnan(x)]
    sr = x.mean() / x.std() * np.sqrt(12) if x.std() > 0 else 0.0
    return sr, 100 * (x > 0).mean(), x.min()


print(f"months={M}  OOS from {OOS_START} (n_oos={M-split})  trades taken (cond): "
      f"{take.sum()} / {M} ({100*take.mean():.0f}%)")
for name, p in (("unconditional short-var", pnl_uncond), ("HAR-conditional short-var", pnl_cond)):
    sr_f, hit_f, wm_f = stats(p, 0, M)
    sr_i, _, _ = stats(p, 0, split)
    sr_o, hit_o, wm_o = stats(p, split, M)
    print(f"{name:26s} Sharpe full={sr_f:4.2f} in={sr_i:4.2f} OOS={sr_o:4.2f}  "
          f"hit={hit_f:4.1f}%  worst month={wm_f:+.4f} var-pts")
worst = np.argsort(pnl_uncond)[:5]
print("  worst unconditional months:", [(m_dates[i], round(float(pnl_uncond[i]), 4)) for i in sorted(worst)])

# ---------------- figure ------------------------------------------------------
x = np.arange(M)
eq_u = np.cumsum(np.nan_to_num(pnl_uncond))
eq_c = np.cumsum(np.nan_to_num(pnl_cond))
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.9, 5.8), sharex=True,
                               gridspec_kw={"height_ratios": [1.25, 1.0]})

ax1.axvline(split, color="#999", lw=0.8, ls=":")
ax1.text(split, eq_u.max() * 0.05, " OOS", fontsize=7.5, color="#666")
ax1.plot(x, eq_u, color="#7c1c2c", lw=1.5, label="unconditional short variance")
ax1.plot(x, eq_c, color="#2f6d4f", lw=1.5, label="HAR-conditional (short only when vol looks rich)")
ax1.axhline(0, color="#666", lw=0.6)
ax1.set_ylabel("cumulative P&L\n(annualized variance points)")
ax1.set_title("(a)  Harvesting the variance premium - and the crashes that pay it back", fontsize=9.3,
              loc="left")
ax1.legend(fontsize=7.6, frameon=False, loc="upper left")
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)
ax1.grid(True, axis="y", alpha=0.25)

ax2.bar(x, np.nan_to_num(pnl_uncond), width=1.0,
        color=np.where(np.nan_to_num(pnl_uncond) >= 0, "#2f6d4f", "#7c1c2c"))
ax2.axhline(0, color="#666", lw=0.6)
ax2.set_ylabel("monthly P&L\n(variance points)")
ax2.set_title("(b)  Small steady gains, rare violent losses (the short-vol signature)", fontsize=9.3,
              loc="left")
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
ax2.grid(True, axis="y", alpha=0.25)
yr = [i for i in range(1, M) if m_dates[i][:4] != m_dates[i - 1][:4] and int(m_dates[i][:4]) % 3 == 0]
ax2.set_xticks(yr); ax2.set_xticklabels([m_dates[i][:4] for i in yr], fontsize=8)

fig.text(0.5, -0.015,
         f"Yahoo ^GSPC + ^VIX, {m_dates[0]} to {m_dates[-1]}, non-overlapping monthly. "
         "Short-variance P&L = (VIX/100)^2 - realized annualized variance - 0.0015 cost. "
         "HAR fitted in-sample only; single fixed rule, no optimization. (Emp)",
         ha="center", fontsize=7.3, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_g2_strategy.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
