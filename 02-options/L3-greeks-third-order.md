---
title: "Third-Order Greeks — Speed, Zomma, Color, Ultima"
last_updated: 2026-09-25
---

# Third-Order Greeks — Speed, Zomma, Color, Ultima

## Abstract

The third-order greeks — speed, zomma, color, and ultima — measure how the second-order greeks themselves move. Speed is how gamma changes as spot moves; zomma is how gamma changes with implied volatility; color is how gamma changes as time passes; and ultima is the third derivative of value in volatility, the convexity of vomma. This paper builds each one as the sensitivity of a lower-order greek, derives its sign structure across moneyness and maturity, and is honest about when it matters: rarely for a discretionary trader, but materially for large or near-expiry delta-hedged books, for the stability of a gamma or vega hedge, and for exotics and model risk. Because they are high-order derivatives of a constant-volatility model, these are the greeks Black–Scholes–Merton is least equipped to price. We compute all four by central finite differences of the verified closed-form gamma and vomma, cross-check them against closed forms to a maximum relative error near 2e-6, and reproduce every figure and printed number from free, self-contained model code.

## Keywords

Speed, zomma, color, ultima, third-order greeks, gamma sensitivity, vomma, vanna, Black–Scholes–Merton, finite differences, central difference, gamma hedging, delta hedging, near-expiry risk, vol-of-vol, model risk, moneyness, option sensitivities, dealer hedging

## 1 Introduction

### 1.1 Motivation and thesis

The greeks form a chain. The first-order greeks — delta, theta, vega, rho — say how an option's value moves when an input moves. The second-order greeks — gamma, and the flow trio vanna, charm, and volga — say how the *hedge* moves: how fast your delta goes stale as spot, time, or volatility change. The third-order greeks are the next link: they say how the *second-order greeks* move. Speed is how gamma changes as spot moves; zomma is how gamma changes with implied volatility; color is how gamma changes as time passes; and ultima is how vomma — the vega of vega — changes with volatility. Each is a partial derivative of a lower-order greek, and reading them in that order is the whole trick.

The thesis of this paper is that the third-order greeks are a *hedge-stability accounting*. A first-order greek is a risk you carry; a second-order greek is the rate at which a first-order hedge decays; a third-order greek is the rate at which that *decay rate* is itself changing. They answer the question a careful hedger asks after the obvious ones: *"my gamma tells me how much to re-hedge per point of spot move — but how reliable is that gamma number, given that a day will pass, the spot will jump, and implied vol will drift before I trade again?"* The answer is that gamma is reliable exactly when speed, zomma, and color are small, and unreliable — sometimes badly so — when they are large. And they are large in one specific, predictable place: near expiry, at the money, on big moves. That is the honest scope of this paper, stated up front. Discretionary traders essentially never quote these greeks, and they are right not to for most positions. They matter for large or near-expiry delta-hedged books, for the stability of a gamma or vega hedge across a vol move, for exotics whose payoff lives in the higher derivatives, and — above all — as a map of where the constant-volatility model is least trustworthy.

### 1.2 Scope, prerequisites, and intended reader

This paper is written to stand on its own. It assumes only that the reader is comfortable with the idea of an option price as a function of spot, time, volatility, and rates, and with a first partial derivative; it uses the Black–Scholes–Merton (BSM) closed forms without deriving them, and it needs no stochastic calculus. Because the third-order greeks are derivatives of gamma and vomma, we re-introduce those two second-order greeks briefly here so the rest of the paper is self-contained.

*Gamma* is the curvature of the option's value in spot — the derivative of delta:

Γ = ∂²V/∂S² = ∂Δ/∂S.

It measures how fast delta itself changes as the underlying moves, which is why a straight-line delta-hedge goes stale the instant spot moves. Gamma is largest at the money and grows without bound as expiry approaches. *Vega* is the sensitivity of value to implied volatility, Vega = ∂V/∂σ, and its own derivative in volatility is *vomma* (also called volga),

vomma = ∂²V/∂σ² = ∂(Vega)/∂σ,

the convexity of the option in volatility. The third-order greeks of this paper are the derivatives of these two objects: three derivatives of gamma (in spot, in vol, in time — speed, zomma, color) and one further derivative of vomma in vol (ultima).

