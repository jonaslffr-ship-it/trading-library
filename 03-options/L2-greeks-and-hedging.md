---
title: "The Greeks — Sensitivities & Hedging"
last_updated: 2026-09-20
---

# The Greeks — Sensitivities & Hedging

## Abstract

An option price is a single number that depends on several moving parts — the underlying, time, volatility, and rates — and the *greeks* are simply the partial derivatives that say how much the price moves when each part moves by a little. This paper builds them from that one idea and treats them as the working vocabulary of a hedger rather than a table to memorize. We derive delta as a hedge ratio and dismantle the "delta equals probability of finishing in the money" folklore; show gamma as the error term a delta-hedge cannot avoid, and demonstrate on a simulation that a hedged option's profit is realized-minus-implied volatility times vega; read theta and gamma as the two sides of one trade; place vega across maturities and explain why the wings are a volatility instrument; give rho one honest page; and define the second-order flow trio — vanna, charm, volga — as tomorrow's *forced* delta adjustments. We aggregate greeks into a dealer's book, compute every greek from scratch in about forty lines of Python, and close with misconceptions and a glossary. Every figure is reproducible on free data; every worked number is printed by the accompanying code.

## Keywords

Delta, gamma, theta, vega, rho, vanna, charm, volga, vomma, Black–Scholes–Merton, delta hedging, gamma scalping, realized versus implied volatility, dollar greeks, dealer hedging, second-order greeks, hedge ratio, moneyness, option sensitivities

## 1 Introduction

### 1.1 Motivation and thesis

An option is a bet whose value changes for at least four different reasons at once: the underlying moves, a day passes, the market's estimate of future volatility shifts, and — more slowly — interest rates change. A trader who holds options and thinks only about the first of these is not hedged; they are exposed to three risks they have not named. The *greeks* are the names. Each one answers a single question of the form *"if this input changes by a small amount and everything else is held still, how much does my option's value change?"* — which is exactly the definition of a partial derivative.

The thesis of this paper is that the greeks are best understood not as formulae to be looked up but as a *hedger's error accounting*. A hedge is a promise to neutralize one risk; every greek beyond the one you hedged is the part of the promise you cannot keep. Delta is the hedge you take on first; gamma is the reason that hedge decays and must be repaired; theta is what you pay (or earn) for holding the position through time; vega is your exposure to the one input nobody can observe directly; and the second-order greeks — vanna, charm, volga — are the map of *how tomorrow's hedge will differ from today's*, before the underlying has moved at all. Read this way, the greeks stop being a glossary and become a single connected story about what it costs to carry optionality. That story is also the foundation for the dealer-flow material in the dealer-flows-and-GEX paper: a market maker who has sold options to the street inherits the mirror image of every greek discussed here, and the mechanical hedging those greeks force is what moves index markets around expiry.

### 1.2 Scope, prerequisites, and intended reader

This paper sits in the Trading Library's *Options* track. It assumes the options-fundamentals paper (*calls and puts, payoff diagrams, moneyness, intrinsic versus extrinsic value, put–call parity*) and the basic volatility vocabulary from the volatility-fundamentals paper (implied versus realized volatility, and that implied volatility is an annualized standard deviation quoted in "vol points"). It assumes comfort with a first partial derivative and a short Python snippet; it assumes no stochastic calculus and does not derive the Black–Scholes–Merton equation, only uses its closed forms.

After reading this paper, a reader can:

- state each greek as a partial derivative in one sentence and in words, and give its sign and rough magnitude for a call and a put across moneyness and maturity;
- delta-hedge a position and explain, with numbers, why the hedge leaks — turning gamma from a symbol into the specific dollar error a discrete hedge leaves behind;
- decompose the profit of a delta-hedged option into the part that is realized-minus-implied volatility and the part that is path-and-discretization noise, and read gamma scalping as that trade;
- read theta and gamma as one trade seen from two directions, and price the weekend and event decay a calendar-day theta implies;
- locate vega across the maturity spectrum, explain why a book of long-dated options is really a book of volatility, and see the bridge to the volatility-surface paper;
- define vanna, charm, and volga, read their sign maps by moneyness, and explain why a hedger treats them as *pre-scheduled* future trades;
- aggregate greeks across strikes and expiries into dollar-greeks and read a dealer's one-line book summary;
- and reproduce every number in this paper from free data with the accompanying code.

### 1.3 Data and reproducibility

All figures and every printed number use freely available data or a self-contained model computation: daily S&P 500 closes from the Yahoo chart API and the CBOE VIX index (FRED series VIXCLS, with a Yahoo fallback), both cached alongside the code so the figures rebuild offline. The remaining figures are didactic Black–Scholes–Merton computations that need no market data at all. Each figure names its inputs and is reproducible from the script cited in its caption. Where a convention could go two ways — per-point versus per-unit vega, per-calendar-day versus per-trading-day theta — the choice is stated explicitly, because a greek quoted without its units is not a number. *This is a research and educational document, not investment advice.*

### 1.4 Organization of this paper

This paper is complete: every section below is written in full, and there are no forthcoming stubs. The arc is a single argument built one greek at a time.

- **Section 2 Why the greeks exist** — the option price as a function of several inputs; sensitivities as partial derivatives, said in words first; Black–Scholes–Merton as the map, with its assumptions listed and honestly flagged as wrong-but-useful.
- **Section 3 Delta** — the hedge ratio and share-equivalent exposure; delta across moneyness and time (Figure 1); a full five-rebalance delta-hedge of a short call on one real month (Figure 2); and why "delta ≈ probability of finishing in the money" is a useful lie and when it misleads.
- **Section 4 Gamma** — convexity as the hedger's unavoidable error term; long versus short gamma P&L; gamma scalping with numbers; realized-versus-implied volatility as the true P&L driver (Figure 3); and gamma's concentration near the money and expiry, the seed of the flow story.
- **Section 5 Theta** — decay profiles across moneyness; theta and gamma as two sides of one trade; and the practical accounting of event and weekend decay.
- **Section 6 Vega** — exposure to implied volatility; vega across maturities; why the wings are a volatility instrument; and the bridge to the volatility-surface paper.
- **Section 7 Rho** — one honest page: negligible intraday, and relevant again in the post-2022 rate regime.
- **Section 8 Second-order greeks (the flow trio)** — vanna, charm, and volga defined; their sign maps by moneyness (Figure 4); and why a hedger reads them as tomorrow's forced delta adjustments.
- **Section 9 Portfolio aggregation** — summing greeks across strikes and expiries; dollar-greeks; and what a dealer's book summary looks like.
- **Section 10 Worked examples in Python** — all the greeks from scratch in about forty lines, printed in the body; a greek surface across strike and time (Figure 5); and a note that every chart rebuilds from free data.
- **Section 11 Common misconceptions and glossary**, followed by the references.

## 2 Why the greeks exist

Before naming a single greek, it is worth being exact about what kind of object we are differentiating and why the derivatives are the right thing to look at.

### 2.1 The price is a function of several inputs

The value of a European option is a function of a handful of inputs:

V = f(S, t, σ, r)

— the underlying price S, the current time t (equivalently the time-to-expiry T), the volatility σ the market is pricing in, and the risk-free rate r, with the strike K and any dividend or carry q held as fixed parameters of the contract. Said in words: the price of an option is a surface that sits over the space of "where the underlying is, how much time is left, how jumpy the market thinks the future is, and what cash costs." The greeks are the *slopes* of that surface in each direction.

The reason slopes matter more than the price itself is that a trader almost never cares about the level of an option's value in isolation; they care about how that value will *change* when the world moves a little between now and their next decision. A first-order Taylor expansion of the price around today's inputs makes this explicit (Hull 2022):

dV ≈ (∂V/∂S) dS + (∂V/∂t) dt + (∂V/∂σ) dσ + (∂V/∂r) dr + ½ (∂²V/∂S²) dS² + …

