---
title: "Backtesting & Hypothesis Testing"
last_updated: 2026-09-25
---

# Backtesting & Hypothesis Testing

## Abstract

A backtest cannot *discover* a trading edge; it can only *fail to reject* one that was specified in advance. This paper sets out the discipline that makes that specification binding — pre-registration of the hypothesis, metric, in-sample/out-of-sample split, and decision rule before any data is examined — and shows, with a simulation, why every choice made after seeing the data is a *researcher degree of freedom* that inflates false discovery. We treat in turn: the anatomy of a backtest and the transaction costs that quietly dominate most apparent edges; data splits and the operational meaning of opening the out-of-sample set exactly once; evaluation by expectancy and the trade distribution rather than the equity curve; the decomposition of an existing track record into skill, factor exposure, and luck; a catalogue of classic failure modes, each with a reconstructed example; regime-conditioning without look-ahead; and reproducibility as a workflow. A single hypothesis — that a low VIX gates a short-side edge in equity-index futures — is carried through the full protocol as a worked case study, including an explicit account of how the real analysis behind it violated these rules. Every numerical example uses freely available data and is reproducible from the accompanying code.

## Keywords

Backtesting, pre-registration, out-of-sample testing, hypothesis testing, effect size, multiple testing, data snooping, backtest overfitting, profit factor, expectancy, R-multiples, walk-forward analysis, look-ahead bias, reproducibility

## 1 Introduction

### 1.1 Motivation and thesis

A backtest is not a discovery engine. It is a *disagreement-resolution device*: it can settle a dispute between two clearly stated views of the world, and it can do nothing else honestly. If you have not stated, before running it, what result would prove you wrong, then whatever the backtest prints will confirm what you already believed — because you will read the ambiguity in your favor. This is not a moral failing; it is the default behavior of a motivated human looking at a noisy chart.

The thesis of this paper follows directly: *most of the work is done before the first line of profit-and-loss is computed, and the most valuable output of a good backtest is often a clean "no."* The sections that follow are, in effect, a single argument made from many angles — that the credibility of a quantitative result is determined by the decisions taken *before* the data can answer, and that a small number of disciplines (pre-registration, an honest out-of-sample split, costs taken seriously, and reproducibility) separate research from expensive self-deception.

### 1.2 Scope, prerequisites, and intended reader

This paper sits in the Trading Library's *Quant Methods* track. It assumes the statistics-for-traders paper: distributions and base rates, expectancy versus hit rate, standard errors, and a working Python setup that can pull a price series and compute returns from free data. It assumes comfort with a simple formula and a short code snippet; it assumes no measure theory and no stochastic calculus.

After reading this paper, a reader can:

- turn a vague market intuition into a one-sentence confirmatory hypothesis with an explicit null, a directional alternative, a pre-committed effect size, and a decision rule — written and frozen before any test;
- build a backtest whose profit-and-loss accounting they trust, and run a cost-sensitivity table that shows the honest range in which an edge lives or dies;
- split data so the out-of-sample result *means something*, and explain operationally what *"the out-of-sample set is opened once"* requires of them;
- judge a strategy by expectancy and the trade distribution, not by a smooth equity curve or a headline win rate;
- take a track record apart — decompose its Sharpe ratio, regress it against obvious factors, and read the return-based red flags of an overfit or mislabeled result;
- recognize each entry of the classic failure catalogue — look-ahead, survivorship, data snooping, regime drift, silent repainting — in the wild;
- and run the direction check reflexively, verifying that the *sign* of the data matches the hypothesis before letting any evidence in.

### 1.3 Data and reproducibility

All numerical examples and figures use freely available data (yfinance for prices, FRED and CBOE for the volatility complex, optionsDX for end-of-day options) and are reproducible from the accompanying code at the commit hash cited beside each result. Where an example draws on a private trade list, that list is not redistributed and the fact is stated explicitly. *This is a research and educational document, not investment advice.*

### 1.4 Organization of this paper

Sections 2 and 3 are complete. The remaining sections (Sections 4–11) are drafted in sequence and are listed here with their scope so the whole arc is visible; sections still to be written are marked *(forthcoming)* and are never presented as finished.