After reading this paper a reader can state each third-order greek as the derivative of a named lower-order greek; give its sign across moneyness and its behavior into expiry; explain, with model numbers, why a once-a-day gamma hedge on a near-expiry book is systematically off; say honestly when each greek is worth computing and when it is noise; and reproduce every number here by finite-differencing a verified pricer. The companion material sits alongside: the mechanics of delta and gamma hedging are developed in the greeks-and-hedging paper; vanna, charm, and volga in the second-order greeks paper; and the market-impact story of aggregate dealer hedging in the dealer-flows-and-GEX paper. This paper needs none of them as prerequisites, but it points to each where the thread continues.

### 1.3 Data and reproducibility

Every figure and every printed number in this paper is a self-contained Black–Scholes–Merton computation that needs no market data at all. The inputs are stated wherever they are used — throughout, unless noted, K = 100, σ = 20%, r = 4%, q = 0 — and each figure names the script that produces it. The third-order greeks are computed by *central finite differences* of the verified closed-form gamma and vomma, and cross-checked against closed forms; the maximum relative error between the two methods is reported in Section 8 and is near 2e-6. Where a convention could go two ways — per vol point versus per unit volatility, per calendar day versus per year, and in particular the sign of color, which depends on whether time is measured forward or as time-to-expiry — the choice is stated explicitly, because a greek quoted without its units and sign is not a number. *This is a research and educational document, not investment advice.*

### 1.4 Organization of this paper

This paper is complete; every section below is written in full. The arc goes one greek at a time and ends with the one scenario in which they collectively matter.

- **Section 2 Why go to third order** — the chain-of-sensitivities pattern, a Taylor view, the honest "when does this matter," and the definitions and notation used throughout, with a flag that these are the most model-dependent greeks.
- **Section 3 Speed** — how gamma changes as spot moves; why a big move makes a gamma estimate stale; largest near expiry at the money (Figure 1).
- **Section 4 Zomma** — how gamma changes with implied vol; the stability of a gamma hedge when vol moves (Figure 3, left).
- **Section 5 Color** — how gamma changes as time passes; the overnight drift of a hedged book's gamma; largest near expiry (Figure 2).
- **Section 6 Ultima** — third-order vol convexity; where it lives and why it matters mainly for vol-of-vol and exotic books (Figure 3, right).
- **Section 7 When third-order greeks actually bite** — one worked scenario: a near-expiry at-the-money delta-hedged book whose second-order greeks move fast within a day, quantified with the model, plus a note on model risk.
- **Section 8 Worked examples in Python** — all four greeks by central finite differences of the verified gamma and vomma, with the closed-form cross-check and the self-check numbers.
- **Section 9 Common misconceptions and glossary**, followed by the references.

## 2 Why go to third order

Before naming a single third-order greek it is worth being precise about what we are differentiating, and honest about how far this is worth taking.

### 2.1 The pattern: each greek is the sensitivity of a lower-order one

A greek is a partial derivative of the option value, and the greeks are organized by *order* — how many times you have differentiated. The first-order greeks differentiate the price once (delta in spot, theta in time, vega in vol, rho in rates). The second-order greeks differentiate a first-order greek once more: gamma is the slope of delta in spot, vanna the slope of delta in vol, charm the slope of delta in time, and vomma the slope of vega in vol. The third-order greeks continue the same move — differentiate a second-order greek once more:

- **speed** = ∂Γ/∂S = ∂³V/∂S³ — gamma's slope in spot;
- **zomma** = ∂Γ/∂σ = ∂³V/(∂S²∂σ) — gamma's slope in vol (equivalently ∂(vanna)/∂S);
- **color** = ∂Γ/∂t = ∂³V/(∂S²∂t) — gamma's slope in time;
- **ultima** = ∂(vomma)/∂σ = ∂³V/∂σ³ — vomma's slope in vol.

Speed, zomma, and color are the three derivatives of gamma; ultima is the one further derivative of vomma in vol that traders bother to name. There are other third-order cross-terms, but these four are the ones with standard names and practical readings, because gamma and vomma are the two second-order greeks a book most often tries to hold flat.

### 2.2 A Taylor view

The reason order matters is the Taylor expansion. The change in an option's value for small moves in spot and vol is

dV ≈ Δ dS + ½ Γ dS² + Vega dσ + ½ vomma dσ² + vanna dS dσ + …,

