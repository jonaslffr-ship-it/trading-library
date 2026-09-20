---
title: "First-Order Greeks — Delta, Theta, Vega, Rho"
last_updated: 2026-09-20
---

# First-Order Greeks — Delta, Theta, Vega, Rho

## Abstract

An option's price is one number that answers to four moving inputs at once — the underlying, the passage of time, the volatility the market is pricing, and the interest rate — and the first-order greeks are simply the four partial derivatives that say how much the price moves when each input moves a little. This paper builds delta, theta, vega, and rho from that single idea, using the Black–Scholes–Merton model not as a forecast but as a ruler that turns each slope into a concrete number. We read delta as a hedge ratio and share-equivalent exposure, and take apart the folklore that a call's delta is its probability of finishing in the money; place theta as a decay that tracks variance rather than the calendar; show vega and rho as the two maturity greeks, both growing with time to expiry; and define elasticity as the leverage built into every option. We aggregate greeks into dollar terms, compute all four from scratch in about thirty lines of Python, and close with common misconceptions and a glossary. Every figure is a reproducible model computation, and every number quoted in the text is printed by the accompanying code.

## Keywords

Delta, theta, vega, rho, elasticity, lambda, Black–Scholes–Merton, hedge ratio, moneyness, time decay, implied volatility, dual delta, dollar delta, option sensitivities, first-order greeks, term structure, N(d1) versus N(d2), risk-neutral probability

## 1 Introduction

### 1.1 Motivation and thesis

Buy a single option and you have, without quite meaning to, taken four bets at once. You have bet on where the underlying goes; on how much time you have; on what the market will decide volatility is worth; and, more quietly, on interest rates. Sell the option and you inherit the mirror image of all four. A trader who watches only the first of these — "will it go up or down?" — is exposed to three risks they have not named, and the whole discipline of option risk begins with giving those risks names and numbers.

The names are the *greeks*. Each answers one question of the same shape: *if this input changes by a small amount and everything else is held still, how much does the option's value change?* — which is precisely the definition of a partial derivative. This paper is about the four *first-order* greeks, the four that attach to the four inputs directly: *delta* for the underlying, *theta* for time, *vega* for volatility, and *rho* for the rate. They are called first-order because each is a first derivative — a straight-line slope of the price surface in one direction — as opposed to the curvature and cross-effects that make up the second-order greeks.

The thesis of this paper is that these four are best understood not as formulae to be looked up but as a single, connected reading of one surface. The option price is a function of four inputs; the greeks are its four slopes; and almost every practical fact about options — why a hedge ratio is not a probability, why an option decays faster the closer it gets to expiry, why a long-dated option is really a volatility instrument, why a cheap out-of-the-money call carries enormous leverage — falls out of looking carefully at those four slopes and where they are largest. Read this way the greeks stop being a glossary and become a way of seeing.

### 1.2 Scope, prerequisites, and intended reader

This paper is deliberately self-contained. It assumes only that you know what a call and a put are — the right, but not the obligation, to buy or to sell at a fixed strike — and that you are comfortable with the idea of a first derivative as a slope and can read a short Python snippet. It does not assume any stochastic calculus, and it does not derive the Black–Scholes–Merton equation; it only uses the model's closed-form price and differentiates it. It does not require any prior paper in this library, though it points, by topic, to three companion papers where the story continues: the greeks-and-hedging paper (curvature, hedging, and the second-order greeks), the volatility-surface paper (how implied volatility varies across strike and maturity), and the dealer-flows-and-GEX paper (how aggregate hedging becomes a force on the market).

After reading this paper, a reader can state each of delta, theta, vega, and rho as a partial derivative in one sentence and in words; give its sign and rough magnitude for a call and a put across moneyness and maturity; explain why a call's delta is not its probability of finishing in the money, and by how much the two differ; read theta as a variance clock rather than a calendar clock; locate vega and rho as the two greeks that grow with maturity; compute an option's elasticity and read it as leverage; restate any greek in dollar terms; and reproduce every number in the paper from the accompanying code.

### 1.3 Data and reproducibility

Every figure and every printed number in this paper is a self-contained Black–Scholes–Merton computation that needs no market data at all: the inputs are stated in each caption, and the greeks are the exact derivatives of the closed-form price. Each figure script also verifies its closed forms against a central finite difference of the price — bumping the underlying, time, volatility, and rate in turn — and prints the worst relative error to the console; across the tested points that error is on the order of one part in a million, which is the paper's guarantee that the plotted greeks are the derivatives they claim to be. Where a convention could go two ways — per-vol-point versus per-unit vega, per-calendar-day versus per-trading-day theta, per-one-percent versus per-unit rho — the choice is stated explicitly, because a greek quoted without its units is not a number. *This is a research and educational document, not investment advice.*

### 1.4 Organization

