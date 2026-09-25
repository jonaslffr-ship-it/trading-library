---
title: "Technical Analysis, Honestly"
last_updated: 2026-09-20
---

# Technical Analysis, Honestly

## Abstract

Technical analysis is the study of price and volume history to inform trading decisions. This paper builds the subject from zero, but with the same discipline the rest of this library applies to any claim: every rule is treated as a *hypothesis to be tested*, not a truth to be memorised. We define the core objects a chartist works with — trend, support and resistance, moving averages, momentum oscillators, chart patterns, and volume — and explain the mechanism each is supposed to capture. We then confront each with the two questions that decide whether it is worth anything: does it beat a fair benchmark *after* realistic costs, and does the apparent edge survive the fact that thousands of people have mined the same data? The published evidence is mixed and honest about it: simple trend and momentum rules have real, decades-long academic support, but most pattern-and-oscillator folklore does not survive transaction costs and data-snooping corrections. The practical payload is a repeatable method — a pre-registered, cost-aware, single-rule test the reader can run on free data — so that "the chart says buy" becomes a falsifiable statement rather than an act of faith.

## Keywords

Technical analysis, trend following, moving average, momentum, mean reversion, support and resistance, chart patterns, volume, data snooping, transaction costs, base rate, pre-registration

## 1 Introduction

### 1.1 Motivation and thesis

Ask two traders about a moving-average crossover and you will often get a religious argument rather than a factual one. One treats it as obviously useful because "it worked on this chart"; the other dismisses it as astrology. Both are reasoning from anecdote. The thesis of this paper is that neither faith nor contempt is warranted a priori: a technical rule is a *conditional bet* — "given this pattern, the next move is more likely to be up than a fair benchmark implies" — and that is a statement you can test. The entire value of technical analysis, if it has any, lives in rules that clear two hurdles: they must beat a fair benchmark *after costs*, and the edge must survive the knowledge that the same price history has been searched by millions of people looking for exactly such rules.

### 1.2 Scope, prerequisites, and intended reader

This paper assumes only that you know what a price chart is and what "the market closed up 1%" means. Every technical term is defined at first use, and the mathematics never exceeds an average and a percentage. It is written for a reader who wants to understand what technical analysis actually claims, which of those claims the evidence supports, and how to check the rest without deceiving themselves. It deliberately does *not* teach a catalogue of patterns to trade on sight; the companion papers on *statistics for traders* and *backtesting methodology* supply the machinery that turns any charting idea into a checkable one, and this paper leans on that machinery rather than repeating it.

### 1.3 Evidence and honesty

Nothing here is called *validated* on the strength of a nice-looking chart. Where an empirical claim is made, it is anchored either to a cited, publicly accessible study or to a test the reader can run themselves from free data (Section 9). The distinction the whole paper turns on is between a rule's *in-sample* appearance — how it looks on the history you already saw — and its *out-of-sample* behaviour on data it was never fitted to; only the latter is evidence. *This is a research and educational document, not investment advice.*

### 1.4 Organization of this paper

Section 2 states precisely what technical analysis claims and the two questions that decide any rule. Section 3 treats trend and the moving average — the one idea with the strongest independent support. Section 4 covers support, resistance, and the special role of round numbers. Section 5 separates momentum from mean reversion and reads oscillators honestly. Section 6 is about chart patterns and the human tendency to see faces in clouds. Section 7 asks what, if anything, volume adds. Section 8 is the reckoning: what the published evidence says survives costs and data-snooping. Section 9 hands the reader a pre-registered single-rule test template. Section 10 collects the common misconceptions, Section 11 is a glossary, and the references close the paper.

## 2 What technical analysis actually claims

Strip away the vocabulary and technical analysis rests on three claims. First, that prices are not a pure random walk — that past prices carry *some* information about future prices, which is a claim about weak-form market efficiency (Fama 1970). Second, that this information shows up in recurring, recognisable configurations of price and volume. Third, that a disciplined observer can act on those configurations profitably after costs. The first claim is partly true and well documented; the second is where most of the folklore lives; the third is where most of the money is lost.

Two questions decide the fate of any specific rule, and they are the spine of this paper. **The benchmark question:** does the rule beat a fair, cost-matched alternative — usually buy-and-hold at the same average exposure — rather than merely making money because the market went up? A rule that is long 60% of the time in a market that rose is not skilful; it is a leveraged coin that landed heads. **The snooping question:** since thousands of analysts have searched the same charts, the *best-looking* rule among many is expected to look good by chance alone (Sullivan, Timmermann & White 1999). An honest evaluation therefore counts how many variants were tried and deflates the result accordingly — exactly the multiple-testing problem the quant-methods track formalises.

## 3 Trend and the moving average

