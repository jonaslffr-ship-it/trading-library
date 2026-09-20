---
title: "Understanding Volatility"
last_updated: 2026-09-20
---

# Understanding Volatility

## Abstract

Volatility is the unit of account of the options market: it is how uncertainty is measured, quoted, and traded. This paper builds the concept from zero. We define volatility as the *dispersion* of returns rather than their direction, derive the √252 bridge between daily and annualized volatility with nothing but arithmetic, and compute realized volatility by hand on twenty-one actual S&P 500 sessions, with every intermediate number shown. Implied volatility is then introduced as the market's priced-in uncertainty, and the VIX is demystified: what it aggregates, what its levels have historically meant across 9,275 trading days since 1990, and why *"the VIX is a price, not a forecast"* is the single most important sentence in this paper. Three behavioral regularities — clustering, mean reversion, and the leverage effect — are each shown on fifteen years of free data. Finally, a pre-committed test of the VIX-implied daily expected move finds the index inside its ±1σ band on 81.4% of 3,770 days, against a naive-normal 68.3% — though most of that gap is the fat-tailed shape of daily returns (a fairly priced but leptokurtic distribution already lands roughly 75–77% inside), and only the residual is the variance risk premium widening the band. Every figure is reproducible from free data with the accompanying scripts.

## Keywords

Volatility, realized volatility, implied volatility, VIX, VXN, VVIX, rule of 16, expected move, sigma-ladder, volatility clustering, mean reversion, leverage effect, variance risk premium, IV rank, IV percentile

## 1 Introduction

### 1.1 Motivation and thesis

Ask a newcomer what the VIX at 20 means and you will usually hear some version of "the market expects a 20% crash." Ask what volatility itself is and you will hear "how much the market moves" — which is close, but leaves out the two distinctions on which everything else depends: volatility measures the *size* of moves and is silent about their *direction*, and the word covers two entirely different objects — a **measured** quantity (what prices actually did) and a **traded price** (what the market charges today for exposure to what prices might do). Confusing the measurement with the price is, in this author's view, the most expensive conceptual mistake available to a beginner in this field, because it turns an insurance quote into a prophecy and a premium into a promise.

The thesis of this paper follows directly: *volatility becomes usable the moment you can compute it yourself and can say, for any volatility number you meet, whether it is a measurement or a price.* Everything here serves that goal. We compute the measured kind (realized volatility) by hand on real data, define the priced kind (implied volatility) without any calculus, put the most famous volatility number in the world — the VIX — in front of thirty-six years of its own history, and then test, on 3,770 trading days, how the priced kind compares with what the market subsequently did. The result of that test, reported as-is, is the paper's empirical centerpiece.

### 1.2 Scope, prerequisites, and intended reader

This paper sits in the Trading Library's *Volatility* track. It assumes you know what a stock index is, what "the S&P 500 closed up 1%" means, and nothing else: every technical term is defined at first use, all mathematics is arithmetic (add, multiply, square, take a square root), and there is no code in the body of the paper. Options appear only to the depth needed to understand where implied volatility comes from; the options-fundamentals paper treats them properly. Deeper volatility material — the VIX term structure, VVIX and the volatility-of-volatility complex, and the variance risk premium as a research object — lives in the volatility-surface paper and the volatility-modeling paper and is only previewed here.

After reading this paper, a reader can:

- compute the *realized volatility* of any price series with nothing but a spreadsheet, and state which window and conventions they used;
- convert between daily and annualized volatility in their head using the rule of 16, and say precisely when that shortcut misleads;
- read a VIX level against thirty-six years of base rates instead of against headlines;
- explain the difference between implied and realized volatility as *price versus outcome*, and why a persistent gap between them is not an error;
- name the three standard behaviors of volatility — clustering, mean reversion, the leverage effect — and the practical consequence of each;
- compute the daily *expected move* from an index level and its volatility index, build a σ-ladder from it, and score yesterday's band honestly against what happened;
- use *IV rank* and *IV percentile* as context filters, and explain why "IV is high" is never, by itself, a trade.

### 1.3 Data and reproducibility

Nothing here is called *validated* on the strength of external sources alone, and where own numbers are shown, the direction of the data is checked explicitly against the direction of the claim before the claim is made.

All numerical examples and figures use freely available data — daily S&P 500 closes from Yahoo Finance's public chart API and the volatility index series from FRED (the Federal Reserve Bank of St. Louis data service) — and are reproducible from the scripts in the `figures/` directory next to this document; each script caches its downloads so the numbers are stable offline. No proprietary or licensed data appears anywhere in this paper. *This is a research and educational document, not investment advice.*

### 1.4 Organization of this paper

Section 2 defines what volatility measures, builds the bridge between daily and annualized volatility, and derives the rule of 16. Section 3 computes realized volatility step by step on twenty-one real S&P 500 sessions (the full worksheet is shown as a table) and explains, in intuition only, why estimators that use the intraday range exist. Section 4 introduces implied volatility as the market's priced-in uncertainty and takes a first look at the gap between implied and realized. Section 5 demystifies the VIX — what it aggregates, what its levels have historically meant, why it is a price and not a forecast — and introduces its siblings VXN and VVIX. Section 6 shows how volatility behaves: clustering, mean reversion and regimes, and the leverage effect, each with its own panel of Figure 3. Section 7 turns implied volatility into the daily expected move and the σ-ladder, scores yesterday's band honestly, and then scores fifteen years of such bands. Section 8 presents the first practical signals (IV rank and IV percentile) and their limits. Section 9 collects common misconceptions, Section 10 is a glossary of roughly forty terms, and the references close the paper.

## 2 What volatility measures

### 2.1 Dispersion, not direction

Start with the raw material. A *return* is the percentage change of a price from one close to the next: if the S&P 500 closes at 7,552 today and 7,638 tomorrow, tomorrow's return is (7,638 ÷ 7,552 − 1) × 100 ≈ +1.14%. A price chart is one line; the same market seen as returns is a sequence of small positive and negative numbers, most of them between −1% and +1%.

*Volatility* is a property of that sequence: it measures how widely the returns are **scattered**, not where they are headed. Two markets can have the same overall drift and utterly different volatility. Imagine two indices that both end a month exactly where they started: the first moved ±0.1% a day, the second alternated +2.0% and −2.0%. Their monthly returns are identical — zero — but the second was twenty times as violent, its options were worth far more, and any position with a stop-loss lived a completely different life in it. Volatility is the number that separates those two worlds, and it does so by ignoring sign: a −1% day and a +1% day contribute *exactly the same amount* to volatility. That is not a defect. It is the definition — volatility answers "how big are the moves?", never "which way?"

