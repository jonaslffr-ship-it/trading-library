---
title: "Volatility Modeling & the Variance Risk Premium"
last_updated: 2026-09-25
---

# Volatility Modeling & the Variance Risk Premium

## Abstract

Volatility is the one quantity in finance that is central, forecastable, and never directly observed — and almost every mistake in volatility research traces back to forgetting the third fact. This paper builds the working toolkit for measuring, modeling, forecasting, and pricing volatility, with the measurement problem treated as first-class throughout. We start with the estimator zoo — close-to-close, Parkinson, Garman–Klass, Rogers–Satchell, Yang–Zhang — and the realized-variance idea that turns a latent quantity into a noisy but observable one, then confront microstructure noise and jumps. We derive the GARCH family from ARCH and fit it by our own maximum likelihood, showing what it captures (clustering, mean reversion) and what it structurally misses (long memory, jumps). We then show why the deliberately simple HAR-RV regression beats most of that machinery out of sample, and we insist on evaluating forecasts the right way: QLIKE rather than MSE, Mincer–Zarnowitz regressions, Diebold–Mariano and Clark–West tests, under one pre-committed out-of-sample protocol that we report honestly even where the primary and secondary metrics disagree. We define and measure the variance risk premium as pre-registered insurance compensation, find it economically present but statistically fragile out of sample, and close by calibrating an arbitrage-free SVI slice with explicit butterfly and calendar checks. Every number is recomputed from free data and reproducible.

## Keywords

Realized volatility, volatility estimators, Yang–Zhang, realized variance, microstructure noise, GARCH, GJR-GARCH, EGARCH, maximum likelihood, HAR-RV, long memory, volatility forecasting, QLIKE, Mincer–Zarnowitz, Diebold–Mariano, Clark–West, out-of-sample evaluation, variance risk premium, VIX, SVI, butterfly arbitrage, calendar arbitrage, local volatility

## 1 Introduction

### 1.1 Motivation and thesis

Volatility occupies a peculiar place in quantitative finance. It is the single most important state variable for anyone who trades options, sizes risk, or prices a derivative — and it is the one variable in that list that is never printed on any tape. Price is observed; return is observed; volatility must be *estimated* from returns, *modeled* to be forecast, and *inferred* from option prices to be priced. Three different objects — realized volatility (what happened), forecast volatility (what we expect), and implied volatility (what the market charges) — all wear the same word, and confusing them is the most common error in the field.

The thesis of this paper is that *the discipline of volatility research is the discipline of respecting the gap between the estimand and the estimator.* Realized volatility is not the daily squared return; it is a latent quantity that the squared return estimates badly and an intraday sum estimates better. A GARCH forecast is not the true conditional variance; it is a parametric guess whose parameters are themselves estimated with error. The VIX is not the market's forecast of realized volatility; it is a risk-neutral price that sits systematically above the physical forecast by an amount — the variance risk premium — that is itself the object of study. Every section below is, in one way or another, an argument for measuring the thing you actually mean and testing your model against a benchmark that can beat it.

Two practical corollaries organize the paper. First, *the loss function is a modeling choice, not a neutral scoreboard.* We will show empirically that mean-squared error and QLIKE rank the same three forecasting models in different orders on the same out-of-sample data, and that reporting only the metric that flatters your model is a form of data snooping in disguise. Second, *a volatility model earns the word "validated" only by beating a naive benchmark out of sample, under a rule fixed before the data could answer.* The random walk — tomorrow's variance equals today's — is a genuinely hard benchmark for volatility because volatility is persistent; a model that cannot beat it out of sample has taught us nothing, however elegant its derivation.

### 1.2 Scope, prerequisites, and intended reader

This paper sits in the Trading Library's *Volatility* track. It sits downstream of two companion papers and assumes them. From the *Volatility* track it assumes *The Volatility Surface and the VIX Complex* (referred to below as the surface paper): the implied-volatility surface, skew and term structure, the VIX/VIX3M slope, and the compact factor set — level, term slope, vol-of-vol, tail, dispersion — that we condition on in Section 7. From the *Quant Methods* track it assumes *Backtesting and Hypothesis Testing* (the pre-registration paper): confirmatory versus exploratory testing, the pre-committed out-of-sample split, effect sizes, and the direction check. It also draws on the multiple-testing companion for the vocabulary of deflated performance and selection bias. The reader is expected to be comfortable with a likelihood, an ordinary-least-squares regression, a little matrix algebra, and a short Python listing; no stochastic calculus is required, though we point to where it lives.

After reading this paper, a reader can:

- choose a realized-volatility estimator deliberately, state its bias and efficiency, and explain why the range estimators sit below close-to-close and why Yang–Zhang recovers the gap;
- derive GARCH(1,1) from ARCH, fit it by maximum likelihood, read its persistence and half-life, diagnose it, and say precisely what it cannot represent;
- write down the HAR-RV cascade, explain why a three-term OLS approximates long memory well enough to win out of sample, and extend it with a jump term and an implied-volatility regressor;
- evaluate competing forecasts with QLIKE, Mincer–Zarnowitz, Diebold–Mariano and Clark–West, under a single pre-committed protocol, and report the honest result when metrics disagree;
- define the variance risk premium in unambiguous units, pre-register a test of it, and read the result as insurance compensation with negative skew rather than as free money;
- and calibrate a raw-SVI slice by least squares, check it for butterfly and calendar arbitrage with the Gatheral–Jacquier criterion, recognize a bad fit, and move from a fitted surface to local volatility and greeks with honest error bars.

### 1.3 Data and reproducibility

Where the sign of a result matters — and in volatility work it almost always does — we run the *direction check* explicitly, stating whether the data support, contradict, duplicate, or merely extend the claim.

All data are free and cached beside the code so every figure re-renders offline: daily S&P 500 OHLC from Yahoo Finance's public chart API, VIX daily closes from FRED (VIXCLS), the VIX/VIX3M complex from Cboe's published history, and a single SPX option-chain snapshot from Cboe's public delayed-quotes feed. Two design decisions are load-bearing and stated once here. The empirical realized-volatility and forecasting work uses the fifteen-year daily cache (September 2011 onward), so the variance-risk-premium study inherits the same window and the same single out-of-sample split date (2 January 2020) as the forecasting horse race — one split, used throughout, chosen before any out-of-sample number was examined. And every empirical statement is *descriptive or pre-registered*, never the survivor of a threshold search: the paper that warns against data snooping does not get to snoop. *This is a research and educational document, not investment advice.*

### 1.4 Organization of this paper

The paper is complete; the arc is as follows. **Section 2** treats measurement: the estimator zoo with formulas and validity conditions, the annualization convention, the realized-variance idea, and the microstructure-noise and jump problems that limit it (Figure 1). **Section 3** derives the GARCH family from ARCH, fits GARCH(1,1) and GJR by own maximum likelihood, and separates what GARCH captures from what it structurally misses (Figure 2). **Section 4** presents HAR-RV as the workhorse forecaster — the daily/weekly/monthly cascade, why it wins, and its jump and implied-vol extensions. **Section 5** is the evaluation core: QLIKE versus MSE, Mincer–Zarnowitz, Diebold–Mariano and Clark–West, under one pre-committed expanding-window protocol run as a three-way horse race (Figure 3). **Section 6** defines and measures the variance risk premium, pre-registered in the text, and reads it as insurance compensation with a violent left tail (Figure 4). **Section 7** turns to term-structure carry signals — slope and roll on VIX versus VIX3M, honest transaction-cost accounting, conditioning on the surface paper's factor set, and a non-stationarity test. **Section 8** calibrates an arbitrage-free SVI slice step by step, with the butterfly and calendar checks and a failure gallery, and connects the fitted surface to local volatility and greeks (Figure 5). **Section 9** is a reproducibility appendix — the full pipeline from data to evaluation, with code listings — and **Section 10** collects the annotated references.

## 2 Measuring realized volatility properly

Before any model can be fitted or any premium measured, volatility has to be *measured*, and the measurement is harder than it looks because the estimand is latent. This section builds the estimator zoo from first principles, states each estimator's bias and efficiency, fixes the annualization convention, and then confronts the two problems — microstructure noise and jumps — that decide how far the high-frequency version can be pushed.

### 2.1 The estimand and the naive estimator

Write the log price as p_t = ln(P_t) and the daily log return as r_t = p_t − p_{t−1}. Under the standard continuous-time idealization the log price follows a diffusion,

```
dp_t = μ_t · dt + σ_t · dW_t
```

and the object we actually want is the *integrated variance* over a day — the accumulated instantaneous variance:

```
IV = ∫_{t−1}^{t} σ²_s ds          (integrated variance over one day, latent)
```

This is a random quantity that is never observed directly. Everything in this section is an estimator of that integral, and the estimators differ in how much of the day's information they use.

The naive *close-to-close* estimator uses only the two closing prices. Over a window of N days it is the sample variance of daily returns:

```
σ²_cc = ( 252 / (N − 1) ) · Σ_{t=1..N} ( r_t − r̄ )²
```

It is unbiased for the return variance under the diffusion, and it is the estimator everyone reaches for first. It is also badly *inefficient*: a single day contributes exactly one squared number, so a one-day variance estimate r_t² is an extremely noisy proxy for that day's integrated variance — it has the right expectation but enormous sampling variance, because r_t²/σ_t² is a χ²₁ variable whose standard deviation is √2 times its mean. The intuition that drives the rest of the section: the day's *high and low* contain information about how far the price travelled that the close alone throws away.

### 2.2 Annualization and the window are assumptions, not facts

Two choices are baked into every volatility number and are silently responsible for much confusion. The first is *annualization*. A daily standard deviation is scaled to annual units by the square-root-of-time rule, σ_annual = σ_daily · √252, using roughly 252 trading days per year; the reciprocal, σ_daily ≈ σ_annual / 16 (since √252 ≈ 15.9), converts an annualized VIX-style number back to an expected daily move. The rule assumes returns are serially uncorrelated: if returns trend or mean-revert intraday-to-daily, √252 over- or under-states the true annual dispersion, and the assumption should be stated rather than assumed. The second choice is the *window* N. A 21-day (one-month) estimate reacts slowly and is stable; a 5-day (one-week) estimate is jumpy and current. Neither is correct in the abstract — they estimate the average volatility over different horizons — so the honest practice is to always name the window, and, better, to read the current level as a *percentile* against a cone of historical windows rather than as an absolute number. Throughout this section we use a rolling 21-day window and √252 annualization, and we state it here so it never has to be re-litigated.

### 2.3 The range estimators

If the price is a driftless Brownian motion within the day, the range — the gap between the intraday high and low — is far more informative about σ than the open-to-close move, because a large range is hard to produce without genuine volatility while a small close-to-close move can hide a wild round trip. Parkinson (1980) turned this into an estimator. With u = ln(H/O) the high-versus-open log range component and d = ln(L/O) the low-versus-open component (both taken from the open so the arithmetic is clean), Parkinson's daily variance estimate is (Parkinson 1980):

```
σ²_P = ( u − d )² / ( 4 · ln 2 )
```

