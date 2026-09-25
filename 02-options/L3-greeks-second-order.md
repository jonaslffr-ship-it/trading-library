---
title: "Second-Order Greeks — Gamma, Vanna, Charm, Vomma"
last_updated: 2026-09-25
---

# Second-Order Greeks — Gamma, Vanna, Charm, Vomma

## Abstract

The first-order greeks say how an option's value moves; the second-order greeks say how the *hedge* moves, and that is the question a hedger actually loses sleep over. This paper treats gamma, vanna, charm, and vomma as the sensitivities of the first-order greeks — the terms that make today's delta-hedge go stale for reasons other than the underlying moving. We organize them around one equation, dΔ = Γ·dS + vanna·dσ + charm·dt: delta drifts through a price channel, a volatility channel, and a time channel, and each channel forces a re-hedge. We derive every closed form from Black–Scholes–Merton, flag where its constant-volatility assumption understates the vol-sensitive greeks, and read charm and vanna as tomorrow's pre-scheduled, computable-in-advance hedging flows for a large book — positioning information, not a prediction. Vomma is developed as vega convexity and the bridge to the volatility surface; veta and vera each get one honest paragraph. Every greek is verified against a central finite difference, and every quoted number and figure is reproducible from the accompanying didactic code on no market data.

## Keywords

Gamma, vanna, charm, vomma, volga, veta, vera, second-order greeks, cross-gamma, Black–Scholes–Merton, dollar gamma, delta decay, vega convexity, vol-of-vol, dealer hedging, forced hedging flow, Taylor expansion, finite-difference verification, moneyness, option sensitivities

## 1 Introduction

### 1.1 Motivation and thesis

A hedger's day is a sequence of small repairs. You sold a book of options, you neutralized its delta with the underlying this morning, and you would like to believe you are flat. You are not — not for long, and not only for the obvious reason. The obvious reason is that the underlying will move, and a delta-hedge is a straight-line approximation to a curved payoff, so any move leaves you exposed. But there are two more reasons, and they are the ones that catch people out: your delta will change *even if the underlying does not move at all*, because a day will pass and because the market's estimate of volatility will shift. Three different forces are quietly pulling your hedge off-true, and only one of them is the price.

The thesis of this paper is that the second-order greeks are the exact names of those forces, and that the cleanest way to hold them in one's head is a single equation for how a hedge decays:

dΔ = Γ·dS + vanna·dσ + charm·dt.

Read it as a sentence. Your delta — the thing you hedged — drifts by three separate channels. It drifts because the price moved (that is gamma). It drifts because implied volatility moved (that is vanna). And it drifts because time passed (that is charm). Each term is a partial derivative of delta, each is a second derivative of the option value, and each forces a trade in the underlying to stay hedged. A fourth greek, vomma, is the same idea applied to vega rather than delta — the convexity that makes a volatility move nonlinear — and two more, veta and vera, close out the second-order table. Where the first-order greeks are a description of the risk you *carry*, the second-order greeks are a schedule of the trades you will be *forced to make*, and that shift — from risk you hold to trades you owe — is why they are worth a paper of their own. It is also why they are the mechanical heart of the dealer-flows-and-GEX paper: a market maker who has sold the street its optionality inherits the mirror image of every drift term here, and the forced re-hedging those terms generate is what presses on index markets around expiry.

### 1.2 Scope, prerequisites, and intended reader

This paper is self-contained. It assumes only that the reader has met the first-order greeks — that delta is an option's sensitivity to the underlying and doubles as a hedge ratio (roughly 0 to +1 for a call, −1 to 0 for a put), that gamma, theta, and vega exist as the sensitivities to the underlying, to time, and to implied volatility — and that the reader is comfortable reading a first partial derivative and a short Python snippet. Everything used beyond that bare vocabulary is re-introduced here from its definition: d₁, d₂, the normal density and cumulative function, dollar-greeks, the Taylor expansion of the price, and each second-order greek's closed form. No stochastic calculus is required, and the Black–Scholes–Merton equation is used, never derived. Where a first-order greek is needed as a reference point — delta's S-curve, gamma's concentration at the money — it is stated in a line rather than assumed as prior reading, so a reader who knows the greeks *exist* but not in detail can still follow every step.

After reading this paper, a reader can:

- write each second-order greek as a partial derivative of a first-order greek in one sentence, and give its sign and rough magnitude across moneyness and maturity;
- use the decay equation dΔ = Γ·dS + vanna·dσ + charm·dt to say, for a given position, which way and how far a hedge will drift when the price, the volatility, or the calendar moves;
- explain why charm makes tomorrow's re-hedge *computable today*, and why vanna's flow depends on the *shape* of a volatility move and not only its size;
- read vomma as vega convexity, locate it in the wings, and see why a naked short-wing position is hit twice by a volatility spike;
- state honestly where veta and vera matter and where they are rounding errors;
- aggregate the drift terms across a book and read them as pre-scheduled hedging flow, while keeping the epistemics straight — this is positioning information, not a forecast;
- and reproduce every number and figure from the accompanying code, each greek cross-checked against a finite difference.

### 1.3 Data and reproducibility

