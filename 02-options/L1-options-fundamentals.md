---
title: "Options Fundamentals"
last_updated: 2026-09-20
---

# Options Fundamentals

## Abstract

An option is a contract that separates the *right* to trade from the *obligation* to trade, and almost everything else about options follows from that one asymmetry. This paper builds the subject from nothing for a reader who knows only what a stock is. We start with what an option actually is — a right for the buyer, an obligation for the seller — and test the popular "insurance" analogy until it breaks. We then take a contract apart piece by piece (strike, expiry, the hundred-times multiplier, American versus European exercise, cash versus physical settlement), classify an option by its *moneyness*, and split its price into the part that is real today and the part that is paid for time and uncertainty. Payoff diagrams give the four building blocks and show why a position's value is a smooth bent curve before expiry and a sharp elbow at it. A no-free-lunch argument — *put-call parity* — is stated in plain words and then checked on a real option chain, which we also learn to read column by column. Three first combinations, the expiration calendar, and three costly misconceptions close the paper. Every figure uses free data and is reproducible.

## Keywords

Options, call, put, strike, expiry, premium, moneyness, intrinsic value, extrinsic value, payoff diagram, break-even, put-call parity, option chain, bid-ask spread, open interest, vertical spread, straddle, strangle, 0DTE, settlement

## 1 Introduction

### 1.1 Motivation and thesis

Most explanations of options begin with a formula and hope the intuition arrives later. This one begins with a single idea and lets everything else grow from it: *an option splits apart two things that a normal trade welds together — the right to make a trade and the obligation to make it.* When you buy a share of stock, you own something and you owe nothing further; the deal is done. When you buy an *option*, you own a *choice* — the right to trade a specific thing, at a specific price, until a specific date — and you can walk away from that choice for nothing more than what you already paid. The person on the other side has no choice at all: they took your money up front and must do whatever you decide.

That asymmetry — one side holds a right, the other carries an obligation — is the whole subject in miniature. It explains why an option has a price at all, why that price has two distinct parts, why the buyer's worst case and the seller's worst case are so wildly different, why the profit picture bends the way it does, and why a handful of contracts can be combined into shapes that a single stock position can never make. The thesis of this paper is therefore simple: *if you truly understand who holds the right and who carries the obligation, and what that costs, the rest of options is bookkeeping.* We will do that bookkeeping carefully, but the ideas underneath it are the point.

### 1.2 Scope, prerequisites, and what you can do after reading

This paper sits in the Trading Library's *Options* track. It is written for a complete beginner. The only thing it assumes is that you know what a *stock* is — a share of ownership in a company, whose price moves up and down — and that you are comfortable with arithmetic: addition, subtraction, multiplication, and reading a simple chart. There is no calculus here, no statistics, and no jargon that is not explained the first time it appears. Every technical term is set in *italics* at first use and defined on the spot.

After reading this paper, you will be able to:

- say precisely what a *call* and a *put* are, and who holds the right versus the obligation on each side of the trade;
- read a real option contract's specification — its *strike*, *expiry*, *multiplier*, exercise style, and settlement — and know what each one changes;
- classify any option as *in*, *at*, or *out of the money*, and split its price into *intrinsic* and *extrinsic* value;
- draw the payoff of a long or short call and put by hand, find its *break-even*, and explain why the curve is bent before expiry;
- state *put-call parity* in one sentence and recognize what a violation of it would mean;
- read an *option chain* column by column — bid, ask, spread, volume, and open interest — and know which numbers are a cost and which are information;
- recognize a *vertical spread*, a *straddle*, and a *strangle* on sight and say what each is for;
- and see through three of the most expensive beginner misconceptions about options.

### 1.3 Data and reproducibility

Every figure and every number in a figure uses *freely available data* or needs no data at all. The didactic payoff diagrams are pure arithmetic; the two figures that touch the real market use delayed option quotes published for free by the Cboe (the exchange that lists the contracts we use as examples). Each figure names the script that reproduces it, and the downloaded snapshot is cached so the figure is stable and offline-reproducible. *This is a research and educational document, not investment advice.* Options can lose money quickly, and the seller's risk in particular can exceed the amount first received; nothing here is a recommendation to trade.

### 1.4 Organization of this paper

The paper is complete: every section below is written in full, in the order a beginner should meet the ideas. Each builds on the one before, so it rewards reading straight through.

- **Section 2 What an option actually is** — the right-versus-obligation split; buyer and seller as mirror images; calls and puts in one picture; the insurance analogy and exactly where it breaks.
- **Section 3 Contract anatomy** — strike, expiry, and the hundred-times multiplier; American versus European exercise; cash versus physical settlement, and AM versus PM settlement, with the SPX/SPY pair as the canonical example; how index, equity, and futures options differ.
- **Section 4 Moneyness and the two parts of price** — in, at, and out of the money; intrinsic versus extrinsic value; why extrinsic value exists at all, and the first informal meeting with *volatility*.
- **Section 5 Payoff diagrams** — the four primitives with their break-evens (Figure 1); profit and loss at expiry versus before it, and why the curve is bent (Figure 2).
- **Section 6 Put-call parity** — the no-free-lunch argument in plain words; the formula decoded term by term; what a violation would mean; and a check on a real chain (Figure 3).
- **Section 7 Reading an option chain** — bid, ask, mid, and the spread as a cost; volume versus open interest as flow versus stock; a real SPX chain walked column by column (Figure 4).
- **Section 8 First combinations** — the vertical spread, the straddle, and the strangle, with payoff and purpose (Figure 5) — a preview, not a strategy catalogue.
- **Section 9 The expiration landscape** — monthlies, weeklies, and dailies; what *0DTE* means; and *OPEX*, terms you will meet again in the dealer-flows-and-GEX paper.
- **Section 10 Common misconceptions** — "options are lottery tickets," "selling premium is free income," and "delta is the probability of profit."
- **Section 11 Glossary** — about forty terms, defined compactly for reference.