- **Section 3 Anatomy of a backtest** — signal → position → P&L; vectorized versus event-driven; the cost-sensitivity curve.
- **Section 4 Data splits that mean something** — train / validation / out-of-sample; walk-forward; embargo periods; what *"opened once"* means operationally. *(forthcoming)*
- **Section 5 Metrics beyond the equity curve** — Sharpe/Sortino, profit factor, drawdown; hit rate versus payoff versus expectancy (R-multiples); the trade distribution. *(forthcoming)*
- **Section 6 Analyzing an existing strategy or track record** — Sharpe decomposition; factor regression; return-based red flags; live-versus-backtest reconciliation. *(forthcoming)*
- **Section 7 The classic failure catalogue** — look-ahead, survivorship, data snooping, regime drift, silent repainting — each with a reconstructed example. *(forthcoming)*
- **Section 8 Regime-conditioning without cheating** — splitting by regime as diagnosis; pre-registered gates versus post-hoc discovery. *(forthcoming)*
- **Section 9 Reproducibility** — seeds, environment pinning, commit hashes, append-only result logs. *(forthcoming)*
- **Section 10 Worked case study** — *"a low VIX gates a short-side edge"* run through the full protocol, from pre-registration to verdict, confronting the real study's rule-breaks. *(forthcoming)*
- **Section 11 Discussion, common misconceptions, and glossary.** *(forthcoming)*

## 2 From idea to testable hypothesis

A backtest can only teach you something if you decide, in advance, what would count as being wrong. The entire purpose of this section is to remove the freedom to decide that *after* the fact — by writing the decision down first.

### 2.1 An idea is not yet a hypothesis

Start with a real sentence a trader might say:

> *"Selling premium works better when volatility is high."*

This is an idea, not a hypothesis. It cannot be tested, because it does not commit to anything. To become testable it must name five things, with no wiggle room left:

| Component | The question it answers | Example (made concrete) |
|---|---|---|
| **Population** | On what, over what period? | S&P 500 index (SPX), regular trading hours, 2005–2026 |
| **Rule** | The exact, codeable condition and action | If VIX at yesterday's close ≥ 20, sell the ATM straddle at today's open, hold to expiry |
| **Metric** | The one number that decides it | Profit factor (gross), and expectancy per trade in R-multiples |
| **Comparison** | Better than *what*? | The same strategy with no VIX condition (the unconditional baseline) |
| **Threshold** | How much better counts? | Profit-factor uplift ≥ 0.10, and the uplift survives out-of-sample |

The moment you are forced to fill this table, half of the appealing ideas evaporate — because you discover you never meant anything precise by "works better," "high," or "premium." That evaporation is the point. A hypothesis you can state this exactly is a hypothesis you can be wrong about — and only claims you can be wrong about can teach you anything.

> **Confirmatory versus exploratory — the most important distinction in this paper.** One study answers exactly *one* confirmatory question, chosen in advance. Everything else you look at along the way is *exploratory*, and must be labelled as such. Exploration is not a sin — it is where ideas come from. The sin is letting an exploratory finding wear the clothes of a confirmatory test. A pattern you noticed *while looking* has not been tested; it has been *generated*. It earns the status "candidate hypothesis," and its test is a new study on new data.

### 2.2 Pre-registration as a workflow, not a ritual

Pre-registration means writing the full specification of the test — hypothesis, design, metric, decision rule — and *freezing it* (committing it to version control, timestamped) before the out-of-sample data has spoken. Afterward the result document is *append-only*: you may add what happened and note deviations, but you may not quietly edit the question to fit the answer. This is not academic bureaucracy; it is the cheapest possible insurance against the failure mode that ruins more strategies than any other — unconsciously tuning the question until the data agrees (Aronson 2006; López de Prado 2018). A template you can copy for each study:

```markdown
# Pre-registration — <study id / short name>

## Confirmatory hypothesis (exactly one)
- H1 (directional): <the effect you expect, with a sign>
- H0 (null): <the boring world: no effect / equal loss / sign absent>

## Expected effect size
- Point expectation: <your honest guess at the magnitude>
- Smallest effect worth acting on (SEWA): <below this, "significant" is irrelevant>

## Data & sample (fixed)
- Instrument(s): <e.g. SPX, VIX from CBOE/FRED>
- Period: <start – end>
- Source & access: <free feed; or "private list, not redistributed">

## In-sample / out-of-sample split (fixed dates, not fractions)
- In-sample (design & selection): <... ≤ date>
- Out-of-sample (opened once, at the end): <date ≤ ...>

## Metric & loss function
- Primary metric: <the ONE number that decides>
- Why this loss and not another: <one sentence>

## Decision rule (the number chosen before you see it)
- Reject H0 iff: <exact inequality> AND <significance test + threshold> AND <direction check passes>
- Otherwise: report as null.

## Multiple-testing correction (if part of a series)
- Number of variants/params to be tried: <N>
- Correction applied: <e.g. deflated Sharpe, Bonferroni, PBO — see the overfitting-control paper>

## Frozen on
- Date: <YYYY-MM-DD> · Commit: <hash> · Seed: <n>
```

