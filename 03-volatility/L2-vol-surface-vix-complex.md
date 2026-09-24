---
title: "The Volatility Surface & the VIX Complex"
last_updated: 2026-09-20
---

# The Volatility Surface & the VIX Complex

## Abstract

Implied volatility is not one number. It is a *surface* — a different value for every strike and every expiry — and almost everything the options market knows about risk is written into that surface's shape rather than its level. This paper teaches the shape: how to read a surface plot in under a minute; how skew is measured and what it says about positioning; why the term structure of index volatility lives in contango most of the time and what its inversions mean; and how the surface actually moves when the market moves (sticky-strike versus sticky-delta, with the published evidence). It then takes apart the Cboe index complex — VIX, VIX3M, VVIX, SKEW, COR1M, VXN — one instrument at a time, and asks the question that is usually skipped: how much of the complex is redundant? A correlation analysis on seventeen years of daily data shows one tight VIX-family block and a single genuinely orthogonal axis, and motivates a compact five-factor daily read in which numeric factors overrule single-index narratives. A case study of February 2018 shows what happens when a product built on the complex becomes the flow that drives it. Every figure is reproducible from free data.

## Keywords

Implied volatility surface, volatility smile, volatility skew, risk reversal, term structure, contango, backwardation, forward volatility, sticky strike, sticky delta, fixed-strike volatility, VIX, VIX3M, VVIX, SKEW, implied correlation, VXN, volatility of volatility, volatility ETPs, roll yield, dispersion

## 1 Introduction

### 1.1 Motivation and thesis

Ask a market what it thinks and it will answer with a price. Ask an *options* market what it thinks and it will answer with thousands of prices at once — one for every strike and every expiry — and each of those prices can be restated as an implied volatility. Collapse them into a single headline number, as the financial press does every day with the VIX, and you have thrown away nearly all of the information: the asymmetry between what the market will pay for crash protection and what it will pay for upside; the difference between fear about *this week* and unease about *next quarter*; the distinction between an index that is dangerous because its components move together and one that is merely noisy because they rotate against each other.

The thesis of this paper is that *the structure is the signal*. A volatility level is an average; the surface — implied volatility as a function of strike and maturity — and its companion indices are where the readable information lives. Two practical corollaries follow and organize everything below. First, the surface must be read in the right coordinates: a trader who compares "the at-the-money volatility today" with "the at-the-money volatility yesterday" after a 2% rally is largely measuring the market's *movement along* a static skew, not a repricing of risk — the fixed-strike lens of Section 5 exists to separate the two. Second, the Cboe index complex that summarizes the surface is heavily redundant — we will show in Section 6 that VIX, VIX3M and VXN are statistically one instrument — so a disciplined daily read needs a small, deliberately chosen *factor set*, each factor measuring a different dimension, with the standing rule that a numeric factor overrules any narrative built on a single index. That factor set is developed in Section 7.

### 1.2 Scope, prerequisites, and intended reader

This paper sits in the Trading Library's *Volatility* track. It assumes the volatility-fundamentals paper (*Understanding Volatility*): what implied and realized volatility are, annualization and the √252 convention, and why implied volatility usually exceeds subsequently realized volatility (the variance risk premium). It also assumes the greeks-and-hedging paper: what vega is and why option prices are, to first order, quotes on volatility. Formulas are shown *and* translated into words; nothing requires stochastic calculus.

After reading this paper, a reader can:

- read an implied-volatility surface plot in under a minute — level, skew, curvature, and term slope, in that order — and say which of the four moved when the surface changes;
- measure skew with a 25-delta risk reversal, explain the sign convention, and distinguish a fixed-strike read from a fixed-delta read;
- state the difference between the spot IV term structure and the VIX futures curve, and compute the forward volatility between two expiries by hand;
- define sticky-strike and sticky-delta, name the regime in which each is the better approximation, and explain why fixed-strike vol is the cleaner lens in both;
- describe what each member of the Cboe complex — VIX, VIX3M, VVIX, SKEW, COR1M, VXN — uniquely measures, quote its typical range, and defend a minimal orthogonal subset with data;
- run a five-factor daily volatility read (level, term slope, vol-of-vol, correlation, skew) as numbers rather than vibes;
- and explain, mechanically, how an inverse-volatility product amplified a sell-off into the largest one-day VIX rise on record in February 2018.

### 1.3 Data and reproducibility

Empirical statements here are *descriptive* — shares of days, correlations, ranges — computed under one pre-committed rule stated in each figure script; no thresholds were searched, and nothing in this paper is a validated trading signal.

All data are free: Cboe's public daily-history CSVs for the index complex, Cboe's public delayed-quotes feed for the SPX option chain, and Yahoo Finance for the 2018 case study. (FRED mirrors the VIX family as VIXCLS/VXVCLS/VXNCLS; it was unreachable at build time, so the Cboe originals are used throughout — same series, primary source.) Downloaded data are cached beside the scripts so every figure re-renders offline. *This is a research and educational document, not investment advice.*

### 1.4 Organization of this paper

The paper is complete; the arc is as follows. **Section 2** builds the surface itself — implied volatility as a function of strike and maturity — and reads a real SPX surface (Figure 1). **Section 3** makes skew operational: the 25-delta risk reversal, fixed-strike versus fixed-delta reads, skew as positioning information, and event behavior. **Section 4** treats the term dimension: contango and backwardation on seventeen years of data (Figure 2), the VIX-futures-curve confusion resolved, event bumps, and forward volatility computed by hand. **Section 5** asks how the surface *moves* — sticky-strike versus sticky-delta, the evidence, and the fixed-strike discipline. **Section 6** walks the Cboe complex one instrument at a time, charts the secular drift of the SKEW index (Figure 3), and closes with the redundancy analysis (Figure 4). **Section 7** condenses everything into a working five-factor daily read. **Section 8** covers volatility products and their flows, with February 2018 as the case study (Figure 5). **Section 9** treats cross-index and cross-asset structure: VXN versus VIX, and single-name versus index volatility in one page. **Section 10** collects common misconceptions, **Section 11** is a glossary, and the references close the paper.

## 2 The implied volatility surface

### 2.1 One number per option, a surface per market

Every listed option has a price, and — given the underlying, the strike K, the expiry T, and a discount rate — that price can be inverted through the Black-Scholes formula into the one free parameter, the *implied volatility* σ(K, T): the volatility input that makes the model price equal the market price. If the Black-Scholes model were literally true, σ(K, T) would be a single flat number — the same for every strike and every maturity. It is not, and the way it is not is the subject of this paper.

Plotted over its two arguments, implied volatility forms the *volatility surface*:

```
σ_imp = f(strike, time to expiry)

  strike axis   →  the "smile"/"skew" dimension (moneyness)
  maturity axis →  the "term structure" dimension
```