## 2 What an option actually is

### 2.1 A right on one side, an obligation on the other

An *option* is a contract between two people about a future trade in some *underlying* — the thing the option is written on, usually a stock or a stock index. The contract names one specific price and one specific deadline. The *buyer* of the option pays a fee, called the *premium*, once and up front. In exchange, the buyer receives a right: the right to make the named trade at the named price, any time the contract allows, up to the deadline. The buyer never has to use that right. If using it would lose money, the buyer simply does nothing and the contract expires worthless; the most the buyer can ever lose is the premium already paid.

The *seller* of the option — also called the *writer* — is in the opposite position, and it is worth stating starkly because everything downstream depends on it. The seller receives the premium up front and in return takes on an obligation. If the buyer chooses to trade, the seller *must* take the other side, at the named price, whether or not that is a good deal for the seller at the time. The seller has no choice; the buyer has all of it.

This is the *asymmetry* at the heart of options, and it is unlike a normal stock trade. When two people trade a share, each gives up something and gets something, and afterward they are quits — neither owes the other anything. When two people trade an option, one of them keeps a live obligation for the whole life of the contract. That is what the premium pays for: the buyer is paying the seller to carry a risk and to surrender a choice.

Two more words make the rest of the paper readable. A trader who owns an option — who paid the premium and holds the right — is said to be *long* that option. A trader who sold an option — who collected the premium and carries the obligation — is said to be *short* it. "Long" and "short" here mean exactly "owns" and "owes," nothing more.

### 2.2 Calls and puts in one picture

There are exactly two kinds of option, and they differ only in which direction the right points.

A *call* is the right to *buy* the underlying at the named price. You would want to use a call when the underlying has risen above that price, because the call lets you buy cheap and the market lets you sell dear. A call buyer is betting, loosely, that the underlying goes *up*.

A *put* is the right to *sell* the underlying at the named price. You would want to use a put when the underlying has fallen below that price, because the put lets you sell high into a market that has gone low. A put buyer is betting, loosely, that the underlying goes *down* — or is buying protection against exactly that.

Putting the two sides and the two kinds together gives four elementary positions, and it is worth holding all four in your head at once because they recur constantly:

| Position | Holds | On the underlying going | Pays or receives premium | Worst case |
|---|---|---|---|---|
| **Long call** | right to buy | up | pays | loses the premium |
| **Short call** | obligation to sell | (against a rise) | receives | very large (see Section 2.3) |
| **Long put** | right to sell | down | pays | loses the premium |
| **Short put** | obligation to buy | (against a fall) | receives | large but bounded |

The named price in all of this has a proper name — the *strike price*, or just *strike* — and the deadline is the *expiration*, or *expiry*. We take those apart in Section 3. For now, notice the pattern in the table: the two buyers each risk only their premium, while the two sellers have collected a small premium against a much larger possible loss. That lopsidedness is not an accident of these examples; it is the structural shape of option selling, and Section 10 returns to it.

### 2.3 Why the seller's worst case is so different

Consider a concrete call. Someone sells you the right to buy one share at a strike of 100, and you pay a premium of 5. If the share finishes at 130, you use your right: you buy at 100 and could sell at 130, a gross gain of 30, less the 5 you paid, for a net of 25. The seller had to hand you a 130-dollar share for 100 dollars, a 30-dollar loss, softened only by the 5 they collected — a net loss of 25. Your 25 gain is exactly the seller's 25 loss. Options are *zero-sum* between the two parties before fees: every dollar you make is a dollar the seller loses, and vice versa.

Now push the share higher. At 200 your net is 95 and the seller's loss is 95; at 300 it is 195 each way. There is no ceiling. A stock can, in principle, rise without limit, so the seller of a call carries an *unbounded* worst case for a premium that was fixed and small. The put seller's worst case is merely *large*: a stock can only fall to zero, so the most a put seller can lose is the strike minus the premium they collected. The buyer of either contract, meanwhile, can never lose more than the premium — that is the whole meaning of holding a right you are free not to use.

### 2.4 The insurance analogy, and where it breaks

The most useful first analogy for a put is *insurance*, and it is worth taking seriously precisely so we can see where it fails. If you own a stock and buy a put on it, you have bought a kind of insurance policy: you pay a premium up front, and if the stock's price "crashes" below the strike, your put pays you the difference, just as a policy pays out after a loss. The strike behaves like the point below which you are covered; the premium behaves like the annual insurance cost; the expiry behaves like the end of the coverage period. The option *seller* plays the insurer, collecting many small premiums and occasionally paying a large claim.

The analogy is genuinely good, and then it breaks in four specific places, each of which teaches something.

First, you can buy the "insurance" on something you do not own. Nothing stops you from buying a put on a stock you have no position in — that is not protection, it is a bet that the stock falls. It is as if you could insure your neighbor's house and collect when it burns down. Options detach the protection from the thing being protected.

Second, the "policy" is freely tradable. You can sell your put to someone else at any time before expiry, at whatever the market will pay, and pocket the change in its value. Real insurance policies are not bought and sold on an open market minute by minute; options are, and most option positions are closed by trading them away, not by exercising them.

Third, the "insurer" can be anyone, and can get out. The seller is not a regulated insurance company with reserves; it is another trader who can buy the same option back to cancel the obligation. The market, through a clearinghouse, guarantees the trade so the two of you never have to trust each other directly — a point Section 3 returns to.

Fourth, and most important, the payout does not require a real-world loss. An insurance claim requires that something actually happened to you. An option pays purely on the number: if the price is past the strike at the right moment, the option is worth money, whether or not you suffered anything. This is what lets options be used to speculate as easily as to protect, and it is why a call — the right to *buy* — has no clean insurance reading at all. Insurance protects against loss; a call is a leveraged bet on a gain. The analogy covers the put and stops there.

