# Pre-Registration — Strategy Campaign (QR006)

> **This document covers the *strategy campaign* only.** The paper's headline **forecasting**
> claim (log-HAR ≻ RW on SPX/h=1) is pre-registered separately in
> **`PREREGISTRATION-FORECAST-EN.md`** (QR002, frozen 2026-08-15). Both are released.


*English translation of the German vault original (`QR006`, dated 2026-08-16). The original
was written and committed **before** the first campaign backtest was run; the campaign code
commit is `cdc87e4`. Nothing below was altered after results were seen; the three
documented deviations are listed at the end.*

## Hypotheses (fixed ex ante)

| ID | Hypothesis | H₀ | Expected effect |
|---|---|---|---|
| Q012 | TSMOM (12M lookback, vol-targeted) yields positive net OOS Sharpe, correlation < 0.5 to VMG | net Sharpe ≤ 0 | Sharpe 0.3–0.6 standalone |
| Q013 | Overnight premium (close→open long) stays net positive after 2× daily costs | net mean ≤ 0 | gross positive, net marginal |
| Q014 | Short-term reversal (z(5d) < −θ above SMA200) adds positive net Sharpe | contribution ≤ 0 | Sharpe 0.2–0.4, episodic |
| Q015 | VIX term-structure sizing (exposure ∝ VXV/VIX) improves Calmar vs. buy-and-hold | ΔCalmar ≤ 0 | +0.05–0.15 |
| Q016 | Turn-of-month window (last 4 + first 3 trading days) carries outsized returns | μ(ToM) = μ(rest) | t > 2 |
| Q017 | A multi-strategy portfolio of weakly correlated sleeves beats every single sleeve risk-adjusted | portfolio Sharpe ≤ max(sleeve) | +0.1–0.3 Sharpe |

## Design (fixed ex ante)

- **OOS:** expanding from 2013-01-02; sub-periods 2013–2019 / 2020–2026.
- **Costs:** 1 bp × |Δw| (base); sensitivity 2 bp / 5 bp; overnight pays 2×|w| bp/day.
- **Leverage cap:** 3.0. All signals use information ≤ t−1 only.
- **Cross-market rule:** a family counts as robust only if the improvement direction holds
  on ≥ 2 of 3 markets (SPX/NDX/DAX).
- **Walk-forward:** train 1260 days → test 252 days → step 252; config chosen by train
  Sharpe; only concatenated test segments are ranked/combined.
- **Monte-Carlo:** stationary block bootstrap, block 21, 5000 paths, seed 42, from €100k.
- **Multiple testing:** every computed configuration counts as one trial for the deflated
  Sharpe ratio; PBO (CSCV) per grid and over the combination universe.

### Parameter grids (complete; no post-hoc extensions)

| Family | Grid |
|---|---|
| TSMOM | lookback {63, 126, 252} × {long/short, long/flat} × vol-target {on, off} |
| Overnight | base; VIX gate {off, VIX<25} |
| Reversal | z-threshold {0.75, 1.0, 1.5} × holding {1, 3, 5} days; SMA200 gate fixed |
| VIX-TS | discrete: threshold {1.00, 1.05} × w_low {0, 0.3}; continuous: a ∈ {1.5, 2.0} |
| Turn-of-month | last {3, 4, 5} × first {2, 3} trading days |
| VMG sizing | target window {21, 42, 63, 126} × cap {1.5, 2.0, 3.0} |
| Portfolio | weights: equal, inverse-vol (63d), ERC-light; sleeves from survivors only |

## Ranking score (fixed ex ante)

`Score = 0.30·Sortino + 0.25·Calmar + 0.20·Sharpe + 0.15·YearConsistency + 0.10·min(PF−1,1)·5`

Disqualification regardless of score: DSR < 0.5 · PBO > 0.7 · single-market-only effect ·
synthetic-option-prices-only basis.

## Honesty clauses

1. Null results are reported in full.
2. Legacy options-overlay numbers (Sharpe 1.3–1.5) rest on synthetic BSM prices and are
   excluded from any tradable ranking.
3. No hypothesis from this campaign can reach `supported` status without a live,
   ex-ante prediction log; the maximum status is `testing`.

## Documented deviations (added after completion)

1. Top-N presentation deduplicates to the best weighting per (subset × market); score order
   unchanged; all 62 combinations remain in the published CSV.
2. Year-consistency (share of calendar years with Sharpe > 0) operationalizes window
   consistency uniformly for combinations/benchmarks; family-level WFA window consistency is
   published separately.
3. VMG walk-forward series begin ~2016 (training requires the 2013+ forecast history);
   horizon lengths are disclosed per candidate (`N_days`).

## Publication-scope addendum (2026-08-31, added after completion — does NOT alter any rule above)

For public release the study is **restricted to the S&P complex (SPX + VIX)** — the data whose
provenance we fully stand behind; NDX and DAX are excluded. The campaign was **recomputed
SPX-only** (trial universe 227 cross-market → 73 SPX-only). Consequently the pre-registered
disqualification rule **"single-market-only effect"** (and PBO > 0.7: the SPX best combination
has PBO = 0.84) applies to the surviving combination, which is therefore **not reported as a
tradeable result**. The published, validated contribution is the SPX realized-volatility
forecasting result (log-HAR ≻ random walk under QLIKE, Clark-West p ≈ 0.03; HAR-IV adds
implied-volatility information) plus the validation methodology and the full record of
failures. This addendum records the scope restriction and its pre-registered consequence; it
changes no ex-ante rule.

## Exploratory forecasting analyses (2026-09-02, added after completion — clearly labelled post-hoc)

The following forecasting analyses are **exploratory and post-hoc**, i.e. *not* part of the
pre-registered confirmatory set above; they are reported as diagnostics and candidates, and by
honesty clause 3 none can exceed **candidate** status without a live prediction log:

1. **Lag / spike diagnostics** (`rv_lag_diag.py`, `rv_spike_ident.py`, paper §6.4):
   Mincer-Zarnowitz calibration, log-error autocorrelation, lead-lag phase, the top-decile
   up-jump spike-miss ratio, and its identification — a DGP simulation of the mechanical floor
   (perfect forecaster ≈ 1.90×) vs. the residual (+0.64, P < 0.001), forecast-decile calibration,
   and upper-tail coverage. Descriptive/diagnostic; the spike statistic conditions on the outcome
   and is interpreted only relative to the simulated floor.
2. **Overnight & intraday same-day channels** (`rv_overnight.py`, `rv_nowcast.py`, §6.4):
   nested Clark-West increments on HAR-IV. The intraday "RV-so-far" nowcast is the strongest
   single lever found (−4.8 % QLIKE) but **does not clear** the multiple-testing bar (CW
   p ≈ 0.09); reported as an honest ceiling, not a confirmed improvement.
3. **Improvement ladder / loss-matched estimator** (`rv_improve.py`, §3e): the C-series,
   including the QLIKE-native Gamma-GLM with the VIX3M/VIX slope (C4: −4 % QLIKE, MSE also
   improved, DM p = 0.0008, lower QLIKE in both sub-periods). It clears the same gates the
   forecasting confirmatory result used, but remains a **candidate** pending a live log.

These were run on the frozen SPX panel with no change to the harness, seeds, or the ex-ante
rules; they add analysis, not degrees of freedom to any tradable claim.
