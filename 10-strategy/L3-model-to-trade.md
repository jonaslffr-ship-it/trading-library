---
title: "From Model to Trade"
last_updated: 2026-09-20
---

# From Model to Trade

## Abstract

The Black-Scholes-Merton model is wrong in every assumption and indispensable anyway. This paper takes it for what it is — a *map*, a lens that converts an option price into a single number, its implied volatility — and asks what a trader can build on that lens. The central reframing is that, once its direction is hedged away, an option is not a bet on where the market goes but on *how much it moves*: the profit-and-loss of a delta-hedged option is, to first order, the gamma-weighted difference between realized and implied variance. An edge in options is therefore an edge in *forecasting realized volatility relative to the price the market has already put on it*. We test that premise honestly on two decades of free S&P 500 and VIX data. First we ask whether a free-data volatility forecast can beat the VIX out of sample, and find that a heterogeneous-autoregressive (HAR) model matches the implied volatility in-sample but does *not* beat it out of sample (QLIKE 0.449 versus 0.444) — while both crush a random walk. Then we pre-register a single short-variance rule and measure what the variance risk premium actually pays: an unconditional short earns a modest Sharpe of about 0.30 with a brutal left tail (a −0.76 variance-point month in March 2020), while conditioning the short on the forecast — standing aside when recent realized volatility is already high relative to implied — avoids the worst months and lifts the out-of-sample Sharpe, a result we report with explicit caveats about its short sample and stylized frictions. The lesson is not a strategy to run but a discipline: the model tells you what you are trading, the forecast tells you when the price is wrong, and honest accounting tells you how little of either survives contact with cost and regime change. Every figure is reproducible from free data.

## Keywords

Black-Scholes-Merton, implied volatility, realized volatility, delta hedging, gamma, variance risk premium, volatility forecasting, HAR-RV, GARCH, QLIKE, short variance, pre-registration, out-of-sample, model risk

## 1 Introduction

### 1.1 Motivation and thesis

Every options trader uses the Black-Scholes-Merton model, and every honest one knows it is false. Its assumptions — constant volatility, no jumps, lognormal returns, costless continuous hedging — are each contradicted by the first chart a beginner ever sees. And yet the model is not discarded, because it does one thing no amount of realism has improved upon: it provides a *common language*. It maps the messy price of an option onto a single, comparable number — the *implied volatility* — and in doing so turns a chaos of strikes and expiries into one surface a human can reason about. The physicist's warning applies exactly: the map is not the territory. But you cannot navigate without a map, and this one is the best we have.

The thesis of this paper is what follows once you hold the model at that arm's length. If an option's price is really a statement about volatility, then *trading* an option — after you have hedged away its direction — is a bet on volatility, and nothing else. The profit-and-loss of a delta-hedged option position is, to first order, proportional to the difference between the volatility that *realizes* and the volatility that was *implied* in the price you paid. An edge in options, therefore, is not a view on the market's direction dressed up in greeks; it is an edge in *forecasting realized volatility relative to the market's own implied forecast, and trading the gap.* This paper builds that idea from the model up, and then — because the house rule of this library is that nothing is believed until it is tested on data that could have refuted it — measures how much of the apparent edge is real. The answer, foreshadowed honestly here, is sobering: the market's implied volatility is very hard to beat, most of the available return is a risk premium rather than a forecasting skill, and the honest craft is knowing the difference.

### 1.2 Scope, prerequisites, and intended reader

This paper sits in the Trading Library's *Strategy & Applications* track. It assumes the greeks-and-hedging paper (delta, gamma, theta, vega as working tools), the volatility papers (realized versus implied volatility, the VIX, the surface), and — critically — the backtesting paper, whose pre-registration and out-of-sample discipline are used here without re-derivation. It uses the Black-Scholes formula as a calculator and states the one first-order P&L result it relies on without a stochastic-calculus derivation; a reader who wants the full derivation is pointed to the literature. The reader is assumed to be comfortable reading a short Python computation and a regression output.

After reading this paper, a reader can:

- state each Black-Scholes assumption, say precisely how it fails, and explain why the model survives its own falseness as a quoting and hedging language;
- explain, and use, the reframing that a delta-hedged option is a position in the realized-minus-implied variance gap;
- compare volatility forecasts (random walk, GARCH, HAR, and the VIX itself) with a proper loss function, and judge honestly whether a free-data model beats the market's implied number out of sample;
- define and measure the variance risk premium, and recognise the short-volatility return signature — high hit rate, positive mean, catastrophic left tail — for what it is;
- pre-register and evaluate a volatility-based strategy end to end, and read its result with the humility that a short out-of-sample window and a stylized cost model demand.