## 3 Contract anatomy

An option contract is defined by a small number of terms, each of which changes what the contract is worth or how it settles. This section names them one at a time.

### 3.1 Strike, expiry, and the multiplier

The *strike price* is the fixed price at which the right can be exercised — the "named price" of Section 2. A call with a strike of 100 is a right to buy at 100 no matter where the market goes; a put with a strike of 100 is a right to sell at 100. The strike never changes over the life of the contract; the market price moves around it, and the option's value comes from the gap between the two.

The *expiration* is the date on which the right ends. After expiry the contract no longer exists: either it was used (exercised) or it lapsed worthless. The length of time from now until expiry is the *time to expiry*, and it matters enormously — a right that lasts a year is worth more than the identical right that lasts a day, because more can happen. We make that precise in Section 4.

The *contract multiplier* is the least glamorous term and the one beginners most often forget, so it is worth stating loudly. A listed option almost never controls one share. A standard equity option controls *one hundred* shares, and its quoted premium is *per share*. A call quoted at 5 therefore costs 5 × 100 = 500 dollars to buy, and controls 100 shares of the underlying. For index options the multiplier is a fixed dollar amount per index point — for the S&P 500 index options we use as examples, *one hundred dollars per index point*. A quoted price of 108.70 on such a contract is thus 108.70 × 100 = 10,870 dollars. Every premium, break-even, and payoff in this paper is stated *per share* or *per index point* — the honest, comparable unit — but the money that actually moves is that number times the multiplier. Forget the multiplier and you will misjudge your risk by a factor of a hundred.

### 3.2 American versus European exercise

Options come in two *exercise styles*, and the difference is about *when* the right may be used.

An *American* option may be exercised at any time up to and including expiry. An *American-style* call on a stock, for instance, can be turned into shares on any trading day the holder likes. Most options on individual stocks and on stock ETFs are American-style.

A *European* option may be exercised only *at* expiry, not before. This does not mean you are trapped in the position — you can still *sell* the option to someone else at any time — it only means you cannot force the underlying trade early. Most *index* options, including the S&P 500 index options used later, are European-style.

The practical consequence for a beginner is small but real: the holder of an American option carries a little extra flexibility (and the writer carries a little extra risk of being *assigned* — forced to fulfill the obligation — earlier than expected, especially around dividends), while European options remove that early-exercise complication entirely. That simplicity is one reason index options are a cleaner teaching example, and it is also why the tidy no-free-lunch relationship of Section 6 holds as an exact equality for them.

### 3.3 Settlement: cash versus physical, AM versus PM

*Settlement* is what actually happens when an option is exercised — how the obligation is discharged.

Under *physical settlement*, the underlying really changes hands: exercising a call means you pay the strike and receive the shares; exercising a put means you deliver the shares and receive the strike. Options on individual stocks and on ETFs settle physically.

Under *cash settlement*, no shares move; instead the two parties exchange the *cash difference* between the settlement price and the strike. Index options settle in cash, for the obvious reason that you cannot deliver "the S&P 500" as a physical thing. If a cash-settled call with strike 7,650 settles at an index level of 7,700, the holder simply receives (7,700 − 7,650) × 100 = 5,000 dollars and the position is closed.

There is a further wrinkle in *when* the settlement price is measured, and it produces the single most useful canonical pair in options education: *SPX versus SPY*. Both track the S&P 500. SPY is an ETF; options on it are American-style, physically settled in ETF shares, and expire on a *PM settlement* basis — their value is fixed from the closing price. SPX is the index itself; its options are European-style and cash-settled, and the traditional monthly contract uses *AM settlement* — its final value is struck from a special calculation based on the opening prices of the index's members on expiration morning, not the close. A trader holding an SPX AM-settled option therefore does not know its final value from Thursday's close or even Friday's open on screen; it is set by the official opening print. The lesson for now is only that two options can track the very same market and still settle by different rules, on different clocks, into different things — and that the fine print decides what you actually own.

### 3.4 Index, equity, and futures options

Finally, the same machinery is written on three broad kinds of underlying, and it is worth naming them so the vocabulary is not surprising later.

*Equity options* are written on a single company's stock (or on an ETF). They are American-style, physically settled, and controlled by the hundred-share multiplier of Section 3.1.

*Index options* are written on a stock index, such as the S&P 500. They are typically European-style and cash-settled, with a dollars-per-point multiplier. Because there is no early exercise and no delivery, they are mechanically the simplest, which is why this paper's real-data figures use them.

*Futures options* are written not on a stock or an index directly but on a *futures contract* — itself an agreement to trade something later. These are common in commodities and in the index-futures market that professional traders use around the clock. Their exercise usually delivers a futures position rather than shares. We mention them only so the word is not new when you meet it; the ideas in this paper transfer to them unchanged.

## 4 Moneyness and the two parts of price

### 4.1 In, at, and out of the money

*Moneyness* is the word for where an option's strike sits relative to the current price of the underlying — and it is the single most useful classification of an option, because it tells you at a glance whether the option is worth anything right now.

Take the current underlying price and compare it to the strike:

- A call is *in the money* (ITM) when the underlying is *above* the strike — you could buy below the market and be ahead. A put is in the money when the underlying is *below* the strike.
- An option is *at the money* (ATM) when the strike is essentially equal to the current price.
- A call is *out of the money* (OTM) when the underlying is *below* the strike — exercising would mean buying above the market, so you would not. A put is out of the money when the underlying is *above* the strike.

A one-line memory aid: an option is in the money exactly when you would use it right now if forced to, at the money when it is on the fence, and out of the money when you would decline. Because moneyness is measured against the moving underlying, an option's classification changes through the day as the price moves — an out-of-the-money call becomes at-the-money and then in-the-money as the underlying rallies through its strike.

### 4.2 Intrinsic and extrinsic value

An option's price splits cleanly into two parts, and separating them is the most important arithmetic in this paper.