Every figure and every printed number in this paper is a self-contained Black–Scholes–Merton computation that uses no market data at all: the inputs are stated (a strike or spot of 100, an implied volatility of 20%, a risk-free rate of 4%, and zero carry unless a figure says otherwise), and the output is a deterministic function of those inputs. Each figure names the script that builds it, and each quoted quantity is printed to standard output by that script, so nothing in the text is a number typed by hand. Because these greeks are error-prone to code — sign conventions, per-point versus per-unit-vol scaling, per-day versus per-year time — every second-order greek is verified against a central finite difference of the corresponding first-order closed form, and the maximum relative error is printed alongside; the checks here pass to better than one part in a million. Where a convention could go two ways it is stated, because a greek quoted without its units is not a number. *This is a research and educational document, not investment advice.*

### 1.4 Organization of this paper

This paper is complete: every section below is written in full, with no forthcoming stubs. The arc runs from the machinery to the meaning.

- **Section 2** builds the second-order greeks from the Taylor expansion, defines d₁, d₂, φ, and N, and flags exactly where the constant-volatility ruler of Black–Scholes–Merton understates the vol-sensitive greeks.
- **Section 3** treats gamma as the hedger's unavoidable error term, connects it to realized-minus-implied volatility, and defines dollar gamma and the sign that seats dealer flow (Figure 1).
- **Section 4** develops vanna — volatility changing your delta with the spot unmoved — its sign flip across the strike, and the skew caveat.
- **Section 5** develops charm — delta decay through time — as the one flow term computable in advance, and shows its sign map and violent growth into expiry (Figure 2).
- **Section 6** develops vomma as vega convexity, near zero at the money and large in the wings, and bridges to the volatility-surface paper (Figure 3).
- **Section 7** gives veta and vera one honest paragraph each.
- **Section 8** aggregates the drift terms into a book's forced trades and reads them as positioning, deferring the market-impact story to the dealer-flows-and-GEX paper.
- **Section 9** computes every greek from scratch in Python and self-checks each against a finite difference.
- **Section 10** collects misconceptions and a glossary, and Section 11 the references.

## 2 Why second-order greeks exist

### 2.1 A hedge is a truncated Taylor series

The value of a European option is a function of the underlying S, the calendar time t, the implied volatility σ, and the rate r, with strike K and carry q as fixed contract parameters. To ask how that value changes when the world moves a little is to write its Taylor expansion around today's inputs, and to go to *second* order is to keep the terms a first-order hedge leaves behind:

dV ≈ Δ·dS + Θ·dt + Vega·dσ + ½·Γ·dS² + ½·Vomma·dσ² + Vanna·dS·dσ + Charm·dS·dt + Veta·dσ·dt + …

The first three terms are the first-order greeks — the slopes in price, time, and volatility. Everything after them is second order: the pure curvatures ½·Γ·dS² and ½·Vomma·dσ² (note the one-half, the signature of a second derivative in a single variable), and the *cross* terms Vanna·dS·dσ, Charm·dS·dt, and Veta·dσ·dt (which carry no one-half, because they are mixed partials). A delta-hedge sets out to cancel the Δ·dS term. The moment it does, the leading survivor is ½·Γ·dS² — quadratic in the move, and therefore never negative in expectation no matter which way the underlying goes — and right behind it are the cross terms that couple the price to volatility and to time. Second-order risk is simply *what a first-order hedge cannot reach.*

There is a more useful way to see the same fact, and it is the organizing idea of this paper. Instead of expanding the value, expand the *hedge*. Delta is itself a function of S, σ, and t, so its own first-order change is

dΔ = (∂Δ/∂S)·dS + (∂Δ/∂σ)·dσ + (∂Δ/∂t)·dt = Γ·dS + vanna·dσ + charm·dt.

This is the equation from the introduction, now earned. The three second-order greeks that matter most for hedging are precisely the three partial derivatives of delta: gamma is delta's price channel, vanna its volatility channel, charm its time channel. And the same construction applied to vega gives its companion trio,

dVega = (∂Vega/∂S)·dS + (∂Vega/∂σ)·dσ + (∂Vega/∂t)·dt = vanna·dS + vomma·dσ + veta·dt,

where vanna reappears (it is both ∂Δ/∂σ and ∂Vega/∂S, the two readings of a single mixed partial), vomma is vega's convexity in volatility, and veta is vega's decay in time. Every named second-order greek in this paper is one entry in these two equations.

> **First-order greeks are risks you hold; second-order greeks are trades you owe.** A gamma is not a number you carry passively — it is a promise that the next price move will leave your delta wrong by Γ·dS, which you will have to trade out of. A charm is a promise that tomorrow's open will find your delta wrong by charm·dt whether or not anything happened overnight. Reading the second-order greeks as the *rate at which your hedge goes stale* turns them from a table into a to-do list.

### 2.2 The ingredients: d₁, d₂, φ, and N

Every closed form below is assembled from the same handful of quantities, so we fix them once. Under Black–Scholes–Merton with continuous carry q, define

d₁ = [ ln(S/K) + (r − q + ½σ²)·T ] / (σ√T),  d₂ = d₁ − σ√T,