The standard measure of scatter is the *standard deviation*, and its computation is four steps of arithmetic: take each return's *deviation* — its distance from the average return; square each deviation (which erases the sign and weights big moves more than proportionally); average the squares (that average is called the *variance*); and take the square root to come back to percent units. Squaring, rather than just dropping the minus signs, is a deliberate choice: it makes one 3% day count as much as nine 1% days, which matches how options and risk actually experience markets — pain and payoff concentrate in the large moves. Section 3 runs these four steps on real data with nothing hidden.

### 2.2 Daily and annualized volatility: the √252 bridge

A daily standard deviation of, say, 0.6% is a perfectly good number, but the industry quotes volatility *annualized* — scaled to a one-year horizon — so that a 30-day option, a 90-day option, and a risk report can all speak the same unit. The bridge between the two rests on one idea: **variances add over time**. If tomorrow's move is unrelated to today's, then the uncertainty of a two-day span is not twice the daily standard deviation — it is twice the daily *variance*, because scatter accumulates in squares, not in straight lines. Concretely: two independent days of 1% daily volatility produce a two-day variance of 1² + 1² = 2, hence a two-day volatility of √2 ≈ 1.41%, not 2%.

Stretch the same logic across a year. A trading year has about 252 sessions (365 days minus weekends and holidays), so the annual variance is 252 × the daily variance, and therefore

annualized volatility = daily volatility × √252 ≈ daily volatility × 15.87.

A market that moves 1% a day is a market with roughly 15.9% annualized volatility. Two honest caveats belong next to this formula. First, the independence assumption is only approximately true — Section 6 shows that the *size* of moves is in fact somewhat predictable from one day to the next — so √252 scaling is a convention, not a law of nature; it is, however, the convention the entire market quotes in, so it is the one to learn. (Hull 2021; Sinclair 2013) Second, the choice of 252 *trading* days (rather than 365 calendar days) is likewise convention, and it is baked into every number in this paper.

### 2.3 The rule of 16 — where it comes from, when it misleads

Reading the bridge backwards gives the most useful mental shortcut in this field. Since √252 ≈ 15.87 ≈ 16 (note that 16 × 16 = 256, nearly 252):

daily volatility ≈ annualized volatility ÷ 16.

This is the *rule of 16*. A VIX at 16 corresponds to daily moves of about 1%; VIX 24 to about 1.5% a day; VIX 32 to about 2%; VIX 80 — the neighborhood of the 2008 and 2020 panics — to daily swings of 5%. The rule turns an abstract index level into a felt quantity, and it is exact enough for any mental arithmetic: 17.71 ÷ 15.87 = 1.116%, while the rule of 16 says 1.107% — a rounding error. Rounding √252 = 15.87 up to 16 overstates daily volatility by 16 ÷ 15.87 − 1 ≈ 0.79%, small enough to ignore for mental arithmetic but worth naming.

The rule misleads in four specific ways, and it is worth naming them now because the rest of the paper returns to each:

- **A standard deviation is not a typical move.** Under a bell-shaped distribution the *average* absolute daily move is only about 0.8 of a standard deviation, so "VIX 16" suggests typical days nearer 0.8% than 1%. The 1σ number is a scale, not a forecast of the median day. (Sinclair 2013)
- **The VIX is not a neutral estimate to begin with.** It carries a built-in premium above subsequent realized volatility (Sections 4.3 and 7.4 measure this at length), so the daily move it implies is systematically on the high side.
- **Thirty days is not "tomorrow."** The VIX averages the coming thirty days; volatility is not spread evenly across them. Ahead of a scheduled event (a Federal Reserve decision, an inflation print) much of the priced move is concentrated in one or two sessions, and the flat daily conversion understates those days while overstating the quiet ones.
- **Returns have fat tails.** Real return distributions put more weight on extreme days than the bell curve allows; no single-number scale conveys that. Section 6's clustering panel shows what the tails actually look like. (Mandelbrot 1963)

Used with those caveats, the rule of 16 is the single fastest way to translate every volatility number you will ever see.

## 3 Realized volatility: measuring what happened

### 3.1 The close-to-close estimator, step by step

*Realized volatility* (RV) — also called historical volatility — is the standard deviation of actual past returns, annualized. It is a measurement, backward-looking by construction: it tells you what the market *did*, over a window you must choose and should always state. The workhorse version, the *close-to-close estimator*, uses only daily closing prices and is exactly the four steps of Section 2.1 plus the √252 bridge. Here it is on real data, with nothing omitted: the twenty-one S&P 500 sessions from 2026-08-19 to 2026-09-17 (one trading month; the return of the first day is computed against the 2026-08-18 close of 7,691.76).

| Day | Date | Close | Return (%) | Return − mean | Squared deviation |
|---|---|---|---|---|---|
| 1 | 2026-08-19 | 7,707.98 | +0.211 | +0.243 | 0.0589 |
| 2 | 2026-08-20 | 7,641.16 | −0.867 | −0.835 | 0.6974 |
| 3 | 2026-08-21 | 7,674.37 | +0.435 | +0.466 | 0.2175 |
| 4 | 2026-08-24 | 7,652.86 | −0.280 | −0.249 | 0.0618 |
| 5 | 2026-08-25 | 7,677.28 | +0.319 | +0.351 | 0.1231 |
| 6 | 2026-08-26 | 7,675.70 | −0.021 | +0.011 | 0.0001 |
| 7 | 2026-08-27 | 7,730.99 | +0.720 | +0.752 | 0.5657 |
| 8 | 2026-08-28 | 7,711.76 | −0.249 | −0.217 | 0.0471 |
| 9 | 2026-08-31 | 7,686.14 | −0.332 | −0.300 | 0.0903 |
| 10 | 2026-09-01 | 7,631.47 | −0.711 | −0.679 | 0.4617 |
| 11 | 2026-09-02 | 7,666.60 | +0.460 | +0.492 | 0.2422 |
| 12 | 2026-09-03 | 7,747.71 | +1.058 | +1.090 | 1.1876 |
| 13 | 2026-09-04 | 7,718.60 | −0.376 | −0.344 | 0.1183 |
| 14 | 2026-09-08 | 7,673.52 | −0.584 | −0.552 | 0.3050 |
| 15 | 2026-09-09 | 7,636.36 | −0.484 | −0.452 | 0.2047 |
| 16 | 2026-09-10 | 7,591.70 | −0.585 | −0.553 | 0.3059 |
| 17 | 2026-09-11 | 7,656.98 | +0.860 | +0.892 | 0.7951 |
| 18 | 2026-09-14 | 7,619.98 | −0.483 | −0.451 | 0.2038 |
| 19 | 2026-09-15 | 7,585.73 | −0.449 | −0.418 | 0.1745 |
| 20 | 2026-09-16 | 7,551.81 | −0.447 | −0.415 | 0.1725 |
| 21 | 2026-09-17 | 7,637.76 | +1.138 | +1.170 | 1.3687 |