The *intrinsic value* is the part of the price that is real *right now* — the money you would capture if the option expired this instant. For a call it is the underlying price minus the strike, but never less than zero (a right you would not use is worth nothing, not a negative amount). For a put it is the strike minus the underlying price, floored at zero. An in-the-money call with the underlying at 130 and a strike of 100 has intrinsic value 130 − 100 = 30. An out-of-the-money option has zero intrinsic value, always.

The *extrinsic value* — also called *time value* — is everything else in the price: the amount by which the option's market price exceeds its intrinsic value. If that same 100-strike call is trading at 34 while its intrinsic value is 30, then 34 − 30 = 4 is extrinsic value. An at-the-money or out-of-the-money option has *zero* intrinsic value, so its entire price is extrinsic. This is why cheap-looking out-of-the-money options are "all time value": there is nothing real in them yet, only the possibility of something.

The identity to carry away is simply:

> **option price = intrinsic value + extrinsic value**, where intrinsic value is what you would collect on the spot and extrinsic value is what you are paying for what might still happen.

One caveat matters for the European index options this series leans on. A European option cannot be exercised early, so its intrinsic value is properly measured against the *forward*, not the spot: the clean split for a put is price = max(0, K·e^(−rT) − S·e^(−qT)) intrinsic + extrinsic, and the mirror for a call. Measured against *spot* intrinsic instead, a deep-in-the-money European option can trade a little *below* what looks like its intrinsic value — on a real SPX chain a deep-in-the-money 8,000-strike put changes hands roughly twenty points under its spot-based K − S — because the payoff is locked until expiry and discounted. So "time value is never negative" holds for American options, where early exercise floors the price, and for the forward-based split; it is not exact for the naive spot-based split on European options. The gap is negligible near the money and only bites deep in the money.

### 4.3 Why extrinsic value exists at all — the first sight of volatility

Why would anyone pay 4 for the *possibility* in an at-the-money option when its intrinsic value is zero? Because before expiry the underlying can still move, and the option's owner gets to keep the good moves while walking away from the bad ones. That one-sided exposure — all of the upside, none of the extra downside beyond the premium — is worth money, and extrinsic value is its price.

Two ingredients set the size of extrinsic value, and both point the same way. The first is *time*: the more time remains before expiry, the more the underlying can wander, so the more that one-sided exposure is worth. As expiry approaches, extrinsic value drains away — a process called *time decay* — until, at the moment of expiry, there is no more "might happen" left and the option is worth exactly its intrinsic value, no more. The second ingredient is how *jumpy* the underlying is expected to be. A calm stock that barely moves offers little chance of a big favorable swing; a wild one offers a lot. This expected jumpiness has a name — *volatility* — and when it is inferred from option prices themselves it is called *implied volatility*.

You do not need any formula for volatility here. You need only the intuition, because it will organize everything that comes later: *extrinsic value is the market's price for time and uncertainty, and volatility is the name for the uncertainty part.* Two options identical in every visible term — same underlying, same strike, same expiry — can trade at different prices only if the market disagrees about how much the underlying might move. That disagreement, made into a number, is where the entire next level of the subject begins.

## 5 Payoff diagrams

### 5.1 The four primitives and their break-evens

The cleanest way to see what an option does is to draw its *payoff diagram*: a picture with the underlying's price at expiry along the bottom and your profit or loss up the side. Because the four elementary positions of Section 2.2 are the building blocks of everything else, we draw all four at once in Figure 1, using a strike of 100, a call premium of 5, and a put premium of 4.

Read the top-left panel — the *long call* — slowly, because the other three are variations on it. Below the strike of 100 the call is out of the money and you would not exercise it, so your result is flat: you are simply out the 5 you paid. Above the strike the call gains a dollar for every dollar the underlying rises, so the line slopes up. Somewhere on the way up you get back to zero: that point is the *break-even*, the underlying price at which your gains exactly repay your premium. For a long call the break-even is strike plus premium, here 100 + 5 = 105. Below 105 you are down (at most the 5 premium); above 105 you are ahead, with no ceiling. The long put in the panel below mirrors this on the downside: its break-even is strike minus premium, 100 − 4 = 96, its maximum loss is the 4 premium, and its maximum gain is 96 (reached only if the underlying goes to zero).

The bottom row is the sellers, and here is the elegant part: each seller's line is the exact mirror image of the buyer's line above it, flipped across the horizontal zero line. That is Section 2.3 made visible — the trade is zero-sum, so wherever the buyer gains the seller loses by the identical amount. The *short call* has a small fixed maximum gain (the 5 premium) and an *unlimited* loss as the underlying rises; the *short put* has a maximum gain of its 4 premium and a large but bounded loss of 96. Nothing in these pictures is a strategy; they are the alphabet. Learn to see any option position as some sum of these four bent lines and you can read any payoff in the paper.

![The four building blocks at expiry, per share, before fees: long call, long put, short call, short put, with strike K = 100, a call premium of 5, and a put premium of 4. Break-evens are marked at 105 for the call and 96 for the put. Top row = buyers, bottom row = sellers; each seller's line is the mirror image of the buyer's above it, because the trade is zero-sum and money only changes sides. Reproduce with figures/fig_payoff_primitives.py.](figures/fig_payoff_primitives.png)

### 5.2 At expiry versus before it — why the curve is bent

Figure 1 shows payoff *at expiry*, when there is no time left and the picture is all sharp elbows. But an option lives for weeks or months before that, and for most of its life its value traces a *smooth, bent curve* rather than a kinked line. Figure 2 shows this for a single long call — an at-the-money call with thirty days to run, priced in a standard option-pricing model at a premium of 2.45, with a break-even at expiry of 102.45.