and the third-order terms are the next line: ⅙ speed dS³ captures the fact that gamma itself is not constant as spot moves, ⅙ ultima dσ³ that vomma is not constant as vol moves, and mixed terms like ½ zomma dS² dσ and ½ color dS² dt that couple the curvature to vol and to time. For everyday moves these terms are tiny — which is exactly why they are usually ignored. They stop being tiny when the coefficient (the third-order greek) is large *and* the move (dS³, dσ³) is large, and both conditions are met in the same corner of the world: short-dated at-the-money options in a fast market. Third order is not a refinement you sprinkle everywhere; it is a correction that is negligible almost everywhere and decisive in one place.

### 2.3 When does this actually matter? (said up front)

It is worth being blunt, because overselling these greeks is the standard failure mode. A discretionary trader holding a few positions for days or weeks will never quote speed, zomma, color, or ultima, and losing no sleep over them is the correct posture. They earn their keep in four situations, and only these: (i) a *large* delta-hedged book, where a small per-option error is multiplied by enormous size; (ii) a *near-expiry* book, where gamma is huge and moving fast so the second-order greeks go stale within a single day; (iii) the *stability of a hedge* — a desk that has neutralized gamma or vomma needs to know how quickly that neutrality decays when spot, time, or vol move it; and (iv) *exotics and model risk*, where the payoff or the model dependence lives in the high derivatives. Everywhere else they are noise. This paper takes them seriously in exactly those settings and nowhere else.

### 2.4 Notation, and a warning about the model

Throughout, for a European option under BSM with continuous carry q, define the standard moneyness terms

d₁ = [ ln(S/K) + (r − q + ½σ²) T ] / (σ√T),  d₂ = d₁ − σ√T,

with φ(·) the standard normal probability density and N(·) its cumulative distribution function. Gamma and vega are

Γ = e^(−qT) φ(d₁) / (S σ√T),  Vega = S e^(−qT) φ(d₁) √T,

and vomma = Vega · d₁d₂/σ. The four third-order greeks have closed forms that we will state as each greek is introduced and collect in Section 8.

One warning belongs here, before any of them. These are the **most model-dependent greeks in this whole track**. Every greek in BSM is computed under the assumption that volatility is a single constant — false, but a serviceable lie for delta and even gamma, because a first or second derivative is fairly robust to the model's misspecification. A *third* derivative is not. Differentiating three times magnifies exactly the curvature the model gets wrong, and two of these greeks (zomma and ultima) are literally derivatives *with respect to* the volatility that BSM pretends is fixed. A stochastic-volatility model, which lets vol move and correlate with spot, produces materially different speed, zomma, color, and ultima (Wilmott 2006; Taleb 1997). So the numbers in this paper should be read as the *structure* the constant-vol model implies — the signs, the shapes, where each greek lives and how it blows up into expiry — and not as precise hedge inputs. Section 7 returns to this point once the structure is on the table.

## 3 Speed

Speed is the rate at which gamma itself changes as spot moves — the slope of gamma in the underlying, and equivalently the third derivative of value in spot:

speed = ∂Γ/∂S = ∂³V/∂S³ = −(Γ/S) · ( d₁/(σ√T) + 1 ).

The reading that matters is the first one. Gamma tells you how much your delta changes per point of spot move, and therefore how much you must re-hedge; speed tells you how much that *gamma* changes per point of spot move. If speed is near zero, gamma is locally flat and a single gamma number describes the neighborhood well. If speed is large, gamma is a moving target: the gamma you read at one price is wrong at a price a little away, so a hedge sized on today's gamma will be mis-sized after a move.

### 3.1 Sign structure across the strike

Figure 1 plots speed across moneyness for three maturities. The defining feature is that **speed changes sign across the strike**. For a call it is positive below the strike and negative above it, crossing zero right around the money — for the one-month option the model prints speed of +0.00715 per index point at S/K = 0.95, −0.00172 at the money, and −0.00696 at S/K = 1.05, with the zero crossing at about S/K = 0.99. The intuition is geometric: gamma is a hump centered near the money, so its *slope* is positive on the way up to the peak (below the strike) and negative on the way down (above it). Speed is that slope, and like the slope of any hump it is zero at the top and opposite in sign on the two sides.

### 3.2 Blow-up near expiry