The constant 4·ln2 is the expected squared range of a standard Brownian motion; dividing by it makes the estimator unbiased for σ² under the driftless-diffusion, no-gap assumption. Parkinson's estimator uses the high and low but ignores the open and close, and it says nothing about drift.

Garman and Klass (1980) added the open and close to squeeze out more efficiency. With c = ln(C/O) the intraday (open-to-close) return, their estimator is (Garman & Klass 1980):

```
σ²_GK = ½ · ( u − d )² − ( 2·ln2 − 1 ) · c²
```

Garman–Klass is the minimum-variance analytic combination of the range and the close under the same no-drift, no-gap assumptions, and it is roughly half as noisy again as Parkinson. Its weakness is that it assumes zero drift; a strongly trending day biases it, because the range no longer reflects volatility alone. Rogers and Satchell (1991) fixed exactly that: their estimator is drift-independent, valid for a Brownian motion with any (unknown) drift, at the cost of a little efficiency (Rogers & Satchell 1991):

```
σ²_RS = u · ( u − c ) + d · ( d − c )
```

The Rogers–Satchell form is the one to reach for when the underlying trends within the day, because it does not assume the mean return is zero.

All three range estimators share one blind spot that matters enormously for real markets: they see only the trading session, from open to close, and are blind to the *overnight gap* between yesterday's close and today's open. For an equity index a large fraction of total variance arrives overnight — earnings, macro prints, and the entire non-US session all land in the gap — so a pure range estimator systematically *understates* total volatility. Yang and Zhang (2000) built the estimator that fixes this. With the overnight return o = ln(O_t / C_{t−1}), it is a weighted sum of three pieces — the variance of the overnight return, the variance of the open-to-close return, and the Rogers–Satchell intraday term — combined so the whole is unbiased, drift-independent, and minimum-variance in its class (Yang & Zhang 2000):

```
σ²_YZ = σ²_o + k · σ²_c + ( 1 − k ) · σ²_RS
k     = 0.34 / ( 1.34 + (N + 1)/(N − 1) )
```

The overnight term restores exactly the information the range estimators discard, which is why Yang–Zhang is the honest default for anything with a gap.

### 2.4 The estimator zoo on real data

Figure 1 puts all five estimators on fifteen years of S&P 500 daily OHLC and reports the two diagnostics that separate them: their *level* (mean annualized volatility over the sample) and a model-free proxy for their *efficiency*.

![Five estimators of the same latent object — close-to-close, Parkinson, Garman–Klass, Rogers–Satchell, Yang–Zhang — on Yahoo daily S&P 500 OHLC, 2011–2026 (3,770 sessions). Panel (a) shows the rolling 21-day annualized estimates from 2023 on; panel (b) shows the full-sample mean level of each. The three pure-range estimators sit well below close-to-close because they cannot see the overnight gap; Yang–Zhang, which adds the overnight term, recovers most of the difference. Reproduce with figures/fig_rv_estimators.py.](figures/fig_rv_estimators.png)

The level diagnostic is stark. Close-to-close averages 14.35% annualized over the sample. The three pure-range estimators sit far below it — Parkinson 11.29% (a ratio of 0.787 to close-to-close), Garman–Klass 10.92% (0.761), Rogers–Satchell 10.86% (0.757) — precisely because they are blind to the overnight gap, and for the S&P over this period the gap carries roughly a quarter of total variance. Yang–Zhang, which adds the overnight term back, recovers most of the shortfall at 12.54% (0.874). The direction check matters here: the range estimators are not "better" for being lower; they are *biased low as estimators of total daily variance* because they measure a different, smaller thing (session-only variance). If you want the volatility that a position actually experiences overnight to overnight, you use close-to-close or Yang–Zhang, not Parkinson.

The efficiency diagnostic is where the range estimators earn their keep. Efficiency is about *sampling variance*, not level: given the same true volatility, a more efficient estimator produces a less noisy day-by-day series. The classical theoretical efficiency gains, relative to close-to-close and under the estimators' own assumptions, are large — Parkinson about 5×, Garman–Klass about 7×, and Yang–Zhang as much as 14× in the idealized case (Parkinson 1980; Garman & Klass 1980; Yang & Zhang 2000). Because the estimand is latent we cannot verify those numbers directly, but a clean model-free proxy is available: true integrated variance is persistent day to day, so a *less noisy* single-day estimate will show *higher lag-1 autocorrelation*, while pure noise is serially uncorrelated. The measured lag-1 autocorrelations bear this out: the single-day close-to-close estimate has autocorrelation 0.444, while Parkinson reaches 0.705 and Garman–Klass 0.684 — the range estimates are visibly smoother reflections of the same underlying persistence. Rogers–Satchell sits lower at 0.559, the price it pays for drift-robustness. The practical reading: for measuring the *level* of total volatility use close-to-close or Yang–Zhang; for a *low-noise daily series* to feed a model, the range estimators are materially better, and Yang–Zhang is the estimator that is both unbiased for total variance and efficient.

### 2.5 Realized variance from intraday returns

The range estimators improve efficiency by using four prices per day. The realized-variance idea improves it much further by using *all* the prices. Partition the day into M intervals and let r_{t,i} be the log return over interval i; the *realized variance* is simply their sum of squares:

```
RV_t = Σ_{i=1..M} r²_{t,i}
```

The theory behind this is the reason high-frequency econometrics exists. As the sampling interval shrinks, RV_t converges in probability to the integrated variance — the quadratic variation of the price path — so a quantity that was latent at the daily frequency becomes, in the limit, *observable* (Andersen, Bollerslev, Diebold & Labys 2003; Barndorff-Nielsen & Shephard 2002). This is a genuine change in kind, not degree: with five-minute returns over a US equity session you get roughly 78 squared returns per day, and RV_t estimates the day's variance with a fraction of the sampling error of r_t². It is what makes the HAR model of Section 4 possible, because HAR regresses a *measured* realized variance on its own lags, and it is the natural object for the daily proxy we use in the forecasting horse race.

For the empirical work in this paper we do not have free tick data, so we use a *daily* realized-variance proxy that captures the two components that matter:

```
RV_t = o²_t + max( σ²_GK,t , 0 )          (overnight gap² + Garman–Klass session variance)
```

This is a whole-day, conditionally-unbiased proxy under the GK assumptions, floored at zero on the rare days the analytic GK combination goes slightly negative, and it is what Section 5 forecasts. Over the fifteen-year sample the GK term is never negative (0 of 3,770 days floored), so the proxy is clean. It is coarser than a five-minute RV, but it is free, reproducible, and — crucially for honest evaluation — it is *the same proxy for every model*, so no model is advantaged by the choice.

### 2.6 Microstructure noise and the sampling-frequency trap

The convergence of RV to integrated variance is an asymptotic statement about a frictionless price. Real prices are not frictionless, and the friction — *microstructure noise* — sets a hard limit on how finely you can sample. Observed transaction prices bounce between bid and ask, land on a discrete tick grid, and reflect the temporary price impact of individual orders; each observed log price is the efficient price plus a noise term. Squaring returns computed from noisy prices adds a bias that *grows* as the interval shrinks, because at very high frequency you are increasingly measuring the variance of the noise rather than of the price. The signature is the *volatility signature plot*: realized variance plotted against sampling frequency rises without bound as the interval goes to zero, instead of converging (Zhang, Mykland & Aït-Sahalia 2005; Hansen & Lunde 2006).

The classical, low-tech response is to *not sample too finely* — five minutes became the industry default precisely because it is fine enough to cut sampling error substantially yet coarse enough that microstructure noise is second-order for a liquid index. The modern response is a family of noise-robust estimators — the two-scales realized variance of Zhang, Mykland and Aït-Sahalia, the realized kernels of Barndorff-Nielsen and co-authors, and pre-averaging methods — that model the noise and remove its bias, allowing much finer sampling (Zhang, Mykland & Aït-Sahalia 2005). The practical lesson survives even without tick data: *there is no free lunch in sampling frequency.* Sampling too coarsely wastes information and leaves you noisy; sampling too finely poisons the estimate with market microstructure. The right frequency is an estimation decision to be made and stated, exactly like the window length in Section 2.2, not a detail to be left implicit.

### 2.7 Jumps and jump-robust measurement

The second problem is that prices *jump*. The diffusion idealization is continuous, but real returns include discontinuities — overnight gaps, the instantaneous repricing at a macro release, flash events. Quadratic variation does not distinguish a continuous burst of volatility from a discrete jump: both inflate RV. For some purposes that is fine, but for forecasting it matters, because the two components have very different persistence. Continuous volatility is highly persistent (it clusters); jumps are close to unpredictable. A forecaster that lumps them together will over-react to a jump day, extrapolating a one-off discontinuity as if it were persistent volatility.

The tool that separates them is *bipower variation*, which sums *products of adjacent absolute returns* rather than squares:

```
BV_t = (π/2) · Σ_{i=2..M} | r_{t,i} | · | r_{t,i−1} |
```

Because a jump lands in a single interval, it enters at most one term of each adjacent product and its contribution washes out asymptotically, so BV_t estimates only the *continuous* part of quadratic variation. The difference RV_t − BV_t, floored at zero, estimates the *jump* contribution (Barndorff-Nielsen & Shephard 2004; Andersen, Bollerslev & Diebold 2007). This decomposition is exactly what the HAR-J extension in Section 4.3 exploits: separate the persistent continuous variance, which you can forecast, from the jump variance, which you largely cannot, and let the regression weight them differently. The measurement section thus hands the forecasting section a cleaner input — and the recurring moral is that most gains in volatility *forecasting* come from measuring the *target* better, not from a fancier model of a badly-measured target.

## 3 Volatility forecasting I — the GARCH family

Volatility clusters: large moves follow large moves and calm follows calm, an observation as old as Mandelbrot. The GARCH family is the parametric machinery built to capture that clustering, and it remains the reference model for conditional variance. This section derives GARCH(1,1) from ARCH, fits it to the S&P by our own maximum likelihood, extends it for the leverage asymmetry, and then says plainly what the model cannot represent.

### 3.1 From ARCH to GARCH(1,1)

Engle's (1982) *ARCH* insight was to let the conditional variance depend on recent shocks. Write the return as r_t = μ + ε_t with ε_t = σ_t · z_t, where z_t is i.i.d. mean-zero unit-variance and σ_t² is the variance *conditional on yesterday's information*. An ARCH(q) model makes that conditional variance a function of past squared shocks:

```
σ²_t = ω + Σ_{i=1..q} α_i · ε²_{t−i}
```

This captures clustering — a big ε²_{t−1} raises today's variance — but to fit slowly-decaying persistence it needs many lags and hence many parameters (Engle 1982). Bollerslev's (1986) *GARCH* solved the parameter problem by adding a lag of the variance itself, giving the recursion that has anchored the field for forty years (Bollerslev 1986):

```
σ²_t = ω + α · ε²_{t−1} + β · σ²_{t−1}
```

Read it as a rule: today's variance is a constant ω, plus a reaction α to yesterday's *surprise*, plus a memory β of yesterday's *variance*. The single lag of σ² does the work of infinitely many ARCH lags, because unrolling the recursion expresses σ_t² as an exponentially-weighted sum of all past squared shocks. Three quantities summarize the model. Taking expectations of both sides — and using the fact that in steady state E[ε²_{t−1}] = E[σ²_{t−1}] — gives the *unconditional variance*:

