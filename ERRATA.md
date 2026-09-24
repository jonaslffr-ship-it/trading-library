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
  **[Superseded by K1 (v1.1): the t(4)/t(5) figures use the *unconditional* kurtosis
  of raw returns, but the test standardizes each day by its own VIX sigma, so the
  correct baseline is the *conditional* VIX-standardized distribution (≈71.9%). The
  premium is therefore the *larger* part — ≈9.5 of the 13.1 excess points, not the
  residual. Abstract, §7.4 and §9 rewritten.]**
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
  missing-parameters point was valid (fixed in A11). **[The ARL₀ ≈ 3,300 quoted
  here is itself the Siegmund large-deviation approximation *without* the
  continuity correction; the exact in-control ARL₀ for this discrete CUSUM is
  ≈ 4,290 (collocation + Monte Carlo). Corrected in §5.4 as K-M04 (v1.1). The four
  detection metrics are unaffected.]**
- **Committed raw vendor caches** (CBOE/optionsDX JSON/CSV under `figures/data/`)
  should be replaced by fetch-at-runtime scripts plus checksums — a follow-up
  item, deferred rather than deleted now so the current figures still build.
- **Per-paper "missing building block" suggestions** (execution-cost boxes,
  bucketed exposure, production runbooks, and similar) are enhancement ideas, not
  errors, and are outside this correction pass.

## v1.1 (2026-09-24) — corrections from a second external audit

A second independent audit re-ran the repository at v1.0 (tag `v1.0` = 2469ade)
with a 21-test reproducing suite (21/21, 119/119 checks, deterministic).

### F. Infrastructure & packaging (applied)

- **F1/F3 · Cache poisoning + offline SKIP.** The seven CBOE-chain figure scripts
  wrote the cache *before* the network read, so a failed fetch left a 0-byte file
  the `os.path.exists` guard then trusted forever. They now validate JSON, write
  atomically (`.part` + `os.replace`), and emit a clean `SKIPPED` line offline.
- **F2 · Data-redistribution claim.** README/LICENSE now distinguish the free CBOE
  *daily-history* CSVs (included) from the licensed *intraday chains* (git-ignored).
- **F4 · verify_repro.sh exit code.** `exit $((fail>0))` so `make verify`/CI can no
  longer stay green on a real reproduction failure; per-figure timeout 60→180 s.
- **F5 · requirements.txt** pins the audited environment (Python 3.11).
- **F6 · prove_fixes.py** now opens the papers (A1/A10/C6), so reverting a corrected
  number in the prose turns it red (previously it re-derived arithmetic only).
- **F7 · LICENSE** no longer references nonexistent tracks 02/06; `NOTICE.md` added.
- **F8 · Missing modules.** `research/.../strategy.py` and `paper_review_fixes.py`
  were referenced by five package modules but absent; both restored.
- **F9 · GJR optimizer** (`fig_garch_fit.py`) now fits via `arch` under the correct
  GJR stationarity condition (see K2).
- **F10 · CPI YoY** (`fig_e1_*.py`) now computed calendar-based, not position-based
  (see K9).

### K. Content corrections (applied)

- **K1 · Volatility Fundamentals — errata C1 corrected the wrong way.** C1 used the
  *unconditional* t(4)/t(5) coverage (77.0%/74.7%) as the fair baseline, but the test
  standardizes each day by its own VIX sigma, so the correct comparison is the
  *conditional* VIX-standardized distribution (excess kurtosis ≈ 1.4, fair coverage
  ≈ 71.9%). Of the 13.1-point over-coverage ≈ 3.7 are fat tails and ≈ 9.5 the variance
  risk premium — the premium is the *larger* part. Abstract, §7.4, §9.
- **K2 · Vol Modeling & VRP — GJR fit on the constraint boundary.** The softmax
  enforced α+γ+β<1 (tighter than the correct GJR condition α+γ/2+β<1), pinning the fit
  to the boundary (α=0.051, γ=0.139, β=0.810, 3.7×, logL 12,638.8). The correct fit
  (via `arch`): α=0.027, γ=0.232, β=0.816, asymmetry ≈9.7×, logL 12,658.4 (LR 141.6).
  §3.3, caption, evidence; figure regenerated.
