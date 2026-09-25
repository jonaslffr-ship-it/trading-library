---
title: "Overfitting Control & Forecast Calibration"
last_updated: 2026-09-20
---

# Overfitting Control & Forecast Calibration

## Abstract

The prequel to this paper argued that a backtest can only *fail to reject* an edge that was specified in advance; this paper builds the machinery that decides whether the failure-to-reject was earned or manufactured. We treat selection under multiple testing as a problem of order statistics, and show by simulation that the best of a hundred zero-edge backtests carries an apparent Sharpe ratio near one on a five-year sample and past two on a one-year sample — a hero made entirely of noise. Against that null we develop three governance tools, implemented rather than merely cited: the Deflated Sharpe Ratio, which discounts an observed Sharpe by the expected maximum of the trials that produced it; the Probability of Backtest Overfitting via combinatorially symmetric cross-validation, which asks how often an in-sample winner survives out of sample; and the bootstrap data-snooping tests of White and Hansen, surveyed against the pragmatism of the first two. We then turn from strategy selection to forecast quality, treating probabilistic forecasts as first-class objects scored by the Brier score and its Murphy decomposition into calibration, resolution, and uncertainty, and we show why a branching forecast that cannot be wrong destroys calibration. We close with base-rate discipline under non-stationarity — recency windows, the minimum-cell-size rule, and the standard error of a small-sample proportion — an assembled research protocol, and a small reusable validation library. Every number uses free or simulated data and is reproducible from the accompanying code.

## Keywords

Multiple testing, selection bias, order statistics, Deflated Sharpe Ratio, Probabilistic Sharpe Ratio, backtest overfitting, PBO, CSCV, Reality Check, superior predictive ability, forecast calibration, Brier score, Murphy decomposition, reliability diagram, proper scoring rules, base rates, non-stationarity, pre-registration

## 1 Introduction

### 1.1 Motivation and thesis

The companion backtesting paper, *Backtesting & Hypothesis Testing*, ended on a promise and a debt. The promise was that a pre-registered backtest, run once against an out-of-sample set opened once, can settle a disagreement about the world honestly. The debt was a single number it could not defend on its own: a gross profit factor that rose from 1.32 to 1.44 when short-side trades in an equity-index future were gated to a low-volatility regime, holding out-of-sample at 1.62. That result was produced by choosing a gate threshold as the best of roughly twenty variants, in-sample, on a four-year trade list that was never pre-registered. The backtesting paper showed the result and warned the reader to distrust it. It did not give the reader the tools to *quantify* the distrust. This paper is that toolkit.

The thesis is stated in one sentence and defended for the rest of the paper: *the credibility of a quantitative result is a property of the process that produced it, not of the number itself, and that process can be measured.* A Sharpe ratio of 1.4 means one thing if it is the only strategy you ever tested and something entirely different if it is the best of two hundred. A forecast that was right means one thing if you committed to it before the event and nothing at all if it was written down afterward. The number is the same in both cases; the process is not, and the process is what we learn to score.

This reframing has a practical consequence that runs through every section. Because credibility is a property of the process, it cannot be recovered after the fact: you cannot look at a finished backtest and reverse-engineer how many trials produced it, you cannot look at a forecast record and tell which entries were written before the event, and you cannot look at a conditional table and see how many regimes it silently averages. The information you need to judge a result is generated *during* the research and destroyed if it is not recorded as it happens. Every tool in this paper is therefore also an instruction to instrument your process while you run it — to count your trials, timestamp your forecasts, and log your refutations — because the alternative is to arrive at a beautiful number you can no longer defend.

Three failures recur across every quantitative research program, and each has a matching instrument here. *Selection under multiple testing* inflates the best result you find to a level that pure noise would have produced anyway — corrected by the Deflated Sharpe Ratio (Section 3) and diagnosed by the Probability of Backtest Overfitting (Section 4). *Miscalibrated confidence* lets a forecaster feel skilled while being systematically overconfident — measured by the Brier score and its decomposition (Section 6). *Non-stationary base rates* let a conditional table look informative when it is merely stale or too thin to read — disciplined by recency windows and a minimum-cell-size rule (Section 7). The paper ends by assembling these into one research protocol (Section 8) and one small library (Section 9) that the other empirical documents in this library reuse.

### 1.2 Scope, prerequisites, and intended reader

This paper sits in the Trading Library's *Quant Methods* track. It assumes the backtesting paper: pre-registration as a workflow, the operational meaning of opening the out-of-sample set once, expectancy and the trade distribution, the *researcher-degrees-of-freedom* argument, and the *garden of forking paths*. It assumes the statistics-for-traders paper for standard errors, the Sharpe ratio as an estimated quantity with sampling error, and comfort reading a short Python listing. It assumes no measure theory, no stochastic calculus, and no familiarity with the specific tests introduced here — the derivations are given at a readable pace, the assumptions behind each are made explicit, and every method is implemented in full rather than left as a citation.

After reading this paper, a reader can:

- state, and defend with a simulation, why the best of *N* backtests is an order statistic rather than a discovery, and how that inflation scales with sample length and number of trials;
- compute a Deflated Sharpe Ratio from the four inputs that actually matter — number of trials, skewness, kurtosis, and sample length — and explain the exact point at which it flips a "discovery" back to noise;
- run combinatorially symmetric cross-validation on a battery of candidate strategies, read the resulting Probability of Backtest Overfitting honestly, and know what 0.3 versus 0.7 says about their *process* rather than any single strategy;
- decide when the full bootstrap machinery of a Reality Check or a Superior-Predictive-Ability test is worth its cost and when the Deflated Sharpe Ratio and the overfitting probability are the pragmatic answer;
- treat a probabilistic forecast as a first-class object — one direction, one falsifier, one probability, one horizon — score it with a proper scoring rule, decompose the score into calibration, resolution, and uncertainty, and recognise the branching forecast that cannot be wrong;
- maintain a conditional base-rate table under regime drift without fooling themselves, refusing to make a claim from a cell with fewer than fifteen observations and knowing the arithmetic that justifies the refusal;
- and wire all of the above into a single append-only research protocol whose status labels mean exactly what they say.

### 1.3 Data and reproducibility

All figures and numerical examples use freely available or purely simulated data. The three multiple-testing figures and the calibration figure are Monte-Carlo simulations with a fixed seed and no market data at all; the base-rate figure uses daily S&P 500 closes pulled from a public chart API and cached locally so the figure reproduces offline. Each figure names its reproducing script. Where an example draws on a private research log, the log is *not* redistributed and the fact is stated explicitly — the reader gets the anonymized number and the method, never the underlying rows. *This is a research and educational document, not investment advice.*

A note on honesty that the rest of the paper depends on: the figures in this paper were generated by scripts written *before* their numbers were known, each embodying exactly one pre-committed rule, precisely because a paper about data-snooping that snooped its own illustrations would be self-refuting. Where a simulated number came out inconvenient — the injected weak edge in Section 4 that the process fails to find, the observed Sharpe in Section 3 that falls *below* its own noise ceiling — it is reported as it fell.

### 1.4 Organization of this paper

The paper is complete; all sections below are written, and the two implementation sections (Section 3 and Section 9) contain runnable code rather than pseudocode.

- **Section 2 Why the best of 100 backtests is a lie** develops multiple testing as an order-statistics problem, drawing the full sampling distribution of the best-of-*N* Sharpe under pure noise and showing its joint dependence on sample length and number of trials, then names the selection bias that hides the trials — the folder of dead strategies nobody publishes.
- **Section 3 The Deflated Sharpe Ratio** derives the Probabilistic Sharpe Ratio and deflates it to the DSR, isolates the four inputs it needs, gives a ~60-line implementation, and runs it on a simulation that mirrors the structure of the backtesting paper's case study — showing exactly when the DSR flips a discovery to noise.
- **Section 4 The Probability of Backtest Overfitting** explains combinatorially symmetric cross-validation without hand-waving, implements it, and runs it on three simulated strategy batteries (pure noise, a weak injected edge, a strong one) so the reader can calibrate what a PBO of 0.5 versus 0.01 means about their process.
- **Section 5 Reality Check and SPA** surveys the bootstrap data-snooping tests of White and Hansen, and draws the line between when their full machinery earns its cost and when the DSR/PBO pair is the pragmatic answer.
- **Section 6 Forecast calibration** treats probabilistic forecasts as first-class objects, imposes the one-direction-one-falsifier discipline and shows why branching forecasts must be scored as several, develops the Brier score and its Murphy decomposition, draws reliability diagrams for a calibrated and an overconfident forecaster, and dismantles the circular-evaluation trap in which in-sample hit rates masquerade as skill.
- **Section 7 Base rates under non-stationarity** treats the conditional table as a living object, frames the recency-versus-full-history choice as an honest bias/variance trade, and makes the minimum-cell-size rule a hard gate backed by the standard error of a small-sample proportion — with the unconditional S&P 500 up-day base rate shown drifting across a century.
- **Section 8 An honest research protocol, assembled** wires pre-registration, the test, the append-only log, the falsification check, and the status-upgrade rules into one loop, expressed as a checklist and a directory template the reader can adopt.
- **Section 9 The validation suite as reusable code** collects the DSR, PBO, and Brier implementations into one small library and shows how the dealer-flows-and-GEX paper and the volatility-modeling paper call into it.
- The **References** are annotated.

## 2 Why the best of 100 backtests is a lie

The backtesting paper gave the headline result: the expected best in-sample annualized Sharpe ratio from trying *N* independent zero-edge strategies grows like σ_SR·√(2 ln N), and the best of a thousand pure-noise backtests on a five-year daily sample shows an apparent Sharpe near 1.45 (Bailey et al. 2014). That figure showed only the *mean* of the best-of-*N*. This section shows the whole distribution, because the mean understates the problem in two directions at once, and because everything in Section 3 and Section 4 is a response to the shape drawn here.

### 2.1 A Sharpe ratio is an estimate, and estimates have a sampling distribution

Write the per-period Sharpe ratio of a return series as SR = μ/σ, the ratio of the sample mean return to the sample standard deviation. Under the null that the true edge is zero and returns are roughly Gaussian and independent, the *estimate* SR is itself a random variable centred on zero with a standard error that shrinks with sample length. Annualized, the standard error of the Sharpe estimate on *T* daily observations is approximately

  σ_SR ≈ √(252 / T).