In words: for a fixed expiry, implied volatility varies across strikes — that cross-section is the *smile* (or, when it is one-sided, the *skew*). For a fixed strike region (say, at-the-money), implied volatility varies across expiries — that cross-section is the *term structure*. The surface is the joint object, and the two cross-sections are the two ways of slicing it. Nothing about this is exotic: the surface is simply the options market's full statement of the probability distribution it is willing to trade at every horizon, written in volatility units (Gatheral 2006).

A reader who has internalized one fact about that statement has most of what matters: for equity indices, the surface is *not symmetric*. Downside strikes trade at persistently higher implied volatility than upside strikes, at every maturity, essentially all the time. Figure 1 shows this on a real SPX chain.

![The SPX implied-volatility smile across four maturities, from Cboe's free delayed-quotes chain, snapshot 2026-09-17, spot ≈ 7,638. Each curve is one expiry — 7, 29, 92 and 183 days out — using out-of-the-money mid-quote IVs as reported by Cboe, strikes between 75% and 115% of spot, one pre-committed selection rule and no smoothing. Downside strikes carry systematically higher implied volatility at every maturity — the equity-index skew — and the smile is steepest at the shortest expiry. Reproduce with figures/fig_iv_surface.py.](figures/fig_iv_surface.png)

### 2.2 Reading a surface in sixty seconds

A surface plot — or a stack of smiles like Figure 1 — is read in four passes, in a fixed order. The order matters because each pass conditions the next.

1. **Level.** Where does the at-the-money spine sit? In Figure 1, ATM implied volatility runs from about 10.9% at 7 days to 14.5% at 183 days — a low-teens vol market, calm by historical standards (the 2009–2026 median VIX close is 16.9; Section 6). Level anchors everything: a 5-point skew means something different at VIX 13 than at VIX 35.
2. **Term slope.** Does the ATM spine rise or fall with maturity? Here it rises — 10.9, 12.1, 13.8, 14.5 across the four expiries — the *contango* shape that Section 4 will show holds about 92% of the time. An inverted spine (near-dated above long-dated) is the single most important warning the surface can issue.
3. **Skew.** How tilted is each smile? In Figure 1 the 25-delta put trades 3.3 to 5.8 volatility points above the 25-delta call, depending on maturity — the persistent equity-index put skew of Section 2.4.
4. **Curvature.** How bowed is the smile — do *both* wings lift relative to the middle? High curvature means the market pays up for movement in either direction (a "fat-tailed" read); it is most visible at short maturities, where Figure 1's 7-day smile turns sharply upward beyond ~104% of spot.

Sixty seconds, four numbers: level, term slope, skew, curvature. Every surface story you will ever hear — "vol is bid", "skew is steep", "the curve inverted", "wings are offered" — is a statement about one of these four, and the first discipline is to ask *which one* before accepting the story.

One practical detail visible in Figure 1: the minimum of each smile sits slightly *above* spot, not at it. This is normal — the smile's floor rides near the forward price (spot plus carry) rather than spot, and the skew drags the minimum further right — and it is the first of many reminders that "at-the-money" is a fuzzier phrase than it sounds.

### 2.3 Smile versus skew

The two words are often used interchangeably; they should not be. A *smile* is symmetric: both wings trade above the middle, as in currency options, where neither direction of a exchange rate is structurally more feared and the market prices fat tails on both sides. A *skew* is one-sided: one wing is persistently expensive relative to the other. Equity indices display a pronounced *put skew* — the downside wing dominates — with only a modest upside smile at short maturities (Figure 1's 7-day curve shows both: a steep left side and a visible right-wing upturn).

The distinction carries information. A symmetric smile says "we expect surprises but not their direction." A put skew says "the direction of the feared surprise is known — down — and we will pay a structural premium to insure it." When the *shape itself* changes — when an index smile becomes more symmetric because upside calls catch a bid, or when the put wing flattens — the market is telling you its asymmetry assessment has changed, and Section 3.4 treats those transitions as tradeable information about positioning.

### 2.4 Why equity-index skew is persistent

Before 19 October 1987, the S&P smile was approximately flat — Black-Scholes was, briefly, an acceptable description of index option prices. The crash repriced the left tail permanently: implied distributions since then embed a fat, negatively skewed lower tail, and the smile literature dates the modern index skew to precisely that event (Rubinstein 1994). Three mechanisms, stacked on top of each other, explain why the skew has never gone away:

- **Crash risk is real and asymmetric.** Index returns jump down, not up. A negatively skewed physical distribution justifies some put skew on expectations alone — but the observed skew is steeper than realized skewness alone can explain, which is where the next two mechanisms come in (Gatheral 2006).
- **The leverage/feedback effect.** Volatility rises when prices fall — mechanically (a firm's equity becomes a more levered claim as it loses value) and behaviorally (drawdowns trigger de-risking, which begets more movement). A negative spot-volatility correlation makes low strikes genuinely more volatile states of the world, and the smile prices that correlation (Gatheral 2006).
- **Flows: one-way insurance demand.** Institutions structurally *buy* index puts (portfolio insurance mandates) and *sell* index calls (overwriting programs). Dealers who absorb both flows are short downside and long upside, and charge accordingly. Bollen and Whaley showed that net buying pressure measurably shapes the implied-volatility function — the skew is steeper where the hedging demand lands (Bollen & Whaley 2004).

The practical consequence: *equity-index put skew is a permanent feature, not a signal by itself.* The information is never "there is skew" — there always is — but how steep it is relative to its own history, and how it is changing. Measuring that is Section 3's job.

## 3 Skew in practice

### 3.1 The 25-delta risk reversal: skew as one number

The market's standard skew ruler is the *25-delta risk reversal* (RR): the implied-volatility difference between an out-of-the-money call and an out-of-the-money put of the same expiry, each chosen at a delta of 0.25 in absolute value:

```
RR(25Δ) = IV(25Δ call) − IV(25Δ put)

  equity indices:  RR < 0   (puts richer than calls — put skew)
  more negative    = steeper skew
```

In words: take the strike where a call has a one-in-four chance-like moneyness (delta +0.25) and the strike where a put has the mirror-image moneyness (delta −0.25), and subtract the put's implied volatility from the call's. Delta is used as the ruler, rather than a fixed percentage of spot, because delta automatically scales with both maturity and volatility level — the "25-delta put" is always a comparably-out-of-the-money option, whether the expiry is a week or a year. (Sign conventions vary: some desks quote index skew as put-minus-call so the number is positive; this paper fixes call-minus-put, so equity index RRs are negative. State your convention — half of all skew confusion is sign confusion.)

From the Figure 1 snapshot, the measured risk reversals are:

| Expiry | Days | ATM IV | 25Δ put IV | 25Δ call IV | RR(25Δ) |
|---|---|---|---|---|---|
| 2026-09-24 | 7 | 10.94 | 13.05 | 9.80 | **−3.25** |
| 2026-10-16 | 29 | 12.10 | 14.87 | 10.67 | **−4.20** |
| 2026-12-18 | 92 | 13.77 | 17.39 | 12.12 | **−5.27** |
| 2027-03-19 | 183 | 14.54 | 18.56 | 12.73 | **−5.83** |

Two honest readings of this table, and they teach opposite-sounding lessons. In *delta space*, the risk reversal widens with maturity (−3.25 to −5.83): the longer-dated 25-delta strikes sit much further from spot in percentage terms, out where the skew has accumulated more total tilt. In *strike space*, the opposite is true: Figure 1 shows the 7-day smile is by far the steepest per percentage point of moneyness (its IV roughly doubles between 95% and 80% of spot, while the 183-day curve barely adds ten points over the same range). Both statements are correct simultaneously because the two rulers measure different things — and this is the first, small instance of the paper's recurring warning: *a skew number without its coordinate system attached is not yet information.*

### 3.2 Fixed-strike versus fixed-delta reads

The coordinate-system warning becomes essential the moment you compare skew (or any implied volatility) *across time*. There are two ways to do it:

- **Fixed-delta (floating) read:** compare "the 25-delta put IV" today against "the 25-delta put IV" yesterday. Convenient — every option chain hands you the number — but the *option itself changed*: after a 2% rally, today's 25-delta put is a different strike than yesterday's. The comparison mixes two effects: genuine repricing of risk, and the mechanical slide of the measurement point along a (possibly unchanged) surface.
- **Fixed-strike read:** compare the *same strike's* implied volatility today against yesterday. This is the clean question — "did the market reprice this actual claim?" — because the instrument is held constant and only its price changed.

The classic trap the fixed-strike read exposes: the index rallies 2%, and ATM implied volatility "falls" half a point. Bearish vol crush? Often not — if the surface is skewed and simply *did not move*, then the new at-the-money sits where a below-market strike used to sit, further down the skew, and the "fall" in ATM IV is pure geometry. Traders call this *rolling down the skew*. Checking the fixed-strike vols tells you which world you are in: if the old strikes are unchanged, nothing was repriced; if fixed-strike vols themselves dropped, volatility was genuinely sold. Section 5 builds this observation into the sticky-strike/sticky-delta framework, where it acquires named regimes and published evidence.

The working rule this paper will keep re-using: *fixed-delta reads for level-independent comparisons across maturities and markets; fixed-strike reads for "what actually repriced?" questions across time.*

### 3.3 Skew as positioning information

Why watch skew at all, if it is always there? Because its *steepness relative to its own history*, and its *changes*, encode where hedging demand currently sits — and hedging demand is positioning you cannot see on any chart of the underlying.

- **Steep and steepening skew** means the crash-insurance bid is intense: put buyers are paying up faster than call buyers. Typical late-cycle or high-anxiety signature; it also mechanically sharpens the downside feedback loop, because a steep skew concentrates dealers' short-put exposure where a sell-off will find it (this connects to the vanna/charm flow machinery of the dealer-flows-and-GEX paper: the steeper the skew, the more delta the dealer community must adjust when volatility moves).
- **Flattening skew into a decline** is ambiguous and worth respect: it can mean hedges are being *monetized* (puts sold back after paying off), or that the anxiety has migrated from the tail to at-the-money — ATM IV rising faster than wing IV compresses the measured skew even as absolute fear rises. Again the ruler matters: in a genuine vol spike, *every* fixed-strike vol is up; the risk reversal may still "flatten." Read levels and skew together, never skew alone.
- **A flat skew in a fragile market** is the configuration practitioners fear most: it means the market is *not* paying for crash protection — no insurance bid, thin dealer long-put inventory — so if a shock arrives, the repricing starts from scratch and moves fast. Cheap insurance in a fragile house is not a comfort; it is a statement that nobody bothered to insure.

A caution on all three readings: skew measures conflate expectations, risk premia, and inventory. The literature's cleanest result is the flow one — net buying pressure shapes the smile (Bollen & Whaley 2004) — which is precisely why skew is best read as *positioning* information rather than as a directional forecast. Section 6.4 will show empirically that a popular tail-risk index built on skew (Cboe SKEW) has drifted structurally higher for decades, which is exactly what sustained growth in institutional tail-hedging programs would produce, and exactly what a naive "high skew = crash imminent" reading would misinterpret.

### 3.4 Skew around events

Scheduled events — CPI prints, FOMC decisions, earnings — bend the surface in characteristic, repeatable ways, and skew participates:

- **Before the event**, uncertainty concentrates in the expiries that span it. ATM IV of the spanning expiry inflates (the *event bump* of Section 4.3), and because the fear usually has a direction, the bump is rarely symmetric: into an inflation print or a central-bank decision, downside strikes of the spanning expiry typically inflate more, steepening the short-dated skew. Into a single stock's earnings, the smile often becomes more *symmetric* instead — both wings bid — because the surprise direction is genuinely unknown.
- **After the event**, the resolved uncertainty leaves the surface at once: the spanning expiry's IV collapses (*the IV crush*), the short-dated skew relaxes toward its baseline, and the term structure re-steepens into contango. Section 4.3 quantifies the term-structure half of this cycle; the skew half is its mirror.
- **The read-through:** event-driven skew steepening is *scheduled repricing*, not new information about regime. The skew move that matters for regime is the one *not* attached to any calendar entry — a steady, dateless steepening (persistent hedge accumulation) or an unexplained flattening (insurance abandoned). Separating calendar-driven from dateless skew changes is one of the highest-value habits in daily surface reading.

## 4 The term structure of volatility

### 4.1 Contango is the normal state; backwardation is the alarm

The term structure is the maturity cross-section of the surface: at-the-money implied volatility read as a function of time to expiry. For the index as a whole the market publishes two convenient points on that curve every day — the VIX (a 30-day constant-maturity SPX volatility) and the VIX3M (the identical construction at 93 days) — and their relationship names the two regimes.

When longer-dated volatility trades above shorter-dated (VIX3M > VIX, an upward-sloping curve), the term structure is in *contango*. When the near dates trade above the far dates (VIX > VIX3M, inverted), it is in *backwardation*. Figure 2 measures how lopsided these two states are on 4,274 common sessions from September 2009 to September 2026: the curve is in contango on **92.4%** of days and in backwardation on only **7.6%**. Contango is not a mild tendency; it is the resting state of the index vol curve.

The reason is the *variance risk premium* seen from the maturity axis. On a calm day the market expects little movement over the next month, but it will not sell three-month protection nearly as cheaply, because three months is long enough for something to go wrong and the seller demands to be paid for that tail. So the far end sits above the near end by default. That default breaks only when the *near* term becomes acutely dangerous — an unfolding crash, a liquidity event — and short-dated demand for protection overwhelms the far end. Backwardation is therefore not a calendar quirk; it is the surface saying the danger is *now*, not later.

The data make the point without any threshold-fitting. The median VIX on contango days is **16.4**; on backwardation days it is **27.8** — inversions live in a different, higher-volatility world. Backwardation also comes in bursts: across the seventeen years there are 105 distinct inverted episodes but only 15 that last five sessions or more, and the longest on record is the COVID crash (24 February to 23 April 2020, 43 straight sessions, the ratio peaking at 1.34 on 28 February). The 2011 US-downgrade sell-off, the December 2018 drawdown, and the April 2025 tariff shock are the other multi-week inversions in the sample. The practical read is blunt: *a persistently inverted curve is one of the highest-information states the vol market offers, and it is rare enough to take seriously every time.*

![The term structure of Cboe index volatility, 2009-2026. Top panel: daily closes of VIX (30-day) and VIX3M (93-day) on free Cboe data, 4,274 common sessions to 2026-09-16. Bottom panel: the slope VIX/VIX3M, with backwardation (ratio above 1) shaded. The curve is in contango on 92.4% of sessions and inverted on only 7.6%; the median VIX is 16.4 in contango versus 27.8 in backwardation, so inversion is a stress state rather than a calendar artefact. The longest inversion on record is the COVID crash (24 Feb to 23 Apr 2020, 43 sessions, peak ratio 1.34). Reproduce with figures/fig_term_structure.py.](figures/fig_term_structure.png)

### 4.2 Two different "term structures" — resolving the VIX-futures confusion

Traders use the phrase "the VIX term structure" for two different objects, and conflating them causes real errors.

- **The spot IV term structure** is what Figure 2 plots: implied volatilities of options *trading today* at different expiries. VIX and VIX3M are two points on it — 30-day and 93-day constant-maturity SPX vol computed from today's SPX option prices. It is a statement about today's option chain.
- **The VIX futures curve** is a curve of *futures prices on the VIX index* at different settlement months. Each future settles to the *spot VIX on its expiry date*, so it is the market's forward-looking price for "the 30-day SPX vol that will prevail one, two, three months from now," plus a risk premium for holding that exposure.

They are cousins, not twins. Both are usually upward-sloping and both invert in stress, because the same fear that lifts near-dated spot vol also lifts near-dated futures. But they answer different questions. The spot curve compares *option maturities as of today*; the futures curve compares *future dates for a single 30-day vol measure*. Crucially, only the futures curve carries a *roll yield* — the mechanical gain or loss from holding a futures position as it converges to spot over time — and it is that roll, not the spot curve, that drives volatility ETPs (Section 8). A note that says "the term structure is in contango, so short-vol is a carry trade" is talking about the futures curve; a note that says "three-month implied is above one-month" is talking about the spot curve. Keep them apart.

One clean way to hold the distinction: the spot curve is a *snapshot* of the surface's maturity axis; the futures curve is the market's *forecast path* for one point on that axis. Figure 2 is the snapshot.

### 4.3 Event bumps

Scheduled events distort the near end of the curve in a predictable way. An option that spans a known event — a CPI print, an FOMC decision, a single name's earnings date — must price the extra variance of that one day, so the *implied volatility of the spanning expiry inflates* relative to its neighbours. On the term structure this shows up as a local hump: the expiry just after the event sits above the smooth curve, and the expiries before it do not.

This can locally invert the very front of the curve without any market-wide stress: in the days before a major macro print, one-week implied can trade above one-month simply because the one-week window is *all event and the one-month window dilutes it*. That is why the front-of-curve gauges (Cboe VIX9D, VIX1D) can spike into an event and collapse the morning after — they are dominated by the single fattest day they contain. The morning after the event the resolved uncertainty leaves the surface at once (the *IV crush*), the hump disappears, and the curve re-steepens into its normal contango. Section 3.4 described the skew half of this cycle; the term-structure half is its mirror image, and the two happen together.

The operational lesson is to *decompose the curve before reading it*: a front-end bump that lines up exactly with a calendar entry is scheduled repricing and carries no regime information, whereas a front-end bump with no event behind it is the market pricing an unscheduled danger — which is exactly the signal worth having.

### 4.4 Forward volatility, by hand

Because *variance* (volatility squared × time) is additive along non-overlapping windows, the term structure lets you extract the volatility the market implies for a future window that has not started yet — the *forward volatility*. If σ₁ is the implied volatility to a near date T₁ and σ₂ the implied volatility to a far date T₂, then the total variance to T₂ splits into the variance up to T₁ plus the forward variance of the window (T₁, T₂):

```
σ₂² · T₂ = σ₁² · T₁ + σ_fwd² · (T₂ − T₁)

⇒  σ_fwd = √[ (σ₂²·T₂ − σ₁²·T₁) / (T₂ − T₁) ]
```

In words: the far-dated variance is a time-weighted blend of the near window and the forward window, so to recover the forward window you strip the near variance out of the far variance and re-annualize over the days that remain. Take the latest Figure 2 closes — VIX = 17.71 at 30 days and VIX3M = 19.73 at 93 days:

```
σ_fwd(30, 93) = √[ (19.73² · 93 − 17.71² · 30) / (93 − 30) ]
              = √[ (36,202 − 9,409) / 63 ]
              = √425.3  =  20.6
```

The market implies about **20.6** volatility points for the 63-day window that *begins* 30 days from now. Notice it exceeds both the 30-day (17.71) and the 93-day (19.73) figures: on an upward-sloping curve the forward vol is always the steepest point, because the far-dated average can sit above the near-dated one only if the marginal window being added is more expensive still. This is the same fact as "VIX3M is a blend of VIX and the forward," read backwards. Forward vol is the honest object to compare against your own view of what a *future* month will be worth; comparing your one-month-in-one-month view against spot VIX compares two different windows and is the most common way traders mis-state a calendar spread.

## 5 How the surface moves

Knowing the shape of the surface is half the job; the other half is knowing how it *moves* when spot moves, because that is what determines the profit and loss of anything with vega or gamma. Two idealized rules bracket the possibilities.

### 5.1 Sticky-strike versus sticky-delta

- **Sticky-strike.** Each fixed strike keeps its implied volatility as spot moves. The whole smile stays pinned to the strike axis; the at-the-money point simply *slides along* the existing skew as spot travels. Consequence: when the index falls, the new (lower) at-the-money strike inherits the higher implied vol that used to belong to an out-of-the-money put — so *ATM vol rises as the market falls* purely by geometry, with no fixed-strike vol changing at all.
- **Sticky-delta (sticky-moneyness).** The smile is a function of *moneyness* (or delta), not of absolute strike, so it *floats with spot*: as the index moves, the whole smile shifts sideways to stay centred on the new spot. Consequence: fixed-strike vols change as spot moves, but the at-the-money vol and the delta-space skew stay put.

The two rules make opposite predictions about the same event, which is why you cannot reason about a vol P&L without committing to one. Under sticky-strike a rally leaves your fixed-strike vols untouched; under sticky-delta the same rally drags every strike's vol down as the smile floats up and away from it. A vertical spread, a calendar, a delta-hedged straddle — each has a different sign of exposure under the two rules.

### 5.2 Which regime, when — the evidence

Derman's classic study of a year of S&P implied volatilities found that neither rule holds always; the market *switches regimes* with its mood (Derman 1999):

- **Range-bound markets → sticky-strike.** When the index chops in a range with no trend, strikes behave like fixed reference points and their vols stay put — the complacent regime.
- **Steadily trending markets → sticky-moneyness (sticky-delta).** When the index trends calmly, the smile travels with it, keeping the same shape in moneyness terms.
- **Jumpy, fearful markets → the surface over-reacts.** In stress the whole surface lifts *more* than sticky-strike would predict: ATM vol rises faster than the market falls, because a sell-off has simultaneously repriced every fixed-strike vol upward (Derman's "sticky implied-tree," or fear, regime).

The regime is not decoration — it decides which way a hedge leans. The empirical anchor in this paper is consistent with the fear regime: Figure 2 shows the curve inverts precisely when the near-term surface lifts hardest (median VIX 27.8 in backwardation versus 16.4 in contango), i.e. sell-offs raise the *level* of the whole surface rather than merely sliding the ATM point along a frozen skew. Practitioners therefore treat sticky-strike as the fair-weather default and expect the surface to *over-shoot* it whenever volatility itself starts moving.

### 5.3 Sell-offs versus melt-ups

The asymmetry of the skew makes the surface move asymmetrically:

- **In a sell-off** the whole surface lifts, the skew *steepens* (put wings bid hardest), and the term structure flattens and can invert into backwardation. Volatility and price move together and violently — the leverage/feedback effect of Section 2.4 in real time.
- **In a melt-up** volatility usually *bleeds* lower as the index grinds up, and the skew often stays stubbornly steep or even steepens (an upside grind does not relieve crash fear, and call overwriting caps the upside wing). Occasional "melt-up panics" — a scramble to buy calls in a fast squeeze — briefly lift the upside wing, but they are rare and short. The base case is: down moves are loud in vol, up moves are quiet.

This is why "volatility is mean-reverting" is true but incomplete: it reverts down slowly along the contango and jumps up fast into backwardation, and a symmetric mental model of vol mis-prices both tails.

### 5.4 Fixed-strike vol as the cleaner lens

Across all of these cases the measurement that stays honest is *fixed-strike volatility* — the implied vol of one specific, unchanging strike tracked through time. It answers the only unambiguous question — "did the market reprice *this* claim?" — because the instrument is held constant while spot, ATM, and the delta-space smile all move around it. Under pure sticky-strike, fixed-strike vols are flat and everything else is geometry; under sticky-delta they move; in a genuine vol event they all jump together. Reading fixed-strike vols therefore tells you *which regime you are in*, which no floating measure can do. The working discipline from Section 3.2 stands: floating (fixed-delta) reads for level-independent comparisons across maturities and markets; fixed-strike reads whenever the question is what actually repriced.

## 6 The Cboe volatility-index complex

The Cboe publishes a family of indices that each summarize one slice of the SPX (and NDX) surface into a single daily number. Read together they are a dashboard; read naively they are six ways of saying the same thing. This section takes them one at a time — construction, what each *uniquely* measures, and typical range on the common 2009–2026 sample of Figure 4 — and then asks how much of the dashboard is redundant.

### 6.1 VIX — the 30-day level (recap)

The VIX is a *model-free* estimate of the risk-neutral expected volatility of the S&P 500 over the next 30 calendar days. It is not read off any single option; it is a weighted strip of *all* out-of-the-money SPX options across two nearby expiries, combined to replicate a 30-day variance swap and quoted as an annualized volatility (Cboe VIX methodology). Because it integrates the whole OTM smile it already contains skew information — a steeper put wing mechanically lifts the VIX — which is worth remembering before treating VIX and SKEW as independent, and which is why the VIX (17.7 on 2026-09-16) sits several points above the ~12% 30-day *at-the-money* SPX vol of Figure 1. On the common sample the VIX ran a p10–median–p90 of **12.4 / 16.9 / 26.7**, with a floor near 9.1 and a crisis peak of 82.7. Low-teens is calm; the low-20s is watchful; above ~30 is stress.

### 6.2 VIX3M — the 93-day level

VIX3M applies the identical variance-swap construction at a 93-day (three-month) constant maturity. Alone it is nearly redundant with the VIX (see Section 6.7); its value is *relative* — the pair (VIX, VIX3M) is the term-structure slope of Section 4, the single most useful two-number reading in the complex. Range on the sample: **14.6 / 19.2 / 28.6**, sitting above the VIX by construction most of the time (that gap *is* the contango).

### 6.3 VVIX — the volatility of volatility

VVIX applies the VIX construction to *VIX options*: it is the 30-day implied volatility of the VIX itself (Cboe VVIX methodology). It measures how uncertain the market is about future volatility — the convexity of the vol surface's own moves. VVIX can rise while the VIX is flat, when traders bid up VIX calls in anticipation of a vol spike; that divergence is its unique signal. Range: **78.8 / 92.5 / 116.3**, spiking to 208 in March 2020. A high VVIX is the market pricing a *fat right tail in volatility itself* — and, through the vanna of dealers' VIX-option books, it is a gate on how reflexive a vol move will be (the bridge to the dealer-flows-and-GEX paper, Section 7.2).

### 6.4 SKEW — the price of the tail

The Cboe SKEW index is derived from the same OTM SPX strip as the VIX, but it isolates the *risk-neutral skewness* of the 30-day return distribution — the relative price of far-downside puts. It is scaled so that 100 means a normal (symmetric) implied distribution and higher values mean a fatter, more negatively skewed left tail; typically it sits between about 115 and 150. Its unique content is *tail shape independent of level*: SKEW can be high while the VIX is low, which says the body of the distribution is calm but the left tail is richly priced.

But SKEW must be read against its *own recent history*, never against an absolute yardstick, because it has drifted structurally upward for a third of a century. Figure 3 shows the full 1990–2026 record: the decade mean climbs from **115.9** in the 1990s to **116.7** (2000s), **126.2** (2010s), and **139.5** in the 2020s. That drift is what sustained growth in institutional tail-hedging would produce — a permanent bid under downside puts — and it is exactly what a naive "SKEW above 140 means a crash is imminent" reading misinterprets: 140 was a rare alarm in 1995 and is an ordinary Tuesday in 2025. SKEW is *positioning* information about tail demand, not a dated crash forecast — the same caution Section 3.3 raised about skew generally, now visible in a third of a century of one index.

![The Cboe SKEW index, 1990-2026: 9,228 daily closes on free Cboe data (thin line) with a 252-day moving average (heavy line) and the full-sample mean of 123. Tail-risk pricing has drifted structurally higher — decade means rise from 115.9 in the 1990s to 116.7 in the 2000s, 126.2 in the 2010s, and 139.5 in the 2020s — so a SKEW level that was extreme in the 1990s is ordinary today, which is why SKEW must be read against its own recent range. Reproduce with figures/fig_skew_history.py.](figures/fig_skew_history.png)

### 6.5 COR1M and COR3M — implied correlation

The implied-correlation indices back out the *average pairwise correlation* the market is pricing among the largest S&P components, by comparing the implied variance of the index with the implied variances of its top constituents (Cboe implied-correlation methodology). Index variance is the sum of single-name variances scaled by their average correlation, so given both legs the correlation falls out; COR1M is the one-month horizon, COR3M the three-month. Its unique content is *how much of index risk is systematic versus stock-specific*: a high reading means names are moving together (macro-driven, risk-on/risk-off), a low reading means they are rotating against each other (a dispersion, stock-picker's market). Range on the sample: **13 / 34 / 60**, and — tellingly — it correlates −0.65 with SKEW in levels (Section 6.7), because a market that fears a *systemic* down-move prices both high correlation and a fat left tail at once.

### 6.6 VXN — the Nasdaq-100 analog

VXN is the VIX methodology applied to Nasdaq-100 (NDX) options: the 30-day model-free implied volatility of the tech-heavy index. Its unique content is *which index the fear is in*. Because NDX is more concentrated and higher-beta than the S&P, VXN trades above the VIX almost all the time — on **95.4%** of common-sample days, with a median VXN/VIX ratio of **1.17** (range 0.76 to 1.73). Its own level ran **14.5 / 19.8 / 30.7**. The ratio itself is the interesting object, and Section 9 reads it as a cross-index signal.

### 6.7 Redundancy: how many independent axes are there really?

Six indices do not mean six independent readings. Figure 4 computes the Pearson correlation among all six, twice — on daily *levels* and on daily *changes* — over the 4,267 common sessions.

The result is stark. VIX, VIX3M and VXN form one tight block: their pairwise level correlations run **0.94 to 0.97**. For daily-change purposes these three are effectively *one instrument wearing three labels* — a single "equity-index vol level" factor. VVIX is closely tied to that level factor in changes (0.74 to 0.79) but looser in levels (~0.64), i.e. it mostly moves *with* vol but carries extra information about how convex the move is. The two genuinely different axes are SKEW and COR1M: SKEW is nearly *orthogonal* to the VIX level (−0.21 in levels, −0.13 in changes), and COR1M, while it rises with vol (~0.60 with the VIX), carries a large dispersion component the level factor misses. SKEW and COR1M share their own axis — the −0.65 level correlation noted above — so they are not independent of each other either.

The practical distillation: the complex has roughly *three* independent dimensions, not six — **(1)** a level/term factor (take the VIX plus the VIX3M slope), **(2)** a vol-of-vol / convexity factor (VVIX), and **(3)** a tail-and-dispersion factor (SKEW with COR1M). A daily read that tracks one representative from each captures nearly everything the six-index dashboard contains; adding the redundant members back in mostly adds the illusion of confirmation. That distillation is the input to the factor set of Section 7.

![Pearson correlation among six members of the Cboe volatility complex — VIX, VIX3M, VXN, VVIX, SKEW, COR1M — over 4,267 common daily sessions (2009-2026), computed on daily levels (left) and daily changes (right). VIX, VIX3M and VXN form one tight block (level correlations 0.94 to 0.97) and are effectively one instrument; VVIX co-moves with that level factor (0.74 to 0.79 in changes) but adds convexity information; SKEW is nearly orthogonal to the level (about -0.2), and COR1M carries a large dispersion component while sharing a -0.65 axis with SKEW. The six indices span roughly three independent dimensions. Reproduce with figures/fig_complex_matrix.py.](figures/fig_complex_matrix.png)

## 7 A working vol-factor set

The redundancy analysis licenses a compact, numeric daily read. The design goal is deliberately modest: a handful of *orthogonal* factors, each quoted as a number against its own history, with a standing rule that the numbers overrule any story told about a single index. This is the publication-grade version of a pre-session volatility checklist.

### 7.1 The term-structure slope as a numeric regime gate

The first factor is the slope of Section 4, quoted as the ratio VIX / VIX3M. It is a *gate*, not a vibe:

```
slope = VIX / VIX3M
  < 1.00   contango       — normal / carry regime
  ≈ 1.00   flat           — transition; watch
  > 1.00   backwardation  — stress regime; near-term danger dominant
```

The latest close puts the ratio at **0.90** — solid contango, the calm regime, consistent with the sub-8% of days that are inverted. The point of quoting the number is that it *overrules* the reflexive narrative: "positive dealer gamma means the day will chop" is a story, but a slope that has ticked above 1.00 is a measurement, and when they disagree the measurement wins. A numeric gate cannot be argued with after the fact, which is its whole value.

### 7.2 VVIX as a vanna-flow gate

The second factor is VVIX, read as a convexity gate. When VVIX is elevated relative to its ~92 median, the market is paying up for VIX optionality, which means dealers who are short those VIX options carry more *vanna* — sensitivity of delta to volatility — and must hedge more aggressively as vol moves. That hedging is pro-cyclical: it amplifies vol spikes and accelerates vol collapses. A high VVIX therefore flags that any move in the vol level is likely to be *reflexive* rather than orderly — the direct bridge to the dealer-flow mechanics of the dealer-flows-and-GEX paper (charm/vanna). VVIX near its median says the opposite: vol will move, if it moves, without a convexity amplifier behind it.

### 7.3 Combining level, slope, VVIX, skew, and correlation into one read

Five numbers, each against its own recent range, give a compact daily state vector — the five spanning the roughly three independent dimensions of Section 6.7, reported separately because each carries a distinct operational meaning even where two share an axis:

| Factor | Instrument | Reads | Latest value (2026-09-16) |
|---|---|---|---|
| Level | VIX | how large moves are, in vol points | 17.7 — low-teens, calm |
| Term slope | VIX / VIX3M | regime gate (contango/backwardation) | ratio 0.90 — contango |
| Vol-of-vol | VVIX | convexity / reflexivity of vol moves | 95 — near median |
| Tail | SKEW (vs own range) | demand for downside insurance | 146 — high in its recent range |
| Dispersion | COR1M | systematic vs stock-specific risk | 14 — very low; a dispersion, stock-picker's tape |

Read as a sentence: *calm level, contango slope, ordinary vol-of-vol, well-bid tail, and unusually low correlation* — a benign, stock-picking regime in which index-level fear is quiet but someone is still paying for the tail, and index moves are being diluted by names rotating against each other. The value of the vector is that it forces all five readings onto the table at once; any four of them agreeing cannot be quietly dropped because the fifth tells a nicer story.

### 7.4 The overruling rule

The one non-negotiable rule that makes the factor set worth having: *a numeric factor overrules a single-index narrative.* If the slope is in backwardation, "but the VIX is only 18" does not rescue a calm thesis; if COR1M is at 14, "but it feels like a macro tape" does not override the measured dispersion. Narratives are hypotheses; the factors are the data, pre-committed and read the same way every day. This is the same discipline the backtesting paper enforces in time — decide the reading rule before the day, not after it.

## 8 Volatility products and their flows

Everything so far treats the surface as information. But the surface is also *traded*, through futures and exchange-traded products, and once enough capital tracks a rule mechanically the flow those products generate can move the very thing they track. This section is context, not advice.

### 8.1 VIX futures, ETPs, and roll yield

You cannot trade the VIX itself — it is a calculation, not an asset. Exposure comes through *VIX futures* and the ETPs built on them. A long-vol ETP (e.g. VXX) holds a rolling position in near-dated VIX futures; an inverse ETP (e.g. the pre-2018 XIV, or SVXY) holds the short side. Because the VIX futures curve is in contango most of the time (Section 4.2), a long-vol holder suffers *negative roll yield*: each day the future it owns rolls down toward a lower spot, so holding the position bleeds value even if spot VIX never moves. The inverse holder harvests exactly that roll as positive carry. This is why long-vol ETPs are structurally decaying instruments, and why inverse-vol ETPs looked, for years, like free money — a carry trade that pays a little every calm day and is short a rare catastrophe.

The catastrophe is not incidental; it is the other side of the carry. An inverse-vol product must *rebalance daily* to keep constant leverage: when VIX futures rise, its short position has grown, so to restore target exposure it must *buy* VIX futures — buying into a rising market. On a small move this is trivial. On a large move it is a feedback loop.

### 8.2 February 2018 — "Volmageddon"

The loop closed on 5 February 2018. A routine equity sell-off pushed VIX futures up during the day; the inverse-vol ETPs (XIV and SVXY together held several billion dollars of short-vol exposure) needed to buy futures into the close to rebalance; that buying pushed futures higher still; which enlarged the rebalancing need; and so on. Figure 5 shows the result: the VIX closed at **37.32**, up **+115.6%** from the prior close of 17.31 — the *largest one-day percentage rise in VIX history since 1990*, rank 1 of 9,273 daily moves.

The products built on the short side were destroyed. SVXY, indexed to 100 at the start of January, fell to **54** by the close of 5 February and to **9** the next day — an overnight loss of about **−83%**, and roughly **−91%** from its January peak. Credit Suisse's XIV, having lost the great majority of its value overnight, was terminated under its acceleration clause. The move in the underlying was not driven by fresh news proportionate to a doubling of the fear gauge; a meaningful part of it was the *forced hedging flow of the products themselves* — a structural, mechanical bid that had to be met regardless of price.

Volmageddon is the canonical case of the paper's structural theme: *when a product's rebalancing rule becomes large enough relative to the market it hedges in, the flow is the fundamental.* It is the clearest real-world instance of the reflexivity that VVIX (Section 7.2) tries to flag in advance, and the reason "short vol carry" and "picking up pennies in front of a steamroller" are the same sentence.

![February 2018 Volmageddon. Top: the VIX (Yahoo daily closes) around 5 February 2018, when it closed at 37.3 — up 115.6% from the prior close, the largest one-day percentage rise in VIX history since 1990 (rank 1 of 9,273 daily moves). Bottom: the inverse-volatility ETP SVXY indexed to 100 at 2 January 2018, which lost about 83% overnight into 6 February and roughly 91% from its January peak. The loop: rising VIX futures force inverse-vol ETPs to buy futures to rebalance, pushing futures higher and enlarging the next rebalance — a structural flow driving the index it tracks. Reproduce with figures/fig_volmageddon.py.](figures/fig_volmageddon.png)

## 9 Cross-index and cross-asset structure

### 9.1 VXN versus VIX — when Nasdaq vol decouples

VXN and VIX measure the same thing on two different indices, and their *ratio* is a cross-index reading. Because the Nasdaq-100 is more concentrated and higher-beta, VXN sits above the VIX on 95.4% of days, at a median ratio of 1.17 (Section 6.6). The information is in the *deviations*: when the ratio climbs well above 1.2, tech-specific risk is being priced *on top of* market-wide risk — an earnings-heavy mega-cap week, an AI-capex scare, a rates move that hits long-duration growth hardest. When it compresses toward 1.0, the fear is broad and macro, hitting both indices alike. A VXN spike with a quiet VIX is a decoupling worth noticing: the danger is in the growth complex, not the whole tape. The ratio's own range on the sample (0.76 to 1.73, Section 6.6) sets the yardstick; like every factor in Section 7, it is read against its history, not an absolute line.

### 9.2 Single-name versus index volatility — dispersion in one page

Index volatility is not the average of its members' volatilities; it is that average *scaled by how much the members move together*. For an index of weighted single-name variances the identity is, to a good approximation:

```
σ_index²  ≈  ρ̄ · (Σ wᵢ σᵢ)²      (with a small idiosyncratic correction)
```

In words: index variance is the average pairwise correlation ρ̄ times the square of the weighted-average single-name volatility. The consequence is the entire dispersion story. If correlation is low, the index is far *calmer* than its typical member, because the members' moves cancel — this is diversification, priced. If a shock drives correlation toward 1, that cushion vanishes and index vol rises toward the single-name average even if no individual stock got much more volatile. This is why COR1M (Section 6.5) is its own factor: it is the hinge between the two regimes. The *dispersion trade* — selling index volatility while buying single-name volatility, or the reverse — is a direct bet on ρ̄, and the implied-correlation indices are simply that bet quoted as a number. For the surface reader the take-home is compact: a low COR1M means index protection is cheap *because* diversification is doing the work, and a spike in COR1M is the market repricing the possibility that it will stop (Cboe implied-correlation methodology).

## 10 Common misconceptions

- **"The VIX predicts market direction."** It does not. VIX is a *level* — the price of 30-day SPX variance — not a sign. A high VIX says moves will be large, not that they will be down; the down-bias people associate with it comes from the fact that vol spikes *coincide* with sell-offs, not that vol *forecasts* them.
- **"VIX is the market's forecast of realized volatility."** It is a *risk-neutral* expectation and sits above subsequently realized volatility on average, by the variance risk premium (the volatility-fundamentals paper). Reading VIX 20 as "the market expects 20% realized" overstates the forecast by the premium.
- **"High SKEW means a crash is coming."** SKEW has drifted structurally higher for three decades (Section 6.4); an absolute reading that was extreme in the 1990s is ordinary today. SKEW is tail-*demand* information read against its own recent range, not a dated alarm.
- **"Contango means the market is calm, full stop."** Contango is the *normal* state (92% of days); its presence alone tells you little. The information is in the *size and changes of the slope*, and above all in the rare switch to backwardation.
- **"ATM vol fell after the rally, so volatility was sold."** Often it is pure geometry — the new ATM strike rolled down a static skew (Section 3.2, Section 5.4). Only the fixed-strike vols say whether anything was actually repriced.
- **"The VIX term structure and the VIX futures curve are the same thing."** Related, not identical (Section 4.2): one is today's option maturities, the other is futures on future spot VIX. Only the futures curve carries the roll yield that drives ETPs.
- **"Short-vol is free carry."** It is carry that is *short a rare catastrophe*; February 2018 (Section 8.2) priced the catastrophe in a single session.

## 11 Glossary

- **Implied volatility surface** — implied volatility as a joint function of strike and expiry; the options market's full statement of the return distribution at every horizon.
- **Smile / skew** — the strike cross-section of the surface; a *smile* is symmetric (both wings up), a *skew* is one-sided (equity indices: put wing richer).
- **Moneyness** — a strike's position relative to spot or forward, often expressed in delta so it scales with maturity and vol.
- **25-delta risk reversal** — IV(25Δ call) − IV(25Δ put); the standard one-number skew measure (negative for equity indices under this paper's convention).
- **Fixed-strike vs fixed-delta read** — comparing a fixed strike's IV over time ("what repriced?") versus a fixed delta's IV over time (level-independent, but the option itself changes).
- **Term structure** — the maturity cross-section of the surface; ATM implied vol as a function of time to expiry.
- **Contango / backwardation** — upward-sloping term structure (far > near; the normal state) versus inverted (near > far; stress).
- **Forward volatility** — the implied volatility of a future window between two expiries, recovered from the additivity of variance.
- **Sticky-strike / sticky-delta** — regimes for how the surface moves with spot: strikes hold their vol (ATM slides along the skew) versus the smile floats with spot (fixed-strike vols move).
- **Fixed-strike volatility** — the IV of one unchanging strike tracked through time; the cleanest lens on what the market actually repriced.
- **VIX / VIX3M** — model-free 30-day and 93-day SPX implied volatility; their ratio is the term-structure slope.
- **VVIX** — the implied volatility of the VIX (vol of vol); a convexity / reflexivity gauge.
- **SKEW** — Cboe index of the risk-neutral tail (downside) skewness of the 30-day SPX distribution; 100 = symmetric.
- **COR1M / COR3M** — implied average pairwise correlation of the largest S&P constituents; a dispersion gauge.
- **VXN** — the VIX construction applied to the Nasdaq-100; VXN/VIX is a cross-index reading.
- **Roll yield** — the mechanical gain/loss of holding a futures position as it converges to spot; negative for long-vol in contango.
- **Volatility ETP** — exchange-traded product tracking VIX futures (long or inverse); it rebalances daily, which can feed back into the futures it holds.
- **Dispersion** — the gap between index volatility and average single-name volatility, governed by implied correlation.
- **Variance risk premium** — the systematic excess of implied over subsequently realized volatility.
- **Vanna** — sensitivity of an option's delta to changes in volatility; the channel by which VVIX-priced convexity becomes dealer hedging flow.

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| Persistent equity-index put skew across four SPX maturities; 25-delta risk reversals from −3.25 to −5.83 (snapshot 2026-09-17) | Own reproducible computation — `figures/fig_iv_surface.py` |
| The index vol term structure is in contango on 92.4% of sessions and backwardated on 7.6%; median VIX 16.4 versus 27.8 | Own reproducible computation — `figures/fig_term_structure.py` |
| The Cboe SKEW index has drifted structurally higher — decade means from 115.9 (1990s) to 139.5 (2020s) | Own reproducible computation — `figures/fig_skew_history.py` |
| VIX, VIX3M and VXN form one block (level correlations 0.94–0.97); the six-index complex spans roughly three independent dimensions | Own reproducible computation — `figures/fig_complex_matrix.py` |
| February 2018 "Volmageddon": VIX +115.6% (largest one-day rise since 1990), SVXY about −83% overnight | Own reproducible computation — `figures/fig_volmageddon.py` |
| The modern equity-index skew dates to the October 1987 crash | Literature — (Rubinstein 1994) |
| Net option buying pressure measurably shapes the implied-volatility function | Literature — (Bollen & Whaley 2004) |
| The surface switches between sticky-strike and sticky-delta regimes with market conditions | Literature — (Derman 1999) |
| Persistent index skew reflects crash asymmetry and negative spot–volatility correlation | Literature — (Gatheral 2006) |
| The VIX/VVIX/SKEW/implied-correlation indices are model-free constructions from option strips | Literature — (Cboe methodologies) |
| Reading a surface in four passes (level, term slope, skew, curvature) and the fixed-strike vs fixed-delta discipline | Practitioner consensus — not independently verified |
| The compact five-factor daily read, with a numeric factor overruling any single-index narrative | Practitioner consensus — not independently verified |

## References

- Bollen, N. P. B., & Whaley, R. E. (2004). Does net buying pressure affect the shape of implied volatility functions? *The Journal of Finance, 59*(2), 711–753.
- Cboe Global Markets. *Cboe Volatility Index (VIX) — White Paper: VIX Index Methodology.* Chicago: Cboe Global Markets (published at cboe.com).
- Cboe Global Markets. *Cboe VVIX Index, Cboe SKEW Index, and Cboe Implied Correlation Index (COR1M/COR3M) methodologies*, and the *Cboe Nasdaq-100 Volatility Index (VXN)* description. Chicago: Cboe Global Markets (published at cboe.com).
- Derman, E. (1999). *Regimes of Volatility.* RISK, April 1999. Author-hosted: <https://emanuelderman.com/regimes-of-volatility-risk-april-1999/>.
- Gatheral, J. (2006). *The Volatility Surface: A Practitioner's Guide.* Hoboken, NJ: Wiley.
- Rubinstein, M. (1994). Implied binomial trees. *The Journal of Finance, 49*(3), 771–818.
- Sinclair, E. (2013). *Volatility Trading* (2nd ed.). Hoboken, NJ: Wiley.

*All references above are publicly accessible: two are published books (Gatheral; Sinclair), two are peer-reviewed journal articles (Bollen & Whaley; Rubinstein), one is an author-hosted research note (Derman, direct link), and two are the exchange's own publicly published index-methodology white papers (Cboe). No proprietary, course, or trading-academy material is cited.*