### 1.3 Data and reproducibility

All numerical examples use freely available data (Yahoo's public chart API for S&P 500 and VIX) and are reproducible from the accompanying `figures/*.py` scripts, which cache their downloads. Where an option value or greek is needed it is computed from Black-Scholes on stated inputs. The strategy of Section 7 is defined by one rule fixed in advance, with the in-sample/out-of-sample split date chosen before any P&L was computed and opened once. *This is a research and educational document, not investment advice.*

### 1.4 Organization of this paper

Section 2 lays out the model as a map — its assumptions, their failures, and why implied volatility is the useful output of a wrong formula. Section 3 states the reframing that an option is a volatility bet and gives the one P&L identity the paper rests on. Section 4 fixes what "realized volatility" means as the forecast target. Section 5 confronts the hard empirical question — can a free-data forecast beat the VIX? — with an out-of-sample horse race (Figure 1). Section 6 explains why the implied-minus-realized gap has a sign and a price: the variance risk premium. Section 7 pre-registers and tests a single short-variance strategy, unconditional and forecast-conditioned, on free data (Figure 2). Section 8 is the failure catalogue — the short-vol tail, hedging frictions, non-stationarity, and the circularity that makes most reported volatility edges evaporate. Section 9 closes with misconceptions, a glossary, and references.

## 2 Black-Scholes as a map, not the territory

### 2.1 The model in one breath

Black-Scholes-Merton prices a European option by assuming the underlying follows a geometric Brownian motion with a *constant* volatility, that trading is continuous and frictionless, that the risk-free rate is known and constant, and that returns are therefore lognormal. Under those assumptions the option can be perfectly replicated by a continuously rebalanced position in the underlying and cash, and its price is the cost of that replication — a value that depends on spot, strike, time, rate, and the one unobservable input, volatility. The formula is not the point; the *replication argument* is, because it is what ties an option's price to volatility in the first place.

### 2.2 Every assumption is false, in a known direction

Each assumption fails, and the failures are not random — they are the reason the market's option prices deviate from the flat-volatility model in a stable, exploitable shape. Volatility is *not* constant: it clusters and mean-reverts, so a single number cannot fit all maturities (the term structure) at once. Returns are *not* lognormal: they have fat tails and jumps, so far-OTM options are worth more than the model says — the skew and smile of the surface. Hedging is *not* continuous or free: you rebalance discretely and pay a spread each time, so perfect replication is a fiction and the replicator bears a residual risk (Section 8.2). Rates are *not* the dominant risk intraday. The honest summary is Rebonato's: implied volatility is *"the wrong number to put into the wrong formula to get the right price"* — a fudge factor that absorbs everything the model omits, and is useful precisely because it does.

### 2.3 Why a false model is still the right lens

The model survives because it is not used as a truth but as a *translator*. Quoting an option in implied-volatility terms strips out the mechanical dependence on spot, strike and time, leaving a single number that is comparable across contracts and days — the way quoting a bond in yield rather than price makes bonds comparable. And the replication argument, though it never holds exactly, is approximately right often enough that the *greeks* it produces are the correct first-order description of an option's risk. The map is wrong about the territory in every detail and still gets you where you are going, because it is the coordinate system everyone else is also using. That is the sense in which this paper "explains Black-Scholes": not as a law of prices, but as the lens that makes the next section's reframing possible.

## 3 The reframing: an option is a bet on volatility

### 3.1 Delta-hedging strips the direction

A long call makes money when the market rises — but only because it has positive delta, and delta can be removed. Sell delta shares of the underlying against the call and, at that instant, the position has no first-order exposure to direction: a small move up or down changes the call and the stock hedge by offsetting amounts. What is left is not nothing. It is *convexity*: the call's delta grows as the market rises and shrinks as it falls, so a delta-hedged long option *gains* from movement in either direction and *pays* for that gain through time decay. The direction has been hedged away; what remains is a pure position in *how much the market moves*.

### 3.2 The one identity this paper rests on

Made precise, the profit-and-loss of a delta-hedged option over a small step is, to first order,

**P&L ≈ ½ · Γ · S² · ( r_realized² − σ_implied² · Δt ),**

the *gamma-weighted difference between realized and implied variance*. Read it slowly. Γ·S² is the *dollar gamma*, the size of the convexity bet. The bracket is the day's realized squared return minus the variance the option's price charged you for that day. If the market moved *more* than implied, a delta-hedged *long* option profits; if it moved *less*, the long option's time decay exceeds its convexity gain and it loses. Summed over the option's life, a delta-hedged position is a bet on realized variance against the implied variance locked in at trade time. This is the whole engine of volatility trading, and it is why the rest of the paper is about *forecasting realized volatility* and *measuring the price the market charges for it* — because those two quantities, and their difference, are literally the terms of the trade.

### 3.3 From identity to edge

The identity has an immediate, humbling consequence. To make money from a delta-hedged option you do not need to predict the market's direction — but you *do* need to predict its realized volatility better than the implied volatility already embedded in the price. The implied volatility is not a lazy guess; it is the market's own forecast, set by participants who also know the identity above. So the question that decides whether any volatility strategy has an edge is exactly the question of Section 5: *can you forecast realized volatility better than the VIX?* If you cannot, then trading the gap is not a forecasting edge at all — it is harvesting a risk premium (Section 6), which is a different and more fragile thing.

## 4 The quantity you are forecasting: realized volatility

Before forecasting volatility one must define it, and the definition is a modelling choice with consequences. *Realized volatility* over a window is the annualized standard deviation of the underlying's returns in that window; the simplest estimator is the close-to-close one — the sample standard deviation of daily log returns, times the square root of 252 to annualize. It is unbiased and transparent, and it is what this paper forecasts: the mean daily variance over the next 21 trading days, a one-month realized-variance target that lines up with the one-month implied volatility of the VIX. More efficient estimators exist — Parkinson, Garman-Klass and Yang-Zhang use the intraday high and low to extract more information per day, and intraday returns give *realized variance* proper — and the volatility-modeling paper treats that estimator zoo in full. Here the close-to-close target suffices, with one honesty flag carried forward: a squared daily return is an extremely *noisy* one-day proxy for variance, which is why the forecasting models of Section 5 lean on weekly and monthly averages rather than yesterday alone.

## 5 Forecasting volatility, and the hard truth about the VIX

### 5.1 The honest horse race

Can a model built on free data forecast next month's realized volatility better than the market's own implied volatility? This is the question that decides whether a "volatility forecasting strategy" is forecasting or merely premium-harvesting, so it must be answered before any strategy is built, and answered out of sample. We compare three forecasts of the next-21-day mean daily variance: a *random walk* (last month's realized variance carried forward), the *VIX* (implied variance, the market's forecast), and a *HAR* model — Corsi's *heterogeneous autoregression*, which regresses future realized variance on its own daily, weekly, and monthly trailing averages, fitted on the in-sample period only. Forecasts are scored by *QLIKE*, a loss function appropriate to variance because it penalises under- and over-prediction asymmetrically and is robust to the noise in the realized proxy.

![Left: the VIX (implied volatility, annualized) against the realized volatility of the following 21 trading days, 2004-2026; the implied line sits above the realized line most of the time (the variance risk premium of section 6) and leads its turns. Right: out-of-sample QLIKE forecast error (lower is better) for the three predictors. The random walk (0.633) is far worse than either the VIX (0.444) or the HAR model (0.449); the free-data HAR matches the market's implied forecast in-sample but does not beat it out of sample. Yahoo GSPC + VIX; HAR fitted in-sample (pre-2020) only, scored out-of-sample.](figures/fig_g2_forecast.png)

### 5.2 What the race shows

The result is the one the literature has found repeatedly, reproduced here on free data. Both the VIX and the HAR model crush the random walk out of sample (QLIKE 0.444 and 0.449 versus 0.633), confirming that volatility is genuinely forecastable — it clusters and mean-reverts, and a model that uses that structure beats naively assuming tomorrow looks like yesterday. But the HAR model, which matches the VIX in-sample, does **not** beat it out of sample: 0.449 against the VIX's 0.444, a hair *worse*. This is the hard truth of the section title. The market's implied volatility already embeds the mean-reversion and clustering that the HAR model learns, plus information the model does not have, and it is a formidable forecast to beat. The honest implication for strategy design is decisive: if a free-data model cannot out-forecast the VIX, then a strategy that trades the implied-minus-realized gap is *not* profiting from superior forecasting. It is being paid a *risk premium* — the subject of Section 6 — and the two must never be confused, because they fail in completely different ways.

## 6 The variance risk premium: why the gap has a sign and a price

### 6.1 Implied exceeds realized, on average

Across the sample the VIX averaged 19.0 % while the volatility that subsequently realized averaged 15.5 % — implied volatility sat roughly three and a half vol points above realized, on average, for two decades. Figure 1's left panel is that fact drawn as two lines: the implied line rides persistently above the realized line. This gap is the *variance risk premium* (VRP): the systematic amount by which the market charges more for variance than variance turns out to cost. It is not a forecasting error — it is a *price*. Option sellers demand it as compensation for bearing the risk that volatility explodes exactly when everything else in a portfolio is going wrong, and buyers pay it for the insurance the tail-hedging paper is entirely about. The premium is the seller's long-run edge and the hedge-buyer's long-run rent.

### 6.2 The premium is a risk premium, not a free lunch

Because the VRP is compensation for a risk, it behaves like one: small and steady in good times, and violently negative exactly when the risk it is paid for materialises. Selling variance earns the premium month after month and then hands a chunk of it back in a crash, when realized volatility gaps far above the implied level that was sold. This is the short-volatility signature — a high hit rate and a positive average masking a catastrophic left tail — and it is the reason the strategy of Section 7 is dangerous in precisely the way a naive Sharpe ratio hides. The premium is real and persistent; it is also, as Section 8 insists, the compensation for a risk that is genuinely borne, not an inefficiency to be casually farmed.

## 7 The mispricing strategy, pre-registered

### 7.1 The rule, fixed in advance

We now trade the gap, with a rule written down before any P&L was computed. Each month, on the first trading day, we compute the short-variance profit over the next 21 trading days as the implied variance sold minus the realized variance that follows, minus a stylized round-trip friction: **P&L = (VIX/100)² − realized annualized variance − 0.0015**. We run it two ways. The *unconditional* version sells variance every month — pure premium harvesting. The *conditional* version sells only when the in-sample-fitted HAR forecast predicts realized variance *below* implied — that is, only when volatility looks *rich* relative to a free-data forecast — and stands aside otherwise. The out-of-sample period (2020 onward) was fixed in advance and opened once. Nothing about the rule, the threshold, or the split was tuned to the result.

![Top: cumulative short-variance P&L in annualized variance points, 2004-2026, for the unconditional short (red) and the HAR-conditional short (green); the vertical line marks the out-of-sample boundary. Both climb steadily and give back sharp chunks in the 2008 and 2020 crashes, but the conditional version - which stands aside when recent realized vol is already high relative to implied - avoids the worst drawdowns. Bottom: the monthly P&L, showing the short-vol signature of small steady gains (green) punctuated by rare violent losses (red), the deepest being -0.76 variance points in March 2020. Yahoo GSPC + VIX, monthly; HAR fitted in-sample only; single fixed rule, no optimization.](figures/fig_g2_strategy.png)

### 7.2 What the strategy earns, honestly

The unconditional short earns a full-sample Sharpe of about **0.30** (in-sample 0.38, out-of-sample 0.20) with a hit rate near **79 %** and a worst month of **−0.76 variance points**, in March 2020. That is the variance risk premium, drawn: a positive but modest risk-adjusted return, most of it given back in the two crashes, exactly the signature Section 6 predicted. The conditional version — standing aside when the forecast says volatility is not actually rich — earns a markedly higher Sharpe (full **0.94**, out-of-sample **1.24**), takes only 73 % of the months, and cuts the worst month to **−0.25**. On its face the forecast conditioning helped, and helped out of sample.

### 7.3 Why the honest verdict is smaller than the number

That out-of-sample Sharpe of 1.24 must be read with discipline, and the discipline says: *do not believe it as stated.* Three reasons, each a Section 8 theme in miniature. First, the improvement comes almost entirely from *avoiding a handful of crash months* — the conditional rule dodged March 2020 because, by the entry date, recent realized volatility had already spiked, so the HAR forecast exceeded the VIX and the rule stood aside. That is genuine, non-look-ahead information, and it is economically sensible ("do not sell volatility that is already erupting"), but it means the edge is *tail-timing on a few observations*, not a dense, repeatable skill — and a few observations are exactly what a Sharpe ratio flatters. Second, the out-of-sample window is short (80 months) and dominated by the calm post-2020 regime that is kind to short-volatility strategies; the number would look different across a window that contained a second 2008. Third, the P&L is *stylized*: a clean variance swap traded costlessly does not exist, and a real implementation via delta-hedged straddles bleeds the discrete-hedging and transaction frictions of Section 8.2, which fall hardest on exactly the volatile months where the edge lives. The honest verdict is therefore modest and useful: the bulk of the return is the unconditional variance premium of Section 6, and the forecast's real contribution is a *stand-aside signal* — knowing when *not* to sell — whose value is real but whose measured magnitude here is fragile. That gap between the flattering number and the defensible claim is the entire reason this library pre-registers, splits, and reports with caveats.

## 8 The traps

### 8.1 Short volatility is picking up nickels in front of a steamroller

The defining danger of every strategy in this paper is the short-volatility tail. A positive average and a high hit rate are perfectly consistent with a strategy that loses more in one month than it made in the previous three years — the −0.76 variance-point March-2020 print against a stream of small green gains. Position sizing, not signal quality, is what kills or saves such a strategy: sized to look good in calm years, it is sized to be destroyed in the first crash. The correct sizing is set from the *tail*, not the average, and pre-committed — the same discipline the tail-hedging paper applies from the buyer's side.

### 8.2 The hedging is not free and not continuous

The clean P&L identity of Section 3.2 assumes continuous, costless delta-hedging. Reality rebalances discretely and pays a spread each time, so the replication is imperfect and the realized P&L carries a *hedging error* that grows with how violently the spot moves between rebalances — again, worst in exactly the volatile periods the strategy cares about. Every backtest in this space that prices options cleanly and hedges frictionlessly, as Figure 2's stylized variance P&L does, is reporting an *upper bound*; the real strategy is that number minus a cost that is largest when it hurts most.

### 8.3 Non-stationarity and the circularity trap

Volatility regimes drift: the VRP compresses for years and then inverts, the skew steepens, the relationship between implied and realized shifts with the growth of 0DTE and vol-control flows. A forecast or a threshold fitted on one regime need not survive the next, which is why the single out-of-sample window of Section 7 is evidence and not proof. The subtler trap is *circularity*: it is fatally easy to fit the volatility forecast on the same data used to test the strategy, so that the forecast "knows" the crashes it is supposed to have predicted. This paper guards against it by fitting the HAR model on the in-sample period only and scoring both the forecast and the strategy out of sample — the minimum discipline, and still not a guarantee against the slower leakage of having lived through the out-of-sample period as its designer. The honest researcher treats every volatility edge as guilty of overfitting until an out-of-sample split, a cost model, and a regime check have each failed to convict it.

## 9 Discussion, misconceptions, glossary, references

### 9.1 Common misconceptions

*"Black-Scholes is useless because its assumptions are false."* — Its assumptions are false and it is indispensable; it is a translator, not a law (Section 2.3). *"If I can price options I can beat the market."* — Pricing is not forecasting; the implied volatility is already the market's forecast, and it is hard to beat (Section 5). *"My delta-hedged option is a directional trade."* — Hedged, it is a volatility trade; the direction is gone and the variance gap remains (Section 3). *"Short volatility is free money — look at the hit rate."* — The hit rate hides the tail; the average is a risk premium paid for a real risk that arrives all at once (Section 6, Section 8.1). *"My backtest hedged perfectly, so the P&L is real."* — Frictionless hedging overstates every volatility strategy; the real number is smaller and worst when it matters (Section 8.2).

### 9.2 Glossary

- **Implied volatility** — the volatility input that makes the Black-Scholes price equal the market price; the market's forecast and quoting language, not a physical quantity.
- **Realized volatility** — the annualized standard deviation of the underlying's actual returns over a window; the quantity a volatility trade is ultimately a bet on.
- **Delta hedging** — holding −delta of the underlying against an option to remove first-order directional exposure, leaving the convexity (volatility) exposure.
- **Dollar gamma (Γ·S²)** — the size of a delta-hedged option's convexity bet; the weight on the realized-minus-implied variance difference in the P&L identity.
- **Variance risk premium (VRP)** — the systematic gap by which implied variance exceeds subsequently realized variance; a risk premium, not a forecast error.
- **HAR-RV** — the heterogeneous autoregressive model of realized volatility, regressing future RV on its daily, weekly and monthly trailing averages; the free-data workhorse forecast.
- **QLIKE** — a loss function for volatility forecasts, robust to the noise in the realized proxy and appropriate to variance's asymmetry.
- **Short variance / short volatility** — a position that earns the VRP by selling implied variance and paying realized; high hit rate, positive mean, catastrophic left tail.

### 9.3 References

- Black, F. & Scholes, M. (1973). *The Pricing of Options and Corporate Liabilities.* Journal of Political Economy. Merton, R. (1973). *Theory of Rational Option Pricing.* Bell Journal.
- Rebonato, R. (2004). *Volatility and Correlation* (2nd ed.). Wiley. [Implied volatility as "the wrong number in the wrong formula".]
- Carr, P. & Madan, D. (1998). *Towards a Theory of Volatility Trading.* In *Volatility* (Risk Books). [The delta-hedged P&L as a variance bet.]
- El Karoui, N., Jeanblanc, M. & Shreve, S. (1998). *Robustness of the Black and Scholes Formula.* Mathematical Finance. [The gamma-weighted variance-difference P&L under model misspecification.]
- Corsi, F. (2009). *A Simple Approximate Long-Memory Model of Realized Volatility.* Journal of Financial Econometrics. [HAR-RV.]
- Bollerslev, T., Tauchen, G. & Zhou, H. (2009). *Expected Stock Returns and Variance Risk Premia.* Review of Financial Studies.
- Carr, P. & Wu, L. (2009). *Variance Risk Premiums.* Review of Financial Studies.
- Bakshi, G. & Kapadia, N. (2003). *Delta-Hedged Gains and the Negative Market Volatility Risk Premium.* Review of Financial Studies.
- Patton, A. (2011). *Volatility Forecast Comparison Using Imperfect Volatility Proxies.* Journal of Econometrics. [QLIKE and robust loss functions.]
- Diebold, F. & Mariano, R. (1995). *Comparing Predictive Accuracy.* Journal of Business & Economic Statistics.
- Derman, E. & Taleb, N. (2005). *The Illusions of Dynamic Replication.* Quantitative Finance. [Why real hedging is neither continuous nor free.]

*All references are publicly accessible: peer-reviewed journal articles (several via open-access working-paper versions) and published books. No proprietary, subscription, or trading-course material is cited.*

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| The delta-hedged option P&L is, to first order, the gamma-weighted difference between realized and implied variance | Literature — (El Karoui, Jeanblanc & Shreve 1998) |
| Implied volatility is "the wrong number in the wrong formula to get the right price" — a useful fudge factor despite every false assumption | Literature — (Rebonato 2004) |
| HAR-RV regresses future realized variance on its daily, weekly and monthly trailing averages | Literature — (Corsi 2009) |
| QLIKE is a proxy-robust loss function appropriate to comparing variance forecasts | Literature — (Patton 2011) |
| Both the VIX and a free-data HAR beat a random walk out of sample (QLIKE 0.444 and 0.449 vs 0.633), but the HAR does not beat the VIX | Own reproducible computation — `figures/fig_g2_forecast.py`; OOS split |
| Over 2004–2026 the VIX averaged 19.0% against 15.5% realized — implied sits ~3.5 vol points above realized | Own reproducible computation — `figures/fig_g2_forecast.py` |
| The implied-minus-realized gap is a risk premium paid for a genuinely borne risk, not a forecasting error | Literature — (Carr & Wu 2009) |
| An unconditional monthly short-variance rule earns a full-sample Sharpe ≈ 0.30, ~79% hit rate, worst month −0.76 variance points (Mar 2020) | Own reproducible computation — `figures/fig_g2_strategy.py`; OOS split |
| HAR-conditioning lifts the out-of-sample Sharpe to 1.24, but the gain is tail-timing on a handful of crash months and is fragile | Own reproducible computation — `figures/fig_g2_strategy.py`; OOS split |
| Real delta-hedging is neither continuous nor free, so a frictionless backtest reports an upper bound on volatility-strategy P&L | Literature — (Derman & Taleb 2005) |
| Short-volatility strategies must be sized from the tail, not the average — a high hit rate masks a catastrophic left tail | Practitioner consensus — not independently verified |
