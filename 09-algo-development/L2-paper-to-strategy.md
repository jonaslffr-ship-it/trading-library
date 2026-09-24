---
title: "From Paper to Strategy — Anomalies & Replication"
last_updated: 2026-09-20
---

# From Paper to Strategy — Anomalies & Replication

## Abstract

A published anomaly is a claim about someone else's data, made under someone else's choices; a strategy is a rule you will trade with your own money under your own costs. The distance between the two is where most retail algorithmic effort is quietly lost. This paper is a practitioner's route across that distance. It starts at the funnel's mouth — where the ideas come from — with a concrete method for mining the free literature, above all SSRN, for candidate strategies and triaging that firehose down to the few worth a day's work. It then teaches how to read a quantitative paper as an adversary — separating the load-bearing claim from the marketing, and running a red-flag checklist for in-sample-only results, unrealistic costs, parameter counts, and suspicious sample windows. It then confronts the replication crisis in asset pricing head-on: how many "anomalies" survive careful re-testing, and how predictability decays after publication, and what both imply for a solo researcher with free data. The core discipline is turning prose into an unambiguous, codeable specification and pre-registering the replication before running it — wired directly to the protocol of the companion backtesting paper. A single worked example carries the argument: a faithful, free-data replication of time-series momentum on the S&P 500, scored down a realism ladder of costs, implementation lag, and post-publication sub-period; a parameter-instability study showing why the best in-sample lookback is not a discovery; and a real, anonymized VIX-gate variant presented with the multiple-testing caveat it demands. Every number is reproducible on freely available data.

## Keywords

Anomalies, replication crisis, factor decay, time-series momentum, out-of-sample testing, pre-registration, specification, transaction costs, capacity, data snooping, deflated Sharpe ratio, parameter instability, researcher degrees of freedom, robustness, reproducibility

## 1 Introduction

### 1.1 Motivation and thesis

Every year the finance literature adds dozens of new "factors" and "anomalies," each documented in a paper with a positive alpha, a plausible story, and a chart that curves the right way. The retail algorithmic trader, sensibly, treats these as a free idea generator — and, because almost all of that literature is posted openly on SSRN, arXiv, and the working-paper repositories, one that costs nothing to tap: someone with a data licence and a referee process has already done the hard measurement, so why not simply *code the rule and trade it*? This paper exists because that step — from the paper's claim to your running strategy — is far longer and far more treacherous than it looks, and because the discipline that makes it survivable is teachable.

The gap has three distinct layers, and confusing them is the root of most disappointment. The first is *epistemic*: a surprising fraction of published anomalies do not replicate even on the original kind of data, once the methodology is tightened. The second is *temporal*: of those that were real, many decay sharply once they are published and arbitraged. The third is *operational*: even a genuine, still-alive effect measured in a paper was measured gross of your costs, at a capacity far above what you will trade, often with short sales the paper assumed were frictionless, on data vintages you cannot cleanly reconstruct. A claim can be true in the paper and worthless in your account, and each of these three layers can independently destroy the edge.

The thesis of this paper follows: *the value a published anomaly has to you is not the alpha printed in its abstract; it is whatever survives your own honest replication, your own costs, and your own out-of-sample test — and the disciplined default expectation is that this is a small fraction of the headline, sometimes nothing.* Treating a paper as a hypothesis to be re-tested rather than a result to be trusted is not cynicism; it is the only posture under which the literature becomes genuinely useful rather than a source of expensive false confidence. Everything that follows is machinery for holding that posture without either naive credulity or reflexive dismissal.

### 1.2 Scope, prerequisites, and intended reader

This paper sits in the Trading Library's Algo-Development track. Its pillar is method. It presupposes two companions and leans on both explicitly: the statistics primer (*Statistics for Traders*) for distributions, base rates, expectancy, and standard errors; and above all *Backtesting & Hypothesis Testing*, whose pre-registration protocol, out-of-sample discipline, cost-sensitivity thinking, and direction check this paper treats as prerequisites rather than re-deriving them. Where the backtesting paper taught how to test *your own* idea honestly, this paper teaches how to import *someone else's* idea and subject it to the same test. A reader who has not met that protocol should read at least the backtesting paper's treatment of going from idea to testable hypothesis first; several arguments here are only fully load-bearing with it in hand.

The reader is assumed to be comfortable with a short Python snippet, able to pull a price series from a free source and compute returns, and at ease with a simple formula stated both symbolically and in words. No measure theory, no stochastic calculus, and no paid data are required — every empirical result in this paper is computed on freely available prices.

After reading this paper, a reader can:

- read a quantitative anomaly paper as an adversary: locate the single load-bearing claim, distinguish the sections that carry evidence from the sections that sell, and run a concrete red-flag checklist over it before spending a day on replication;
- state, with numbers, how badly the anomaly literature replicates and how fast published edges decay, and translate both into a prior for their own work;
- convert a paper's prose into an unambiguous, codeable specification — surfacing every implicit choice the authors left unstated and reasoning about how each one moves the result;
- pre-register a *replication* (not just an original study), freezing the specification, split, metric, and decision rule before running it, wired to the backtesting paper's protocol;
- take a replicated result down a realism ladder — gross, then costs, then implementation lag, then a post-publication sub-period — and read honestly what survives;
- derive a defensible *variant* of a replicated base without dressing overfitting up as improvement, using the deflated Sharpe ratio from the overfitting-control paper as the guard, and present any in-sample-selected result with the multiple-testing caveat it requires.

### 1.3 Data and reproducibility

All numerical examples and figures use freely available data — daily S&P 500 prices from Yahoo Finance's public chart API — and are reproducible from the accompanying code in `figures/`, which caches its downloads to `figures/data/` so the results are stable offline. Where an example draws on a private trade list (the VIX-gate case study of Section 6), that list is *not* redistributed: only aggregate statistics are shown, and the fact is stated wherever it applies. *This is a research and educational document, not investment advice.*

### 1.4 Organization of this paper

This paper is complete; all sections are written, and the figures are reproducible. The arc is a single argument built from the outside in — from how to read a paper, to why so many fail, to how to specify and test one honestly, to how to build a defensible variant.

- **Section 2 Sourcing and reading a quant paper** starts at the funnel's mouth — mining SSRN and the free literature for candidates and triaging the firehose down cheaply — then dissects the anatomy of a claim (population, rule, evidence, robustness, limitations), separates the sections that carry evidence from the sections that sell, and gives a concrete red-flag checklist (in-sample-only results, unrealistic costs, too many parameters, a suspiciously convenient sample window).
- **Section 3 The anomaly zoo and the replication crisis** surveys the survivors (momentum, value, carry, low-volatility, seasonality), states with numbers how many published anomalies fail careful replication, and turns post-publication decay into a working prior for a solo researcher.
- **Section 4 From claim to specification** turns prose into an unambiguous codeable rule, enumerates the implicit choices a paper leaves to the reader and how each one changes the result, and pre-registers the replication itself, wired to the backtesting paper's protocol.
- **Section 5 The paper-to-reality gap** names the five gaps — costs, capacity, shorting constraints, data vintage, regime shift — and works a full free-data replication of time-series momentum on the S&P 500 down a realism ladder, with one pre-committed specification frozen before the results (Figure 1).
- **Section 6 Deriving your own variant** shows how to move from a replicated base to a defensible modification without laundering overfitting, using parameter instability (Figure 2) and the deflated Sharpe ratio as guards, and presents a real anonymized VIX-gate variant with its full multiple-testing caveat, plus a one-series illustration of post-publication decay (Figure 3).
- **Section 7 Discussion** collects the common misconceptions, a glossary, and references.

## 2 Sourcing and reading a quant paper

A replication begins long before any code is written — in *finding* the paper and then *reading* it. The sourcing job is to turn the free literature's firehose into a shortlist cheaply; the reading job is not to admire the survivor but to locate the exact claim it makes, find the evidence that actually supports it, and decide — before investing a day of work — whether it is worth reproducing at all. This section is a method for both.

### 2.1 Where the papers come from — SSRN and the free literature