This one formula carries the whole section — with one assumption named now and discharged in Section 3.1: it treats returns as serially *independent*. When they are autocorrelated (leveraged, trend-following, or overlapping-holding-period strategies) the effective sample is smaller and this formula runs *optimistic*; Section 3.1 gives the Lo (2002) correction and insists it not be skipped silently. On the S&P 500's daily returns the measured first-order autocorrelation is about −0.11 (the 1-day reversal *strategy* of the backtesting paper de-correlates further — its own returns show an AR(1) near −0.005), small enough that the iid formula is a fair approximation *here*, but the caveat is general. On a five-year sample (*T* = 1260) it gives σ_SR ≈ 0.45; on a one-year sample (*T* = 252) it gives σ_SR ≈ 1.0. A single zero-edge strategy on one year of data therefore has an annualized Sharpe that is a standard normal variable — routinely ±1, occasionally ±2, entirely by chance. Nothing is wrong with that strategy; it simply has no edge and a short measurement window.

### 2.2 The best of *N* is an order statistic

Now stop looking at one strategy and look at the best of *N*. If you compute *N* such estimates and keep the largest, you are no longer sampling from the distribution of a Sharpe ratio — you are sampling from the distribution of the *maximum* of *N* draws, an *order statistic*. The maximum of *N* independent standard-normal draws grows without bound, slowly, like √(2 ln N); multiplied by σ_SR it gives the ceiling the backtesting paper quoted. But the maximum has a full distribution of its own, and two features of that distribution matter more than its mean.

Figure 1 draws it directly. For *N* in {1, 10, 100, 1000} zero-edge strategies, on both a five-year and a one-year daily sample, it plots the Monte-Carlo sampling distribution of the best in-sample annualized Sharpe over twenty thousand repetitions. Two lessons fall out. First, *the distribution shifts right and tightens as N grows*: the best of many noise backtests is not just biased upward on average, it is *reliably* impressive — the spread of the maximum shrinks even as its centre climbs, so "I got unlucky, my best number is just a tail event" becomes a weaker and weaker excuse. On the five-year sample the expected best rises from essentially zero at *N* = 1 to 0.69 at *N* = 10, 1.12 at *N* = 100, and 1.45 at *N* = 1000. Second, *sample length scales every hero by √(252/T)*: the one-year panel is the five-year panel stretched by a factor of √5 ≈ 2.24. On one year of data the best of a hundred zero-edge strategies has an expected annualized Sharpe of 2.51, and more than four in five such "best" strategies clear a Sharpe of 2.0 — a threshold most practitioners would read as a serious edge. Short samples manufacture the biggest heroes.

![The best of N zero-edge backtests, full sampling distribution rather than just its mean. For N in {1, 10, 100, 1000} strategies with zero true edge, the Monte-Carlo distribution (20,000 repetitions, seed 42) of the best in-sample annualized Sharpe, on a five-year sample (left) and a one-year sample (right). The distribution shifts right and tightens as N grows; halving-to-a-fifth the sample length scales every Sharpe by the square root of five. On one year of data the best of 100 pure-noise strategies has an expected Sharpe near 2.5. Reproduce with figures/fig_sharpe_noise_dist.py.](figures/fig_sharpe_noise_dist.png)

The complement to the backtesting paper's Figure 1 is deliberate: that paper plotted the expected maximum against the √(2 ln N) ceiling to establish *that* selection inflates; Figure 1 here plots the *whole* distribution across two sample lengths to establish *how reliably* it inflates and *how sharply sample length amplifies it*. The first figure justifies pre-registration; this one justifies the deflation arithmetic of Section 3, which needs the spread of the maximum, not just its centre.

It is worth pausing on how *slowly* the √(2 ln N) ceiling grows, because the slowness is a trap. Going from ten trials to a hundred raises the ceiling by a factor of √(ln 100 / ln 10) ≈ 1.4, and from a hundred to a thousand by only ≈ 1.2. This gentleness is seductive in exactly the wrong way: it means that a researcher who quietly triples their trial count barely moves the ceiling, so the inflation feels negligible at each step — and yet the *cumulative* effect over a long research program, where thousands of little variants are tried across dozens of studies, is an expected best Sharpe near 1.5 out of pure noise on a five-year sample and past 3 on a single year. The danger is not that any one extra trial is costly; it is that no single trial feels costly, so the count is never taken seriously until the number that emerges is indefensible. The √-of-a-log is precisely the functional form that lulls a careful person into overfitting.

### 2.3 The folder of dead strategies nobody publishes

The arithmetic above assumes you *know* *N* — the number of trials. In practice the most dangerous *N* is the one you cannot see. Selection bias in a research pipeline operates in two layers, and only the first is under your control.

The inner layer is your own search. Every threshold you nudged, every instrument you swapped, every sub-period you dropped, every exit rule you tried and abandoned is a trial, whether or not you ran it as an explicit backtest. The backtesting paper called this the garden of forking paths; the point here is quantitative — each of those silent trials increases the *N* that Section 3 will demand you deflate by, and the honest count is almost always larger than the remembered one. A discipline follows directly: log the trials as you make them, so that the *N* fed to the DSR is real rather than flattering.

The outer layer is the literature you read. Published strategies, vendor backtests, and the results that circulate on trading forums are a *survivorship-selected* sample: the strategies that failed were quietly deleted, and only the winners were written up. The reader of a single impressive backtest is seeing the maximum of an unknown and possibly enormous *N* without being told the *N*. This is the folder of dead strategies nobody publishes, and it is why an external result — even a one — can never move a hypothesis past "formulated" in this library's status scheme (Section 8): the citation reports the winner, not the search that produced it, and the search is exactly what the DSR needs to see. The only *N* you can ever fully account for is your own, which is one more reason to run your own tests rather than inherit someone else's number.

## 3 The Deflated Sharpe Ratio

If Section 2 is the disease, the Deflated Sharpe Ratio is the first treatment: given an observed Sharpe ratio and an honest count of the trials that produced it, it returns the probability that the true Sharpe exceeds the level that selection alone would have manufactured. It was introduced by Bailey and López de Prado (2014) and rests on a simpler object, the Probabilistic Sharpe Ratio (Bailey & López de Prado 2012); we derive the second and then deflate it into the first.

### 3.1 From Sharpe to Probabilistic Sharpe

The observed Sharpe ratio SR is an estimate, and Section 2.1 gave its standard error under Gaussian returns. Real return series are not Gaussian — they are skewed and heavy-tailed — and the standard error of the Sharpe estimate depends on exactly those higher moments. Mertens (2002) and Bailey and López de Prado (2012) give the corrected standard error of the per-period Sharpe estimate on *n* observations as

  σ(SR) = √( (1 − γ₃·SR + (γ₄ − 1)/4·SR²) / (n − 1) ),

where γ₃ is the skewness of the returns and γ₄ their kurtosis (non-excess, so a Gaussian series has γ₄ = 3). Negative skew and fat tails — the signature of most premium-selling and trend strategies — *inflate* this standard error, which means the same headline Sharpe is worth less when it comes from an uglier return distribution. The Probabilistic Sharpe Ratio turns this standard error into a probability. For a benchmark Sharpe SR\*, define

  PSR(SR\*) = Φ( (SR − SR\*)·√(n − 1) / √(1 − γ₃·SR + (γ₄ − 1)/4·SR²) ),

where Φ is the standard normal CDF. In words: PSR(SR\*) is the probability that the *true* Sharpe exceeds SR\*, given the observed Sharpe, the sample length, and the higher moments. Setting SR\* = 0 answers "is the true Sharpe positive at all?" — a weak question, because Section 2 showed that a Sharpe comfortably above zero is exactly what selection manufactures. The strong question is: positive relative to *what selection would have produced anyway?*

Two assumptions sit under the standard-error formula and both deserve a caveat before we build on it. First, it assumes returns are serially *independent*; if they are autocorrelated — as leveraged, trend-following, or overlapping-holding-period strategies routinely are — the effective sample size is smaller than *n*, and Lo (2002) gives the correction that scales the Sharpe standard error by a factor capturing the autocorrelation structure. The `psr` implementation in Section 9.1 therefore takes an optional first-order autocorrelation argument and deflates the effective sample by the AR(1) factor (1 − ρ)/(1 + ρ); left at its ρ = 0 default it assumes independence, and skipping the correction when returns are in fact autocorrelated makes a strategy look more precisely measured than it is — the optimistic direction — so it must not be skipped silently. Second, the formula treats the higher moments γ₃ and γ₄ as known, when on a few hundred observations they are themselves noisily estimated — kurtosis especially, being a fourth-moment quantity, is unstable in small samples and can swing the PSR denominator around. The honest use of the PSR is therefore as a well-calibrated *order of magnitude*, not a fourth-decimal verdict; Section 9.3 returns to this limit and the others.

### 3.2 Deflating the benchmark to the noise ceiling

The Deflated Sharpe Ratio answers the strong question by setting the benchmark SR\* not to zero but to the *expected maximum Sharpe under the null of no true edge across all N trials*. Bailey and López de Prado (2014) give this expected maximum, using the asymptotics of the maximum of *N* Gaussian draws, as

  SR\*₀ = √(V[SR]) · [ (1 − γ)·Z⁻¹(1 − 1/N) + γ·Z⁻¹(1 − 1/(N·e)) ],

where V[SR] is the variance of the Sharpe estimates *across the N trials*, γ ≈ 0.5772 is the Euler–Mascheroni constant, Z⁻¹ is the inverse standard normal CDF, and *e* is Euler's number. The intuition is exactly Figure 1: as *N* grows, the expected best Sharpe climbs, and SR\*₀ is that climbing ceiling written as a formula. The DSR is then simply the PSR measured against this deflated benchmark:

  DSR = PSR(SR\*₀).