Every greek is one term in this expansion. Delta (Δ = ∂V/∂S) multiplies the move in the underlying, theta (Θ = ∂V/∂t) the passage of time, vega (∂V/∂σ) the change in volatility, rho (ρ = ∂V/∂r) the change in rates. Gamma (Γ = ∂²V/∂S²) is the leading *second-order* term — it multiplies the *square* of the underlying move, which is why it never disappears no matter how well you hedge the first-order part, and why it is where most of the interesting behavior lives. The whole of greek-based risk management is the discipline of reading this expansion: neutralize the terms you do not want to bet on, and know precisely which terms you are still exposed to.

> **Greeks are a language for "what happens next," not "what is it worth."** The market gives you the price. The greeks are your own translation of that price into the sentence *"if the underlying moves a point, if a day passes, if implied vol ticks up, here is what I make or lose."* A position is only understood once that sentence is written down.

### 2.2 Black–Scholes–Merton as the map

To turn those partial derivatives into concrete numbers you need a formula for V, and the standard one is the Black–Scholes–Merton (BSM) model (Black & Scholes 1973; Merton 1973). For a European call with continuous carry q,

C = S · exp(−qT) · N(d₁) − K · exp(−rT) · N(d₂),  where  d₁, d₂ = [ ln(S/K) + (r − q ± ½σ²) T ] / (σ√T),

and N(·) is the standard normal cumulative distribution function. The greeks are then just the partial derivatives of this expression, and because the formula is closed-form, so are they — every number in this paper's model figures comes from differentiating this one equation and evaluating it, with no numerical fitting.

It is important to be honest about what this map gets wrong. BSM assumes, among other things, that the underlying follows a geometric Brownian motion with *constant* volatility, that trading is continuous and frictionless, that the underlying pays a known continuous dividend, and that returns are log-normally distributed with no jumps (Hull 2022; Sinclair 2010). Every one of these assumptions is false in a real market: volatility is stochastic and clusters, markets gap, liquidity is finite, and the return distribution has fat tails and a persistent skew. If the assumptions were even approximately complete, a single implied volatility would price every strike — and the existence of the *volatility smile*, the fact that different strikes trade at different implied vols, is the market's own admission that the model is wrong (Natenberg 1994).

And yet the greeks computed from this "wrong" model are the industry's working language, for a reason worth stating precisely: BSM is used not as a theory of the true price but as a *quoting and translation device*. Traders take the observed market price of each option, invert the formula to find the implied volatility that reproduces that price, and then use the model's greeks *at that implied vol* to translate between price and risk. The model is wrong about the level of volatility — so the market supplies the volatility, one number per strike — but its sensitivities are a stable, shared, well-understood coordinate system for talking about risk. That is the sense in which BSM is *wrong but useful*: it is a bad forecaster and an excellent ruler. Throughout this paper we use it as a ruler, quote every model input, and flag the places where its wrongness would actually mislead a hedger — most sharply in Section 8, where the constant-volatility assumption directly understates the second-order flow greeks.

## 3 Delta

Delta is the first greek every trader meets and the one they most often half-understand. It is the slope of the option's value in the underlying — but its real job is as a *hedge ratio*, and its most famous interpretation is a lie that is useful right up until it isn't.

### 3.1 Delta as a hedge ratio and as share-equivalent exposure

Formally, delta is the partial derivative of the option value with respect to the underlying:

Δ = ∂V/∂S.

Under BSM, a call's delta is exp(−qT)·N(d₁) and a put's is exp(−qT)·(N(d₁) − 1), so a call delta runs from 0 to about +1 and a put delta from about −1 to 0. In words: delta tells you how many dollars the option's value changes for a one-dollar change in the underlying. A call with delta 0.45 gains roughly 45 cents when the underlying rises a dollar; a put with delta −0.30 loses 30 cents on that same up-move.

The operational reading is the *share-equivalent exposure*. An option with delta 0.45 on a contract covering 100 shares behaves, for small moves, like being long 45 shares of the underlying. This is what makes delta a hedge ratio: to neutralize the directional risk of that option you short 45 shares (or the futures equivalent), and the combined position has, momentarily, zero delta. "Momentarily" is doing enormous work in that sentence, and undoing it is the entire subject of Section 4. A *delta-neutral* book is one whose greeks sum to roughly zero delta — it is not directionally flat forever, only flat for the next small move, at this instant.

### 3.2 Delta across moneyness and time

Figure 1 plots delta (and, ahead of the next sections, gamma, theta, and vega) for a call across moneyness S/K at three maturities. Three features of the delta panel matter.

First, delta is a smooth S-shaped curve from 0 to 1: deep out-of-the-money the option barely responds to the underlying (delta near 0), deep in-the-money it moves nearly one-for-one (delta near 1), and it passes through roughly ½ near the money. Second, the curve *steepens* as expiry approaches — a one-week option's delta swings from 0 to 1 over a narrow band of prices around the strike, while a three-month option's delta changes gently. That steepening is gamma, and it is why short-dated options are treacherous to hedge. Third, the at-the-money delta is not exactly 0.5: the model prints 0.517 at one week, 0.535 at one month, and 0.560 at three months for these inputs. The tilt above ½ comes from the carry term — with a positive rate the forward sits above spot, so an at-the-money-spot call is slightly in-the-money relative to the forward — and it grows with maturity because there is more time for the forward drift to matter.

The maturity effect on out-of-the-money options is even starker and previews the flow story. A 10%-out-of-the-money call has delta 0.0001 at one week, 0.041 at one month, and 0.183 at three months: the same strike is almost inert near expiry and meaningfully directional with a quarter to run. Time is what gives an out-of-the-money strike its delta, and the *loss* of that delta as time passes has a name — charm — which Section 8 makes central.

![First-order greeks for a European call under Black–Scholes–Merton, plotted across moneyness S/K at three maturities (1 week, 1 month, 3 months); K=100, sigma=20%, r=4%, q=0. Delta is an S-curve that steepens toward expiry; gamma, theta and vega all sharpen and concentrate around the money as the option gets shorter-dated. At-the-money the call delta is 0.517 / 0.535 / 0.560 at the three maturities, tilted above one-half by the carry term. Reproduce with `figures/fig_greeks_profiles.py`.](figures/fig_greeks_profiles.png)

### 3.3 A worked delta-hedge: short one call over five rebalances

Symbols become intuition only when they cost money, so we hedge a real position over one real month. The pre-committed rule, fixed before the outcome was seen: take the most recent 21 completed S&P 500 sessions in the cache; at the first session sell one 1-month at-the-money call (strike = spot rounded to the nearest 5 index points, the SPX listing increment); set the option's implied volatility to the CBOE VIX close on the trade date; and delta-hedge the short by holding long shares, rebalancing to the model delta at five fixed points — sessions 0, 5, 10, 15, and settlement at session 20. Interest on premium and hedge cash is ignored (a simplification flagged here and quantified as small at these rates). The trade opened on 2026-08-19 with the index at 7707.98, strike 7710, and VIX at 14.89%, for a premium of 140.31 index points — $14,031 on the 100-multiplier.

Table 1 is the rebalance ledger, printed verbatim by the figure's code. "Held" is the long share-equivalent position (delta × 100) carried to hedge the short call; "traded" is the change made at that rebalance; "hedge P&L" is the cumulative profit on the share leg; "opt P&L" is the cumulative profit on the short-call leg (positive as the call loses value); "net P&L" is their sum.