A *moving average* replaces each day's price with the average of the last *n* prices, smoothing the jagged series into a slow line. It is the workhorse of trend identification: price above a rising average is read as an uptrend, price below a falling one as a downtrend, and a *crossover* — price or a fast average cutting through a slow one — as a change of regime. The mechanism it is meant to capture is real and has a name outside charting: *momentum*, the empirical tendency of recent relative performance to persist over horizons of months (Jegadeesh & Titman 1993; Moskowitz, Ooi & Pedersen 2012).

This is the part of technical analysis with the strongest independent support. Simple trend rules on major indices showed statistically detectable predictive content in careful academic tests (Brock, Lakonishok & LeBaron 1992), and time-series momentum — buy what has risen over the past year, sell what has fallen — has positive average returns across dozens of markets and a century of data (Moskowitz, Ooi & Pedersen 2012). The honest caveats are equally important, and two later studies qualified the 1992 result in *different* ways that are worth keeping separate. Bessembinder & Chan (1998) showed its paper profits shrank once realistic transaction costs were charged; and Sullivan, Timmermann & White (1999) ran the best of a large rule universe through White's Reality Check and found that the best rule *survived* the data-snooping correction in the full in-sample period (roughly 1897–1986) but no longer beat the benchmark out-of-sample over 1987–1996. So the honest verdict is not "the data-snooping correction killed it" but "costs eat it, and its edge does not persist out-of-sample." A moving average also has *no* forecasting power in a range-bound market — it whipsaws, buying every false break and selling every false dip. Trend rules pay a steady stream of small losses in calm markets in exchange for capturing the rare large move, which is the same convexity trade-off the tail-hedging paper describes, drawn on the underlying instead of on options.

## 4 Support, resistance, and round numbers

*Support* is a price level below the market where buying has repeatedly appeared; *resistance* is a level above where selling has repeatedly appeared. The idea is that these levels act as memory: participants who transacted there create standing orders and behavioural anchors, so the level tends to halt or reverse moves until it eventually gives way. The most defensible version of the claim is the mildest one — that *round numbers* (a stock at 100, an index at 5,000) attract disproportionate order flow and show small but detectable clustering and barrier effects, a regularity documented in currency and equity microstructure (Osler 2003). The strong version — that a hand-drawn line connecting two past highs predicts the next reversal — is far weaker, because with enough past pivots a line can be drawn to "explain" almost any level, which is a fitting exercise, not a forecast.

The practical reading is a matter of order of magnitude. Treat well-defined levels — prior highs and lows, round numbers, the prior session's range — as places where liquidity and attention cluster, and therefore where moves are more likely to pause or accelerate on a break. Do not treat them as precise price magnets, and never draw the line *after* the reversal and call it a prediction.

## 5 Momentum and mean reversion: reading oscillators honestly

Two opposite behaviours coexist in markets at different horizons, and most oscillator confusion comes from mixing them up. Over months, relative returns *persist* — this is momentum, Section 3. Over days to a couple of weeks, index returns show mild *mean reversion*: an unusually large move is somewhat more likely to be partly retraced than extended, a short-horizon reversal effect visible in the negative first-order autocorrelation of index returns (the short-horizon reversal literature is Jegadeesh 1990 and Lehmann 1990, on single stocks; the index sign here is our own measurement, *not* the intermediate-horizon momentum of Jegadeesh & Titman 1993). A *momentum oscillator* such as the Relative Strength Index or the stochastic is simply a bounded transform of recent returns designed to flag "overbought" and "oversold" states — that is, states from which short-horizon mean reversion is hypothesised.

Read this way, an oscillator is a mean-reversion signal wearing a horizon it rarely states out loud, and that omission is where traders get hurt. The same "overbought" reading that precedes a healthy pullback in a range precedes *nothing* in a strong trend, where the market stays "overbought" for weeks while it climbs — the reason the folklore "sell when RSI exceeds 70" bleeds money in exactly the trends a trend-follower is harvesting. The honest use of an oscillator is therefore conditional: as a mean-reversion timing aid only after you have separately established that you are in a mean-reverting regime, never as a standalone reason to fight a trend.

## 6 Chart patterns and pareidolia

Head-and-shoulders, triangles, flags, double tops — the pattern zoo is the most recognisable and least reliable part of technical analysis. The difficulty is not that patterns never carry information; a rigorous, algorithmic definition of several classic patterns did find modest, statistically detectable predictive content in U.S. stocks (Lo, Mamaysky & Wang 2000). The difficulty is *pareidolia*: the human visual system is superb at finding faces in clouds and heads-and-shoulders in noise, and a pattern identified by eye, after the fact, on a hand-picked chart is evidence of nothing. The gap between the 2000 study's result and the folklore is entirely the difference between a pattern defined precisely enough for a computer to find it the same way every time, and a pattern a person recognises when it suits their existing view.