A DSR of 0.95 says: even accounting for the *N* trials, their correlation (through V[SR], which shrinks when the trials share trades), and the non-normality of the winning series, there is a 95% probability that the true Sharpe of the selected strategy exceeds the level selection alone would have produced. Four inputs, and only four, drive the verdict: the *number of trials N*, the *skewness γ₃* and *kurtosis γ₄* of the selected series, and the *sample length n*. Everything else is arithmetic. This is worth dwelling on because it tells you where the leverage is: doubling your sample length helps through both σ(SR) and n; halving your honest trial count helps through SR\*₀; and a nasty return distribution (negative skew, fat tails) hurts twice, once in the standard error and once because such strategies tend to be the ones that overfit most eagerly.

### 3.3 Implementation

The whole calculation fits in about sixty lines with no dependencies beyond the standard library. The only non-trivial piece is an inverse normal CDF; we use Acklam's rational approximation, accurate to better than 1e-9, so the module is self-contained.
```python
import math

EULER = 0.5772156649015329

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def norm_ppf(p):
    """Acklam's rational approximation to the inverse normal CDF (|err| < 1e-9)."""
    a = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00)
    if p < 0.02425:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > 1 - 0.02425:
        return -norm_ppf(1 - p)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

def psr(sr, sr_star, n, skew, kurt, rho=0.0):
    """Probabilistic Sharpe Ratio: P(true SR > sr_star). Per-period units.
    rho = first-order autocorrelation of the returns. Under serial dependence the
    effective sample is smaller than n (Lo 2002); deflate it by the AR(1) factor
    (1-rho)/(1+rho) so the standard error is not understated. rho=0 -> iid."""
    n_eff = n * (1.0 - rho) / (1.0 + rho) if rho else n
    den = math.sqrt(max(1e-12, 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr ** 2))
    return norm_cdf((sr - sr_star) * math.sqrt(n_eff - 1.0) / den)

def expected_max_sr(n_trials, var_trials):
    """E[max of n_trials zero-mean SR estimates], per period (Bailey & LdP 2014)."""
    return math.sqrt(var_trials) * ((1 - EULER) * norm_ppf(1 - 1.0 / n_trials)
                                    + EULER * norm_ppf(1 - 1.0 / (n_trials * math.e)))

def deflated_sharpe(sr, n, skew, kurt, n_trials, var_trials, rho=0.0):
    """DSR: PSR measured against the expected max of n_trials noise trials.
    rho forwards the Lo (2002) AR(1) correction to psr, so the DSR is also
    deflated for serial dependence (rho=0 -> iid)."""
    return psr(sr, expected_max_sr(n_trials, var_trials), n, skew, kurt, rho)
```

Three implementation notes decide whether the answer is honest. First, `sr` and `var_trials` are *per-period* quantities; if you work in annualized Sharpe, divide by √252 before calling and the ratio is unchanged, but do not mix units — a per-period Sharpe fed to a formula expecting annualized inflates the result grotesquely. Second, `var_trials` is the variance of the Sharpe estimates *across your trials*, and it is the channel through which trial *correlation* enters: gate variants that share most of their trades produce highly correlated Sharpes and a *small* V[SR], which lowers the noise ceiling — twenty near-identical variants are not twenty independent trials, and the formula rewards you for that only if you measure V[SR] from the trials themselves rather than assuming independence. Third, `n_trials` is the honest count from Section 2.3, including the silent ones; understating it is the easiest way to make a bad strategy pass.

### 3.4 Worked example, wired to the backtesting paper's case study

The backtesting paper's case study selected a VIX gate as the best of roughly twenty variants on a four-year trade list, producing a profit factor of 1.44 in-sample. To see what the DSR does to a selection of that *shape*, we simulate its structure with the truth known: twenty candidate return series over 1005 daily observations (~4 years), 50% pairwise correlated because gate variants share most of their trades, and *zero true edge* in every one. A negatively-skewed common shock is baked in so the winning series has realistic higher moments. We then select the variant with the best in-sample Sharpe — exactly the operation the real study performed — and ask both the naive PSR and the DSR for a verdict.

Figure 2 shows the outcome. The twenty variants scatter around zero as they must, and the selected one carries an annualized Sharpe of 0.72 with a gross profit factor of 1.12, mild negative skew (−0.18) and near-normal kurtosis (3.21). The naive PSR — treating the winner as if it were the only strategy ever tested, benchmark zero — returns **0.925**: read alone, that looks like a discovery, a 92% probability of positive true Sharpe. But the expected maximum of twenty correlated zero-edge trials is an annualized Sharpe of **0.85**, and the observed winner at 0.72 sits *below* its own noise ceiling. The DSR, measuring against that ceiling, returns **0.400**: not a discovery, entirely consistent with the best of twenty noise trials. Same number, different history, different verdict — and the difference is the whole point of the tool.

![The Deflated Sharpe Ratio applied to a best-of-20 selection with zero true edge. Left: twenty correlated zero-edge variants (T=1005 daily observations, ~4 years, 50% pairwise correlation); the selected in-sample winner carries an annualized Sharpe of 0.72, below the dashed noise ceiling — the expected maximum of 20 noise trials at 0.85. Right: the null distribution of that maximum, with the observed winner marked; the naive PSR reads 0.93 while the DSR reads 0.40. Reproduce with figures/fig_dsr_worked.py.](figures/fig_dsr_worked.png)

How high would the observed Sharpe have had to be to survive? Inverting the DSR for these moments, this *N*, and this sample length, the selected variant would need an annualized Sharpe of **1.69** to clear a DSR of 0.95 — more than double what selection alone produced. That number is the honest bar the in-sample result of the backtesting paper's case study was quietly failing to clear.

It is worth walking the arithmetic once by hand, because the gap between the two verdicts comes entirely from one substitution. The naive PSR plugs the observed per-period Sharpe, the sample length of 1005, and the measured skew and kurtosis into the PSR formula with SR\* = 0, and the resulting z-score is comfortably positive, giving Φ(z) = 0.925. The DSR changes exactly one thing: it replaces the benchmark 0 with SR\*₀, the expected maximum of twenty correlated noise trials, whose per-period value corresponds to an annualized 0.85. Because the *observed* annualized Sharpe (0.72) is now *below* the benchmark it is measured against, the numerator (SR − SR\*₀) turns negative, the z-score flips sign, and Φ of a negative number falls below one-half — 0.400. Nothing about the strategy changed between the two calculations; the only new information was the count of trials, entering through SR\*₀, and it was enough to move the verdict across the decision line. That single substitution is the entire content of the deflation, and seeing it done by hand is the fastest inoculation against reading a naive PSR as if it were a DSR.

This is the point at which the DSR flips a discovery to noise, and it is worth stating precisely what it does and does not say about the real study. The DSR sees only the in-sample selection, and on the in-sample selection its verdict is unambiguous: a profit factor uplift chosen as the best of ~20 variants is statistically indistinguishable from a best-of-20 fluke, and should never have been reported as a finding. What keeps the real hypothesis alive at all is the *separate, out-of-sample* observation that the gate held at a profit factor of 1.62 on data the threshold never saw — an independent corroboration the DSR does not and cannot use, because the DSR is a statement about the in-sample search, not about the out-of-sample hold. The correct reading is therefore layered: the in-sample number is worthless as evidence (DSR says so), the out-of-sample hold is a single encouraging data point (not a pre-registered test, so at most a status of "formulated" under Section 8), and the honest next step is a genuinely pre-registered replication on fresh data. A number that good, selected that way, earns exactly one thing: a new study.

### 3.5 Correlated trials and the effective number of independent bets

The single input researchers get most wrong is *N*, and the error runs in both directions. Understating it — forgetting the silent variants of Section 2.3 — makes a fluke pass. But mechanically inflating it can also mislead, because the *N* in the expected-maximum formula is a count of *independent* trials, and twenty gate variants that share nine-tenths of their trades are nowhere near twenty independent bets. The DSR handles this correctly, but only if V[SR] is *measured from the trials themselves* rather than assumed: highly correlated variants produce Sharpe estimates that cluster tightly, hence a small V[SR], hence a lower noise ceiling SR\*₀ than twenty independent trials would demand. The formula, in other words, already gives you credit for the fact that your twenty variants were really only a handful of distinct ideas — but you collect that credit only by feeding it the empirical variance across the trials, never a textbook value.

A useful sanity check is the *effective number of independent trials*, roughly N_eff ≈ N / (1 + (N − 1)·ρ̄) for average pairwise correlation ρ̄. The twenty variants of the backtesting paper's case study at ρ̄ ≈ 0.5 behave like only about two independent bets by this crude measure — which is why the correctly-measured V[SR] in the simulation was small, and why the honest noise ceiling (0.85) was far below what twenty *independent* trials would have implied. The lesson cuts against the reflex to pad the trial count for safety: the right move is not to inflate *N* but to measure the covariance the variants actually share, and let SR\*₀ reflect the truth that a wide search over near-identical ideas is a narrow search wearing a wide costume.

## 4 The Probability of Backtest Overfitting

The DSR corrects a *single* selected Sharpe for the trials behind it. The Probability of Backtest Overfitting asks a different and complementary question about the *process*: across all the ways you could have split your data into a design half and a validation half, how often does the strategy you would have selected in-sample end up below the median out-of-sample? If the answer is "about half the time," your selection procedure has no ability to pick out-of-sample winners, and it does not matter which strategy it happened to pick. PBO was introduced by Bailey, Borwein, López de Prado and Zhu (2017), with the accessible companion argument in their *Notices of the AMS* paper (Bailey et al. 2014).

### 4.1 Combinatorially symmetric cross-validation, without hand-waving

The mechanism is called *combinatorially symmetric cross-validation* (CSCV), and the two adjectives are the whole idea. Take the matrix of returns for *N* candidate strategies over *T* periods and cut the *T* periods into *S* equal, contiguous blocks (we use *S* = 16). Now consider every way of choosing *S*/2 of those blocks to be the in-sample set, leaving the other *S*/2 as out-of-sample. There are C(16, 8) = 12,870 such splits. *Combinatorial* means you use all of them, not a single arbitrary train/test cut; *symmetric* means every split has a complementary partner with in-sample and out-of-sample swapped, so no period is privileged as "training" or "testing" — each block spends exactly half the splits on each side. This is what makes the diagnostic a statement about the *process* rather than an accident of where you happened to draw the line.

