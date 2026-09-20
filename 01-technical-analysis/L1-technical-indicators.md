---
title: "The Indicators, from the Formula Up"
last_updated: 2026-09-20
---

# The Indicators, from the Formula Up

## Abstract

Most traders meet technical indicators as coloured lines with rules attached and never see the arithmetic underneath. This paper does the opposite: it derives the standard indicators from their formulas, so that each one stops being a black box and becomes a transparent transform of price. We work through the two families a chartist actually uses — *smoothers* (simple, weighted, and exponential moving averages, and the MACD built from them) and *oscillators* (RSI, the stochastic, Bollinger Bands, ATR, and the ADX/DMI system) — writing out each definition, the single thing it measures, and the specific way it misleads. The unifying result is deflationary and important: every one of these indicators is a deterministic function of the same price and volume series, so none of them adds information that is not already in the chart; they only *reshape* it to make one feature — trend, momentum, volatility, or dispersion — easier to read. Understanding the formula is what lets a trader see when an indicator is saying something real and when it is merely re-describing the price with a lag.

## Keywords

Moving average, EMA, MACD, RSI, stochastic oscillator, Bollinger Bands, ATR, ADX, directional movement, lag, smoothing, volatility, indicator overfitting

## 1 Introduction

### 1.1 Motivation and thesis

An indicator is a promise: "compute this number from recent prices, and it will tell you something the raw chart hid." Sometimes the promise is kept — a volatility measure genuinely summarises dispersion you would struggle to eyeball — and sometimes it is empty, a lagged copy of price dressed up as a signal. The only way to tell which is which is to know the formula. The thesis of this paper is that every popular indicator is a *deterministic transform* of the price (and sometimes volume) series, so it can add no information that was not already present; its value is entirely in whether that transform makes a genuine feature — trend, momentum, volatility — easier and more honest to read.

### 1.2 Scope, prerequisites, and intended reader

You need to know what a price series is and be comfortable with an average, a percentage, and a standard deviation; nothing else. Every symbol is defined where it first appears. This paper is a *reference*: it states each indicator precisely enough that you could implement it yourself and know exactly what your charting package is drawing. It is the companion to the conceptual technical-analysis paper, which argues *whether* rules built on these indicators survive testing; here we only build the instruments, honestly labelled.

### 1.3 Notation and reproducibility

Let $P_t$ be the closing price on day $t$, and where an indicator needs them, $H_t$, $L_t$ the day's high and low. All definitions below are the standard public forms; where a smoothing convention has a common variant (notably Wilder's smoothing versus a textbook exponential average), it is named. Every indicator here is a few lines of arithmetic and can be reproduced from free daily data with no special library. *This is a research and educational document, not investment advice.*

### 1.4 Organization of this paper

Section 2 draws the map: two families, smoothers and oscillators, and what separates them. Section 3 builds the moving averages (simple, weighted, exponential) and the lag they all pay. Section 4 assembles the MACD from two of them. Sections 5 and 6 build the momentum oscillators RSI and the stochastic. Section 7 builds Bollinger Bands from a moving average and a standard deviation. Section 8 builds ATR as a volatility measure, and Section 9 the ADX/DMI trend-strength system. Section 10 states the deflationary result — no indicator adds information — and its consequences for overfitting. Section 11 collects misconceptions, Section 12 is a glossary, and the references close the paper.

## 2 Two families of indicator

Almost every indicator on a standard platform belongs to one of two families, and knowing which tells you in advance what it can and cannot do. *Smoothers* average price over a window to expose the slow component — the trend — at the cost of *lag*: because they look backward, they turn after the price does. Moving averages and the MACD are smoothers. *Oscillators* normalise recent price action onto a bounded or centred scale to expose a fast component — momentum, or distance from a local mean — and are prone to the opposite error: they flag "overbought" or "oversold" states that persist for a long time in a trend. RSI, the stochastic, and the %B reading of Bollinger Bands are oscillators. A third, smaller group measures *dispersion* rather than direction — ATR and the band width — and a fourth measures *trend strength without direction* — the ADX. The families are not decoration; a smoother used as a timing trigger and an oscillator used to fight a trend fail for reasons written into their formulas.