Before a paper can be read critically it has to be found, and the single most useful fact for a solo researcher is that the raw material is almost entirely free. The working-paper repositories that professional quants scan every week are open to anyone: *SSRN* (the Social Science Research Network, whose Financial Economics Network carries the bulk of new asset-pricing and strategy work), *arXiv*'s quantitative-finance section (`q-fin`), the *NBER* and *RePEc* working-paper series, and the public research pages of practitioner shops such as AQR and Research Affiliates. Between them they post, in preprint form and often months before any journal, essentially every anomaly a retail algorithmic trader could hope to trade. The idea-generation problem is not scarcity; it is triage.

SSRN is the natural centre of that search, and it rewards a deliberate method rather than idle browsing. Three entry points cover most of the ground. The first is *topic search*: SSRN's eLibrary can be filtered by network (Financial Economics) and by keyword or JEL classification (`G11` portfolio choice, `G12` asset pricing, `G14` market efficiency), turning "find me the momentum papers" into a dated, sortable list. The second is *following authors*: a small number of researchers produce a large share of the durable results, and subscribing to an author's feed surfaces their new work before it is refereed. The third — used carefully — is SSRN's *top-downloads* lists, which reveal what the professional crowd is reading; this is a discovery tool and simultaneously a warning, because a paper at the top of the download charts is a paper whose edge is being competed away as you read it (Section 3.3).

The reason sourcing is a distinct skill, and not just "search and read everything," is that the funnel is brutally lossy by design. A working estimate for a solo researcher's pipeline is that of every twenty abstracts skimmed, perhaps three survive to a serious read and perhaps one is worth a full day of replication. The job of the sourcing stage is to reach that one *cheaply* — to spend minutes, not days, discarding the other nineteen — and a fast triage does most of the work, every question answerable from the abstract and the data section alone. *Can I even get the data?* An anomaly measured on a proprietary options-microstructure feed or on point-in-time fundamentals is unbuildable for a retail researcher no matter how real it is, and belongs in the discard pile on sight. *Is the instrument liquid and the turnover low?* A durable, capacity-tolerant, low-turnover effect on a liquid instrument is worth ten fragile microcap ones, because it is the kind most likely to survive the realism ladder of Section 5. *Is there any out-of-sample or post-publication evidence, or is it one fitted window?* — the first item of the red-flag checklist (Section 2.4), applied here as a coarse pre-filter. *And how old is it?* A paper old enough to have accumulated an honest post-publication track record is worth more than this week's preprint, whose edge is untested by time even if it is real.

One honesty rider belongs here, because it sharpens every prior that follows. SSRN and arXiv are *un-refereed*: a posted working paper has cleared no bar beyond its authors' willingness to attach their names to it. That makes the base-rate skepticism of Section 3 not merely applicable but *more* severe than for a journal-published result — the replication-failure rates documented there were measured on the *published* literature, and the working-paper stream that feeds it is noisier still. The compensating advantage is timing: the preprint reaches you before the post-publication decay of Section 3.3 has fully run. Sourcing well means holding both facts at once — the free literature is an extraordinary, and extraordinarily unreliable, idea generator — and treating everything it hands you as a hypothesis to be re-tested, never a result to be trusted. Everything from here to the end of the paper is the machinery for doing exactly that with the one candidate in twenty that survives the funnel.

### 2.2 The anatomy of a claim

Strip away the prose and almost every empirical anomaly paper reduces to a five-part claim. Reading well means finding each part explicitly, and being suspicious of any that is missing or vague.

| Part | The question it answers | What to extract |
|---|---|---|
| **Claim** | What single effect is asserted, with a sign? | The one sentence you would have to reproduce; its direction |
| **Population** | On what, over what period, under what universe? | Instruments, dates, inclusion rules, rebalancing frequency |
| **Method** | How was the effect measured? | Portfolio construction, weighting, the exact metric, the benchmark |
| **Robustness** | Does it survive perturbation? | Sub-periods, sub-universes, cost assumptions, alternative specs |
| **Limitations** | Where do the authors say it fails? | Capacity, data caveats, what was assumed frictionless |

The most important discipline is to write the *claim* as a single directional sentence before reading the rest — "stocks with high trailing 12-month returns outperform low ones over the next month, in the cross-section of US equities" — and then hold everything else to that sentence. A paper that cannot be reduced to one such sentence is usually a paper testing many things at once, which is a paper testing nothing confirmatorily (the backtesting paper). And the *sign* in that sentence is the object of the direction check that runs through the whole replication: if your reproduction shows the effect with the opposite sign at the right magnitude, that is a falsification, not a near-miss.

To see the anatomy in use, read the classic momentum result of Jegadeesh and Titman (1993) through the five slots. The **claim** is directional and single: past winners (top-decile trailing 3-to-12-month returns) outperform past losers over the next 3 to 12 months. The **population** is US common stocks on the major exchanges, 1965–1989, monthly — a specific universe and a specific quarter-century, not "the stock market." The **method** is a zero-cost long-short portfolio of winner minus loser deciles, equal-weighted, with an explicit one-week or one-month skip between the ranking period and the holding period to avoid short-term reversal and bid-ask bounce. The **robustness** slot is where the paper earns trust: the effect is shown across several ranking/holding horizons and sub-periods, and the authors themselves note it partially reverses at long horizons. The **limitations** slot is where a replicator's suspicion should concentrate: the strategy is a *long-short* one that assumes the losers can be shorted, is measured *gross*, and — a detail invisible in the abstract — leans on smaller stocks where costs and short constraints bite hardest. Reading only the abstract, you would code a winners-minus-losers rule and expect the headline. Reading the five slots, you already know your replication's three battlegrounds before writing a line: the skip period (an implicit-choice trap, Section 4), the shortability of the loser leg (Section 5.1), and costs against turnover. The anatomy converts a paragraph of prose into a punch-list of exactly what to stress-test.

### 2.3 Sections that carry evidence versus sections that sell

Papers are not uniform in information density. Roughly, the abstract and introduction *sell*, the data and methodology *bind*, the robustness section *reveals*, and the conclusion *oversells*. The reading order that protects you inverts the writing order.

- **Data and sample construction** is where the truth lives and where the reader spends the most time. Which universe, screened how, over which dates, with what survivorship treatment? A cross-sectional equity anomaly measured on a universe that silently excludes delisted firms is measuring a different, easier world than the one you will trade.
- **The exact portfolio and metric.** "We form decile portfolios" hides a dozen choices: value- or equal-weighted, rebalanced when, held how long, long-short or long-only, gross or net. Two honest researchers implementing the same abstract can produce Sharpe ratios that differ by a factor of two purely through these choices — which is precisely the specification problem of Section 4.
- **The robustness section is the most honest part of most papers**, because it is where the authors, pre-empting referees, show the result under perturbation. A robustness section that only ever strengthens the headline is itself a red flag; a good one shows where the effect weakens and says so.
- **The abstract and conclusion are marketing** and should be read last and trusted least. The abstract's job is to make the result sound inevitable; your job is to find the conditions under which it was not.

A useful reflex: read the data section and the robustness tables *first*, form your own view of how strong the effect is, and only then read the abstract to see how much the authors' framing inflated it. The gap between your reading and their framing is a direct estimate of how much salesmanship to discount.

### 2.4 A red-flag checklist

Some warning signs recur across the weakest anomaly papers so reliably that a short checklist catches most of them before replication begins. None is by itself disqualifying, but each raises the prior that the headline will not survive your own out-of-sample test.

> **Red-flag checklist for an anomaly paper.**
> 1. **In-sample only.** Is there any genuine out-of-sample or post-publication evidence, or is the entire result fitted and evaluated on one window? A result with no out-of-sample split is a *hypothesis*, not a *finding* (the backtesting paper).
> 2. **Costs assumed away.** Are transaction costs, shorting costs, and turnover reported? A long-short anomaly with high turnover and no cost accounting is reporting a gross number that may be entirely a spread you would pay (the backtesting paper). *Turnover is the multiplier* — always find it.
> 3. **Too many parameters / degrees of freedom.** How many thresholds, lookbacks, and screens does the rule contain, and were they justified ex ante or chosen? Every free parameter is a place the result could have been fitted to the sample (the backtesting paper). If the paper tried many specifications and reports the best, it owes a multiple-testing correction — and rarely pays it.
> 4. **Suspicious sample window.** Does the sample start or end at a suspiciously convenient date? An effect that exists 1963–1990 and vanishes afterward, presented on the 1963–1990 window, is telling you something the abstract is not.
> 5. **Story-first.** Does the mechanism read as though it was written to fit the result rather than to predict it? A mechanism that predicts a sign *before* the test is evidence; a mechanism narrated *after* is HARKing (the backtesting paper).
> 6. **No capacity discussion.** Does the paper say anything about how much capital the effect can absorb? A microcap-concentrated anomaly can be real and untradeable at any size that matters.