Two fields carry the heavy load and deserve a closer look: the *decision rule* and the *out-of-sample split*. The split gets its own treatment in Section 4. The decision rule is the rest of this section.

### 2.3 H₀, H₁, and where the burden of proof sits

The null hypothesis H₀ is the boring world: *no edge, no difference, equal loss between your model and the naive benchmark.* You begin the study standing inside H₀, and you need real evidence to leave it. The alternative H₁ is your claim, and — this matters — it is *directional*: it commits to a sign, not merely to "something is different."

A clean example from a companion study in this library (realized-volatility forecasting) shows the shape:

- **H₀:** the log-HAR model does *not* have a lower out-of-sample QLIKE loss than a random walk (on SPX, one-day horizon).
- **H₁ (directional):** log-HAR's out-of-sample QLIKE is *lower* than the random walk's.
- **Decision rule:** reject H₀ *only if* QLIKE(log-HAR) < QLIKE(RW), *and* the Clark–West nested-model test gives *p* < 0.05, *and* the sign of the average loss difference agrees with H₁ (Patton 2011; Clark & West 2007).

Notice what the decision rule refuses to allow. A lower QLIKE that is *not* statistically distinguishable from the benchmark does not count. A significant test with the *wrong sign* does not count. Only the conjunction of magnitude, significance, and direction clears the bar — and all three were named before the out-of-sample data was opened.

> **Why directional matters.** A two-sided "is it different?" question quietly doubles your chance of a false positive and, worse, lets you retro-fit a story to whichever tail shows up. If your idea has a mechanism, the mechanism predicts a *sign*. Commit to it.

### 2.4 Commit to an effect size — a number, before the test

Most trader-hypotheses skip this and pay for it. You must write down two magnitudes in advance:

1. **Your point expectation** — honestly, how big do you think the effect is? This is a forecast, and (per the overfitting-control paper) it can itself be scored later. Being wrong about the size is informative; refusing to guess is not.
2. **The smallest effect worth acting on (SEWA)** — the magnitude below which a "statistically significant" result is *operationally meaningless*, because costs, capacity, or noise eat it.

The SEWA protects you from the most seductive trap in backtesting: a *real, significant, and useless* edge. With enough data, a profit-factor improvement of 0.02 can be "significant." It is also smaller than one tick of slippage. If you have not pre-committed a SEWA, you will find yourself defending that 0.02 because the p-value looked good — and the p-value was never the question. Statistical significance answers "is it there?"; the effect size answers "do I care?" You need both, and you must set the second one first, while you still have no incentive to lower the bar.

### 2.5 The direction check — a hard gate, learned the hard way

Before any evidence is allowed to update a hypothesis, one question is asked and must be answered explicitly: does the *sign* of the data actually match the direction of the claim?

This sounds trivial. It is the single most expensive mistake in this author's own research history. In an earlier study, a hypothesis stated that a certain flow *increases* volatility. Confirming data arrived showing a strong effect of the right *magnitude* — and it was recorded as a confirmation. The data actually showed volatility being *damped*: right size, opposite sign. The claim had been "validated" by evidence that contradicted it, because nobody checked the sign.
The fix is a reflex, not a technique: for every piece of evidence you ingest, state in one line whether it *supports*, *contradicts*, *duplicates*, or merely *extends* the existing claim — and when it contradicts, flag both the new result and the old claim for review instead of silently absorbing it. A backtest that "works" in the wrong direction is not a weak result; it is a falsification wearing a disguise.

### 2.6 Why "I'll know it when I see it" guarantees self-deception

Suppose you skip all of the above and just "explore until something looks good." Here is the mechanism by which that reliably produces a false discovery, even with complete honesty and no bugs.

Every choice you make *after* seeing the data — which threshold (20? 18? 22?), which instrument, which sub-period, which exit rule, whether to winsorize that one outlier — is a *researcher degree of freedom*. Each is a small parameter you are fitting to the noise in this particular sample. You are rarely aware of doing it, because each choice feels locally reasonable ("of course I'd drop the flash-crash day"). But the choices are not independent of the outcome: you keep the ones that improve the result and abandon the ones that don't. This is the *garden of forking paths* (Gelman & Loken 2013): you do not have to run a hundred explicit backtests to overfit — walking one adaptive path through the data, steered by what you see, is enough. And *HARKing* — *Hypothesizing After the Results are Known* — is its most flattering form: you observe a pattern, then present it as the hypothesis you "had all along."