The paper is a single argument built one slope at a time. Section 2 sets up the option price as a surface over four inputs, writes the first-order Taylor expansion whose terms are the greeks, and introduces Black–Scholes–Merton as the ruler that makes them concrete, with its assumptions listed and honestly flagged as wrong-but-useful. Section 3 develops delta as a hedge ratio, reads its shape across moneyness and time, and dismantles the delta-as-probability folklore (Figure 1). Section 4 treats theta as time decay that tracks variance, not the calendar. Section 5 places vega across maturities and explains why the wings are a volatility instrument (Figure 2). Section 6 gives rho its honest page. Section 7 defines elasticity, the leverage built into every option (Figure 3). Section 8 briefly shows how greeks aggregate and how dollar-greeks put them in one currency. Section 9 computes all four from scratch in Python and checks the numbers. Section 10 collects common misconceptions and a glossary, and the references close the paper.

## 2 Why first-order greeks exist

Before naming a single greek it is worth being exact about what we are differentiating and why the derivatives are the right thing to look at.

### 2.1 The price is a surface over four inputs

The value of a European option is a function of a handful of inputs:

V = f(S, t, σ, r)

— the underlying price S, the current time t (equivalently the time to expiry T), the volatility σ the market is pricing in, and the risk-free rate r, with the strike K and any dividend or carry q held as fixed parameters of the contract. Said in words, the price of an option is a surface sitting over the space of "where the underlying is, how much time is left, how jumpy the market thinks the future is, and what cash costs." The greeks are the *slopes* of that surface in each direction.

Slopes matter more than the level because a trader almost never cares about what an option is worth in isolation; they care about how that worth will *change* when the world moves a little between now and their next decision. A first-order Taylor expansion of the price around today's inputs makes this exact (Hull 2022):

dV ≈ (∂V/∂S) dS + (∂V/∂t) dt + (∂V/∂σ) dσ + (∂V/∂r) dr + ½ (∂²V/∂S²) dS² + …

Each first-order greek is one term in this expansion. *Delta* (Δ = ∂V/∂S) multiplies the move in the underlying; *theta* (Θ = ∂V/∂t) the passage of time; *vega* (∂V/∂σ) the change in volatility; *rho* (ρ = ∂V/∂r) the change in rates. These four are the subject of this paper. The next term, ½(∂²V/∂S²)dS², is the leading *second-order* correction: it multiplies the *square* of the underlying move, and the sensitivity in front of it — gamma — is where the curvature of the surface lives. Gamma and the other second-order greeks are the subject of the greeks-and-hedging paper; here they matter only as the reason a first-order picture is a linear approximation with a known error term, and we flag where that error would mislead.

> First-order greeks are a language for *what happens next*, not *what is it worth.* The market hands you the price. The greeks are your own translation of that price into the sentence: *if the underlying moves a point, if a day passes, if implied volatility ticks up, if rates shift — here is what I make or lose.* A position is only understood once that sentence is written down.

### 2.2 Black–Scholes–Merton as a ruler

To turn those partial derivatives into concrete numbers you need a formula for V, and the standard one is the Black–Scholes–Merton model (Black & Scholes 1973; Merton 1973). For a European call with continuous carry q,

C = S · exp(−qT) · N(d₁) − K · exp(−rT) · N(d₂),

and for a put, P = K · exp(−rT) · N(−d₂) − S · exp(−qT) · N(−d₁), where

d₁ = [ ln(S/K) + (r − q + ½σ²) T ] / (σ√T),  and  d₂ = d₁ − σ√T.

Two special functions do all the work, and both are elementary. The *standard normal probability density* φ(x) = exp(−x²/2) / √(2π) is the familiar bell curve. The *standard normal cumulative distribution* N(x) is the area under that bell to the left of x — the probability that a standard normal draw comes out below x — and it is available from the error function as N(x) = ½[1 + erf(x/√2)], which is why the code in Section 9 needs nothing beyond Python's `math` module. The quantities d₁ and d₂ are just standardized log-moneyness: d₂ measures how many standard deviations, over the life of the option, the strike sits below the risk-neutral forward, and d₁ is the same distance shifted up by one half of that standard deviation, σ√T. Every greek in this paper is a partial derivative of the call or put formula above, and because those formulae are closed-form, so are the greeks — no numerical fitting anywhere.

It is important to be honest about what this ruler gets wrong. Black–Scholes–Merton assumes, among other things, that the underlying follows a geometric Brownian motion with *constant* volatility, that trading is continuous and frictionless, that any dividend is a known continuous yield, and that returns are log-normal with no jumps (Hull 2022; Sinclair 2010). Every one of these is false in a real market: volatility is stochastic and clusters, markets gap, liquidity is finite, and the return distribution has fat tails and a persistent skew. If the assumptions were even approximately complete, a single implied volatility would price every strike — and the existence of the *volatility smile*, the fact that different strikes trade at different implied volatilities, is the market's own admission that the model is incomplete (Natenberg 1994).

And yet the greeks computed from this "wrong" model are the industry's working language, for a reason worth stating precisely: the model is used not as a theory of the true price but as a *quoting and translation device.* Traders take the observed market price of each option, invert the formula to find the implied volatility that reproduces that price, and then use the model's greeks *at that implied volatility* to translate between price and risk. The model is wrong about the level of volatility — so the market supplies the volatility, one number per strike — but its sensitivities are a stable, shared, well-understood coordinate system for talking about risk. That is the sense in which it is *wrong but useful*: a bad forecaster and an excellent ruler. Throughout this paper we use it as a ruler, quote every input, and set q = 0 in the figures unless stated, so the carry effects we do discuss are the ones the rate r alone produces.

