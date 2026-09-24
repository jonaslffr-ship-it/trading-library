# Trading Library

A curated library for traders — from market foundations to options mechanics, orderflow, volatility, quantitative methods, market flows, macro, and algo development.

This library is a set of original scientific papers written by Jonas Löffler (`L1`/`L2`/`L3`) — scientific-paper format, every empirical number reproducible from **free data** with the accompanying `figures/*.py` script.

> **Disclaimer.** These are research and educational documents, **not investment advice**, not a recommendation or solicitation to trade any security, and not a statement of the views of any employer. Any rule or threshold shown (e.g. a volatility cut-off) is an illustration of a method, not a signal to act on. Trading options and derivatives involves substantial risk of loss. You are responsible for your own decisions.

**Version & corrections.** Series **v1.1** (2026-09-24). Found errors are fixed in the open — see [CHANGELOG.md](CHANGELOG.md) and [ERRATA.md](ERRATA.md). Licensing: papers and figures under [CC BY 4.0](LICENSE); code under [MIT](LICENSE-CODE).

## Difficulty badges

| Badge | Level | Meaning |
|---|---|---|
| 🟢 | Beginner (L1) | No prior knowledge required |
| 🟡 | Intermediate (L2) | Assumes the track's L1 + market basics |
| 🔴 | Advanced (L3) | Research level: derivations, cited literature, reproducible code |

## The system: 7 tracks, 4 pillars

The library holds 25 papers. The core is a program of 22 documents across seven tracks, grouped into four pillars — **Mechanics** (how markets move), **Method** (how you test and build systems), **Context** (why markets move), and **Application** (how you deploy it — alpha and risk management) — plus three foundational papers on futures/market structure and technical analysis.

| Pillar | Track | L1 🟢 | L2 🟡 | L3 🔴 |
|---|---|---|---|---|
| Mechanics | A · Options | Options Fundamentals | The Greeks & Hedging | Dealer Flows & GEX |
| Mechanics | B · Volatility | Understanding Volatility | Vol Surface & VIX Complex | Vol Modeling, SVI & VRP |
| Mechanics | D · Market Mechanics | How Markets Move | — | The Flow Landscape |
| Method | C · Quant Methods | Statistics for Traders | Backtesting & Hypothesis Testing | Overfitting Control & Calibration |
| Method | F · Algo Development | — | From Paper to Strategy | Building, Running & Killing Algos |
| Context | E · Macro & Sentiment | Macro Foundations | Macro Regimes & Reaction Function | Sentiment & Positioning |
| Application | G · Strategy & Applications | — | Options as Crisis Insurance | From Model to Trade · ML for Strategy Building |

## Tracks

| # | Track | Scope | Level range |
|---|---|---|---|
| 00 | [Foundations](00-foundations/) | Futures contracts, margin & mark-to-market, the order book, the term structure | 🟢 |
| 01 | [Technical Analysis](01-technical-analysis/) | Trend, levels, momentum & the indicators — tested honestly | 🟢–🟡 |
| 02 | [Options](02-options/) | Payoffs, greeks, dealer hedging flows (GEX/vanna/charm) | 🟢–🔴 |
| 03 | [Volatility](03-volatility/) | RV vs. IV, the VIX complex, the surface, vol modeling & VRP | 🟢–🔴 |
| 04 | [Quant](04-quant/) | Statistics, backtesting, overfitting control & calibration | 🟢–🔴 |
| 05 | [Market Mechanics & Flows](05-market-mechanics/) | The auction & participants; the systematic/dealer flow landscape | 🟢/🔴 |
| 06 | [Macro, Fundamentals & Sentiment](06-macro-context/) | Growth/inflation/rates/liquidity, regimes, positioning | 🟢–🔴 |
| 07 | [Algo Development](07-algo-development/) | Anomaly replication; building, running & retiring strategies | 🟡–🔴 |
| 08 | [Strategy & Applications](08-strategy/) | Tail hedging; the Black-Scholes vol-forecast strategy; honest ML for strategy building | 🟡–🔴 |