The arithmetic is unforgiving. The expected maximum in-sample Sharpe ratio from trying *N* independent strategies on pure noise is, to a good finite-*N* approximation, σ_SR·[(1−γ)Φ⁻¹(1−1/N) + γΦ⁻¹(1−1/(N·e))], where σ_SR is the standard error of the Sharpe estimate and γ ≈ 0.5772 is the Euler–Mascheroni constant (Bailey & López de Prado 2014). The cruder σ_SR·√(2 ln N) is only the *asymptotic ceiling* of this quantity — it runs about 14% high at N = 1,000 — so we use the finite-*N* expression and quote √(2 ln N) only as an upper bound. Figure 1 makes this concrete with a simulation: with a five-year daily sample, the best of one thousand zero-edge strategies has an expected in-sample annualized Sharpe of ≈ 1.45 — manufactured entirely out of noise, and matching the finite-*N* formula (≈ 1.46), not the √(2 ln N) ceiling (≈ 1.66) — and shorter samples or more trials push it past 2. The best of a hundred backtests is not a discovery; it is an *order statistic*, and the overfitting-control paper is devoted to correcting for it. But the first and cheapest defense lives here, in this paper: freeze the question before the data can answer it, and treat every post-hoc choice as exploration that owes you a fresh test.

![Expected best in-sample annualized Sharpe ratio across *N* independently backtested strategies that all have zero true edge: Monte-Carlo estimate (20,000 repetitions, seed 42) against the Bailey–López de Prado finite-*N* expected maximum and the σ_SR·√(2 ln N) asymptotic upper bound, on a five-year daily sample. The Monte-Carlo curve tracks the finite-*N* formula, not the √(2 ln N) ceiling; the best of 1,000 pure-noise backtests shows an apparent Sharpe near 1.45. Reproduce with `figures/fig_multiple_testing.py`.](figures/fig_multiple_testing.png)

> **The one-sentence version.** *"I'll know it when I see it"* is a promise to fit your hypothesis to the noise. Pre-registration is the promise not to. Everything else in this paper is enforcement.

### 2.7 A worked pre-registration, carried through this paper

To make this concrete — and to set up the case study in Section 10 — here is the frozen pre-registration for the hypothesis we will run end to end. Read it now; in Section 10 we will confront exactly which of these commitments the *real* study honored and which it broke.

```markdown
# Pre-registration — VIX-gate short-side edge (illustrative)

## Confirmatory hypothesis (exactly one)
- H1: A short-side intraday edge in index futures is present when the prior-day
      VIX close is LOW and DEGRADES as VIX rises; gating shorts to VIX < 20
      raises gross profit factor vs. the ungated baseline.
- H0: Gating shorts to VIX < 20 does NOT raise gross profit factor
      (the VIX condition carries no information about short-side edge).

## Expected effect size
- Point expectation: profit factor +0.10 to +0.15 (baseline ~1.3).
- SEWA: +0.05 gross (below this, a live short-side edge is doubtful after costs).

## Data & sample (fixed)
- Instrument: E-mini S&P 500 (ES) intraday trade list; VIX & VIX3M daily (free).
- Period: 2022-09-05 – 2026-09-10.
- Source: VIX from free daily data; the ES trade list is private and NOT redistributed.

## In-sample / out-of-sample split (fixed dates)
- In-sample (design & threshold selection): trades ≤ 2024-12-31.
- Out-of-sample (opened once): trades ≥ 2025-01-01.

## Metric & loss function
- Primary: gross profit factor. Secondary: expectancy per contract, Sharpe, max drawdown.

## Decision rule
- Support H1 iff PF(gated) − PF(baseline) ≥ +0.05 IN-SAMPLE, the sign holds
  OUT-OF-SAMPLE, and the per-VIX-bucket pattern matches "shorts degrade as VIX rises"
  (direction check).

## Multiple-testing correction
- Threshold and gate variants tried: ~20 → correction REQUIRED (see Section 10 and the overfitting-control paper).

## Frozen on
- (Illustrative — the real study was analyzed post-hoc; Section 10 is explicit about this.)
```