## 3 Delta

Delta is the first greek every trader meets and the one they most often half-understand. It is the slope of the option's value in the underlying — but its real job is as a *hedge ratio*, and its most famous interpretation is a lie that is useful right up until it isn't.

### 3.1 Delta as a hedge ratio and share-equivalent exposure

Formally, delta is the partial derivative of value with respect to the underlying,

Δ = ∂V/∂S,

and under Black–Scholes–Merton a call's delta is exp(−qT)·N(d₁) while a put's is −exp(−qT)·N(−d₁). So a call delta runs from 0 to about +1 and a put delta from about −1 to 0. In words, delta tells you how many dollars the option's value changes for a one-dollar change in the underlying: a call with delta 0.45 gains roughly 45 cents when the underlying rises a dollar; a put with delta −0.30 loses 30 cents on that same up-move.

The operational reading is *share-equivalent exposure.* An option with delta 0.45 on a contract covering 100 shares behaves, for small moves, like being long 45 shares of the underlying. That is what makes delta a hedge ratio: to neutralize the directional risk of that option you short 45 shares (or the futures equivalent), and the combined position has, momentarily, zero delta. "Momentarily" is doing real work in that sentence — the delta changes as soon as the underlying moves, because the price surface is curved, and the rate of that change is a second-order greek (gamma) developed in the greeks-and-hedging paper. For the purposes of this paper, delta is the instantaneous share-equivalent, and a *delta-neutral* book is one whose net delta is roughly zero: directionally flat for the next small move, at this instant, and no longer.

### 3.2 Delta across moneyness and time

Figure 1 plots delta — with theta, vega, and rho beside it, ahead of the sections that treat them — for a call across moneyness S/K at three maturities. Three features of the delta panel matter.

First, delta is a smooth S-shaped curve from 0 to 1: deep out-of-the-money the option barely responds to the underlying (delta near 0), deep in-the-money it moves nearly one-for-one (delta near 1), and it passes through roughly one-half near the money. Second, the curve *steepens* as expiry approaches — a one-week option's delta swings from 0 to 1 over a narrow band of prices around the strike, while a three-month option's delta changes gently. That steepening is the curvature of the price in the underlying; its greek is gamma, treated in the greeks-and-hedging paper, and it is the reason short-dated options are so much harder to keep hedged.

Third, the at-the-money delta is not exactly 0.5. For these inputs the model prints 0.517 at one week, 0.535 at one month, and 0.560 at three months. The tilt above one-half is the *carry tilt*: with a positive rate the forward price sits above spot, so an at-the-money-spot call is slightly in-the-money relative to the forward, and its delta reflects that. The tilt grows with maturity because there is more time for the forward drift to accumulate — which is the same rate effect that rho will measure directly in Section 6, seen here through delta.

The maturity effect on out-of-the-money options is starker still. A 10%-out-of-the-money call has delta 0.0001 at one week, 0.041 at one month, and 0.183 at three months: the same strike is almost inert near expiry and meaningfully directional with a quarter to run. Time is what gives an out-of-the-money strike its delta, and the *loss* of that delta as time passes is itself a (second-order) greek, charm, which the greeks-and-hedging paper makes central.

![First-order greeks for a European call under Black–Scholes–Merton, plotted across moneyness S/K at three maturities (1 week, 1 month, 3 months); K=100, sigma=20%, r=4%, q=0. Delta is an S-curve that steepens toward expiry; theta deepens and concentrates around the money as the option shortens; vega and rho are largest at the money and grow with maturity. At the money the call delta is 0.517 / 0.535 / 0.560 at the three maturities, tilted above one-half by the carry term. Reproduce with `figures/fig_fo_first_order.py`.](figures/fig_fo_first_order.png)

### 3.3 "Delta ≈ probability of finishing in the money" — the useful lie

Traders routinely read a 0.30-delta call as "about a 30% chance of expiring in the money." This is close enough to be useful and wrong in three specific ways worth knowing.

The clean fact is that under Black–Scholes–Merton the risk-neutral probability that a call finishes in the money is N(d₂), whereas the delta (with q = 0) is N(d₁). Since d₁ = d₂ + σ√T, delta is always *larger* than the in-the-money probability. For the one-month at-the-money call above, the model gives d₁ = 0.0866 and d₂ = 0.0289, so delta = N(d₁) = 0.5345 while N(d₂) = 0.5115 — a gap of 0.0230, about two and a third points. The gap is essentially φ(d₁)·σ√T wide, so it is negligible for short-dated, low-vol options and grows with both maturity and volatility. Push to a one-year option at 30% volatility and the model prints delta = 0.6115 against N(d₂) = 0.4934 — a gap of nearly twelve points, at which point the folklore is quietly but badly misleading.