For each of the 12,870 splits, the procedure does four things: compute each strategy's Sharpe on the in-sample blocks; select the strategy with the best in-sample Sharpe (this is your selection rule, applied honestly to each split); compute that same strategy's Sharpe on the out-of-sample blocks; and record its *rank* among all *N* strategies out-of-sample, converted to a logit. If the in-sample winner lands in the top half out-of-sample, the logit is positive; if it lands in the bottom half, negative. The Probability of Backtest Overfitting is simply the fraction of splits in which the in-sample winner ends *at or below* the out-of-sample median — the fraction of the time your selection rule picked an out-of-sample loser.

  PBO = (number of splits with logit ≤ 0) / (total number of splits).

Two properties make this honest where a single train/test split is not. Because it averages over all 12,870 splits, PBO cannot be gamed by a lucky choice of cut date. And because it selects *within each split* using your real rule, it measures your *procedure's* propensity to overfit, not the quality of one pre-chosen strategy — which is exactly the object Section 2.3 said you cannot otherwise see.

### 4.2 Implementation and the block-sufficient-statistics trick

Twelve thousand splits over fifty strategies sounds expensive; it is not, because the in-sample and out-of-sample Sharpes can be assembled from *per-block sufficient statistics* — the sum and sum-of-squares of returns within each block — computed once. Each split is then a handful of vector additions rather than a re-scan of the data.
```python
import math, itertools
import numpy as np

def pbo_cscv(returns, s_blocks=16):
    """Probability of Backtest Overfitting via CSCV.
    returns: (T, N) array of per-period returns for N candidate strategies.
    Returns (pbo, logits) where logits<0 means the IS winner fell below the OOS median."""
    t, n = returns.shape
    b = t // s_blocks
    r = returns[:b * s_blocks].reshape(s_blocks, b, n)
    bs, bq = r.sum(axis=1), (r ** 2).sum(axis=1)      # per-block sum, sum of squares
    half = s_blocks // 2
    m = half * b                                       # observations per half
    tot_s, tot_q = bs.sum(axis=0), bq.sum(axis=0)
    logits = []
    for combo in itertools.combinations(range(s_blocks), half):
        idx = list(combo)
        s1, q1 = bs[idx].sum(axis=0), bq[idx].sum(axis=0)   # in-sample half
        s2, q2 = tot_s - s1, tot_q - q1                     # out-of-sample half
        mean1, mean2 = s1 / m, s2 / m
        var1 = (q1 - m * mean1 ** 2) / (m - 1)
        var2 = (q2 - m * mean2 ** 2) / (m - 1)
        sr1, sr2 = mean1 / np.sqrt(var1), mean2 / np.sqrt(var2)
        j = int(np.argmax(sr1))                             # in-sample winner
        rank = int((sr2 < sr2[j]).sum()) + 1                # its OOS rank (1 = worst)
        w = rank / (n + 1.0)
        logits.append(math.log(w / (1.0 - w)))
    logits = np.array(logits)
    return float((logits <= 0).mean()), logits
```

The full distribution of logits, not just its mean, is the useful output: a symmetric cloud centred on zero is the signature of a process with no out-of-sample selection ability, while a distribution pushed firmly to the right is a process that reliably finds real edges.

### 4.3 Diagnostics on a simulated strategy battery

To calibrate what PBO values *mean*, we run three batteries of *N* = 50 daily return series over *T* = 1248 periods (~5 years), mildly correlated through a common factor. Battery A has fifty zero-edge strategies. Battery B is identical but one strategy is given a true annualized Sharpe of 1.0 — a *real* edge that must nonetheless compete in-sample against forty-nine noise strategies whose best fluctuations rival it. Battery C gives that one strategy a true annualized Sharpe of 2.0, strong enough that the selection process should find it. Figure 3 shows the logit distribution and PBO for each.

![Combinatorially symmetric cross-validation on three strategy batteries. Each panel plots the distribution of the out-of-sample rank (as a logit) of the in-sample winner across all C(16,8)=12,870 symmetric splits, for N=50 strategies over T=1248 periods. Left: fifty zero-edge strategies, PBO 0.52. Middle: one strategy with a true annualized Sharpe of 1.0 injected, PBO 0.46. Right: one strategy with a true Sharpe of 2.0, PBO 0.01. A weak real edge drowns among noise competitors; a strong one is found almost every time. Reproduce with figures/fig_pbo_cscv.py.](figures/fig_pbo_cscv.png)

The numbers tell a graded story. Battery A returns **PBO 0.52** — a coin flip. The in-sample winner is below the out-of-sample median about half the time, its mean out-of-sample annualized Sharpe is −0.32, and no single strategy dominates the selection (the most-often-picked wins only 23% of splits). This is what a pure data-mining process looks like: it produces a "best" strategy on every split, and that strategy is worthless. Battery B is the humbling one: even with a *genuine* annualized-Sharpe-1.0 edge present, **PBO is 0.46** and the injected strategy is selected in only 19% of splits, with a mean out-of-sample Sharpe of −0.24. A real but modest edge, buried among forty-nine noise competitors on five years of data, is *not reliably findable by selection* — the noise strategies' best in-sample fluctuations out-compete it too often. Only Battery C, with a true Sharpe of 2.0, is cleanly recovered: **PBO 0.01**, the injected strategy selected in 98.8% of splits, mean out-of-sample Sharpe 1.53.

### 4.4 Reading PBO honestly

The temptation is to read PBO as a property of a strategy — "my strategy has a PBO of 0.3, so it is 70% good." It is not. PBO is a property of *the pairing of your strategy universe and your selection rule*, and it answers one question: does the way I pick winners in-sample carry any information about which will win out-of-sample? A PBO near 0.5 says it does not, and the correct response is not to tweak the chosen strategy but to distrust the entire selection — you are mining noise, and Battery B proves that even a real edge cannot save a process that searches too wide a universe on too short a sample. A PBO near 0.1 or below says your process reliably surfaces out-of-sample winners, which is a statement you have *earned the right to make about the process* before you ever defend the particular strategy. The practical reading of intermediate values is deliberately blunt: below ~0.2, the process is trustworthy enough to proceed to a pre-registered out-of-sample test of the selected strategy; between 0.2 and 0.5, treat any selected strategy as a candidate hypothesis needing fresh data, not a result; above 0.5 — which is possible — your in-sample winners are *anti-predictive* out-of-sample, a sign of a search so aggressive it fits the training folds against the validation folds. In every case the lesson is about the folder of dead strategies from Section 2.3: PBO makes the invisible *N* visible by simulating the selection you would have done on data you did not privilege, and it is the cheapest honest audit of a research pipeline available. One numerical caveat keeps it honest in the other direction: a single PBO estimate is itself a noisy statistic — resampled on a battery of about fifty null strategies its Monte-Carlo standard deviation runs on the order of 0.2 — so a fine distinction like Battery A at 0.52 versus Battery B at 0.46 is well within noise. Read PBO in wide bands (near-0.5 versus near-0.1), never as a sharp threshold on the second decimal.

### 4.5 Choosing the block count, and the companion diagnostics

Two practical questions decide whether a PBO number is trustworthy. The first is the number of blocks *S*. Too few — say *S* = 4, giving only C(4, 2) = 6 splits — and the PBO estimate is itself noisy; too many and each block becomes too short to give a stable per-block Sharpe, and contiguous blocks stop preserving the return series' autocorrelation, which biases the out-of-sample ranks. The original authors' default of *S* = 16, giving 12,870 symmetric splits, is a reasonable balance for a multi-year daily series and is what Section 4.3 used; the honest move is to recompute PBO at a second block count (say 10 or 12) and confirm the verdict does not swing on the choice, because a PBO that jumps from 0.2 to 0.5 when you change *S* is telling you the estimate is unstable rather than that the process is fine.

The second is that PBO is one member of a family, and the same CSCV pass yields its siblings at no extra cost. The *performance-degradation* slope — from a regression of the in-sample winner's out-of-sample rank on its in-sample rank across all splits — measures how much out-of-sample performance you lose per unit of in-sample performance; a shallow or negative slope is the real signature of overfitting, sometimes visible even when PBO looks acceptable. The *probability of loss* — the fraction of splits in which the in-sample winner is outright unprofitable out-of-sample — translates the abstract rank into a number a risk manager understands. A process can post a middling PBO of 0.35 alongside a brutal degradation slope, meaning the modest out-of-sample edge it does find evaporates fast; reading the three diagnostics together, rather than fixating on PBO alone, is the difference between a number and a diagnosis.

## 5 Reality Check and SPA

The DSR and PBO are pragmatic: the first needs only summary statistics and an honest trial count, the second needs the return matrix but runs in seconds. There is an older and in some ways more rigorous family of tests that asks the multiple-testing question directly through the bootstrap, and an advanced reader should know what it does and when its extra cost is justified.

### 5.1 White's Reality Check

White's Reality Check (2000) formalizes exactly the Section 2 problem: given a *set* of *N* strategies (or forecasting models) and a benchmark, is the *best-performing* member genuinely superior, or is its outperformance what the best of *N* would show under the null of no edge? The null hypothesis is that no strategy in the set beats the benchmark — max over strategies of the expected performance difference is ≤ 0. White's insight is that the sampling distribution of this maximum statistic can be obtained by *bootstrapping the whole set jointly*: resample the time series of performance differences (with a stationary or block bootstrap to preserve autocorrelation), recompute the maximum on each resample, and read the data-snooping-adjusted p-value off the bootstrap distribution (White 2000; Politis & Romano 1994 for the stationary bootstrap). Because the resampling is joint across strategies, the test automatically accounts for the correlation between them — the same correlation the DSR captures through V[SR] — without assuming independence.

### 5.2 Hansen's Superior Predictive Ability test

Hansen (2005) identifies a defect in the Reality Check and repairs it. The Reality Check's null centres every strategy at the benchmark, including strategies that are obviously terrible; those poor models inflate the variance of the maximum statistic and make the test *conservative* — it loses power to detect a genuine winner when the set is padded with junk, which is precisely the situation Section 4's Battery B described. Hansen's Superior Predictive Ability (SPA) test studentizes the performance differences and uses a sample-dependent recentering that effectively removes the hopeless models from the null distribution, restoring power while keeping the size correct (Hansen 2005). In practice SPA is the better-behaved of the two whenever the candidate set is large and heterogeneous, which is the usual case.