That last line is not a footnote — it is the lesson. The real analysis behind this case study was run *post-hoc* on an existing trade list, with the threshold chosen *in-sample* across roughly twenty variants, and it was never pre-registered. It still produced a striking result (a gross profit factor rising from 1.32 to 1.44, holding out-of-sample). In Section 10 we will show that result *and* dismantle it with the tools of this paper — because a number that good, selected that way, is exactly the kind this section is designed to make you distrust.

## 3 Anatomy of a backtest

Before we can argue about whether an edge is real, we need a backtest whose numbers we trust. A backtest is a pipeline with three stages — signal, position, and profit-and-loss — and a mistake in any one of them manufactures returns that never existed. This section walks the pipeline, says when the fast way of computing it is safe, and then shows, on free data, how transaction costs decide whether an apparent edge survives contact with reality.

### 3.1 Three stages: signal, position, and P&L

A backtest maps information to money in three steps, and each has one discipline that matters most:

- **Signal** — a rule that turns the information available at time *t* into a desired exposure. The binding constraint: the signal at time *t* may use *only* data known at or before *t*. Every violation of this is a look-ahead leak, and Section 7 catalogues the ways it sneaks in.
- **Position** — the signal becomes an actual holding: sizing, rounding to tradable units, position limits, and one crucial timing detail. You enter at the *next* tradable price after the signal is known, not at the price that produced it. Computing a signal from today's close and then "buying at today's close" is the most common way to manufacture a fictitious edge — an off-by-one in time.
- **P&L** — mark the position to market and account the return. For a daily strategy, `strategy_return[t] = position[t−1] × asset_return[t] − cost[t]`, where `position[t−1]` is the exposure decided at the previous close and `cost[t]` is the trading cost of any change in position. Getting these subscripts right is not pedantry; it is the difference between a backtest and a look-ahead machine.

The rule behind Figure 2 is a clean example of the timing: the position held on day *t* is minus the sign of day *t*−1's return, and it earns day *t*'s return — decision strictly before outcome.

### 3.2 Vectorized versus event-driven

There are two ways to compute a backtest, and choosing the wrong one is either slow or dishonest.

- **Vectorized** — compute signals, positions, and returns over the whole series with array operations, often in a few lines of NumPy or pandas. It is fast enough to screen hundreds of variants and is *correct* whenever the position does not depend on the intrabar path: no stops or limit orders that fill mid-bar, no capital or margin constraint that binds partway through, no queue position. Most daily close-to-close studies are safely vectorized.
- **Event-driven** — step through the data bar by bar, holding state: open orders, fills, cash, realized slippage. This becomes *necessary* the moment execution is path-dependent — stop-losses and take-profits that trigger intrabar, partial fills, sizing that depends on current equity, or portfolio-level constraints across instruments. It is slower, but the only honest way to model realistic execution.

The discipline is to prototype vectorized and then re-run the survivors event-driven. A discrepancy between the two is itself a diagnostic: it is almost always a look-ahead leak or an optimistic fill assumption hiding in the fast version.

### 3.3 Costs: where edges go to die

Three components make up trading cost: the *bid-ask spread* (you cross roughly half of it per side), *slippage* (market impact plus the drift between decision and fill), and *commissions and fees*. Bundle them into a single round-trip cost per unit traded, in the instrument's own units (basis points or ticks), and be pessimistic — optimism here is indistinguishable from a fraud against your future self.

The move that separates honest research from wishful thinking is the *cost-sensitivity curve*: recompute the headline metric across a grid of cost assumptions. An edge that is alive at 0 bps and dead at 2 bps is not an edge; it is a spread you were quietly paying yourself on paper. And *turnover is the multiplier* — total cost drag ≈ turnover × per-trade cost — so a signal that flips often can show a large gross edge and no net edge, while a slow signal barely notices costs. Report turnover next to every return.

Figure 2 shows this on free data with one pre-committed, transparent rule: a 1-day reversal on the S&P 500 — hold long after a down day, short after an up day — on daily closes from Yahoo Finance, 2011–2026. Gross, it looks like a real strategy, at an annualized Sharpe of 0.41 — though that gross figure is not itself statistically distinguishable from zero: with σ_SR = √(252/T) ≈ 0.26 on T = 3,769 days the t-statistic is only about 1.6 (two-sided p ≈ 0.11) and a 95% interval of roughly [−0.09, 0.92] straddles zero. But it flips about 130 round trips a year, so cost bites fast: net Sharpe falls to 0.26 at a 1 bp one-way cost, to 0.11 at 2 bps, and reaches zero at a break-even of ≈ 2.7 bps one-way (≈ 5.4 bps round trip) — well inside the real cost of trading the index for most participants. To a first approximation, what looked like an edge was inside the spread — and, as the gross figure above already shows, it was not statistically distinguishable from zero to begin with, so there was little genuine edge for costs to eat. Nothing about the rule was tuned; it is a textbook signal reported as-is, precisely because the subject here is the cost curve, not the strategy.