The rule that follows is simple and unforgiving: a pattern is worth something only if you can define it precisely enough to detect it *mechanically*, count how often it appeared, and measure what happened next against a fair benchmark — before you ever traded it. If you cannot state the pattern as an algorithm, you are not testing the market; you are testing your own hindsight.

## 7 Volume and confirmation

Volume — the number of shares or contracts traded — is the one input beyond price that classical technical analysis leans on, usually as *confirmation*: a breakout "on high volume" is treated as more trustworthy than one on thin volume, because it implies broad participation rather than a few orders pushing an illiquid tape. There is a real microstructure kernel here: volume is correlated with volatility and with the arrival of information, and moves on very thin volume are more easily reversed. But volume as a directional signal is far weaker than the folklore suggests, and the "confirmation" heuristic is hard to falsify precisely because it is vague — high relative to what window, and by how much?

Volume earns its keep less as a standalone signal and more as a *context* variable: it tells you how much conviction and liquidity sat behind a move, which matters for whether a level will hold and for your own execution, rather than for the move's direction. The genuinely informative volume events — the opening and closing auctions, and expiry-driven concentration — are treated in the market-mechanics and dealer-flow papers, where volume is tied to a specific mechanism rather than to a rule of thumb.

## 8 The reckoning: what survives testing

Pulling the evidence together, three findings are robust across the published literature. First, *trend and momentum are real*: simple trend rules had detectable predictive content (Brock, Lakonishok & LeBaron 1992) and time-series momentum is one of the most replicated anomalies in finance (Moskowitz, Ooi & Pedersen 2012). Second, *most of the rest does not survive scrutiny*: once you correct for the enormous number of rules that have been tried on the same data, the average technical trading rule's apparent profitability largely evaporates, and the broad survey literature reaches a guarded verdict rather than an endorsement (Sullivan, Timmermann & White 1999; Park & Irwin 2007). Third, *costs are decisive*: rules that trade often can look profitable on paper and lose money in practice, because each round trip pays a spread and a commission that the paper test omitted.

The lesson is not "technical analysis is worthless" and it is not "the chart is a crystal ball." It is that the field contains a small number of robust, tradable regularities buried in a large amount of untested folklore, and the only way to tell them apart is the discipline the rest of this library is built on: a fair benchmark, honest costs, an out-of-sample split, and a correction for how many rules you tried. A chartist who applies that discipline is doing empirical research; one who does not is reading tea leaves with a ruler.

## 9 A pre-registered single-rule test you can run

The antidote to self-deception is to fix the rules of the test *before* you see the result. What follows is a template, not a strategy; it turns "does this work?" into a falsifiable experiment on free daily data (for example, Yahoo Finance index closes).