### 5.3 When the full machinery earns its cost

The bootstrap tests deliver something the DSR and PBO do not: a single, formally justified, data-snooping-adjusted p-value for the joint claim "the best of my set beats the benchmark," with the strategies' cross-correlation handled by resampling rather than by a moment assumption. That rigor has a price. It requires the *full time series of performance differences for every strategy in the set* — not summary statistics — and it requires choosing and tuning a bootstrap scheme (block length, number of resamples) whose assumptions about the dependence structure can themselves be wrong. The pragmatic division of labour this library adopts is therefore: use the DSR when you have a single selected Sharpe and an honest trial count and want a fast verdict; use PBO when you have the return matrix and want to audit the *selection process* rather than one strategy; and reach for the Reality Check or SPA when the deliverable is a publishable, formally-adjusted significance statement for a *fixed, fully-recorded* universe of models — a volatility-forecasting horse race (the volatility-modeling paper) is the natural home, where the set of models is small, fixed in advance, and every model's loss series is retained. For the day-to-day work of deciding whether a mined strategy is real, the DSR and PBO carry the load at a fraction of the cost, and they fail gracefully — an understated trial count or a too-wide universe shows up as a suspiciously high pass rate that a second look catches.

### 5.4 Stepwise tests and the false-discovery-rate view

Two refinements are worth naming because an advanced reader will meet them and should know where they fit. The Reality Check and the SPA test answer a single joint question — is the *best* model better than the benchmark — but often the real deliverable is to identify *which* of many models are genuinely superior while controlling the family-wise error across the whole set. Romano and Wolf (2005) extend White's bootstrap into a *stepwise* procedure: reject the clearly-superior models first, remove them from the set, and re-test the remainder, iterating until nothing more clears. This recovers power that a single-step test wastes while still controlling the probability of even one false rejection. Where family-wise control is simply too strict — as it is when screening hundreds of candidate signals, where a handful of false positives is a tolerable price for finding the real ones — the *false discovery rate* framework of Benjamini and Hochberg (1995) controls the expected *proportion* of rejected hypotheses that are false, rather than the probability of any false rejection at all, and it is the natural lens for large-scale signal mining.

The choice among all of these is a choice about which error you fear most, and it must be made before you look. The DSR and the family-wise tests protect against declaring *anything* real when nothing is — the right stance when a false positive means committing capital to noise. The FDR protects against a research *program* in which most of what you act on is spurious — the right stance when you run a portfolio of many small bets and can absorb some duds. Both are principled; the only indefensible move is to pick the criterion after seeing which one lets your favourite result through.

### 5.5 Which test, when — a decision recap

The four instruments answer four different questions, and confusing them is the most common misuse. Use the *DSR* when you hold a single selected Sharpe and an honest trial count and want a fast per-strategy verdict. Use *PBO/CSCV* when you hold the full return matrix and want to audit whether your *selection procedure* has any out-of-sample skill, independent of which strategy it happened to pick. Reach for the *Reality Check or SPA* when the deliverable is a formally-adjusted significance statement for a fixed, fully-recorded universe of models. And reach for *stepwise or FDR control* when you must decide *which several* of many candidates to keep. The first two are the day-to-day workhorses of this library; the last two are the heavy machinery a horse-race study rolls out when a publishable p-value is the point.

## 6 Forecast calibration

Everything so far concerns *strategy selection* — deciding whether a backtested edge is real. This section concerns *forecast quality* — deciding whether the probabilistic judgments a researcher makes, day after day, are any good. The two are the same discipline wearing different clothes: a forecast, like a backtest, is worthless unless it was committed to in advance and can be scored against what actually happened, and the ways it fools you are the calibration analogues of the selection biases above.

### 6.1 A forecast is a first-class object: one direction, one falsifier

Treat a forecast as a structured object with four fields, not a mood: a *direction* (what will happen, with a sign), a *probability* (how sure, as a number like p = 0.55, never "medium-high"), a *horizon* (by when), and a *falsifier* (the single observation that would prove it wrong). The discipline that makes the object scoreable is that the primary forecast commits to *exactly one direction and exactly one falsifier*. This sounds like a stylistic preference; it is a mathematical necessity, and the reason is the calibration analogue of the two-sided-test warning from the backtesting paper.

Consider a "forecast" that hedges both ways: *"the market will grind higher, unless it breaks support, in which case it falls."* This cannot be wrong. Whatever happens, some clause of it was right, so it is recorded as confirmed, and a forecaster who speaks this way accumulates a hit rate near 100% while having said nothing. In a real research log this is not hypothetical — it is the single most common way a forecast record silently destroys its own value. A private prediction log maintained behind this library carried exactly this defect: multi-branch forecasts whose branches together covered every outcome were each scored as a single confirmed call, and the branch probabilities leaked into the calibration measurement as false confidence. When the scoring was corrected so that *each branch is a separate forecast with its own probability and its own falsifier* — and the tail branches no longer counted as confidence in the primary direction — the log's Brier score improved from **0.287 to 0.223** (private data, not redistributed). The improvement was not a change in forecasting skill; it was the removal of a measurement artifact that had been flattering the forecaster. A branching forecast, in short, scores as *several* forecasts, and if you are not willing to write down and score each branch separately, you do not have a forecast — you have an alibi.

### 6.2 The Brier score and why it is proper

The Brier score (1950) is the mean squared error of a probabilistic forecast of a binary event:

  BS = (1/N) · Σᵢ (fᵢ − yᵢ)²,

where fᵢ ∈ [0, 1] is the forecast probability and yᵢ ∈ {0, 1} the outcome. It ranges from 0 (perfect) to 1 (perfectly wrong); a forecaster who always says 0.5 scores 0.25, and the unconditional base rate p̄ scores p̄(1 − p̄). The reason to use it rather than a hit rate is that the Brier score is a *strictly proper scoring rule* (Gneiting & Raftery 2007): its expectation is minimized, uniquely, by reporting your *true* believed probability. A hit rate is not proper — it rewards you for rounding every forecast to 0 or 1, i.e. for overconfidence — which is exactly why a forecaster optimizing for "how often was I right" drifts toward unfalsifiable certainty, while a forecaster optimizing for Brier is paid to be honestly uncertain. This property is the whole reason probabilistic forecasts, rather than binary calls, are the first-class object.

### 6.3 The Murphy decomposition: calibration, resolution, uncertainty

A single Brier number says how good a forecaster is; Murphy's (1973) decomposition says *why*. Partitioning the forecasts into groups by their distinct values and writing p̄ for the overall base rate, n_k for the count in group *k*, f_k for the forecast value there and ō_k for the realized frequency in that group,

  BS = REL − RES + UNC, where

  REL = (1/N) Σ_k n_k (f_k − ō_k)²  (reliability, a.k.a. calibration error),
  RES = (1/N) Σ_k n_k (ō_k − p̄)²   (resolution),
  UNC = p̄(1 − p̄)                   (uncertainty).

*Reliability* measures how far, within each forecast bin, the realized frequency departs from the forecast probability — this is calibration error, and lower is better (zero is perfect). *Resolution* measures how far the bin frequencies spread away from the base rate — how much the forecasts actually *separate* outcomes — and higher is better, so it enters with a minus sign. *Uncertainty* is the irreducible base-rate variance: an event that happens half the time is intrinsically harder to forecast than one that happens 5% of the time, and no forecaster can reduce UNC. The decomposition is exact when computed over distinct forecast values, and it is the honest way to read a Brier score, because two forecasters with the same Brier can be good for opposite reasons.

Figure 4 shows this on two synthetic forecasters facing the same 800 binary events. Forecaster A is calibrated (its forecasts equal the true probabilities plus small noise); forecaster B sees the same information but is *overconfident*, doubling the log-odds before reporting — pushing 0.65 out toward 0.78 and 0.35 down toward 0.22. On the reliability diagram, A tracks the diagonal and B bends away from it, over-stating both tails. The scores make the mechanism precise: A scores a Brier of **0.215 = REL 0.006 − RES 0.041 + UNC 0.250**, while B scores **0.233 = REL 0.025 − RES 0.041 + UNC 0.250**. The instructive detail is that B's *resolution is identical* to A's — 0.041 in both — because doubling the log-odds is a strictly monotone relabeling of the forecasts, and resolution depends only on how the outcomes are partitioned, not on the probability labels attached to them, so it cannot move. B's entire Brier penalty is therefore *reliability* (0.025 vs 0.006): overconfidence is not apparent sharpness bought at a price paid elsewhere, it is a pure transfer of score into miscalibration, and the decomposition catches it in the act.

![Reliability diagram and Murphy decomposition for a calibrated and an overconfident forecaster on 800 shared binary events (true probabilities in {0.2, 0.35, 0.5, 0.65, 0.8}). The calibrated forecaster A tracks the diagonal; the overconfident forecaster B, which doubles the log-odds, bends off it and over-states both tails. Marker area is proportional to the number of forecasts at each value; hollow markers are cells with fewer than 15 observations (anecdotes, off the line). A scores Brier 0.215, B scores 0.233; B's resolution is identical to A's — a strictly monotone relabeling cannot change it — so its entire penalty is reliability. Reproduce with figures/fig_reliability.py.](figures/fig_reliability.png)

The implementation is the same brier_murphy routine used to generate the figure, and it appears in the reusable library of Section 9.

### 6.4 The circular-evaluation trap: only out-of-sample calibration counts

There is a calibration analogue of the Section 2 selection bias, and it is at least as dangerous because it disguises itself as evidence of skill. Suppose you discover a set of recurring patterns by looking through your own history, then score how often those patterns "worked" on the *same* history. The hit rate will be excellent — near 90 or 100% — for the same reason the best of 100 backtests looks excellent: the patterns were *defined* on that data, so measuring them there is circular. This is the calibration version of HARKing, and the fix is procedural and strict.