The second feature is the one that makes speed practical rather than decorative: its amplitude **explodes as expiry approaches**. The peak magnitude of speed across the range is 0.0028 at three months, 0.0078 at one month, and 0.031 at one week — the one-week option's speed is more than ten times the three-month's. This is the same near-expiry sharpening that makes gamma spike, one derivative further along and therefore even more violent. The practical consequence is direct: for a near-expiry book, gamma is not merely large, it is *fast* — a move of a percent or two relocates the option along a steeply sloped gamma curve, so the gamma you were hedging on has changed materially by the time you trade. A gamma figure printed at the open is a reliable guide to the close only if the day is quiet; the larger speed is, the shorter its shelf life. This is precisely why the one scenario in Section 7 is built on a near-expiry at-the-money book.

![Speed (the third derivative of value in spot, the slope of gamma) for a European call under Black–Scholes–Merton across moneyness S/K at three maturities (1 week, 1 month, 3 months); K=100, sigma=20%, r=4%, q=0. Speed is positive below the strike and negative above it, crossing zero near the money, and its amplitude grows more than tenfold from three months to one week — a near-expiry gamma estimate goes stale fast on a large move. Reproduce with `figures/fig_to_speed.py`.](figures/fig_to_speed.png)

## 4 Zomma

Zomma is the rate at which gamma changes when *implied volatility* moves — the slope of gamma in vol, and equivalently the slope of vanna in spot:

zomma = ∂Γ/∂σ = ∂³V/(∂S²∂σ) = ∂(vanna)/∂S = Γ · (d₁d₂ − 1)/σ.

Its subject is the *stability of a gamma hedge*. A desk that has neutralized gamma has done so at today's implied vol; zomma says how much that gamma reappears if implied vol moves. Multiply zomma by the change in vol and you get the gamma you did not expect to be carrying after a vol move.

### 4.1 Negative at the money, positive in the wings

The left panel of Figure 3 maps zomma across moneyness for three vol levels. The sign structure is: **negative near the money, positive out in the wings**. At the money a rise in implied vol *flattens and spreads* the gamma hump — the peak comes down and the shoulders fill in — so at-the-money gamma falls (zomma < 0) while wing gamma rises (zomma > 0). The model makes the at-the-money value concrete for a one-month option: zomma is −0.00608 per vol point at 15% vol, −0.00343 at 20%, and −0.00153 at 30% — larger in magnitude at low vol, because a low-vol gamma peak is tall and narrow and therefore easy to knock down. The crossover to positive zomma sits further out as vol rises: at 15% vol it has already turned positive by S/K = 0.95 (+0.00081) and S/K = 1.05 (+0.00124), while at 20% and 30% those same strikes are still on the negative, near-the-money side, because higher vol widens the whole structure.

### 4.2 Why a gamma hedge is only as stable as vol

The practical reading follows from the sign. A book that is gamma-flat at the money today will, after a jump in implied vol, find itself *short* at-the-money gamma — because at-the-money gamma fell and its hedge did not. That is an uncomfortable place to be: implied vol usually jumps in stressed, fast markets, which is exactly when being short gamma hurts most. Zomma is the greek that quantifies this leak in a gamma hedge. It is second-order small for gentle vol moves and rarely quoted by anyone hedging vanilla books day to day, but for a large book carried across a vol regime change — or for a desk that markets itself as gamma-neutral — it is the term that says how neutral that neutrality really is.

## 5 Color

Color is the rate at which gamma changes as *time passes* — gamma decay, and equivalently the third derivative of value in two spot derivatives and one time derivative:

color = ∂Γ/∂t = ∂³V/(∂S²∂t).

It is the overnight drift of a hedged book's gamma. Even if the underlying is perfectly pinned and implied vol does not move, a day passing changes your gamma by color, so the gamma you re-hedge on tomorrow is not the gamma you hedged on today.

### 5.1 A sign convention worth stating

Color is where the "time" convention bites hardest, so we fix it explicitly. We quote color as ∂Γ/∂t, the change in gamma as *calendar time passes* (so time-to-expiry T shrinks), per calendar day. Haug's tabulated closed form is written the other way, as a derivative with respect to time-to-maturity T, and therefore carries the opposite sign; color as time passes is minus that expression, divided by 365 for a per-day figure (Haug 2007). The point of stating this is not pedantry: it is the single most common error in a hand-transcribed third-order greek, and Section 8 shows the finite-difference cross-check that catches it.

### 5.2 At the money gamma builds; just off it, gamma decays