```
σ̄² = ω / ( 1 − α − β )
```

which exists and is positive only if the *persistence* α + β < 1. That persistence governs how fast a shock decays: after a shock, the expected variance reverts toward σ̄² geometrically at rate α+β, with a *half-life* of ln(0.5) / ln(α+β) days. When α+β approaches one the model approaches *integrated GARCH*, where shocks never fully die and the unconditional variance ceases to exist — a boundary the S&P sits uncomfortably close to. A useful reparameterization for fitting is *variance targeting*: fix ω = σ̄²·(1 − α − β) at the sample variance, leaving only α and β to estimate, which stabilizes the optimization.

### 3.2 Fitting by maximum likelihood

GARCH is estimated by maximum likelihood. Assuming Gaussian innovations z_t ~ N(0,1), the conditional density of each return is normal with variance σ_t², and the log-likelihood of the whole series is

```
ℓ(ω, α, β) = − ½ · Σ_t [ ln( 2π · σ²_t ) + ε²_t / σ²_t ]
```

where each σ_t² is built by running the recursion forward from a starting value. Even when returns are not truly Gaussian, maximizing this *quasi*-likelihood gives consistent parameter estimates — the QMLE property — which is why the Gaussian likelihood is used almost universally as a workhorse (Bollerslev 1986). We fit it ourselves, in numpy, with a self-contained Nelder–Mead simplex and no optimization package; the positivity and stationarity constraints (ω > 0, α, β ≥ 0, α + β < 1) are imposed by a softmax reparameterization so the optimizer cannot wander into an explosive region. The core is a dozen lines:

```python
def nll_garch(theta, r):                      # negative Gaussian log-likelihood
    w = np.exp(theta[0])                       # omega > 0
    e = np.exp(np.array([theta[1], theta[2], 0.0]))
    a, b = e[0]/e.sum(), e[1]/e.sum()          # softmax keeps a + b < 1
    s2 = np.empty(len(r)); s2[0] = r.var()
    for t in range(1, len(r)):
        s2[t] = w + a*r[t-1]**2 + b*s2[t-1]     # the GARCH recursion
    if np.any(s2 <= 0): return 1e10
    return 0.5*np.sum(np.log(2*np.pi*s2) + r**2/s2)
```

Fitted to 3,770 daily S&P returns (demeaned, 2011–2026), the maximum-likelihood estimates are: ω = 4.11×10⁻⁶, α = 0.162, β = 0.798, giving a persistence of α+β = 0.960, a half-life of 16.8 days, and an implied long-run volatility of √(252·σ̄²) = 16.0% annualized, with a log-likelihood of 12,587.6. The persistence of 0.96 is the empirical fingerprint of volatility clustering: a shock to variance is half-forgotten only after about three trading weeks. The reaction coefficient α = 0.16 is on the high side of the textbook 0.05–0.10 range, and the memory β = 0.80 correspondingly lower, because this particular sample contains several sharp, reactive spikes (February 2018, the 2020 crash, 2022) that a single-regime QMLE accommodates by leaning on the fast-reacting α term. The long-run volatility of 16.0% is a sensible reading for the S&P over a period that mixed long calm stretches with three violent ones.

Panel (a) of Figure 2 shows the fitted conditional-volatility path tracking the clusters and then decaying geometrically between them — the visual signature of the GARCH recursion.

