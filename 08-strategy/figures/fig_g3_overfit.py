"""
Figure 1 (G3) - The overfitting gap: in-sample glitters, out-of-sample collapses.

The single most important picture in machine learning for trading. We train a
gradient-boosted classifier to predict the sign of the S&P 500's NEXT-day return
from a set of features - a few genuine ones (lagged returns, a momentum term, a
realized-vol term) plus deliberately added PURE NOISE features - and sweep the
model's capacity (tree depth). For each capacity we measure the Sharpe ratio of
the resulting daily long/short strategy both IN-SAMPLE (the data the model was
fit on) and OUT-OF-SAMPLE (a later, untouched period).

Free data: ^GSPC daily closes (cached, shared with the other figures).
Split (opened once): out-of-sample = 2018-01-01 onward.

The expected and honest result: as capacity rises, the in-sample Sharpe climbs
toward the sky (the model memorises the noise) while the out-of-sample Sharpe
stays near zero - a coin flip. The widening gap IS overfitting, drawn.

Reproducible:
    python fig_g3_overfit.py     # numpy, matplotlib, scikit-learn
"""
import os, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OOS_START = "2018-01-01"
rng = np.random.default_rng(0)


def load(cache):
    d, c = [], []
    with open(os.path.join(DATA, cache)) as f:
        for row in csv.DictReader(f):
            d.append(row["date"]); c.append(float(row["close"]))
    return d, np.array(c)


dates, close = load("gspc_daily.csv")
r = np.concatenate([[0.0], np.diff(np.log(close))])
N = len(dates)

# --- features known at close of day t (predict sign of r[t+1]) ---------------
def roll_mean(x, w):
    out = np.full(N, np.nan); cs = np.concatenate([[0.0], np.cumsum(x)])
    for t in range(N):
        if t + 1 >= w:
            out[t] = (cs[t + 1] - cs[t + 1 - w]) / w
    return out


def roll_std(x, w):
    out = np.full(N, np.nan)
    for t in range(N):
        if t + 1 >= w:
            out[t] = x[t + 1 - w:t + 1].std()
    return out


feats = {
    "r_lag1": r,
    "r_lag2": np.concatenate([[0.0], r[:-1]]),
    "r_lag3": np.concatenate([[0, 0.0], r[:-2]]),
    "mom10": roll_mean(r, 10) * 10,
    "vol10": roll_std(r, 10),
    "vol20": roll_std(r, 20),
}
# genuine + noise
for k in range(14):
    feats[f"noise{k}"] = rng.standard_normal(N)

X = np.column_stack([feats[k] for k in feats])
y = (np.concatenate([r[1:], [0.0]]) > 0).astype(int)     # sign of NEXT day
fwd = np.concatenate([r[1:], [0.0]])                     # next-day return for P&L

valid = ~np.isnan(X).any(axis=1)
valid[-1] = False                                        # last row has no forward
idx = np.where(valid)[0]
d_ok = [dates[i] for i in idx]
split = next(k for k, dd in enumerate(d_ok) if dd >= OOS_START)
Xv, yv, fv = X[idx], y[idx], fwd[idx]


def sharpe(sig, ret):
    s = sig * ret
    return s.mean() / s.std() * np.sqrt(252) if s.std() > 0 else 0.0


depths = [1, 2, 3, 4, 6, 8, 12]
sr_in, sr_oos = [], []
print(f"sample {d_ok[0]}..{d_ok[-1]}  n={len(idx)}  OOS from {OOS_START} (n_oos={len(idx)-split})")
print(f"{'max_depth':>9s} {'IS Sharpe':>10s} {'OOS Sharpe':>11s} {'IS acc':>7s} {'OOS acc':>8s}")
for md in depths:
    clf = GradientBoostingClassifier(n_estimators=150, max_depth=md,
                                     learning_rate=0.1, subsample=1.0, random_state=0)
    clf.fit(Xv[:split], yv[:split])
    p_in = clf.predict(Xv[:split]); p_oo = clf.predict(Xv[split:])
    sig_in = 2 * p_in - 1; sig_oo = 2 * p_oo - 1
    si = sharpe(sig_in, fv[:split]); so = sharpe(sig_oo, fv[split:])
    sr_in.append(si); sr_oos.append(so)
    acc_in = (p_in == yv[:split]).mean(); acc_oo = (p_oo == yv[split:]).mean()
    print(f"{md:9d} {si:10.2f} {so:11.2f} {acc_in:7.3f} {acc_oo:8.3f}")

# Majority-class ("always-long") baseline: the honest benchmark for a directional
# call is NOT a 50% coin flip but predicting the majority class every day. On this
# sample up-days are ~54.6%, so a model at ~52% OOS accuracy is worse than always-long.
base_acc = float((yv[split:] == 1).mean())                     # OOS up-day fraction
base_sr = sharpe(np.ones_like(fv[split:]), fv[split:])          # always-long OOS Sharpe
print(f"{'baseline':>9s} {sharpe(np.ones_like(fv[:split]), fv[:split]):10.2f} "
      f"{base_sr:11.2f} {(yv[:split]==1).mean():7.3f} {base_acc:8.3f}   "
      f"<- always-long majority-class baseline (OOS acc to beat = {base_acc:.3f})")

# ---------------- figure ------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.9, 4.3))
ax.plot(depths, sr_in, "o-", color="#7c1c2c", lw=2.0, label="in-sample (fit on this data)")
ax.plot(depths, sr_oos, "s-", color="#31536e", lw=2.0, label="out-of-sample (untouched)")
ax.axhline(0, color="#666", lw=0.7)
ax.axhline(base_sr, color="#2f6d4f", lw=1.3, ls="--",
           label=f"always-long baseline (Sharpe {base_sr:.2f}; {base_acc*100:.1f}% up-days)")
ax.fill_between(depths, sr_oos, sr_in, color="#c9a24b", alpha=0.18)
ax.annotate("the overfitting gap", xy=(8, 0.5 * (sr_in[-2] + sr_oos[-2])),
            xytext=(4.4, 0.55 * max(sr_in)), fontsize=9, color="#8a6410",
            arrowprops=dict(arrowstyle="->", color="#c9a24b", lw=1.1))
ax.set_xlabel("model capacity (gradient-boosting tree depth)", fontsize=9)
ax.set_ylabel("strategy Sharpe ratio (annualized)", fontsize=9)
ax.set_title("Adding capacity buys in-sample Sharpe and no out-of-sample edge whatsoever",
             fontsize=10.2, loc="left")
ax.legend(fontsize=8.4, frameon=False, loc="center left")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, alpha=0.22)
fig.text(0.5, -0.02,
         f"Gradient-boosted classifier predicting the sign of the next-day S&P 500 return, "
         f"6 genuine + 14 noise features. Yahoo ^GSPC, {d_ok[0]} to {d_ok[-1]}; OOS from {OOS_START}. (Emp)",
         ha="center", fontsize=7.5, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_g3_overfit.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