Figure 2 plots color across moneyness for three short maturities. Two things stand out. First, **at the money color is positive** — gamma *builds* into expiry, it does not decay. This surprises readers who take the name "gamma decay" literally: at the strike, as the clock runs down, the gamma hump grows taller, so its rate of change with time is positive. The model prints at-the-money color of +0.00114 per day at one month, +0.00346 at two weeks, and +0.00979 at one week — the daily gamma build is nearly nine times larger at one week than at one month, the same near-expiry explosion seen in speed. Second, **just off the money color turns negative**: as the gamma hump grows taller it also grows *narrower*, so at a fixed point a little away from the strike gamma is actually falling. The sign-change crossings move inward toward the strike as expiry approaches — for the one-month option they sit at about S/K = 0.94 and 1.06, but for the one-week option they have closed in to 0.97 and 1.03. The picture is a peak that is simultaneously rising at its center and thinning at its flanks, faster and faster into expiry.

### 5.3 The overnight drift of a hedged book

The consequence for a hedger is that a delta-hedged book's gamma is not a constant it can read once. A desk holding near-expiry at-the-money options is *long* a fast-building gamma from color alone, quite apart from any spot move; a desk short those options is short a gamma that grows against it every night. Color is the greek that lets that drift be anticipated: like charm, it needs no price move at all — the change happens as the clock ticks — so tomorrow's gamma can be estimated today. Combined with speed, it is what makes a once-a-day hedge on a near-expiry book systematically wrong, which is the subject of Section 7.

![Color (the change in gamma as one calendar day passes) for a European call under Black–Scholes–Merton across moneyness S/K at three short maturities (1 week, 2 weeks, 1 month); K=100, sigma=20%, r=4%, q=0. At the money color is positive and grows sharply into expiry (gamma builds), reaching about +0.0098 per day at one week; just off the money it turns negative as the gamma peak narrows, and the sign-change moneyness closes in toward the strike as expiry approaches. Reproduce with `figures/fig_to_color.py`.](figures/fig_to_color.png)

## 6 Ultima

Ultima is the third-order vol convexity — the rate at which vomma changes as volatility moves, and therefore the third derivative of value in vol:

ultima = ∂(vomma)/∂σ = ∂³V/∂σ³ = −(Vega/σ²) · [ d₁d₂ (1 − d₁d₂) + d₁² + d₂² ].

If vomma is the convexity of the option in vol — the vega of vega — then ultima is the *convexity of that convexity*, the term a book needs when it is not enough to know that vega changes as vol moves (vomma) but one must also know that *vomma itself* changes as vol moves. It is the deepest vol greek in common use, and the one with the narrowest audience.

### 6.1 Zero at the money, large on the shoulders

The right panel of Figure 3 maps ultima across moneyness for three vol levels. Its structure is the mirror of the intuition that "vol greeks live at the money": ultima is **near zero at the money and large on the shoulders**. At the money vomma is at a stationary point in vol, so its slope — ultima — is small; the model prints at-the-money ultima of just −3.1 per unit vol cubed — a third derivative in σ, so its natural unit is per (unit vol)³; equivalently −3.1×10⁻⁶ per vol point cubed — for a one-month option at 20% vol. Move a little off the strike and it grows sharply negative: at S/K = 0.95 and 1.05 the one-month ultima is −316 and −349 at 20% vol, and larger still at low vol (−587 and −571 at 15%), shrinking as vol rises (−88 and −105 at 30%). Further out in the wings it turns positive and then decays back toward zero as vega itself vanishes. The vol-of-vol convexity of a vanilla book therefore does not live at the strike where vega and vomma peak; it lives on the shoulders, and it is sharpest when volatility is low.

### 6.2 A greek for vol-of-vol and exotic books

Ultima is honestly a specialist's greek. A directional trader never needs it; even a vanilla vega trader who is content to be re-marked as vol moves can ignore it. It becomes first-order relevant for books whose whole business is the *behavior of volatility itself* — vol-of-vol positions, variance and volatility derivatives, and exotics such as barriers and cliquets whose value is a nonlinear function of the vol path. For those books, being vomma-hedged is not enough: ultima says how that vomma hedge decays as vol moves, in the same way zomma said how a gamma hedge decays. And because it is a third derivative in the very input BSM holds constant, ultima is the greek most exposed to model risk in this whole paper — a point Section 7 makes general.