Now the four steps, using the table's own numbers:

1. **Average return.** The twenty-one returns sum to a mean of −0.032% — essentially zero, as is typical for a single month.
2. **Deviations and squares.** Column five is each return minus that mean; column six is each deviation squared. The squared deviations sum to 7.4017.
3. **Variance and daily volatility.** The variance is the average squared deviation: 7.4017 ÷ 21 = 0.3525. Its square root, 0.594% per day, is the daily volatility.
4. **Annualize.** Multiply by √252 = 15.87: the 21-day realized volatility is 0.594 × 15.87 ≈ **9.4% annualized**.

That is the whole computation — a spreadsheet with six columns. One instructive detail sits in plain view: the single largest squared deviation, the +1.138% session of 2026-09-17, contributes 1.3687 of the 7.4017 total — nearly a fifth of the entire month's measured variance from one day. Squaring makes volatility a story about the few large days, which is exactly why the clustering of large days (Section 6.1) matters so much.

![Twenty-one S&P 500 daily returns, 2026-08-19 to 2026-09-17 (Yahoo daily ^GSPC closes), the same sessions as the worksheet table. Dashed lines mark the mean return ± one daily standard deviation of 0.59%; annualized, the window's realized volatility is 9.4%. Reproduce with figures/fig_rv_walkthrough.py.](figures/fig_rv_walkthrough.png)

### 3.2 What the number does and does not say

Three conventions hide inside "RV = 9.4%," and stating them is the difference between a number and a measurement:

- **The window is an assumption, not a fact.** Twenty-one trading days (a month) is the common default; a 5-day RV is far jumpier, a 63-day (quarterly) RV far smoother. None is "correct" — they answer different questions — but any RV quoted without its window is meaningless. Always say "21-day RV," not "the RV."
- **Small conventions barely matter; the window dominates.** Dividing the squared deviations by 20 instead of 21 (the statistician's *sample* convention) turns 9.42% into 9.65%; skipping the mean-subtraction entirely (a common practitioner shortcut, defensible because daily means are tiny) gives 9.44%. Both effects are dwarfed by moving the window a week. Pick conventions, state them, and stop worrying about them.
- **Level needs context.** Is 9.4% quiet or loud? Against the last fifteen years of the same index — where the median 21-day RV was 11.8% and the extremes ran from 3.4% to 94.5% (Section 6.2) — it is a quieter-than-usual month. An RV level only becomes information next to its own history.

### 3.3 Why intraday ranges matter: Parkinson and Garman–Klass, in intuition only

The close-to-close estimator has one blind spot: it sees a single snapshot per day. Consider a session that rallies 2% by lunch and closes exactly flat. Close-to-close records a 0% return — a perfectly calm day — while anyone watching lived through real turbulence. The information about that journey exists in the day's *high* and *low*, and a family of estimators is built to harvest it. The *Parkinson estimator* uses the daily high-low range: a wide range means a volatile day even if the close round-trips. The *Garman–Klass estimator* refines this by combining the range with the open and close, extracting still more from the same day. (Parkinson 1980; Garman & Klass 1980)

The intuition for why they help: each daily range is like measuring a river's width at several points instead of one, so range-based estimators reach a given precision from *fewer days* of data — which lets you use shorter windows without drowning in noise. Their blind spot is the mirror image of their strength: they see only the session and miss *overnight gaps* (a market that closes at 100 and opens at 97 had a violent night that no intraday range records), and pure close-to-close captures exactly those. Practitioners therefore treat the two families as complements. For this paper's purposes the close-to-close estimator, honestly windowed, is entirely sufficient — but when you later meet "Parkinson volatility" in a tool, you now know it is the same quantity measured through a wider aperture, not a different concept.

## 4 Implied volatility: the market's priced-in uncertainty

### 4.1 Backing volatility out of an option price

To define implied volatility we need options, in three sentences. An *option* is a tradable contract on an underlying asset: a *call option* is the right (not the obligation) to buy the underlying at a fixed *strike price* on or before an *expiration* date, and a *put option* the right to sell at the strike; the price paid for this right is the *premium*. A put on a stock index is functionally an insurance policy on the market — it pays when the market falls below the strike — and, like any insurance, its premium depends on how dangerous the insured period looks: the shakier the road, the more the policy costs. A contract whose strike sits at the current index level is called *at-the-money* (ATM); strikes away from the current level are *out-of-the-money* (OTM).

Pricing models — the famous one is the *Black–Scholes model* — connect a premium to its ingredients: the underlying's price, the strike, the time to expiration, interest rates, and one number describing how much the underlying is expected to move — a volatility. (Hull 2021) Here is the key inversion, and it needs no formula. Of those ingredients, every one is publicly observable *except* the volatility. But the premium itself is also observable — options trade all day. So run the machine backwards: **find the volatility number that makes the model's price equal the market's price.** That number is the *implied volatility* (IV) of the option. It is "implied" in the literal sense: nobody typed it in; it is reverse-engineered from what buyers and sellers actually paid. When a trader says "that option trades at 18 vol," they mean: the premium changing hands is consistent with the market pricing 18% annualized volatility over the option's life.

### 4.2 IV is a price, RV is an outcome

Set the two concepts side by side, because the entire volatility field lives in the space between them:

| | Realized volatility (RV) | Implied volatility (IV) |
|---|---|---|
| **Direction of view** | backward — what happened | forward — what is being priced |
| **Source** | the underlying's price history | traded option premiums |
| **Nature** | a measurement, a statistic | a price — what insurance costs now |
| **Changes because…** | prices moved | supply and demand for options shifted |

The compact version worth memorizing: *IV is the price, RV is the result.* IV is what the market charges today for exposure to future movement; RV is what the movement subsequently turned out to be. An insurance analogy carries the full weight: IV is this year's premium on the policy, RV is what the roads actually did. The premium is set in advance by a market — it reflects expectations, but also the sellers' need to be compensated and the buyers' urgency — and the outcome settles later. Neither number is "wrong" when they differ, any more than your car insurance premium was "wrong" in a year you had no accident.

### 4.3 The gap between them: a first look at the variance risk premium

Once both numbers exist, the obvious move is to compare them — and the comparison has a famous, persistent shape: **on equity indices, implied volatility sits above subsequently realized volatility most of the time.** The average gap is called the *variance risk premium* (VRP), and it is one of the best-documented regularities in derivatives markets. (Carr & Wu 2009) The economic reading is exactly the insurance reading: sellers of index options carry a risk that explodes precisely in the worst states of the world (Section 6.3), and they charge an ongoing premium for carrying it — so market insurance, like most insurance, costs more than an actuarially fair rate, most of the time. In the occasional crisis the relationship flips violently and realized volatility overwhelms what was priced; those episodes are when the insurance pays out.

One live illustration from this paper's own data, with the direction check made explicit: on 2026-09-16 the VIX closed at 17.71 — pricing roughly 17.7% annualized volatility for the coming month — while the trailing 21-day realized volatility computed in Section 3.1 was 9.4%. Priced volatility stood some eight points *above* freshly measured volatility, which is the direction the VRP claim predicts (IV above RV, not below). One day proves nothing on its own; the systematic version of this comparison, run over 3,770 days, is Section 7.4 — and the premium will be visible there as a hit rate. The full treatment of the VRP — how large it is, when it inverts, and what harvesting it costs in crashes — is the subject of the volatility-modeling paper.

## 5 The VIX, demystified

### 5.1 What the VIX aggregates

The *VIX* — formally the Cboe Volatility Index — is a single number answering a single question: **what does thirty days of S&P 500 insurance cost right now, expressed as an annualized volatility?** Mechanically, the index does not come from one option but from a whole strip of them: it aggregates the live prices of a wide range of out-of-the-money SPX puts and calls across two expirations bracketing the 30-day mark, and interpolates to a constant 30-day horizon. (Cboe Global Markets, methodology; Whaley 2009) Two properties of this construction matter even at an introductory level. First, it is *model-free*: the formula converts option prices directly into an implied variance without assuming Black–Scholes, so the VIX is not hostage to one model's assumptions. Second, because the strip spans many strikes — including deep downside puts — the VIX automatically absorbs the market's pricing of crash protection, not merely at-the-money uncertainty. It is quoted in annualized percentage points: VIX 17.71 means the strip prices about 17.71% annualized volatility, or about 1.1% per day by the rule of 16.

### 5.2 Reading the level: what 12, 16, 20, 30, 40 have historically meant

A VIX level means little in isolation and a great deal against its own history. Figure 2 shows every daily close since 1990 — 9,275 observations — with the conventional practitioner bands drawn in; the base rates below are computed from that same data.

![Daily VIX closes from FRED, series VIXCLS, 1990-01-02 to 2026-09-16, 9,275 observations, with the practitioner bands 12/16/20/30/40 shaded. Labeled peaks: LTCM/Russia 1998 at 45.7, the post-9/11 reopening at 43.7, the 2002 dot-com bear at 45.1, Lehman 2008 at 80.9, the 2011 US downgrade at 48.0, the 2015 China devaluation at 40.7, Volmageddon 2018 at 37.3, COVID-19 2020 at 82.7 — the all-time closing high, the 2024 yen-carry unwind at 38.6, and the 2025 tariff shock at 52.3. Reproduce with figures/fig_vix_history.py.](figures/fig_vix_history.png)

| Band | Share of days since 1990 | Historical character |
|---|---|---|
| below 12 | 8.6% | deep calm — grinding bull markets (2005–06, 2017); the all-time closing low is 9.14 (2017-11-03) |
| 12–16 | 30.3% | ordinary calm — the single most common state |
| 16–20 | 24.1% | normal — the long-run median close is 17.58 |
| 20–30 | 29.1% | elevated — corrections, macro uncertainty, bear-market grind |
| 30–40 | 5.7% | stress — genuine risk-off episodes |
| 40 and above | 2.2% | crisis — 1998, 2001–02, 2008, 2011, 2020, 2025 |

Three observations turn this table into usable intuition. First, **the teens are home**: 63% of all days closed below 20, so "VIX under 20" is not news, it is the resting state. Second, **the extremes are rare and brief**: only one day in twelve closed below 12, and barely one in fifty at 40 or above — the 2008 and 2020 panics that dominate memory (closing peaks 80.86 and 82.69) occupy a sliver of actual time. Third, **the bands are base rates, not signals**: VIX 25 does not "mean sell" any more than VIX 13 means safe — Section 6.2 shows that both calm and stress persist far longer than newcomers expect, and Section 8.2 shows why level alone is never a trade. What the bands do give you is a calibrated first reaction: at 17 you are looking at an unremarkable market; at 33 you are in the worst 4% of days since 1990 and should expect 2%-a-day swings as the local normal.

### 5.3 A price, not a forecast

Here is the single most important sentence in this paper: **the VIX is a price, not a forecast.** It is the going rate for thirty days of index insurance, set by supply and demand — not the output of a forecasting model, and not a prophecy. Three consequences follow, and each corrects a common misreading:

- **It embeds a premium.** Because it is built from premiums that sellers must be paid to write, the VIX runs persistently above the volatility that subsequently materializes (Section 4.3, Section 7.4). Treating it as an unbiased prediction guarantees systematic surprise in one direction.
- **It moves with demand, not only with "information."** When institutions rush to buy protection, the VIX rises because premiums rose — whether or not anyone's actual forecast of volatility changed. A price can spike on positioning alone; a forecast cannot.
- **It looks backward more than its reputation suggests.** The VIX tracks recent realized volatility closely — compare Figure 2 with the RV panel of Figure 3, which spike and fade together — so much of any day's VIX level is a rear-view mirror of the volatility just experienced, marked up by the premium.

None of this makes the VIX useless — quite the opposite: prices aggregate information and positioning in ways no single forecaster can, and the rest of this paper leans on the VIX heavily. It makes the VIX a *price*, to be read the way one reads any price: as what the market currently charges, premium included, not as what the market "knows will happen."

### 5.4 Siblings: VXN and VVIX

The *VXN* applies the identical 30-day methodology to the Nasdaq-100 instead of the S&P 500. Because the Nasdaq-100 is narrower and dominated by a handful of large technology names, its volatility — and therefore the VXN — typically runs a few points above the VIX; the two move together, and their *spread* is a quick read on whether stress is broad-based or concentrated in tech. For anyone trading Nasdaq instruments, the VXN, not the VIX, is the right input for the expected-move arithmetic of Section 7 — the mechanics are identical, only the index changes.

The *VVIX* goes one level up: it is the implied volatility *of the VIX itself*, computed from options on the VIX — the market's priced uncertainty about where insurance prices are headed, often called *vol-of-vol*. It rises when demand concentrates in crash hedges (VIX calls), and it can stir while the VIX itself is still quiet — which is why practitioners watch it as an early-warning complement rather than an echo. Both indices, and the richer structure around them (the VIX term structure, VIX9D/VIX3M, skew), are treated properly in the volatility-surface paper; here it is enough to know they exist and what question each answers.

## 6 How volatility behaves

If volatility were an unpredictable constant-of-the-day, most of this track would end here. It is not: volatility has strong, well-documented habits — three of them, each visible to the naked eye in fifteen years of free data (Figure 3), and each with a direct practical consequence.

![Three behaviors of volatility on about fifteen years of free data — Yahoo daily ^GSPC 2011-09-20 to 2026-09-17, 3,770 returns; VIX from FRED, 3,768 overlapping days. Panel a: absolute daily returns cluster in time. Panel b: rolling 21-day realized volatility swings between calm regimes near 3–10% and stress regimes above 30%, peaking at 95% in April 2020, median 11.8%. Panel c: daily S&P 500 return against the same-day VIX change; correlation −0.80. Reproduce with figures/fig_vol_behavior.py.](figures/fig_vol_behavior.png)

### 6.1 Clustering: big days come in groups

Mandelbrot put it in one sentence in 1963: *"large changes tend to be followed by large changes, of either sign, and small changes tend to be followed by small changes."* (Mandelbrot 1963) That is *volatility clustering*, and panel (a) shows it without statistics: the spikes of the absolute-return series bunch into episodes — 2011, late 2018, the 2020 pandemic, the 2022 bear, 2025 — separated by long flat stretches.

The numbers behind the picture make the point precise. Over these 3,770 sessions, the correlation between one day's return and the next day's return is −0.11 — essentially nothing exploitable; the market's *direction* tomorrow is close to a coin flip. But the correlation between one day's *size* of move and the next day's size is +0.34 — solidly positive. Sharper still: after the 204 days in the sample where the index moved more than 2% in either direction, the *next* day's average absolute move was 1.49%, against an unconditional average of 0.71% — more than double. The practical consequence is the founding insight of volatility research: **the size of moves is forecastable in a way the direction is not.** Today's turbulence is genuine information about tomorrow's turbulence — which is why RV appears on the right-hand side of every serious volatility forecast, and why a trader who sizes positions off recent volatility is not being superstitious but statistical.

### 6.2 Mean reversion and regimes: calm is long, stress is sharp

Volatility wanders, but it wanders home. Panel (b) — rolling 21-day realized volatility — shows the shape: a median of 11.8%, long unhurried stretches below it, and occasional violent departures that decay back over weeks to months rather than staying. The extremes of the sample are instructive: a low of 3.4% (October 2017, one of the calmest markets ever recorded) and a high of 94.5% (April 2020) — a factor of nearly thirty between the quietest and loudest readings *of the same index*. Yet extremes do not persist: RV spent 34.3% of all days below 10%, and only 2.7% of days above 30%; in the VIX's longer history, only 2.2% of days closed at 40 or above (Section 5.2). Volatility is *mean-reverting*: high readings predict lower readings ahead, low readings predict (eventually) higher — with the crucial asymmetry that spikes arrive in days and drain away in months, while calm builds slowly and lingers.

This produces the most consequential concept of the section: volatility *regimes*. Markets spend their time in extended states — calm regimes of single-digit RV and grinding price action, stress regimes of 30%+ RV and multi-percent daily swings — with fast, cliff-edge transitions between them. And **strategies do not travel across regimes**. A system tuned in calm — tight stops sized for 0.5% days, selling premium for steady income, buying every dip — meets a stress regime as a different planet: the "normal" daily range quintuples, stops sized for calm are noise-triggered at machine-gun rate, and short-premium income strategies concentrate a year of gains into a week of losses. The reverse holds too: crisis-calibrated caution bleeds slowly in a calm regime it never trusts. The lesson here is not any particular fix but the diagnostic reflex: before judging any strategy or signal, ask *which volatility regime is this, and which regime was the strategy built in?* Much of what looks like a broken edge is an unchanged edge meeting a changed regime.

### 6.3 The leverage effect: prices down, volatility up

The third habit couples volatility to direction — the one place the two meet. Panel (c) plots each day's S&P 500 return against the same day's *change* in the VIX: the cloud slopes hard down-right, with a correlation of **−0.80**. When the index falls, implied volatility jumps; when the index rallies, volatility bleeds lower. The relationship is also visibly asymmetric in the cloud's tails: the largest VIX explosions (+10 to +25 points in a day) sit almost exclusively over the worst return days, while even the strongest rally days produce only modest VIX declines — fear arrives in jumps, calm returns on foot.

The traditional name, *leverage effect*, comes from Black's 1976 explanation: a falling stock price raises a firm's debt-to-equity ratio, making the equity mechanically riskier. (Black 1976) The modern reading adds a demand channel that likely matters more for indices: falling markets trigger urgent buying of protection (puts), which bids up premiums and therefore implied volatility — the insurance-price channel of Section 5.3 operating in real time. Whatever the mix of causes, the consequences are immediate even at an introductory level: protection is most expensive precisely when it is most wanted (buying puts *after* the drop means paying crisis premiums); anything short volatility is implicitly long the market, and anything long volatility is implicitly short it — there is no such thing as a direction-neutral volatility position over a crash; and volatility exposure is one of the few things that reliably pays off in equity disasters, which is exactly why its insurance carries the standing premium of Section 4.3. The three habits of this section are one story told three ways: markets alternate between long calm and sharp fear, fear clusters, and fear is priced — dearly — the moment prices fall.

## 7 Expected move and σ-ladders

### 7.1 From implied volatility to the expected move

Everything so far becomes operational in one construction. The *expected move* (EM) is the one-standard-deviation price change implied by current option prices over a stated horizon — the market's own "±1σ" band, in index points. For a single day, take the annualized IV (for the S&P 500, simply the VIX) back across the √252 bridge and scale by the index level:

daily EM = index level × (VIX ÷ 100) ÷ √252 — or, mentally, level × VIX% ÷ 16.

Real numbers, from the data used throughout: on 2026-09-16 the S&P 500 closed at 7,551.81 with the VIX at 17.71. Daily σ = 17.71 ÷ 15.87 = 1.116%, so the daily EM was 7,551.81 × 1.116% ≈ **84 points**, and the implied ±1σ band for the next session ran from roughly 7,468 to 7,636. For longer horizons, scale by the square root of time exactly as in Section 2.2: a week (5 sessions) is √5 ≈ 2.24 daily EMs, a month about 4.6.

There is a second, purely market-based route that needs no formula at all. A *straddle* is a call and a put bought together at the same at-the-money strike and expiration; its owner profits if the index moves — either way — by more than the combined premium. That makes the ATM straddle's price the market's *breakeven move*: pay it, and you need the index to travel at least that far by expiration to win. To a good approximation, the straddle price *is* the expected absolute move the market is pricing for that horizon, read directly off the option chain. (Sinclair 2013) The two routes are consistent: under a bell curve the average absolute move is about 0.8σ (Section 2.3), so the 1σ EM is roughly the ATM straddle price ÷ 0.8 — a useful cross-check when you have an option chain in front of you, and the reason practitioner "expected move" numbers from straddles come out slightly below the 1σ band computed from IV.

### 7.2 Building a σ-ladder

A single band is useful; a *σ-ladder* — the same EM laid out at fractional multiples around the reference price — turns it into a map. Using the real 2026-09-16 numbers (close 7,551.81, daily EM 84.2 points):

| Rung | Distance | Downside | Upside | Reading |
|---|---|---|---|---|
| ±0.25σ | 21 pts | 7,531 | 7,573 | noise — ordinary intraday drift |
| ±0.50σ | 42 pts | 7,510 | 7,594 | a directional session, still unremarkable |
| ±1.0σ | 84 pts | 7,468 | 7,636 | the day's implied boundary — ~68% naive coverage |
| ±2.0σ | 168 pts | 7,384 | 7,720 | an exceptional day — a few times a year at this VIX |

The ladder's purpose is to convert every price you see during a session into *volatility units*. "Down 40 points" is ambiguous; "down 0.5σ" is calibrated — the same statement at VIX 18 and at VIX 35 refers to a very different number of points, and the ladder does that conversion once, before the session, when judgment is cheap. In this author's own pre-session process the day's ladder (computed exactly as above, from the relevant volatility index) is the first thing on the sheet each morning: it anchors "is this move ordinary or is something happening?" to arithmetic rather than adrenaline, and distances to any level of interest are stated in σ units rather than points. The same ladder logic scales to a week by multiplying the daily EM by √5.

### 7.3 A worked example, honestly scored

A band is a claim, and claims get scored. The EM above was computed entirely from information available at the 2026-09-16 close — index 7,551.81, VIX 17.71, band 7,468 to 7,636. The next session, 2026-09-17, the S&P 500 closed at 7,637.76: a move of +85.9 points, or +1.138%, against an implied 1σ of 84.2 points. The realized move was **1.02σ — outside the band by 1.7 points**.

Scored honestly: the band failed, barely. And the failure is the instructive part. First, this is what a 1σ boundary *means* — even a perfectly calibrated band is pierced roughly one day in three; a band that never breaks is a band drawn uselessly wide. Second, the miss was a rally: bands break upward too, which surprises anyone who has quietly equated volatility with downside (Section 2.1). Third, and most important: one day is an anecdote. The honest question is not whether yesterday's band held but how often such bands hold across many days — and that question was settled in advance to be the next section's test, before this particular day's outcome was known.

### 7.4 Fifteen years of bands: the premium made visible

The test is pre-committed and has no free parameters: for every one of 3,770 days from 2011 to 2026, compute the daily EM exactly as in Section 7.1 from that day's close and VIX, then check whether the *next* session's absolute close-to-close move stayed inside ±1 EM. If the VIX were an unbiased volatility forecast and daily returns bell-shaped, about 68.3% of days should land inside. The result: **81.4% of days stayed inside the ±1σ band.** At ±2 EM the count is 98.3% inside, against a naive 95.4%.

![Rolling one-year share of sessions whose absolute next-day move stayed inside the VIX-implied ±1σ expected move, on 3,770 days of free data, 2011 to 2026 — Yahoo ^GSPC and FRED VIXCLS. The overall average is 81.4% against the naive normal expectation of 68.3%; the rolling share ranges from 68.7% in December 2022 to 92.5% in November 2021. One pre-committed rule, no tuning, reported as-is. Reproduce with figures/fig_expected_move.py.](figures/fig_expected_move.png)

The direction check first: over-coverage (81% > 68%) means the priced band was systematically *wider* than what the market subsequently did — implied volatility above realized volatility. That is the same direction as Section 4.3's single-day illustration and the VRP literature, so the pieces agree; had the share come in *below* 68%, it would have contradicted the premium claim and this section would say so. One caveat sizes the claim honestly, though: 68.3% is the *normal* benchmark, and daily returns are fat-tailed, so even a fairly priced band sits above it — a standardized Student-t with four degrees of freedom already lands 77.0% inside its ±1σ band, one with five degrees of freedom 74.7%. Measured against that leptokurtic baseline the premium's contribution is the excess over roughly 75%, not the full thirteen-point excess over 68%; a large part of the visible over-coverage is kurtosis, not premium. What the figure adds is texture: the rolling one-year share never fell below 68.7% (reached in December 2022, at the end of a grinding bear market — the one period where the VIX band was merely fair rather than generous) and stretched to 92.5% in the placid markets of late 2021, where the VIX overpriced daily movement spectacularly.

Three honest limits before anyone trades this. The test scores *close-to-close* moves only — intraday excursions can pierce a band even when the close crawls back inside, so the band held less often than 81% as an intraday statement. It converts a *30-day* quote into a *1-day* band, inheriting the event-concentration caveat of Section 2.3. And over-coverage is not free money: it says short-volatility strategies were paid a standing premium, but Section 6's regime and leverage sections say exactly when that premium is clawed back — in fast, clustered, downside episodes. The band over-covers on ordinary days and is overwhelmed on the extraordinary ones; that asymmetry, not the 81%, is the deep fact. Quantifying it is the volatility-modeling paper's job.

## 8 First practical signals

### 8.1 IV rank and IV percentile

The recurring lesson of Section 5 and Section 7 is that a volatility level means little without its own history. Two standard normalizations operationalize this. *IV rank* (IVR) places today's IV inside its 52-week range:

IVR = (IV today − 52-week low) ÷ (52-week high − 52-week low) × 100.

If an index's IV has run between 12 and 40 over the past year and sits at 18 today, IVR = (18 − 12) ÷ (40 − 12) = 21 — today is in the lower fifth of its yearly range. *IV percentile* (IVP) asks a subtly different question: on what share of the past year's days was IV *below* today's level? The two can diverge sharply after a single spike: one week at IV 40 in an otherwise 12-to-18 year drags IVR down for months (the range's ceiling is now 40) while IVP barely notices — which is why IVP is the more robust habit and quoting both is better still. Either way, the normalization converts "IV is 18" into "IV is cheap/rich *relative to its own recent life*" — a first, genuinely useful filter that costs one subtraction and one division.

### 8.2 Why "high IV" alone is not a trade

The seductive syllogism runs: IV is high → options are expensive → sell them (or its mirror: IV is low → buy them). It fails as stated, for reasons this paper has already assembled:

- **High IV is usually high for a reason.** IVR 100 readings cluster in exactly the episodes of Figure 2's spikes — when realized volatility is *also* exploding (Section 6.2's 94.5% RV came with the VIX in the 80s). Selling "expensive" insurance during the fire is how option sellers get carried out; the question is never "is IV high?" but "is IV high *relative to the RV that is materializing*?" — the Section 4.3 comparison, not the Section 8.1 normalization.
- **Mean reversion has no clock.** Volatility reverts (Section 6.2), but low-IV regimes persisted for *years* in 2013–2017 while premium buyers bled, and elevated regimes ran for months in 2022. A normalized level says where you are, not when it ends.
- **The payoff is asymmetric.** A short-volatility position collects small premiums on the 81% of ordinary days and pays out large multiples on the clustered, down-market exceptions (Section 6.1, Section 6.3) — precisely the days when everything else in a typical portfolio is also losing. A high hit rate around a fat left tail is the classic shape of strategies that look brilliant until they don't.

