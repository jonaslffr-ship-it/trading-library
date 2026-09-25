---
title: "Machine Learning for Strategy Building"
last_updated: 2026-09-20
---

# Machine Learning for Strategy Building

## Abstract

A machine-learning model applied to markets is, by default, a machine for manufacturing overfit: given enough capacity and enough tries, it will fit the past perfectly and predict the future not at all. This paper is about the discipline that turns that default into something occasionally useful. We start from what machine learning actually is for a trader — supervised learning of a target from features — and argue that finance is the hardest domain that discipline is ever asked to work in: a signal-to-noise ratio near zero, a data-generating process that changes while you study it, and a sample that is far smaller than its row count suggests. We then draw the two pictures that matter. In the first, a gradient-boosted classifier predicting the sign of tomorrow's S&P 500 return is given rising capacity; its in-sample Sharpe ratio climbs from below two to thirteen — a perfect in-sample fit — while its out-of-sample Sharpe never leaves the neighbourhood of a coin flip. The widening gap between the two curves *is* overfitting, drawn on free data. In the second, two thousand strategies with no edge whatsoever, by construction, are searched for the best in-sample Sharpe; the winner posts a Sharpe of 0.90 and an out-of-sample Sharpe of 0.04, and the correlation between in-sample and out-of-sample performance across all two thousand is +0.02 — indistinguishable from nothing. Around these pictures we assemble the honest workflow: leakage-free pipelines, cross-validation that respects time, and a mandatory deflation gate (the deflated Sharpe ratio and the probability of backtest overfitting) before any result is believed. The conclusion is not that machine learning has no place in trading, but that it is a servant of an economic hypothesis and never a substitute for one. Every figure is reproducible from free data.

## Keywords

Machine learning, overfitting, out-of-sample, data leakage, purged cross-validation, deflated Sharpe ratio, probability of backtest overfitting, multiple testing, feature importance, non-stationarity, gradient boosting, calibration

## 1 Introduction

### 1.1 Motivation and thesis

There is a version of machine learning in trading that is pure fantasy: feed a flexible model enough price history and enough features, and it will discover the hidden structure of the market and print money. The reason this fantasy is so durable is that its first half is trivially achievable — a modern model *can* fit the past perfectly — and the gap between fitting the past and predicting the future is invisible until you go looking for it. This paper's job is to make that gap visible, measure it on free data, and lay out the discipline that is the only thing standing between a machine-learning pipeline and expensive self-deception.

The thesis is blunt: *applied naively to markets, machine learning is a machine for manufacturing overfit, and the entire value of a machine-learning practitioner in this domain is the discipline they impose to stop it.* The algorithms are commodities — a gradient-boosting library is a `pip install` away, and it will happily hand you a backtest with a Sharpe ratio of thirteen. What is scarce, and what this paper is about, is the set of habits that separate a result which will survive contact with the future from one that is an artefact of the search: leakage-free data handling, cross-validation that respects the arrow of time, a correction for the number of things you tried, and — above all — an economic reason for the model to work that was written down *before* the model was trained. Machine learning does not lift the burden of having a hypothesis; it multiplies the number of ways you can fool yourself into thinking you have one.

### 1.2 Scope, prerequisites, and intended reader

This paper sits in the Trading Library's *Strategy & Applications* track, and it leans hard on two earlier documents: the backtesting paper (pre-registration, the out-of-sample split, the failure catalogue) and the overfitting-control paper (the deflated Sharpe ratio, the probability of backtest overfitting, calibration scoring), whose tools are used here as a ready-made validation suite rather than re-derived. It assumes the reader can read a short Python computation using a standard machine-learning library and is comfortable with the idea of training and test sets. It does not assume prior machine-learning expertise; the concepts it needs — supervised learning, capacity, the bias-variance trade-off, cross-validation — are introduced from scratch, in the specific and unusually hostile context of financial data.

After reading this paper, a reader can:

- frame a trading idea as a supervised-learning problem, and explain why finance is a uniquely hostile domain for it (low signal-to-noise, non-stationarity, small effective sample);
- recognise the overfitting gap between in-sample and out-of-sample performance, and reproduce it;
- identify the leakage that silently invalidates most machine-learning backtests, and build a pipeline that avoids it;
- run cross-validation that respects time (purging and embargo) instead of the standard k-fold that leaks;
- apply the deflation gate — the deflated Sharpe ratio and the probability of backtest overfitting — to a search over many models, and read what it says honestly;
- state what machine learning can genuinely add (nonlinear interactions, high-dimensional combination) and what it categorically cannot (create signal from noise, foresee an unseen regime, supply the economic hypothesis).

### 1.3 Data and reproducibility

All numerical examples use freely available data (Yahoo's public chart API for the S&P 500) and are reproducible from the accompanying `figures/*.py` scripts (numpy, matplotlib, and scikit-learn), which cache their downloads. The models are deliberately standard and the demonstrations deliberately simple, so that the *methodology*, not a clever architecture, is what carries the argument. *This is a research and educational document, not investment advice.*

### 1.4 Organization of this paper

Section 2 defines machine learning for a trader and explains why finance is the hardest place to do it. Section 3 draws the central picture — the overfitting gap — on free data (Figure 1). Section 4 catalogues the data-pipeline landmines, of which leakage is the fatal one. Section 5 fixes cross-validation so that it respects time. Section 6 is the validation gate: multiple testing, the deflated Sharpe ratio, and the probability of backtest overfitting, demonstrated with two thousand no-edge strategies (Figure 2). Section 7 draws the honest boundary of what machine learning can and cannot do. Section 8 assembles the disciplined workflow end to end. Section 9 closes with misconceptions, a glossary, and references.

## 2 What machine learning actually is — and why finance is the hardest place to use it

### 2.1 Supervised learning in one paragraph

Almost all machine learning used in trading is *supervised learning*: you assemble a table of *features* (inputs known at decision time — past returns, volatility, volume, fundamentals) and a *target* (the thing to predict — tomorrow's return, its sign, its volatility), and you fit a flexible function that maps features to target by minimising error on a *training* set. The model's *capacity* is how flexible that function is allowed to be — the depth of a decision tree, the number of parameters in a network. The central tension of the whole field is the *bias-variance trade-off*: too little capacity and the model cannot capture real structure (bias); too much and it captures the noise as if it were structure (variance), fitting the training data beautifully and generalising terribly. Everything in this paper is a consequence of that trade-off being catastrophically hard to manage in markets.

### 2.2 Why markets are the adversarial case

Machine learning earned its reputation in domains — image recognition, language — where the signal-to-noise ratio is high, the data-generating process is stable, and labelled examples are effectively unlimited. Finance is the mirror image of all three. The *signal-to-noise ratio* is near zero: the predictable component of a daily return is a whisper under a roar of noise, so a model has almost nothing to learn and enormous latitude to hallucinate. The process is *non-stationary*: the market adapts, regimes change, and a relationship that held in-sample can be gone — or reversed — out of sample, so the very premise of supervised learning (that train and test are drawn from the same distribution) is violated by construction. And the *effective sample* is tiny: twenty years of daily data is only ~5,000 rows, and because returns are serially dependent and regime-clustered, the number of genuinely independent observations is far smaller still — a dataset that looks large and behaves small. A method built for millions of independent, high-signal examples, applied to thousands of dependent, near-noise ones, will do what it was built to do: fit. The question is only whether you will notice.

## 3 The overfitting trap, demonstrated

The abstract danger becomes concrete the moment you actually run it. We train a *gradient-boosted classifier* — a standard, powerful workhorse — to predict the sign of the S&P 500's next-day return from twenty features: six genuine ones (lagged returns, a momentum term, two realized-volatility terms) and fourteen columns of *pure random noise*, added on purpose. We then sweep the model's capacity through its tree depth and, at each setting, measure the annualized Sharpe ratio of the resulting daily long/short strategy on the in-sample data the model was fit on, and on a later out-of-sample period the model never saw.

![A gradient-boosted classifier predicting the sign of the next-day S&P 500 return, as its capacity (tree depth) rises. The in-sample Sharpe ratio (red) climbs from 1.7 to 13.0 - at depth 8 the model classifies the training data with 100% accuracy - while the out-of-sample Sharpe (blue) never leaves the region of no skill — below even the always-long baseline (dashed green line, Sharpe 0.62) — and out-of-sample accuracy stays near 52%, under the 54.5% majority-class "always predict up" baseline. The shaded region between the curves is the overfitting gap: all of the apparent performance is memorisation of the training set, none of it generalises. Yahoo GSPC daily, 2004-2026, 6 genuine + 14 noise features; out-of-sample from 2018.](figures/fig_g3_overfit.png)

The result is the whole paper in one chart. At the lowest capacity the in-sample Sharpe is already a flattering 1.7 and the out-of-sample Sharpe a limp 0.2. As capacity rises the in-sample Sharpe rockets — 3.7, 6.8, 9.5, and finally **13.0**, at which point the model classifies the training set with *100 % accuracy*, having simply memorised it, noise columns and all. And the out-of-sample Sharpe? It never leaves the neighbourhood of zero; out-of-sample accuracy sits stuck near **52 %** — and the honest benchmark for a *directional* call is not a 50 % coin flip but the **majority-class baseline**: on the out-of-sample window used here up-days run about **54.5 %**, so "always predict up" already scores 54.5 %. At 52 % the classifier is therefore doing *worse than the trivial always-long rule* — whose out-of-sample Sharpe of 0.62 the model never approaches — not squeaking past a coin flip. Measured against the only benchmark that matters for a directional call, its skill is *negative*. Every bit of the spectacular in-sample performance is overfitting — the shaded gap between the curves is the visual definition of the word. Note especially what capacity bought: not a better model, but a more confident illusion. The fourteen noise features, which by construction contain nothing, were woven into a perfect in-sample story. This is the default behaviour the rest of the paper exists to prevent, and it is why the single most important number in any machine-learning trading result is the one measured on data the model has never touched.

## 4 The data pipeline and its landmines

If Section 3 is the disease, the pipeline is where most of the infection enters. The great majority of machine-learning trading results that look wonderful and fail live are not undone by the model at all — they are undone in the data preparation, and usually by one specific error.

### 4.1 Leakage: the cardinal sin

*Leakage* is the use, anywhere in the pipeline, of information that would not have been available at the moment of decision — and it is the single most common reason a backtest lies. It creeps in through a hundred doors: scaling or imputing features using statistics computed over the *whole* dataset (so the training rows "know" the test set's mean); constructing a label from data that overlaps the feature window; using a fundamental figure on the date it *refers to* rather than the later date it was *published*; joining a "point-in-time" database that has been silently revised. Every one of these lets the model peek at the future, and the symptom is always the same — a backtest far better than anything achievable live. The defence is a discipline, not a tool: every transformation must be fit on training data only and applied to test data, and every feature must be stamped with the time it was genuinely knowable.

### 4.2 Labels and features that respect time

Two subtler pipeline choices decide whether a financial machine-learning problem is even well-posed. Labelling — turning a price path into a target — is not obvious: a fixed-horizon "return over the next N days" label mixes signal across overlapping windows and ignores the path in between, which is why practitioners use path-aware schemes such as the *triple-barrier* method (label by whichever of a profit target, a stop, or a time limit is hit first). And overlapping labels create *serial dependence* in the target that ordinary cross-validation treats as independent information, inflating apparent performance — the problem Section 5 exists to fix. The theme is constant: in a domain this close to noise, the way you frame the question leaks or protects more edge than the model you choose to answer it.

## 5 Cross-validation that isn't a lie

Cross-validation is how machine learning estimates out-of-sample performance without spending its precious hold-out set, and the standard recipe is actively dangerous in finance. Ordinary *k-fold* cross-validation shuffles rows into folds at random, training on some and testing on others. With time-series data this is leakage by design: a randomly chosen test day is surrounded by training days from immediately before and after it, so the model is tested on a point whose near-neighbours — highly correlated with it — it has already seen. The estimate that results is optimistic, sometimes wildly so.

The fix has two parts, both from the overfitting-control paper. *Walk-forward* validation trains on the past and tests on the strictly-later future, preserving the arrow of time — the honest default. *Purged k-fold with an embargo* is its more data-efficient cousin: when a test fold is carved out, the training observations whose label windows *overlap* the test period are *purged* (removed), and a short *embargo* is imposed after the test period before training resumes, so that serial dependence cannot carry information across the boundary. The rule underneath both is the one the whole library repeats: the out-of-sample estimate is only worth as much as the care taken to ensure the model could not, by any path, have seen the answer.

## 6 The validation gate: multiple testing and deflation

Even a leakage-free pipeline with honest cross-validation is not enough, because of the problem that defines machine-learning research: you do not try one model, you try *many*, and you keep the best. That search is itself a form of overfitting, and it must be paid for.

### 6.1 The best of many is a lie

We demonstrate the multiple-testing problem in its purest form. We generate two thousand trading strategies with *no edge whatsoever by construction* — each is a random sequence of long/short bets, a fair coin — and score every one on real S&P 500 returns, keeping the best in-sample Sharpe.

![Left: the distribution of in-sample Sharpe ratios from 2000 random long/short strategies that have no edge by construction, on real S&P 500 returns. The best of the 2000 posts a Sharpe of 0.90 - far past the naive single-test 5% significance line (0.44) - purely because the maximum of many noisy estimates is large by chance (the expected maximum under the null is 0.92). Right: each strategy's in-sample Sharpe against its out-of-sample Sharpe; the cloud is round and the correlation is +0.02, so the in-sample number carries essentially no information about out-of-sample performance. The best in-sample strategy delivers an out-of-sample Sharpe of +0.04. Yahoo GSPC daily, in-sample to 2018.](figures/fig_g3_dsr.png)

The result is decisive. The best of the two thousand no-edge strategies posts an in-sample Sharpe of **0.90** — comfortably past the *naive* single-test significance line of 0.44, the threshold you would use if this were the only strategy you had tested. But it is not the only one; it is the best of two thousand, and the *expected* maximum of two thousand pure-noise Sharpes is **0.92**, so a 0.90 is not even surprising given the search — it lands almost exactly on the null expectation. Its out-of-sample Sharpe is **0.04** — gone. And the right panel delivers the coup de grâce: across all two thousand strategies the correlation between in-sample and out-of-sample Sharpe is **+0.02**, statistically indistinguishable from zero. The in-sample number, the one every naive backtest reports, carries *no information* about the future. This is not a pathology of random strategies; it is the exact mechanism by which a machine-learning search over architectures, features, and hyperparameters manufactures a "discovery."

### 6.2 The deflation gate

The correction is to judge a result not against the single-test threshold but against the distribution of the *best of everything you tried* — which is precisely what the tools from the overfitting-and-calibration paper do. The *deflated Sharpe ratio* (DSR) discounts an observed Sharpe by the number of trials, the length of the track record, and the skew and kurtosis of its returns, answering: is this Sharpe still significant once we account for how hard we looked? The *probability of backtest overfitting* (PBO) estimates, by combinatorial cross-validation, how often the configuration that was best in-sample underperforms out-of-sample — a direct read on whether your selection process is discovering signal or noise. And because a machine-learning model often outputs a *probability*, its calibration must be scored (Brier score, reliability diagrams) rather than assumed. The mandatory gate, before any machine-learning result is believed: the number of configurations tried is logged, the best is deflated, the selection process is stress-tested with PBO, and the out-of-sample window is opened exactly once. A result that cannot survive this gate is not a weak discovery — it is, on the evidence of Figure 2, most likely no discovery at all.

## 7 What machine learning can and cannot do

Honesty about the danger must not curdle into the opposite error — that machine learning is useless here. It is not; it is a sharp tool with a narrow, real edge, and the discipline is knowing where that edge is.

### 7.1 What it genuinely adds

Machine learning earns its place where the structure is *nonlinear* and *high-dimensional* in ways a human specification misses. It can capture *interactions* — an effect that only appears when volatility is high *and* the trend is up *and* liquidity is thin — that a linear model would never find. It can *combine* many weak features into a single signal more gracefully than hand-tuned rules. It can *adapt* weights as conditions change. Where there is genuine, stable, nonlinear structure and enough independent data to pin it down — more often in higher-frequency or cross-sectional problems than in daily index timing — machine learning can extract edge that simpler methods leave behind.

### 7.2 What it categorically cannot do

But it cannot do the three things people most want from it. It cannot *create signal where there is none*: Figure 1's model was offered fourteen noise features and built a perfect in-sample strategy from them, and no algorithm can distinguish that from a real one without out-of-sample evidence. It cannot *foresee a regime it has never seen*: a model trained only on a low-inflation, falling-rate world has no basis whatever for 2022, because supervised learning interpolates within its training distribution and cannot extrapolate beyond it. And it cannot *supply the economic hypothesis* — the reason a relationship should exist and persist once others find it. The seductive "feature importances" a model reports are an *in-sample* decomposition of a possibly-overfit fit; they explain how the model reached its (perhaps worthless) answer, not how the world works, and reading them as economic truth is one of the most common and expensive mistakes in the field. Machine learning is an amplifier: pointed at a real, economically-grounded edge it can sharpen it; pointed at noise it amplifies your capacity for self-deception.

## 8 A disciplined workflow, assembled

The defensive pieces combine into one workflow, and its ordering is the whole point — the economics come first, the machine last.

1. **Hypothesis before model.** Write down, in advance, the economic reason an edge should exist and persist, and the pre-registered test that would confirm or refute it (the backtesting-methodology discipline). A model without a prior hypothesis is a search, and a search must be deflated (Section 6).
2. **Features with priors, not a kitchen sink.** Choose features because theory says they should matter, not because they are available; every superfluous feature is another dimension in which to overfit (Figure 1's noise columns).
3. **A leakage-free, point-in-time pipeline.** Fit every transformation on training data only; stamp every feature with the time it was knowable (Section 4).
4. **Time-respecting validation.** Walk-forward, or purged k-fold with an embargo — never shuffled k-fold (Section 5).
5. **The deflation gate.** Log the number of configurations tried; deflate the best Sharpe (DSR); stress the selection with PBO; score probability calibration; open the out-of-sample set once (Section 6).
6. **Paper-trade, then size from the tail.** Even a survivor is reconciled live against its backtest before real capital, and sized from its worst case, not its average — the position-sizing discipline any live deployment demands.

The workflow is deliberately unglamorous, and that is the message. In a domain this close to noise, the returns to a cleverer algorithm are small and the returns to a more honest process are large. Machine learning belongs in a trader's toolkit as a servant of a hypothesis, wrapped in this discipline — and nowhere else.

## 9 Discussion, misconceptions, glossary, references

### 9.1 Common misconceptions

*"A high backtest Sharpe means the strategy works."* — Not after a search: the best of two thousand no-edge strategies scored 0.90 in-sample and 0.04 out (Section 6). *"More features and more data can only help."* — More features add dimensions to overfit; more *rows* of dependent, non-stationary data add little independent information (Section 2.2, Section 3). *"The model found these features important, so they matter."* — Feature importances are an in-sample decomposition of a possibly-overfit model, not a statement about the world (Section 7.2). *"Cross-validation proved it generalises."* — Only if the cross-validation respected time; shuffled k-fold leaks and lies (Section 5). *"Deep learning will find the pattern humans miss."* — Capacity without discipline finds patterns in noise perfectly (Figure 1); the pattern it "finds" is usually your own search.

### 9.2 Glossary

- **Supervised learning** — fitting a function from features (inputs known at decision time) to a target (the thing predicted) by minimising error on a training set.
- **Capacity** — how flexible a model is allowed to be (tree depth, parameter count); more capacity fits training data better and generalises worse past a point.
- **Bias-variance trade-off** — too little capacity misses real structure (bias); too much fits noise as structure (variance). Managing it is the core problem, and it is brutal in finance.
- **Overfitting** — fitting the training data's noise as if it were signal; visible as a large gap between in-sample and out-of-sample performance (Figure 1).
- **Leakage** — using information not available at decision time (whole-sample scaling, revised data, overlapping labels); the most common cause of a backtest that fails live.
- **Purged k-fold / embargo** — cross-validation that removes training observations overlapping the test window and pauses after it, preventing serial-dependence leakage across the boundary.
- **Deflated Sharpe ratio (DSR)** — a Sharpe ratio discounted for the number of trials, sample length, skew and kurtosis; the significance test for a *searched* result.
- **Probability of backtest overfitting (PBO)** — the estimated probability that the in-sample-best configuration underperforms out of sample; a read on the selection process itself.

### 9.3 References

- López de Prado, M. (2018). *Advances in Financial Machine Learning.* Wiley. [Leakage, triple-barrier labels, purged CV, PBO — the field's core reference.]
- Gu, S., Kelly, B. & Xiu, D. (2020). *Empirical Asset Pricing via Machine Learning.* Review of Financial Studies. [Where ML genuinely adds cross-sectional edge, done honestly.]
- Arnott, R., Harvey, C. & Markowitz, H. (2019). *A Backtesting Protocol in the Era of Machine Learning.* Journal of Financial Data Science. [The disciplined workflow.]
- Bailey, D. & López de Prado, M. (2014). *The Deflated Sharpe Ratio.* Journal of Portfolio Management.
- Bailey, D., Borwein, J., López de Prado, M. & Zhu, Q. (2017). *The Probability of Backtest Overfitting.* Journal of Computational Finance.
- Harvey, C., Liu, Y. & Zhu, H. (2016). *…and the Cross-Section of Expected Returns.* Review of Financial Studies. [Multiple testing in factor research.]
- Hastie, T., Tibshirani, R. & Friedman, J. (2009). *The Elements of Statistical Learning* (2nd ed.). Springer. [Freely available; the bias-variance trade-off and cross-validation.]
- Dixon, M., Halperin, I. & Bilokon, P. (2020). *Machine Learning in Finance.* Springer.
- Gneiting, T. & Raftery, A. (2007). *Strictly Proper Scoring Rules, Prediction, and Estimation.* Journal of the American Statistical Association. [Calibration scoring.]

*All references are publicly accessible: peer-reviewed journal articles (several via open-access working-paper versions) and published books, one of which (Hastie et al.) is freely available online. No proprietary, subscription, or trading-course material is cited.*

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| A gradient-boosted classifier's in-sample Sharpe climbs to 13.0 (100% training accuracy) while out-of-sample it stays ~52% accurate — below the 54.5% majority-class ("always-long") baseline, i.e. worse than no model — the overfitting gap | Own reproducible computation — `figures/fig_g3_overfit.py`; OOS split |
| The best of 2,000 no-edge strategies posts an in-sample Sharpe of 0.90 but an out-of-sample Sharpe of 0.04, and the in-sample/out-of-sample correlation across all 2,000 is +0.02 | Own reproducible computation — `figures/fig_g3_dsr.py`; OOS split |
| Leakage — whole-sample scaling, overlapping labels, revised point-in-time data — is the most common reason a machine-learning backtest fails live | Literature — (López de Prado 2018) |
| Purged k-fold with an embargo and path-aware (triple-barrier) labels prevent the serial-dependence leakage ordinary k-fold ignores | Literature — (López de Prado 2018) |
| The deflated Sharpe ratio discounts an observed Sharpe for the number of trials, track length, skew and kurtosis | Literature — (Bailey & López de Prado 2014) |
| The probability of backtest overfitting estimates how often the in-sample-best configuration underperforms out of sample | Literature — (Bailey, Borwein, López de Prado & Zhu 2017) |
| Searching many candidates inflates the best in-sample Sharpe, so significance must be corrected for the number of trials | Literature — (Harvey, Liu & Zhu 2016) |
| Probabilistic model outputs must be calibration-scored (Brier score, reliability diagrams) rather than assumed | Literature — (Gneiting & Raftery 2007) |
| Machine learning adds genuine edge where structure is nonlinear and high-dimensional, more in higher-frequency and cross-sectional problems than daily index timing | Literature — (Gu, Kelly & Xiu 2020) |
| The disciplined workflow puts the economic hypothesis before the model | Literature — (Arnott, Harvey & Markowitz 2019) |
| A surviving model is paper-traded against its backtest and sized from its worst case before real capital | Practitioner consensus — not independently verified |