**Beginner path:** start with the L1 papers: `03/L1` (volatility), `04/L1` (statistics), `02/L1` (options), `05/L1` (markets), `06/L1` (macro).
**Already trading?** Jump to the L3 flagships: `02/L3` (dealer flows & GEX), `07/L3` (building/running/killing algos). **Want applications?** The `08/` track deploys the rest: `08/L2` (crisis hedging with tail options), `08/L3` (the Black-Scholes vol-forecast strategy), `08/L3` (honest ML for strategy building).

## Index — original papers

| File | Track | Pillar | Level | Description |
|---|---|---|---|---|
| [L1-futures-and-market-structure](00-foundations/L1-futures-and-market-structure.pdf) | 00 Foundations | Mechanics | 🟢 | What a futures contract is; margin & mark-to-market; the order book; contango/backwardation & the roll; basis & hedging |
| [L1-technical-analysis](01-technical-analysis/L1-technical-analysis.pdf) | 01 Technical Analysis | Method | 🟢 | Trend, levels, momentum vs. mean-reversion, patterns — every rule treated as a testable hypothesis after costs & data-snooping |
| [L1-technical-indicators](01-technical-analysis/L1-technical-indicators.pdf) | 01 Technical Analysis | Method | 🟢 | The standard indicators (MA/EMA, MACD, RSI, stochastic, Bollinger, ATR, ADX) derived from their formulas |
| [L1-options-fundamentals](02-options/L1-options-fundamentals.pdf) | 02 Options | Mechanics | 🟢 | Reading a chain, payoffs, moneyness, put-call parity, the expiration landscape |
| [L2-greeks-and-hedging](02-options/L2-greeks-and-hedging.pdf) | 02 Options | Mechanics | 🟡 | Delta/gamma/theta/vega/rho + the vanna-charm-volga flow trio; a worked delta hedge |
| [L2-greeks-first-order](02-options/L2-greeks-first-order.pdf) | 02 Options | Mechanics | 🟡 | The four first-order greeks in depth — delta, theta, vega, rho — plus elasticity and dual delta |
| [L3-greeks-second-order](02-options/L3-greeks-second-order.pdf) | 02 Options | Mechanics | 🔴 | Gamma, vanna, charm, vomma (with veta/vera): how a first-order hedge goes stale |
| [L3-greeks-third-order](02-options/L3-greeks-third-order.pdf) | 02 Options | Mechanics | 🔴 | Speed, zomma, color, ultima: the sensitivities of the second-order greeks, and when they bite |
| [L3-dealer-flows-gex](02-options/L3-dealer-flows-gex.pdf) | 02 Options | Mechanics | 🔴 | How dealer hedging shapes index dynamics: GEX construction, the identification problem, honest limits |
| [L1-volatility-fundamentals](03-volatility/L1-volatility-fundamentals.pdf) | 03 Volatility | Mechanics | 🟢 | What vol measures, RV vs. IV, reading the VIX, expected move & σ-ladders |
| [L2-vol-surface-vix-complex](03-volatility/L2-vol-surface-vix-complex.pdf) | 03 Volatility | Mechanics | 🟡 | Skew & term structure, the CBOE index complex, an orthogonal vol-factor set |
| [L3-vol-modeling-vrp](03-volatility/L3-vol-modeling-vrp.pdf) | 03 Volatility | Mechanics | 🔴 | RV estimators, GARCH/HAR forecasting, forecast evaluation, the variance risk premium, SVI |
| [L1-statistics-for-traders](04-quant/L1-statistics-for-traders.pdf) | 04 Quant | Method | 🟢 | Distributions, base rates, expectancy vs. hit rate, bootstrap, a free-data toolset |
| [L2-backtesting-methodology](04-quant/L2-backtesting-methodology.pdf) | 04 Quant | Method | 🔴 | Pre-registration, OOS discipline, costs, track-record analysis, the failure catalogue |
| [L3-overfitting-calibration](04-quant/L3-overfitting-calibration.pdf) | 04 Quant | Method | 🔴 | Deflated Sharpe, PBO/CSCV, Brier calibration — the reusable validation suite |
| [L1-how-markets-move](05-market-mechanics/L1-how-markets-move.pdf) | 05 Market Mechanics | Mechanics | 🟢 | Price as an agreement, the order book, what moves price, the participant map |
| [L3-flow-landscape](05-market-mechanics/L3-flow-landscape.pdf) | 05 Market Mechanics | Mechanics | 🔴 | Dealer, vol-target, CTA & passive flows; price impact; a flow calendar & regime map |
| [L1-macro-foundations](06-macro-context/L1-macro-foundations.pdf) | 06 Macro | Context | 🟢 | Growth, inflation, rates, liquidity; the cycle, the yield curve, key data releases |
| [L2-macro-regimes-fundamentals](06-macro-context/L2-macro-regimes-fundamentals.pdf) | 06 Macro | Context | 🟡 | Computable regimes, the reaction function, financial conditions, a macro dashboard |
| [L3-sentiment-positioning](06-macro-context/L3-sentiment-positioning.pdf) | 06 Macro | Context | 🔴 | Survey/market/flow sentiment, COT positioning, the contrarian claim tested honestly |
| [L2-paper-to-strategy](07-algo-development/L2-paper-to-strategy.pdf) | 07 Algo Dev | Method | 🟡 | Reading papers critically, the replication crisis, the paper-to-reality gap |
| [L3-building-running-killing-algos](07-algo-development/L3-building-running-killing-algos.pdf) | 07 Algo Dev | Method | 🔴 | Spec, sizing & risk, live monitoring, real case studies incl. a kill case, retirement discipline |
| [L2-tail-hedging](08-strategy/L2-tail-hedging.pdf) | 08 Strategy | Application | 🟡 | Options as crisis insurance: the far-OTM "1-delta" put, the two convexities, the bleed, crisis alpha, sizing & monetization |
| [L3-model-to-trade](08-strategy/L3-model-to-trade.pdf) | 08 Strategy | Application | 🔴 | Black-Scholes as a map; a delta-hedged option is a variance bet; beating the VIX; a pre-registered short-variance strategy |
| [L3-ml-strategy-building](08-strategy/L3-ml-strategy-building.pdf) | 08 Strategy | Application | 🔴 | Honest ML: the overfitting gap, leakage, purged CV, the deflated-Sharpe/PBO gate, what ML can and cannot do |