![Annualized Sharpe ratio of a fixed 1-day reversal on the S&P 500 (Yahoo daily ^GSPC, 2011–2026, 3,771 sessions) as a function of the assumed one-way transaction cost. Gross Sharpe is 0.41; at roughly 130 round trips per year the edge halves by 1 bp and reaches zero at a break-even near 2.7 bps one-way. The rule is fixed in advance and reported as-is. Reproduce with `figures/fig_cost_sensitivity.py`.](figures/fig_cost_sensitivity.png)

A headline Sharpe reported with no cost assumption stated is therefore not a result. The first question to put to any backtest — your own most of all — is *"at what cost does this die?"*, and the honest place to answer it is a curve like Figure 2, drawn before any capital is at risk.

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| The best of N zero-edge backtests is inflated by selection: the best of 1,000 shows an apparent Sharpe ≈1.45 on a five-year daily sample | Own reproducible computation — `figures/fig_multiple_testing.py` |
| The expected maximum in-sample Sharpe under the null ≈ σ_SR·[(1−γ)Φ⁻¹(1−1/N)+γΦ⁻¹(1−1/(N·e))] (finite-*N*; σ_SR·√(2 ln N) is its asymptotic upper bound, ~14% high at N=1,000) | Literature — (Bailey & López de Prado 2014) |
| A textbook 1-day reversal on the S&P 500 is gross-positive (Sharpe 0.41, though not significant: t ≈ 1.6, p ≈ 0.11) and dies at a break-even near 2.7 bps one-way cost | Own reproducible computation — `figures/fig_cost_sensitivity.py` |
| Adaptive post-hoc choices overfit noise even without running many explicit backtests (garden of forking paths) | Literature — (Gelman & Loken 2013) |
| Pre-registration is the cheapest insurance against tuning the question until the data agrees | Literature — (Aronson 2006; López de Prado 2018) |
| A directional decision rule must clear magnitude, significance, and sign together (log-HAR vs random walk, QLIKE/Clark–West) | Literature — (Patton 2011; Clark & West 2007) |
| The direction check as a hard gate, learned from an in-house sign-inversion that "validated" a claim its data contradicted | Practitioner consensus — not independently verified |
| The VIX-gate case study: gross profit factor rose 1.32→1.44, selected in-sample across ~20 variants on a private trade list and holding out-of-sample | Practitioner consensus — not independently verified; OOS split |

## References

- Aronson, D. R. (2006). *Evidence-Based Technical Analysis: Applying the Scientific Method and Statistical Inference to Trading Signals.* Hoboken, NJ: Wiley.
- Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2014). Pseudo-mathematics and financial charlatanism: The effects of backtest overfitting on out-of-sample performance. *Notices of the American Mathematical Society, 61*(5), 458–471. Open access: <https://www.ams.org/notices/201405/rnoti-p458.pdf>. The source of the σ_SR·√(2 ln N) asymptotic ceiling.
- Bailey, D. H., & López de Prado, M. (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting, and non-normality. *Journal of Portfolio Management, 40*(5), 94–107. The finite-*N* expected-maximum formula used in the text and Figure 1.
- Clark, T. E., & West, K. D. (2007). Approximately normal tests for equal predictive accuracy in nested models. *Journal of Econometrics, 138*(1), 291–311.
- Gelman, A., & Loken, E. (2013). *The garden of forking paths: Why multiple comparisons can be a problem, even when there is no "fishing expedition" or "p-hacking" and the research hypothesis was posited ahead of time.* Working paper, Department of Statistics, Columbia University. Open access: <https://sites.stat.columbia.edu/gelman/research/unpublished/p_hacking.pdf>.
- López de Prado, M. (2018). *Advances in Financial Machine Learning.* Hoboken, NJ: Wiley.
- Patton, A. J. (2011). Volatility forecast comparison using imperfect volatility proxies. *Journal of Econometrics, 160*(1), 246–256.
*All references above are publicly accessible: two are open-access papers (direct links given), two are peer-reviewed journal articles, and two are published books. No proprietary, course, or trading-academy material is cited.*