![Zomma and ultima for a European call under Black–Scholes–Merton across moneyness S/K at three implied-vol levels (15%, 20%, 30%), one-month maturity; K=100, r=4%, q=0. Left: zomma (gamma's sensitivity to vol, per vol point) is negative near the money and positive in the wings, and larger at low vol. Right: ultima (vomma's sensitivity to vol, per unit vol cubed) is near zero at the money and large on the shoulders — the vol-of-vol convexity lives off the strike, not on it. Reproduce with `figures/fig_to_zomma_ultima.py`.](figures/fig_to_zomma_ultima.png)

## 7 When third-order greeks actually bite

Everything so far has been structure. This section shows the one setting where the structure becomes money, and then draws the model-risk lesson.

### 7.1 A near-expiry at-the-money delta-hedged book

Consider a desk running a delta-hedged book concentrated in one-week at-the-money index options, re-hedged once a day at the open — a common cadence for a book that is not staffed for continuous hedging. Take the model inputs of this paper (K = 100, σ = 20%, r = 4%, q = 0) and follow the *gamma* the desk uses to size its hedges through a single day. The desk's problem is not that its gamma is large — it knows that. Its problem is that its gamma is *moving*, and the third-order greeks say how fast.

From **color**, gamma builds as expiry nears: on a trading-day clock — one week is five sessions — the one-week gamma of 0.141 at the open becomes 0.158 by the same time tomorrow, a **+11.8% drift from the passage of time alone**, before the spot has moved at all. (The per-*calendar*-day color of +0.0098 is a 365-day rate; adding it to a maturity measured in 252 trading days is what an earlier version did to report a spurious +6.9% — the drift and the maturity must use the same clock.) From **speed**, gamma also moves along the spot axis: a +1% move takes gamma to 0.130 (−8.4%) and a −1% move to 0.136 (−3.8%), while a +3% move nearly halves it, to 0.076 (−46.4%). So within one day the gamma that sizes every hedge trade can move by seven percent from time and by tens of percent from a realistic move — and these are exactly the near-expiry at-the-money conditions where speed and color peak (Figures 1 and 2).

Put a size on it. A desk short 2,000 of these contracts on the 100-multiplier reads its book gamma at the open and concludes that a +1% move will hand it about 28,300 index-units of delta to hedge. But by the time it actually re-hedges, color alone has grown the per-option gamma, so the same +1% move now implies about 31,600 index-units — a **+11.8% mis-size** purely from the day's decay, with the mis-size from an intraday move on top of that. A once-a-day hedge that treats gamma as a constant between rebalances is therefore *systematically* off near expiry, always in the direction the third-order greeks predict, and the error scales with the size of the book. There is even a further honesty here: the first-order speed estimate for the +1% move (gamma ≈ 0.138) itself *over*-predicts the true 0.130, because speed is *also* moving — near expiry, even the third-order term is only a local guide, and the clean fix is to re-hedge the second-order greeks more often, not to extrapolate them further.

### 7.2 A short model-risk note

The scenario above is computed in constant-volatility BSM, and this is precisely where that model is weakest. Two of these greeks (zomma, ultima) are derivatives with respect to a volatility the model assumes never changes, and all four are third derivatives that magnify whatever curvature the model gets wrong. A real market violates the constant-vol assumption in exactly the way that matters here: implied vol moves, and it moves *with* spot — the leverage effect, vol rising as equities fall — a spot-vol correlation that BSM sets to zero. A stochastic-volatility model that respects this correlation produces materially different speed, color, zomma, and ultima, because in such a model a spot move *is* a vol move, so the channels this paper treated separately feed back into one another (Wilmott 2006; Taleb 1997). The practical posture that follows is the one this paper has argued throughout: use the third-order greeks *qualitatively* — for their signs, for where they live, and for the robust fact that they explode into expiry — and not as precise hedge coefficients. When they are large enough to matter, the honest response is to shorten the hedge interval so the second-order greeks are re-measured before the third-order terms can carry them far, rather than to trust a static extrapolation from a model that is least reliable exactly here.

## 8 Worked examples in Python

The robust way to get a third-order greek is not to transcribe a closed form — the closed forms are long, and the sign of color is a standing trap — but to *finite-difference a verified lower-order greek*. Gamma and vomma have been checked elsewhere in this track; bumping their inputs by a small amount and taking a central difference gives speed, zomma, color, and ultima directly, with the closed forms serving only as a cross-check. If the two ever disagreed, the finite difference of the verified greek is the one to trust.

### 8.1 Central finite differences of gamma and vomma

