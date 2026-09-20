# Changelog

All notable changes to the Trading Library paper series are recorded here.
The series is versioned as a whole; corrections to individual claims are itemised
in [ERRATA.md](ERRATA.md). Dates are ISO (YYYY-MM-DD).

## v1.0 — 2026-09-20

First public release, incorporating an external critical review.

### Added
- `LICENSE` (CC BY 4.0, papers + figures), `LICENSE-CODE` (MIT, scripts),
  `CITATION.cff`, `CHANGELOG.md`, and `ERRATA.md`.
- A visible disclaimer block and a "Data license" and "Methodology & corrections"
  section in `README.md`.
- A version line (`v1.0 · <date>`) on every paper's title page.
- Laubach–Williams and Holston–Laubach–Williams references to the macro-regimes
  paper (neutral-rate literature).

### Changed / Fixed
- Corrected the proven factual errors and code findings raised in review — the
  full list, per paper, is in [ERRATA.md](ERRATA.md). Highlights: the
  N(d₁)−N(d₂) gap (φ(d₁)·σ√T, not σ√T); the theta–gamma "impossibility" (a
  deep-in-the-money European put breaks it); the vanna "pull toward ½"; the Fed's
  headline- vs core-PCE target; the "no third possibility" taker/maker claim; the
  McLean–Pontiff decay split; the reliability-diagram resolution claim; the GEX
  sign reconciliation; the expected-maximum Sharpe (0.92, not 1.04).
- Two figure scripts were corrected and their PNGs regenerated:
  `fig_g3_dsr.py` (expected-max Sharpe now via the Bailey–López de Prado formula)
  and `fig_reliability.py` (forecaster B is now a strict monotone relabeling of A,
  so resolution is invariant by construction).
- Two embedded listings were hardened: the first-order-greeks elasticity now
  guards against a divide-by-zero deep out-of-the-money; the probabilistic
  Sharpe ratio now implements the Lo (2002) autocorrelation correction.
- All title-page dates set to the v1.0 release date (removing the appearance of
  back-dating relative to each paper's last data point).
- Softened the data-provenance wording where CBOE/optionsDX chains are used, to
  distinguish "freely retrievable" from "redistributable".