| Session | Spot | Days left | Call | Delta | Held | Traded | Hedge P&L | Opt P&L | Net P&L |
|---|---|---|---|---|---|---|---|---|---|
| 2026-08-19 | 7707.98 | 20 | 140.31 | 0.536 | 53.6 | +53.6 | $0 | −$0 | $0 |
| 2026-08-26 | 7675.70 | 15 | 103.55 | 0.484 | 48.4 | −5.2 | −$1,730 | +$3,676 | +$1,946 |
| 2026-09-02 | 7666.60 | 10 | 76.17 | 0.451 | 45.1 | −3.3 | −$2,171 | +$6,415 | +$4,244 |
| 2026-09-10 | 7591.70 | 5 | 22.94 | 0.245 | 24.5 | −20.6 | −$5,553 | +$11,737 | +$6,185 |
| 2026-09-17 | 7637.76 | 0 | 0.00 | 0.000 | 0.0 | −24.5 | −$4,422 | +$14,031 | +$9,609 |

Read the ledger as a story. We sold the call and immediately bought 53.6 units to flatten the delta. Over the month the index drifted down and chopped, so the call's delta fell and we sold shares back down toward zero — buying high at the open, selling lower into the decline, which is why the hedge leg *lost* money and finished at −$4,422. Meanwhile the short call decayed toward worthless, and the option leg earned the full premium back, finishing at +$14,031 as the call expired out-of-the-money (spot 7637.76 below the 7710 strike, intrinsic zero). Net, the delta-hedged book made **+$9,609 — about 68.5% of the premium collected**.

Now compare it to doing nothing. A *naked* short call, unhedged, would have kept the entire $14,031, because the call happened to expire worthless. The hedge, in this particular month, *cost* roughly $4,400 relative to the naked position. That looks like the hedge lost — and here is the lesson. The naked short won more only because the path was kind: the index finished below the strike. Had it rallied through 7710 into expiry, the naked short would have taken an unbounded loss while the hedged book would have been protected. The hedge did not underperform; it *bought certainty*, and the price of that certainty was $4,400. What the hedge actually isolated is the volatility premium: over this window the index realized only 9.85% annualized against the 14.89% implied that was sold, and it is that gap — realized far below implied — that made the short-vol position profitable in the first place. The delta-hedge stripped out the directional luck and left the vol edge, which is exactly what Section 4 will formalize.