The second error is that N(d₂) is the *risk-neutral* probability, not the real-world one. It is computed under the pricing measure, in which the underlying drifts at the risk-free rate rather than at its true expected return, and it embeds the market's risk premia. It is the right number for pricing and the wrong number for "what do I actually think will happen." The third, subtler point is that the approximation conflates two different objects — a hedge ratio and a probability — that only happen to be numerically close; treating delta *as* a probability invites the mistake of adding deltas across strikes and reading the sum as a probability, which is meaningless. Delta is a hedge ratio first; its resemblance to a probability is a coincidence of the normal distribution, not a definition. Use it as a shorthand for short-dated, near-the-money options, and reach for N(d₂) explicitly the moment maturity, volatility, or arithmetic-on-probabilities enters.

### 3.4 The dual delta

There is a fifth first-order slope hiding in the same formula: the sensitivity of the option's value not to the underlying but to its own *strike.* This is the *dual delta,* ∂V/∂K, and for a call it is −exp(−rT)·N(d₂), for a put +exp(−rT)·N(−d₂). It is the mirror of ordinary delta across the S–K symmetry of the pricing formula: where delta reads how the price moves as spot moves, the dual delta reads how the price would differ for an adjacent strike, all else equal. For the one-month at-the-money call above the model prints a dual delta of −0.5098 — a call is worth less at a higher strike, so the sign is negative, and its magnitude is the discounted risk-neutral in-the-money probability exp(−rT)·N(d₂). The dual delta is rarely traded on directly, but it is the natural language for the slope of value along the strike axis and it makes precise what "the next strike up is cheaper" means; it reappears wherever one reasons across a strip of strikes rather than along a single contract's path.

## 4 Theta

Theta is the greek traders feel most viscerally — the daily bleed on a long option, the daily drip into a short one. It is the slope of value in time, and its shape is entirely a story about where an option's optionality is worth the most.

### 4.1 Time decay across moneyness and maturity

Theta is the derivative of value with respect to the passage of time,

Θ = ∂V/∂t,

conventionally quoted per calendar day, so that "theta = −0.04" means the option loses four cents of value per day, all else equal. Under Black–Scholes–Merton the call theta is

Θ_call = −(S · exp(−qT) · φ(d₁) · σ) / (2√T) − r · K · exp(−rT) · N(d₂) + q · S · exp(−qT) · N(d₁),

quoted per year and divided by 365 for a per-day figure; the put differs only in the sign of the rate and carry terms. For a long option theta is negative (time is the enemy); for a short option it is positive (time is the ally). The theta panel of Figure 1 shows the shape: decay is largest, in absolute terms, for at-the-money options and tapers toward zero deep in- or out-of-the-money, and it *accelerates* as expiry approaches. The model prints at-the-money theta of −0.027 per day at three months, −0.043 at one month, and −0.083 at one week — the daily bleed roughly triples as the option's life shortens from a quarter to a week.

The shape has an intuitive reading. An option's extrinsic value is the price of optionality, and optionality is worth most when the outcome is genuinely uncertain — which is precisely at the money. Deep in- or out-of-the-money the outcome is nearly settled, there is little optionality left to decay, and theta is small. And the closer expiry, the faster the remaining optionality evaporates, because there is less and less future in which the underlying can surprise you. The famous "theta curve" — extrinsic value falling ever faster into expiry, roughly like the square root of time remaining for an at-the-money option — is the same phenomenon seen through the option's price rather than its slope.

### 4.2 Theta as a variance clock

The clean calendar-day theta of the model hides a practical complication that matters for anyone holding options over specific dates: *not all days decay equally, because not all days carry the same expected variance.* Time decay is, at bottom, the price of the variance the underlying is expected to generate before expiry, and variance accrues on trading days when the market is open and events resolve — not on quiet calendar days. This is the sense in which theta is a *variance clock* rather than a calendar clock.

The most reliable example is the weekend. A model that decays value smoothly per calendar day implies that an option loses value on Saturday and Sunday just as on a Wednesday. But no variance is realized while the market is closed, so a rational market tends to *pull the weekend decay forward*: implied volatilities and prices soften on Friday afternoon, and the option opens Monday having already given up much of the two-day theta, because everyone knows those two days carry no trading risk (Sinclair 2010; Natenberg 1994). A long-option holder who marks to a naive calendar clock is repeatedly surprised on Monday mornings; a short-premium seller who expects to "collect the weekend" often finds it was already priced out on Friday. Scheduled events invert the same logic: an earnings report or a central-bank decision concentrates a burst of expected variance into a single session, so options spanning it carry an *event premium* — elevated implied volatility that is really extra variance priced into one day — which decays sharply the moment the event resolves, the notorious volatility crush.

The deeper reason theta cannot be fully understood on its own is that it is the price you pay for *curvature*: the negative theta of a long option is the rent on the positive gamma that lets a delta-hedged position profit from motion, and under Black–Scholes–Merton the two are locked together by an identity of the form Θ ≈ −½ · Γ · S² · σ². That identity, and the realized-versus-implied volatility trade it encodes, belong to the greeks-and-hedging paper because gamma is a second-order greek; we note here only that theta is best read as one side of a two-sided trade, and that its variance-clock behavior is the first-order footprint of that deeper accounting.