- **K3 · Model-to-Trade — OOS Sharpe 1.24.** §7.3 now carries the bootstrap 95% CI
  ≈ [0.39; 2.64] and a thin, two-sided single-month dependence (taking March 2020 → ≈0.09;
  no other out-of-sample month moves it *down* by >0.07, but dropping April 2025 *raises* it
  to ≈1.99), and the honest break-even (−0.0015 ≈ 3.5% of variance sold; the *unconditional*
  premium breaks even near 0.008 annualized-variance points, the *conditional* rule near 0.0163).
  Re-corrected in v1.1 after a second audit found the earlier ">0.07" and "0.008" phrasings
  one-directional and mis-attributed (see the second-audit follow-ups below).
- **K4 · Dealer Flows / GEX — "0.1% agree" reassurance.** §4.4 now states the 0.1%
  median is near-the-money only, and that +$5.4 bn (all live contracts) vs −$28 bn
  (filtered `live & iv>0.01 & oi>0`, `max(dte,1)/365`) are different populations under
  different time conventions — so both sign and magnitude of the net are model choices.
- **K5 · Greeks & Hedging — charm "four times".** §8.2 corrected to ≈2.2× (OTM) /
  ≈2.9× (ITM) for the *same* option; the 4× compared different moneyness across
  maturities. Caption updated.
- **K6 · Backtesting — the only backtest.** §2.6 now reports the gross Sharpe 0.41 is
  not significant (σ_SR ≈ 0.26, t ≈ 1.6, p ≈ 0.11, 95% CI [−0.09, 0.92]). Evidence updated.
- **K7 · Overfitting — σ_SR = √(252/T).** §2.1 now names the iid assumption, forward-
  references the §3.1 Lo (2002) autocorrelation correction, and states the measured
  ρ₁ ≈ −0.11.
- **K8 · Macro Regimes — NFCI>1 crisis extreme.** §4.2 now discloses the cell is ~90%
  pre-1990 (341/378 weeks, +0.334%), 2008–09 is 37 weeks (−2.129%), and March 2020
  peaked at NFCI ≈ 0.27 and never entered it; on the modern subsample the extreme does
  foreshadow weakness.
- **K9 · Macro Foundations — CPI YoY.** The three L1 figure scripts computed YoY
  position-based (`v[12:]/v[:-12]`), which over the un-published Oct-2025 gap gave
  ≈3.71% for Aug-2026 instead of ≈3.35% and contradicted the L2 dashboard. Now
  calendar-based; figures regenerated (F10).
- **K10 · Tail-Hedging — skew acts on both sides.** §5.2/§6 now state flat-VIX pricing
  flatters the overlay on both axes; the ×8,800 crash multiple is a resting-value
  denominator artefact (≈×251 vs entry premium); a naked put's loss is bounded by the
  strike (≈95 per 100), only the call side is unbounded.
- **K13 · Paper-to-Strategy — replication prior.** §3.4 now carries the published
  counter-position: Chen & Zimmermann (CFR 2022), ~100% replication over 319 predictors,
  disputing the Hou-Xue-Zhang classification; both priors shown (8% → ~25%). Reference added.
- **K14 · How Markets Move — the third possibility.** §3.1 now names internalisation /
  PFOF (retail orders filled off-book by wholesalers) alongside the batch auction, and
  flags the 2024 Reg NMS sub-penny tick change.
- **K-M04 · Building/Running/Killing Algos — ARL₀.** §5.4 corrected from ≈3,300 to
  ≈4,290 (3,300 was Siegmund without the continuity correction); the four detection
  metrics are unaffected.

### K (research package — volatility-managed-strategies, applied)

- **K11 · MCS on two loss matrices** (§3e): the ML-MCS run is computed on a different loss matrix
  than the classical one (same model names, different QLIKE — HAR-CJ 0.564 vs 0.256, LHAR 1.852 vs
  0.684) and is degenerate (HAR-CJ, second-worst, inside the 90% set; HAR-IV, third-best, outside).
  §3e now says the two runs are not comparable and no longer reads it as a displacement.
- **C4 under Clark-West** (§3f): the Gamma-GLM candidate fails the pre-registered Clark-West test
  against its Bonferroni threshold (CW p ≈ 0.027 vs baseline, 0.037 vs the nesting parent; both
  above 0.05/6 ≈ 0.0083). §3f now states this; it was already marked exploratory/candidate.