## 3 Moving averages and the price of smoothing

A *simple moving average* (SMA) of length $n$ is the plain mean of the last $n$ closes:

$$\mathrm{SMA}_n(t) = \frac{1}{n}\sum_{i=0}^{n-1} P_{t-i}.$$

It smooths the series but reacts slowly and weights a price from $n-1$ days ago exactly as heavily as today's. A *weighted moving average* (WMA) fixes the second complaint by giving linearly larger weight to recent prices, and an *exponential moving average* (EMA) fixes it recursively and cheaply:

$$\mathrm{EMA}_t = \alpha\,P_t + (1-\alpha)\,\mathrm{EMA}_{t-1}, \qquad \alpha = \frac{2}{n+1}.$$

Here $\alpha$ is the *smoothing factor*: a larger $\alpha$ (shorter $n$) tracks price closely and stays jumpy; a smaller $\alpha$ (longer $n$) is smoother and slower. One smoothing convention is worth naming because several later indicators use it: *Wilder's smoothing* is an EMA with $\alpha = 1/n$ rather than $2/(n+1)$, which is why a "14-period" Wilder average is slower than a "14-period" textbook EMA. Every moving average shares one unavoidable property — *lag*. Because it is an average of past prices, it necessarily turns after the price turns, and the smoother you make it, the later it turns. That lag is not a bug to be tuned away; it is the price you pay for suppressing noise, and it is why moving-average crossovers whipsaw in ranges and shine only when a trend runs far enough to outpay the late entry and late exit.

## 4 MACD: two moving averages in a trench coat

The *moving average convergence/divergence* is not a new idea but a packaging of Section 3. It is the difference of two EMAs, conventionally 12- and 26-period, with a third EMA of that difference as a *signal line*:

$$\mathrm{MACD}_t = \mathrm{EMA}_{12}(P)_t - \mathrm{EMA}_{26}(P)_t, \qquad \mathrm{signal}_t = \mathrm{EMA}_{9}(\mathrm{MACD})_t,$$

and the *histogram* is $\mathrm{MACD}_t - \mathrm{signal}_t$. Because $\mathrm{EMA}_{12}$ reacts faster than $\mathrm{EMA}_{26}$, their difference is positive when the fast average is above the slow one — a short-term uptrend relative to a longer one — and its sign changes are just crossovers of the two underlying averages, seen through one number. The histogram, being the gap between the MACD and its own smoother, is essentially a measure of how fast the trend relationship is *accelerating*. Knowing this deflates most MACD folklore: a "bullish MACD cross" is exactly a fast-EMA-over-slow-EMA cross, carries the same lag as any moving-average system, and adds no information beyond the two averages it is built from.

## 5 RSI: bounded momentum