## House rules for the original papers

- **No claim is "validated" without an out-of-sample test.** External sources make a claim *plausible*, never *confirmed*; only an own reproducible result with an OOS split earns the stronger word.
- **Every empirical figure is reproducible** from free data (Yahoo, FRED, CBOE, CFTC) with the `figures/*.py` script beside it; downloaded data is cached so figures are stable offline.
- **Pre-registration and direction checks.** Effect sizes and out-of-sample splits are fixed before the test; the sign of the data is checked against the sign of the claim before the claim is made.
- **Errata over silent edits.** When a number is wrong, it is corrected in [ERRATA.md](ERRATA.md), not quietly swapped.
- **Not investment advice.** These are research and educational documents.

## Data license

Every number is reproducible from **free, publicly retrievable** sources — Yahoo Finance's chart API, FRED, CBOE public delayed quotes and daily-history CSVs, CFTC, and optionsDX end-of-day chains. "Freely retrievable" is **not** the same as "redistributable": the figure scripts re-fetch the **licensed intraday option-chain snapshots** at run time (these are git-ignored and never redistributed), while the **free daily-history CSVs that CBOE publishes for public download** (e.g. `VIX_History.csv`, nine files under `03-volatility/figures/data/`) are included so the daily-data figures rebuild offline. This repository therefore redistributes no licensed optionsDX or CBOE intraday chains — only those free daily histories, derived aggregates, and the code needed to rebuild them (ERRATA F2). Anyone re-fetching that data is bound by the vendor's own terms of use.

## Sources & copyright

Papers and figures are © 2026 Jonas Löffler, licensed [CC BY 4.0](LICENSE); the accompanying code is licensed [MIT](LICENSE-CODE).