The code below uses stdlib `math` only. It defines gamma and vomma from the BSM closed forms, then obtains each third-order greek as a central difference — `(f(x+h) − f(x−h)) / 2h` — of the appropriate lower-order greek: speed and color by bumping spot and time in gamma, zomma by bumping vol in gamma, and ultima by bumping vol in vomma. Color is computed as the change per calendar day as time passes, i.e. minus the derivative in time-to-maturity, divided by 365.

```python
import math
SQRT2PI = math.sqrt(2.0 * math.pi)

def npdf(x): return math.exp(-0.5 * x * x) / SQRT2PI

def _d1d2(S, K, T, r, sigma, q):
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrtT)
    return d1, d1 - sigma * sqrtT, sqrtT

def gamma_raw(S, K, T, r, sigma, q=0.0):                 # verified 2nd-order greeks
    d1, _, sqrtT = _d1d2(S, K, T, r, sigma, q)
    return math.exp(-q * T) * npdf(d1) / (S * sigma * sqrtT)

def vomma_raw(S, K, T, r, sigma, q=0.0):
    d1, d2, sqrtT = _d1d2(S, K, T, r, sigma, q)
    vega = S * math.exp(-q * T) * npdf(d1) * sqrtT
    return vega * d1 * d2 / sigma

def central(f, x, h): return (f(x + h) - f(x - h)) / (2.0 * h)

def third_order_fd(S, K, T, r, sigma, q=0.0):
    hS, hsig, hT = 1e-2, 1e-5, 1e-6
    speed  = central(lambda s: gamma_raw(s, K, T, r, sigma, q), S, hS)
    zomma  = central(lambda v: gamma_raw(S, K, T, r, v, q), sigma, hsig)
    color  = -central(lambda t: gamma_raw(S, K, t, r, sigma, q), T, hT) / 365.0
    ultima = central(lambda v: vomma_raw(S, K, T, r, v, q), sigma, hsig)
    return dict(speed=speed, zomma=zomma, color=color, ultima=ultima)
```

### 8.2 The self-check against the closed forms

Running the accompanying script on the at-the-money one-month option (S = K = 100, T = 21/252, r = 4%, σ = 20%, q = 0) prints each greek by finite difference and by closed form, and the maximum relative error between them:

```
greek      finite diff    closed form    rel.err   units
speed      -0.00172100    -0.00172100   2.07e-06   per index point
zomma      -0.34334047    -0.34334047   2.47e-09   per unit vol
color       0.00114011     0.00114011   5.99e-11   per calendar day
ultima     -3.10557720    -3.10557718   7.67e-09   per unit vol cubed

max relative error (finite diff vs closed form): 2.07e-06
```

The two methods agree to within about two parts in a million, the residual being the truncation error of the central difference rather than any disagreement of substance. The closed forms used for the cross-check are

speed = −(Γ/S)(d₁/(σ√T) + 1),  zomma = Γ(d₁d₂ − 1)/σ,  ultima = −(Vega/σ²)[ d₁d₂(1 − d₁d₂) + d₁² + d₂² ],

with color given by minus the Haug ∂Γ/∂T expression per day, as Section 5.1 fixed. Every quoted number in this paper — the sign-change moneyness in Section 3, the color values in Section 5, the ultima shoulders in Section 6, and the near-expiry book figures in Section 7 — is printed by one of the four scripts named in the captions and in `figures/fig_to_worked_examples.py`, so the whole document rebuilds from free, self-contained model code.

## 9 Common misconceptions and glossary

### 9.1 Common misconceptions

- **"Third-order greeks are purely academic."** They are noise for almost every position, but for a large or near-expiry at-the-money delta-hedged book they set how fast gamma goes stale within a day — a systematic, quantifiable hedging error, not a curiosity (Section 7).
- **"Gamma is constant enough to hedge once a day."** Speed and color say otherwise near expiry: at one week, gamma drifts +11.8% from time alone in a trading day and moves −8.4% for a 1% spot move and nearly −50% for a 3% move, so a once-a-day hedge sized on the open's gamma is systematically mis-sized (Section 7).
- **"Color means gamma always decays."** At the money gamma *builds* into expiry — color is positive there — and only just off the money does gamma decay. The name is a convention, not a direction (Section 5).
- **"Higher order means higher precision."** Not from a misspecified model. These are third derivatives of a constant-vol formula, so more differentiation magnifies the assumption BSM gets wrong rather than buying accuracy; near expiry even the third-order term is only local (Sections 2, 7).
- **"The vol greeks all live at the money."** Vega and vomma peak there, but zomma is negative at the money and positive in the wings, and ultima is near zero at the money and large on the shoulders. The higher vol greeks live *off* the strike (Sections 4, 6).
- **"The closed form is the ground truth."** The verified finite difference is. Closed forms for third-order greeks are long and easy to mis-transcribe — color's sign especially — so the robust practice is to finite-difference a verified lower-order greek and use the closed form only as a cross-check (Section 8).