- **Q015 / Q012** (§6.3): Q015 (VIXTS Calmar target +0.05–0.15) misses its band (best ΔCalmar
  ≈ +0.023, four of six grid points negative) → recorded not supported; Q012 (TSMOM, corr < 0.5 to
  VMG) measures 0.751, violating its condition. Both now in the graveyard with verdicts.
- **Diversification ratio** (§9.2): corrected from ≈ 1.8 to ≈ 1.3 (1.25–1.47); the 1.8 is not
  reproducible from the result files.
- **V-09 · NDX-PBO** (§6.2): the same `thesis_validation.csv` reports PBO 0.365 on NDX, so the
  SPX overfitting flag is market-specific — now stated.

**Note on the research paper PDF:** the `.md` and `.tex` corrections above are applied, and the PDF
has been rebuilt from the paper's own LaTeX source (`volatility-managed-strategies.tex`) with
tectonic — the author's title-page and section styling is preserved. `.md`, `.tex` and `.pdf` are
consistent.

### N. Second re-audit follow-ups (v1.1)

A second external audit re-ran the repository after the v1.0 corrections and, crucially,
re-verified the *first* audit's own claims. Six of those claims had been adopted into the papers
without independent checking; five were wrong or mis-labelled. Every item below was reproduced
with the repository's own code on free data before being applied.

- **N1 · `make verify` regression.** The track-renumber (03→02 … 10→08) left eight stale paper
  paths in `verify_listings.py`/`prove_fixes.py`; `make verify` aborted with exit 2. Repointed to
  02–08; harness green (verify_listings 17/17, prove_fixes 26/26).
- **N4 · Cache-poisoning pattern, fully swept.** The F1/F3 atomic-write (`.part` + `os.replace`) +
  offline-`SKIPPED` fix now covers the remaining **7 volatility + 12 macro** figure scripts (19
  total), not only the seven option-chain scripts.
- **N5a · Model-to-Trade §7.3 single-month claim.** "no other *in-sample* month moves it by more
  than 0.07" → the dependence is *out-of-sample* and two-sided: no month moves it *down* by >0.07,
  but dropping April 2025 *raises* the OOS Sharpe to ≈1.99 (reproduced from `fig_g2_strategy.py`).
- **N5b · Model-to-Trade §7.3 break-even.** "edge gone at a *realistic* 0.008" → 0.008 is the
  *unconditional* break-even; the *conditional* OOS rule survives to ≈0.0163 (Sharpe ≈0.70 at a
  0.008 cost). "realistic" dropped.
- **N5c · Tail-Hedging §5.2 skew comparison.** "+20–110 % at the same *strike*" → at the same
  *delta*; at the same *strike* the skew premium effect is several-fold larger (direction confirmed
  numerically).
- **N5d · Research §6.3 Q015.** "four of six grid points negative" → **five of six** (ΔCalmar
  against a buy-and-hold Calmar of 0.392; reproduced from `sleeves_SPX.csv`).
- **N5e · How Markets Move §3.1 tick date.** "half-cent ticks from late 2025" → the SEC extended
  the compliance date to **November 2026** and a further slip to 2027 is widely expected.
- **N5f · Overfitting §2.1 autocorrelation.** The −0.11 AR(1) is the S&P *index return's*; the
  1-day reversal *strategy's* own returns show AR(1) ≈ **−0.005** (both reproduced). Attribution fixed.
- **N6 · Corrections propagated.** Tail §6.1 body now carries the ×8 800 denominator-artefact caveat
  (≈×251 against the entry premium); research §8 no longer calls C4 "real by our gates" — it clears
  DM but not the pre-registered Clark-West gate, as §3f already states.
- **N7 · Regression guard.** `prove_fixes.py` now holds one text anchor per v1.1 correction (K2, K9,
  N5a/b/d/e/f, N6), so reverting any of them turns the harness red.

*Not adopted from the second audit:* N8 (the "byte-identical" wording — flagged, not re-verified),
N9 (Markdown and PDF agree on every *corrected* claim but differ in overall length), and the ~40
open high-severity findings outside K1–K14 (N10), which remain a separate work item.