The constructive version: IVR/IVP are *filters* that set context, to be combined — at minimum — with the current RV comparison (is the premium earned?), the regime label of Section 6.2, and, one level up, the volatility term structure of the volatility-surface paper. "High IV" is the beginning of a checklist, never its conclusion. This is also where this paper stops: turning that checklist into tested rules with hit rates and expectancies is what the backtesting paper exists to discipline.

## 9 Common misconceptions

- **"Volatility tells you the market's direction."** It measures dispersion and is sign-blind by construction (Section 2.1). Even the leverage effect (Section 6.3) is a correlation between *changes* in price and *changes* in IV, not a directional forecast from the level of either.
- **"VIX 20 means the market expects a 20% crash."** VIX 20 means options price about 20% *annualized* standard deviation — roughly 1.25% daily moves by the rule of 16 (Section 2.3). It is a scale for ordinary wiggles, not a crash probability.
- **"The VIX predicts volatility."** It is a *price* — premium-laden (81.4% inside a "68%" band, Section 7.4), demand-driven, and substantially a rear-view mirror of recent realized volatility (Section 5.3). Prices inform; they do not prophesy.
- **"When IV and RV differ, one of them is wrong."** The persistent gap is the variance risk premium — compensation to insurance sellers (Section 4.3) — not a mispricing waiting to be arbitraged away by a newcomer with a spreadsheet.
- **"About 68% of days stay inside the ±1σ expected move."** Empirically 81.4% did (Section 7.4), because daily returns are fat-tailed and the band is built from a premium-inflated price. Naive theory quotes 68%; measurement says otherwise — and neither number makes selling the band free money, because the misses cluster in the worst tapes.
- **"Low VIX means the market is safe" / "low VIX means a crash is imminent."** Both readings over-interpret a base rate. Calm is the most common state (63% of days below VIX 20, Section 5.2) and calm regimes persist (Section 6.2); depressed volatility is neither an all-clear nor a countdown timer.
- **"Realized volatility is *the* volatility of the market."** RV is an estimate over a chosen window with chosen conventions (Section 3.2); move the window and the number moves. Any RV without its window attached is an opinion dressed as a measurement.

