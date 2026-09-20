# Errata

Corrections to the papers are recorded here in the open, with the version they
first appeared in and the version that fixed them. A visible erratum is a
quality signal; silently swapping a PDF is the opposite. Found something? Please
open an issue.

Each entry is applied to **both** the English and the German edition unless
noted. Numbers quoted below were re-derived; where a figure script was changed,
its PNG was regenerated so text and figure agree.

---

## v1.0 (2026-09-20) — corrections from an external critical review

### A. Proven factual errors

- **A1 · The Greeks & Hedging — N(d₁) vs N(d₂) gap (§3.4, §11.1).** The text said
  delta and the risk-neutral in-the-money probability "differ by about σ√T." The
  *arguments* d₁ and d₂ differ by σ√T; the *probabilities* differ by about
  φ(d₁)·σ√T — for the 1-month ATM example ≈ 0.023, not the 0.058 that σ√T alone
  implies. Corrected in the body and the misconceptions list.
- **A2 · The Greeks & Hedging — positive theta with positive gamma (§5.2, §11.1).**
  The text called this combination impossible ("the identity forbids it; any
  exception is a mislabeled greek"). That holds only at zero carry. The full
  identity is Θ = −½σ²S²Γ − (r−q)SΔ + rV; at a positive rate a deep-in-the-money
  European put (S=60, K=100, r=5%, σ=20%, T=1) has Γ>0 and Θ>0 together.
  Reworded to "uncommon, not impossible," with the full identity shown.
- **A3 · The Greeks (both greeks papers) — vanna "pull toward ½" (§8.1 / §4.2).**
  The text said rising volatility pulls delta "toward the ½ that maximal
  uncertainty implies." ½ is a waypoint, not an attractor: a moderately
  in-the-money call's delta bottoms around 0.63–0.74 and then climbs back toward
  1 as σ→∞. Corrected in both the greeks-and-hedging and the second-order-greeks
  paper.
- **A4 · Options Fundamentals — time value never negative (§4.2).** For European
  options intrinsic value is properly measured against the *forward*, not the
  spot; measured against spot-intrinsic a deep-in-the-money European put can
  trade ~20 points below its K−S. Added the forward-based split and the caveat.
- **A5 · Macro Foundations & Macro Regimes — the Fed's target index.** The 2%
  goal was described as *core* PCE; it is written on *headline* PCE (core PCE is
  watched as a less-noisy trend guide). Fixed in macro-foundations §4.2/§6.1 and
  in the macro-regimes §3.2 justification for using core PCE in the Taylor rule.
- **A6 · How Markets Move — "no third possibility" (§3.1).** Taker-meets-maker is
  the rule in *continuous* trading, but the batch auction (opening/closing cross,
  §6.1) is a genuine third mechanism. Qualified accordingly.
- **A7 · From Paper to Strategy — McLean & Pontiff numbers (§3.3).** The 26% and
  58% were mis-assigned. 26% is the in-sample overfitting portion (the decay
  already visible out-of-sample *before* publication); ~32% is the additional
  publication effect; 58% is the total post-publication decay. Rewritten.
- **A8 · Overfitting & Calibration — reliability diagram resolution (Fig 4).** The
  text claimed the overconfident forecaster B had *higher* resolution (0.045 vs
  0.041). Overconfidence is a strictly monotone relabeling of the forecasts, and
  resolution is invariant to that — it depends only on the partition of outcomes.
  `fig_reliability.py` was corrected so B is a true relabeling of A; RES(A) =
  RES(B) = 0.041 exactly, and the entire Brier gap (0.215 vs 0.233) is
  reliability. Figure regenerated.
- **A9 · Dealer Flows & GEX — contradictory level (§4.1 vs §4.3).** The same
  standard estimator appeared as +$5.4 bn and −$28.2 bn. Both are real outputs
  measuring different things: +$5.4 bn is the CBOE-supplied gamma summed at spot;
  −$28.2 bn is the Black–Scholes-recomputed gamma at spot (estimator E1). They
  straddle zero because the snapshot sits on the gamma flip (+0.24% above spot).
  Reconciled and explained in-text and in the evidence table.
- **A10 · ML for Strategy Building — expected-max Sharpe (Fig 2).** The expected
  maximum of 2,000 no-edge Sharpes was 1.04, from the crude √(2 ln M)
  approximation, which overstates it for finite M. Replaced with the
  Bailey–López de Prado (2014) estimate (the same one the overfitting paper's
  DSR library uses): **0.92**. The observed best of 0.90 now lands right on the
  null expectation, which strengthens the point. `fig_g3_dsr.py` fixed, PNG
  regenerated.
- **A11 · Building, Running & Killing Algos — monitoring parameters (Fig 3).** The
  CUSUM's threshold h and in-control run length were never stated. Added:
  reference k = 0.20σ, threshold h = 14σ, ARL₀ ≈ 3,300 trades. (Re-running the
  script confirmed the four reported metrics — median lag 108, p90 158, 85.4%
  detected, 14.6% false-alarm — all come from this single configuration; see
  section E.)

### B. Code / listing findings

- **B1 · First-Order Greeks §9 — divide-by-zero.** `elasticity = delta*S/price`
  threw `ZeroDivisionError` for deep out-of-the-money options whose Black–Scholes
  price underflows to 0 — precisely the "1-delta" options the tail-hedging paper
  is about. Now guarded (returns NaN below a price floor).
- **B2 · Second-Order Greeks §9 — self-check units.** The printed `self_check`
  differenced delta/vega in natural units while `bsm_greeks` returns per-vol-point
  and per-calendar-day, so vanna/charm/vomma/veta sat a factor 100/365/10000/100
  away from the closed forms they were meant to verify. The finite differences
  are now scaled into the reported units; every greek checks to 1:1.
- **B3 · Second-Order Greeks — spurious rounding identity.** ATM vanna and charm
  were both printed as −0.00057, inventing an identity. Now printed to enough
  places to distinguish them (−0.000574 vs −0.000566).
- **B4 · Overfitting & Calibration §3.3/§9.1 — Lo (2002) not implemented.** The
  autocorrelation correction to the Sharpe standard error was cited but not in
  the `psr` code, so PSR loses calibration under serial dependence (its stated
  use case). `psr` now takes a first-order autocorrelation `rho` and deflates the
  effective sample by (1−ρ)/(1+ρ); ρ=0 reproduces the old iid behaviour.
- **B5 · Overfitting & Calibration §4.4 — single PBO as a gate.** A single PBO
  value carries a Monte-Carlo standard deviation on the order of 0.2 on ~50 null
  strategies, so fine thresholds (0.52 vs 0.46) are noise. Added a caveat to read
  PBO in wide bands, not on the second decimal.

### C. Cross-cutting corrections

- **C1 · Volatility Fundamentals — band coverage as VRP.** The 81.4%-inside-±1σ
  result (vs a naive-normal 68.3%) was sold wholesale as "the variance risk
  premium made visible." Most of the gap is the fat-tailed shape of returns — a
  fairly priced standardized t(4) already lands 77.0% inside, t(5) 74.7% — and
  only the residual over ~75% is premium. Caveat added to the abstract and §7.4.
- **C2 · Volatility Fundamentals — rule of 16.** The +0.79% error of 16 against
  √252 = 15.87 is now quantified where the shortcut is introduced.
- **C3 · Vol Modeling & VRP — DM vs Clark–West.** The Diebold–Mariano statistic
  for the *nested* HAR-vs-random-walk pair is now flagged as descriptive only;
  the valid nested test is Clark–West (already reported in the paper, p = 0.049).
- **C4 · Vol Modeling & VRP §6.3 — variance vs volatility units.** Clarified that
  the +6.98 %²/month premium and the ~3.7-vol-point wedge are different summaries
  and do not square into each other (3.7 vol points ≈ 9.96 %²), the very trap §6.1
  warns against.
- **C5 · Macro Regimes — Taylor gap and r\*.** Added a caveat that the rule fixes
  the neutral real rate at r\* = 2.00, which alone contributes 2.00 of the 6.31
  prescription; time-varying estimates (Laubach–Williams; Holston–Laubach–Williams,
  now cited) place it nearer 0.5–1%, shrinking the gap by more than a point. (The
  paper already attributed the gap to the inflation terms, not the output gap.)
- **C6 · Macro Regimes §2.4 — overlapping CIs.** Overlapping one-sample 95%
  intervals do not imply an insignificant difference. A proper two-sample test of
  the equity Goldilocks-minus-Stagflation gap gives t ≈ 2.88, p ≈ 0.004
  (reproduced from `fig_e2_quadrant_assets.py`). Reworded from "suggestive, not
  established" to established-but-modest, and softened the "prove it is not"
  conclusion.
- **C7 · Statistics for Traders §3.2 — sample variance.** The prose defined
  variance as the population average of squares; added Bessel's n−1 correction
  for the sample estimator (the default in numpy/pandas), which matters on small
  samples.
- **C8 · Flow Landscape §5.2 — 31.7% one-day NAV cut.** Flagged as inflated by the
  equal-weight 21-day volatility window (its discrete edge steps), evidenced by
  the largest single-day cut in the whole sample landing in an unremarkable month
  (Nov 1991) rather than 2008/2020; an EWMA estimator would smooth it.
- **C9 · Flow Landscape §8.1 — private artifacts.** Made explicit that the private
  four-regime taxonomy (Chop/Grind/Expansion/Cascade) and the H001–H004 registry
  are non-load-bearing labels: the public two-regime backbone and the fully
  stated hypotheses are all a reader needs to test the argument.

### D. Repository & presentation

- Added LICENSE (CC BY 4.0), LICENSE-CODE (MIT), CITATION.cff, CHANGELOG.md, this
  file, a README disclaimer block, a "Data license" section, and a title-page
  version line.
- Set every paper's title date to the v1.0 release date, removing the appearance
  of back-dating relative to each paper's last data point.

### E. Reviewer points reviewed but NOT changed (with reasons)

- **Editorial restructuring** — merging the four greeks papers into two,
  withholding the ML and model-to-trade papers, staggered release, and a Zenodo
  DOI — are editorial calls left to the author; not applied in this pass.
- **"Fig 3 monitoring metrics are inconsistent from one threshold."** Re-running
  `fig_monitoring.py` reproduces all four metrics from a single CUSUM (k = 0.20σ,
  h = 14σ, ARL₀ ≈ 3,300) over 5,000 seeded paths, because the shift to detect is
  small (0.41σ). The inconsistency claim did not reproduce; only the
  missing-parameters point was valid (fixed in A11).
- **Committed raw vendor caches** (CBOE/optionsDX JSON/CSV under `figures/data/`)
  should be replaced by fetch-at-runtime scripts plus checksums — a follow-up
  item, deferred rather than deleted now so the current figures still build.
- **Per-paper "missing building block" suggestions** (execution-cost boxes,
  bucketed exposure, production runbooks, and similar) are enhancement ideas, not
  errors, and are outside this correction pass.