First, every forecast is tagged as either *ex-ante* (recorded before the event) or *reconstructed* (written up afterward), and reconstructed forecasts are *quarantined* — they may illustrate a pattern but they never enter the calibration measurement, because a forecast written after the outcome is look-ahead-contaminated by construction. Second, a *discovery freeze* date separates the in-sample period, during which patterns were defined, from the out-of-sample period, during which they are tested: only forecasts made after the freeze count toward a pattern's track record, and in-sample hit rates are labelled *in-sample* everywhere they appear, never quoted as skill. Third — and this is the finding that humbles every young forecast log — until you have accumulated a meaningful number of *refuted* forecasts, no hit rate is trustworthy: a log with three refutations out of thirty-one decided forecasts has a base rate near 90%, and against a 90% base rate *every pattern looks perfect* because there is almost nothing for it to discriminate. The scarce and precious data point is the honest miss. A calibration log's maturity is measured not by how often it was right but by how many times it has been *allowed to be wrong*, and a log that has never logged a refutation has not been measured at all — it has been admired.

### 6.5 A by-hand Murphy decomposition

The decomposition is easier to trust once you have computed it on numbers small enough to check. Suppose a forecaster made twenty forecasts using just two distinct values. On ten occasions they said 0.8 and the event happened seven times; on ten occasions they said 0.4 and the event happened five times. The overall base rate is p̄ = (7 + 5)/20 = 0.6, so uncertainty is UNC = 0.6·0.4 = 0.240. Reliability weights each bin's squared calibration gap: the 0.8 bin realized 0.7, contributing (10/20)·(0.8 − 0.7)² = 0.005; the 0.4 bin realized 0.5, contributing (10/20)·(0.4 − 0.5)² = 0.005; so REL = 0.010. Resolution weights each bin's squared distance from the base rate: (10/20)·(0.7 − 0.6)² + (10/20)·(0.5 − 0.6)² = 0.005 + 0.005 = 0.010, so RES = 0.010. The decomposition predicts a Brier of REL − RES + UNC = 0.010 − 0.010 + 0.240 = 0.240. Computing the raw Brier directly — the mean of (f − y)² over the twenty forecasts — gives the same 0.240, as the identity guarantees. This forecaster is well-calibrated (tiny REL) but has almost no resolution (tiny RES): their forecasts barely separate outcomes from the base rate, so despite being honest they are only marginally more useful than a forecaster who always says 0.6. That is precisely the diagnosis a single Brier number would hide and the decomposition makes plain.

### 6.6 The logarithmic score, sharpness, and why we still default to Brier

The Brier score is not the only proper scoring rule. The *logarithmic score*, −ln f evaluated at the realized outcome (equivalently the negative log-likelihood), is also strictly proper and is the natural choice when the tails matter, because it punishes a confident wrong call far more harshly than the Brier score does: assigning probability 0.01 to something that then happens costs 4.6 under the log score but only ≈ 0.98 under Brier (Gneiting & Raftery 2007). That severity is a feature when a single overconfident miss *should* dominate the evaluation and a liability when one unavoidable surprise should not sink an otherwise-good forecaster; the log score is also undefined at f = 0, so it forbids the certainty the Brier score merely discourages. This library defaults to the Brier score for its bounded, interpretable range and its clean Murphy decomposition, and reaches for the log score only when tail-sensitivity is the explicit goal.

Both scores share the concept the calibration/resolution split already introduced: *sharpness*. Subject to being calibrated, a forecaster should make forecasts as far from the base rate as the evidence allows — this is the resolution term of Section 6.3 seen from the other side. The maxim, due to Gneiting and colleagues, is to *maximize sharpness subject to calibration*: be as bold as the evidence permits while staying honest about your uncertainty. A forecaster who only ever recites the base rate is perfectly calibrated and perfectly useless, and one who is bold but miscalibrated pays for the boldness in reliability, as forecaster B did in Figure 4. Skill lives in the narrow band where confidence and honesty coincide, and the Brier score, decomposed, is the instrument that shows whether a forecaster is standing in it.

## 7 Base rates under non-stationarity

The forecast scoring of Section 6 assumes there is a stable thing to forecast. There often is not. Markets change regime, and a conditional probability table estimated over one regime can be actively misleading in the next. This section treats the base-rate table as a living object that must be updated as regimes drift, and it imposes the one discipline that prevents a thin table from lying: a minimum cell size, backed by the arithmetic of a small-sample proportion.

### 7.1 The base rate itself drifts

Before conditioning on anything, look at the unconditional base rate and watch it move. Figure 5 takes every daily close of the S&P 500 from a public data feed — nearly a century, 24,794 return days — and computes the frequency of an up day, with one and only one pre-committed conditioning: the calendar decade. No alternative windows, no alternative instruments, no threshold search — exactly one cut, chosen in advance, because a figure warning about data-snooping that snooped its own conditioning would be self-refuting.

![The unconditional base rate drifts across decades: S&P 500 up-day frequency by calendar decade, from a public daily feed (1927-2026, 24,794 return days). Each point is P(close up on the day) with a 95% Wilson confidence interval; ochre marks partial decades; the dashed line is the full-sample rate of 0.524. The 1930s sit below 0.50 while the 2010s reach 0.549 - a drift of several points across regimes, on the unconditional rate before any conditioning is added. Reproduce with figures/fig_baserate_drift.py.](figures/fig_baserate_drift.png)

The full-sample up-day frequency is 0.524. But the decades do not agree: the 1930s sit at 0.484 — below a coin flip, the fingerprint of the Depression bear market — while the 1950s (0.542), 2010s (0.549), and 2020s-so-far (0.542) run several points higher, and the 1970s (0.506) sit near neutral. These differences are not all statistically distinguishable — the Wilson intervals overlap substantially, and that overlap is itself the point: even with two-and-a-half-thousand observations per decade, the *unconditional* base rate is estimated only to within a point or two, and it genuinely moves across regimes. If the unconditional rate drifts this much on a century of data, a *conditional* cell — P(up | some regime flag) estimated on a few dozen observations — is on far thinner ice than its point estimate suggests.

### 7.2 Recency windows versus full history: an honest bias/variance trade

The drift forces a choice with no free lunch. Estimate the base rate on the *full history* and you get low variance (many observations) but high bias if the current regime differs from the historical average — you are answering a question about a world that no longer exists. Estimate it on a *recent window* and you get low bias (the estimate reflects the current regime) but high variance (few observations, a wide interval). This is the bias/variance trade-off stated in its most concrete form, and the honest way to present it is to *show both*: report the full-history rate and a recency-window rate side by side, and let the reader see when they disagree. When they disagree materially, the recency rate is the better guide to the next observation and the full-history rate is the better guide to the long-run average, and pretending one number serves both purposes is the error. A global sample of a hundred observations is not automatically a single regime, and the moment a regime break is visible, the recency window earns its higher variance by shedding the stale bias. There is no threshold that is correct in general; there is only the discipline of showing both and naming which regime each answers for.

### 7.3 The minimum-cell-size rule and its arithmetic

The hardest discipline is also the simplest to state: *a cell with fewer than fifteen observations makes no claim.* The justification is the standard error of a proportion. For a cell with *k* successes in *n* trials, the estimated proportion is p̂ = k/n and its standard error is

  SE(p̂) = √( p̂(1 − p̂) / n ).

At the worst case p̂ = 0.5, this is √(0.25/n), and the table below shows why fifteen is roughly where a conditional cell stops being an anecdote:

| n | SE at p̂ = 0.5 | 95% CI half-width (≈ 1.96·SE) | 95% CI at p̂ = 0.5 |
|---|---|---|---|
| 5 | 0.224 | 0.438 | [0.06, 0.94] |
| 10 | 0.158 | 0.310 | [0.19, 0.81] |
| 15 | 0.129 | 0.253 | [0.25, 0.75] |
| 30 | 0.091 | 0.179 | [0.32, 0.68] |
| 100 | 0.050 | 0.098 | [0.40, 0.60] |

At *n* = 10 a cell showing "70% up" has a confidence interval running from below 40% to above 90% — it is consistent with everything from a slight edge against to a strong edge for, and it can support no directional claim. Even at *n* = 15 the interval spans a quarter of the probability axis in each direction. Only by *n* = 30 does the interval narrow to something a decision could rest on, and even then loosely. For proportions near 0 or 1 the Wilson interval (used in Figure 5) is preferable to this normal approximation because it does not spill past the [0, 1] boundary, but the lesson is unchanged: *small cells are noise, and the honest response to a thin cell is silence, not a confidently-quoted percentage.* In practice this becomes a hard gate — n < 15 in a conditional cell means the cell is marked as an anecdote and no claim is drawn from it — and a corollary that the backtesting paper's expectancy discussion anticipated: a conditional read is only worth stating if it beats the unconditional base rate by more than its own confidence interval. A pattern that "hits 90%" when the unconditional rate is already 90% is the base rate wearing an expensive costume, and the lift, not the level, is the quantity that has to clear the bar.

### 7.4 Shrinkage: the principled version of the cell-size gate

The n < 15 rule is a blunt instrument, and it is worth knowing the smooth version it approximates, because the smooth version explains *why* fifteen is roughly the right number. A hard cutoff says a thin cell contributes nothing and a fat cell contributes its raw rate; a *shrinkage* estimator says every cell contributes, but a thin one is pulled hard toward the unconditional base rate and a fat one is trusted on its own. The Bayesian form is a Beta-Binomial: with a prior centred on the base rate p̄ and a prior strength of κ pseudo-observations, a cell of *k* successes in *n* trials is estimated not as k/n but as

  p̂_shrunk = (k + κ·p̄) / (n + κ).

For a cell with two successes in three trials and a base rate of 0.5, a raw estimate screams 0.67; with κ = 15 pseudo-observations the shrunk estimate is (2 + 7.5)/(3 + 15) ≈ 0.53 — barely distinguishable from the base rate, which is the correct humility for three observations. As *n* grows past κ the data dominate and the shrinkage fades, so a cell with a hundred observations is trusted almost fully. The hard n < 15 rule is what you get when you set κ ≈ 15 and then round the smooth curve to a step: below about fifteen observations, the prior still owns most of the estimate, so quoting the raw rate is quoting mostly the prior while pretending it is data. Shrinkage is the honest generalisation, and it has the pleasant side effect of never producing a cell that says 0% or 100% off a handful of trials — the estimate that most reliably destroys a forecaster's calibration. Where a table feeds a model rather than a human eyeball, prefer the shrunk estimate to the hard gate; where it feeds judgment, the hard gate is the memorable shadow of the same idea.

