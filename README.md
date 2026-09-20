# Trading Library

A curated library for traders — from market foundations to options mechanics, orderflow, volatility, quantitative methods, market flows, macro, and algo development.

This library is a set of original scientific papers written by Jonas Löffler (`L1`/`L2`/`L3`) — scientific-paper format, every empirical number reproducible from **free data** with the accompanying `figures/*.py` script.

> **Disclaimer.** These are research and educational documents, **not investment advice**, not a recommendation or solicitation to trade any security, and not a statement of the views of any employer. Any rule or threshold shown (e.g. a volatility cut-off) is an illustration of a method, not a signal to act on. Trading options and derivatives involves substantial risk of loss. You are responsible for your own decisions.

**Version & corrections.** Series **v1.0** (2026-09-20). Found errors are fixed in the open — see [CHANGELOG.md](CHANGELOG.md) and [ERRATA.md](ERRATA.md). Licensing: papers and figures under [CC BY 4.0](LICENSE); code under [MIT](LICENSE-CODE).

## Difficulty badges

| Badge | Level | Meaning |
|---|---|---|
| 🟢 | Beginner (L1) | No prior knowledge required |
| 🟡 | Intermediate (L2) | Assumes the track's L1 + market basics |
| 🔴 | Advanced (L3) | Research level: derivations, cited literature, reproducible code |

## The system: 6 tracks, 3 pillars

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
| 03 | [Options](03-options/) | Payoffs, greeks, dealer hedging flows (GEX/vanna/charm) | 🟢–🔴 |
| 04 | [Volatility](04-volatility/) | RV vs. IV, the VIX complex, the surface, vol modeling & VRP | 🟢–🔴 |
| 05 | [Quant](05-quant/) | Statistics, backtesting, overfitting control & calibration | 🟢–🔴 |
| 07 | [Market Mechanics & Flows](07-market-mechanics/) | The auction & participants; the systematic/dealer flow landscape | 🟢/🔴 |
| 08 | [Macro, Fundamentals & Sentiment](08-macro-context/) | Growth/inflation/rates/liquidity, regimes, positioning | 🟢–🔴 |
| 09 | [Algo Development](09-algo-development/) | Anomaly replication; building, running & retiring strategies | 🟡–🔴 |
| 10 | [Strategy & Applications](10-strategy/) | Tail hedging; the Black-Scholes vol-forecast strategy; honest ML for strategy building | 🟡–🔴 |

**Beginner path:** start with the L1 papers: `04/L1` (volatility), `05/L1` (statistics), `03/L1` (options), `07/L1` (markets), `08/L1` (macro).
**Already trading?** Jump to the L3 flagships: `03/L3` (dealer flows & GEX), `09/L3` (building/running/killing algos). **Want applications?** The `10/` track deploys the rest: `10/L2` (crisis hedging with tail options), `10/L3` (the Black-Scholes vol-forecast strategy), `10/L3` (honest ML for strategy building).

## Index — original papers