The checklist is not a scoring rubric to be summed; it is a set of questions whose answers tell you *where to aim your own replication*. If the paper is in-sample only, your first job is an honest out-of-sample split. If costs are absent, your first job is a cost-sensitivity curve. The paper hands you your test plan by what it omits.

Run it once, concretely, against a hypothetical "we found a profitable rule: buy the S&P 500 when a 14-parameter indicator crosses zero, backtested 2009–2020, Sharpe 1.8." Item 1: no out-of-sample split — the whole 2009–2020 window is both training and evaluation, so the 1.8 is an in-sample number and worth little. Item 2: no costs or turnover reported — unknowable whether the edge survives the spread. Item 3: fourteen parameters — a vast fitting surface; the deflated-Sharpe ceiling (Section 6.2) for that many degrees of freedom is high enough that 1.8 in-sample is unremarkable. Item 4: the window is exactly the post-2009 bull market, a suspiciously convenient sample for a mostly-long rule. Four red flags fire on one sentence, and each one names a specific test: split out-of-sample, draw the cost curve, deflate for the parameter count, and re-run across a bear-inclusive window. The checklist did not tell you the rule is worthless — it told you exactly what four experiments would settle the question, which is the entire point of reading critically before replicating.

## 3 The anomaly zoo and the replication crisis

Before replicating any single paper it helps to know the base rate of the population it belongs to. The empirical asset-pricing literature is not a list of stable facts; it is a large, heterogeneous zoo in which a minority of animals are robust, many are fragile, and a substantial fraction appear not to have existed as described. Calibrating a prior over that zoo is the single most useful thing a solo researcher can do before trusting any one exhibit.

### 3.1 The survivors

A handful of effects have been documented across many markets, asset classes, and decades by independent authors, and are the closest thing the field has to durable phenomena. It is worth naming them, because they are the ones most worth a solo researcher's replication effort.

- **Momentum.** Assets that have outperformed over the past 3–12 months tend to continue outperforming over the next 1–12 months. Documented cross-sectionally in US equities by Jegadeesh and Titman (1993) and, as a time-series effect across 58 instruments in equities, bonds, currencies, and commodities, by Moskowitz, Ooi, and Pedersen (2012). It is the effect this paper replicates in Section 5.
- **Value.** Cheap assets (high book-to-market, low multiples) tend to outperform expensive ones over long horizons; robust across markets but with long, painful drawdowns.
- **Carry.** Holding the higher-yielding asset in a pair (high-yield currencies, upward-sloping futures curves) earns a premium in normal times and pays for it in crises.
- **Low volatility / low beta.** Lower-risk assets have historically delivered higher risk-adjusted returns than the CAPM predicts — a robust but capacity- and leverage-constrained effect.
- **Seasonality.** Calendar effects (turn-of-month, some day-of-week and holiday patterns) that are statistically persistent but small, easily eaten by costs, and the most prone to data-snooping of the group.

These survive in the sense that independent replications keep finding *something*; they do not survive in the sense of being free money, and each comes with the temporal and operational haircuts of Section 3.3 and Section 5. It is worth naming the haircut attached to each, because "robust" and "tradeable" are different words. Momentum is durable but crash-prone — it suffers rare, violent reversals (2009 is the textbook case) precisely when it has been most crowded. Value works over long horizons but has endured decade-long droughts that would exhaust most real capital. Carry is a premium for bearing exactly the risk that shows up in crises, so its Sharpe flatters it in calm samples and misleads about the tail. Low-volatility needs leverage to reach an interesting return, and leverage reintroduces the risk the anomaly was supposed to avoid. Seasonality is the smallest and the most cost-fragile, and the most likely of the group to be a data-snooping artifact. Each survivor, in other words, is a *conditional* survivor — real under conditions the abstract rarely foregrounds.

### 3.2 How many anomalies fail replication

The uncomfortable headline of the last decade of meta-research is that most published cross-sectional anomalies are weaker than their original papers claimed, and many are indistinguishable from noise once the methodology is tightened. Two results anchor the prior.

Hou, Xue, and Zhang (2020), in *Replicating Anomalies*, re-tested 452 anomalies from the published literature under a uniform, careful methodology — most importantly, weighting stocks by value (so that tiny, illiquid microcaps cannot drive the result) and requiring standard significance. **Roughly 65% failed to replicate at the conventional 5% significance level; among some categories the failure rate was higher still** (Hou, Xue & Zhang 2020). The single largest driver of the discrepancy was microcaps: many published anomalies were concentrated in the smallest, least tradeable stocks and shrank drastically under value-weighting. This is not a claim that two-thirds of anomalies are frauds; it is a claim that two-thirds were fragile to reasonable methodological choices — which is exactly what a replicator most needs to know.

Harvey, Liu, and Zhu (2016), in *…and the Cross-Section of Expected Returns*, approached the same problem from the multiple-testing angle: with hundreds of factors tested against the same return data over the decades, the conventional *t* > 2 threshold is far too lenient, because it ignores that the literature as a whole is one giant multiple-comparison exercise. They argue that a newly proposed factor should clear a hurdle closer to **t > 3** to account for the mass of tests that preceded it (Harvey, Liu & Zhu 2016). Their message is the field-scale version of the backtesting paper's warning about the garden of forking paths: the best of many tested factors is an order statistic, and must be judged as one.

The practical translation is blunt. If you pick a random published anomaly and replicate it faithfully, the base-rate expectation — *before* you even reach costs and decay — is that it is meaningfully weaker than advertised, and more likely than not fails a strict re-test. Your prior on any single paper should start there.

### 3.3 Post-publication decay

Even the anomalies that *were* real face a second haircut: publication itself. McLean and Pontiff (2016), in *Does Academic Research Destroy Stock Return Predictability?*, studied 97 predictors and compared their returns in three windows — in the original sample, after the sample but before publication, and after publication. They found that **predictor returns decay by about 58% out-of-sample after publication** relative to the in-sample estimate; of that decline, roughly 26 percentage points is ordinary in-sample overfitting — the decay already visible out-of-sample *before* publication — and the remaining ~32% is the additional decline caused by publication itself, as informed capital trades the signal away (McLean & Pontiff 2016). The interpretation is that publication informs arbitrageurs, capital flows in, and the mispricing is partly competed away — the more so for anomalies in liquid, easily traded securities. Arnott and co-authors at Research Affiliates make the same point from the practitioner side, warning that factor crowding and post-publication performance-chasing turn many "smart beta" strategies into disappointments precisely when they are most popular (Arnott, Beck & Kalesnik 2016).

Two riders keep this honest. First, decay is a *cross-sectional average*: some anomalies decay to nothing, others persist (momentum has been notably durable), and the average masks that spread. Second, decay is not the same as death — a halved return can still be tradeable if it was large enough to begin with. But the direction of the effect is unambiguous and the reason mechanical, which makes it a reliable prior.

### 3.4 What this implies for a solo researcher

Combine the three haircuts and a working prior falls out. Take a random published anomaly. With probability well above one-half it was fragile and will not cleanly replicate (Section 3.2). If it does replicate, expect roughly half of the in-sample return to be gone out-of-sample and post-publication (Section 3.3). Whatever remains must then survive *your* costs, *your* capacity, and *your* execution (Section 5), which for a high-turnover or microcap effect can be the largest haircut of all. The compounded expectation is sobering: the modal outcome of faithfully replicating a random anomaly paper is a small, fragile, or absent edge.