where T is the time to expiry in years. Write φ(x) = exp(−x²/2)/√(2π) for the standard normal probability density and N(x) for its cumulative distribution. Two discount factors recur: D_q = exp(−qT) for the carry and D_r = exp(−rT) for the rate. With these, the call price is C = S·D_q·N(d₁) − K·D_r·N(d₂), and every greek in this paper is a partial derivative of that expression, evaluated in closed form. Because the ingredients are shared, the greeks are not nine unrelated formulae; they are nine ways of combining φ(d₁), d₁, d₂, and the discount factors.

### 2.3 The ruler is straight where the world is curved

Black–Scholes–Merton earns its place as the industry's coordinate system not because it is true but because it is a stable, shared *ruler* for translating between an option's price and its risk: traders take each option's market price, invert the formula for the implied volatility that reproduces it, and read the greeks at that implied vol. The model is a bad forecaster and an excellent ruler — with one caveat that lands squarely on this paper. Its defining assumption is that volatility is *constant*. That is exactly the assumption every vol-sensitive greek here is about violating. Vanna is the rate at which your delta changes when volatility moves; vomma is the rate at which your vega changes when volatility moves; a model that swears volatility never moves is, by construction, telling you these numbers with a straight face while denying the event they describe.

The practical consequence is a known, one-directional bias: the constant-volatility model systematically *understates* the greeks that depend on volatility being alive. A stochastic-volatility or local-volatility model, calibrated to the smile, produces fatter vanna, charm, and vomma than the flat-vol formulas below, because it lets volatility co-move with the underlying and with time (Natenberg 1994; Taleb 1997). So the figures in this paper are honest about their *structure* — the signs, the sign flips across the strike, the explosive growth into expiry — and deliberately conservative about their *magnitudes*. When we later read these greeks as dealer-hedging flow, this is the caveat that matters most: the flat-vol numbers are a floor, not an estimate, and the direction in which reality departs from them is always toward *more* second-order flow, not less.

## 3 Gamma: the curvature a delta-hedge cannot reach

### 3.1 Convexity as the unavoidable error term

Gamma is the second derivative of value in the underlying, equivalently the first derivative of delta:

Γ = ∂²V/∂S² = ∂Δ/∂S,  with the closed form  Γ = D_q·φ(d₁)/(S·σ·√T).

It is identical for a call and a put (the two differ by a linear term in S, which has zero second derivative), and it is always positive for a long option. Its meaning is the price channel of the decay equation: for every point the underlying moves, your delta changes by Γ, so a delta-hedge set this instant is wrong by Γ·dS the instant after. Gamma is the curvature that a straight-line hedge approximates away, and the residual ½·Γ·dS² is the error that survives — quadratic, so it does not care which direction the underlying took. Long gamma (owning options) is therefore a bet on *motion in either direction*: each round trip of the underlying lets you re-hedge buy-low-sell-high and bank a small profit, the practice called gamma scalping. Short gamma is the mirror, forcing you to buy high and sell low on every re-hedge, bleeding on each oscillation.

That bleed is not free money for the long side, because gamma is paid for through theta, and the two are locked by the identity Θ ≈ −½·Γ·S²·σ² (in the zero-rate case). Reading the two together, the daily profit of a delta-hedged position collapses to a single contest — ½·Γ·S²·(σ²_realized − σ²_implied)·dt — so that a long-gamma book earns exactly when the underlying realizes more volatility than the implied it paid, and loses when it realizes less. This realized-minus-implied engine is developed in full in the greeks-and-hedging paper; here it is enough to see that gamma is the greek through which that contest is fought, and that its sign decides whether motion pays you or costs you.

### 3.2 Where gamma lives: at the money, into expiry

Gamma is not spread evenly across strikes or maturities; it *piles up* at the money and *spikes* as expiry approaches. Figure 1 shows both faces of this — a surface over strike and maturity, and a set of profiles across moneyness at one week, one month, and three months. At the money the model prints gamma of 0.0688 at one month, rising to 0.1415 at one week and falling to 0.0191 at one year: the one-week option carries roughly 7.4 times the gamma of the one-year option for the same notional. Push closer to expiry and the pile becomes a spike — at two days to expiry the at-the-money gamma is 0.2694, and it diverges without bound as T → 0. Away from the money gamma collapses toward zero in both directions, so an option's entire convexity is packed into an ever-narrowing band around the strike as the clock runs down. This geometry — enormous, spiky gamma concentrated exactly where the market is trading in the last sessions before a large expiry — is the seed of the whole dealer-flow story.

![Gamma for a European option under Black–Scholes–Merton, K/spot=100, sigma=20%, r=4%, q=0; left, a surface over strike and maturity for a fixed spot; right, profiles across moneyness at one week, one month, and three months. Gamma concentrates at the money and spikes into expiry, reaching 0.2694 at two days versus 0.0191 at one year. Reproduce with figures/fig_so_gamma_surface.py.](figures/fig_so_gamma_surface.png)

### 3.3 Dollar gamma and the sign that seats dealer flow

Raw gamma is in awkward units (delta per point) and is not comparable across underlyings of different price levels, so desks restate it as *dollar gamma* — the change in dollar delta for a one-percent move in the underlying:

dollar gamma = Γ·S²·(multiplier)/100.