Two things in that picture are worth more than any formula. First, follow the curves from thirty days left, to ten, to one, down to the sharp elbow at expiry: as time runs out the smooth curve straightens toward the elbow. The kink that defines the payoff only appears *at the very end*; before then, value bends continuously. That bend is the visible fingerprint of extrinsic value, and it is the doorway to the *greeks* — the sensitivities the greeks-and-hedging paper is built on — but you can see its shape here with no mathematics at all.

Second, notice what happens if the underlying simply sits still at 100. With thirty days left the position is at break-even (you paid 2.45 and the option is worth 2.45); with ten days left, held at the same 100, it is worth about 1.08 less; with one day left, about 2.03 less. The underlying never moved, and the buyer still lost money — because time drained the extrinsic value away. This is *time decay* from Section 4.3, and it is the quiet cost the option buyer pays every day for the privilege of holding a right that "might" pay off. The seller, mirror-image as ever, collects exactly that decay as their reward for carrying the obligation. Keep this asymmetry in mind for Section 10.

![A 30-day at-the-money call in a standard option-pricing model (stock = strike = 100, volatility 20 percent per year, interest 4 percent, no dividends): the premium paid is 2.45 and the break-even at expiry is 102.45. Before expiry the profit-and-loss curve is smooth and bent, not a sharp elbow; and it sinks day by day even at an unchanged stock price — held at 100 the position is worth about 1.08 less with 10 days left and 2.03 less with 1 day left, the buyer paying time decay. Reproduce with figures/fig_payoff_before_expiry.py.](figures/fig_payoff_before_expiry.png)

## 6 Put-call parity

### 6.1 The no-free-lunch argument in plain words

Calls and puts are not independent prices that the market sets in isolation. They are locked together by an argument so simple it needs no mathematics to state: *two recipes that deliver the same meal must cost the same, or someone gets a free lunch.*

Here are two recipes. Recipe A: buy a call at strike K, and set aside enough cash to have exactly K on hand at expiry. Recipe B: buy the underlying today, and buy a put at the same strike K. Now ask what each recipe is worth at expiry, in every possible world:

- If the underlying finishes *above* K, Recipe A exercises the call — pays K from the set-aside cash, receives the underlying — and ends holding the underlying. Recipe B already holds the underlying and lets the put lapse. Both end holding the underlying. Equal.
- If the underlying finishes *below* K, Recipe A lets the call lapse and keeps the cash K. Recipe B exercises the put — sells the underlying for K — and ends holding K in cash. Both end holding K. Equal.

In every possible world the two recipes end with exactly the same thing. So they must cost the same today — otherwise you could buy the cheap recipe, sell the expensive one, and pocket the difference with no risk and no capital of your own at stake. That risk-free, capital-free profit is called *arbitrage*, and the working assumption of any functioning market is that such free lunches are competed away almost instantly. The relationship the argument forces on option prices is *put-call parity*.

### 6.2 The formula, decoded term by term

Written out, the equality of the two recipes rearranges into the compact form beginners will see everywhere:

> **C − P = S − K · e^(−rT)**

Take it one symbol at a time, because each has a plain meaning:

- **C** is the price of the call and **P** the price of the put — same underlying, same strike, same expiry. Their *difference* is the left side.
- **S** is the current price of the underlying.
- **K** is the shared strike.
- **r** is the *risk-free interest rate* — roughly, what safe cash earns over the period — and **T** is the time to expiry measured in years.
- **e^(−rT)** is a *discount factor*: the value *today* of one dollar to be received at expiry. It is slightly less than 1, because a dollar later is worth a little less than a dollar now. Multiplying the strike by it, **K · e^(−rT)**, gives the *present value* of the strike — the amount of cash you would set aside today to have exactly K at expiry. That is the "set aside enough cash" step of Recipe A.

So the whole right-hand side, S − K · e^(−rT), is the cost today of owning the underlying while deferring payment of the strike until expiry — and parity says that difference must equal the difference between the call and put prices. Rearranged, it also says you can build any one of the four instruments (call, put, underlying, cash) out of the other three. The call and the put are two views of the same object, separated only by the underlying and a little interest.

### 6.3 What a violation would mean — and a check on a real chain

If put-call parity failed by more than trading costs, it would mean a genuine free lunch was sitting on the screen: you could assemble the cheaper recipe, sell the dearer one, and lock in a profit that no future price movement could take away. In deep, liquid markets that essentially never happens, and it is instructive to see how tightly the relationship binds on real quotes.

Figure 3 checks parity on a real S&P 500 index (SPX) option chain — a delayed snapshot published free by the Cboe, taken on 2026-09-17 with the index at 7,637.76 and the October 16, 2026 expiry, 29 days out. For every one of the 447 strikes that had a live two-sided quote on both the call and the put, we take the call-minus-put difference from the mid quotes and plot it against the strike. The result is not a cloud; it is a straight line, exactly as parity demands. Fitting that line back-recovers the market's own numbers with no outside input: an implied *interest rate* of 4.48 percent and an implied *forward* price of 7,658.74 for the index at that expiry.

There is one honest subtlety, and it is a teaching gift. The simple textbook line S − K · e^(−rT) assumes the underlying pays no dividends. The S&P 500 does pay dividends, and the picture shows it: the real quotes sit a near-constant 6.4 index points off the no-dividend line — that gap *is* the present value of the dividends the index will pay before expiry, which the naive formula ignores. Once we account for it (by fitting the line the market actually respects), the leftover scatter — the honest measure of any real, tradable parity violation — is tiny: a typical deviation of just 0.29 point, and a worst case under 2 points across a chain quoted in thousands. Parity is not an approximation that mostly holds; on real quotes it is essentially exact, and the small residual it leaves over is itself information (the dividend stream), not noise.