![GARCH(1,1) fitted to S&P 500 daily returns by own Gaussian maximum likelihood (Nelder–Mead, softmax-constrained) and GJR-GARCH(1,1) fitted by maximum likelihood under the correct GJR stationarity condition (via `arch`), 2011–2026. Panel (a): the GARCH(1,1) conditional volatility against absolute returns, rising into clusters and decaying geometrically out of them. Panel (b): the news-impact curves — GARCH is symmetric in the sign of yesterday's return, while GJR lifts the response to negative returns, capturing the leverage effect. Reproduce with figures/fig_garch_fit.py.](figures/fig_garch_fit.png)

### 3.3 Asymmetry: GJR and EGARCH

Plain GARCH has a symmetry that the data reject: through ε²_{t−1} it reacts identically to a −3% day and a +3% day. Equity volatility does not — it rises much more after a fall than after an equal-sized rise, the *leverage* or *volatility-feedback* effect. Two models add the asymmetry. The *GJR-GARCH* of Glosten, Jagannathan and Runkle (1993) adds a term that switches on only after negative shocks (Glosten, Jagannathan & Runkle 1993):

```
σ²_t = ω + α · ε²_{t−1} + γ · 1{ε_{t−1} < 0} · ε²_{t−1} + β · σ²_{t−1}
```

so a negative return contributes α+γ where a positive one contributes only α. Fitting GJR gives ω = 3.91×10⁻⁶, α = 0.027, γ = 0.232, β = 0.816: the leverage coefficient γ is many times *larger than the symmetric coefficient* α, meaning a down day drives next-day variance about **nine to ten times** (≈9.7×) as hard as an up day of the same size. The improvement is decisive — the log-likelihood rises to 12,658.4, a likelihood-ratio statistic of 141.6 against the one-parameter restriction γ = 0, which is off the chart of any χ²₁ distribution (the 0.1% critical value is 10.8). (An earlier revision reported α = 0.051, γ = 0.139, β = 0.810 and only a 3.7× asymmetry; that fit sat on a softmax constraint α+γ+β<1, tighter than the correct GJR stationarity condition α+γ/2+β<1, which pinned the estimate to the boundary and understated the leverage. The corrected fit uses the proper condition — via `arch` — and has the higher likelihood; see ERRATA.) Panel (b) of Figure 2 draws the two *news-impact curves* — next-day volatility as a function of yesterday's return — and the GJR curve's leftward lift is the leverage effect made visible.

Nelson's (1991) *EGARCH* models the log-variance instead:

```
ln σ²_t = ω + β · ln σ²_{t−1} + α · ( |z_{t−1}| − E|z_{t−1}| ) + γ · z_{t−1}
```

which has two structural advantages: modeling the log removes the need for any positivity constraints on the parameters, and the standalone γ·z_{t−1} term captures the sign asymmetry directly (Nelson 1991). GJR and EGARCH usually agree on the economics; the choice between them is mostly a matter of which constraint structure is more convenient.

### 3.4 What GARCH captures and what it structurally misses

GARCH earns its longevity by capturing two facts cleanly: *volatility clustering* (through the recursion) and *mean reversion* (through persistence < 1). Both are real and both are economically important, and a well-fitted GJR is a serviceable one-day-ahead forecaster. Diagnostics confirm the fit is reasonable — the standardized residuals z_t = ε_t / σ_t should be approximately i.i.d., and a Ljung–Box test on their squares should find little remaining ARCH structure, which is the standard check after fitting; a residual QQ-plot against the Gaussian typically still shows fat tails, which is why practitioners often refit with Student-t innovations (Bollerslev 1986). Parameter stability is the other diagnostic worth running: refitting on rolling subsamples usually shows α and β drifting, and the near-unit persistence means the estimated long-run variance σ̄² = ω/(1 − α − β) is sensitive — a small change in α+β near the boundary moves the implied long-run level a lot, so the 16.0% figure above should be read with wide error bars.

But GARCH has two structural blind spots that no amount of parameter tuning removes, and naming them is the point of this section. First, *long memory.* The autocorrelation of realized variance decays *hyperbolically* — slowly, like a power law — so volatility today is correlated with volatility months ago. GARCH's autocorrelation decays *geometrically* at rate (α+β)^k, which is far too fast: to fit the slow decay it is forced toward α+β → 1 (our 0.96 is symptomatic), at which point it loses its mean-reverting anchor. A single GARCH cannot be both persistent enough to match long memory and stationary enough to revert; the data want both, and the model can supply only one (Corsi 2009). Second, *jumps.* GARCH treats every large ε² as a persistent shock to variance, so a one-off discontinuity — a jump that carries no information about tomorrow — is extrapolated as if it were clustering, producing forecasts that over-shoot after jump days. Section 2.7 showed how to separate jumps from continuous variance in *measurement*; GARCH, working only from daily returns, cannot make that separation at all. These two misses are exactly the gaps the next section's model was built to fill — not with more parameters, but with a change of target and a change of functional form.

### 3.5 Multi-step forecasting and the variance term structure

GARCH forecasts more than one day ahead, and the shape of its multi-step forecast is where its mean-reversion becomes visible and testable. Iterating the recursion under the model, the k-step-ahead conditional-variance forecast reverts geometrically toward the unconditional variance:

```
E_t[ σ²_{t+k} ] = σ̄² + ( α + β )^{k−1} · ( σ²_{t+1} − σ̄² )
```

So from wherever today's conditional variance sits, the forecast fans out toward the long-run level σ̄² at the persistence rate α+β. With the fitted persistence of 0.960 that reversion is slow — the same 16.8-day half-life — so a GARCH fitted to the S&P implies a *term structure of expected variance* that decays only gradually from the current level to the 16%-annualized anchor. This object is directly comparable to the observed VIX/VIX3M slope of Section 7: it is the model's own answer to "what does the volatility curve look like?", and comparing the two is a clean specification check. The comparison also exposes GARCH's long-memory failure from a second angle: because the model's reversion is *geometric* while the real variance term structure decays *hyperbolically*, a single GARCH systematically misprices the far end of the curve — too flat when volatility is high, too steep when it is low — which is one more reason the flat-looking HAR cascade, with its slower implied decay, tends to win at longer horizons. The direction check is worth stating: a GARCH forecast curve that reverts faster than the market's implied curve is not evidence the market is wrong; it is usually evidence the model's memory is too short.

## 4 Volatility forecasting II — HAR-RV, the workhorse

If GARCH is the elegant model, the *Heterogeneous Autoregressive* model of realized volatility is the one that quietly wins. It looks almost too simple to work — an ordinary regression of realized variance on three of its own averages — yet it forecasts better than most of the parametric competition out of sample, and it does so while remaining transparent and trivially estimable. This section explains why.

### 4.1 The cascade

Corsi's (2009) HAR-RV forecasts tomorrow's realized variance as a linear function of the realized variance measured over three horizons — the past day, the past week, and the past month (Corsi 2009):

```
RV_t = c + β_d · RV^(d)_{t−1} + β_w · RV^(w)_{t−1} + β_m · RV^(m)_{t−1} + ε_t
```

where RV^(d) is the previous day's realized variance, RV^(w) its average over the past 5 days, and RV^(m) its average over the past 22. The economic story is the *heterogeneous market hypothesis*: different participants operate on different horizons — day traders, weekly swing traders, monthly portfolio managers — and each generates volatility persistence at its own scale, so the aggregate volatility process is a cascade of components across horizons. HAR mimics that cascade with three regressors. It is not a true long-memory model, but three overlapping horizons approximate the slow hyperbolic decay of the realized-variance autocorrelation well enough that the difference rarely matters in practice — and it does so with three interpretable coefficients estimated by ordinary least squares, rather than a fractional-integration parameter that is delicate to estimate.

In practice one models the *logarithm* of realized variance, ln(RV), for two reasons: log realized variance is much closer to Gaussian than the strongly right-skewed level, which makes OLS well-behaved, and modeling logs guarantees positive variance forecasts. The forecast is then mapped back to the level with the lognormal correction RV_t = exp( ŷ_t + ½·s² ), where s² is the regression's residual variance — the standard adjustment for the mean of a lognormal, without which the level forecast is biased low. Fitted on an expanding window to the daily proxy of Section 2.5, the log-HAR coefficients at the end of the sample are [c, β_d, β_w, β_m] = [−1.153, 0.250, 0.440, 0.197] with residual variance 0.696. The weights are informative: the *weekly* term carries the largest coefficient, and the three persistence coefficients sum to 0.887 — high, but comfortably below the unit-root boundary GARCH was pinned against, which is precisely how HAR represents strong persistence *without* sacrificing mean reversion.

### 4.2 Why a dumb-looking OLS wins

There is something almost provocative about HAR beating GARCH: no likelihood, no asymmetry term, no distributional assumption beyond OLS, just three moving averages. It wins out of sample for a stack of reasons that all point the same way. It forecasts a *measured* target — realized variance — rather than inferring a latent conditional variance from squared daily returns, so it inherits the efficiency gains of Section 2.5 for free. It approximates long memory, the exact thing GARCH structurally cannot do. It is linear and estimated by OLS, so it is robust, has no convergence failures, and does not overfit the way a richly parameterized likelihood model can. And its regressors are averages, which are stable and slow-moving, so its forecasts are not whipped around by a single day. There is one econometric caveat worth stating plainly: the weekly and monthly regressors are overlapping moving averages, so the regression's residuals are serially correlated and the *reported* OLS standard errors are too small — inference on the coefficients needs a HAC (Newey–West) correction. That caveat is about the coefficient standard errors, not the point forecasts, which remain unbiased; it is why the evaluation in Section 5 tests forecast *accuracy* out of sample rather than trusting in-sample coefficient t-statistics. The general lesson from the forecasting literature is blunt: *simple, robust, well-specified models beat complex ones out of sample*, and HAR is the canonical illustration in volatility (Corsi 2009). Section 5 tests this claim under a pre-committed protocol rather than asserting it.

### 4.3 Extensions: HAR-J and implied-vol augmentation

HAR is a frame, not a fixed model, and two extensions are standard. The first uses the jump decomposition of Section 2.7. *HAR-J* splits the daily regressor into its continuous part (bipower variation) and its jump part (RV − BV)⁺, letting the regression assign them different coefficients (Andersen, Bollerslev & Diebold 2007). Empirically the continuous component is strongly persistent and forecastable while the jump component is nearly transient — its coefficient is small — so separating them improves forecasts by preventing the model from extrapolating one-off jumps. The finer *HAR-RV-CJ* variant carries continuous and jump terms at all three horizons.

The second extension adds *implied* information. Because the VIX is a forward-looking, risk-neutral expectation of variance, it contains information about the future that backward-looking realized variance cannot — so an *implied-vol-augmented HAR* adds ln(VIX²/12) as a regressor alongside the realized-variance cascade. In many studies the implied term is significant and improves the fit, sometimes subsuming the monthly realized term, because the market's own variance forecast already aggregates a great deal of information (Bollerslev, Tauchen & Zhou 2009). The caveat is the theme of Section 6: the VIX carries the variance risk premium, so it is a *biased* forecast of realized variance, high on average; an augmented HAR must estimate a coefficient on the implied term that is free to correct that bias rather than swallowing it whole. The extension is powerful precisely because the object it adds — the wedge between implied and realized — is the subject of the second half of this paper.

### 4.4 Multi-horizon forecasting: direct versus iterated

Most uses of a volatility forecast are not one day ahead but one week or one month — an option's life, a risk horizon, a rebalancing period — and there are two ways to produce them. The *iterated* forecast builds the h-day forecast by feeding one-step forecasts back into the model repeatedly (as in the GARCH term structure of Section 3.5); it is statistically efficient *if the one-step model is correctly specified*, and badly biased if it is not, because specification error compounds at every step. The *direct* forecast side-steps that compounding by changing the target: regress the realized variance *over the next h days* directly on today's information, fitting one model per horizon. HAR is unusually well-suited to the direct route, because its regressors are already multi-horizon averages — to forecast the next month's realized variance you simply put the next 22 days' cumulative realized variance on the left-hand side and keep the same daily/weekly/monthly cascade on the right. That is a large part of why HAR is the workhorse of option-pricing and risk applications: the same three-regressor OLS, re-pointed at a longer target, gives a direct multi-horizon forecast with no compounding of model error, and it inherits the long-memory approximation at every horizon. The trade-off is honest and worth stating: direct forecasting is robust but throws away the cross-horizon restrictions that an iterated model imposes, so with a *correctly specified* model the iterated forecast is more efficient — which, given that no volatility model is correctly specified, is precisely why the direct HAR route usually wins in practice.

## 5 Forecast evaluation done right

A forecast is only as credible as the contest it survived, and volatility forecasting is unusually easy to evaluate dishonestly: the target is latent, the losses disagree, and the temptation to report the metric that flatters your model is strong. This section fixes one pre-committed protocol, runs the three models of Section 3–Section 4 against the hardest naive benchmark, and reports the outcome honestly — including where the primary and secondary metrics point in different directions.

### 5.1 The proxy problem and why the loss function is a choice

Because integrated variance is latent, every forecast is scored against a *proxy* — here the daily realized-variance proxy of Section 2.5. Patton (2011) showed that this is dangerous: many intuitive loss functions, when applied to a noisy proxy instead of the true variance, rank forecasts *inconsistently*, preferring a worse forecast because it happens to fit the proxy's noise. Only a specific subclass of losses is *robust* — guaranteed to rank forecasts the same way whether scored against the true variance or an unbiased proxy — and the two most used members of that class are mean-squared error and QLIKE (Patton 2011). Both are robust, yet they emphasize completely different things, and choosing between them is a modeling decision that must be made in advance.

QLIKE, the loss implied by the Gaussian likelihood, with h the variance forecast, is

```
QLIKE( RV, h ) = RV/h − ln( RV/h ) − 1
```

It penalizes *proportional* errors: being off by 20% costs the same in a calm regime as in a crisis, because only the ratio RV/h enters. Mean-squared error, MSE = (RV − h)², penalizes *absolute* errors in variance units, so it is dominated by the few days with the largest variance — one badly-forecast crash day can outweigh a year of accurate calm days. This is not a subtlety; it decides the contest. A model that nails the 2020 spike but is mediocre elsewhere can win MSE while losing QLIKE, and a model that is proportionally accurate across all regimes can win QLIKE while losing MSE. QLIKE is also asymmetric in a way that suits risk management: it punishes *under*-prediction of variance more heavily than over-prediction, which is the right bias for a loss that will inform position sizing. The honest researcher picks the loss that matches the decision the forecast will inform — for risk sizing, proportional accuracy across regimes (QLIKE) is usually what you want — and *pre-commits to it*.

### 5.2 The pre-committed protocol

Following the pre-registration paper, the entire evaluation was fixed before any out-of-sample number was examined. Stated once, in full:

- **Models.** A random walk (h_t = RV_{t−1}, the hard naive benchmark), a GARCH(1,1) re-estimated by own QMLE each January on an expanding window, and a log-HAR re-fit by OLS every day on an expanding window with the lognormal correction. No other variants were tried.
- **Split.** Out-of-sample is 2 January 2020 onward — the same single split date used throughout the paper — opened once. In-sample is 2011-09-20 to 2019-12-31 (2,084 observations); out-of-sample is 1,686 observations.
- **Primary loss.** QLIKE. Secondary: MSE on variance.
- **Tests.** Diebold–Mariano on the QLIKE loss differential (Newey–West HAC standard errors, 5 lags) for the non-nested comparisons; Clark–West for the nested log-HAR-versus-random-walk comparison; Mincer–Zarnowitz level regressions per model, out-of-sample only.
- **Decision rule.** A model beats the random walk only if its out-of-sample QLIKE is lower *and* the corresponding test rejects equal predictive accuracy at 5% *and* the sign agrees. Report the null otherwise.

The Diebold–Mariano test itself is simple: form the per-day loss differential d_t = L(model A) − L(model B), and test whether its mean is zero using a heteroskedasticity-and-autocorrelation-consistent standard error, DM = mean(d) / se_HAC(mean(d)), which is asymptotically standard normal (Diebold & Mariano 1995). Every model sees only data strictly prior to each forecast; the expanding-window re-estimation means the GARCH and HAR parameters at each date used no future information. This is the operational meaning of "opened once": the out-of-sample block is scored a single time, with the protocol above, and whatever it prints is the result.

### 5.3 The result, reported honestly

![Strict out-of-sample one-day-ahead volatility forecasts, 2020–2026 (1,686 sessions), for the random walk, GARCH(1,1), and log-HAR, each estimated only on data prior to every forecast. Panel (a): the log-HAR and GARCH forecast paths against the realized proxy on a log scale. Panel (b): mean out-of-sample QLIKE, the pre-committed primary loss — log-HAR lowest, then GARCH, then the random walk. Reproduce with figures/fig_har_oos.py.](figures/fig_har_oos.png)

On the primary loss the ordering is clean and the effect large. Mean out-of-sample QLIKE is 0.685 for the random walk, 0.405 for GARCH, and 0.377 for log-HAR — HAR best, GARCH second, both far ahead of the naive benchmark. The Diebold–Mariano tests confirm the gaps are not noise: HAR versus the random walk gives a loss differential of 0.308 with a DM statistic of 10.5 (one-sided p effectively zero), and GARCH versus the random walk gives 0.280 with a DM statistic of 8.2 (p ≈ 1×10⁻¹⁶). One caveat travels with the HAR–random-walk pair specifically: HAR *nests* the random walk, so the Diebold–Mariano statistic is not strictly valid for it and is shown here only for descriptive completeness — the correct nested test is Clark–West, applied below, and it returns a far more guarded verdict. On QLIKE, the pre-committed primary metric, both models decisively beat the random walk and HAR beats GARCH. The direction check passes — the signs are all in HAR's and GARCH's favor — so on the primary loss the protocol supports the models.

Now the honesty that the protocol forces. On the *secondary* loss, MSE, the ordering *changes*: GARCH has the lowest MSE (6.00×10⁻⁸), then log-HAR (6.29×10⁻⁸), then the random walk (6.64×10⁻⁸). MSE prefers GARCH; QLIKE prefers HAR. This is Section 5.1 made concrete on real data: because MSE is dominated by the handful of extreme-variance days in 2020, and the log-HAR's lognormal forecast handles those tail days slightly less well than GARCH in absolute variance units, the two robust losses rank the top two models in opposite orders. Neither metric is wrong; they answer different questions. We committed to QLIKE as primary, so the headline is "HAR wins" — but a researcher who had quietly switched to MSE after seeing the result could have written "GARCH wins" with equal apparent justification, and that switch is exactly the researcher degree of freedom the pre-registration was designed to remove.

The Mincer–Zarnowitz regressions add a third, uncomfortable angle. Regressing realized variance on each forecast (RV = a + b·F), an ideal forecast gives intercept 0 and slope 1. Out-of-sample the slopes are 0.689 (random walk), 0.700 (GARCH), and 1.366 (log-HAR), with R² of 0.475, 0.544, and 0.445 respectively. HAR's slope of 1.37 says its level forecasts are biased *low* on average — they need scaling up by a third — a residue of the lognormal correction struggling with fat tails, even though HAR's *proportional* accuracy (QLIKE) is the best of the three. And HAR's MZ R² is actually the *lowest*: GARCH explains more of the level variance. So the tidy story "HAR is best, full stop" is false. The correct, defensible statement is narrower and more useful: *HAR wins the pre-committed primary loss (QLIKE) decisively, GARCH is competitive and wins on absolute-error and level-R² diagnostics, and both crush the random walk* — a result in which the choice of loss function genuinely decides the winner, which is the entire point of the section.

Finally, the nested test earns its own caveat. The Diebold–Mariano statistic assumes the two forecasts are non-nested; HAR nests the random walk (set the weekly and monthly coefficients so it reduces to a persistence rule), so the correct nested test is Clark–West, which adjusts for the extra estimation noise a larger model carries under the null (Clark & West 2007). Clark–West gives a statistic of only 1.65, one-sided p = 0.049 — barely significant, in sharp contrast to the overwhelming DM statistic on QLIKE. The two tests disagree in *strength* because Clark–West is computed on the MSE-type loss where the 2020 outliers dominate and the random walk is much more competitive. This is a genuine, publishable tension: the primary-loss verdict is overwhelming, the nested-model MSE-based verdict is marginal, and an honest write-up reports both rather than quoting whichever is more flattering. The single number to carry away is the QLIKE horse race — HAR 0.377, GARCH 0.405, random walk 0.685 — with the explicit footnote that the ranking is loss-dependent and the nested test is only marginal.

### 5.4 Forecast combination and encompassing

One of the most humbling regularities in the forecasting literature is that a simple *combination* of two decent forecasts often beats both of them, because each captures information the other misses and averaging cancels their idiosyncratic errors. The tool for deciding whether to combine is the *forecast-encompassing* test: regress the realized target on both forecasts at once, and read the coefficients. If one forecast's coefficient is significant and the other's is zero, the first *encompasses* the second — the second adds nothing once you have the first — and you should just use the first. If both coefficients are significant, neither encompasses the other, and a combination will beat either alone. For our horse race the economics all but guarantees the second outcome: HAR carries the long-memory information that GARCH structurally lacks, while GARCH's leverage term and its level dynamics capture asymmetry that the symmetric HAR cascade ignores, so a HAR–GARCH combination would very likely lower the out-of-sample QLIKE below HAR's 0.377. The disciplined point, though, is what we do *not* do: a combination was not in the pre-committed protocol of Section 5.2, so fitting one now and reporting its improved loss would be exactly the post-hoc, results-known model selection the pre-registration paper forbids. The honest treatment is to record "test a pre-committed HAR–GARCH combination and encompassing regression" as a hypothesis for a *future* study on *future* data, and to leave the current horse race's verdict — HAR wins the pre-committed primary loss — untouched by hindsight.

## 6 The variance risk premium

The first half of this paper forecast the *physical* volatility that will be realized. The market prices a *risk-neutral* expectation of that same variance, and the two are not equal. The systematic wedge between them — the variance risk premium — is one of the most robust anomalies in asset pricing and the economic engine behind every short-volatility strategy. This section defines it precisely, measures it under a pre-registered test, and reads the result as what it is: insurance compensation with a violent left tail.

### 6.1 Definition and units

The *variance risk premium* is the difference between the risk-neutral and physical expectations of future variance over the same horizon:

```
VRP_t = E^Q_t[ RV_{t,t+τ} ] − E^P_t[ RV_{t,t+τ} ]
```

The risk-neutral expectation E^Q is what the option market charges for variance and can be read off option prices model-free — it is essentially the squared VIX, since the VIX is constructed as the price of a 30-day variance swap from a strip of out-of-the-money options (Carr & Wu 2009; Bollerslev, Tauchen & Zhou 2009). The physical expectation E^P is the variance that will actually be realized. In the index the premium is *positive on average*: options are, on average, priced above the variance that subsequently occurs, so a seller of variance (short options, delta-hedged) collects a premium for bearing volatility risk. This is the rigorous, model-free form of the loose observation that implied volatility usually exceeds realized volatility.

Units are where measurement goes wrong, so we fix them explicitly. Working in monthly percentage-variance points: the implied leg is IV²_t = VIX²_t / 12 (the annual variance divided by twelve for a one-month horizon), and the realized leg RV_t is the sum of squared daily percentage log returns over the *next* 21 trading days. Then VRP_t = IV²_t − RV_t, a number in monthly %². A word on the measurement pitfalls, which are real: the two legs must cover the *same horizon* (a 30-day implied against a 21-trading-day realized is the standard, slightly imperfect, alignment); the realized leg is forward-looking and overlapping, so consecutive observations share days and are heavily autocorrelated, which inflates naive standard errors and demands a HAC correction; there is a variance-versus-volatility subtlety, because by Jensen's inequality the premium measured in variance units and in volatility units are not the same object and must not be mixed; and the sign convention differs across the literature — some authors define the premium with the opposite sign (physical minus risk-neutral) so that the "long variance" holder's premium is negative. We fix implied-minus-realized so that a positive number means variance sold rich.

### 6.2 The premium as insurance compensation

Why should this wedge exist and persist? Because variance is an *insurance* market. End-users — funds with drawdown mandates, structured-product desks, anyone who must not blow up in a crash — are structural *buyers* of variance and tail protection, because variance spikes exactly when their other assets fall. Dealers and volatility sellers provide that insurance and demand to be paid for it, because they cannot hedge the risk frictionlessly and they are the ones left short gamma into a crash (Carr & Wu 2009). The premium is the price of that insurance. The economic prediction is therefore not merely "the premium is positive" but "the premium is compensation for a *negatively skewed* payoff": the variance seller wins a little most of the time and loses catastrophically, rarely — the textbook shape of an insurance underwriter's P&L. Any honest empirical test has to look at the whole distribution, not just the mean, because the mean of an insurance payoff is the least informative moment.

### 6.3 A pre-registered empirical study

We test the premium on free data under a protocol fixed in the text *before* the result, exactly as the pre-registration paper requires.

- **H₀:** the mean variance risk premium is ≤ 0 (variance does not sell at a premium).
- **H₁ (directional):** the mean variance risk premium is > 0.
- **Data.** VIX daily closes (FRED VIXCLS) inner-joined to daily S&P 500 closes over the shared 2011–2026 cache; 3,749 overlapping 21-day windows.
- **Primary metric.** Mean VRP in monthly %² with a Newey–West t-statistic (21 lags, for the overlapping windows). Secondary: the share of windows with VRP > 0 (the hit rate).
- **Split.** Out-of-sample is 2 January 2020 onward — the paper's single split date — opened once.
- **Decision rule.** Reject H₀ only if the mean is positive, the Newey–West t exceeds the one-sided 5% critical value, and the sign holds out-of-sample.

The direction check is built into the hypothesis: H₁ commits to a positive sign, so a negative mean, however large, cannot be read as support.

![The variance risk premium on free data, 2011–2026: VIX²/12 minus the realized variance of the following 21 trading days, in monthly percentage-variance points, over 3,749 overlapping windows. Panel (a): implied volatility (VIX) against the realized volatility that actually followed. Panel (b): the premium itself — small and positive most of the time (green), occasionally and violently negative when realized variance overshoots (red, clipped; the 2020 crash reaches far past the axis). Reproduce with figures/fig_vrp.py.](figures/fig_vrp.png)

The results, reported exactly as computed. Full-sample, the mean premium is +6.98 %² per month with a Newey–West t of 2.31 (one-sided p = 0.010) and a hit share of 84.6% — variance sold at a premium in roughly six windows out of seven. In vol-point terms the mean implied volatility was 18.0% against a mean subsequent realized volatility of 14.3%, a wedge of about 3.7 volatility points, which is economically large. (These are two different summaries and must not be conflated: the +6.98 %²/month is the mean of the variance differences, while the 3.7-point wedge is the gap between the average volatilities; by Jensen's inequality one does not square into the other — 3.7 vol points corresponds to roughly 9.96 %², not 6.98 %² — which is exactly the variance-versus-volatility trap flagged in Section 6.1.) So far the picture supports H₁ cleanly. But the out-of-sample split delivers the honest complication the paper's discipline exists to surface: in-sample (pre-2020) the mean premium is +7.64 with an overwhelming t of 7.31, while *out-of-sample* (2020 onward) the mean is +6.15 with a hit share of 84.8% but a Newey–West t of only 0.92 (one-sided p = 0.18) — *not significant at conventional levels*.

Read the tension carefully, because it is the whole lesson. The out-of-sample point estimate has the right sign and a nearly identical hit rate (85%), yet the pre-committed significance test *fails to reject H₀*. The reason is the insurance structure of Section 6.2 made manifest in the data: the out-of-sample period contains the 2020 crash, whose five deepest inversions run from about −635 to −680 %² per month — a variance seller's catastrophe an order of magnitude larger than the typical monthly premium. Those few observations blow up the variance of the overlapping-window mean, and the Newey–West correction, doing its job over 21 overlapping lags, is appropriately conservative. So the strict verdict of the pre-registered test is: *we fail to reject the null out-of-sample at conventional significance, even though the sign and the 85% hit rate agree with H₁.* Overall, across the full sample, 15.4% of windows had a negative premium — the insurance underwriter's occasional large loss.

The temptation now is to quietly emphasize the hit rate ("wins 85% of the time!") and bury the insignificant t. That is precisely the move the protocol forbids. The pre-committed primary metric was the Newey–West t on the mean, and out-of-sample it is 0.92. The correct scientific statement is that *the variance risk premium is economically present and directionally robust — positive mean, 85% hit rate, ~3.7 vol points — but its out-of-sample statistical significance is fragile, dominated by a small number of catastrophic inversions, exactly as an insurance premium with negative skew should be.* That is a more useful finding than a spurious victory lap, because it tells the would-be variance seller the truth: the edge is real on average and it will occasionally take back years of premium in a week. It also cautions against over-reading the very high hit rate — 85% of windows positive looks like a near-sure thing until one remembers that the 15% are where all the losses live and that overlapping windows make the effective sample far smaller than 3,749.

### 6.4 When the premium compresses and inverts

The premium is not constant. It *compresses* in calm, low-volatility regimes, when implied volatility is already floored near realized and there is little wedge left to sell — selling variance when the VIX is in the low teens harvests a thin premium against the same fat left tail, a poor risk-reward. And it *inverts* — goes sharply negative — precisely in crises, when realized variance overshoots the implied that preceded it, which is the mechanism behind every one of the 2020 inversions above. This time-variation is itself forecastable to a degree and connects the premium back to the surface paper's term structure: a steep contango and a compressed premium mark the complacent regime where sellers are paid least for the most tail risk, while an inverted term structure coincides with the premium going negative in real time. Bollerslev, Tauchen and Zhou (2009) further showed that the *variance risk premium itself* predicts future equity returns — a high premium forecasts high returns — making it not just a trading P&L but a genuine state variable (Bollerslev, Tauchen & Zhou 2009). For the purposes of this paper the operational read is simpler: the premium is real, it is insurance, and it is measured honestly only when the left tail is kept in the frame.

### 6.5 The premium as the P&L of a delta-hedged short option

The variance risk premium is not an abstract wedge between two expectations; it is, almost exactly, the expected profit-and-loss of *selling an option and delta-hedging it to expiry*. The daily P&L of a continuously delta-hedged short option position is, to leading order,

```
dP&L ≈ ½ · Γ · S² · ( σ²_implied − r²_realized )
```

where Γ is the option's gamma and S the spot: the hedger collects theta each day, priced off the implied volatility they sold, and pays out on the realized squared move through gamma. Summed over the option's life and weighted by dollar gamma, the accumulated P&L of the delta-hedged short is proportional to the integrated gap between implied and realized variance — which *is* the variance risk premium. So the 3.7-volatility-point wedge measured in Section 6.3 is not a curiosity; it is the gross edge that a variance seller monetizes, and the mechanism by which they monetize it is exactly the gamma-theta trade-off: short gamma earns the premium in calm and bleeds it back in a large realized move. This closes the loop with the insurance framing of Section 6.2 and with the leverage effect of Section 3.3, because the realized moves that overwhelm the premium are the down-moves that also spike implied volatility, so the variance seller loses on gamma and on vega at the same time — the double loss that makes the left tail of Section 6.3 so violent. It also delivers the practitioner's warning in one line: the premium is real and harvestable, but the instrument that harvests it is short gamma into exactly the moves that matter most, so position size, not the sign of the mean, is what keeps a variance seller solvent.

## 7 Term-structure studies

The variance risk premium of Section 6 is a premium on the *level* of variance. The volatility term structure carries a second, related premium — on the *slope* — and harvesting it is the economic basis of the entire volatility-carry industry. This section treats slope and carry signals honestly: what the signal is, how brutally transaction costs bite, how to condition it on the surface paper's factor set, and how to test whether it survives across macro regimes rather than assuming it does.

### 7.1 Slope, carry, and roll

The surface paper established the two facts this section builds on: the VIX term structure is in contango — longer-dated implied above shorter-dated, VIX3M above VIX — on about 92% of days, and it inverts into backwardation only in stress, roughly 8% of the time, with a median VIX of about 16 in contango against 28 in backwardation (companion surface paper, on Cboe data). Contango is the resting state, and it is the source of a carry. A holder of a long-volatility position via VIX futures suffers *negative roll yield* in contango: each day the future it owns rolls down toward a lower spot VIX, bleeding value even if spot never moves, while the short-volatility holder harvests exactly that roll as positive carry. The *slope*, quoted as the ratio VIX/VIX3M, is therefore simultaneously a regime gate (above 1 means stress) and a carry signal (well below 1 means the short-volatility roll is fat). A term-structure carry strategy, in its simplest honest form, is: be short volatility when the curve is in steep contango, flat or long when it flattens or inverts. Crucially, this is a signal about the *futures* curve and its roll, not merely the spot-implied term structure — the surface paper's warning that these are cousins, not twins, matters here, because only the futures curve carries the roll yield that pays the carry.

### 7.2 Honest transaction-cost accounting

Every apparent volatility-carry edge must survive its costs, and in this corner of the market the costs are unusually large and unusually easy to understate. Three components dominate. First, the *bid–ask spread* on VIX futures and, far worse, on the volatility ETPs built on them, which for the leveraged and inverse products can be many multiples of the spread on the underlying index. Second, the *roll cost* of continuously rebalancing a constant-maturity exposure, which is a real, recurring transaction, not a paper entry. Third, and most insidiously, the *rebalancing cost of the products themselves*: an inverse-volatility ETP must buy futures into a rising market to maintain constant leverage, so its worst fills come at the worst possible moments — the mechanism that destroyed the inverse-vol complex in February 2018, documented in the surface paper.

The pre-registration paper's cost-sensitivity discipline applies with full force: recompute the strategy's Sharpe across a grid of cost assumptions and report the break-even cost at which the edge dies. A worked illustration of the arithmetic makes the danger concrete. Suppose a slope-conditioned short-vol rule turns over its position, on average, twice a month — twenty-four round trips a year — and suppose the realistic all-in round-trip cost in a volatility ETP is a conservative 30 basis points. Then the annual cost drag is roughly 24 × 30 bps = 7.2% of notional per year, before any market-impact tail on the bad days. A gross carry that looked like an annualized 8–10% is, net, a low-single-digit return exposed to the February-2018 tail — and if the turnover is higher or the spreads wider on the days that matter (they always are), the net edge can vanish entirely. Because turnover in these strategies is high, the cost drag — turnover times per-trade cost — is frequently larger than the entire gross carry. A volatility-carry backtest that reports a headline Sharpe with no cost curve is not a result; the honest null is that much of the raw contango carry is compensation for exactly these frictions plus the crash risk, not a free lunch.

### 7.3 Conditioning on the factor set

A naive carry signal — short volatility whenever the curve is in contango — is short volatility 92% of the time, which is not a signal but a permanent exposure to the crash it cannot survive. The improvement is to *condition* the carry on the surface paper's compact factor set rather than trading the slope alone. That factor set spans roughly three independent dimensions: a level/term factor (the VIX and the VIX/VIX3M slope), a vol-of-vol/convexity factor (VVIX), and a tail-and-dispersion factor (SKEW with implied correlation). Each conditions the carry differently. A steep contango *with a low, stable VVIX* is the benign carry regime — the roll is fat and the market is not pricing a convex vol move. The same contango *with an elevated VVIX* is a warning: the market is paying up for VIX optionality, dealer vanna hedging is primed to amplify any vol spike, and the short-carry position is precisely the one that reflexive flow will run over. Conditioning the carry on VVIX, and standing aside when the tail factor is bid into a flattening slope, is the difference between harvesting a premium and underwriting a catastrophe with the premium as bait. The standing rule from the surface paper carries over verbatim: *a numeric factor overrules a single-index narrative* — a slope that has ticked toward backwardation overrules "but the VIX is still low," and it does so because the reading rule was fixed before the day, not after it.

### 7.4 Testing non-stationarity across regimes

The deepest risk in any term-structure study is that the relationship it exploits is *not stationary* — that the parameters drift across macro regimes, so an edge fitted in one era evaporates in the next. This is not a hypothetical concern; Section 6 already exhibited it. The variance risk premium, which is the level-analogue of the term-structure carry, had an in-sample Newey–West t of 7.31 and an out-of-sample t of 0.92 across the single 2020 split — the same sign, a similar hit rate, and a collapse in statistical strength driven by one macro regime (the COVID crash) that the pre-2020 sample never saw. That is non-stationarity in the raw data, surfaced only because the protocol pre-committed to an out-of-sample split rather than reporting the flattering full-sample number. The methodological prescription follows directly: never report a term-structure carry result on a single sample. Split it across regimes — pre- and post-a-major-structural-break, high- and low-rate environments, quantitative-easing and quantitative-tightening eras — and require the sign and rough magnitude to hold across all of them before believing the edge. Where they do not hold, the honest conclusion is that the carry is regime-dependent and its unconditional Sharpe is a fiction averaged over incompatible worlds. The zero-cost defense is the pre-registration paper's: fix the regime definitions and the split *before* looking, so the regimes are not themselves chosen to make the result look stable. Conditioning the carry on the factor set (Section 7.3) is, in this light, an attempt to *make* the relationship more stationary by controlling for the state variable — VVIX, the slope — whose variation drives the drift.

## 8 Fitting the surface: SVI with no-arbitrage constraints

The final tool is the one an options desk cannot function without: a parameterization of the implied-volatility smile that fits the observed quotes, interpolates and extrapolates them smoothly, and — this is the hard part — does not permit arbitrage. The *stochastic-volatility-inspired* (SVI) parameterization is the industry standard for a single-maturity slice. This section states it, calibrates it to a real SPX chain step by step with our own least squares, checks it rigorously for butterfly and calendar arbitrage, shows what a bad fit looks like, and connects the fitted slice to local volatility and greeks.

### 8.1 The raw SVI parameterization

SVI parameterizes the *total implied variance* of a slice — w(k) = σ_BS(k)²·T, the Black–Scholes implied variance times time to expiry — as a function of *log-moneyness* k = ln(K/F), where F is the forward. Gatheral's raw form is (Gatheral & Jacquier 2014):

```
w(k) = a + b · ( ρ·(k − m) + √( (k − m)² + σ² ) )
```

with five parameters: a shifts the overall level, b ≥ 0 sets the slope of the wings, ρ ∈ (−1, 1) tilts the smile (the skew), m translates it horizontally, and σ > 0 controls the curvature at the bottom. The functional form is a hyperbola: linear in k far in each wing, smoothly rounded near the money. It is flexible enough to fit an equity smile tightly and rigid enough to extrapolate the wings sensibly, which is why it displaced ad-hoc polynomial fits. The total variance w(k) is the natural object rather than the volatility itself because the no-arbitrage conditions are cleanest in variance-and-time units. The asymptotic wing slopes of total variance are b·(1 − ρ) on the left and b·(1 + ρ) on the right, and Roger Lee's moment formula bounds those slopes — neither may exceed 2 — a constraint the wings must respect to be free of arbitrage in the extreme tails.

A warning that will become a theme: the raw parameters are *not individually interpretable*, and worse, they are not even uniquely identified from a single slice. This is a known pathology, not a fitting error, and Gatheral and Jacquier introduced alternative "natural" and "jump-wings" parameterizations precisely because the raw parameters trade off against one another along a nearly flat valley (Gatheral & Jacquier 2014). We return to this in Section 8.3.

### 8.2 The calibration pipeline, step by step

We calibrate to the cached Cboe SPX snapshot (2026-09-17, spot 7,638), fitting the expiry nearest 30 days — the 29-day slice expiring 2026-10-16, the VIX-horizon maturity — with 357 out-of-the-money strikes across log-moneyness −0.246 to +0.095. The pipeline is five deliberate steps:

1. **Select the slice.** One expiry, out-of-the-money quotes only (puts below spot, calls above), positive implied vol and positive bid, restricted to a liquid strike band (0.78–1.10 of spot). Log-moneyness is computed against spot as a proxy for the forward; the shift parameter m absorbs the small spot–forward offset.
2. **Convert to total variance.** For each strike, w_mkt = (IV)²·T, with T in years.
3. **Fit by least squares.** Minimize the sum of squared *implied-volatility* residuals (in vol points, the units we ultimately report) over the five parameters, with positivity imposed by reparameterization (b = e^β, σ = e^s, ρ = tanh) and a self-contained Nelder–Mead simplex — no scipy. Multiple starting points guard against local minima.
4. **Regularize the degeneracy.** Add a light penalty on the wing amplitude b and a centering of the vertex m toward the money, which is negligible against the data term but forbids the runaway of Section 8.3 and selects the natural, interior solution.
5. **Report the fit and its derived quantities.** Because the raw parameters are uninformative, report the interpretable *jump-wings* quantities the curve implies.

The fit is excellent: RMSE 0.144 volatility points across 357 strikes, worst single-strike error 0.28 vol points. The raw parameters are a = −0.018, b = 0.090, ρ = +0.185, m = +0.082, σ = 0.212 — and, true to Section 8.1, they are close to uninterpretable. The *derived* quantities are what a human reads: an at-the-money implied volatility of 12.3% (consistent with the surface paper's ~12% 30-day ATM), an at-the-money skew ∂σ/∂k ≈ −0.81 volatility points per 1% of log-moneyness (a pronounced, correctly-signed *put* skew), a smile vertex at k* = +0.042 (the minimum-variance strike sits just above spot, exactly the surface paper's observation that the smile floor rides near the forward), and total-variance wing slopes of 0.073 (left) and 0.107 (right). The skew is unambiguously negative — the equity put skew — even though the raw ρ came out slightly *positive*, which is the identifiability point of the next subsection made numerical.

Panel (a) of Figure 5 shows the fitted curve threading the observed OTM implied vols with the RMSE reported in the title.

![Raw-SVI calibration to the SPX 2026-10-16 slice (29 days, 357 OTM strikes, RMSE 0.14 vol points), from the cached Cboe delayed-quotes snapshot, fitted by own least squares. Panel (a): Cboe implied vols (dots) and the SVI fit (line) against log-moneyness. Panel (b): the Gatheral–Jacquier butterfly function g(k), which stays positive across the traded strikes (min +0.041, shaded band), so the slice is free of butterfly arbitrage over the quoted range; it dips below zero only in the extrapolated call wing beyond the traded strikes — standard raw-SVI wing behaviour, not a defect of the fit. Reproduce with figures/fig_svi_fit.py.](figures/fig_svi_fit.png)

### 8.3 The identifiability pathology, honestly

A single SVI slice is over-parameterized, and pretending otherwise produces nonsense. Fitting the five raw parameters by unconstrained least squares to this slice, the optimizer runs off toward the boundary — b grows, ρ → 1, m drifts to a spurious +0.4 — while the fitted *curve over the traded strikes barely changes* and the RMSE improves only in the fourth decimal. The reason is that the smile's asymmetry can be represented either by a negative ρ (a tilted hyperbola centered near the money) or by a positive ρ with the vertex m shoved far to one side, and the data over a finite, one-sided strike range cannot distinguish the two: they are the same curve. This is exactly why Gatheral and Jacquier introduced parameterizations whose parameters *are* interpretable (Gatheral & Jacquier 2014).

The disciplined response is not to report a boundary solution and call it a calibration, but to (a) regularize — a light penalty on the wing amplitude and a centering of the vertex, which selects the natural interior point without materially affecting the fit — and (b) report the *derived* quantities (ATM level, ATM skew, vertex, wing asymptotics) that are invariant across the degenerate valley, rather than the raw quintuple (a, b, ρ, m, σ) that is not. The lesson generalizes beyond SVI: when a model is not identified, the honest output is the set of quantities the data actually constrain, and quoting an unidentified raw parameter as if it were "the skew" is a category error that a good desk-quant spots instantly.

The interpretable quantities themselves are what Gatheral's *jump-wings* parameterization is built from, and it is worth naming them because they are what we report: the at-the-money total variance (level), the at-the-money skew ∂w/∂k (tilt), the minimum total variance the slice attains, and the two asymptotic wing slopes — the left slope b·(1 − ρ) and the right slope b·(1 + ρ) — which govern the deep-put and deep-call behavior. Every one of these is a function of the raw quintuple, but unlike the raw parameters each is stable across the degenerate valley and each has an unambiguous market meaning; the jump-wings form simply re-parameterizes SVI so that these five quantities *are* the parameters, which is why it is the form a human calibrates and reads. For a full surface, the *SSVI* (surface SVI) parameterization goes one step further, tying the individual slices together through a single at-the-money-variance term-structure curve and one skew function, which both reduces the parameter count and makes calendar-arbitrage-freeness enforceable by construction — the natural next step once the single-slice pathology is understood.

### 8.4 Butterfly and calendar arbitrage checks

A fit that interpolates the quotes but permits arbitrage is worse than useless, because it will be picked off. Two no-arbitrage conditions must hold, and both have clean tests (Gatheral & Jacquier 2014).

*Butterfly* arbitrage is the absence of a negative risk-neutral density — a butterfly spread must never have negative value. The condition is expressed through Durrleman's function, with w' and w'' the first and second derivatives of total variance in k:

```
g(k) = ( 1 − k·w'(k)/(2·w(k)) )²  −  ( w'(k)²/4 )·( 1/w(k) + ¼ )  +  w''(k)/2
```

which is proportional to the implied risk-neutral density: the slice is free of butterfly arbitrage if and only if g(k) ≥ 0 for all k (and w > 0). For raw SVI the derivatives are analytic — with S = √((k−m)² + σ²), one has w'(k) = b·(ρ + (k−m)/S) and w''(k) = b·σ²/S³ — so g(k) is computed exactly and scanned on a dense grid. For our fitted slice the minimum of g over the *traded* strikes (and a small extrapolation beyond them) is +0.041, attained at the right edge near k = +0.145, so the slice carries *no butterfly arbitrage over the range that is actually quoted*. It is **not**, however, strictly positive everywhere: push the scan deep into the extrapolated call wing and g turns negative — for these fitted parameters it dips below zero from about k ≈ +0.18 to k ≈ +0.52, reaching roughly −0.05 near k ≈ +0.31. That is exactly where the paragraph's own caveat points — the right edge, in the extrapolated call wing beyond the traded strikes — and it is the standard raw-SVI wing behaviour catalogued in Section 8.5: a property of the *extrapolation*, not a defect of the calibrated slice, and it would matter only if one priced options at strikes the market never quoted. Panel (b) of Figure 5 therefore shows g(k) positive across the shaded traded strikes and dipping below zero only out in the extrapolated wing. Read the certificate as "no butterfly arbitrage across the traded strikes," not as a global statement about the density in the untraded wing.

*Calendar* arbitrage is the requirement that total variance be non-decreasing in maturity at every fixed log-moneyness — a longer-dated option can never imply less total variance than a shorter-dated one at the same k, or a calendar spread would have negative value. This is a condition *across* slices, so we check it model-free on the strikes shared by the fitted 29-day slice and the next-longer 92-day slice: over 275 shared strikes, the smallest gap w_92(k) − w_29(k) is +0.0019 — positive everywhere, so total variance is non-decreasing and there is *no calendar arbitrage* between the two maturities. A full surface calibration would enforce this jointly across all maturities, typically by fitting the slices sequentially from near to far with the monotonicity as a constraint, or by adopting the SSVI form of Section 8.3 that guarantees it.

### 8.5 A failure gallery

Knowing what a good fit looks like is only half the skill; recognizing a bad one is the other half. The characteristic SVI failure modes, each with its symptom and cure:

- **Negative density in the wings.** g(k) dips below zero, almost always in an extrapolated wing beyond the traded strikes, when b and ρ are pushed to make the wing too steep. Symptom: a min g(k) < 0; cure: constrain the wing slope b·(1 ± ρ) (respect Lee's bound of 2) or refit with the no-arbitrage constraint active.
- **The unidentified boundary fit of Section 8.3.** RMSE looks perfect, but ρ has hit ±1 and m has run off; the "calibration" is a point on a flat valley, and tomorrow's snapshot will produce wildly different raw parameters for an almost identical smile. Symptom: parameters at the boundary and unstable day-to-day; cure: regularize and report derived quantities.
- **Overfitting illiquid quotes.** Forcing the curve through deep out-of-the-money strikes with wide bid–ask spreads and unreliable Cboe-reported IVs bends the whole slice to fit noise. Symptom: a wiggly fit with a low RMSE dominated by a few far strikes; cure: restrict to a liquid band (as we did, 0.78–1.10 of spot) and weight by liquidity or vega.
- **Calendar crossings.** Two independently-fitted slices cross, w_far(k) < w_near(k) somewhere. Symptom: a negative shared-strike gap; cure: fit slices jointly or sequentially with the monotonicity constraint.

The meta-lesson is that *a low RMSE is necessary but nowhere near sufficient*. A fit that nails every quote and permits arbitrage is a liability; a fit with a slightly higher RMSE that is provably arbitrage-free is the one to ship.

### 8.6 From fitted surface to local volatility and greeks, with error bars

A calibrated, arbitrage-free surface is the input to the two things a desk actually needs. First, *local volatility*: Dupire's formula inverts a complete arbitrage-free surface of European option prices into the unique local volatility function σ_loc(K, T) — the instantaneous volatility as a function of spot and time — that reproduces every quoted price, expressed through the surface's first calendar derivative and its first two strike derivatives (Dupire 1994; Gatheral & Jacquier 2014). This is why the no-arbitrage checks are not academic niceties: Dupire's denominator is essentially g(k), so a surface with g(k) < 0 produces a *negative* (imaginary) local variance and the whole construction collapses. Butterfly-freeness is the precondition for a usable local-vol model, and calendar-monotonicity is the precondition for the time derivative in Dupire's numerator to have the right sign.

Second, *greeks*. The fitted smile gives implied volatility — and its strike and maturity derivatives — at every point, which feeds the vanna and volga (the second-order volatility greeks) that the surface paper connected to dealer hedging flows. A smooth, arbitrage-free skew is what makes those cross-derivatives stable enough to hedge on; a jagged or arbitrageable fit produces greeks that flip sign between adjacent strikes and are useless for risk.

And the honest coda: *error bars.* The fitted parameters carry estimation uncertainty from the finite, noisy set of quotes, and that uncertainty propagates into local volatility and every greek derived from it. The wings, where quotes are sparse and spreads wide, are the least certain part of the surface, and any greek that depends on the wing curvature — precisely the tail-sensitive ones — inherits the largest error bars. A calibration reported without an honest statement of where the surface is well-determined (near the money, many liquid quotes) and where it is a smooth guess (the wings, few noisy quotes) is overstating what the data support — the same discipline that runs through every section of this paper, now applied to the last tool in the kit.

## 9 Reproducibility appendix

Every number in this paper is regenerable with the accompanying scripts from free, publicly retrievable sources — Yahoo Finance, FRED, and the CBOE public delayed-quotes chain — with no paid or subscription inputs. Note, though, that "freely retrievable" is not the same as "redistributable": the scripts re-fetch the vendor inputs at run time rather than the repository redistributing raw CBOE quotes (see the repository DATA-LICENSE note). This appendix states the full pipeline so a reader can reproduce it end to end.

**Environment.** Python with numpy and matplotlib only — no pandas, no scipy, no statistics packages. Every estimator, likelihood, optimizer, and test is implemented in the figure scripts themselves: the GARCH and SVI fits use a hand-written Nelder–Mead simplex, the standard-normal CDF for the test p-values is computed via `math.erf`, and the HAR regressions use `numpy.linalg.solve` on the normal equations. This is a deliberate constraint: it keeps the numerical content auditable and the results independent of any package's internal defaults.

**Data provenance.** Five cached free sources, all under `figures/data/`: daily S&P 500 OHLC (`spx_ohlc.csv`) and daily closes (`spx_daily.csv`) from Yahoo Finance's public chart API; VIX daily closes (`vixcls.csv`) from FRED (VIXCLS); the VIX/VIX3M complex from Cboe's published history; and one SPX option-chain snapshot (`SPX_options_snapshot.json`, 2026-09-17) from Cboe's public delayed-quotes feed. All are cached so the figures re-render offline; nothing is re-downloaded at build time.

**The pipeline, in five stages, one script each:**

1. **Estimators (Section 2).** `fig_rv_estimators.py` reads the OHLC cache, computes the five estimators on a rolling 21-day window, and prints the mean levels, ratios to close-to-close, and lag-1 autocorrelations.
2. **GARCH (Section 3).** `fig_garch_fit.py` reads the closes, demeans the returns, and fits GARCH(1,1) and GJR by own QMLE, printing ω, α, β, persistence, half-life, long-run vol, and the likelihood-ratio statistic.
3. **HAR horse race (Section 4–Section 5).** `fig_har_oos.py` builds the daily realized-variance proxy, runs the expanding-window random-walk / GARCH / log-HAR forecasts, and prints the QLIKE and MSE losses, the Mincer–Zarnowitz regressions, and the Diebold–Mariano and Clark–West statistics.
4. **Variance risk premium (Section 6).** `fig_vrp.py` inner-joins VIX to the daily S&P closes, computes the forward 21-day realized variance and the premium, and prints the full-sample / in-sample / out-of-sample means, Newey–West t-statistics, hit shares, and the deepest inversions.
5. **SVI (Section 8).** `fig_svi_fit.py` parses the option snapshot, calibrates raw SVI to the ~30-day slice by regularized least squares, computes Durrleman's g(k) analytically, checks calendar monotonicity against the next slice, and prints the parameters, derived quantities, RMSE, and min g(k).

**Pre-registration and honesty.** The forecasting and variance-risk-premium studies were run under protocols fixed before any out-of-sample number was examined: one out-of-sample split date (2 January 2020) used throughout, one primary loss per study (QLIKE for forecasting, the Newey–West t on the mean for the premium), and results reported as computed — including the loss-dependent forecasting ranking of Section 5.3 and the insignificant out-of-sample premium t of Section 6.3. No thresholds were searched; the SVI regularization was chosen for identifiability, not to improve the fit, and its effect is reported as the RMSE. Where a number is uncomfortable, it is in the paper.

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| Five realized-volatility estimators on 15 years of S&P OHLC: close-to-close 14.35% versus Yang–Zhang 12.54%, range estimators biased low by the overnight gap | Own reproducible computation — `figures/fig_rv_estimators.py` |
| Own maximum-likelihood GARCH(1,1)/GJR fit: persistence 0.960, half-life 16.8 days, GJR leverage γ ≫ α, asymmetry ≈9.7× (likelihood ratio 141.6) | Own reproducible computation — `figures/fig_garch_fit.py` |
| Out-of-sample forecasting horse race: QLIKE HAR 0.377 < GARCH 0.405 < random walk 0.685, with MSE reversing the HAR/GARCH order | Own reproducible computation — `figures/fig_har_oos.py`; OOS split |
| Variance risk premium +6.98 %²/month, 84.6% hit rate, ~3.7 vol points; in-sample t 7.31 but out-of-sample t only 0.92 | Own reproducible computation — `figures/fig_vrp.py`; OOS split |
| Raw-SVI calibration to a 29-day SPX slice: RMSE 0.14 vol points, butterfly g(k) ≥ 0 across the traded strikes (min +0.041; g dips < 0 only in the extrapolated call wing), no calendar arbitrage | Own reproducible computation — `figures/fig_svi_fit.py` |
| OHLC range estimators (Parkinson, Garman–Klass, Rogers–Satchell, Yang–Zhang) and their bias and efficiency | Literature — (Parkinson 1980; Garman & Klass 1980; Rogers & Satchell 1991; Yang & Zhang 2000) |
| Summed intraday squared returns converge to integrated variance; bipower variation isolates jumps; microstructure noise caps sampling frequency | Literature — (Andersen, Bollerslev, Diebold & Labys 2003; Barndorff-Nielsen & Shephard 2004; Zhang, Mykland & Aït-Sahalia 2005) |
| The GARCH/GJR/EGARCH conditional-variance models with leverage asymmetry, and HAR-RV as a long-memory approximation | Literature — (Bollerslev 1986; Glosten, Jagannathan & Runkle 1993; Corsi 2009) |
| Proxy-robust loss (QLIKE) and predictive-accuracy tests (Diebold–Mariano, Clark–West, Mincer–Zarnowitz) | Literature — (Patton 2011; Diebold & Mariano 1995; Clark & West 2007) |
| The variance risk premium as model-free insurance compensation that also predicts equity returns | Literature — (Carr & Wu 2009; Bollerslev, Tauchen & Zhou 2009) |
| The SVI no-arbitrage parameterization (butterfly/calendar criteria) and Dupire local volatility | Literature — (Gatheral & Jacquier 2014; Dupire 1994) |
| In volatility carry, turnover times per-trade cost frequently exceeds the gross contango carry, so raw carry is largely frictions plus crash risk | Practitioner consensus — not independently verified |

## References

- Andersen, T. G., Bollerslev, T., & Diebold, F. X. (2007). Roughing it up: Including jump components in the measurement, modeling, and forecasting of return volatility. *Review of Economics and Statistics, 89*(4), 701–720. — Introduces the jump/continuous decomposition and the HAR-J forecasting extension used in Section 2.7 and Section 4.3.
- Andersen, T. G., Bollerslev, T., Diebold, F. X., & Labys, P. (2003). Modeling and forecasting realized volatility. *Econometrica, 71*(2), 579–625. — The foundational realized-variance paper establishing that summed intraday squared returns estimate integrated variance.
- Barndorff-Nielsen, O. E., & Shephard, N. (2004). Power and bipower variation with stochastic volatility and jumps. *Journal of Financial Econometrics, 2*(1), 1–37. — Develops bipower variation, the jump-robust measure that separates continuous from discontinuous variance.
- Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity. *Journal of Econometrics, 31*(3), 307–327. — The original GARCH paper, adding a lagged-variance term to ARCH; the model derived and fitted in Section 3.
- Bollerslev, T., Tauchen, G., & Zhou, H. (2009). Expected stock returns and variance risk premia. *Review of Financial Studies, 22*(11), 4463–4492. — Shows the variance risk premium predicts equity returns and frames it as a state variable; the basis of Section 6.4.
- Carr, P., & Wu, L. (2009). Variance risk premiums. *Review of Financial Studies, 22*(3), 1311–1341. — The model-free definition and cross-market evidence of the variance risk premium as compensation for volatility risk (Section 6.1–Section 6.2).
- Clark, T. E., & West, K. D. (2007). Approximately normal tests for equal predictive accuracy in nested models. *Journal of Econometrics, 138*(1), 291–311. — The nested-model forecast-comparison test used for HAR versus the random walk in Section 5.3.
- Corsi, F. (2009). A simple approximate long-memory model of realized volatility. *Journal of Financial Econometrics, 7*(2), 174–196. — Introduces the HAR-RV cascade; the workhorse forecaster of Section 4 (widely available open-access preprint).
- Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. *Journal of Business & Economic Statistics, 13*(3), 253–263. — The canonical test of equal predictive accuracy between two forecasts (Section 5.2–Section 5.3).
- Dupire, B. (1994). Pricing with a smile. *Risk, 7*(1), 18–20. — Derives the local-volatility function that reproduces an arbitrage-free surface; the destination of Section 8.6.
- Engle, R. F. (1982). Autoregressive conditional heteroscedasticity with estimates of the variance of United Kingdom inflation. *Econometrica, 50*(4), 987–1007. — The ARCH paper that began conditional-variance modeling (Section 3.1).
- Garman, M. B., & Klass, M. J. (1980). On the estimation of security price volatilities from historical data. *Journal of Business, 53*(1), 67–78. — The OHLC range estimator combining range and close for higher efficiency (Section 2.3).
- Gatheral, J., & Jacquier, A. (2014). Arbitrage-free SVI volatility surfaces. *Quantitative Finance, 14*(1), 59–71. Open access: <https://arxiv.org/abs/1204.0646>. — The SVI parameterization, the butterfly criterion g(k), and the calendar condition; the entire basis of Section 8.
- Glosten, L. R., Jagannathan, R., & Runkle, D. E. (1993). On the relation between the expected value and the volatility of the nominal excess return on stocks. *Journal of Finance, 48*(5), 1779–1801. — The GJR-GARCH asymmetry term for the leverage effect (Section 3.3).
- Hansen, P. R., & Lunde, A. (2006). Realized variance and market microstructure noise. *Journal of Business & Economic Statistics, 24*(2), 127–161. — Documents the microstructure-noise bias and the volatility signature plot (Section 2.6).
- Mincer, J., & Zarnowitz, V. (1969). The evaluation of economic forecasts. In J. Mincer (Ed.), *Economic Forecasts and Expectations* (pp. 3–46). New York: NBER. Open access: <https://www.nber.org/books-and-chapters/economic-forecasts-and-expectations-analysis-forecasting-behavior-and-performance>. — The forecast-optimality regression (intercept 0, slope 1) used in Section 5.3.
- Nelson, D. B. (1991). Conditional heteroskedasticity in asset returns: A new approach. *Econometrica, 59*(2), 347–370. — The EGARCH model of log-variance with unconstrained asymmetry (Section 3.3).
- Parkinson, M. (1980). The extreme value method for estimating the variance of the rate of return. *Journal of Business, 53*(1), 61–65. — The high–low range estimator of daily variance (Section 2.3).
- Patton, A. J. (2011). Volatility forecast comparison using imperfect volatility proxies. *Journal of Econometrics, 160*(1), 246–256. — Establishes which loss functions rank forecasts consistently under a noisy proxy; the basis for using QLIKE in Section 5.
- Rogers, L. C. G., & Satchell, S. E. (1991). Estimating variance from high, low and closing prices. *Annals of Applied Probability, 1*(4), 504–512. — The drift-independent range estimator (Section 2.3).
- Yang, D., & Zhang, Q. (2000). Drift-independent volatility estimation based on high, low, open, and close prices. *Journal of Business, 73*(3), 477–491. — The estimator that adds the overnight term to become unbiased and efficient (Section 2.3–Section 2.4).
- Zhang, L., Mykland, P. A., & Aït-Sahalia, Y. (2005). A tale of two time scales: Determining integrated volatility with noisy high-frequency data. *Journal of the American Statistical Association, 100*(472), 1394–1411. — The two-scales noise-robust realized-variance estimator (Section 2.6).

*All references above are publicly accessible: two carry direct open-access links (Gatheral & Jacquier on arXiv; Mincer & Zarnowitz at the NBER), and the remainder are peer-reviewed journal articles available through standard academic channels. No proprietary, vendor, course, or trading-academy material is cited; all empirical numbers are recomputed from free data.*