To make the compounding explicit, put rough numbers on it — not as precise probabilities but as a discipline of multiplication. Suppose a randomly chosen published anomaly has a one-in-three chance of replicating cleanly under tightened methodology (the Hou-Xue-Zhang complement) — though this prior is contested: Chen and Zimmermann's *Open Source Cross-Sectional Asset Pricing* (Critical Finance Review 2022) hand-reproduces 319 predictors and finds a replication rate near 100% (158 of 161 clear t > 1.96), regressing reproduced on original t-statistics with a slope of 0.88, and argue the low Hou-Xue-Zhang rate is partly a *classification* choice (heavy microcap screening and value-weighting) rather than genuine non-replication. With their prior the first factor is closer to 1 than 1/3 and the ~8% below rises to ~25%. The replication *rate* is itself disputed, so carry both priors and read the multiplication as a discipline, not a point estimate. Condition on replication, and expect roughly half the in-sample return to remain out-of-sample (McLean-Pontiff). Condition on *that*, and for a high-turnover or microcap effect, costs and capacity can remove half again. Multiply — (1/3) × (1/2) × (1/2) ≈ 8% — and the point is not the exact figure but the shape: the expected fraction of the headline that reaches your account is small, and it is small because three independent haircuts multiply rather than add. A durable, low-turnover, large-cap effect improves every term; a fashionable, high-turnover, small-cap one worsens every term. The prior is not "anomalies don't work"; it is "the specific anomaly in front of you is probably weaker than advertised, and you should design your replication to find out *where* it dies."

This is not an argument against reading the literature — it is an argument for reading it as a *source of hypotheses to be re-tested on your own out-of-sample data*, never as a source of results to be trusted. It also reframes what a solo researcher's edge actually is. You will not out-data or out-compute a quant fund. What you can do is choose durable, capacity-tolerant effects; hold yourself to an honest out-of-sample split the literature often skipped; and take costs seriously from the first line. The rest of this paper is that program, made concrete.

## 4 From claim to specification

Suppose you have chosen a paper worth replicating. The next task is deceptively hard: turning the paper's prose into a rule so exact that two people implementing it independently would produce the same equity curve. The prose almost never contains such a rule. It contains a claim and a sketch, and it leaves a surprising number of choices to the reader — choices that individually feel minor and collectively can flip the result.

### 4.1 Prose is not a rule

Consider the sentence a momentum paper might use: *"We go long assets with positive trailing returns and short those with negative trailing returns, rebalancing monthly."* This reads as a rule. It is not. At least nine choices are unstated:

1. **Lookback length.** Trailing over what — 3 months, 12 months, something else? (Momentum papers use several; the choice moves the result materially — see Section 6.)
2. **Skip period.** Do you skip the most recent month to avoid short-term reversal, as much of the equity-momentum literature does?
3. **Signal definition.** Sign of the return, magnitude of the return, or a rank/z-score across assets?
4. **Rebalance timing.** On the last day of the month at the close, the first of the next month at the open, or with a lag?
5. **Position sizing.** Equal-weight, value-weight, or inverse-volatility scaled (as time-series momentum typically is)?
6. **Universe.** Which instruments, and how is the universe screened over time?
7. **Costs and shorting.** Gross or net, and can the shorts actually be borrowed?
8. **Holding period.** Held one month, or overlapping multi-month holdings averaged?
9. **Data treatment.** Total return or price return, how are gaps and splits handled, what vintage of the series?

Each of these is a *researcher degree of freedom* (the backtesting paper). The danger is not that they exist — they must be resolved for any implementation — but that they are resolved *after* seeing the result, each nudged in the direction that improves the backtest. Resolved that way, the replication is not a test of the paper; it is a fresh fit to your sample wearing the paper's name.

### 4.2 The specification sheet: fixing every choice, in advance

The remedy is a *specification sheet*: a written table that resolves every implicit choice to a single value, with a one-line justification for each, completed and frozen before any result is computed. The justification column is what protects you — a choice you can justify from the paper or from prior reasoning is a choice you did not fit to the sample. Here is the completed spec sheet for the Section 5 replication, which is exactly the frozen rule that figure code scores.

| Choice | Value fixed | Justification (ex ante) |
|---|---|---|
| **Effect** | Time-series momentum, single-asset sign rule | Moskowitz-Ooi-Pedersen (2012), simplest faithful form |
| **Instrument** | S&P 500 index (^GSPC), daily closes | Free, long history, one liquid series |
| **Lookback** | 12 months | The central horizon of the MOP paper; fixed, not searched |
| **Signal** | Sign of trailing 12-month return: long if > 0, short if < 0 | The paper's sign rule; no magnitude scaling |
| **Skip period** | None | Time-series (not cross-sectional) momentum; MOP use no skip |
| **Sizing** | Constant unit exposure (±1), no volatility scaling | Deliberately the plain form; vol-scaling is a variant, not the base |
| **Rebalance** | Monthly, at month-end close | Standard monthly TSMOM cadence |
| **Holding** | One month, position held every trading day of month *t*+1 | Non-overlapping, simplest accounting |
| **Costs** | 10 bps one-way per unit of turnover | Pessimistic-but-plausible index cost; scored as a ladder step |
| **Lag** | One trading day (variant step iii) | Realistic: you cannot trade the close that defined the signal |
| **Data** | Yahoo ^GSPC, range=max, cached | Free, reproducible, offline-stable |

The point of freezing this table is not that these are the *only* defensible values — several are debatable, and the lookback in particular is one many replicators would tune. The point is that they were chosen *before* the result was seen and justified without reference to it. Section 6 will deliberately violate this discipline for the lookback, sweeping it across sixteen values, precisely to show what tuning buys and does not buy.

It is worth being explicit about *how each implicit choice moves the result*, because that is where the reader's intuition for the fragility of a replication is built. The **lookback** is the largest lever: on the same S&P 500 series, sweeping it from 3 to 18 months moves the in-sample Sharpe from roughly 0.14 to 0.37 and reorders which sub-period looks best — a range wide enough that a tuner could report almost any story (this is Figure 2). The **skip period** matters most for cross-sectional equity momentum, where the last month carries a reversal that can flip the sign of the shortest-horizon signal; for a single-index time-series rule it matters far less, which is why the spec fixes it to none. The **sizing** choice — constant unit versus inverse-volatility scaling — is what separates this replication's Sharpe of 0.32 from MOP's headline above 1: volatility scaling and 58-instrument diversification did most of the work in the paper, and dropping them is the single biggest haircut (Section 5.3), not a detail. The **rebalance timing and lag** determine whether the backtest is honest or a look-ahead machine: trading the very close that defined the signal manufactures a fictitious edge (the backtesting paper), and the one-day lag that fixes it costs about 0.03 in Sharpe here. **Costs** interact with turnover, which for this slow rule is small; for a monthly cross-sectional long-short with high turnover the same 10 bps would be several times more punishing. The lesson is that "the same" replication, under different-but-defensible resolutions of these choices, spans a range of results large enough to contain both "clear edge" and "no edge" — which is exactly why the choices must be frozen before, not after, the data is seen.

### 4.3 Pre-registering the replication itself

A replication deserves the same pre-registration as an original study, and for the same reason: the freedom to reinterpret "did it replicate?" after seeing the answer is exactly the freedom that produces false confirmations. The backtesting paper's template applies unchanged; the only twist is that the "expected effect size" is now anchored to the paper's own claim, discounted by the Section 3 priors. Frozen for the Section 5 replication:

```markdown
# Pre-registration — TSMOM replication on SPX (single-asset sign rule)

## Confirmatory hypothesis (exactly one)
- H1 (directional): The 12-month-return sign rule on the S&P 500 earns a
      POSITIVE gross Sharpe ratio over the full free-data sample.
- H0 (null): The rule's gross Sharpe is <= 0 (the sign of the trailing
      12-month return carries no information about next month's return).

## Expected effect size
- Point expectation: gross Sharpe ~0.3-0.5 for a single unscaled asset
      (well below MOP's diversified, vol-scaled ~1+, per the Section 3 haircut).
- SEWA: the net, lagged rule must at least not be DOMINATED by buy-and-hold
      on the identical window; a rule that loses to passive exposure is not
      a strategy regardless of its own Sharpe.

## Data & sample (fixed)
- Instrument: S&P 500 (^GSPC), daily closes, Yahoo range=max, cached.
- Period: full available history through 2026-09-17.

## Realism ladder (scored in order, decided before results)
- (i) paper-faithful gross; (ii) + 10 bps one-way costs;
- (iii) + 1-day implementation lag; (iv) post-publication sub-period 2012+.

## Metric & decision rule
- Primary: annualized Sharpe (monthly returns x sqrt 12); secondary CAGR.
- Report every step's Sharpe and CAGR honestly; compare each to buy-and-hold
  on the identical window. No step is dropped for being unflattering.

## Multiple-testing correction
- Base replication: ZERO free parameters searched (all fixed in Section 4.2).
- The lookback SWEEP of Section 6 is exploratory and labelled as such; its best
  in-sample value earns no confirmatory status (deflated Sharpe, the overfitting-control paper).

## Frozen on
- 2026-09-18 (spec written before the figure code was run).
```