For the one-month at-the-money option above, with a 100-contract multiplier, dollar gamma is Γ·S²·100/100 = 0.0688·100²·1 = about \$688 per one-percent move. In words: if the index moves one percent, this single position's directional exposure shifts by roughly \$688 of underlying, which is the size of the re-hedge that move forces. Dollar gamma is the quantity the entire dealer-gamma literature is built on, and its *sign* is the whole game. A trader who is long options is long gamma and re-hedges *against* the move — selling into rallies, buying into dips — which damps price and pins it toward the strikes where the gamma sits. A dealer who has *sold* those options is short that gamma and re-hedges *with* the move — buying rallies, selling dips — which amplifies price and feeds momentum. Which regime the market is in is a question about the sign and location of the *aggregate* dealer book, not about any single option; this paper builds the quantity and stops at its definition, and the dealer-flows-and-GEX paper estimates the aggregate sign from public open-interest data and tests whether it moves index prices.

## 4 Vanna: volatility changes your delta

### 4.1 The delta that moves while the spot stands still

Vanna is the mixed second derivative of value in the underlying and in volatility, and it has two readings that are the same number:

vanna = ∂²V/(∂S·∂σ) = ∂Δ/∂σ = ∂Vega/∂S,  with the closed form  vanna = −D_q·φ(d₁)·d₂/σ

per unit of volatility (divide by 100 for a per-vol-point quote, the convention used in every number below). The reading that matters for a hedger is the first: *when implied volatility changes, your delta changes, even though the underlying has not moved.* A book that closed perfectly delta-neutral can open un-hedged after an overnight two-point drop in implied vol, with vanna the entire cause — the volatility channel of the decay equation, dΔ = … + vanna·dσ + …, silently handing you a delta to trade out of. This is the leakage of vega into delta: the same mixed partial that says "your delta depends on vol" also says "your vega depends on the spot," and it is why a vega exposure, which a desk normally offsets with *other options*, can nonetheless land as buying or selling in the *underlying* the moment vol moves.

### 4.2 The sign flip and the pull toward the center

Vanna's sign is the interesting part, and it flips across the strike. The left panel of Figure 2 (Section 5) maps it: for a call, vanna is *positive* below the strike (out of the money) and *negative* above it (in the money), passing through roughly zero at the money. The model makes this concrete — at thirty days, call vanna is +0.01246 per vol point at S/K = 0.95, essentially zero at the money (−0.00057, a small negative set by the carry term), and −0.01131 at S/K = 1.05. The mechanism is intuitive once named: raising implied volatility from a low base widens the distribution of where the underlying might finish, which pulls an out-of-the-money call's delta *up* (positive vanna) and an in-the-money call's delta *down* (negative vanna), narrowing the gap between them. Over the range of volatilities that matter in practice both move toward ½, and vanna is the rate of that blurring. But ½ is a waypoint, not an attractor: push volatility high enough and both deltas are pulled *back* toward 1 (for a non-dividend call d₁ ≈ ½σ√T → +∞, so N(d₁) → 1), so an in-the-money call's delta bottoms out well above one-half — around 0.63–0.74 for a moderately in-the-money strike — rather than settling on it. More volatility blurs the distinction between in and out of the money; it does not erase it.

### 4.3 The skew caveat: a real vol move is not uniform

There is a caveat here that the constant-volatility ruler hides, and it is not pedantic — it changes the flow reading in Section 8. The closed form for vanna assumes that when volatility moves, it moves *uniformly*: every strike's implied vol shifts by the same dσ. Real volatility moves are nothing like that. In equity indices a sell-off steepens the skew — downside puts bid up far more than upside calls — and a rally flattens it, and the term structure twists at the same time. So the *aggregate* vanna flow a book actually experiences depends on *how* the surface moved, not merely on how far the overall level moved: a two-point rise in at-the-money vol accompanied by a skew steepening delivers a different delta shock than a parallel two-point rise. The flat-vol vanna is the right first-order object and the wrong last word; it tells you the direction and rough size of the delta the book will inherit from a vol move, and the volatility-surface paper is where the shape of that move — level, term structure, skew — is taken apart.

## 5 Charm: delta decays through time

### 5.1 The one flow term you can compute in advance

Charm — also called delta decay — is the mixed second derivative of value in the underlying and in time, the time channel of the decay equation:

charm = ∂²V/(∂S·∂t) = ∂Δ/∂t = ∂Θ/∂S.

Its closed form carries a carry piece and a main piece; for a call and a put respectively,

charm_call = q·D_q·N(d₁) − D_q·φ(d₁)·(2(r−q)T − d₂·σ√T)/(2Tσ√T),
charm_put = −q·D_q·N(−d₁) − D_q·φ(d₁)·(2(r−q)T − d₂·σ√T)/(2Tσ√T),

quoted per year and divided by 365 for a per-calendar-day figure. Charm is what makes an out-of-the-money option's delta bleed toward zero as expiry nears (it is running out of time to reach the strike) and an in-the-money option's delta drift toward one (its fate is increasingly settled). What distinguishes charm from the other two drift channels is decisive for the flow story: it needs *no market move at all*. Gamma acts only when the price moves and vanna only when vol moves, but charm acts simply because the clock ticks. That makes tomorrow's charm-driven re-hedge *deterministic and computable today* — a hedger can calculate before the close exactly how much delta a flat overnight will hand them by the open, and pre-place the trade. It is the most predictable of the forced flows.