- **Pre-register (write down first, then do not change).** State the exact rule as an algorithm — e.g. "long when the 50-day average is above the 200-day average, flat otherwise" — the instrument, the sample period, the benchmark (buy-and-hold at the rule's average exposure), the cost per switch (a realistic spread plus commission), and the single number you will judge it by (e.g. net Sharpe ratio). Fix an *out-of-sample* period you will not look at until the end.
- **Compute honestly.** Run the rule in-sample, subtract costs on every position change, and compare to the benchmark. Then — only once — run the frozen rule on the untouched out-of-sample period. The out-of-sample result is the evidence; the in-sample result was always going to look good.
- **Deflate for search.** If you tried several averages, lengths, or thresholds before settling, you did not test one rule, you tested many, and the best of them is expected to look good by chance. Count the variants and apply the deflation the overfitting-control paper describes, or your "edge" is a data-snooping artefact.
- **Kill criterion.** State in advance the result that would make you abandon the rule (for example, an out-of-sample net Sharpe below the benchmark's), and honour it.

Run this once, on any rule you care about, and you will learn more about technical analysis than a shelf of pattern books can teach — because you will have measured, on data that could have said no, whether the rule carries information you can keep after costs.

## 10 Common misconceptions

- **"It worked on this chart, so it works."** A single chart is one draw from the machine; a rule that fits the history you already saw tells you nothing until it is tested on history it never saw (Section 1.3, Section 9).
- **"Support and resistance are precise price magnets."** The defensible effect is mild clustering around salient levels, especially round numbers; a line drawn through two past pivots is a fit, not a forecast (Section 4).
- **"RSI over 70 means sell."** An oscillator is a mean-reversion signal; in a strong trend the market stays "overbought" for weeks, and fighting it there loses money (Section 5).
- **"This head-and-shoulders predicts a drop."** A pattern spotted by eye after the fact is pareidolia; only a mechanically defined pattern, counted and benchmarked, is evidence (Section 6).
- **"High volume confirms the breakout."** Volume is context — conviction and liquidity — more than direction, and "confirmation" is too vague to falsify as stated (Section 7).
- **"Technical analysis is either magic or nonsense."** Neither; it is a mix of a few robust regularities (trend, momentum) and a lot of untested folklore, separable only by testing (Section 8).

## 11 Glossary

- **Breakout** — a move of price beyond a prior level (a high, a range edge, a round number), often watched as a possible start of a new trend.
- **Crossover** — the moment a faster average or price cuts through a slower average, used as a trend-change signal.
- **Data snooping** — the distortion that arises when many rules are tried on the same data and the best is reported as if it were the only one tested.
- **Mean reversion** — the tendency, over short horizons, for an unusually large move to be partly retraced rather than extended.
- **Momentum** — the tendency, over horizons of months, for recent relative performance to persist.
- **Moving average** — the average of the last *n* prices, recomputed each day, used to smooth the series and identify trend.
- **Oscillator** — a bounded transform of recent returns (e.g. RSI, stochastic) flagging "overbought"/"oversold" states.
- **Out-of-sample** — data a rule was not fitted to; the only fair place to judge it.
- **Pareidolia** — the human tendency to perceive meaningful patterns (faces, shapes) in random data.
- **Support / resistance** — price levels below/above the market where buying/selling has repeatedly appeared.
- **Trend** — a persistent directional drift in price over time.
- **Volume** — the quantity of shares or contracts traded in a period; a proxy for participation and liquidity.

## References

- Bessembinder, H., & Chan, K. (1998). Market efficiency and the returns to technical analysis. *Financial Management, 27*(2), 5–17. The source of the transaction-cost caveat to Brock, Lakonishok & LeBaron (1992).
- Brock, W., Lakonishok, J., & LeBaron, B. (1992). Simple technical trading rules and the stochastic properties of stock returns. *Journal of Finance, 47*(5), 1731–1764.
- Fama, E. F. (1970). Efficient capital markets: A review of theory and empirical work. *Journal of Finance, 25*(2), 383–417.
- Jegadeesh, N. (1990). Evidence of predictable behavior of security returns. *Journal of Finance, 45*(3), 881–898. The short-horizon (monthly/weekly) reversal result — distinct from the intermediate-horizon momentum of Jegadeesh & Titman (1993).
- Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers: Implications for stock market efficiency. *Journal of Finance, 48*(1), 65–91. The intermediate-horizon (3–12 month) *momentum* result, on individual stocks.
- Lehmann, B. N. (1990). Fads, martingales, and market efficiency. *Quarterly Journal of Economics, 105*(1), 1–28. Weekly return reversals.
- Lo, A. W., Mamaysky, H., & Wang, J. (2000). Foundations of technical analysis: Computational algorithms, statistical inference, and empirical implementation. *Journal of Finance, 55*(4), 1705–1765.
- Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). Time series momentum. *Journal of Financial Economics, 104*(2), 228–250. Open access: <https://pages.stern.nyu.edu/~lpederse/papers/TimeSeriesMomentum.pdf>.
- Osler, C. L. (2003). Currency orders and exchange rate dynamics: An explanation for the predictive success of technical analysis. *Journal of Finance, 58*(5), 1791–1820.
- Park, C.-H., & Irwin, S. H. (2007). What do we know about the profitability of technical analysis? *Journal of Economic Surveys, 21*(4), 786–826.
- Sullivan, R., Timmermann, A., & White, H. (1999). Data-snooping, technical trading rule performance, and the bootstrap. *Journal of Finance, 54*(5), 1647–1691.

*All references above are publicly accessible: peer-reviewed journal articles (with an open-access link given where a public author copy exists). No proprietary, course, or trading-academy material is cited or used anywhere in this paper.*

## Evidence basis

| Claim | Basis |
|---|---|
| Simple trend rules on major indices show detectable predictive content | Literature — (Brock, Lakonishok & LeBaron 1992) |
| Time-series momentum has positive average returns across markets and a century of data | Literature — (Moskowitz, Ooi & Pedersen 2012) |
| Short-horizon index returns mean-revert (negative first-order autocorrelation) | Own measurement, reproducible from free daily data; short-horizon reversal in the literature is Jegadeesh (1990) and Lehmann (1990) — *not* Jegadeesh & Titman (1993), which is the intermediate-horizon momentum result |
| Algorithmically defined chart patterns carry modest predictive content; eyeballed ones do not | Literature — (Lo, Mamaysky & Wang 2000) |
| Round numbers attract order-flow clustering and mild barrier effects | Literature — (Osler 2003) |
| Across a large rule universe the best rule's edge does not persist out-of-sample and is eaten by costs (its data-snooping-corrected *in-sample* edge did survive) | Literature — (Sullivan, Timmermann & White 1999; Bessembinder & Chan 1998; Park & Irwin 2007) |
| The only fair test of a rule is out-of-sample, cost-adjusted, and deflated for the number of variants tried | Practitioner consensus; method detailed in the backtesting and overfitting-control papers |