## 10 Glossary

| Term | Meaning |
|---|---|
| Annualized volatility | Volatility rescaled to a one-year horizon; daily volatility × √252 (Section 2.2). |
| At-the-money (ATM) | An option whose strike is at (or nearest) the current price of the underlying. |
| ATM straddle | A call plus a put bought at the same at-the-money strike and expiration; its price approximates the market's expected absolute move (Section 7.1). |
| Backwardation | A volatility term structure with near-term volatility priced above longer-term — the stress shape (previewed in the volatility-surface paper). |
| Call option | The right, without obligation, to buy the underlying at the strike price until expiration. |
| Close-to-close estimator | Realized volatility computed from daily closing prices only (Section 3.1). |
| Contango | A volatility term structure with near-term below longer-term volatility — the calm, normal shape (previewed in the volatility-surface paper). |
| Correlation | A number between −1 and +1 measuring how two series move together; 0 is no linear relationship. |
| Deviation | A single observation minus the average of its series; the raw material of variance (Section 2.1). |
| Dispersion | How widely values are scattered around their average; what volatility measures (Section 2.1). |
| Expected move (EM) | The one-standard-deviation price change implied by option prices for a stated horizon, in points (Section 7.1). |
| Expiration | The date an option contract ceases to exist and is settled. |
| Fat tails | The property of return distributions that extreme outcomes occur far more often than a bell curve predicts (Section 2.3). |
| Garman–Klass estimator | A realized-volatility estimator using open, high, low, and close of each session (Section 3.3). |
| Implied volatility (IV) | The volatility number that makes an option-pricing model reproduce the option's traded market price (Section 4.1). |
| IV percentile (IVP) | The share of the past year's days on which IV was below today's level (Section 8.1). |
| IV rank (IVR) | Today's IV positioned inside its 52-week low-to-high range, from 0 to 100 (Section 8.1). |
| Leverage effect | The strong negative correlation between index returns and same-day changes in implied volatility (Section 6.3). |
| Mean reversion | The tendency of volatility to return toward its long-run typical level after departures (Section 6.2). |
| Normal distribution | The bell curve; the naive benchmark under which ±1σ contains about 68.3% of outcomes. |
| Option | A tradable contract conveying a right (not an obligation) on an underlying asset (Section 4.1). |
| Out-of-the-money (OTM) | An option whose strike is away from the current price on the side that makes immediate exercise worthless. |
| Parkinson estimator | A realized-volatility estimator built from each session's high-low range (Section 3.3). |
| Premium | The price paid for an option contract. |
| Put option | The right, without obligation, to sell the underlying at the strike price until expiration; index insurance (Section 4.1). |
| Realized volatility (RV) | The annualized standard deviation of actual past returns over a stated window; also historical volatility (Section 3.1). |
| Regime | An extended market state — calm or stress — with characteristic volatility; strategies rarely survive regime changes unchanged (Section 6.2). |
| Return | The percentage change of price between two dates, here close-to-close (Section 2.1). |
| Rule of 16 | Annualized volatility ÷ 16 ≈ daily volatility, because √252 ≈ 16 (Section 2.3). |
| Sigma (σ) | Shorthand for one standard deviation; "a 2σ day" is a move twice the daily standard deviation. |
| σ-ladder | The expected move laid out at fractional multiples (±0.25σ, ±0.5σ, ±1σ…) around a reference price (Section 7.2). |
| Skew | The pattern of different implied volatilities across strikes of the same expiration; index puts typically price richer than calls (previewed in the volatility-surface paper). |
| Standard deviation | The square root of variance; the standard measure of dispersion, in the same units as the data (Section 2.1). |
| Straddle | See ATM straddle. |
| Strike price | The fixed price at which an option's right to buy or sell applies. |
| Term structure | Implied volatility as a function of horizon (30 days, 3 months, …); its slope defines contango and backwardation (previewed in the volatility-surface paper). |
| Underlying | The asset an option refers to — here, an equity index. |
| Variance | The average of squared deviations; standard deviation squared (Section 2.1). |
| Variance risk premium (VRP) | The persistent average gap by which index implied volatility exceeds subsequently realized volatility (Section 4.3). |
| VIX | The Cboe Volatility Index: the 30-day implied volatility of the S&P 500, model-free, from a strip of OTM SPX options (Section 5.1). |
| Volatility | The dispersion of returns over a horizon, usually quoted as an annualized standard deviation (Section 2.1). |
| Volatility clustering | The tendency of large moves to follow large moves and small to follow small (Section 6.1). |
| Vol-of-vol | The volatility of volatility itself; what the VVIX prices (Section 5.4). |
| VVIX | The implied volatility of the VIX, computed from VIX options (Section 5.4). |
| VXN | The 30-day implied volatility index of the Nasdaq-100, constructed like the VIX (Section 5.4). |

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| 21-day S&P 500 realized volatility worked out by hand to 9.4% annualized | Own reproducible computation — `figures/fig_rv_walkthrough.py` |
| VIX base rates since 1990 — 63% of days below 20, median close 17.58, across 9,275 observations | Own reproducible computation — `figures/fig_vix_history.py` |
| Clustering, mean reversion, and the leverage effect (return vs same-day VIX-change correlation −0.80) on ~15 years | Own reproducible computation — `figures/fig_vol_behavior.py` |
| 81.4% of next-day moves stayed inside the VIX-implied ±1σ band versus a naive 68.3%, over 3,770 days | Own reproducible computation — `figures/fig_expected_move.py` |
| √252 annualization / square-root-of-time scaling as the quoted convention | Literature — (Hull 2021; Sinclair 2013) |
| The average absolute daily move is about 0.8 of a standard deviation under a normal distribution | Literature — (Sinclair 2013) |
| Index implied volatility sits above subsequently realized volatility on average (variance risk premium) | Literature — (Carr & Wu 2009) |
| The VIX is a model-free 30-day implied volatility from a strip of OTM SPX options | Literature — (Cboe methodology; Whaley 2009) |
| The leverage effect — falling prices raise volatility — and its debt-to-equity reading | Literature — (Black 1976) |
| Range estimators (Parkinson, Garman–Klass) extract volatility from the intraday high–low | Literature — (Parkinson 1980; Garman & Klass 1980) |
| IV rank / IV percentile as context filters, and why "high IV" alone is not a trade | Practitioner consensus — not independently verified |
| The σ-ladder as the pre-session anchor for reading moves in volatility units | Practitioner consensus — not independently verified |