![Put-call parity on a real SPX option chain (Cboe delayed snapshot, 2026-09-17, index 7,637.76, October 16 2026 expiry, 29 days). For all 447 strikes with a live two-sided quote on both legs, the call-minus-put mid quote falls on one straight line; fitting it recovers an implied interest rate of 4.48 percent and an implied forward of 7,658.74. The near-constant 6.4-point gap to the textbook no-dividend line is the present value of dividends, and around the dividend-adjusted line the typical deviation is only 0.29 point. SPX options are European-style, so parity applies as an equality. Reproduce with figures/fig_parity_check.py.](figures/fig_parity_check.png)

## 7 Reading an option chain

### 7.1 The layout, and bid, ask, and mid

Everything so far has been about one option at a time. In practice you look at a whole grid of them at once — an *option chain* — and learning to read it is a concrete skill. The classic layout puts the calls on the left, the puts on the right, and the list of strikes down the middle, one row per strike, so that a single row shows the call and the put that share a strike. Figure 4 is a real SPX chain in exactly this layout, from the same delayed Cboe snapshot as Section 6.

Start with the price columns. The *bid* is the highest price a buyer is currently willing to pay; the *ask* (or *offer*) is the lowest price a seller is currently willing to accept. They are two different numbers, and the honest single price for an option is usually taken as the *mid* — the midpoint of the two. In Figure 4 the at-the-money 7,650 call shows a bid of 108.30 and an ask of 109.10, so its mid is (108.30 + 109.10) / 2 = 108.70.

### 7.2 The spread is a cost, not a price

The gap between bid and ask — here 109.10 − 108.30 = 0.80 point — is the *bid-ask spread*, and it is one of the most important numbers on the screen for a beginner to respect. It is a cost you pay just to get in and out. If you buy at the ask (109.10) and immediately sell at the bid (108.30), you are down 0.80 point before the market has moved at all — the spread went to the market-maker on the other side. Expressed against the mid, that is 0.80 / 108.70 ≈ 0.7 percent, round-trip, for doing nothing.

Two rules of thumb follow. First, a *wide* spread is expensive; a *narrow* spread is cheap; and spreads are widest exactly where beginners are tempted — in thinly traded, far-out-of-the-money options that look cheap in absolute terms but cost a large fraction of their value to trade. Second, because the multiplier of Section 3.1 turns every point into a hundred dollars, a spread that looks like "less than a point" is real money: 0.80 point on this contract is 80 dollars of round-trip friction per contract. Read the spread as a toll booth you pass through twice.

### 7.3 Volume versus open interest — flow versus stock

Two more columns matter, and beginners routinely confuse them because both sound like "how much is going on." They measure completely different things.

*Volume* is the number of contracts *traded* during the current day. It resets to zero every morning and counts activity — the *flow*. High volume means a lot of that contract changed hands today.

*Open interest* is the number of contracts *currently outstanding* — positions that have been opened and not yet closed. It is updated once per day, overnight, and it counts standing positions — the *stock*, in the inventory sense of the word. High open interest means a lot of that contract is being *held*.

The distinction is easiest to feel with an analogy: volume is how many cars drove past your window today; open interest is how many cars are parked on the street right now. In Figure 4 the 7,650 call shows an open interest of 7,116 contracts against a volume of 652 that day — a strike where far more is *held* than *traded* today. The two numbers answer different questions: volume tells you where attention is *right now*, open interest tells you where positions have *accumulated*. Both are useful, and confusing them — reading today's flow as if it were the standing inventory — is a classic beginner error that later levels of this track are careful to avoid.

![A real SPX option chain read column by column (Cboe delayed snapshot, 2026-09-17, index 7,637.76, October 16 2026 monthly, 29 days out): calls on the left, puts on the right, strikes down the middle. The at-the-money 7,650 call quotes 108.30 bid / 109.10 ask (mid 108.70, spread 0.80 point, about 0.7 percent of mid); its open interest is 7,116 contracts against 652 traded that day. Shading marks the in-the-money half of each side. Contract multiplier: 100 dollars per index point. Reproduce with figures/fig_chain_annotated.py.](figures/fig_chain_annotated.png)

## 8 First combinations

The four primitives of Section 5 can be added together, and a few standard sums are common enough to have names. This section previews three of them — it is deliberately *not* a catalogue of strategies. The single idea to take away is that *a combination adds hockey sticks together*: it never conjures a new payoff from nothing, it only trades away profit in one region to buy a cheaper or safer shape in another. Figure 5 draws all three, built from the same didactic premiums as Section 5.

### 8.1 The vertical spread

A *vertical spread* combines two options of the same kind and expiry but different strikes — buying one and selling the other. The version in Figure 5 is a *bull call spread*: buy the 100-strike call and simultaneously sell the 110-strike call. The premium you pay for the lower call is partly funded by the premium you collect on the higher one, so the net cost — the *debit* — is only 3 rather than the 5 of the bare call. In exchange you give up all profit above 110: your gain is *capped* at 7 (the 10-point distance between strikes minus the 3 you paid), and your break-even improves to 103. **Purpose:** a cheaper, defined-risk way to express a moderately bullish view when you do not need unlimited upside.

### 8.2 The straddle and the strangle

A *straddle* buys the call *and* the put at the same strike and expiry — in Figure 5, the 100-strike call and put together, for a combined debit of 9. Its payoff is a V: you lose the most if the underlying sits exactly at 100 (both options expire worthless) and you profit if it moves far enough in *either* direction, with break-evens at 91 and 109. **Purpose:** a bet on a *big move* whose direction you do not know — you are long volatility itself, and you need a swing larger than the 9 you paid to come out ahead.

A *strangle* is the cheaper cousin: buy an out-of-the-money put and an out-of-the-money call — here the 95-strike put and the 105-strike call — for a smaller combined debit of 4.5. Because both options start out of the money, the position costs less, but it needs a *larger* move to pay off, with break-evens pushed out to 90.5 and 109.5. **Purpose:** the same "big move, unknown direction" bet as the straddle, bought more cheaply in return for requiring more movement.