### 5.2 The sign map and the violence into expiry

Like vanna, charm flips sign across the strike, and the right panel of Figure 2 maps it: for a call, charm is *negative* below the strike (delta drifting down toward zero) and *positive* above it (delta drifting up toward one). At thirty days the model prints charm of −0.00470 per day at S/K = 0.95 and +0.00328 at S/K = 1.05. The number that matters most, though, is how charm *grows into expiry* — and it grows violently. Tracking a call just below the strike at S/K = 0.97, the model prints charm of −0.00372 per day at thirty days, −0.00909 at fourteen days, −0.01823 at seven days, and −0.02887 at three days: a 7.8-fold increase in magnitude over the last month of the option's life, most of it in the final week. Delta decay is a trickle a month out and a flood in the last sessions. This is why a dealer's charm hedging concentrates into the end of the day and the end of the expiry cycle, and why it is largest exactly when the most open interest sits near the money in the final sessions before a monthly or weekly expiration — the calendar-locked pressure that the dealer-flows-and-GEX paper is built on.

![Sign maps of the two delta-drift greeks for a European call under Black–Scholes–Merton (K=100, sigma=20%, r=4%, q=0): vanna (delta change per +1 vol point) and charm (delta change per calendar day) across moneyness and days to expiry, with the zero contour drawn solid and red positive, blue negative. Both flip sign across the strike and grow sharply into expiry, the out-of-the-money charm reaching about −0.018 per day at seven days. Reproduce with figures/fig_so_vanna_charm.py.](figures/fig_so_vanna_charm.png)

## 6 Vomma: vega has convexity

### 6.1 The vega of your vega

Vomma — equivalently volga — is the second derivative of value in volatility, the vol channel of the vega equation:

vomma = ∂²V/∂σ² = ∂Vega/∂σ,  with the closed form  vomma = Vega·d₁·d₂/σ.

Because it is built on Vega (itself per vol point in this paper), vomma is quoted here as the change in *per-point vega per additional vol point* — the vega of your vega, the curvature of the option in volatility. Its sign lives entirely in the product d₁·d₂. At the *forward*-at-the-money strike d₂ = −d₁ and the product is exactly negative; but at the *spot*-at-the-money strike used here, with r = 4%, both d₁ (≈ +0.12) and d₂ (≈ +0.04) are slightly *positive*, so their product is small and positive — and since vega is at its peak and locally flat in vol, vomma is near zero and (barely) positive: the model prints only +0.00004 at the money for a sixty-day option at 20% vol. The distinction matters because it is the only thing that reconciles the sign of the printed number with the formula: d₂ = −d₁ holds at r = q = 0 (or at the forward), not at the spot strike when rates are positive. Move into either wing and d₁ and d₂ eventually share a sign, the product turns solidly positive, and vomma climbs — the same option prints +0.00539 at S/K = 0.90 and +0.00605 at S/K = 1.10, with the right-wing peak near S/K = 1.12. Vomma is a wing phenomenon: near zero where vega is largest, largest where vega is small.

### 6.2 The short-wing double hit, and vol-of-vol

The practical bite of vomma is an asymmetry that has ended many short-premium accounts. A trader who is long wing options is long vomma; one who is short the wings is short vomma, and short vomma is negatively convex in volatility. When a volatility spike arrives, the short-wing position is hit *twice*: once by the direct vega loss as vol rises, and again because vomma makes vega itself grow *against* the position as vol rises, so each further point of the spike hurts more than the last. Losses accelerate rather than accumulate linearly. This is the mechanism behind the classic "picking up pennies in front of a steamroller" blow-up, and it is why vomma is the greek that responds to *vol-of-vol* — the volatility of volatility itself. A market that expects volatility to be jumpy bids up the wings and steepens the smile, and vomma is where that expectation is priced. Note the magnitude also *falls* as base vol rises — the same option prints wing vomma near +0.0072 at 15% vol but only +0.0025 at 30% — because higher vol flattens and widens the vega hump. Vomma is second-order and slower-moving than vanna and charm, so it is the junior partner for flow, but it is what turns a large implied-vol move from a linear vega event into a nonlinear one, and it is the direct bridge from these greeks to the curvature of the smile developed in the volatility-surface paper.

![Vomma across moneyness at three implied volatilities for a sixty-day European option under Black–Scholes–Merton (K=100, r=4%, q=0), in units of per-point vega change per +1 vol point. Vomma is near zero at the money and peaks in both wings; higher base volatility lowers and widens the peaks. Reproduce with figures/fig_so_vomma.py.](figures/fig_so_vomma.png)

## 7 Veta and vera: the honest paragraphs

**Veta (∂Vega/∂t)** is the time channel of the vega equation — the rate at which vega decays as the calendar advances — and it is the greek a vega trader needs when holding a volatility position across time rather than trading it intraday. Its closed form is