## 5 Vega

Delta, theta, and rho concern inputs a trader can observe — the underlying, the clock, the rate. Vega concerns the one input nobody observes directly: the volatility the market is pricing in. It is the greek that turns an option position into a position on volatility itself.

### 5.1 Exposure to implied volatility

Vega is the derivative of value with respect to volatility,

Vega = ∂V/∂σ = S · exp(−qT) · φ(d₁) · √T,

conventionally quoted per *vol point* — a one-percentage-point change in implied volatility — which is the per-unit figure above divided by 100. A vega of 0.115 means the option gains about 11.5 cents if implied volatility rises one point, from 20% to 21%. Both calls and puts have *positive* vega — the formula depends on the strike only through d₁, and φ(d₁) is the same for the call and the put at a given strike — because more volatility makes every option more valuable: optionality is worth more when the future is wider. So being long options of any stripe is being long volatility, and being short premium is being short volatility. Mind the units: "vega" in this paper is always per one vol *point,* which is why the numbers look like small fractions; some texts quote it per unit vol, a figure 100 times larger. A greek without its units is not a number, and vega is where that warning bites hardest.

### 5.2 Vega grows with maturity

The defining feature of vega is its maturity dependence. Where delta's carry tilt and theta's acceleration are effects that sharpen near expiry, vega does the opposite: it *grows with time to expiry.* Figure 1 already shows this at the money — vega is 0.056 per point at one week, 0.115 at one month, and 0.197 at three months — and Figure 2 extends the same at-the-money vega out along the maturity axis: 0.276 at six months, 0.381 at one year, and 0.516 at two years. The one-year option carries roughly seven times the vega of the one-week option (a ratio of about 6.9, close to √52 ≈ 7.2).

That factor is not a coincidence: vega scales roughly with the square root of time to expiry, and Figure 2 draws a √T reference curve through the one-year point to make the fit visible. The reason is structural. Implied volatility is quoted as an *annualized* number, and a change in it compounds over the whole remaining life of the option; a longer-dated option simply has more time over which a higher annualized volatility can act, and the standard deviation of the terminal price scales as σ√T. Short-dated options live and die by what the underlying actually does between now and a near expiry; long-dated options live and die by where the market marks implied volatility. The same underlying and strike, at a different maturity, is a different instrument.

### 5.3 Why the wings are a volatility instrument

There is a subtlety in "vega peaks at the money." In *absolute* per-point terms it does: the at-the-money option has the largest vega, and vega falls off toward the wings. But in *relative* terms — vega as a fraction of the option's own premium — the wings are far more vol-sensitive. A deep out-of-the-money option has almost no delta and a tiny dollar theta; essentially its entire premium is time value that exists only because of implied volatility. A one-point move in implied volatility can change such an option's value by a large fraction of what little it is worth. Its price is, to a first approximation, a pure quote on volatility.

This is why the *wings* of the option chain are where the volatility surface actually lives, and it is the natural bridge to the volatility-surface paper. The market does not quote a single volatility; it quotes a different implied volatility for every strike, and the systematic pattern — higher implied volatilities for downside puts than for upside calls in equity indices — is the *skew.* Skew is a statement about the wings, and the wings are the strikes whose value is almost purely vega. A book of options at more than one strike or maturity is therefore not a position on "volatility" as a scalar; it is a position on the *shape* of the volatility surface across strike and maturity. Decomposing vega into exposure to the level, the term structure, and the skew of implied volatility is the subject of the volatility-surface paper; this paper's job is only to establish that vega is the coordinate that decomposition is written in.

![Maturity dependence of at-the-money vega and at-the-money rho for a European call under Black–Scholes–Merton (S=K=100, sigma=20%, r=4%, q=0), from 1 week to 2 years. Vega grows roughly like the square root of time to expiry (dashed reference, anchored at 1 year), from 0.055 per point at one week to 0.516 at two years; rho grows a little faster than linearly, from 0.010 per 1% at one week to 1.027 at two years. Both are the maturity greeks: they scale up with time to expiry rather than concentrating near it. Reproduce with `figures/fig_fo_term_structure.py`.](figures/fig_fo_term_structure.png)

## 6 Rho

Rho is the greek that earns exactly one honest page, because for most of the last two decades it deserved less than that — and because the last two years have quietly made it matter again.

Rho is the derivative of value with respect to the risk-free rate, conventionally quoted per one-percentage-point change in rates,

ρ = ∂V/∂r,

which for a call is K · T · exp(−rT) · N(d₂) and for a put −K · T · exp(−rT) · N(−d₂), each divided by 100 for the per-1% figure. A call has positive rho and a put negative: higher rates raise the forward price of the underlying — the same carry that tilted the at-the-money call delta above one-half in Section 3.2 — and discount the strike you would pay, both of which help a call and hurt a put. Rho grows with maturity, and Figure 2 shows it climbing along the same axis as vega: the at-the-money model rho runs 0.010 per 1% at one week, 0.042 at one month, 0.129 at three months, 0.259 at six months, 0.519 at one year, and 1.027 at two years. Unlike vega, which grows like √T, rho grows a little faster than linearly, because both the discounting of the strike and the forward drift compound over the full life of the option.