## References

- Black, F. (1976). Studies of stock price volatility changes. *Proceedings of the 1976 Meetings of the American Statistical Association, Business and Economics Statistics Section*, 177–181.
- Carr, P., & Wu, L. (2009). Variance risk premiums. *The Review of Financial Studies, 22*(3), 1311–1341.
- Cboe Global Markets. *Volatility Index Methodology: Cboe Volatility Index.* Official methodology document: <https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf>.
- Garman, M. B., & Klass, M. J. (1980). On the estimation of security price volatilities from historical data. *The Journal of Business, 53*(1), 67–78.
- Hull, J. C. (2021). *Options, Futures, and Other Derivatives* (11th ed.). Harlow: Pearson.
- Mandelbrot, B. (1963). The variation of certain speculative prices. *The Journal of Business, 36*(4), 394–419.
- Parkinson, M. (1980). The extreme value method for estimating the variance of the rate of return. *The Journal of Business, 53*(1), 61–65.
- Sinclair, E. (2013). *Volatility Trading* (2nd ed.). Hoboken, NJ: Wiley.
- Whaley, R. E. (2009). Understanding the VIX. *The Journal of Portfolio Management, 35*(3), 98–105.

*All references above are publicly accessible: one is an official exchange methodology document (direct link given), five are peer-reviewed journal articles, one is a published conference-proceedings paper, and two are published books. No proprietary, course, or trading-academy material is cited.*