veta = ∂Vega/∂t = S·D_q·φ(d₁)·√T·[ q + (r−q)·d₁/(σ√T) − (1 + d₁·d₂)/(2T) ],

per year. A word on that formula: it is written here with the sign that matches the calendar-time convention used for theta and charm (value and greeks decaying as *t advances*), and it was verified against a central finite difference of vega before being quoted — the finite-difference check flagged that the commonly tabulated expression carries the opposite sign, corresponding to the derivative with respect to time-*to-expiry*; when the closed form and the finite difference disagreed, we trusted the finite difference (Section 9). For the one-month at-the-money call, veta prints −0.68324 per vol point per year: the option's vega erodes as expiry approaches, which is the vega-side statement of the same fact that made vega grow with maturity in the greeks-and-hedging paper. Veta matters when a book's vega and its calendar are both live — calendar spreads, and any position deliberately long the back and short the front of the term structure — and is otherwise a small, slow term.

**Vera (∂ρ/∂σ)**, sometimes called rhova, is the cross-sensitivity of rho to volatility, equivalently of vega to the rate: ∂²V/(∂σ·∂r). It is the most peripheral greek in this paper and earns a single honest sentence of practical guidance. For the short-dated equity options that dominate this library's flow material it is entirely negligible — rho itself is a rounding error intraday, and its sensitivity to volatility is a rounding error on a rounding error. Vera becomes a real number only for *long-dated* instruments in an environment where both the rate and the volatility can move meaningfully — multi-year options, structured products, LEAPS — where the value depends jointly on discounting and on vol, and the two interact. For everything this paper is aimed at, it is safe to know that vera exists, know that it is ∂ρ/∂σ, and not track it.

## 8 Aggregation and the flow reading

### 8.1 The book's forced trades

A single option's second-order greeks are a warm-up; the object that matters is the *aggregate*. Because differentiation is linear, second-order greeks add across positions exactly as first-order greeks do — the book's gamma is the signed, multiplier-weighted sum of its positions' gammas, and the same for vanna, charm, and vomma. Summing the decay equation over a whole book therefore gives the book's total forced re-hedge:

dΔ_book = Γ_book·dS + vanna_book·dσ + charm_book·dt.

Read term by term, this is a market maker's day written in advance. The charm term is the cleanest: it says that even on a perfectly flat overnight, the book's delta will drift by charm_book·dt by tomorrow's open, and to stay hedged the desk *must* buy or sell a knowable quantity — a trade that can be computed today and is essentially certain to be placed. The vanna term says that when implied vol moves, and it moves every day, the book inherits a further delta of vanna_book·dσ to trade out of, its direction set by the book's sign and the strikes it concentrates at. The gamma term is the one contingent on a price move, but its size and sign are equally knowable in advance. These are not risks in the ordinary sense of "the market might go against me"; they are *pre-scheduled hedging flows*, latent in the shape of the book and released by the mere passage of time and the ordinary drift of volatility.

### 8.2 What the reading is, and what it is not

This is where the constant-volatility caveat of Section 2.3 has to be honored rather than forgotten. The flat-vol charm and vanna surfaces are qualitatively right — the sign flips across the strike and the explosive growth into expiry are robust features that a richer model only sharpens — and they are quantitatively a conservative floor, because a stochastic-vol world produces *more* second-order flow, not less. So the aggregate drift terms are a genuine, computable description of the trades a large hedged book is compelled to make. But two disciplines keep the reading honest. First, the arithmetic is exact only at a shared set of inputs: adding a one-week charm to a one-year charm is arithmetically valid and physically misleading, because the short-dated term will dominate and then vanish while the long-dated one hums quietly — desks read charm and vanna as *profiles* by strike and expiry, not only as book totals. Second, and more important, this flow is *positioning information, not a prediction*. By the time a charm- or vanna-driven re-hedge prints on the tape, it is being placed, not forecast; the second-order greeks tell you the direction and rough size of trades that a hedged community is *obliged* to make, which is valuable precisely because it is mechanical, but it is not a claim about where price will go. Turning this positioning into an estimate of market impact — building the aggregate from public open-interest data and testing whether it actually moves index prices — is the work of the dealer-flows-and-GEX paper; this paper's job is to give that work its greeks and to state their epistemic status plainly.

## 9 Worked examples in Python

Everything above is a few dozen lines of standard-library Python — no pricing library, no `scipy`, just `math`. The function below extends the greeks-and-hedging paper's `bsm_greeks` with veta and returns the full second-order set; the point is not a production pricer but to show that each greek is a specific arithmetic combination of the same φ(d₁), d₁, d₂, and discount factors, and to *check* every one of them.