| File | Track | Pillar | Level | Description |
|---|---|---|---|---|
| [L1-futures-and-market-structure](00-foundations/L1-futures-and-market-structure.pdf) | 00 Foundations | Mechanics | 🟢 | What a futures contract is; margin & mark-to-market; the order book; contango/backwardation & the roll; basis & hedging |
| [L1-technical-analysis](01-technical-analysis/L1-technical-analysis.pdf) | 01 Technical Analysis | Method | 🟢 | Trend, levels, momentum vs. mean-reversion, patterns — every rule treated as a testable hypothesis after costs & data-snooping |
| [L1-technical-indicators](01-technical-analysis/L1-technical-indicators.pdf) | 01 Technical Analysis | Method | 🟢 | The standard indicators (MA/EMA, MACD, RSI, stochastic, Bollinger, ATR, ADX) derived from their formulas |
| [L1-options-fundamentals](03-options/L1-options-fundamentals.pdf) | 03 Options | Mechanics | 🟢 | Reading a chain, payoffs, moneyness, put-call parity, the expiration landscape |
| [L2-greeks-and-hedging](03-options/L2-greeks-and-hedging.pdf) | 03 Options | Mechanics | 🟡 | Delta/gamma/theta/vega/rho + the vanna-charm-volga flow trio; a worked delta hedge |
| [L2-greeks-first-order](03-options/L2-greeks-first-order.pdf) | 03 Options | Mechanics | 🟡 | The four first-order greeks in depth — delta, theta, vega, rho — plus elasticity and dual delta |
| [L3-greeks-second-order](03-options/L3-greeks-second-order.pdf) | 03 Options | Mechanics | 🔴 | Gamma, vanna, charm, vomma (with veta/vera): how a first-order hedge goes stale |
| [L3-greeks-third-order](03-options/L3-greeks-third-order.pdf) | 03 Options | Mechanics | 🔴 | Speed, zomma, color, ultima: the sensitivities of the second-order greeks, and when they bite |
| [L3-dealer-flows-gex](03-options/L3-dealer-flows-gex.pdf) | 03 Options | Mechanics | 🔴 | How dealer hedging shapes index dynamics: GEX construction, the identification problem, honest limits |
| [L1-volatility-fundamentals](04-volatility/L1-volatility-fundamentals.pdf) | 04 Volatility | Mechanics | 🟢 | What vol measures, RV vs. IV, reading the VIX, expected move & σ-ladders |
| [L2-vol-surface-vix-complex](04-volatility/L2-vol-surface-vix-complex.pdf) | 04 Volatility | Mechanics | 🟡 | Skew & term structure, the CBOE index complex, an orthogonal vol-factor set |
| [L3-vol-modeling-vrp](04-volatility/L3-vol-modeling-vrp.pdf) | 04 Volatility | Mechanics | 🔴 | RV estimators, GARCH/HAR forecasting, forecast evaluation, the variance risk premium, SVI |
| [L1-statistics-for-traders](05-quant/L1-statistics-for-traders.pdf) | 05 Quant | Method | 🟢 | Distributions, base rates, expectancy vs. hit rate, bootstrap, a free-data toolset |
| [L2-backtesting-methodology](05-quant/L2-backtesting-methodology.pdf) | 05 Quant | Method | 🔴 | Pre-registration, OOS discipline, costs, track-record analysis, the failure catalogue |
| [L3-overfitting-calibration](05-quant/L3-overfitting-calibration.pdf) | 05 Quant | Method | 🔴 | Deflated Sharpe, PBO/CSCV, Brier calibration — the reusable validation suite |
| [L1-how-markets-move](07-market-mechanics/L1-how-markets-move.pdf) | 07 Market Mechanics | Mechanics | 🟢 | Price as an agreement, the order book, what moves price, the participant map |
| [L3-flow-landscape](07-market-mechanics/L3-flow-landscape.pdf) | 07 Market Mechanics | Mechanics | 🔴 | Dealer, vol-target, CTA & passive flows; price impact; a flow calendar & regime map |
| [L1-macro-foundations](08-macro-context/L1-macro-foundations.pdf) | 08 Macro | Context | 🟢 | Growth, inflation, rates, liquidity; the cycle, the yield curve, key data releases |
| [L2-macro-regimes-fundamentals](08-macro-context/L2-macro-regimes-fundamentals.pdf) | 08 Macro | Context | 🟡 | Computable regimes, the reaction function, financial conditions, a macro dashboard |
| [L3-sentiment-positioning](08-macro-context/L3-sentiment-positioning.pdf) | 08 Macro | Context | 🔴 | Survey/market/flow sentiment, COT positioning, the contrarian claim tested honestly |
| [L2-paper-to-strategy](09-algo-development/L2-paper-to-strategy.pdf) | 09 Algo Dev | Method | 🟡 | Reading papers critically, the replication crisis, the paper-to-reality gap |
| [L3-building-running-killing-algos](09-algo-development/L3-building-running-killing-algos.pdf) | 09 Algo Dev | Method | 🔴 | Spec, sizing & risk, live monitoring, real case studies incl. a kill case, retirement discipline |
| [L2-tail-hedging](10-strategy/L2-tail-hedging.pdf) | 10 Strategy | Application | 🟡 | Options as crisis insurance: the far-OTM "1-delta" put, the two convexities, the bleed, crisis alpha, sizing & monetization |
| [L3-model-to-trade](10-strategy/L3-model-to-trade.pdf) | 10 Strategy | Application | 🔴 | Black-Scholes as a map; a delta-hedged option is a variance bet; beating the VIX; a pre-registered short-variance strategy |
| [L3-ml-strategy-building](10-strategy/L3-ml-strategy-building.pdf) | 10 Strategy | Application | 🔴 | Honest ML: the overfitting gap, leakage, purged CV, the deflated-Sharpe/PBO gate, what ML can and cannot do |

## House rules for the original papers

- **No claim is "validated" without an out-of-sample test.** External sources make a claim *plausible*, never *confirmed*; only an own reproducible result with an OOS split earns the stronger word.
- **Every empirical figure is reproducible** from free data (Yahoo, FRED, CBOE, CFTC) with the `figures/*.py` script beside it; downloaded data is cached so figures are stable offline.
- **Pre-registration and direction checks.** Effect sizes and out-of-sample splits are fixed before the test; the sign of the data is checked against the sign of the claim before the claim is made.
- **Errata over silent edits.** When a number is wrong, it is corrected in [ERRATA.md](ERRATA.md), not quietly swapped.
- **Not investment advice.** These are research and educational documents.

## Data license

Every number is reproducible from **free, publicly retrievable** sources — Yahoo Finance's chart API, FRED, CBOE public delayed quotes and daily-history CSVs, CFTC, and optionsDX end-of-day chains. "Freely retrievable" is **not** the same as "redistributable": the figure scripts re-fetch vendor data at run time, and this repository does not redistribute raw CBOE/optionsDX quotes — only derived aggregates and the code needed to rebuild them. Anyone re-fetching that data is bound by the vendor's own terms of use.

## Sources & copyright

Papers and figures are © 2026 Jonas Löffler, licensed [CC BY 4.0](LICENSE); the accompanying code is licensed [MIT](LICENSE-CODE).