This is where the paper wires directly into the author's own vault practice. The internal hypothesis register (H001–H004, on options-dealer hedging mechanics) is precisely a discipline of turning published and semi-published claims into pre-registered, testable theses *in the wild*, under an explicit evidence-tier rule: external evidence — even top-tier academic evidence — moves a hypothesis only to *formulated*, never to *supported*; the stronger status requires an own out-of-sample research note, and every evidence intake runs the direction check first (the internal conventions). H001 carries a permanent correction log recording exactly the failure the backtesting paper describes — a claim once "confirmed" by data of the right magnitude and the wrong sign. The lesson generalizes to replication: *importing* a paper's claim is an evidence intake like any other, and it is subject to the same tier rule and the same direction check. A paper is `formulated`-grade evidence for your thesis until your own out-of-sample test says otherwise.

## 5 The paper-to-reality gap

A specification that replicates the paper gross is only the start. Between a gross in-sample number and your live account sit five gaps, each of which independently subtracts from the edge. This section names them and then works one full replication down a realism ladder on free data, reporting honestly whatever it shows.

### 5.1 The five gaps

- **Costs.** The spread you cross, the slippage you suffer, and the commissions you pay, multiplied by turnover. A gross edge with high turnover can be entirely a spread you would pay yourself on paper (the backtesting paper).
- **Capacity.** The amount of capital an effect can absorb before your own trading moves the price against you. A microcap or thin-futures anomaly can be real and vanish at any size worth trading; the paper rarely says at what capital its alpha survives.
- **Shorting constraints.** Many long-short anomalies assume costless, unlimited short sales. In reality some names cannot be borrowed, borrow fees on exactly the hard-to-short names can exceed the alpha, and short availability is worst precisely when the short leg would pay most.
- **Data vintage and look-ahead.** The paper used a point-in-time database with delisting returns and as-reported fundamentals; your free feed is survivorship-screened and back-adjusted. Index composition, splits, and restatements all leak future information into naively reconstructed history.
- **Regime shift.** The sample the paper measured is not the regime you will trade. Post-publication decay (Section 3.3) is one form; structural change — decimalization, the zero-commission era, the rise of 0DTE options — is another. An edge measured 1990–2010 is a claim about that world.

Two of these gaps deserve a concrete illustration because they are the ones most often waved away. On **capacity**: a cross-sectional anomaly whose alpha lives in the smallest decile of stocks can carry a beautiful paper Sharpe and be untradeable at any size that matters, because the bid-ask spreads and price impact in those names are multiples of the per-name alpha; Hou-Xue-Zhang's finding that value-weighting alone kills two-thirds of anomalies *is* the capacity gap, quantified at the population level. On **shorting**: the loser leg of a long-short momentum or value strategy is disproportionately made of exactly the hard-to-borrow, high-fee names, and borrow is withdrawn precisely in the stressed markets where the short would pay most — so the "costless short" assumed in the paper is unavailable at the worst possible moment, converting a symmetric backtest into an asymmetric live result. The **data-vintage** gap is subtler and more insidious: a free, back-adjusted, survivorship-screened series silently encodes decisions (which firms survived, how splits and dividends were applied, when index membership changed) that were not known at the time, and a naive reconstruction of "the universe as it is today, projected backward" leaks the future into the past. The realism ladder below cannot exercise capacity or shorting on a single liquid index — that is a virtue for clarity and a limitation to keep in mind — but it makes the *costs*, *lag*, and *regime* gaps quantitative on one series, and the reader should mentally add the other three whenever the effect being replicated is cross-sectional, small-cap, or short-dependent.

The realism ladder below makes the *costs*, *lag*, and *regime* gaps quantitative on one series. Capacity and shorting are qualitatively small for a single liquid index future but are exactly where a cross-sectional microcap anomaly would die, and the reader should keep them in view even though this particular example does not stress them.

### 5.2 The worked replication: time-series momentum on the S&P 500

We replicate the single-asset sign rule of Moskowitz, Ooi, and Pedersen (2012): at each month-end, compute the trailing 12-month return; hold a long unit of exposure for the next month if that return is positive, a short unit if it is negative. The specification is the frozen sheet of Section 4.2, and the pre-registration of Section 4.3 was written before the figure code was run. We then score four steps, in the order fixed in advance:

- **(i) Paper-faithful gross** — the position in force for every trading day of the following month, no costs, no lag.
- **(ii) + transaction costs** — 10 bps one-way per unit of turnover (a full long-to-short flip trades two units, so 20 bps).
- **(iii) + one-day implementation lag** — the new position only takes effect from the close of the first trading day *after* the month-end signal, since you cannot trade the very close that defined the signal.
- **(iv) post-publication sub-period** — step (iii) evaluated only on months from January 2012 onward, the year MOP was published in the *Journal of Financial Economics*.

Throughout, buy-and-hold on the identical window is carried as the benchmark, because the honest question is not "does the rule make money?" but "does it beat simply owning the asset?"

The entire rule is a few lines, and showing them makes the timing discipline concrete — the signal is decided at a month-end and only earns *later* days' returns, never the bar that defined it:

```python
# month-end indices me[j]; C = close[me] are month-end closes; r = daily returns
sig = np.sign(C[j] / C[j - 12] - 1.0)        # signal at month-end j: +1 up, -1 down
# position in force for return day i, held from close i-1 to close i, with `lag`:
pos[me[j] + lag + 1 : me[j+1] + lag + 1] = sig
ret = pos * r - (cost_bps / 1e4) * np.abs(np.diff(pos, prepend=0.0))  # net daily P&L
sharpe = ret_monthly.mean() / ret_monthly.std() * np.sqrt(12)         # annualized
```

The `+ lag + 1` in the position slice is the whole honesty of the backtest: the position earns its first return strictly *after* the signal day, so no future information leaks in. Change that one offset and the ladder's numbers improve — and become fiction.

![Time-series-momentum replication on the S&P 500 (Yahoo daily ^GSPC, range=max, 1927 to 2026, 24,795 sessions, 1,173 strategy months): the 12-month sign rule scored at each step of the realism ladder, with growth of a dollar on a log scale (left) and the Sharpe haircut (right). Annualized Sharpe falls from 0.32 gross to 0.31 after 10 bps costs to 0.28 after a one-day lag; the post-2012 net-and-lagged sub-period reads 0.33. Buy-and-hold over the same window is 0.41 full-sample and 0.95 post-2012. One frozen spec, no tuning; the single asset flips only about once a year, so costs barely bite and the real gap is to plain long-only exposure. Reproduce with `figures/fig_tsmom_haircut.py`.](figures/fig_tsmom_haircut.png)

### 5.3 Reading the result honestly

The printed numbers are worth stating plainly, because they do not flatter the rule:

| Step | Annualized Sharpe | CAGR |
|---|---|---|
| (i) paper-faithful gross | 0.32 | 4.18% |
| (ii) + 10 bps costs | 0.31 | 3.98% |
| (iii) + 1-day lag | 0.28 | 3.55% |
| (iv) post-2012, net + lag | 0.33 | 3.80% |
| buy-and-hold, full sample | 0.41 | 6.06% |
| buy-and-hold, post-2012 | 0.95 | 13.01% |

Three honest lessons come straight off the table, and none is the lesson a naive reader expected.