## 8 An honest research protocol, assembled

The instruments of the preceding sections are components; this section assembles them into a single loop that a working researcher can run, and states the status-upgrade rules that keep the loop's outputs meaning what they say. The protocol generalizes and anonymizes a workflow this library's private research process runs in practice; nothing here depends on the private data, only on its shape.

### 8.1 The loop

The research loop has five stages, and they run in a strict order because each stage exists to remove a degree of freedom that the next stage would otherwise abuse.

1. **Pre-register.** Before any out-of-sample data is examined, write and version-control the full specification from the backtesting paper: the one confirmatory hypothesis with a directional H₁ and a null H₀, the point effect size and the smallest effect worth acting on, the fixed in-sample/out-of-sample split by *date* (not fraction), the single primary metric, the decision rule as an explicit inequality including a *direction check*, and — the field this paper adds — the number of variants to be tried and the multiple-testing correction that number requires (DSR, PBO, or a bootstrap test). Freeze it with a timestamp and a commit hash.
2. **Test.** Run the design on the in-sample data. Select, tune, and explore here to your heart's content — this is where the researcher degrees of freedom are *allowed*, because the out-of-sample set is untouched. Record every variant you try; the honest trial count is the *N* that Section 3 and Section 4 will hold you to.
3. **Log, append-only.** Write the result to a log that can only be appended to, never edited. If the study is a forecast, the log entry carries the one direction, one probability (p = 0.NN), one horizon, and one falsifier of Section 6, plus the trade plan (entry, invalidation, target) and the realized R-multiple so that *expectancy*, not just directional correctness, is scored. Reconstructed entries are tagged and quarantined.
4. **Falsification check.** Open the out-of-sample set once. Ask the pre-registered question and only that question. Run the direction check: does the *sign* of the out-of-sample data match H₁? A significant result with the wrong sign is a falsification, not a weak confirmation. Run the applicable multiple-testing correction on the honest *N*. Record the verdict — supported, refuted, or undecided — against the frozen decision rule, without renegotiating the rule.
5. **Status upgrade (or not).** Apply the rules of Section 8.2. Then, whatever the verdict, cross-verify it against the existing body of results: does it *support*, *contradict*, *duplicate*, or *extend* what is already recorded? A contradiction flags *both* the new result and the old one for review rather than silently overwriting either.

### 8.2 Status-upgrade rules

The loop is only as honest as the words it is allowed to use, so the status labels are defined precisely and the upgrade rules are strict.

- **formulated** — the hypothesis is stated testably and has external support (a citation, a mechanism, a vendor claim) *or* an in-sample result. This is the ceiling for anything not yet tested on your own out-of-sample data. An external source, *however authoritative*, maxes out here: a peer-reviewed paper reports its winner, not the search behind it (Section 2.3), so it can make a claim plausible but never confirmed.
- **supported** — the hypothesis has survived a pre-registered out-of-sample test on *your own* data, the direction check passed, and the multiple-testing correction was applied and cleared. "Supported" requires linked, own, out-of-sample evidence; it is the only status that earns the word *validated*, and it is never awarded on the strength of a citation or an in-sample number.
- **refuted** — the out-of-sample test failed the decision rule, or the direction check caught a sign inversion. Refutations are the scarce, valuable data (Section 6.4) and are logged with the same care as confirmations.
- **needs-review** — a contradiction surfaced against an existing result. This is a flag, not a verdict; resolving it is a human decision backed by a fresh result, never an automatic downgrade.

The single rule underneath all four is the one the backtesting paper opened with and this paper has quantified throughout: *an external result makes a claim plausible; only your own out-of-sample test makes it supported.* The DSR, PBO, and calibration tools exist precisely to keep the word "supported" expensive.

### 8.3 A directory template

The loop maps onto a directory the reader can copy, one folder per study:

```text
study-<id>-<short-name>/
  00-prereg.md          # frozen spec: H0/H1, effect size, split dates,
                        #   metric, decision rule + direction check,
                        #   N variants planned + correction. Commit-hashed.
  01-data/              # cached inputs (free data) + a manifest with source & date
  02-insample.ipynb     # design, selection, exploration; logs every variant tried
  03-oos-result.md      # append-only: the one OOS run, the verdict, the DSR/PBO/Brier
  04-log.md             # append-only forecast/trade log (direction, p, horizon,
                        #   falsifier, plan E/Inv/Target, realized R)
  05-crosscheck.md      # supports / contradicts / duplicates / extends the corpus
  validation.py         # the Section 9 library, imported by 02 and 03
```

The point of the layout is that the frozen specification (`00-prereg.md`) is written first and touched last, the in-sample notebook is where freedom lives, and the out-of-sample result and the log are append-only by construction. A study that cannot produce a `00-prereg.md` with an earlier commit timestamp than its `03-oos-result.md` has not been pre-registered, and the directory makes that failure visible at a glance.

### 8.4 A worked pre-registration for a calibration study

The backtesting paper gave a pre-registration template for a *backtest*; the forecast-scoring apparatus of Section 6 needs its own, because the object under test is a stream of probabilistic forecasts rather than a single Sharpe. The shape below is what a frozen specification looks like when the deliverable is calibration rather than an edge — it commits, before any forecast is scored, to the metric, the in-sample/out-of-sample freeze, and the exact rule that separates a genuine improvement from a measurement artifact.

```markdown
# Pre-registration — forecast-calibration study <id>

## Object under test
- A stream of ex-ante probabilistic forecasts, each: one direction, one
  probability p=0.NN, one horizon, one falsifier. Branching forecasts are
  split into separate scored forecasts (each branch its own p and falsifier).

## Confirmatory hypothesis (exactly one)
- H1: the forecaster is calibrated OUT-OF-SAMPLE, i.e. reliability (Murphy)
      is below <threshold> on forecasts made after the freeze date.
- H0: out-of-sample reliability is no better than a base-rate-only forecaster.

## Metric & decomposition
- Primary: Brier score. Reported: Murphy REL / RES / UNC. Secondary: expectancy
  (mean realized R) so directional correctness is not mistaken for edge.

## In-sample / out-of-sample freeze (fixed dates)
- Discovery/in-sample (patterns defined here): forecasts <= <freeze date>.
- Out-of-sample (the only calibration that counts): forecasts >= <freeze date>.
- Reconstructed (post-hoc) forecasts: quarantined, never scored.

## Decision rule
- Claim "calibrated" iff OOS reliability < <threshold> AND the log has
  >= <min> refuted forecasts (so the base rate is discriminable) AND
  the direction check passed on each scored forecast.

## Minimum-evidence gate
- No per-pattern hit rate quoted from a cell with n < 15 (see Section 7).

## Frozen on
- Date: <YYYY-MM-DD> · Commit: <hash>
```

The two fields that do the work are the *freeze date* and the *minimum-refutation gate*. The freeze date is the calibration analogue of the backtesting paper's out-of-sample split: forecasts before it defined the patterns and are labelled in-sample everywhere, forecasts after it are the only ones that count toward the calibration claim. The refutation gate encodes the Section 6.4 finding directly — a log with too few misses cannot discriminate against a high base rate, so a calibration claim from such a log is refused by construction rather than by after-the-fact judgment. Freezing both before scoring is what keeps "well-calibrated" from becoming the calibration equivalent of a best-of-100 Sharpe.

## 9 The validation suite as reusable code

The instruments of this paper are small enough to live in one module, and the payoff of collecting them is that the *other* empirical documents in this library — the dealer-flows-and-GEX paper and the volatility-modeling paper — do not re-implement governance; they import it. This section gives the consolidated module and shows the two wiring points.

### 9.1 One module

The listing below is the whole suite: the DSR stack from Section 3, the PBO/CSCV routine from Section 4, and the Brier/Murphy decomposition from Section 6, with a thin convenience wrapper that reports a verdict. It has no dependencies beyond NumPy and the standard library, and every function in it was used to generate a figure in this paper, so it is tested by construction.
```python
"""validation.py - the Trading Library governance suite (DSR, PBO, Brier).
No dependency beyond numpy + stdlib. Every routine is used to produce a
figure in this paper; the figure scripts are the regression tests."""
import math, itertools
import numpy as np

EULER = 0.5772156649015329

# ---- normal helpers -------------------------------------------------------
def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def norm_ppf(p):
    a = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00)
    if p < 0.02425:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > 1 - 0.02425:
        return -norm_ppf(1 - p)
    q = p - 0.5; r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

# ---- Deflated Sharpe Ratio (Bailey & Lopez de Prado 2012, 2014) -----------
def psr(sr, sr_star, n, skew, kurt, rho=0.0):
    n_eff = n * (1.0 - rho) / (1.0 + rho) if rho else n   # Lo (2002) AR(1) effective-sample deflation
    den = math.sqrt(max(1e-12, 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr ** 2))
    return norm_cdf((sr - sr_star) * math.sqrt(n_eff - 1.0) / den)

def expected_max_sr(n_trials, var_trials):
    return math.sqrt(var_trials) * ((1 - EULER) * norm_ppf(1 - 1.0 / n_trials)
                                    + EULER * norm_ppf(1 - 1.0 / (n_trials * math.e)))

def deflated_sharpe(sr, n, skew, kurt, n_trials, var_trials, rho=0.0):
    """DSR verdict for a per-period Sharpe `sr` selected as best of `n_trials`.
    `var_trials` is the variance of the Sharpe estimates ACROSS the trials.
    `rho` forwards the Lo (2002) AR(1) correction to psr so the DSR is also
    deflated for serial dependence (rho=0 -> iid); skipping it under
    autocorrelation makes the gate look more precise than it is."""
    return psr(sr, expected_max_sr(n_trials, var_trials), n, skew, kurt, rho)

# ---- Probability of Backtest Overfitting via CSCV (Bailey et al. 2017) ----
def pbo_cscv(returns, s_blocks=16):
    t, n = returns.shape
    b = t // s_blocks
    r = returns[:b * s_blocks].reshape(s_blocks, b, n)
    bs, bq = r.sum(axis=1), (r ** 2).sum(axis=1)
    half = s_blocks // 2; m = half * b
    tot_s, tot_q = bs.sum(axis=0), bq.sum(axis=0)
    logits = []
    for combo in itertools.combinations(range(s_blocks), half):
        idx = list(combo)
        s1, q1 = bs[idx].sum(axis=0), bq[idx].sum(axis=0)
        s2, q2 = tot_s - s1, tot_q - q1
        mean1, mean2 = s1 / m, s2 / m
        v1 = (q1 - m * mean1 ** 2) / (m - 1); v2 = (q2 - m * mean2 ** 2) / (m - 1)
        sr1, sr2 = mean1 / np.sqrt(v1), mean2 / np.sqrt(v2)
        j = int(np.argmax(sr1))
        rank = int((sr2 < sr2[j]).sum()) + 1
        w = rank / (n + 1.0)
        logits.append(math.log(w / (1.0 - w)))
    logits = np.array(logits)
    return float((logits <= 0).mean()), logits

# ---- Brier score + exact Murphy decomposition (Brier 1950; Murphy 1973) ---
def brier_murphy(f, y):
    """Returns (brier, reliability, resolution, uncertainty); brier = rel - res + unc."""
    f, y = np.asarray(f, float), np.asarray(y, float)
    brier = float(np.mean((f - y) ** 2))
    ybar = float(y.mean()); rel = res = 0.0
    for v in np.unique(f):
        mask = f == v
        nk, ok = int(mask.sum()), float(y[mask].mean())
        rel += nk / len(f) * (v - ok) ** 2
        res += nk / len(f) * (ok - ybar) ** 2
    return brier, rel, res, ybar * (1 - ybar)
```

