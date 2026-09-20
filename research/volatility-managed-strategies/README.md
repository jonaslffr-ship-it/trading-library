# Realized-Volatility Forecasting & Volatility-Managed Sizing on the S&P 500

**A pre-registered, walk-forward, multiple-testing-corrected study — that disqualifies its own
trading strategy under its own rules.** The validated, reproducible contribution is the
*forecasting* result and the *validation methodology*; the trading strategy is reported as a
**null result**, in full.

> **Research/educational project — not investment advice.** Historical simulation on a price
> index net of assumed costs. Licensed raw data is not redistributed (sha256 fingerprints in
> `data/data_manifest.csv`).

## What holds up

**1 · Realized volatility is forecastable (own replication).** Leakage-free expanding-window
OOS test (first forecast 2013-01-02, QLIKE loss, Clark-West nested test), SPX 5-minute RV:

| Model | QLIKE ↓ | OOS R² vs. RW |
|---|--:|--:|
| Random walk | 0.308 | 0 % |
| HAR (Corsi 2009) | 0.247 | +20 % |
| **log-HAR** | **0.225** | **+23 %** |
| HAR-IV (+ VIX) | 0.204 | +30 % |
| OLS / Ridge / Lasso (rich features) | 0.197 | — |
| Gradient boosting | 0.205 | — |
| **GLM + IV-slope (loss-matched)** | **0.196** | — |

- log-HAR beats the random walk (**Clark-West p ≈ 0.03**); the edge grows with horizon
  (OOS R² +23 % at h=1 → **+43 % at h=22**).
- Implied volatility adds information (**HAR-IV**, Clark-West p = 0.019).
- Regularized *and unregularized* linear models on a rich realized-feature set all reach
  QLIKE ≈ 0.197 (**OLS 0.1968 = Ridge 0.1968 ≤ Lasso 0.1977**), while gradient boosting adds
  nothing (DM p = 0.86): **the gain is features, not regularization or nonlinearity.**
  *(Caveat: those QLIKE wins come with an MSE-based R² of −65 % — filter/retransform-dependent.)*
- The one **discovery** rather than replication: a **loss-matched Gamma-GLM with the VIX
  term-structure slope** lowers *both* QLIKE (−4 % vs. HAR-IV) *and* MSE, in both sub-periods
  (DM p = 0.0008) — QLIKE-native estimation removes the retransform fragility above. Still a
  **candidate, not `supported`** (no live log).

*The HAR results replicate known findings (Andersen et al. 2003; Corsi 2009; Patton 2011); the
loss-matched GLM + IV-slope is the only forecasting increment claimed here.*

**2 · The trading strategy does NOT survive validation (null result).** A volatility-managed +
VIX-term-structure sizing campaign on the S&P 500, walk-forward selected, produces a best
combination of Sharpe **0.96** / max-drawdown **−9.9 %** vs. buy-and-hold 0.83 / −34.0 %. But:

- its probability of backtest overfitting is **PBO = 0.84**, and our **pre-registered
  disqualification rule** (PBO > 0.7 **and** single-market effect) rules it out;
- the Sharpe uplift (+0.13) is **inside the bootstrap noise band** (95 % CI [0.44, 1.46]);
- the clean tail (P(DD>20 %) 3.5 % vs. 91 %) is largely a **volatility-level artifact**
  (≈ 6.5 % vs. 17 % vol), not a diversification edge, once you are on a single market.

**We therefore report no tradeable edge.**

**3 · The graveyard (reported in full).** Long/short index momentum (−68 % drawdown),
turn-of-month (single-market artifact), overnight carry (gross +7.3 %/yr, **net dead at 5 bp:
Sharpe −2.38**), and a 6-test mechanism battery in which only HAR-IV carried evidence.

**4 · Lag diagnostics — why the forecast "lags," precisely.** The forecast is well-calibrated on
average (Mincer-Zarnowitz slope ≈ 1, efficient errors); the visible "lag" is a **2.5×
underestimation of the worst volatility spikes.** Features + implied vol cut it from 4× (random
walk) to 2.5×; an intraday nowcast (first-hour RV — the **strongest single lever**, −4.8 % QLIKE)
only to 2.45×, because the worst spikes emerge *after* the first hour, where no morning-anchored
forecast can see them. This is the **same blind spot that makes the sizing strategy fail** — the
lag and the null are one fact. (`figures/report/18_lag_spike.png`.)

## Why this is the honest outcome

Publication is restricted to the S&P complex (SPX + VIX) — the data whose provenance we fully
stand behind. Our pre-registration (`PREREGISTRATION-EN.md`) **already disqualifies
single-market-only effects**, so an SPX-only strategy result cannot be a tradeable claim by our
own ex-ante rules. What survives is the forecasting result, the anti-overfitting machinery
(deflated Sharpe, PBO/CSCV, block bootstrap, walk-forward), and the complete record of
failures. **No result reaches `supported` status — there is no live track record yet.**

## Reproduce

No licensed data needed for the smoke test:
```bash
pip install -r requirements.txt     # pinned, seed 42
python run.py                        # synthetic seed-42 pipeline, end-to-end (illustrative)
pytest tests/                        # incl. a no-look-ahead guard
```
Full SPX reproduction (licensed MarketTick 1-minute data required — not redistributed):
```bash
export MARKETTICK_APIKEY=<your key>
python analyze.py     --raw data/raw --tag SPX    # forecast ladder  -> results/oos_metrics.csv
python ml_models.py                                # OLS/Ridge/Lasso/GBRT vs HAR-IV
python strategy_lab.py --raw data/raw --tag SPX   # sleeves
python walkforward.py  --raw data/raw --tag SPX   # honest walk-forward
python portfolio_combos.py                         # SPX campaign + DSR/PBO + ranking
python sensitivity.py                              # cost stress, sub-periods, leverage
# forecasting diagnostics (paper §3e, §6.4):
python _build_panel.py                             # improvement panel (rv/features/ivslope)
python rv_improve.py                               # C-series incl. loss-matched GLM (C4)
python rv_lag_diag.py                              # Mincer-Zarnowitz / error-efficiency / spike-miss
python rv_overnight.py && python rv_nowcast.py     # overnight & intraday same-day channels
python rv_lag_figures.py                           # -> figures/report/18_lag_spike.png
```
Shipped `results/*.csv` carry the reported numbers (seed 42). Data fingerprints (sha256,
shipped files + raw-dataset aggregate) in `data/data_manifest.csv`, regenerate with
`python make_manifest.py`.

## Paper
`paper/volatility-managed-strategies.md` — working paper (PDF: `paper/volatility-managed-strategies.pdf`).

## License & disclaimer
Code MIT · **research/educational project, not investment advice.** Historical simulation on a
price index (no dividends) net of assumed costs; live results will differ. A pre-registered
prediction log (`predictions/`) is the designated next step and the only route from `testing`
to evidence.