Notice the recurring trade-off in all three: every combination lowers a cost or a risk *somewhere* only by surrendering a payoff *somewhere else*. That conservation — you pay for every good feature by giving up another — is the honest heart of options structuring, and it is why there is no combination that is simply "better" than a single option in every respect.

![Three first combinations at expiry, per share, built from the primitives with the same didactic premiums: a bull call spread (long 100-call, short 110-call; cost 3, break-even 103, capped gain 7), a long straddle (long 100 call and put; cost 9, break-evens 91 and 109), and a long strangle (long 95-put, long 105-call; cost 4.5, break-evens 90.5 and 109.5). Combinations add hockey sticks together; they buy a cheaper or safer shape by giving up profit somewhere else. Reproduce with figures/fig_combos.py.](figures/fig_combos.png)

## 9 The expiration landscape

The final piece of vocabulary is the calendar. Options do not all expire on one day; a given underlying has many expirations listed at once, and a beginner should know the ladder.

The oldest rung is the *monthly* expiration — traditionally the third Friday of each month. For decades this was the option expiration, and the monthly SPX contract is the AM-settled, European, cash-settled contract of Section 3.3. The acronym *OPEX* (options expiration) usually refers to this monthly event, and the quarterly ones — March, June, September, December — are larger still because index futures and options expire together, an event colloquially called *triple witching*.

Over time the exchanges added *weekly* expirations — contracts expiring on other Fridays, and then on other weekdays — so that at any moment many nearby expiries are available. Most recently, and most consequentially, came *daily* expirations: for major index products such as SPX there is now an expiration *every* trading day, Monday through Friday.

That last development gives the term you will hear most often: *0DTE*, which stands for *zero days to expiration* — an option on its own expiration day, with only hours of life left. Because all of an option's remaining extrinsic value must drain away by the close (Section 4.3), the final hours of a 0DTE option are where time decay, and the market forces that surround expiration, are at their most concentrated. At this stage that is all you need: 0DTE means "expiring today," and it is a large and fast-moving part of the modern index-options market rather than an exotic corner.

These calendar terms — monthly, weekly, daily, 0DTE, OPEX — are set down here only as vocabulary. They come back with real weight in the dealer-flows-and-GEX paper, where the *behavior* of the underlying around expiration (and the dealer-hedging forces that can concentrate prices near heavily-held strikes) becomes the subject in its own right. For now, know the words and the ladder they name.

## 10 Common misconceptions

Three beliefs about options are common, comfortable, and wrong in a way that costs beginners money. Each is worth dismantling with nothing more than the arithmetic already in this paper.

**"Options are lottery tickets."** There is a grain of truth here, which is exactly why it misleads. A far *out-of-the-money* option is cheap and occasionally pays off enormously, which does feel like a lottery ticket — and, like a lottery ticket, its buyer usually receives nothing, because the underlying rarely travels far enough before the extrinsic value decays to zero (Section 5.2). But "option" is a whole category, not that one corner of it. An at-the-money option, a covered position, or a defined-risk spread behaves nothing like a lottery ticket. The error is treating the most speculative sliver of the category as if it were the category. If you *only ever* buy cheap, far-out-of-the-money options, you have indeed chosen the lottery-ticket strategy — but that is a choice you made, not a fact about options.

**"Selling premium is free income."** Selling options brings in cash immediately, and because the seller wins on the large majority of quiet days, it *feels* like income. Figure 1 shows why it is not free. The short call and short put collect a small, fixed premium against a loss that is large (the put) or unlimited (the call). The profit arrives often and small; the loss arrives rarely and large. Collecting 5 many times over does not make you rich if a single move costs you 95 — and the market prices the premium precisely so that, on average and before skill, the two roughly offset. The premium is not income; it is *payment for carrying a risk*, and the risk is real even when it has not shown up yet. Judging the strategy by its win rate rather than by the size of its rare losses is the trap, and it is the beginner error that later levels of this library treat with the most care.

**"Delta is the probability of profit."** *Delta* is a greek — a sensitivity you will meet properly in the greeks-and-hedging paper — and it is often loosely quoted as "the probability the option finishes in the money." Even taken at face value that is a probability of *finishing in the money*, which is not the same as a probability of *profit*. To profit as a buyer you must recover the premium first, so your break-even lies *beyond* the strike (Section 5.1): a long call with a strike of 100 and a premium of 5 does not pay until 105, so the chance of *profit* is smaller than the chance of merely finishing above 100. Worse, the "probability" that delta approximates is a *pricing-model* probability used for hedging, not a real-world forecast of the odds. Two separate errors compound here — confusing "in the money" with "profitable," and confusing a model's internal number with a real-world likelihood — and both flatter the buyer into overestimating their chances. Delta is a useful sensitivity; it is not your odds of making money.

## 11 Glossary