### 9.2 How the dealer-flows-and-GEX and volatility-modeling papers wire in

The two flagship empirical documents call the suite at exactly the two governance moments this paper identified.

The dealer-flows-and-GEX paper translates each dealer-hedging claim — a gamma or charm or vanna regime that is supposed to move the underlying — into a pre-registered, falsifiable hypothesis, and it screens many candidate gate definitions against a free-data reconstruction of the option-implied regime. That screening is a selection, so before any gate is reported, it runs `pbo_cscv` on the return matrix of its candidate gates to audit whether its *selection process* has out-of-sample skill at all, and it runs `deflated_sharpe` on the single selected gate with the honest count of variants it tried. A gate that clears PBO below the threshold *and* a DSR of 0.95 earns a pre-registered out-of-sample test; a gate that does not is reported as a candidate hypothesis, not a result — which is precisely the discipline that the backtesting paper's VIX-gate case study, run before this suite existed, was missing.

The volatility-modeling paper is a forecasting horse race — competing models (HAR, its log variant, a random walk benchmark) producing one-day-ahead volatility forecasts — and it uses the suite at both the strategy and the forecast layer. At the strategy layer, because its model set is small, fixed in advance, and fully recorded, it is the natural home for the bootstrap Reality Check / SPA machinery of Section 5, with the DSR as a fast pre-check. At the forecast layer, every model's probabilistic outputs are scored with `brier_murphy`, and the Murphy decomposition is reported so that a model which wins on resolution but loses on reliability is caught rather than crowned. The two studies thereby share one governance codebase and one vocabulary, and the library becomes a single research *program* rather than a shelf of unrelated results — which was the point of writing the suite down once.

### 9.3 Honest limits of the suite

The suite is deliberately small, and its limits are worth stating plainly so no one mistakes a green light for a guarantee. The DSR assumes the trial Sharpes are approximately Gaussian and that V[SR] estimated from the trials captures their dependence; when the trials are few or wildly non-normal, the expected-maximum formula is an approximation and the DSR should be read as an order-of-magnitude verdict, not a fourth decimal place. PBO's block cross-validation assumes the block length is long enough to preserve the return series' autocorrelation but short enough to give enough blocks; with strong long-memory dependence the block count and length become judgment calls that change the answer. The Brier decomposition is exact only over distinct forecast values, and with few forecasts and small bins its resolution term overfits toward the uncertainty term — the same small-*n* fragility Section 7 warned about, now inside the scoring rule itself. None of these caveats is a reason to skip the tools; they are the reason to run all three, read them together, and treat any single suspiciously clean pass with the same distrust Section 2 taught for a single suspiciously good backtest. The governance suite is a smoke detector, not a fire marshal: it reliably catches the obvious disasters and it makes the process auditable, but it does not absolve the researcher of the pre-registration and out-of-sample discipline that remains, in the end, the only real defense.

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| The best-of-N Sharpe under pure noise, full sampling distribution: best of 100 on one year of data has expected Sharpe ≈2.5; on five years, best of 1,000 ≈1.45 | Own reproducible computation — `figures/fig_sharpe_noise_dist.py` |
| The higher-moment standard error of the Sharpe estimate and the Probabilistic Sharpe Ratio | Literature — (Bailey & López de Prado 2012; Mertens 2002) |
| The Deflated Sharpe Ratio and its expected-maximum-Sharpe benchmark | Literature — (Bailey & López de Prado 2014) |
| DSR worked example: a best-of-20 zero-edge winner reads naive PSR 0.925 but DSR 0.400, and would need an annualized Sharpe of 1.69 to clear DSR 0.95 | Own reproducible computation — `figures/fig_dsr_worked.py` |
| The combinatorially symmetric cross-validation construction of the Probability of Backtest Overfitting | Literature — (Bailey et al. 2017) |
| PBO on simulated batteries: pure noise 0.52, a genuine Sharpe-1.0 edge 0.46 (unfindable among noise), a Sharpe-2.0 edge 0.01 | Own reproducible computation — `figures/fig_pbo_cscv.py`; OOS split |
| The bootstrap data-snooping tests (Reality Check, SPA, stepwise control, FDR) and the stationary bootstrap | Literature — (White 2000; Hansen 2005; Romano & Wolf 2005; Benjamini & Hochberg 1995; Politis & Romano 1994) |
| The Brier score is strictly proper and decomposes (Murphy) into reliability, resolution, and uncertainty | Literature — (Brier 1950; Murphy 1973; Gneiting & Raftery 2007) |
| Reliability diagram: overconfidence is a monotone relabeling, so it leaves resolution unchanged (0.041 for both) and pays its entire penalty in reliability (Brier 0.215 vs 0.233) | Own reproducible computation — `figures/fig_reliability.py` |
| The unconditional S&P 500 up-day base rate drifts across decades, from 0.484 in the 1930s to 0.549 in the 2010s (full sample 0.524) | Own reproducible computation — `figures/fig_baserate_drift.py` |
| Correcting a private forecast log's branching forecasts to one-falsifier scoring improved its Brier from 0.287 to 0.223 | Practitioner consensus — not independently verified |
| The VIX-gate case study held at a gross profit factor of 1.62 on data its threshold never saw | Practitioner consensus — not independently verified; OOS split |

## References

- Bailey, D. H., & López de Prado, M. (2012). The Sharpe ratio efficient frontier. *Journal of Risk, 15*(2), 3–44. Introduces the Probabilistic Sharpe Ratio and the higher-moment standard error of the Sharpe estimate; the foundation deflated in Section 3.
- Bailey, D. H., & López de Prado, M. (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting, and non-normality. *Journal of Portfolio Management, 40*(5), 94–107. The DSR itself, including the expected-maximum-Sharpe benchmark used throughout Section 3.
- Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2014). Pseudo-mathematics and financial charlatanism: The effects of backtest overfitting on out-of-sample performance. *Notices of the American Mathematical Society, 61*(5), 458–471. The accessible companion to the PBO paper and the source of the √(2 ln N) selection argument of Section 2. Open access: <https://www.ams.org/notices/201405/rnoti-p458.pdf>.
- Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2017). The probability of backtest overfitting. *Journal of Computational Finance, 20*(4), 39–69. The formal CSCV construction implemented in Section 4.
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: A practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society, Series B, 57*(1), 289–300. The FDR framework surveyed in Section 5.4 for large-scale signal screening.
- Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. *Monthly Weather Review, 78*(1), 1–3. The original quadratic scoring rule of Section 6; freely available through the American Meteorological Society journals archive.
- Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association, 102*(477), 359–378. Establishes propriety — why the Brier score rewards honest probabilities and a hit rate does not (Section 6.2).
- Hansen, P. R. (2005). A test for superior predictive ability. *Journal of Business & Economic Statistics, 23*(4), 365–380. The SPA test of Section 5, repairing the conservativeness of White's Reality Check.
- Lo, A. W. (2002). The statistics of Sharpe ratios. *Financial Analysts Journal, 58*(4), 36–52. The autocorrelation correction to the Sharpe standard error cited in Section 3.1.
- Mertens, E. (2002). *Comments on variance of the IID estimator in Lo (2002).* Working paper. Gives the higher-moment standard error of the Sharpe estimate used in the PSR of Section 3.1.
- Murphy, A. H. (1973). A new vector partition of the probability score. *Journal of Applied Meteorology, 12*(4), 595–600. The reliability–resolution–uncertainty decomposition of Section 6.3; freely available through the American Meteorological Society journals archive.
- Politis, D. N., & Romano, J. P. (1994). The stationary bootstrap. *Journal of the American Statistical Association, 89*(428), 1303–1313. The resampling scheme that preserves autocorrelation in the bootstrap tests of Section 5.
- Romano, J. P., & Wolf, M. (2005). Stepwise multiple testing as formalized data snooping. *Econometrica, 73*(4), 1237–1282. The stepwise extension of White's Reality Check discussed in Section 5.4.
- White, H. (2000). A reality check for data snooping. *Econometrica, 68*(5), 1097–1126. The joint bootstrap test for the best of a set of models, surveyed in Section 5.1.
*All references above are publicly accessible: the AMS Notices survey is open-access with a direct link, the Brier and Murphy papers are freely available through the American Meteorological Society journals archive, and the remainder are peer-reviewed journal articles available through standard academic channels. No proprietary, course, or trading-academy material is cited. The anonymized calibration figures drawn from a private research log (Section 6.1) are reported as numbers only; the underlying data is not redistributed.*