For an intraday or even a swing trader in liquid equity options, rho is *negligible,* and the reason is a comparison of speeds. Rates move in increments of a quarter point a few times a year, on a schedule everyone can see; the underlying can move an option's value by more in an hour than a plausible rate change would in a quarter. A day trader who tracks rho is optimizing the fourth decimal while the first is on fire, which is why rho is traditionally taught last and dismissed fastest.

Two honest caveats keep it on the page. First, rho was near-irrelevant through the 2009–2021 zero-rate era not because it is unimportant in principle but because rates simply did not move and sat near zero, so both the sensitivity's input and the forward drift it feeds were tiny. In the post-2022 regime — policy rates moving from near zero to above five percent and back within a couple of years — the carry those rates create is no longer negligible for anyone holding longer-dated options, and the at-the-money delta tilt of Section 3.2 (delta above one-half, growing with maturity) is a direct, visible footprint of exactly that carry. Second, for very long-dated instruments — LEAPS, structured products, anything with years to run — the maturity growth in Figure 2 means rho is a first-order risk that must be hedged like any other; the "ignore it" advice is a statement about short-dated equity options, not a law of nature. The practical posture is conditional: quote rho, know its sign, and check whether your book's maturity and the current rate environment make it a rounding error or a real exposure.

## 7 Lambda: elasticity and leverage

The four greeks so far measure a *dollar* change in value per unit change in an input. Sometimes the more revealing quantity is a *percentage* change — and that is elasticity.

*Lambda* (Λ), also called elasticity or omega, restates delta as a percentage sensitivity:

Λ = Δ · S / V,

the percentage change in the option's value per one-percent change in the underlying. It is delta scaled by the ratio of the underlying's price to the option's price, and it is the honest number behind the word "leverage." A call trading at 2.47 with delta 0.53 on an underlying at 100 has elasticity 0.53 × 100 / 2.47 ≈ 21.6: a one-percent move in the underlying moves the option's value about twenty-two percent. You control roughly a hundred dollars of share-equivalent exposure for two and a half dollars of premium, and lambda is the multiplier that gap creates.

Figure 3 plots lambda across moneyness for a one-month call. The shape is the important thing. Deep in-the-money the option behaves almost like the underlying itself — its price is mostly intrinsic value and its delta is near one — so a one-percent move in the underlying is close to a one-percent move in the option, and lambda drifts toward one. Move toward and then past the strike and lambda *rises,* because the premium in the denominator shrinks far faster than delta does. For the one-month call the model prints lambda 10.1 at 10% in-the-money (S/K = 1.10), 14.6 just in-the-money (1.05), 21.6 at the money, 31.4 at 5% out-of-the-money (0.95), and 43.6 at 10% out-of-the-money (0.90). That last option costs about 0.085 of premium and yet a one-percent move in the underlying swings its value roughly 44 percent — the far-out-of-the-money wing is where an option's built-in leverage is highest.

The honest reading of that leverage is the point of this section. High lambda is not free money; it is high *sensitivity in both directions,* multiplied by a low probability. The same 43-times multiplier that turns a one-percent up-move into a 44-percent gain turns a one-percent down-move into a comparable loss, and — because the option is far out of the money — the most likely outcome is that it decays to zero and the leverage never pays. Lambda measures how much exposure your premium buys; it says nothing about whether that exposure is likely to be rewarded, which is what delta's connection to probability (Section 3.3) and theta's decay (Section 4) are for. Leverage is a description of the payoff's steepness, not a forecast of its sign.