*First, costs and lag are the small haircuts here.* Gross-to-net-to-lagged costs only 0.32 → 0.31 → 0.28 in Sharpe. The reason is turnover: the single-asset sign rule flips barely once a year, so the cost multiplier that killed the fast reversal strategy in the backtesting paper (~130 flips a year) barely touches this slow one. This is the *turnover-is-the-multiplier* point running in reverse — a genuinely useful contrast — but it is not where this strategy's edge dies.

*Second, the biggest haircut is invisible on the ladder and comes from the replication choice itself.* MOP's headline Sharpe (above 1) was for a *diversified, volatility-scaled portfolio of 58 instruments*. Replicating "the rule" on one unscaled index strips out the diversification and the vol-scaling that did most of the work, leaving a gross Sharpe of 0.32 — a pale shadow of the paper's number, and entirely expected once you read what the paper actually built. The gap between "the anomaly" and "the free-data replication a solo researcher can actually run" is the largest haircut of all, and it never appears as a cost line. This is Section 3.4 made concrete.

*Third, the benchmark is the real verdict.* The rule's post-2012 Sharpe of 0.33 might look like survival — no decay here — until you notice that simply owning the S&P 500 over the same window earned 0.95. In the post-publication bull market a long-biased trend rule spends most of its time long anyway, pays a lag and a cost to do it, and occasionally goes short at exactly the wrong time, so it *underperforms the passive exposure it is a complicated proxy for*. By the SEWA fixed in Section 4.3 — the rule must not be dominated by buy-and-hold — the single-asset replication **fails its own pre-committed bar**, gross or net, and fails it worse in the modern regime. Reported honestly, that is the result: the famous effect, replicated faithfully on the data a retail researcher actually has, is not a strategy on this instrument. Recording a clean "no" is exactly what a good replication is for (the backtesting paper).

## 6 Deriving your own variant

A faithful replication rarely ends the work; it usually motivates a modification. This is the most dangerous moment in the whole pipeline, because "improving" a replicated base is indistinguishable, from the inside, from fitting the base to your sample. This section is about the narrow path between a defensible variant and dressed-up overfitting — and it uses a real, anonymized example whose result is good enough to be genuinely tempting.

### 6.1 From a replicated base to a defensible modification

A variant is *defensible* when the modification is motivated by a mechanism stated before the test, tested out-of-sample, and reported with the multiple-testing cost of however many variants were tried. It is *overfitting in disguise* when the modification is chosen because it improved the in-sample curve and then narrated with a mechanism afterward. The difference is not in the code — the two produce identical backtests — but in the order of operations and in whether the search cost is paid. The three questions that separate them:

1. **Was the modification's direction predicted before the test?** A mechanism that predicts a *sign* is evidence; one written to fit the result is HARKing (the backtesting paper).
2. **Does it hold out-of-sample?** On a split opened once, at the end.
3. **How many variants were tried to find it, and has that been corrected for?** This is the question almost everyone skips, and it is the subject of Section 6.2.

The contrast is sharpest when drawn on two variants that produce the *same* improved backtest. Variant A: you notice the strategy loses money in high-volatility conditions, form the mechanism "panic rebounds overrun the short leg" *before* testing, predict that short-side edge should fall as VIX rises, and then test that single prediction on an out-of-sample split. Variant B: you grid-search thresholds on twenty market-state features, keep the VIX cut at 20 because it maximized the in-sample profit factor, and then write "in a volatility spike, panic rebounds overrun the short leg" as the justification. The code is identical; the equity curves are identical; the epistemic status is not. Variant A is a pre-registered directional test with one degree of freedom; Variant B is a twenty-way search whose winner is an order statistic dressed in a post-hoc story. The Section 6.3 case study is honest that the *real* history was closer to B than to A — which is exactly why it is presented with a multiple-testing caveat rather than as a discovery. The moral is uncomfortable but freeing: you cannot tell A from B by looking at the backtest, so you must record which one you actually did, before the result can seduce you into misremembering.

### 6.2 The overfitting trap and the deflated-Sharpe guard

The instability is not hypothetical. Take the very replication of Section 5 and do the one thing Section 4.2 forbade: sweep the lookback across sixteen values, 3 to 18 months, and pick the best. Score each lookback on two halves of the common sample — the first half as an in-sample "selection" set, the second half as out-of-sample — and ask whether the in-sample winner is the out-of-sample winner.

![Parameter instability of the momentum lookback on the S&P 500. The TSMOM sign rule is swept over lookbacks of 3 to 18 months and scored on two halves of the common sample (Yahoo daily ^GSPC, 1,167 common months split into 583 in-sample and 584 out-of-sample). The best in-sample lookback (10 months, Sharpe 0.37) happens to hold up out-of-sample this time and lands rank 1 of 16 — but the ranking as a whole barely survives: the in-sample-versus-out-of-sample rank correlation across the sixteen candidates is only 0.22, with the 4-month lookback strong in-sample and near-worst out, and the 13-month lookback the reverse. The point is the instability of the selection, not any single winner. Reproduce with `figures/fig_param_sensitivity.py`.](figures/fig_param_sensitivity.png)

The printed numbers are deliberately reported without cosmetic help. The best in-sample lookback is 10 months (in-sample Sharpe 0.37), and this time it happens to also be the best out-of-sample (Sharpe 0.49, rank 1 of 16). A careless reader would take that as vindication of parameter search — and would be exactly wrong. The honest number is the *rank correlation* between in-sample and out-of-sample Sharpe across the sixteen lookbacks: **0.22**, barely above zero. The 4-month lookback ties for second-best in-sample (0.29) and is near-worst out-of-sample (0.15); the 13-month lookback is near-worst in-sample (0.11) and perfectly respectable out (0.45). The ordering the in-sample data hands you is close to random with respect to the future. That the single top pick survived is a coincidence you cannot count on and must not report as a method — and I am keeping it in the figure precisely because re-drawing the split until the winner *failed* would be the same data-snooping this paper warns against, run in the opposite direction.

The formal guard against calling such a winner a discovery is the *deflated Sharpe ratio* from the overfitting-control paper (Bailey & López de Prado 2014). The idea in words: the more strategies you tried, the higher the best in-sample Sharpe you would expect *from luck alone*, so the observed maximum must be discounted by how many trials produced it and by the non-normality of returns. The expected maximum in-sample Sharpe from *N* independent zero-edge trials is, to a good approximation, E[max SR over N trials] ≈ σ_SR·[(1−γ)·Z⁻¹(1−1/N) + γ·Z⁻¹(1−1/(N·e))], which for large *N* simplifies to the more memorable σ_SR·√(2 ln N) — where σ_SR is the standard error of a single Sharpe estimate, γ ≈ 0.577 is the Euler–Mascheroni constant, Z⁻¹ is the inverse standard-normal CDF, and *e* is Euler's number. In words: the noise ceiling grows with the square root of the log of the number of trials, so it climbs slowly but never stops. Sixteen lookbacks already lift that ceiling appreciably, and the ~20 variants of the VIX-gate in Section 6.3 lift it further; a strategy selected across twenty variants must clear a bar meaningfully above zero before it is even a candidate, and the deflated Sharpe is exactly the observed Sharpe re-expressed as a probability that it exceeds this inflated ceiling. The rule of practice: *the number of variants tried is part of the result, and a Sharpe — or a profit factor — reported without it is not a result.*

### 6.3 A real anonymized variant: the VIX-gate

The cleanest way to teach this is on a variant that actually worked well enough to be dangerous. The example is the author's own, and it is presented in exactly the frame the backtesting paper set up, because the backtesting paper carried the same case through its own protocol; here we complete it. *The underlying trade list is private and is not redistributed — only aggregate statistics appear below.*

The base is an intraday mean-reversion strategy on E-mini S&P 500 futures (ES), trading both long and short around a volatility-weighted band. The observation that motivated the variant: the strategy's *short* side seemed to bleed in high-volatility conditions while the long side did not. The mechanism, stated as a directional prediction: in a volatility spike, panic rebounds carry price back *up* through the upper band (so shorts placed there get overrun), while reversion back *up* from the lower band strengthens (so longs are helped). This predicts a *sign* before the test — short-side edge should *degrade as VIX rises* — which is what makes the subsequent gate a hypothesis rather than a curve-fit.