The *Relative Strength Index* maps recent up-moves against recent down-moves onto a 0–100 scale. Over a window (Wilder's original is $n = 14$), let the average gain be the Wilder-smoothed mean of the up-closes and the average loss the Wilder-smoothed mean of the down-closes (as a positive number). Then

$$\mathrm{RS} = \frac{\text{average gain}}{\text{average loss}}, \qquad \mathrm{RSI} = 100 - \frac{100}{1 + \mathrm{RS}}.$$

When gains dominate, $\mathrm{RS}$ is large and RSI approaches 100; when losses dominate, RSI approaches 0; when they balance, RSI sits at 50. The conventional 70/30 thresholds label "overbought" and "oversold" states. The formula makes the standard warning precise: RSI is a bounded transform of the *ratio* of recent gains to losses, so in a persistent trend the ratio stays lopsided and RSI can pin near an extreme for weeks while price keeps going. Reading a single RSI reading as a reversal signal is therefore reading a momentum measure as if it were a mean-reversion one — safe only after you have separately established a mean-reverting regime.

## 6 The stochastic oscillator: position within the range

Where RSI works from gains and losses, the *stochastic oscillator* works from *where price sits inside its recent range*. Over a look-back of $n$ periods,

$$\%K_t = 100 \cdot \frac{P_t - \min_{i<n} L_{t-i}}{\max_{i<n} H_{t-i} - \min_{i<n} L_{t-i}}, \qquad \%D_t = \mathrm{SMA}_3(\%K)_t.$$

$\%K$ is 100 when the close is at the top of its $n$-period range and 0 when it is at the bottom; $\%D$ is a 3-period smoothing of $\%K$ used as a signal line. The intuition is that closes near the top of the range signal strength and near the bottom signal weakness, and that turns in $\%K$ relative to $\%D$ hint at momentum shifts. The same caveat as RSI applies and for the same structural reason: in a strong trend the close sits near the top (or bottom) of its range day after day, so the stochastic saturates and its "overbought" reading is not a warning but a description of a healthy trend.

## 7 Bollinger Bands: a moving average with a volatility envelope

*Bollinger Bands* wrap a moving average in a band whose width scales with recent volatility. With a 20-period SMA and the sample standard deviation $\sigma_{20}$ of the last 20 closes,

$$\text{middle} = \mathrm{SMA}_{20}(t), \qquad \text{upper/lower} = \mathrm{SMA}_{20}(t) \pm k\,\sigma_{20}(t),$$

with $k = 2$ conventionally. Because the band is $\pm k$ standard deviations, it automatically widens when the market is volatile and narrows when it is calm — the much-discussed "squeeze" is simply $\sigma_{20}$ falling. The bands answer a precise question: how far is price from its recent mean, measured in units of its own recent volatility? A close outside a band means an unusually large move *relative to recent dispersion*, nothing more — it is a statement about volatility-scaled distance, not a reversal signal, and in a trend price can "walk the band" for a long time.

## 8 ATR: measuring how much it moves

The *Average True Range* strips out direction entirely and measures only how much an instrument moves per day, correctly accounting for gaps. The *true range* on day $t$ is the largest of the day's own range and the two gap-adjusted ranges to the prior close:

$$\mathrm{TR}_t = \max\big(H_t - L_t,\; |H_t - P_{t-1}|,\; |L_t - P_{t-1}|\big),$$

and the ATR is a Wilder-smoothed average of $\mathrm{TR}$, conventionally over 14 periods. ATR is a volatility measure in price units, and its honesty is exactly that it says nothing about direction. Its genuine uses are practical rather than predictive: sizing a position so that a fixed dollar risk corresponds to a fixed multiple of ATR, or setting a stop a volatility-scaled distance away so that the same stop is wide in turbulent markets and tight in calm ones — the same volatility-normalisation logic that runs through the risk and volatility papers.

## 9 ADX and DMI: trend strength without direction

The *Directional Movement* system separates the question "is there a trend?" from "which way?". From the day-to-day changes in the high and low it forms *directional movement* up and down, smooths each (Wilder) and divides by ATR to get the positive and negative *directional indicators* $+\mathrm{DI}$ and $-\mathrm{DI}$. Their normalised gap is the *directional index*,

$$\mathrm{DX} = 100 \cdot \frac{|+\mathrm{DI} - {-\mathrm{DI}}|}{+\mathrm{DI} + {-\mathrm{DI}}},$$

and the *ADX* is a Wilder-smoothed average of DX. The two DI lines carry direction — $+\mathrm{DI}$ above $-\mathrm{DI}$ means up-moves dominate — while the ADX carries only *strength*: a high ADX means a strong trend of either sign, a low ADX means a range. This separation is the whole point and the one genuinely distinct idea in the indicator zoo: ADX is the tool that answers the prior question the moving-average and oscillator families both quietly assume — whether the market is trending at all, which decides which family should be trusted right now.

## 10 The deflationary result: no indicator adds information

Step back and the common structure is unmistakable. Every indicator above is a fixed, deterministic function of $P_t$ (and for a few, $H_t$, $L_t$, and volume). A function of the data cannot contain information the data did not — it can only *reshape* what is already there to make one feature legible. That is the honest description of what an indicator does and the boundary of what it can do: a moving average makes trend legible and lags; an oscillator makes short-horizon distance-from-mean legible and saturates in trends; ATR makes volatility legible and is silent on direction; ADX makes trend *strength* legible. None of them is a source of new predictive content, and stacking five of them does not create any — it mostly creates *overfitting*, because each indicator adds parameters (lengths, thresholds) to tune until the past looks explained. The discipline the rest of this library insists on therefore applies with full force: an indicator-based rule is worth exactly as much as it proves out-of-sample, after costs, deflated for the number of indicator-and-parameter combinations you tried — and no more.

## 11 Common misconceptions

- **"More indicators mean more information."** All indicators are transforms of the same price and volume; adding them adds parameters to overfit, not information (Section 10).
- **"The MACD cross is its own signal."** A MACD sign change is exactly a fast-EMA-over-slow-EMA crossover, with the same lag as any moving average (Section 4).
- **"RSI over 70 means reverse."** RSI is bounded momentum; in a trend it pins near an extreme for weeks (Section 5).
- **"A close outside the Bollinger Band is a reversal."** It is an unusually large move relative to recent volatility; in a trend, price walks the band (Section 7).
- **"ATR tells me where price is going."** ATR measures how much, never which way; its uses are sizing and stops (Section 8).
- **"A high ADX means go long."** ADX measures trend *strength* of either sign; direction lives in the $+\mathrm{DI}/-\mathrm{DI}$ lines (Section 9).

## 12 Glossary

- **ADX (Average Directional Index)** — a smoothed measure of trend strength, direction-agnostic.
- **ATR (Average True Range)** — a smoothed average of the true range; a volatility measure in price units.
- **Bollinger Bands** — a moving average with an envelope at $\pm k$ standard deviations of recent price.
- **DI ($+\mathrm{DI}$, $-\mathrm{DI}$)** — directional indicators measuring the dominance of up- versus down-moves.
- **EMA (exponential moving average)** — a recursive weighted average with smoothing factor $\alpha = 2/(n+1)$.
- **Lag** — the delay with which any backward-looking average turns after price turns.
- **MACD** — the difference of a fast and a slow EMA, with a signal-line EMA of that difference.
- **RSI (Relative Strength Index)** — a 0–100 transform of the ratio of recent average gain to average loss.
- **SMA (simple moving average)** — the unweighted mean of the last $n$ prices.
- **Stochastic oscillator** — $\%K$, the close's position within its recent high–low range, and $\%D$, its smoothing.
- **Wilder's smoothing** — an exponential average with $\alpha = 1/n$, used in RSI, ATR, and ADX.

## References

- Wilder, J. W. (1978). *New Concepts in Technical Trading Systems.* Greensboro, NC: Trend Research. (The original definitions of RSI, ATR, and the directional-movement/ADX system.)
- Bollinger, J. (2001). *Bollinger on Bollinger Bands.* New York: McGraw-Hill. (The volatility-band construction and its intended reading.)
- Murphy, J. J. (1999). *Technical Analysis of the Financial Markets.* New York: New York Institute of Finance. (A standard, widely held reference for the definitions of the common indicators.)
- Park, C.-H., & Irwin, S. H. (2007). What do we know about the profitability of technical analysis? *Journal of Economic Surveys, 21*(4), 786–826. (Survey evidence on indicator-based rules.)

*All references above are publicly accessible: widely held published books and a peer-reviewed survey article. No proprietary, course, or trading-academy material is cited or used anywhere in this paper; every formula is a standard public definition.*

## Evidence basis

| Claim | Basis |
|---|---|
| Each indicator is a deterministic transform of price/volume and adds no new information | Own reasoning from the stated formulas; reproducible from free daily data |
| The MACD sign change is identical to a fast/slow EMA crossover | Own derivation from the definition (Section 4) |
| RSI and the stochastic saturate in trends because they are bounded transforms of recent momentum | Own derivation (Sections 5–6) |
| Bollinger Bands widen/narrow with recent volatility because width is $\pm k\,\sigma$ | Own derivation (Section 7) |
| RSI, ATR, and ADX use Wilder's $\alpha = 1/n$ smoothing | Literature — (Wilder 1978) |
| Indicator-based rules must be judged out-of-sample, after costs, deflated for parameter search | Practitioner consensus; method in the backtesting and overfitting-control papers |