```python
import math
SQRT2PI = math.sqrt(2.0 * math.pi)
def npdf(x): return math.exp(-0.5 * x * x) / SQRT2PI            # standard normal pdf
def ncdf(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))  # standard normal cdf

def bsm_greeks(S, K, T, r, sigma, q=0.0, call=True):
    """BSM price and greeks. vega/vanna/vomma per vol POINT; theta and charm per
    CALENDAR DAY; rho per 1% rate; veta per vol point per YEAR. sign=+1 call, -1 put."""
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    dq, dr = math.exp(-q * T), math.exp(-r * T)
    s = 1.0 if call else -1.0
    delta = s * dq * ncdf(s * d1)
    gamma = dq * npdf(d1) / (S * sigma * sqrtT)
    vega  = S * dq * npdf(d1) * sqrtT / 100.0
    vanna = -dq * npdf(d1) * d2 / sigma / 100.0
    charm = (q * s * dq * ncdf(s * d1)
             - dq * npdf(d1) * (2 * (r - q) * T - d2 * sigma * sqrtT)
             / (2 * T * sigma * sqrtT)) / 365.0
    vomma = S * dq * npdf(d1) * sqrtT * d1 * d2 / sigma / 10000.0
    veta  = (S * dq * npdf(d1) * sqrtT
             * (q + (r - q) * d1 / (sigma * sqrtT) - (1 + d1 * d2) / (2 * T))) / 100.0
    return dict(delta=delta, gamma=gamma, vega=vega, vanna=vanna,
                charm=charm, vomma=vomma, veta=veta)
```

Run on the one-month at-the-money call (S = K = 100, T = 21/252, r = 4%, σ = 20%), it prints gamma +0.06884, vanna −0.000574, charm −0.000566, vomma +0.0000143, and veta −0.68324 — the near-zero at-the-money vanna, charm, and vomma being the small residuals the carry term leaves at the sign-flip line. Vanna and charm are close here but *not* equal (−0.000574 against −0.000566); they are two different greeks in two different units, and rounding both to −0.00057 would print a coincidence that is not there. The value of coding them from scratch is that each can be *verified*. A second-order greek is a derivative of a first-order greek, so a central finite difference of the corresponding first-order closed form must reproduce it: bump S and difference delta to check gamma, bump σ to check vanna and vomma (the latter differencing vega), bump the calendar to check charm and veta. Each difference is scaled back into the units `bsm_greeks` reports — vol-sensitive greeks per vol point, time greeks per calendar day — so a correct closed form reproduces its return one-for-one:

```python
def self_check(S, K, T, r, sig, h=1e-4):
    """FD each greek in the SAME units bsm_greeks reports: vanna/vomma per vol
    POINT, charm/veta per CALENDAR DAY. Without these scalings the raw natural-
    unit differences sit a factor 100/365/100^2/100 away and the comparison is
    apples to oranges."""
    delta = lambda S, sig, T: bsm_greeks(S, K, T, r, sig)["delta"]
    vega  = lambda S, sig, T: bsm_greeks(S, K, T, r, sig)["vega"] * 100.0   # per unit vol
    gamma_fd = (delta(S + 1e-3, sig, T) - delta(S - 1e-3, sig, T)) / (2e-3)
    vanna_fd = (delta(S, sig + h, T) - delta(S, sig - h, T)) / (2 * h) / 100.0
    charm_fd = -(delta(S, sig, T + 1e-5) - delta(S, sig, T - 1e-5)) / (2e-5) / 365.0
    vomma_fd = (vega(S, sig + h, T) - vega(S, sig - h, T)) / (2 * h) / 100.0 / 100.0
    veta_fd  = -(vega(S, sig, T + 1e-5) - vega(S, sig, T - 1e-5)) / (2e-5) / 100.0
    return gamma_fd, vanna_fd, charm_fd, vomma_fd, veta_fd
```

comparing each closed form to its finite difference over a grid of moneyness and maturities away from the sign flips, the maximum relative error printed by the figure scripts is 4.4 × 10⁻⁷ — better than one part in a million for gamma, vanna, charm, vomma, and veta alike. Two conventions are worth restating because they are where coding errors hide: the vol-sensitive greeks are quoted per vol *point* (a factor of 100, or 100² for vomma, from the per-unit-vol form), and the time derivatives use the calendar-time sign (delta and vega decaying as *t advances*). It was exactly this finite-difference check that caught the veta sign discussed in Section 7: the commonly tabulated closed form differed from the finite difference by a factor of −1, and we kept the finite-differenced sign.

## 10 Common misconceptions and glossary

### 10.1 Common misconceptions

- **"Gamma is the only reason a delta-hedge fails."** Gamma is only the *price* channel. Delta also drifts through the volatility channel (vanna) and the time channel (charm): dΔ = Γ·dS + vanna·dσ + charm·dt. A book can be perfectly gamma-flat and still be handed a delta overnight by vanna and charm alone (Section 2.1, Section 8).
- **"Vanna only matters when the underlying moves."** The opposite — vanna is precisely the delta change when the underlying does *not* move and volatility does. It is the reason a delta-neutral book opens un-hedged after an overnight vol move (Section 4.1).
- **"A vol move just changes my vega."** It also changes your *delta* (vanna) and, through vomma, your *vega itself*. This is why a vega hedged with other options can still generate delta flow in the underlying, and why a short-wing vol spike hits twice (Section 4.1, Section 6.2).
- **"Vomma peaks at the money, like vega."** Vomma is near zero at the money — where vega peaks and is locally flat in vol — and largest in the wings, where d₁·d₂ turns solidly positive (Section 6.1).
- **"Charm is unpredictable, like any hedging need."** Charm is the *most* predictable flow greek: it needs no market move, so tomorrow's charm re-hedge is computable today from the shape of the book (Section 5.1).
- **"The flat-vol second-order greeks are just wrong, so ignore them."** They are a conservative *floor*: the constant-vol assumption understates the vol-sensitive greeks, so reality has more vanna, charm, and vomma flow, not less. The signs and the growth into expiry are robust (Section 2.3, Section 8.2).
- **"Second-order flow predicts the market."** It is positioning information, not a prediction. By the time a charm- or vanna-driven re-hedge prints, it is being placed, not forecast (Section 8.2).