The data bear the direction out. Bucketing every short trade by the prior day's VIX, the gross short-side profit factor runs **1.02 (VIX < 15) · 1.44 (15–20) · 0.74 (20–25) · 0.45 (25–30) · 0.32 (≥ 30)** — profitable in the calm regime, sharply loss-making once VIX clears 20, while the long side stays healthy across all buckets. The average dollar result per short trade falls monotonically from positive to deeply negative across the same buckets. The direction check (the backtesting paper) therefore *passes*: the sign of the data matches the sign of the predicted mechanism.

The variant is a *gate*: disable short trades when the prior-day VIX is at or above 20 (take shorts only in the calm regime), leaving the long side untouched. Its effect on gross profit factor, over the full 2022-09-05 to 2026-09-10 sample of 2,284 trades, with an in-sample/out-of-sample split fixed at 2024-12-31 before the analysis:

| Profit factor (gross) | Baseline | Shorts gated to VIX < 20 |
|---|---|---|
| **Full sample** | 1.32 | 1.44 |
| **In-sample (≤ 2024-12-31, n = 1,314)** | 1.26 | 1.32 |
| **Out-of-sample (≥ 2025-01-01, n = 970)** | 1.40 | 1.62 |

The headline is real: the gate lifts full-sample gross profit factor from **1.32 to 1.44**, and — the part that makes it tempting — the uplift *holds out-of-sample*, where the gated profit factor reaches **1.62** against a baseline of 1.40. This is precisely the number the backtesting paper flagged in advance as "exactly the kind this section is designed to make you distrust," and completing it honestly means dismantling it with this paper's own tools:

1. **It was selected in-sample across roughly twenty variants.** The threshold "20," the bucket edges, and several alternative gating features (a VIX/VIX3M term-structure ratio, a moving-average z-score, a five-day VIX change) were all tried on the same series — about twenty variants in total. By Section 6.2, twenty trials lift the luck-ceiling substantially; the result owes a deflated-Sharpe-style correction it has not yet been given, and the raw 1.62 must be read as an *order statistic*, not a clean estimate.
2. **One finding measured four ways is not four proofs.** The short-side degradation shows up in all four feature languages, which feels like corroboration but is not: it is one underlying pattern observed through four correlated lenses — "one finding, measured four times, not four independent pieces of evidence." Correlated confirmations do not multiply confidence the way independent ones would.
3. **The out-of-sample split is not a walk-forward.** A single fixed split opened once shows *direction stability* — the sign held — but it is one draw, not the many-fold re-selection a true walk-forward would impose. Direction-stable is weaker evidence than walk-forward-stable.
4. **The tail buckets rest on a handful of episodes.** The most dramatic degradation (VIX ≥ 25) is carried by only about 200 trades clustered in essentially three volatility episodes. The effective sample is far smaller than the trade count suggests, and a mini-cell of that size cannot support a confident per-bucket claim.
5. **It is gross.** All figures are before costs and slippage; for an intraday strategy those are first-order, and cost assumptions are known to reorder rankings elsewhere in the same research.

None of this means the gate is fake — the mechanism is plausible, the direction check passes, and the sign held out-of-sample, which collectively make it a *good candidate hypothesis*. It means the honest status of the result is exactly what the backtesting paper's evidence rule assigns: `formulated`, not `supported`. To earn the stronger word it needs a genuine walk-forward, an after-cost re-test, and out-of-sample confirmation on trades not used in any of the twenty selections — a *new* study on *new* data, pre-registered. Reporting the 1.62 without every one of these five caveats attached would be to launder an in-sample-selected order statistic as a discovery, which is the precise error this paper exists to prevent.

A closing honesty note on the same example: a further redesign layered an R-multiple exit ladder (partial take-profits at 1.0R, 1.5R, 2.5R) onto the gated base. In backtest those take-profit targets *never filled* — the realized exits were break-even trails and end-of-day closes — so the R-ladder has *no realized expectancy yet* and is reported here only as an unvalidated designed variant, not as a result. A specified, plausible, code-complete variant that has not actually traded its intended exits is a hypothesis with a nice interface, nothing more.

### 6.4 Post-publication decay on one series — and its honest limits

To close the loop with Section 3.3, it is tempting to *show* post-publication decay on the replicated TSMOM rule. The honest result refuses to cooperate, which is why it is worth showing.

![Post-publication decay on one series: rolling five-year annualized Sharpe of the gross TSMOM sign rule on the S&P 500 (Yahoo daily ^GSPC, 1927 to 2026, 1,173 strategy months), with the Moskowitz-Ooi-Pedersen publication year (2012) marked. Honestly, this single series does not decay: full-sample Sharpe is 0.31, pre-2012 is 0.29, and post-2012 is 0.47, while the rolling window swings from minus 0.42 to plus 0.99 after publication. One series is an illustration of the decay shape and of rolling instability, not a cross-sectional test of the McLean-Pontiff result. Reproduce with `figures/fig_decay_split.py`.](figures/fig_decay_split.png)

On this one series the rule's Sharpe *rose* after publication (0.29 → 0.47) rather than decaying — because the post-2012 bull market suited a mostly-long trend rule, a regime effect that has nothing to do with arbitrage competing the anomaly away. This is exactly why McLean and Pontiff's result is a *cross-sectional average over 97 predictors* and not a claim about any single series: one instrument in one regime is dominated by idiosyncratic and regime noise, and the rolling five-year Sharpe swinging from −0.42 to +0.99 makes that noise visible. The figure is an honest illustration of the *shape* of the decay question and of rolling-window instability; it is emphatically *not* evidence for or against decay, and labelling it otherwise would be the single-series overreach Section 3.3 warned against. The discipline the whole paper teaches applies to its own figures: report what the data show, and refuse the tidy story the data do not support.

### 6.5 The workflow, assembled

The three figures and the case study are one pipeline, and it is worth stating it as a sequence a reader can follow. *Source*: mine SSRN and the free literature and triage the firehose down to the one candidate in twenty worth a day's work (Section 2.1). *Read* the survivor adversarially and reduce it to one directional claim with a test plan drawn from its omissions (Section 2). *Prior*: discount the claim by the base rates of the anomaly zoo before writing any code (Section 3). *Specify*: freeze every implicit choice in a justified spec sheet and pre-register the replication, wired to the backtesting paper (Section 4). *Replicate*: score the frozen rule down the realism ladder and compare it to the honest benchmark, recording whatever it shows — here, a famous effect that fails its own SEWA on free single-asset data (Section 5). *Vary, if at all, with discipline*: modify only from a pre-stated mechanism, test out-of-sample, and pay the multiple-testing cost of every variant tried, using the deflated Sharpe as the guard (Section 6). At no point in this pipeline does a good number earn trust on its own; trust is earned only by the order of operations that produced it. That is the single transferable skill of this paper — not any one anomaly, but the habit of asking, of every published edge and every improvement to it, *what would have to be true for this to survive contact with my account, and did I test that before or after I saw the answer?*

## 7 Discussion

### 7.1 Common misconceptions

> **"It's published in a top journal, so it's real."** Publication survives peer review, not out-of-sample time and not your costs. Roughly two-thirds of cross-sectional anomalies fail careful replication (Section 3.2), and even survivors decay after publication (Section 3.3). Publication is a reason to *test*, not a reason to *trust*.

> **"I replicated the abstract, so I replicated the paper."** The abstract is the marketing; the result lives in the data section and the exact portfolio construction. A single-asset, unscaled version of a diversified, vol-scaled, 58-instrument strategy is a different, weaker object (Section 5.3) — and the difference never appears as a cost line.

> **"Costs are a rounding error."** Only for slow signals. Cost drag is turnover times per-trade cost; a fast rule can show a large gross edge and no net edge (the backtesting paper). Always report turnover next to return, and always ask "at what cost does this die?"

> **"My variant improves the strategy."** If the variant was chosen because it improved the in-sample curve, you have measured the sample, not the world. The number of variants tried is part of the result; without a multiple-testing correction (deflated Sharpe — see the overfitting-control paper), the in-sample best is an order statistic (Section 6.2).

> **"It held out-of-sample, so it's confirmed."** A single fixed split opened once shows direction stability, not walk-forward robustness — especially when the rule was selected in-sample across many variants. Holding out-of-sample upgrades a candidate to a *good* candidate; confirmation needs a fresh, pre-registered test on data used in no prior selection (Section 6.3).