### 9.2 Glossary

- **Speed** — ∂Γ/∂S = ∂³V/∂S³. How gamma changes as spot moves; positive below the strike, negative above; blows up near expiry.
- **Zomma** — ∂Γ/∂σ = ∂(vanna)/∂S. How gamma changes with implied vol; negative near the money, positive in the wings; the stability of a gamma hedge under vol moves.
- **Color** — ∂Γ/∂t = ∂³V/(∂S²∂t). How gamma changes as time passes; positive (gamma building) at the money, negative just off it; largest near expiry; quoted per calendar day.
- **Ultima** — ∂(vomma)/∂σ = ∂³V/∂σ³. Third-order vol convexity; near zero at the money, large on the shoulders; the vol-of-vol convexity of a vega book.
- **Gamma (Γ)** — ∂²V/∂S². The curvature of value in spot that speed, zomma, and color differentiate.
- **Vomma (volga)** — ∂²V/∂σ². The vol-convexity that ultima differentiates.
- **Vanna** — ∂²V/(∂S∂σ). Delta's sensitivity to vol; zomma is its slope in spot.
- **Central finite difference** — a numerical derivative, (f(x+h) − f(x−h))/2h; here the robust way to obtain a third-order greek from a verified lower-order one.
- **d₁, d₂, φ, N** — the Black–Scholes–Merton moneyness terms and the standard normal density and cumulative distribution function.
- **Moneyness** — the position of spot relative to strike, here S/K; drives the shape of every greek.

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| Speed flips sign across the strike (+0.00715/−0.00172/−0.00696 at 1 month) and its amplitude grows more than tenfold from 3 months to 1 week | Own reproducible computation — `figures/fig_to_speed.py` |
| Color is positive at the money (gamma builds: +0.00114 at 1M to +0.00979 at 1W) and turns negative just off the strike | Own reproducible computation — `figures/fig_to_color.py` |
| Zomma is negative near the money and positive in the wings; ultima is near zero at the money and large on the shoulders | Own reproducible computation — `figures/fig_to_zomma_ultima.py` |
| Near-expiry 1-week at-the-money book: gamma drifts +11.8% per trading day from the passage of time, and −8.4% (+1% move) to −46.4% (+3% move) from speed, mis-sizing a once-daily hedge | Own reproducible computation — `figures/fig_to_worked_examples.py` |
| All four third-order greeks by central finite difference match the closed forms to a max relative error of 2.07e-6 | Own reproducible computation — `figures/fig_to_worked_examples.py` |
| Closed-form gamma, vomma, and third-order greeks (including the tabulated color/∂Γ/∂T sign) | Literature — (Haug 2007) |
| Third derivatives of a constant-vol model are least trustworthy; a stochastic-vol model with spot-vol correlation gives materially different speed, zomma, color, and ultima | Literature — (Wilmott 2006; Taleb 1997) |
| Discretionary traders essentially never quote the third-order greeks; they are noise for most positions | Practitioner consensus — not independently verified |

## References

- Haug, E. G. (2007). *The Complete Guide to Option Pricing Formulas* (2nd ed.). New York: McGraw-Hill.
- Hull, J. C. (2022). *Options, Futures, and Other Derivatives* (11th ed.). Harlow: Pearson.
- Natenberg, S. (1994). *Option Volatility and Pricing: Advanced Trading Strategies and Techniques* (2nd ed.). New York: McGraw-Hill.
- Taleb, N. N. (1997). *Dynamic Hedging: Managing Vanilla and Exotic Options.* New York: Wiley.
- Wilmott, P. (2006). *Paul Wilmott on Quantitative Finance* (2nd ed.). Chichester: Wiley.

*All references above are publicly accessible: all five are published books widely held in libraries and in print. No proprietary, course, or trading-academy material is cited, and no licensed or vendor data is used anywhere in this paper.*