![Elasticity (lambda) across moneyness for a 1-month European call under Black–Scholes–Merton (K=100, sigma=20%, r=4%, q=0), with call delta on the right axis. Lambda = delta*S/price is the percentage change in the option's value per one-percent change in the underlying — its built-in leverage. It drifts toward one deep in the money (where the option tracks the underlying) and rises toward the out-of-the-money wing, reaching about 22 at the money and about 44 at 10% out of the money, because the premium shrinks faster than delta. Reproduce with `figures/fig_fo_leverage.py`.](figures/fig_fo_leverage.png)

## 8 Aggregation and dollar-greeks

A single option's greeks are a warm-up; a real position holds many strikes and expiries, and the only way to manage it is to aggregate. Two facts make that tractable.

The first is that greeks are *additive across positions,* because differentiation is linear. The delta of a book is the sum of the deltas of its positions, each weighted by the signed number of contracts (long positive, short negative) and by the contract multiplier, and the same holds for theta, vega, and rho:

Δ_book = Σ nᵢ · mᵢ · Δᵢ,  Θ_book = Σ nᵢ · mᵢ · Θᵢ,  and so on,

where nᵢ is the signed contract count of position i and mᵢ its multiplier. This linearity lets a desk holding hundreds of lines report a single net delta and hedge the aggregate — one trade in the underlying, not one per line. The honest caveat is that additivity is exact only when every greek is evaluated at the same inputs and interpreted consistently: adding a one-week vega to a one-year vega gives an arithmetically correct sum that hides two very different exposures, which is why desks look at greeks not only as book totals but as profiles across strike and maturity.

The second fact is that raw greeks come in mixed and awkward units and are not comparable across underlyings of different price levels. The fix is *dollar-greeks,* which restate each greek as the P&L impact of a standardized move (Hull 2022). The most common is *dollar delta* — the dollar value of the underlying you are effectively long or short:

dollar delta = Δ_book · S · m,

with m the contract multiplier. It answers "how many dollars of the underlying am I really holding?" and it is the number a risk report leads with, because it is directly comparable across a portfolio of different names and directly hedgeable with a single position in each underlying. The same restatement applies to the other greeks and to the second-order quantities — dollar gamma above all — that the dealer-flows-and-GEX paper builds its estimates on; here the point is only that additivity plus a common currency turns a book of options into a short, readable vector of net exposures.

## 9 Worked examples in Python

Everything above can be computed from scratch in a few dozen lines of standard-library Python — no pricing library, no `scipy`, just `math`. The normal density and cumulative function are all the special functions we need, and `math.erf` supplies the latter with no dependency; everything else is the closed forms differentiated in the earlier sections.

```python
import math

SQRT2PI = math.sqrt(2.0 * math.pi)
def npdf(x): return math.exp(-0.5 * x * x) / SQRT2PI            # standard normal pdf
def ncdf(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))  # standard normal cdf

def first_order_greeks(S, K, T, r, sigma, q=0.0, call=True):
    """BSM price and first-order greeks. vega per vol POINT; theta per CALENDAR
    DAY; rho per 1% rate. call=True -> call, False -> put."""
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    dq, dr = math.exp(-q * T), math.exp(-r * T)
    s = 1.0 if call else -1.0
    price = s * (S * dq * ncdf(s * d1) - K * dr * ncdf(s * d2))
    delta = s * dq * ncdf(s * d1)
    vega  = S * dq * npdf(d1) * sqrtT / 100.0
    theta = (-S * dq * npdf(d1) * sigma / (2 * sqrtT)
             - s * r * K * dr * ncdf(s * d2)
             + s * q * S * dq * ncdf(s * d1)) / 365.0
    rho   = s * K * T * dr * ncdf(s * d2) / 100.0
    dual  = -s * dr * ncdf(s * d2)          # dual delta, dV/dK
    # elasticity (leverage); undefined once the BSM price underflows toward 0
    # deep out-of-the-money, so guard the division instead of crashing there
    lam   = delta * S / price if price > 1e-12 else float("nan")
    return dict(price=price, delta=delta, vega=vega, theta=theta,
                rho=rho, dual_delta=dual, elasticity=lam)

if __name__ == "__main__":
    g = first_order_greeks(S=100, K=100, T=21/252, r=0.04, sigma=0.20)
    for k in ("price", "delta", "theta", "vega", "rho", "dual_delta", "elasticity"):
        print(f"{k:11s} {g[k]:+.4f}")
```

Run on a one-month at-the-money call (S = K = 100, T = 21/252, r = 4%, σ = 20%), it prints a price of +2.4694, delta +0.5345, theta −0.0433, vega +0.1147, rho +0.0425, a dual delta of −0.5098, and an elasticity of +21.65 — matching, to the precision quoted, the Figure 1 values (delta 0.535, theta −0.043, vega 0.115, rho 0.042) and the Figure 3 elasticity (21.65). Flip `call=False` and the same function returns the put's delta of −0.4655 and rho of −0.0406, the mirror images of the call. The point of reproducing the numbers here from a self-contained function is that you can change one input and watch the whole first-order risk vector move: shorten T and theta deepens while vega and rho shrink; raise σ and every greek's shape widens around the strike. The four greeks are not four unrelated formulae — they are four slopes of the *same* surface, and this function evaluates all of them at once. The figure scripts named in the captions go one step further and check each closed form against a central finite difference of the price, printing a worst-case relative error on the order of 1e-6, so the plotted curves are provably the derivatives they claim to be. One guard is worth naming because it bites exactly where the crisis-insurance paper lives: elasticity is delta·S/price, and for a deep out-of-the-money "one-delta" option the Black–Scholes price underflows toward zero, so the ratio is undefined; the function returns NaN there rather than dividing by zero.

## 10 Common misconceptions and glossary

### 10.1 Common misconceptions

- **"Delta is the probability of finishing in the money."** A useful shorthand that is systematically too high (delta is N(d₁), the risk-neutral probability is N(d₂), and they differ by about σ√T), risk-neutral rather than real-world, and a hedge ratio rather than a probability. Safe for short-dated near-the-money options; misleading for long-dated or high-vol ones, and never a thing to do arithmetic on (Section 3.3).
- **"An at-the-money option has delta 0.50."** Only with zero carry. With a positive rate the forward sits above spot and the at-the-money-spot call delta runs about 0.52–0.56, growing with maturity — a visible footprint of rho (Section 3.2, Section 6).
- **"Theta is a smooth daily bleed."** Theta tracks *variance,* which accrues on trading days and around events, not evenly across the calendar. Weekends decay early and event premium crushes on resolution (Section 4.2).
- **"Vega is the same for a one-week and a one-year option."** No — vega grows roughly like √T, so a one-year option can carry seven times the vega of a one-week option at the same strike. Short-dated options are barely vega instruments; long-dated ones are almost entirely vega (Section 5.2).
- **"Rho never matters."** True for short-dated equity options in a quiet-rate world; false for long-dated instruments, and false again in a regime where policy rates swing five points in two years (Section 6).
- **"High lambda means easy money."** Elasticity measures how much exposure your premium buys, in both directions, multiplied by a low probability of paying off; it is the steepness of the payoff, not a forecast of its sign (Section 7).
- **"The greeks describe my option."** For a single position, yes; but greeks *aggregate,* and the object a desk actually manages is the net dollar-greek vector of a whole book (Section 8).

### 10.2 Glossary

- **Delta (Δ)** — ∂V/∂S. Share-equivalent exposure and hedge ratio; about 0 to +1 for calls, −1 to 0 for puts.
- **Theta (Θ)** — ∂V/∂t. Time decay, quoted per calendar day; largest at the money and accelerating into expiry; tracks variance, not the calendar.
- **Vega** — ∂V/∂σ. Sensitivity to implied volatility, per vol point; positive for all options; grows roughly like √T with maturity.
- **Rho (ρ)** — ∂V/∂r. Sensitivity to the risk-free rate, per 1%; positive for calls, negative for puts; grows with maturity.
- **Lambda (Λ)** — Δ·S/V. Elasticity or leverage; the percentage change in value per one-percent change in the underlying; highest far out of the money.
- **Dual delta** — ∂V/∂K. Sensitivity of value to the strike; −exp(−rT)·N(d₂) for a call, +exp(−rT)·N(−d₂) for a put.
- **Moneyness** — the position of spot relative to strike, here S/K; drives the shape of every greek.
- **Implied volatility** — the volatility that, put into Black–Scholes–Merton, reproduces the market price of an option; the input vega is a sensitivity to.
- **d₁, d₂** — standardized log-moneyness in the pricing formula; d₁ = d₂ + σ√T; N(d₂) is the risk-neutral in-the-money probability.
- **φ, N** — the standard normal probability density and cumulative distribution functions.
- **Delta-neutral** — a book whose net delta is about zero, so it is directionally flat for the *next small move* only.
- **Dollar delta** — delta restated as the dollar value of the underlying you are effectively long or short: Δ·S·multiplier.
- **Carry (q)** — a continuous dividend or cost-of-carry yield on the underlying; set to zero in this paper's figures unless stated.
- **Volatility crush** — the sharp fall in implied volatility, and thus option value, when a scheduled event resolves and its variance premium is realized.

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| First-order greek profiles: delta S-curve (at-the-money 0.517/0.535/0.560), theta −0.027/−0.043/−0.083; closed forms checked against finite differences to ~1e-6 | Own reproducible computation — `figures/fig_fo_first_order.py` |
| Across maturity, at-the-money vega grows ~√T (0.055 to 0.516) and rho faster than linearly (0.010 to 1.027) | Own reproducible computation — `figures/fig_fo_term_structure.py` |
| Elasticity (lambda) rises from ~21.6 at the money to ~43.6 at 10% out of the money | Own reproducible computation — `figures/fig_fo_leverage.py` |
| Black–Scholes–Merton closed-form price; the greeks are its exact partial derivatives | Literature — (Black & Scholes 1973; Merton 1973) |
| The greeks are the terms of a first-order Taylor expansion of the price | Literature — (Hull 2022) |
| BSM's constant-vol assumptions are false; the volatility smile is the market's own admission | Literature — (Natenberg 1994; Sinclair 2010) |
| Delta N(d₁) systematically exceeds the in-the-money probability N(d₂) by about σ√T | Literature — (Hull 2022; Natenberg 1994) |
| Theta is a variance clock: weekend decay is pulled forward and event premium crushes on resolution | Literature — (Sinclair 2010; Natenberg 1994) |

## References

- Black, F., & Scholes, M. (1973). The pricing of options and corporate liabilities. *Journal of Political Economy, 81*(3), 637–654.
- Haug, E. G. (2007). *The Complete Guide to Option Pricing Formulas* (2nd ed.). New York: McGraw-Hill.
- Hull, J. C. (2022). *Options, Futures, and Other Derivatives* (11th ed.). Harlow: Pearson.
- Merton, R. C. (1973). Theory of rational option pricing. *The Bell Journal of Economics and Management Science, 4*(1), 141–183.
- Natenberg, S. (1994). *Option Volatility and Pricing: Advanced Trading Strategies and Techniques* (2nd ed.). New York: McGraw-Hill.

*All references above are publicly accessible: two are peer-reviewed journal articles and three are published books widely held in libraries and in print. No proprietary, course, or trading-academy material is cited, and no licensed or vendor data is used anywhere in this paper.*
