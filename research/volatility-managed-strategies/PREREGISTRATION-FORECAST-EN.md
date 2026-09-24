# Pre-Registration — Realized-Volatility Forecasting

*English translation of the German original (`PREREGISTRATION.md`; note `QR002`,
hypothesis id `Q006`), **frozen 2026-08-15, before the first result was seen.** Changes after the
first backtest run are append-only and dated. This document governs the paper's **headline
forecasting claim**; the strategy campaign is pre-registered separately in `PREREGISTRATION-EN.md`
(`QR006`).*

## Confirmatory hypothesis (exactly one)

- **H0.** log-HAR does **not** have a lower out-of-sample QLIKE than the random walk on **SPX,
  horizon h = 1** (loss difference ≤ 0).
- **H1 (directional).** QLIKE(log-HAR) < QLIKE(RW) on SPX / h = 1; Clark-West p < 0.05.

Everything else is **exploratory** and reported as such (to avoid multiple-testing inflation).

## Fixed design

| Item | Setting |
|---|---|
| Primary market / horizon | SPX, h = 1 (confirmatory) |
| Exploratory | NDX, DAX; h = 5, 22; HAR-J/HAR-CJ; HAR-IV / VRP; the rich linear/ML feature set; the Gamma-GLM (C4) |
| RV proxy (primary) | 5-minute RV, regular trading hours (09:30–16:00 ET) |
| RV proxy (robustness) | 1-min, 10-min, subsampled/averaged RV |
| Target transform | log-RV (primary), level-RV (robustness) |
| OOS procedure | expanding window; first OOS forecast **2013-01-02**; burn-in 2005–2012 |
| Overnight | excluded (regular trading hours only) |
| Loss | **QLIKE (primary)** + MSE (both proxy-consistent, Patton 2011) |
| Tests | Diebold-Mariano; **Clark-West** (nested, on MSPE); Mincer-Zarnowitz |
| Seed | 42 |
| Reproducibility | git commit hash + data_version (sha256 + date) recorded at run time |

## Decision rule

Confirmed if and only if QLIKE(log-HAR) < QLIKE(RW) on SPX / h = 1 **and** Clark-West p < 0.05
**and** the sign of the loss difference matches the claim (direction check).

## Scope

This is a **forecasting** test (QLIKE), **not** a trading-edge claim. A trading setup additionally
requires a post-cost backtest and ex-ante hits in a prediction log.

## Documented deviations / clarifications (added after completion)

1. The confirmatory result is reported as such (SPX/h=1: QLIKE 0.2254 vs 0.3086, Clark-West
   p = 0.03114). HAR-IV, the rich-feature linear models, the Model Confidence Set and the
   Gamma-GLM (C4) are **exploratory** extensions, labelled as such throughout §3.
2. The VIX level used by the exploratory HAR-IV enters as $\mathrm{ivar}=(\mathrm{VIX}/100)^2/252$
   from the licensed MarketTick 1-minute VIX feed (not FRED); the VIX3M/VIX slope is from FRED.

---
*Frozen: 2026-08-15 · Seed: 42.*