![Delta-hedging a short 1-month at-the-money S&P 500 call through one real month (Yahoo daily ^GSPC, 21 sessions ending 2026-09-17; the option's sigma is set to the CBOE VIX close on the trade date, 14.89%). Top: the index path with the strike (dashed) and the five weekly rebalances (dots). Bottom: cumulative P&L of the naked short call versus the delta-hedged book. The hedged book finishes at +9,609 dollars, about 68.5% of the premium; the naked short kept the full premium only because the path finished out-of-the-money. Reproduce with `figures/fig_delta_hedge.py`.](figures/fig_delta_hedge.png)

### 3.4 "Delta ≈ probability of finishing in the money" — the useful lie

Traders routinely read a 0.30-delta call as "about a 30% chance of expiring in the money." This is close enough to be useful and wrong in three specific ways worth knowing.

The clean fact is that under BSM the risk-neutral probability that a call finishes in the money is N(d₂), whereas the delta (with q = 0) is N(d₁), and since d₁ = d₂ + σ√T, delta is always *larger* than the in-the-money probability. For the one-month at-the-money call above, delta is 0.535 while N(d₂) is about 0.512 — a two-point gap. Note the gap is in the *probabilities*, not in the *arguments*: d₁ and d₂ differ by exactly σ√T, but N(d₁) − N(d₂) differs by only about φ(d₁)·σ√T — here roughly 0.023, not the 0.058 that σ√T alone would suggest. That probability gap is negligible for short-dated, low-vol options and grows with both maturity and volatility. For a one-year option at 30% vol the two numbers can differ by ten points or more, at which point the folklore is quietly misleading.

The second error is that N(d₂) is the *risk-neutral* probability, not the real-world one. It is computed under the pricing measure, in which the underlying drifts at the risk-free rate rather than at its true expected return, and it embeds the market's risk premia. It is the right number for pricing and the wrong number for "what do I actually think will happen." The third, subtler point is that the approximation conflates two different objects — a hedge ratio and a probability — that only happen to be numerically close; treating delta *as* a probability invites the mistake of adding deltas across strikes and reading the sum as a probability, which is meaningless.

> **When the lie is safe and when it bites.** For a short-dated, near-the-money option, delta and in-the-money probability agree to a point or two and the shorthand is fine. For long-dated or high-vol options, or whenever you are tempted to do arithmetic *on* the probabilities, use N(d₂) explicitly and remember it lives under the risk-neutral measure. Delta is a hedge ratio first; its resemblance to a probability is a coincidence of the normal distribution, not a definition.

**Seed of the flow story.** Delta is the exposure a hedger must neutralize, and a dealer who is short a large book of index calls is *long* a correspondingly large negative-delta hedge in the underlying. The size of that hedge, and how it changes, is the raw material of dealer flow: everything in Section 8 and Section 9 is about how the *aggregate* delta of a dealer's book moves — not because prices moved, but because time passed and volatility shifted — and what re-hedging that forced delta change does to the tape.

## 4 Gamma

If delta is the hedge you take, gamma is the reason it never stays put. It is the single most important greek for anyone who actually hedges, because it is the *curvature* that a straight-line delta-hedge cannot capture — the error term made explicit.

### 4.1 Convexity as the hedger's error term

Gamma is the second derivative of value in the underlying, equivalently the first derivative of delta:

Γ = ∂²V/∂S² = ∂Δ/∂S.

It says how fast delta itself changes as the underlying moves. A delta-hedge is a *linear* approximation: you offset the option's slope with shares and declare yourself flat. But the option's value is *curved*, and gamma measures that curvature. The instant the underlying moves, the option's delta has changed while your share hedge has not, so you are no longer flat — you have to re-hedge, and the amount you must trade to re-flatten is proportional to gamma times the move. Recall the Taylor expansion of Section 2: after delta neutralizes the dS term, the leading survivor is ½·Γ·dS². That term is quadratic in the move and, crucially, always has the *same sign as your gamma* regardless of the move's direction — because dS² is positive whether the underlying rose or fell.

This is the deep fact about gamma: it is a bet on the *size* of moves, not their direction. Long gamma (owning options) profits from motion either way; short gamma (having sold options) profits from stillness and bleeds from motion either way.

### 4.2 Long versus short gamma P&L

Make the asymmetry concrete. Suppose you are *long* an at-the-money option and delta-hedged. If the underlying rallies, your call's delta rises, so your hedge (short shares) is now too small — you were effectively long into the rally and you profit; to re-flatten you sell shares at the higher price. If instead it falls, the call's delta drops, your hedge is now too large — you were effectively short into the decline and you profit again; you buy shares back at the lower price. Long gamma means you are structurally *buying low and selling high* as you re-hedge: every round trip of the underlying banks a small profit. That is *gamma scalping*.

Short gamma is the mirror. Having sold the option and hedged, a rally leaves you under-hedged in the wrong direction — you must buy shares *after* they have gone up — and a decline forces you to sell *after* they have gone down. Short gamma means *buying high and selling low* on every re-hedge, bleeding a little on each oscillation. This is not bad luck; it is the structural cost of being short convexity, and it is exactly what the delta-hedge ledger in Section 3.3 showed: the hedge leg on the short call lost $4,422 precisely because we were short gamma and forced to chase the index around.

Nothing in life is free, so long gamma must be paid for, and it is — with theta. The two are joined at the hip, which Section 5 develops. For now the accounting is: **long gamma, short theta** (you earn from motion, you pay for time); **short gamma, long theta** (you earn from time, you pay for motion).

### 4.3 Gamma scalping and the realized-versus-implied engine

Here is the result that ties the whole section together, and it is worth stating as a theorem of practice: *the profit of a continuously delta-hedged option is, to leading order, proportional to the difference between the volatility the underlying realizes and the implied volatility that was paid, scaled by the option's vega.* You buy an option at some implied vol; if the underlying then thrashes around *more* than that implied vol, your gamma scalps earn more than the theta you pay, and you profit. If it moves *less*, theta wins and you lose. The strike price of the game is the implied vol you paid.

Figure 3 demonstrates this on a clean simulation with no market data. We draw 800 geometric-Brownian-motion paths of 21 trading days, each with its *own* true volatility drawn uniformly between 8% and 36%. On every path we buy a one-month at-the-money straddle at a *fixed* 20% implied vol and delta-hedge it once a day at that same 20%. We then plot the final P&L against the volatility the path actually realized minus the 20% we paid.

The result is a near-straight line through the origin. The fitted slope is **0.226 dollars of P&L per vol point** of (realized − implied), with an R-squared of 0.83, and the scatter around the line is the discretization-and-path noise a once-a-day hedge cannot remove. The punchline is the comparison the code prints alongside: the straddle's initial vega is **0.230 per vol point** — within rounding of the regression slope. The empirical exchange rate between realized-vol surprise and hedged P&L *is* the option's vega, exactly as the theory says. And the sign discipline is stark: **97.4% of the paths that realized more than 20% were profitable, versus only 9.7% of the paths that realized less**. Long gamma is not a directional view and it is not a free lunch; it is a bet, priced fairly on average, that realized volatility will beat the implied volatility you paid.

![P&L of a daily delta-hedged long 1-month at-the-money straddle against the volatility it realized minus the 20% implied it paid, over 800 seeded GBM paths (seed 42; S0=K=100, r=q=0). The fitted slope is 0.226 dollars per vol point, within rounding of the straddle's initial vega of 0.230, with an R-squared of 0.83; 97.4% of paths that realized above 20% were profitable versus 9.7% of those that realized below. Reproduce with `figures/fig_gamma_pnl.py`.](figures/fig_gamma_pnl.png)

### 4.4 Where gamma lives, and the seed of the flow story

Look again at the gamma panel of Figure 1, and ahead to the gamma surface in Figure 5. Gamma is not spread evenly: it *concentrates* at the money and *explodes* as expiry approaches. The model makes this quantitative — at-the-money gamma is 0.028 at six months, 0.069 at one month, and 0.142 at one week, and it diverges toward a spike at expiry. A one-week at-the-money option carries roughly seven times the gamma of a one-year one for the same notional. Away from the money, gamma collapses toward zero in both directions; the whole of an option's convexity is packed into a narrowing band around the strike as time runs out.

This concentration is the geometric fact underneath the entire dealer-flow story of the dealer-flows-and-GEX paper. If market makers are net short a large quantity of options at strikes near the current index level in the last day or two before a major expiry, they are short an enormous, spiky gamma concentrated right where the market is trading. Being short gamma, their re-hedging *amplifies* moves — they must sell into declines and buy into rallies to stay flat, feeding momentum. If instead they are net long gamma there, their re-hedging *damps* moves — selling rallies and buying dips, pinning the index toward the strike. Which regime holds is a question about the sign and location of the aggregate book, and it is exactly the question Section 9 sets up and the flow paper answers. Gamma is where "the greeks" stop being about one trader's option and start being about the market's mechanics.

## 5 Theta

Theta is the greek traders feel most viscerally — the daily bleed on a long option, the daily drip into a short one — and it is best understood not on its own but as the exact counterweight to gamma.

### 5.1 Decay profiles across moneyness

Theta is the derivative of value with respect to the passage of time:

Θ = ∂V/∂t,

conventionally quoted per calendar day so that "theta = −0.04" means the option loses four cents of value per day, all else equal. For a long option theta is negative (time is the enemy); for a short option it is positive (time is the ally). The theta panel of Figure 1 shows the shape: decay is largest, in absolute terms, for at-the-money options and tapers toward zero deep in- or out-of-the-money, and it *accelerates* as expiry approaches. The model prints at-the-money theta of −0.027 per day at three months, −0.043 at one month, and −0.083 at one week — the daily bleed roughly triples as the option's life shortens from a quarter to a week.

The shape has an intuitive reading. An option's extrinsic value is the price of optionality, and optionality is worth most when the outcome is genuinely uncertain — which is precisely at the money. Deep in- or out-of-the-money the outcome is nearly settled, there is little optionality left to decay, and theta is small. And the closer expiry, the faster the remaining optionality evaporates, because there is less and less future in which the underlying can surprise you. The famous "theta curve" — extrinsic value falling ever faster into expiry, roughly like the square root of time remaining for an at-the-money option — is the same phenomenon seen through the option's price rather than its slope.

### 5.2 Theta and gamma: two sides of one trade

The reason theta cannot be understood alone is that it is the *price of gamma*. Under BSM with zero rates the two are locked together by an identity that falls straight out of the pricing equation (Hull 2022; Natenberg 1994):

Θ ≈ −½ · Γ · S² · σ².

In words: the theta you pay per unit time is exactly the gamma you own, times the variance you expect the underlying to generate in that time. This is the same trade Section 4 described, now read from the time side. The daily profit-and-loss of a delta-hedged position collapses to a single tug-of-war between what the underlying *did* and what it was *priced* to do:

P&L per day ≈ ½ · Γ · S² · (σ²_realized − σ²_implied) · dt.

When you are long gamma you own convexity that pays off from motion, and you pay for it continuously through negative theta at a rate set by the *implied* variance; your gamma scalps, meanwhile, earn at a rate set by the *realized* variance. Your net is the difference — realized minus implied variance — which is the same realized-versus-implied engine of Section 4.3, now visible as "did my gamma earnings cover my theta rent?" The two rates cancel exactly when realized equals implied, so the break-even move per step is about S·σ·√dt — the one-standard-deviation cone (Natenberg 1994).

This is why, *under the zero-rate identity above*, a trader cannot wish for "positive theta *and* positive gamma": with carry switched off you are either long gamma and paying theta (betting on motion) or short gamma and collecting theta (betting on calm). But the sign-lock is a property of the zero-rate approximation, not a law of nature. The full identity carries two more terms,

Θ = −½ · σ² · S² · Γ − (r − q) · S · Δ + r · V,

and when rates are positive the discounting term r·V can outweigh the small at-the-money gamma term. A deep-in-the-money European option — a put at a positive rate, or a call on a high-dividend underlying — can then show positive gamma and positive theta at the same time (a put at S = 60, K = 100, r = 5%, σ = 20%, T = 1 has Γ > 0 and Θ > 0). It is uncommon, not impossible. Away from that corner the choice of which side to be on is a volatility forecast in disguise, and the greek that reprices that forecast when the market's estimate itself moves is vega — Section 6.

### 5.3 Event decay and the weekend effect

The clean calendar-day theta of the model hides a practical complication that matters for anyone holding options over specific dates: *not all days decay equally, because not all days carry the same expected variance.* The identity above says decay tracks *variance*, and variance accrues on trading days when the market is open and events resolve — not on quiet calendar days.

The most reliable example is the weekend. A model that decays value smoothly per calendar day implies that an option loses value Saturday and Sunday just as it does on a Wednesday. But no variance is realized while the market is closed, so a rational market tends to *pull the weekend decay forward*: implied volatilities and prices soften on Friday afternoon and the option opens Monday having already given up much of the two-day theta, because everyone knows those two days carry no trading risk (Sinclair 2010; Natenberg 1994). A long-option holder who marks to a naive calendar clock is repeatedly surprised on Monday mornings; a short-premium seller who expects to "collect the weekend" often finds it was already priced out on Friday.

Scheduled events invert the same logic. An earnings report, a central-bank decision, or a major economic release concentrates a burst of expected variance into a single session. Options spanning that event carry an *event premium* — elevated implied vol that is really the market pricing extra variance into one day — and that premium decays sharply the moment the event passes and the uncertainty resolves, the notorious *volatility crush*. The practical rule is that theta is a variance clock, not a calendar clock: to anticipate decay, ask how much the underlying can actually move in each session, and weight the days accordingly.

**Seed of the flow story.** Theta's tie to gamma means that the dealers who are short the market's gamma are the ones *collecting* its theta — and their willingness to keep collecting it is exactly what makes them keep re-hedging in the vol-damping direction. The daily theta a dealer earns is the daily premium they are paid for absorbing the market's demand for optionality; the flow that premium finances is the subject of Section 8 and Section 9.

## 6 Vega

Delta, gamma, and theta all concern the underlying and time — inputs you can observe. Vega concerns the one input you cannot observe directly: the volatility the market is pricing in. It is the greek that turns an option book into a position on volatility itself.

### 6.1 Exposure to implied volatility

Vega is the derivative of value with respect to volatility, conventionally quoted per *vol point* — a one-percentage-point change in implied vol:

Vega = ∂V/∂σ.

A vega of 0.115 means the option gains about 11.5 cents if implied vol rises one point, from 20% to 21%. Both calls and puts have *positive* vega — more volatility makes every option more valuable, because optionality is worth more when the future is wider — so being long options of any stripe is being long vol, and being short premium is being short vol. Note the units carefully: "vega" in this paper is always per one vol *point*, which is why the numbers look like small fractions; some texts quote it per unit vol (100× larger). A greek without its units is not a number, and vega is where that warning bites hardest.

Vega is conceptually distinct from gamma even though both are "volatility" greeks, and confusing them is a classic error (Section 11). Gamma is exposure to *realized* volatility — what the underlying actually does — and it pays off through delta-hedging over time. Vega is exposure to *implied* volatility — what the market *quotes* — and it reprices instantly, before the underlying has moved at all, the moment the market changes its estimate. You can lose on vega and win on gamma in the same session: implied vol collapses (vega loss) while the underlying whips around violently (gamma gain). They are different bets on different objects.

### 6.2 Vega across maturities

The defining feature of vega is its maturity dependence, and it runs *opposite* to gamma's. Where gamma concentrates in short-dated options, vega grows with maturity. The at-the-money vega in the model is 0.056 per point at one week, 0.115 at one month, 0.276 at six months, and 0.381 at one year — the one-year option carries nearly seven times the vega of the one-week option. The reason is structural: a change in *annualized* volatility compounds over the whole remaining life of the option, so a longer-dated option has more time over which the higher vol can act, and vega scales roughly with the square root of time to expiry.

This opposition is the single most useful fact in Figure 5 and worth stating as a slogan: **short-dated books are gamma books; long-dated books are vega books.** A trader running weekly options lives and dies by realized volatility and re-hedging; their vega is almost an afterthought. A trader running one-year options barely notices the daily gamma; their P&L is dominated by where the market marks implied vol. The same underlying, the same strike, a different maturity — and a completely different risk to manage.

### 6.3 Why the wings are a volatility instrument

There is a subtlety in "vega peaks at the money." In *absolute* per-point terms it does: the at-the-money option has the largest vega, and vega falls off toward the wings. But in *relative* terms — vega as a fraction of the option's own premium — the wings are far more vol-sensitive. A deep out-of-the-money option has almost no delta, negligible gamma, and a tiny dollar theta; essentially its entire premium is time value that exists only because of implied volatility. A one-point move in implied vol can change such an option's value by a large fraction of what little it is worth. Its price is, to a first approximation, a pure quote on volatility.

This is why the *wings* of the option chain are where the volatility surface actually lives, and it is the natural bridge to the volatility-surface material. The market does not quote a single volatility; it quotes a different implied vol for every strike, and the systematic pattern — higher implied vols for downside puts than for upside calls in equity indices — is the *skew*. Skew is a statement about the wings, and the wings are the strikes whose value is almost purely vega. A book of options is therefore not a position on "volatility" as a scalar; it is a position on the *shape* of the vol surface across strike and maturity. Managing that — decomposing vega into its exposure to the level, the term structure, and the skew of implied vol — is precisely the subject of the volatility-surface paper, *The Volatility Surface & the VIX Complex*.

> **A vega book is a vol-surface book.** The moment you hold options at more than one strike or maturity, your "vega" is not one number but a profile across the surface. You are long the front and short the back, or long the wings and short the body, and each of those is a different view on how the surface will move. The volatility-surface paper takes that profile apart; this paper's job is only to establish that vega is the coordinate it is written in.

**Seed of the flow story.** Vega links directly to the flow trio of Section 8. When implied volatility moves, it does not only reprice the book — it *changes the book's delta*, through vanna. Crucially, a dealer neutralizes vega itself by trading *other options* (offsetting expiries, variance instruments), not the underlying — so vega on its own creates no flow in the index. It is only the *delta side-effect* of a vol move, vanna, that lands as buying or selling in the underlying. That vega-into-delta leakage is one of the two engines of dealer flow, and Section 8 names it.

## 7 Rho

Rho is the greek that earns exactly one honest page, because for most of the last two decades it deserved less than that — and because the last two years have quietly made it matter again.

Rho is the derivative of value with respect to the risk-free rate, conventionally quoted per one-percentage-point change in rates:

ρ = ∂V/∂r.

A call has positive rho and a put negative: higher rates raise the forward price of the underlying (the carry term in Section 2.2) and discount the strike you would pay, both of which help a call and hurt a put. Rho grows with maturity — a one-year option's value depends far more on the rate than a one-week option's, because the discounting and the forward drift both compound over time.

For an intraday or even a swing trader in liquid equity options, rho is *negligible*, and the reason is simply a comparison of speeds. Interest rates move in increments of 0.25 percentage points a few times a year, on a schedule everyone can see. The underlying can move that option's value by more in an hour than a plausible rate change would in a quarter. A day trader who tracks rho is optimizing the fourth decimal while the first is on fire. This is why rho is traditionally taught last and dismissed fastest.

Two honest caveats keep it on the page. First, rho was near-irrelevant during the 2009–2021 zero-rate era not because it is unimportant in principle but because rates simply did not move and sat near zero, so both the sensitivity's input and the forward drift it feeds were tiny. In the post-2022 regime — policy rates moving from near zero to above five percent and back within a couple of years — the *carry* those rates create is no longer negligible for anyone holding longer-dated options, and the at-the-money delta tilt we saw in Section 3.2 (delta above ½, growing with maturity) is a direct, visible footprint of exactly that carry. Second, for very long-dated instruments — LEAPS, structured products, anything with years to run — rho is a first-order risk that must be hedged like any other; the "ignore it" advice is a statement about short-dated equity options, not a law of nature.

The practical posture, then, is a conditional one. Quote rho, know its sign, and check whether your book's maturity and the current rate environment make it a rounding error or a real exposure. For the short-dated index options that dominate this library's flow material it is a rounding error, and we will not track it further; for a long-dated book in a moving-rate world it is not, and pretending otherwise is the same wishful accounting Section 3.3 warned against. There is no flow story here — rate re-hedging is slow, scheduled, and macro, not the fast mechanical delta adjustment that drives intraday index flow — and that absence is itself the reason rho sits apart from the trio we turn to next.

## 8 Second-order greeks: the flow trio

The first-order greeks answer "how does my value change when an input changes?" The second-order greeks answer the question a hedger actually loses sleep over: *"how does my hedge change when an input changes?"* Delta is the thing you hedge; the second-order greeks are the rate at which your delta-hedge goes stale for reasons other than the underlying moving. Three of them — vanna, charm, and volga — form what practitioners call the *flow trio*, because they are the source of the delta adjustments a large hedged book is *forced* to make on a schedule, and forced trading is what moves markets. A useful mnemonic: delta drifts through three channels — the price channel (gamma), the time channel (charm), and the vol channel (vanna) — and each channel forces a re-hedge.

### 8.1 Vanna: delta's sensitivity to volatility

Vanna is the cross-derivative of value in the underlying and in volatility — equivalently, how much your delta changes when implied vol moves, or how much your vega changes when the underlying moves:

vanna = ∂²V/(∂S ∂σ) = ∂Δ/∂σ = ∂(Vega)/∂S.

The reading that matters for hedging is the first one: *when implied volatility changes, your delta changes, even though the underlying has not moved.* A dealer who was perfectly delta-hedged at yesterday's close can arrive to a market where implied vol has dropped two points overnight and find their book is no longer delta-neutral — vanna has silently handed them a delta they must now trade out of. This is the vega-into-delta leakage flagged at the end of Section 6.

Vanna's *sign* is the interesting part, and it flips across the strike. The left panel of Figure 4 maps it: for a call, vanna is positive below the strike (out-of-the-money) and negative above it (in-the-money), passing through zero right at the money. The model values make this concrete — at 30 days, call vanna is +0.0125 per vol point at S/K = 0.95, essentially zero at the money, and −0.0113 at S/K = 1.05. In words: raising implied vol pushes an out-of-the-money call's delta *up* (it becomes more likely to matter) and an in-the-money call's delta *down* (toward, but never reaching, ½). Over the range of volatilities that matter in practice both effects pull delta *toward* the center — more volatility blurs the distinction between in- and out-of-the-money — but the pull is bounded, not a slide to one-half: an in-the-money call's delta bottoms out well above ½ (around 0.63–0.74 for a moderately in-the-money strike) and then climbs *back* toward 1 as volatility becomes extreme, because in that limit the ½σ√T drift in d₁ dominates and N(d₁) → 1. One further caveat the constant-vol model hides: a real vol move is not uniform across the surface, so aggregate vanna flow depends on *how* the skew and term structure shift, not just on the level of vol.

### 8.2 Charm: delta's decay through time

Charm — also called *delta decay* — is the cross-derivative of value in the underlying and in time: how much your delta changes simply because a day has passed.

charm = ∂²V/(∂S ∂t) = ∂Δ/∂t = ∂Θ/∂S.

This is the effect previewed in Section 3.2: an out-of-the-money option's delta bleeds toward zero as expiry approaches (it is running out of time to reach the strike), while an in-the-money option's delta drifts toward one (its fate is increasingly settled). Charm is the *rate* of that drift, and like vanna it changes sign across the strike. The right panel of Figure 4 shows it: for a call, charm is negative below the strike (delta drifting down) and positive above it (delta drifting up). At 30 days the model prints −0.0047 per day at S/K = 0.95 and +0.0033 at S/K = 1.05.

The number that matters most is how charm *grows into expiry*. At seven days, the same out-of-the-money and in-the-money calls show charm of −0.0182 and +0.0155 per day — roughly four times the 30-day magnitude. Delta decay accelerates violently in the last days of an option's life. This is what makes charm the most *predictable* flow greek: unlike gamma, it needs no price move at all — the drift happens automatically as the clock ticks, so tomorrow's charm-driven re-hedge can be computed today. And it is largest exactly when the most contracts sit near the money in the final sessions before a monthly or weekly expiry, which is why a dealer's charm hedging concentrates into the end of the day and the end of the expiry cycle.

### 8.3 Volga: vega's sensitivity to volatility

Volga — also *vomma* — is the second derivative of value in volatility, the convexity of the option in vol:

volga = ∂²V/∂σ² = ∂(Vega)/∂σ.

It says how much your vega changes when implied vol changes — the vega of your vega. Its sign lives entirely in the product d₁·d₂: it is near zero at the money (where vega is at its peak and locally flat in vol) and positive in both wings (where d₁ and d₂ share a sign), so a book that is *long* wing options is long volga and a book that is *short* the wings is short volga (Natenberg 1994). The practical consequence is a nasty asymmetry: a naked short-wing position is negatively convex in vol, so a volatility spike hits it twice — the vega loss itself, plus vega growing against the position as vol rises — which is the mechanism behind many short-premium blow-ups. Volga is the greek that responds to *vol-of-vol*, and it is the direct link between the greeks of this paper and the curvature of the smile in the volatility-surface paper: a market that expects volatility itself to be jumpy bids up the wings and steepens the smile. It is second-order and slower-moving than vanna and charm, so it is the junior member of the trio for flow purposes, but it is what turns a large implied-vol move from a linear vega event into a nonlinear one.

![Sign maps of the two delta-drift greeks for a European call under Black–Scholes–Merton (K=100, sigma=20%, r=4%, q=0): vanna (delta change per +1 vol point) and charm (delta change per calendar day) across moneyness and days to expiry. The solid line is the zero contour; red is positive, blue negative. Both flip sign across the strike and grow sharply into expiry — at 7 days the out-of-the-money charm reaches about −0.018 per day, four times its 30-day value. Reproduce with `figures/fig_second_order.py`.](figures/fig_second_order.png)

### 8.4 Why a hedger reads the trio as tomorrow's forced trades

Here is the point that makes the second-order greeks the pivot of this whole track. A first-order greek is a risk you *currently* carry; a second-order greek is a trade you are *going to be forced to make*, on a schedule, regardless of what the market does. Charm says: even if the underlying is perfectly flat overnight, a day will pass, your book's delta will drift by a knowable amount, and to stay hedged you will have to buy or sell a knowable quantity at tomorrow's open. Vanna says: if implied vol moves — and it moves every day — your delta will shift by another knowable amount, and you will have to trade that too. These are not risks in the ordinary sense of "the market might move against me." They are *pre-scheduled hedging flows*, computable today from the shape of the book.

That is why the constant-volatility falsehood in BSM (Section 2.2) matters most exactly here: the model that produces these clean vanna and charm surfaces assumes volatility never moves, which is the assumption vanna is entirely about violating. The signs and shapes in Figure 4 are qualitatively right and quantitatively a starting point, not the last word; a stochastic-vol model would fatten them. But the *structure* — sign flips across the strike, explosive growth into expiry — is robust, and it is enough to see the mechanism.

**Seed of the flow story.** Now assemble it. If dealers as a group are short a large book of index options concentrated near the current level into an expiry, then charm and vanna are, every day, handing that group a delta they did not ask for and must hedge. The direction of those forced trades depends on the sign of the aggregate book, and their size depends on how much open interest sits near the money and how close expiry is — both of which peak into monthly and weekly expirations. Note the epistemics carefully: this flow is *information about positioning, not a prediction* — by the time it prints, the hedges are being placed, not forecast. The recurring, calendar-locked hedging pressure this creates is what the dealer-flows-and-GEX paper is about; Section 8 has given it its greeks and Section 9 gives it its bookkeeping.

## 9 Portfolio aggregation

A single option's greeks are a warm-up. A trading book holds hundreds or thousands of positions across many strikes and expiries, and the only way to manage it is to *aggregate* — to collapse the whole book into a handful of net numbers. This section shows how, and what a dealer's resulting book summary actually looks like.

### 9.1 Greeks are additive; sum them

The one structural fact that makes portfolio risk tractable is that greeks are *additive* across positions, because differentiation is linear. The delta of a book is the sum of the deltas of its positions, each weighted by how many contracts you hold (long positive, short negative) and by the contract multiplier. The same holds for gamma, theta, vega, and every other greek:

Δ_book = Σ n_i · m_i · Δ_i ,   Γ_book = Σ n_i · m_i · Γ_i ,   and so on,

where n_i is the signed contract count of position i and m_i its multiplier. This linearity is what lets a desk holding a thousand lines report a single net delta, a single net gamma, and hedge the aggregate rather than each line — you neutralize the book's net delta with one trade in the underlying, not a thousand.

There is one important honesty caveat: additivity is exact *only when every greek is evaluated at the same set of inputs and interpreted consistently.* Adding a one-week option's gamma to a one-year option's gamma gives an arithmetically correct sum, but the two contribute utterly different risks — the short-dated gamma will swamp the book near expiry and vanish afterward, the long-dated gamma is a slow background hum. The sum is a valid instantaneous hedge target and a misleading summary of *where* the risk lives. That is why desks look at greeks not only as book totals but as *profiles* — gamma by strike, vega by expiry — which is the aggregated cousin of the surfaces in Figure 5.

### 9.2 Dollar-greeks: putting everything in one currency

Raw greeks are in mixed and awkward units — delta in shares, gamma in delta-per-point, vega in dollars-per-vol-point-per-contract — and they are not comparable across underlyings of different price levels. The fix desks use is *dollar-greeks*, which restate each greek as the P&L impact of a *standardized* move, so that everything is in dollars and directly comparable (Hull 2022).

The two that dominate the flow literature are worth defining precisely:

- **Dollar delta** — the dollar value of the underlying you are effectively long or short: Δ_book × S × m (with m the contract multiplier). It answers "how many dollars of the index am I really holding?"
- **Dollar gamma** — the change in dollar delta for a 1% move in the underlying, usually written Γ_book × S² × m / 100. It answers "how much does my directional exposure change if the index moves one percent?" — which is exactly the size of the re-hedge a 1% move forces on you.

Dollar gamma is the quantity that the entire dealer-gamma-exposure literature is built on. When commentators speak of a market maker's aggregate gamma exposure at a price level, they mean the total dollar gamma of the dealer community's book at that level — the dollar amount of underlying they must trade per percent move to stay hedged. Its *sign* is the whole game: positive aggregate dollar gamma means dealers buy dips and sell rallies (damping, mean-reverting flow), negative means they sell dips and buy rallies (amplifying, momentum flow). This paper deliberately builds these quantities from freely available first principles and stops at the definition; the sign, magnitude, and market impact of the real aggregate book is the subject of the dealer-flows-and-GEX paper, and it is estimated there from public open-interest data, never from any licensed or proprietary feed.

> **Where the tidy arithmetic meets a messy desk.** Aggregation gives an exact instantaneous number and hides four real frictions that the dealer-flows-and-GEX paper must confront. Hedging is *discrete*, done in bands to save transaction costs, not continuously — so the book is rarely exactly flat. Capital and risk limits are finite, and under stress a forced de-risking can make hedging *more* pro-cyclical than the sign of gamma alone suggests. The hedge is often placed in *futures* (ES, NQ), not the cash index, which changes where the flow footprint lands. And "the dealer" does not exist — the aggregate is an estimate over many heterogeneous books with different signs and strikes. None of this breaks the greeks; it means the book summary is a model of a force, not a meter reading.

### 9.3 What a dealer's book summary looks like

Put the pieces together and a market maker's risk report is a short, readable line. Stripped to its essentials it is a vector of net dollar-greeks with a note on where they concentrate:

> *Net dollar delta ≈ flat (hedged); net dollar gamma −$X million per 1% (short gamma, concentrated at strikes near spot in the front expiry); net vega +$Y thousand per vol point (long the back months, short the front); net charm +$Z million delta-to-buy per day into Friday's expiry.*

Every term in that summary is a greek from this paper, aggregated by Section 9.1 and dollarized by Section 9.2. The delta line says the book is hedged *now*. The gamma line says which way and how hard re-hedging will push the market on the next move, and where. The vega line says the book's exposure to the vol surface shifting. And the charm line — the one a first-order-only trader never sees — says how much delta the book will be *forced* to trade tomorrow simply because a day passed. A dealer reads this summary and knows, before the market opens, the direction and rough size of the trades the book will compel them to make. That foreknowledge, aggregated across the whole dealer community and made mechanical by the size and calendar-locking of index option open interest, is the reason the greeks in this paper are not merely a risk-management vocabulary but a description of a force that acts on the market itself. Building the estimate of that force from public data, and testing whether it actually moves index prices, is where this track goes next.

## 10 Worked examples in Python

Everything above can be computed from scratch in a few dozen lines of standard-library Python — no pricing library, no `scipy`, just `math`. This section prints that code, checks it against the numbers quoted earlier, and points to the surface figure it generates. The purpose is not to build a production pricer but to make the greeks *concrete*: each one is a specific arithmetic combination of the same handful of quantities, and seeing them side by side dissolves the mystery.

### 10.1 All the greeks from scratch

The normal density and cumulative function are all the special functions we need, and `math.erf` gives us the latter without any dependency. Everything else is the closed forms differentiated in the earlier sections.

```python
import math

SQRT2PI = math.sqrt(2.0 * math.pi)
def npdf(x): return math.exp(-0.5 * x * x) / SQRT2PI            # standard normal pdf
def ncdf(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))  # standard normal cdf

def bsm_greeks(S, K, T, r, sigma, q=0.0, call=True):
    """Black-Scholes-Merton price and greeks. vega/vanna/volga per vol POINT;
    theta and charm per CALENDAR DAY; rho per 1% rate. sign=+1 call, -1 put."""
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    dq, dr = math.exp(-q * T), math.exp(-r * T)
    s = 1.0 if call else -1.0
    price = s * (S * dq * ncdf(s * d1) - K * dr * ncdf(s * d2))
    delta = s * dq * ncdf(s * d1)
    gamma = dq * npdf(d1) / (S * sigma * sqrtT)
    vega  = S * dq * npdf(d1) * sqrtT / 100.0
    theta = (-S * dq * npdf(d1) * sigma / (2 * sqrtT)
             - s * r * K * dr * ncdf(s * d2)
             + s * q * S * dq * ncdf(s * d1)) / 365.0
    rho   = s * K * T * dr * ncdf(s * d2) / 100.0
    vanna = -dq * npdf(d1) * d2 / sigma / 100.0
    charm = (q * s * dq * ncdf(s * d1)
             - dq * npdf(d1) * (2 * (r - q) * T - d2 * sigma * sqrtT)
             / (2 * T * sigma * sqrtT)) / 365.0
    volga = S * dq * npdf(d1) * sqrtT * d1 * d2 / sigma / 10000.0
    return dict(price=price, delta=delta, gamma=gamma, vega=vega, theta=theta,
                rho=rho, vanna=vanna, charm=charm, volga=volga)

if __name__ == "__main__":
    g = bsm_greeks(S=100, K=100, T=21/252, r=0.04, sigma=0.20, call=True)
    for name in ("price", "delta", "gamma", "vega", "theta", "rho", "vanna", "charm"):
        print(f"{name:6s} {g[name]:+.5f}")
```

Run on a one-month at-the-money call (S = K = 100, T = 21/252, r = 4%, sigma = 20%), it prints delta +0.535, gamma +0.069, vega +0.115, theta −0.043, and rho +0.043 — matching, to the printed precision, the at-the-money one-month values quoted from Figure 1 in Section 3–Section 6. The point of reproducing them here from a self-contained function is that you can now change one input and watch the whole risk vector move: shorten T and gamma and theta blow up while vega shrinks; raise sigma and vanna and volga come alive. The greeks are not nine unrelated formulae; they are nine slopes of the *same* surface, and this function is that surface's derivative in every direction at once.

### 10.2 The two risk mountains

To see the maturity opposition of Section 4 and Section 6 in one image, Figure 5 plots gamma and per-point vega as surfaces over strike and maturity for a fixed spot, using the same closed forms. The two shapes tell the whole story of where each risk lives. Gamma is a sharp ridge running along the at-the-money line that *rises without bound* as maturity shrinks toward zero — the near-expiry spike that Section 4.4 identified as the seat of dealer-gamma flow. Vega is a broad hill, also centered at the money, that *grows* with maturity and is nearly flat near expiry — the back-month volatility exposure that Section 6 called the real content of a long-dated book. Laid side by side they make the slogan visual: the front of the curve is a gamma instrument, the back is a vega instrument, and the same strike is a different animal depending only on how much time it has left.

![Gamma and per-point vega for a fixed spot of 100 across strike and maturity under Black–Scholes–Merton (sigma=20%, r=4%, q=0). Gamma piles up at the money and explodes as expiry approaches (ATM gamma 0.142 at one week versus 0.019 at one year); vega also sits at the money but grows with maturity (0.056 to 0.381 per point over the same range). Short-dated books are gamma books; long-dated books are vega books. Reproduce with `figures/fig_greeks_surface.py`.](figures/fig_greeks_surface.png)

### 10.3 Every chart rebuilds from free data

A methodological note that this library treats as non-negotiable: nothing in this paper requires paid or proprietary data. Three of the five figures are pure model computations that need no data at all. The delta-hedge example (Figure 2) uses only daily S&P 500 closes from the public Yahoo chart API and the CBOE VIX index from FRED, both cached in the figures folder so the charts rebuild offline and identically. The gamma-P&L simulation (Figure 3) is fully determined by its seed. Anyone can clone the repository, run the five scripts named in the captions, and reproduce every number and every image in this document, which is the standard the whole Trading Library holds itself to.

## 11 Common misconceptions and glossary

### 11.1 Common misconceptions

- **"Delta is the probability of finishing in the money."** A useful shorthand that is systematically too high (delta is N(d₁), the risk-neutral probability is N(d₂), and they differ by roughly φ(d₁)·σ√T), risk-neutral rather than real-world, and a hedge ratio rather than a probability. Safe for short-dated near-the-money options; misleading for long-dated or high-vol ones, and never a thing to do arithmetic on (Section 3.4).
- **"Gamma and vega are both volatility, so they're the same risk."** Gamma is exposure to *realized* volatility and pays off through re-hedging over time; vega is exposure to *implied* volatility and reprices instantly. You can win on one and lose on the other in the same hour (Section 6.1).
- **"Positive theta and positive gamma at once is impossible."** True only at zero carry, where Θ ≈ −½ Γ S² σ² does force opposite signs: owning convexity costs time-decay, collecting time-decay means being short convexity. But the full identity Θ = −½ σ² S² Γ − (r − q) S Δ + r V carries a discounting term, and at a positive rate a deep-in-the-money European put (or a call on a high-dividend underlying) can carry Γ > 0 and Θ > 0 together. It is uncommon, not forbidden, and not evidence of a mislabeled greek (Section 5.2).
- **"Theta is a smooth daily bleed."** Theta tracks *variance*, which accrues on trading days and around events, not evenly across the calendar. Weekends decay early and event premium crushes on resolution (Section 5.3).
- **"An at-the-money option has delta 0.50."** Only with zero carry. With a positive rate the forward sits above spot and the at-the-money-spot call delta runs 0.52–0.56, growing with maturity — a visible footprint of rho (Section 3.2, Section 7).
- **"Rho never matters."** True for short-dated equity options in a quiet-rate world; false for long-dated instruments and false again in a regime where policy rates swing five points in two years (Section 7).
- **"Vega creates buying and selling in the underlying."** No — a dealer hedges vega with other options, not the index. Only vanna, the delta side-effect of a vol move, produces flow in the underlying (Section 6.3, Section 8.1).
- **"The greeks describe my option."** For a single position, yes; but greeks *aggregate*, and the interesting object is the net dollar-greek profile of a whole book — which, summed across the dealer community, becomes a force on the market rather than a description of one trade (Section 9).

### 11.2 Glossary

- **Delta (Δ)** — ∂V/∂S. Share-equivalent exposure and hedge ratio; ~0 to +1 for calls, ~−1 to 0 for puts.
- **Gamma (Γ)** — ∂²V/∂S² = ∂Δ/∂S. Curvature; the rate at which a delta-hedge goes stale. Concentrates at the money and near expiry.
- **Theta (Θ)** — ∂V/∂t. Time decay, quoted per calendar day; the price paid (or earned) for gamma.
- **Vega** — ∂V/∂σ. Sensitivity to implied volatility, per vol point; positive for all options; grows with maturity.
- **Rho (ρ)** — ∂V/∂r. Sensitivity to the risk-free rate, per 1%; positive for calls, negative for puts; grows with maturity.
- **Vanna** — ∂²V/(∂S ∂σ) = ∂Δ/∂σ. How delta moves when implied vol moves; sign flips across the strike.
- **Charm** — ∂²V/(∂S ∂t) = ∂Δ/∂t. Delta decay; how delta drifts as time passes; explodes into expiry.
- **Volga (vomma)** — ∂²V/∂σ² = ∂(Vega)/∂σ. Convexity in vol; near zero at the money, largest in the wings; the vol-of-vol exposure.
- **Moneyness** — the position of spot relative to strike, here S/K; drives the shape of every greek.
- **Implied volatility** — the volatility that, put into BSM, reproduces the market price of an option; the input vega is a sensitivity to.
- **Delta-neutral** — a book whose net delta is ~0, so it is directionally flat for the *next small move* only.
- **Gamma scalping** — re-hedging a long-gamma position to bank the buy-low/sell-high profit that motion produces; pays off when realized vol beats implied.
- **Dollar delta / dollar gamma** — greeks restated as the dollar P&L of a standardized move; the currency in which a book's risk and a dealer's hedging flow are measured.
- **Volatility crush** — the sharp fall in implied vol (and thus option value) when a scheduled event resolves and its variance premium is realized.

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| First-order greek profiles across moneyness and maturity; at-the-money call delta 0.517/0.535/0.560 | Own reproducible computation — `figures/fig_greeks_profiles.py` |
| A delta-hedged short 1-month at-the-money S&P 500 call over one real month nets +$9,609 (~68.5% of premium); realized 9.85% versus 14.89% implied | Own reproducible computation — `figures/fig_delta_hedge.py` |
| The hedged straddle's P&L per vol point (slope 0.226) equals the option's vega (0.230), R² 0.83, over 800 GBM paths | Own reproducible computation — `figures/fig_gamma_pnl.py` |
| Vanna and charm sign maps flip across the strike and grow into expiry | Own reproducible computation — `figures/fig_second_order.py` |
| Gamma and vega surfaces: gamma spikes into expiry, vega grows with maturity | Own reproducible computation — `figures/fig_greeks_surface.py` |
| Black–Scholes–Merton closed-form price and greeks | Literature — (Black & Scholes 1973; Merton 1973) |
| The greeks are the terms of a first-order Taylor expansion of the price | Literature — (Hull 2022) |
| BSM's constant-vol assumptions are false; the volatility smile is the market's own admission | Literature — (Natenberg 1994; Sinclair 2010) |
| The theta–gamma identity Θ ≈ −½·Γ·S²·σ² and the realized-versus-implied engine | Literature — (Hull 2022; Natenberg 1994) |
| Theta tracks variance, not the calendar: weekend decay pulled forward, event-premium crush | Literature — (Sinclair 2010; Natenberg 1994) |
| Real dealer hedging is discrete, banded, often placed in futures, and aggregated across heterogeneous books | Practitioner consensus — not independently verified |

## References

- Black, F., & Scholes, M. (1973). The pricing of options and corporate liabilities. *Journal of Political Economy, 81*(3), 637–654.
- Hull, J. C. (2022). *Options, Futures, and Other Derivatives* (11th ed.). Harlow: Pearson.
- Merton, R. C. (1973). Theory of rational option pricing. *The Bell Journal of Economics and Management Science, 4*(1), 141–183.
- Natenberg, S. (1994). *Option Volatility and Pricing: Advanced Trading Strategies and Techniques* (2nd ed.). New York: McGraw-Hill.
- Sinclair, E. (2010). *Option Trading: Pricing and Volatility Strategies and Techniques.* Hoboken, NJ: Wiley.

*All references above are publicly accessible: two are peer-reviewed journal articles and three are published books widely held in libraries and in print. No proprietary, course, or trading-academy material is cited, and no licensed or vendor data is used anywhere in this paper.*
