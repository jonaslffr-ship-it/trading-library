#!/usr/bin/env python3
"""Anti-overfitting validation harness (Lopez de Prado / Bailey et al.).

Every strategy should pass through here, not just report a raw Sharpe:
  - Probabilistic Sharpe Ratio (PSR): P(true SR > benchmark), skew/kurtosis-aware.
  - Deflated Sharpe Ratio (DSR): PSR against the EXPECTED-MAX SR of N trials -> kills
    the "best of many configs" illusion (Bailey & Lopez de Prado 2014).
  - PBO via CSCV: Probability of Backtest Overfitting (Bailey et al. 2017).
  - Purged & embargoed K-fold CV generator (AFML ch. 7) for leakage-free tuning.
  - Block-bootstrap confidence intervals for the (annualized) Sharpe.

Demo (__main__): build a grid of vol-managed configs on SPX and report DSR + PBO
for the in-sample-best -> an honest read on whether the edge survives selection.
Run from repo root:  python validation.py
"""
from __future__ import annotations

import itertools
import numpy as np
import pandas as pd
from scipy.stats import norm, rankdata

PPY = 252
GAMMA = 0.5772156649015329  # Euler-Mascheroni


def _sr(ret):
    """Per-period Sharpe (ddof=1)."""
    r = np.asarray(ret, float); r = r[~np.isnan(r)]
    sd = r.std(ddof=1)
    return r.mean() / sd if sd > 0 else np.nan


def psr(ret, sr_bench_pp=0.0):
    """Probabilistic Sharpe Ratio: P(true per-period SR > sr_bench_pp)."""
    r = np.asarray(ret, float); r = r[~np.isnan(r)]; n = len(r)
    sr = _sr(r)
    s = pd.Series(r)
    g3 = s.skew(); g4 = s.kurt() + 3.0                      # non-excess kurtosis
    se = np.sqrt((1 - g3 * sr + (g4 - 1) / 4.0 * sr ** 2) / (n - 1))
    return float(norm.cdf((sr - sr_bench_pp) / se))


def expected_max_sr(sr_std_pp, n_trials):
    """Expected maximum per-period Sharpe across n_trials independent strategies."""
    z1 = norm.ppf(1 - 1.0 / n_trials)
    z2 = norm.ppf(1 - 1.0 / (n_trials * np.e))
    return sr_std_pp * ((1 - GAMMA) * z1 + GAMMA * z2)


def deflated_sharpe(ret, sr_std_pp, n_trials):
    """Deflated Sharpe Ratio = PSR against the expected-max SR of n_trials."""
    return psr(ret, expected_max_sr(sr_std_pp, n_trials))


def pbo_cscv(R, S=10):
    """Probability of Backtest Overfitting via CSCV (Bailey et al. 2017).

    R: (T x N) array of returns for N configs. Split time into S partitions; for
    every way to pick S/2 as in-sample, take the IS-best config and check its OOS
    rank. PBO = fraction where the IS-best lands below the OOS median.
    """
    R = np.asarray(R, float)
    T, N = R.shape
    parts = np.array_split(np.arange(T), S)
    logits = []
    for tr in itertools.combinations(range(S), S // 2):
        te = [p for p in range(S) if p not in tr]
        itr = np.concatenate([parts[p] for p in tr])
        ite = np.concatenate([parts[p] for p in te])
        sr_is = np.array([_sr(R[itr, j]) for j in range(N)])
        sr_oos = np.array([_sr(R[ite, j]) for j in range(N)])
        n_star = int(np.nanargmax(sr_is))
        w = rankdata(sr_oos)[n_star] / (N + 1)             # OOS rank in (0,1)
        logits.append(np.log(w / (1 - w)))
    logits = np.array(logits)
    return float(np.mean(logits <= 0)), logits


def purged_kfold(n, n_splits=5, embargo=0.01):
    """Purged & embargoed K-fold indices (AFML ch. 7) for leakage-free CV."""
    idx = np.arange(n)
    emb = int(n * embargo)
    for te in np.array_split(idx, n_splits):
        lo, hi = te[0], te[-1]
        tr = np.concatenate([idx[:max(0, lo - emb)], idx[min(n, hi + 1 + emb):]])
        yield tr, te


def block_bootstrap_sharpe_ci(ret, n_boot=2000, block=21, alpha=0.05, seed=42):
    """Stationary block-bootstrap CI for the ANNUALIZED Sharpe."""
    r = np.asarray(ret, float); r = r[~np.isnan(r)]; T = len(r)
    rng = np.random.RandomState(seed)
    nb = int(np.ceil(T / block))
    out = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.randint(0, max(1, T - block + 1), nb)
        samp = np.concatenate([r[s:s + block] for s in starts])[:T]
        out[b] = _sr(samp) * np.sqrt(PPY)
    return float(np.percentile(out, 100 * alpha / 2)), float(np.percentile(out, 100 * (1 - alpha / 2)))


# ---------------------------------------------------------------- demo
def _demo():
    from analyze import build_features, FIRST_OOS
    from strategy import vol_managed, forecasts

    feat = build_features()
    rvol = np.sqrt(feat["rv"])
    fc = forecasts(feat)
    fc["Combo"] = pd.concat([fc["HAR"], fc["log-HAR"]], axis=1).mean(axis=1)

    idx = feat.index
    for p in fc.values():
        idx = idx.intersection(p.dropna().index)
    idx = idx[idx >= pd.Timestamp(FIRST_OOS)]

    cols = {}
    for win in (21, 42, 63, 126):
        target = rvol.rolling(win).mean().shift(1)
        for cap in (1.5, 2.0, 3.0):
            for fn in ("HAR", "log-HAR", "Combo"):
                s, _ = vol_managed(feat, fc[fn].reindex(idx), target.reindex(idx), lev_cap=cap)
                cols[f"{fn}|w{win}|L{cap}"] = s.reindex(idx)
    R = pd.DataFrame(cols).dropna()
    n_trials = R.shape[1]

    srs = R.apply(lambda c: _sr(c.values)) * np.sqrt(PPY)   # annualized SR per config
    best = srs.idxmax()
    sr_std_pp = (srs / np.sqrt(PPY)).std()

    ann = srs[best]
    ps = psr(R[best].values, 0.0)
    ds = deflated_sharpe(R[best].values, sr_std_pp, n_trials)
    pbo, _ = pbo_cscv(R.values, S=10)
    lo, hi = block_bootstrap_sharpe_ci(R[best].values)

    print(f"grid configs (trials): {n_trials} | obs: {len(R)}")
    print(f"best config: {best}  ann.Sharpe={ann:.3f}")
    print(f"PSR (vs 0):            {ps:.3f}   (P true SR>0, 1 trial)")
    print(f"Deflated Sharpe (DSR): {ds:.3f}   (deflated for {n_trials} trials)")
    print(f"PBO (CSCV, S=10):      {pbo:.3f}   (prob. of backtest overfitting)")
    print(f"Sharpe 95% bootstrap:  [{lo:.3f}, {hi:.3f}]")
    print("\nread: DSR>0.95 & PBO<0.5 -> edge survives selection; "
          "high PBO / low DSR -> the 'best config' is likely overfit.")


if __name__ == "__main__":
    _demo()