- **American option** — an option exercisable at any time up to and including expiry (typical for equity and ETF options).
- **Ask (offer)** — the lowest price at which someone is currently willing to sell an option.
- **Assignment** — being selected, as an option seller, to fulfill the obligation when a buyer exercises.
- **At the money (ATM)** — a strike essentially equal to the current price of the underlying.
- **Bid** — the highest price at which someone is currently willing to buy an option.
- **Bid-ask spread** — the gap between bid and ask; a round-trip trading cost, not a price.
- **Break-even** — the underlying price at which a position's profit is exactly zero (for a long call, strike plus premium; for a long put, strike minus premium).
- **Bull call spread** — buying a lower-strike call and selling a higher-strike call of the same expiry; a cheaper, capped bullish position.
- **Call** — the right to *buy* the underlying at the strike.
- **Cash settlement** — settling an exercised option by exchanging the cash difference rather than delivering the underlying (typical for index options).
- **Contract multiplier** — the number of underlying units (or dollars per point) one contract controls; 100 shares for standard equity options, 100 dollars per index point for the SPX examples here.
- **Debit / credit** — the net premium paid (debit) or received (credit) to establish a position.
- **Delta** — a greek measuring how much an option's price moves per unit move in the underlying; loosely (and imperfectly) read as a probability of finishing in the money.
- **Discount factor (e^(−rT))** — the value today of one dollar to be received at expiry.
- **European option** — an option exercisable only at expiry (typical for index options).
- **Exercise** — using an option's right to make the underlying trade at the strike.
- **Expiration (expiry)** — the date on which the option's right ends.
- **Extrinsic value (time value)** — the part of an option's price above its intrinsic value; the price of time and uncertainty.
- **Forward** — the price agreed today for the underlying to be traded at a future date; recoverable from the option chain via parity.
- **Implied volatility** — the expected jumpiness of the underlying inferred from option prices.
- **In the money (ITM)** — a call with the underlying above the strike, or a put with it below; positive intrinsic value.
- **Index option** — an option written on a stock index; usually European and cash-settled.
- **Intrinsic value** — the part of an option's price you would collect if it expired now (never below zero).
- **Long** — owning an option (having paid the premium and holding the right).
- **Mid** — the midpoint of bid and ask; the usual single "fair" price quote.
- **Moneyness** — where a strike sits relative to the underlying's current price (ITM / ATM / OTM).
- **0DTE** — zero days to expiration; an option on its own expiration day.
- **OPEX** — options expiration, usually the monthly (third-Friday) event; quarterly ones with futures are *triple witching*.
- **Open interest** — the number of contracts currently outstanding (held), updated once daily; the "stock."
- **Option** — a contract giving its buyer the right, and its seller the obligation, to trade an underlying at a set strike by a set expiry.
- **Out of the money (OTM)** — a call with the underlying below the strike, or a put with it above; zero intrinsic value.
- **Payoff diagram** — a plot of profit or loss (vertical) against the underlying price (horizontal).
- **Physical settlement** — settling an exercised option by actually delivering the underlying (typical for equity options).
- **Premium** — the price of the option, paid once by the buyer to the seller.
- **Present value** — the worth today of a future amount, after discounting.
- **Put** — the right to *sell* the underlying at the strike.
- **Put-call parity** — the no-arbitrage relationship C − P = S − K · e^(−rT) linking a call, a put, the underlying, and cash.
- **Settlement** — how an exercised option is discharged (cash or physical; AM or PM).
- **Short** — having sold an option (having collected the premium and carrying the obligation).
- **Straddle** — buying a call and a put at the same strike; a bet on a big move in either direction.
- **Strangle** — buying an out-of-the-money call and put; a cheaper straddle needing a larger move.
- **Strike price** — the fixed price at which an option's right may be exercised.
- **Time decay** — the daily erosion of extrinsic value as expiry approaches.
- **Underlying** — the stock, index, or futures contract an option is written on.
- **Volatility** — how much the underlying is expected to move; the uncertainty priced into extrinsic value.
- **Volume** — the number of contracts traded during the current day (resets daily); the "flow."
- **Writer** — the seller of an option.

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| Long/short call and put payoff primitives with break-evens at 105 (call) and 96 (put) | Own reproducible computation — `figures/fig_payoff_primitives.py` |
| A 30-day at-the-money call's pre-expiry P&L is a smooth bent curve; premium 2.45, time decay ~1.08 at 10 days and ~2.03 at 1 day with spot unchanged | Own reproducible computation — `figures/fig_payoff_before_expiry.py` |
| Put-call parity holds on a real SPX chain (447 strikes): implied rate 4.48%, implied forward 7,658.74, dividend-adjusted residual ~0.29 point | Own reproducible computation — `figures/fig_parity_check.py` |
| A near-constant 6.4-point gap to the no-dividend parity line equals the present value of index dividends | Own reproducible computation — `figures/fig_parity_check.py` |
| A real SPX chain read column by column: at-the-money 7,650 call mid 108.70, spread 0.80 (~0.7%), open interest 7,116 versus 652 traded | Own reproducible computation — `figures/fig_chain_annotated.py` |
| The three first combinations (bull call spread cost 3, straddle cost 9, strangle cost 4.5) and their break-evens | Own reproducible computation — `figures/fig_combos.py` |
| Put-call parity C − P = S − K·e^(−rT) as a no-arbitrage relationship | Literature — (Hull 2022) |
| Moneyness, intrinsic versus extrinsic value, and payoff shapes | Literature — (Natenberg 2015) |
| Contract mechanics: exercise style, assignment, cash versus physical and AM versus PM settlement, the 100 multiplier | Literature — (OCC; Cboe) |
| Most option positions are closed by trading them away rather than by exercise | Practitioner consensus — not independently verified |

## References

- Hull, J. C. (2022). *Options, Futures, and Other Derivatives* (11th ed.). Hoboken, NJ: Pearson. (Introductory chapters on option mechanics and put-call parity.)
- Natenberg, S. (2015). *Option Volatility and Pricing: Advanced Trading Strategies and Techniques* (2nd ed., chs. 1–3). New York: McGraw-Hill. (The language of moneyness, intrinsic and extrinsic value, and payoff shapes.)
- Options Clearing Corporation (OCC). *Characteristics and Risks of Standardized Options* (the "Options Disclosure Document"). Chicago: OCC. Publicly available: <https://www.theocc.com/company-information/documents-and-archives/options-disclosure-document>. (Authoritative plain-language description of what standardized options are, exercise, assignment, and settlement.)
- Cboe Global Markets. *Cboe Options Institute educational materials and S&P 500 (SPX) options product specifications.* Publicly available: <https://www.cboe.com/education/> and <https://www.cboe.com/tradable_products/sp_500/spx_options/>. (Contract specifications, AM versus PM settlement, and the daily-expiration schedule referenced in Section 3 and Section 9.)

*All references above are publicly accessible: two are widely published textbooks, and two are free educational and disclosure documents from the OCC and Cboe (direct links given). No proprietary, course, or trading-academy material is cited.*