> **"The backtest went up, so the effect is there."** The best of many zero-edge backtests goes up by construction. Direction of the equity curve is not evidence until the question was frozen before the data could answer it (the backtesting paper).

> **"The mechanism shows up in four different indicators, so it's well-corroborated."** Correlated confirmations are one finding measured four ways, not four independent pieces of evidence (Section 6.3). Four lenses onto the same underlying pattern raise the *feeling* of confidence without raising the *evidence*; independence, not repetition, is what compounds.

> **"I used free data, so at least it's clean."** Free, back-adjusted, survivorship-screened series encode decisions that were not known at the time (Section 5.1). Clean-looking is not point-in-time; the convenience of the feed is paid for in silent look-ahead you must actively reason about.

### 7.2 Glossary

- **Anomaly** — a documented, cross-sectional or time-series pattern in returns not explained by standard risk models; the raw material of factor investing and the subject of the replication crisis.
- **Replication crisis** — the finding that a large fraction of published empirical results, in finance and elsewhere, do not reproduce under careful or independent re-testing.
- **Post-publication decay** — the tendency of an anomaly's return to shrink after it is published, as informed capital arbitrages it; averaging roughly a 58% out-of-sample reduction across predictors (McLean & Pontiff 2016).
- **Time-series momentum (TSMOM)** — the tendency of an asset's own past return to predict its future return; long after positive trailing returns, short after negative (Moskowitz-Ooi-Pedersen 2012).
- **Specification sheet** — a written table resolving every implicit choice in a paper's rule to a single, ex-ante-justified value, frozen before results.
- **Researcher degree of freedom** — any analytical choice made after seeing the data that can be nudged to improve the result; each one inflates false discovery (the backtesting paper).
- **Realism ladder** — a sequence of steps (gross → costs → lag → post-publication sub-period) that subtracts successive layers of optimism from a replicated result.
- **Capacity** — the amount of capital an effect can absorb before market impact erodes it; a real anomaly can be untradeable at size.
- **Deflated Sharpe ratio** — a Sharpe estimate discounted for the number of trials that produced it and for non-normality, so that the best of many backtests is judged as an order statistic (Bailey & López de Prado 2014; the overfitting-control paper).
- **Profit factor** — gross profit divided by gross loss; a profit factor above 1 is profitable gross, and the metric used for the Section 6 VIX-gate case.
- **Walk-forward** — repeated re-selection and testing on rolling out-of-sample windows; stronger evidence than a single fixed split opened once.
- **Direction check** — the reflex of confirming that the *sign* of the data matches the *sign* of the claim before accepting any evidence (the backtesting paper).
- **HARKing** — Hypothesizing After the Results are Known: presenting a pattern found while exploring as though it were the hypothesis held in advance; the most flattering form of overfitting (the backtesting paper).
- **Order statistic** — the maximum (or another rank) of many draws; the best of *N* backtests is an order statistic of the trial distribution, systematically higher than any single true value, and must be judged as such.
- **Point-in-time data** — data reconstructed as it was actually known at each historical moment, including delistings and as-reported figures; the opposite of a survivorship-screened, back-adjusted convenience series.
- **Turnover** — how much of the position is traded per period; the multiplier on per-trade cost, so total cost drag ≈ turnover × per-trade cost (the backtesting paper).
- **SEWA** — smallest effect worth acting on: the pre-committed magnitude below which a statistically significant result is operationally irrelevant (the backtesting paper).
- **Factor crowding** — the erosion of a published factor's return as capital chases it, a mechanism behind post-publication decay and sudden factor drawdowns (Arnott et al. 2016).

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| Single-asset TSMOM sign rule on the S&P 500 earns only ~0.32 gross Sharpe, ~0.28 net-and-lagged, and is dominated by buy-and-hold (0.41 full-sample, 0.95 post-2012) | Own reproducible computation — `figures/fig_tsmom_haircut.py`; OOS split |
| The momentum lookback is unstable: in-sample vs out-of-sample Sharpe rank correlation is only 0.22 across 16 candidate lookbacks | Own reproducible computation — `figures/fig_param_sensitivity.py`; OOS split |
| On this one series TSMOM shows no post-publication decay — post-2012 Sharpe rises to 0.47 — a regime artifact, not a cross-sectional test | Own reproducible computation — `figures/fig_decay_split.py` |
| The VIX-gate variant lifts gross profit factor 1.32 → 1.44 (out-of-sample 1.62), but was selected post-hoc across ~20 variants | Own reproducible computation — private trade list, not redistributed; OOS split |
| Cross-sectional and time-series momentum are durable, independently documented effects | Literature — (Jegadeesh & Titman 1993; Moskowitz, Ooi & Pedersen 2012) |
| Roughly 65% of 452 published anomalies fail to replicate under uniform value-weighting | Literature — (Hou, Xue & Zhang 2020) |
| A newly proposed factor should clear roughly t > 3 to survive field-wide multiple testing | Literature — (Harvey, Liu & Zhu 2016) |
| Predictor returns decay about 58% out-of-sample after publication across 97 predictors | Literature — (McLean & Pontiff 2016) |
| Factor crowding turns popular "smart beta" strategies into post-publication disappointments | Literature — (Arnott, Beck & Kalesnik 2016) |
| The deflated Sharpe ratio discounts the best of N trials as an order statistic | Literature — (Bailey & López de Prado 2014) |
| Sourcing funnel: of ~20 abstracts skimmed, roughly one is worth a full day of replication | Practitioner consensus — not independently verified |

## References

- Arnott, R. D., Beck, N., & Kalesnik, V. (2016). *How Can "Smart Beta" Go Horribly Wrong?* Research Affiliates (public publication). Practitioner account of factor decay and crowding — why popular factors disappoint precisely when performance-chasing capital arrives. Public: <https://www.researchaffiliates.com/publications/articles/442_how_can_smart_beta_go_horribly_wrong>.
- Bailey, D. H., & López de Prado, M. (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting, and non-normality. *Journal of Portfolio Management, 40*(5), 94–107. The formal guard used in Section 6 for judging an in-sample-selected best as an order statistic. Open access: <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551>.
- Harvey, C. R., Liu, Y., & Zhu, H. (2016). …and the cross-section of expected returns. *Review of Financial Studies, 29*(1), 5–68. Argues that with hundreds of factors tested on one dataset the field is one giant multiple-comparison problem, so a new factor should clear roughly *t* > 3. Open access: <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2249314>.
- Hou, K., Xue, C., & Zhang, L. (2020). Replicating anomalies. *Review of Financial Studies, 33*(5), 2019–2133. Re-tests 452 anomalies under uniform value-weighted methodology; roughly 65% fail to replicate, mostly because they were microcap-driven. Open access (NBER w23394): <https://www.nber.org/papers/w23394>.
- Chen, A. Y., & Zimmermann, T. (2022). Open source cross-sectional asset pricing. *Critical Finance Review, 11*(2), 207–264. Hand-reproduces 319 published predictors and reports a replication rate near 100%, disputing the Hou-Xue-Zhang classification of anomalies as failures — the published counter-position to the replication-crisis prior (Section 3.4).
- Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers: Implications for stock market efficiency. *Journal of Finance, 48*(1), 65–91. The foundational cross-sectional momentum paper; a durable survivor of the anomaly zoo. Peer-reviewed journal article.
- McLean, R. D., & Pontiff, J. (2016). Does academic research destroy stock return predictability? *Journal of Finance, 71*(1), 5–32. Documents ~58% out-of-sample post-publication decay across 97 predictors; the empirical anchor of Section 3.3. Open access: <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623>.
- Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). Time series momentum. *Journal of Financial Economics, 104*(2), 228–250. The diversified, vol-scaled TSMOM paper replicated (in its plain single-asset form) in Section 5. Open access: <https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum>.

*All references above are publicly accessible: five are open-access papers or public practitioner publications with direct links given, and the remaining peer-reviewed journal articles are available through standard library access. No proprietary, course, or trading-academy material is cited, and the private trade list underlying the Section 6 case study is not redistributed — only aggregate statistics appear.*