### 10.2 Glossary

- **Gamma (Γ)** — ∂²V/∂S² = ∂Δ/∂S = D_q·φ(d₁)/(S·σ·√T). Curvature; the price channel of delta drift. Concentrates at the money and spikes into expiry.
- **Vanna** — ∂²V/(∂S·∂σ) = ∂Δ/∂σ = ∂Vega/∂S = −D_q·φ(d₁)·d₂/σ (per unit vol). The volatility channel of delta drift; sign flips across the strike.
- **Charm** — ∂²V/(∂S·∂t) = ∂Δ/∂t = ∂Θ/∂S. The time channel of delta drift; computable in advance; sign flips across the strike; grows violently into expiry.
- **Vomma (volga)** — ∂²V/∂σ² = ∂Vega/∂σ = Vega·d₁·d₂/σ. Vega convexity; near zero at the money, large in the wings; the vol-of-vol exposure.
- **Veta** — ∂Vega/∂t. The time channel of vega drift; the rate at which vega decays as the calendar advances; matters for calendar spreads.
- **Vera (rhova)** — ∂ρ/∂σ = ∂Vega/∂r. Cross-sensitivity of rho to volatility; negligible except for long-dated instruments in a moving-rate, moving-vol world.
- **Dollar gamma** — Γ·S²·(multiplier)/100. The change in dollar delta for a 1% move; the size of the re-hedge a 1% move forces, and the quantity whose aggregate sign seats dealer flow.
- **d₁, d₂** — d₁ = [ln(S/K) + (r − q + ½σ²)T]/(σ√T); d₂ = d₁ − σ√T. The standardized log-moneyness that every greek is built from.
- **φ, N** — the standard normal probability density and cumulative distribution.
- **Cross-gamma** — a mixed second partial coupling two inputs (vanna, charm, veta, vera); carries no one-half in the Taylor expansion, unlike a pure second derivative.
- **Per vol point** — a sensitivity to a one-percentage-point change in implied volatility (the per-unit-vol form divided by 100; by 100² for vomma).
- **Decay equation** — dΔ = Γ·dS + vanna·dσ + charm·dt, the statement that a delta-hedge goes stale through a price, a volatility, and a time channel.

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| Gamma concentrates at the money and spikes into expiry (0.0688 at 1M, 0.1415 at 1W, 0.0191 at 1Y, 0.2694 at 2 days); dollar gamma ~$688 per 1% | Own reproducible computation — `figures/fig_so_gamma_surface.py` |
| Vanna and charm flip sign across the strike and grow into expiry (charm −0.0037 at 30 days to −0.0289 at 3 days) | Own reproducible computation — `figures/fig_so_vanna_charm.py` |
| Vomma is near zero at the money and peaks in the wings, falling as base volatility rises | Own reproducible computation — `figures/fig_so_vomma.py` |
| Every second-order greek matches a central finite difference to 4.4e-7, which corrected the tabulated veta sign | Own reproducible computation |
| Black–Scholes–Merton closed-form price and its differentiated greeks | Literature — (Black & Scholes 1973; Merton 1973) |
| Constant-vol BSM systematically understates the vol-sensitive greeks; stochastic or local vol fattens vanna, charm, and vomma | Literature — (Natenberg 1994; Taleb 1997) |
| Closed-form expressions for the higher-order greeks, including the tabulated veta | Literature — (Haug 2007) |
| The theta–gamma identity Θ ≈ −½·Γ·S²·σ² sets the realized-minus-implied engine | Literature — (Hull 2022; Natenberg 1994) |
| Aggregate second-order greeks act as pre-scheduled dealer hedging flows around expiry | Practitioner consensus — not independently verified |

## References

- Black, F., & Scholes, M. (1973). The pricing of options and corporate liabilities. *Journal of Political Economy, 81*(3), 637–654.
- Haug, E. G. (2007). *The Complete Guide to Option Pricing Formulas* (2nd ed.). New York: McGraw-Hill.
- Hull, J. C. (2022). *Options, Futures, and Other Derivatives* (11th ed.). Harlow: Pearson.
- Merton, R. C. (1973). Theory of rational option pricing. *The Bell Journal of Economics and Management Science, 4*(1), 141–183.
- Natenberg, S. (1994). *Option Volatility and Pricing: Advanced Trading Strategies and Techniques* (2nd ed.). New York: McGraw-Hill.
- Taleb, N. N. (1997). *Dynamic Hedging: Managing Vanilla and Exotic Options.* New York: Wiley.

*All references above are publicly accessible: two are peer-reviewed journal articles and four are published books widely held in libraries and in print. No proprietary, course, or trading-academy material is cited, and no licensed or vendor data is used anywhere in this paper.*
