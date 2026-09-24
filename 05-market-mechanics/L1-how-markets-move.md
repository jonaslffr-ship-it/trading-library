---
title: "How Markets Move — Auction, Order Book & Participants"
last_updated: 2026-09-20
---

# How Markets Move — Auction, Order Book & Participants

## Abstract

The number on a screen labelled "price" quietly teaches a false idea: that price is a fixed property of an asset, the way mass is a property of a stone. It is not. A price is an *event* — the record of the most recent agreement between one buyer and one seller — and the instant you understand it that way, the mechanics of how markets move stop being mysterious and become, in places, predictable. This paper builds those mechanics from nothing, for a reader who has never placed a trade. We decode bid, ask, and last; describe the *double auction* that settles them; open the *order book* and name its two fundamental actions, providing and taking liquidity; separate the two distinct mechanisms by which price actually moves — liquidity taken versus liquidity withdrawn; map the participants and show why some of them *must* trade regardless of price, which is exactly where predictable flow is born; read the shape of a trading day off real market data; and close the loop with reflexivity, where price changes behaviour that changes price. Only arithmetic is used, every technical term is explained where it first appears, and every empirical number is reproducible from free data.

## Keywords

Market mechanics, price discovery, double auction, order book, limit order, market order, bid-ask spread, liquidity, depth of market, market impact, order-flow imbalance, market maker, hedger, systematic fund, passive fund, forced flow, opening auction, closing auction, overnight session, reflexivity, feedback loop

## 1 Introduction

### 1.1 Motivation and thesis

Open any trading app and it shows you one number and calls it "the price of Apple" or "the price of the S&P 500." One number, sitting there, updating now and then, exactly like a temperature reading. This is a convenient lie, and it is the first thing a serious student of markets has to unlearn. There is no single price. At any instant there is a *highest price some buyer is willing to pay* and a *lowest price some seller is willing to accept*, and these are two different numbers with a gap between them. The single number the app displays is neither of those — it is the *last price*, the leftover echo of the most recent trade that already happened, a fact about the past dressed up as a fact about the present.

The thesis of this paper is a single sentence: *a price is an agreement, not a number* — the last point at which one specific buyer and one specific seller consented to exchange, produced by a continuous auction and immediately out of date. Everything else here is the unpacking of that sentence. Once you see price as an agreement, you naturally ask who the two parties to the agreement were, what each of them wanted, and whether either of them had any choice in the matter. Those questions lead straight to the deepest idea in this entire track of the library, and it is worth stating up front so the whole paper can build toward it:

> **The idea the whole track rests on.** Some participants *must* trade, and must trade *regardless of price* — their mandate, their rules, or their risk limits force their hand. A trader who is forced to act does not wait for a good price; they take whatever price is there. That is where *predictable flow* comes from, and predictable flow is the raw material of everything the rest of this library tries to measure.

You do not need this idea to be a good trader by intuition. You need it to reason about markets *mechanically* — to replace "the stock went up because of good news" with a chain of concrete events: who sent which orders, what those orders consumed, and why. That mechanical picture is what a beginner is almost never given, and it is the entire point of this paper.

### 1.2 Scope, prerequisites, and intended reader

This paper sits in the Trading Library's *Market Mechanics & Flows* track. It is written for a complete beginner, assuming no prior exposure to trading, finance, or statistics. If you can add, multiply, compute a percentage, and understand what a weighted average is (we will re-derive it when we need it), you have every mathematical prerequisite. There is no calculus, no probability theory, and no jargon that is not defined the moment it appears — each technical term is set in *italics* at first use and explained in the same breath, and all of them are collected again in the Glossary at the end.

After reading this paper, a reader can:

- read a quote screen correctly — distinguish the *bid*, the *ask*, the *last price*, and the *spread*, and explain why there is never really "one price";
- describe the *double auction* that runs continuously underneath every liquid market, and say precisely where and why a trade occurs;
- open an *order book* and name the two fundamental actions in any market — *providing liquidity* with a limit order and *taking liquidity* with a market order — and compute the cost of taking it;
- separate the two distinct mechanisms that move a price — liquidity being *taken* and liquidity *vanishing* — and recognise which one is at work from the volume that accompanies a move;
- lay out the *participant map*: who is on the other side of your trade, what each participant wants, and which of them are forced to trade regardless of price;
- read the shape of a trading day — why the open and especially the *close* are the largest liquidity events, and how the overnight world differs from the regular session;
- and reason about *reflexivity*: how a price move changes behaviour, which moves the price again, for good and for ill.

The paper deliberately stops short of formulas for price impact and order-flow imbalance. Those exist, they are useful, and they belong to the flow-landscape paper; here we build only the intuition on which those formulas later rest.

### 1.3 Data and reproducibility

All empirical figures use freely available data (here, 5-minute price bars from a public market-data feed), cached alongside the code so that the figures reproduce offline and unchanged. The diagrams that illustrate mechanics — the order book, the ten-tick move, the participant map — use *fictitious* numbers chosen for arithmetic clarity, and they say so plainly; they are teaching diagrams, not measurements, and they are flagged as such in their captions. *This is a research and educational document. It is not investment advice, and nothing in it is a recommendation to buy or sell anything.*

### 1.4 Organization of this paper

This paper is complete: every section listed below is written in full. The map exists so you can see the whole arc before walking it, and so you can jump to what you need.

- **Section 2 Price as an agreement, not a number** — decoding bid, ask, and last; the double auction; why "the price" is always the *last* agreement and always slightly out of date.
- **Section 3 The order book, concretely** — limit orders versus market orders as the two fundamental verbs; depth; the spread as a cost you pay; thin versus deep books, worked on a diagram.
- **Section 4 What actually moves price** — the two distinct mechanisms, liquidity *taken* versus liquidity *vanishing*, walked through one ten-tick move; aggression and imbalance in plain words.
- **Section 5 Who is on the other side** — the participant map: market makers, hedgers, systematic funds, discretionary managers, retail, and passive funds — each with a motive and a constraint — and the forced-flow zone at the bottom.
- **Section 6 The time structure of a session** — opening and closing auctions, why the close is the single biggest liquidity event, overnight versus regular hours, and the three-session view, shown on real data.
- **Section 7 Reflexivity and feedback** — how a price move changes behaviour, which moves the price, without jargon; the difference between a stabilising loop and a runaway one.
- **Section 8 Bridge forward** — a one-page map of the whole library, and how this paper connects to options, volatility, and the flow landscape.
- **Section 9 Common misconceptions**, followed by a **Glossary** of about forty terms, and the **References**.

## 2 Price as an agreement, not a number

Start with the screen. A quote for a liquid stock or futures contract shows, at minimum, three numbers, and a beginner who conflates them will misread every market event that follows.

The *bid* is the highest price at which someone is, right now, willing to *buy*. The *ask* (also called the *offer*) is the lowest price at which someone is, right now, willing to *sell*. The *last price* is the price at which the most recent trade actually took place. On a typical liquid market the bid might read 100.00, the ask 100.01, and the last 100.00 or 100.01 depending on which side traded most recently. Three numbers, three different meanings — and the app's headline "price" is usually the last one, the historical one.

Why can the bid and the ask not simply be equal? Because they represent two *different people who have not yet agreed*. The buyer would love to pay less; the seller would love to receive more. Each posts the least generous price they are willing to live with, and between those two prices sits a no-man's-land — the *spread* — inside which no trade can occur, because no buyer will reach up to the seller's price and no seller will reach down to the buyer's. The spread is the visible width of the disagreement. When people say "the market is 100.00 bid at 100.01 offered," they are describing exactly this standoff: someone will buy at 100.00, someone will sell at 100.01, and until one of them blinks, nothing happens.

A convenient fourth number, the *mid* (or *midpoint*), is simply the average of the bid and the ask — here (100.00 + 100.01) / 2 = 100.005. The mid is a useful reference precisely because it is a price at which *nobody has agreed to anything*; it is the centre of the disagreement, handy for measuring how far a trade landed from fair-ish value, and we will use it that way in Section 3.

> **The one distinction to keep.** The bid and the ask are *live intentions* — offers standing open right now, either of which you could accept this instant. The last price is a *completed fact* — an agreement that already happened and is already history. Live intention versus completed fact: confusing the two is the most common beginner error on a quote screen.

### 2.1 The double auction

Underneath every liquid, continuously traded market runs a *double auction*. The word "double" means both sides are auctioning at once: buyers bid *up* from below, competing with each other to be the one who gets filled, and sellers offer *down* from above, competing with each other to be the one who sells. It is not one auctioneer selling to a room; it is two crowds pushing toward each other from opposite directions, and a trade occurs at exactly the point where they touch.

Concretely: buyers place bids at various prices — some eager buyer at 100.00, a less eager one at 99.99, a bargain-hunter at 99.95. Sellers place offers — an eager seller at 100.01, a greedier one at 100.02, and so on. As long as the highest bid is *below* the lowest offer, the two crowds do not touch and no trade happens; the market just sits there quoting 100.00 / 100.01. A trade happens only when someone *crosses the spread* — when a buyer decides 100.01 is acceptable after all and reaches up to take the seller's offer, or a seller decides 100.00 is acceptable and reaches down to hit the buyer's bid. At that instant the two intentions meet, an agreement is struck, and a new *last price* is printed. (Harris 2003)

This is *price discovery*: the ongoing process by which a market finds the one price at which a buyer and a seller are simultaneously willing to transact. It happens "every time a seller and a buyer interact," in the words of CME Group's own educational material (CME Group, *Price Discovery*), and it never truly finishes — the moment one agreement is struck, the crowds re-form and the search for the next agreement begins. That is why a price is never a settled state. It is a running series of momentary agreements, each one true for an instant and then replaced.

### 2.2 "The price" is always the last agreement, and always slightly stale

Put the pieces together and the headline number dissolves into something more honest. "The price of the S&P 500 is 5,000" really means: *the most recent time two people agreed to trade it, they agreed at 5,000.* It says nothing about whether you could buy or sell at 5,000 right now — for that you need the bid and the ask, the live intentions. In a fast market the last price can be several ticks away from where you could actually transact, because the world moved on between the last agreement and this instant.

This is not pedantry; it changes how you read every event. "The stock is up 2% today" means the last agreement is 2% above yesterday's reference agreement — it does not mean anyone can still get that level. "It broke through 100" means an agreement was struck at 100 and buyers kept reaching up; whether the *next* buyer finds anyone still offering there is a separate question, and answering it is what the rest of this paper is about. A price is an agreement between two willing parties, printed and immediately aging. Hold that, and Section 3 — the machinery that stores all those willing parties and their prices — will read like common sense.

## 3 The order book, concretely

If a price is an agreement waiting to be struck, then somewhere there must be a list of everyone currently willing to strike one, and at what price. That list is the *order book* — also called the *depth of market* or *DOM* — and it is the single most clarifying object in all of market mechanics. Once you can read an order book, most of what markets do stops being metaphor and becomes bookkeeping.

### 3.1 The two fundamental verbs: providing versus taking liquidity

There are exactly two things you can do when you send an order, and they are opposites. Understanding them is 80% of understanding markets.

A *limit order* is an order to buy or sell *at a specified price or better, but no worse*. "Buy 100 shares at 99.99 or lower." A limit order does not demand an immediate trade; if no one will meet your price, it simply *rests* in the book — it joins the queue of standing intentions and waits. In doing so it *provides liquidity*: it becomes one of the offers that someone else can later accept. The person who posts a limit order is patient. They are saying: *I will trade, but only on my terms; I am willing to wait.*

A *market order* is an order to buy or sell *right now, at whatever price is available*. "Buy 100 shares, immediately, I don't care about the exact price." A market order demands an instant trade, so it reaches across the spread and *takes* whatever resting limit orders are there to meet it. In doing so it *takes liquidity*: it consumes offers that other people had posted. The person who sends a market order is impatient. They are saying: *I will pay for immediacy; get me in (or out) now.*

> **The two verbs.** A *limit order provides* liquidity and waits; a *market order takes* liquidity and pays for the privilege of not waiting. Every trade in *continuous* trading is one impatient order (the *taker*) meeting one or more patient resting orders (the *makers*). In continuous trading there is no third possibility — with two exceptions worth naming. The first is a batch auction, where many orders cross at once at a single price and neither side takes the other, which is exactly the opening- and closing-auction mechanism of Section 6.1. The second, larger for US *equities* specifically, is *internalisation*: most retail marketable orders never reach a public order book at all — they are routed via payment for order flow (PFOF) to wholesalers who fill them from their own inventory at or just inside the national best bid/offer (a small "price improvement"), rather than as a taker crossing a resting maker. For index futures and options the maker/taker picture holds cleanly; for a retail stock order the counterparty is often a wholesaler you never see, and "who is providing, who is taking" is answered off-book. (This also dates the one-cent tick used later: the 2024 Reg NMS amendments introduce a half-cent tick for tight-spread stocks, with the compliance date extended from the original November 2025 to November 2026 and widely expected to slip further toward 2027.) When you internalise this, "who is buying?" splits into two much sharper questions: who is providing, and who is taking?

The professional who systematically posts limit orders on both sides, hoping to earn the spread, is a *liquidity provider* or *market maker* (Section 5). The trader who fires a market order to get filled now is a *liquidity taker*. Most price *movement*, as Section 4 will show, is the story of takers consuming what makers have posted — or of makers pulling their posts before anyone can take them.

### 3.2 Depth, the spread as a cost, and thin versus deep books

The order book stacks all the resting limit orders by price. On the buy side, bids pile up *below* the current market — the best (highest) bid on top, then progressively lower bids beneath it. On the sell side, offers pile up *above* — the best (lowest) offer first, then progressively higher offers above it. Each price rung is a *level*, and the quantity resting at a level is the *depth* at that price. The total quantity available near the current price is the market's *depth* in the loose sense: a *deep* book has large size resting close to the market, so it can absorb big orders without moving much; a *thin* book has little resting size, so even a modest order pushes the price a long way.

Figure 1 draws a complete miniature book for a fictitious stock trading near \$100.00 with a one-cent *tick* — the *tick size* being the smallest price increment the market allows, here \$0.01. Read it as two queues facing each other across the spread. The best bid is 100.00 (the highest price any buyer will pay right now); the best ask is 100.01 (the lowest price any seller will accept right now); the spread between them is one tick, and the mid is 100.005. Behind each of those best prices stand more orders at worse prices — 2,900 shares resting in total on the bid side across five levels, and 2,900 on the ask side across five levels, in this deliberately symmetric example.

![Didactic schematic of a ten-level order book for a fictitious \$100 stock with a one-cent tick. Bids (patient buy limit orders) rest below the market on the left; asks (patient sell limit orders) rest above it on the right; the shaded band between the best bid of 100.00 and the best ask of 100.01 is the one-tick spread — the width of the disagreement. A 700-share market buy is shown walking the ask side: it takes all 300 shares resting at 100.01 and then 400 of the 500 at 100.02, for an average fill of 100.0157, about 1.07 ticks above the 100.005 mid — the price of immediacy, made visible. Numbers are chosen for arithmetic clarity, not taken from a feed. Reproduce with figures/fig_orderbook_schematic.py. (Didactic; no data download)](figures/fig_orderbook_schematic.png)

Now use the book to see why *the spread is a cost you pay*, not an abstract number. Suppose you are impatient and send a *market buy* for 700 shares. You do not get 700 shares at the mid of 100.005, and you do not even get them all at the best ask of 100.01. You get the 300 shares resting at 100.01 first; that clears the level. The remaining 400 shares can only be filled at the next level up, 100.02. Your *average fill price* — the total dollars paid divided by shares bought — works out to (300 × 100.01 + 400 × 100.02) / 700 = 100.0157. That is about 1.07 ticks *above* the mid you saw on the screen.
That gap is the cost of immediacy, and it has two named parts. Half of the quoted spread — the distance from the mid (100.005) up to the best ask (100.01) — is the *spread cost* you pay simply for choosing to take rather than provide. The additional distance, from the best ask up to your average fill (100.0157), is *slippage*: the extra you paid because your order was larger than the size resting at the best price and had to eat into worse levels. Slippage is the market's way of charging you more the more urgently and heavily you demand liquidity. A patient trader posting a limit buy at 100.00 pays neither cost — but risks never being filled at all. Immediacy is not free; the book shows you its exact price.

Notice one more thing the diagram makes concrete. After your 700-share buy, the 300 shares at 100.01 are gone and only 100 of the original 500 remain at 100.02. The new best ask is 100.02, and the spread has widened from one tick to two. Your single impatient order did not just cost *you* a tick of slippage — it *moved the market*, nudging the best offer up and leaving the book thinner than it found it. That is the seed of Section 4: taking liquidity and moving price are the same act seen from two angles.

## 4 What actually moves price

Here is the question that separates a mechanical understanding of markets from a superstitious one: *what, physically, makes the last price go from 100.00 to 100.10?* The honest answer is that there are two entirely different mechanisms that produce the same visible result, and they have opposite meanings. A trader who cannot tell them apart is guessing.

### 4.1 Mechanism one: liquidity is taken

The first way a price rises is the one everyone imagines: buyers get aggressive. Impatient *market buy* orders arrive and consume the resting sell offers, level by level, exactly as the 700-share order did in Section 3 — only now they keep going. Each level they clear removes the cheapest remaining offer, so the *next* trade can only happen at a higher price. The book is literally eaten upward, and every bite prints a higher last price. This is price movement by *liquidity taking*: real trades occur, real shares change hands, and the tape shows heavy volume as the buyers pay their way up through the offers.

The left and middle panels of Figure 2 show this. We start with ten resting ask levels between 100.01 and 100.10. Aggressive buyers send market orders that consume every offer from 100.01 through 100.09 — 3,400 shares in total — and then take another 100 of the 800 shares resting at 100.10. In all, **3,500 shares trade**, and the last price has risen ten ticks, from 100.00 to 100.10. The move is real, it is expensive for the buyers (they paid progressively worse prices all the way up), and it left a large footprint of volume behind it.
### 4.2 Mechanism two: liquidity vanishes

The second way a price rises leaves almost no footprint at all, and it is the one beginners never see coming. Suppose no one buys aggressively. Instead, the *sellers* who had posted all those offers between 100.01 and 100.09 simply *cancel* them — they pull their limit orders out of the book, perhaps because they got nervous, or the news changed, or a bigger order elsewhere spooked them. No trade occurs when a limit order is cancelled; the order just disappears. But now the cheapest remaining offer in the book is the one at 100.10. The best ask has jumped ten ticks in an instant, and a single tiny *market buy* for 100 shares, arriving afterward, prints at 100.10.

The right panel of Figure 2 shows exactly this. The same nine levels that were *traded through* in mechanism one are here *cancelled, never traded*. Only **100 shares** change hands — a single small order finding the new, higher offer. Same ten-tick move in the last price. Thirty-five times less volume.

![Didactic schematic: one ten-tick move produced two different ways. Left, the starting book near 100.00 with ten resting ask levels. Middle, mechanism one — liquidity taken: aggressive market buys consume every offer from 100.01 to 100.09 (3,400 shares) plus 100 more at 100.10, so 3,500 shares trade and the last price rises to 100.10. Right, mechanism two — liquidity vanished: the same nine levels are cancelled by their owners with no trade, and a single 100-share market buy then prints at 100.10. Same ten-tick move; 3,500 shares versus 100 shares, a 35-to-1 volume ratio. Numbers chosen for arithmetic clarity. Reproduce with figures/fig_ten_tick_move.py. (Didactic; no data download)](figures/fig_ten_tick_move.png)

> **The distinction that changes how you read a chart.** Price can rise because buyers *took* liquidity (heavy volume, real conviction, expensive to do) or because sellers *withdrew* liquidity (almost no volume, no conviction required, nearly free). A ten-tick move on 3,500 shares and a ten-tick move on 100 shares look identical on a price chart and mean opposite things. Volume is the tell. This is why experienced traders never look at price without looking at the volume that produced it.

The two mechanisms usually act together and reinforce each other, which is what makes fast moves so violent: aggressive takers arrive *and* the makers ahead of them flee, so the book is being eaten from one side while it evaporates from the other. But keeping them conceptually separate is essential, because they carry different information. A move on heavy volume tells you a lot of capital was committed at these prices. A move on thin volume tells you only that the previous prices were an illusion — nobody was really willing to hold them, and the offers vanished at the first sign of pressure.

### 4.3 Aggression and imbalance, in plain words

Two more ideas, kept deliberately informal here; their formal, quantitative treatment is the job of the flow-landscape paper.

*Aggression* is simply the tendency to use market orders rather than limit orders — to take rather than provide, to demand immediacy rather than wait for it. A market with many aggressive buyers and few aggressive sellers will drift up even without dramatic news, because takers keep reaching across the spread on the buy side and makers keep having to re-post their offers higher. Aggression is impatience made visible in the tape.

*Order-flow imbalance* is the plain-language observation that, over some window, more volume arrived on one side than the other — more shares bought by takers than sold by takers, or more size added to the bid than to the ask. When buying pressure persistently exceeds selling pressure, the book gets eaten faster on the offer side than it can be replenished, and price rises; the reverse for selling pressure. That is the whole intuition. Turning "more on one side" into a number that predicts the *size* of the next move — the mathematics of *price impact*, including the well-known result that impact tends to grow roughly with the *square root* of order size rather than in proportion to it — is deferred to the flow-landscape paper (Section 8). Here it is enough to hold the mechanical picture: price moves when the balance between takers and makers tips, either because takers get hungrier or because makers get scarcer.

## 5 Who is on the other side

Every time you trade, someone is on the other side of it, and that someone had a reason. Beginners imagine a faceless, uniform "market." In reality the crowd is made of a handful of distinct *participant families*, each with a characteristic *motive* (what they are trying to achieve) and a characteristic *constraint* (what limits their freedom to walk away from a bad price). The single most useful thing to know about any participant is not their motive but their constraint — because the constraint tells you whether they are free to wait for a good price or *forced* to take whatever price is there.

Figure 3 is the *participant map*. It places each family by two axes: horizontally, its typical *holding horizon* — how long it tends to hold a position, from a market maker's seconds to a pension fund's decade — and vertically, how *price-sensitive* its trading is. At the top sit participants who trade only when the price suits them; at the bottom, in the shaded band, sit participants who must trade *regardless* of price. That band is the whole reason this track exists.

![Didactic schematic: the participant map. Six participant families placed by typical holding horizon (horizontal, log scale from seconds to a decade) and by how price-sensitive their trading is (vertical). Near the top, price-sensitive discretionary managers and retail traders trade only at prices they like; in the shaded band near the bottom, hedgers and passive/index funds must trade regardless of price, driven by exposure changes and index rebalances. Market makers and systematic funds sit in between. The shaded price-insensitive zone is the origin of predictable flow — the subject of the flow-landscape paper. Placements are typical orders of magnitude, not measurements; any participant can act out of character. Reproduce with figures/fig_participant_map.py. (Didactic; no data download)](figures/fig_participant_map.png)

Walk the families one by one.

**Market makers** hold for seconds to minutes. Their motive is narrow and mechanical: earn the *spread* by continuously posting both a bid and an ask, buying at the bid, selling at the ask, and pocketing the difference across thousands of tiny round trips. Their constraint is *inventory*: a market maker does not want to end the day holding a large directional position, because that is precisely the risk they are trying to avoid. So when they accumulate too much of something, they *must* trade out of it — sometimes at an unfavourable price — simply to get flat. They are moderately price-sensitive: happy to quote where they like, but forced to trade when inventory piles up.
**Hedgers** — including the *dealers* who sell options and the corporates who manage currency or commodity exposure — hold for days. Their motive is not profit from the trade itself but the *shedding of a risk they never wanted*. A dealer who has sold an option has taken on a risk as a by-product and must offset it; a corporation with revenue in a foreign currency must neutralise the exchange-rate exposure. Their constraint is the sharpest on the map: *when their exposure changes, they must trade to re-neutralise it, at essentially any price.* They are deeply price-insensitive — they are not trying to get a good price, they are trying to get *flat* — and that is exactly what makes their flow so mechanical and, in aggregate, so predictable. In this library's private research, the canonical case of exactly this behaviour is dealer option-hedging, where the requirement to re-hedge *regardless of price* is the foundation of the entire research programme. Here we state only the public, general principle: a hedger trades because their risk changed, not because the price is attractive.
**Systematic funds** — trend-followers (*CTAs*, from "commodity trading advisor") and *volatility-targeting* funds that size their positions to a risk budget — hold for weeks to months. Their motive is to follow tested, rule-based strategies across many markets at once. Their constraint is the rulebook itself: when a rule triggers, the fund *must* enter or exit, on schedule, whether or not a human would think the price is good. Their trading is only moderately price-sensitive, because the rule, not the price, is in charge. This mechanical obedience to rules is why their flow, too, can be anticipated in part — the subject of the flow-landscape paper.
**Retail traders** — individuals trading their own accounts — hold anywhere from minutes to months. Their motive is a mix of profit, long-term saving, and, honestly, entertainment. Their constraint is mostly their small size and their tendency to *pay the spread*: retail flow is typically price-sensitive (they chase prices they like and flee prices they don't) and erratically timed. Individually small, retail flow can matter in aggregate, but it is the least mechanically forced of all the families.

**Discretionary managers** — human portfolio managers acting on a researched view — hold for months to years. Their motive is to profit from judgment. Their constraint is subtle and often overlooked: *risk limits and client redemptions can force them to sell exactly when they least want to.* A manager convinced a position is cheap may still be forced to dump it because the fund breached a drawdown limit or investors asked for their money back. So even the most price-sensitive, opinionated participant on the map has a floor of forced behaviour beneath them.

**Passive and index funds** hold for years to decades. Their motive is the simplest of all: track a benchmark index as cheaply as possible, never trying to beat it. Their constraint puts them right down in the forced-flow band with the hedgers: they *must* invest new inflows and they *must* rebalance to match index changes — and crucially, they overwhelmingly prefer to do this trading *at the close* (Section 6), where the day's largest pool of liquidity sits. A passive fund does not care whether the close is a good price; its mandate is to match the index at the index's price. This is about as price-insensitive as a participant can be, and the sums involved are enormous.
> **Where predictable flow is born.** Look again at the shaded band. Hedgers and passive funds sit in it because their mandates strip away the freedom to wait for a good price — and market makers, systematic funds, and even discretionary managers each have a constraint that can, at the wrong moment, push them into it. A participant who *must* trade regardless of price generates *forced flow*: buying or selling you can, in principle, see coming, because it is driven by a rule or an obligation rather than an opinion. The entire measurement programme of this library — dealer positioning, flow calendars, regime maps — is an attempt to locate and anticipate this forced flow. Everything downstream depends on the fact that some of the crowd is not free to say no.

## 6 The time structure of a session

A trading day is not uniform. Liquidity — the amount of size available to trade against — is wildly unevenly distributed across the hours, and knowing *when* the market trades is nearly as important as knowing *what* it trades. The shape is so consistent that it has a name.

### 6.1 The opening and closing auctions

A continuously trading market usually does not simply "switch on" at the opening bell. It holds an *opening auction*: for a short window before the open, orders accumulate without trading, and then at the bell they are matched *all at once* at the single price that maximises the volume that can trade. This concentrates the overnight backlog of orders — everything that built up while the continuous market was closed — into one price-discovery event, so the day starts from a real, agreed-upon reference price rather than a chaotic scramble.

The mirror image happens at the end of the day, and it is the more important of the two. The *closing auction* matches a large batch of orders at a single closing price at the bell. It matters disproportionately because of a special order type: the *market-on-close* (*MOC*) order, an instruction to trade whatever quantity is needed *at the official closing price, whatever that turns out to be*. Recall from Section 5 who is forced to trade at the close: passive and index funds, which must match a benchmark that is itself struck at the close, and many other rule-based and risk-managed participants who want the day's most reliable, most liquid price. All of that forced, price-insensitive flow piles into one moment.

### 6.2 The close is the single biggest liquidity event — shown on real data

The consequence is measurable, and Figure 4 measures it. Using 5-minute volume bars for a large, liquid exchange-traded fund tracking the S&P 500 (SPY), over 60 full regular sessions from 2026-06-24 to 2026-09-17, we bucket each day's volume by time of day, express each bucket as a share of that day's total, and average across days. No strategy, no tuning — just a plain picture of *when* volume happens.
![SPY 5-minute volume by time of day, expressed as each bucket's share of the day's total and averaged over 60 full regular sessions (2026-06-24 to 2026-09-17). The profile is the classic U-shape: a busy open, a quiet midday, and a close that is the single largest liquidity event of the day. The first 30 minutes carry 14.5% of the day's volume and the last 30 minutes carry 21.2%; the two together with the rest of the first and last hour make up 51.4% of the whole day in just two of the six-and-a-half hours. The lunchtime trough near 13:45 ET is about 0.62% of the day per five-minute bar, while the closing bar alone is about 9.73%. Free public 5-minute data, cached for offline reproducibility. Reproduce with figures/fig_intraday_profile.py.](figures/fig_intraday_profile.png)

The numbers make the point sharply. The *first* 30 minutes of the session carry **14.5%** of the day's volume, as the opening auction's backlog works itself out and overnight news gets priced. The *last* 30 minutes carry **21.2%** — half again as much as the open — as the closing auction and its MOC flow dominate. The first and last hour together account for **51.4%** of the entire day's volume: more than half of all trading happens in just two of the roughly six-and-a-half regular-session hours. In between lies the *lunchtime trough*, where the quietest five-minute bar near 13:45 ET is a mere **0.62%** of the day, while the single closing bar is about **9.73%** — the biggest bucket on the chart by a wide margin.
This is the *U-shape*, and it is one of the most robust regularities in all of market microstructure. (Harris 2003) Its practical meaning for a beginner: liquidity is a resource that is abundant at the open and close and scarce at midday. The same order that barely moves the price at 15:55 can shove it around at 13:00, because there is far less resting size to absorb it. If you understood Section 3 and Section 4, you now understand *why* the U-shape has teeth — a thin midday book moves more per share taken — and the participant map of Section 5 tells you *who* fills the fat ends of the U: the forced, price-insensitive flow that concentrates at the open and, above all, the close.

### 6.3 Overnight versus regular hours, and the three-session view

The regular session is only part of the story. Many instruments — index futures especially — trade nearly around the clock in an *overnight session* (in futures, often called *Globex* after the exchange's electronic platform). Overnight liquidity is much thinner than regular-hours liquidity, so prices can travel a long way on relatively little volume, and the overnight range often sets the stage — support and resistance levels, liquidity pools — for the regular session that follows.

A useful lens, used in this library's own daily process, is the *three-session view*: the global trading day handed off around the clock between regions. The *Asian session* tends to be driven by macro and currency (FX) flows; the *European session* is where large institutions position ahead of the US day, and moves that originate there tend, empirically, to hold better than moves that originate in the thin Asian hours; and the *US regular session* is the main liquidity event, anchored by the open and close we just measured. The details of how overnight structure conditions the regular session belong to the trading playbook, not to an introductory mechanics paper — but the beginner should carry away the shape: liquidity is not a constant. It ebbs and floods on a daily clock and a global relay, and the same order is a different act depending on when you send it.

## 7 Reflexivity and feedback

So far the picture has been mechanical but static: orders arrive, the book gets eaten or replenished, price moves. The final piece is what makes markets feel alive — and occasionally unhinged. *Reflexivity* is the plain fact that a price move *changes the behaviour* of the participants, and their changed behaviour then moves the price again. Cause and effect chase each other in a loop. There is no jargon needed to see it; there is only the loop.

Consider a price that starts falling. Several things happen *because* it fell. A trader who had placed a *stop-loss* — a standing instruction to sell if the price drops to some level, to cap a loss — now has that stop triggered, so they sell, which pushes the price lower still. A systematic fund whose rule says "reduce exposure as volatility rises" sees the falling, jumpy price and mechanically sells, pushing it lower again. A market maker, seeing the book getting eaten and their inventory growing, widens their spread and pulls offers to protect themselves, thinning the book (Section 4's second mechanism) so the *next* sell moves price even more. Each of these reactions was *caused* by the fall and each *deepens* the fall. That is a *feedback loop*, and specifically a *positive* (self-reinforcing) one: the output feeds back in a way that amplifies the input. Positive feedback is how an ordinary down-move becomes a cascade or a crash.

Now consider the opposite. Suppose the dominant participants are ones who *buy as price falls* — value buyers who find the lower price more attractive, or a class of hedger whose mechanical response to a falling price is, by the structure of their position, to *buy*. As price drops, they buy; their buying arrests the drop and pushes price back up; as price rises, that same mechanism has them selling, capping the rise. This is *negative* (stabilising) feedback: the reactions oppose the move and damp it. A market dominated by stabilising flow is quiet and mean-reverting — pushes get absorbed and prices oscillate in a range. A market dominated by amplifying flow is trending and prone to violent, self-feeding moves.

> **The whole idea in one loop.** Price moves → participants react to the move → their reactions move the price. When the reactions *oppose* the move, the market is stable and calm; when the reactions *feed* the move, the market trends and can run away from itself. Which loop you are in is not fixed — it depends on *who is on the other side* (Section 5) and *what their positions force them to do* as price changes. This is precisely why identifying forced, mechanical flow matters so much: it tells you which loop the market is currently wired for.

You do not need any mathematics to use this. You need only to stop seeing a price move as a single event and start seeing it as the first step of a loop — and to ask, each time, whether the participants who must react will *push back* against the move or *pile into* it. The advanced machinery of this library, especially everything to do with dealer hedging, is in the end a detailed answer to that one question: given how the forced participants are positioned, is today's market wired to absorb shocks or to amplify them?

## 8 Bridge forward

This paper is the entry point to a larger structure. It is worth seeing the whole map at once, because every other topic in the library plugs into the mechanics you now understand.

The library is organised into three broad *pillars*. The first is **mechanics and microstructure** — how markets physically work — and this paper is its front door. The flow-landscape paper, in the same track, is where the intuition of Section 4 and Section 5 becomes quantitative: a full taxonomy of flows, the mathematics of *price impact* (including the square-root-of-size relationship gestured at in Section 4.3), and a side-by-side treatment of dealer-hedging flow, volatility-targeting flow, trend-following flow, and passive rebalancing flow, together with the calendar and regime map that says *when* each one fires. Everything in that paper is built directly on the forced-flow idea of Section 5.

The second pillar is **options and volatility**, and it is where the single most important forced participant — the option *dealer* of Section 5 — gets a microscope. The options track explains how selling an option saddles a dealer with a risk that must be hedged in the underlying market, *regardless of price*, producing exactly the mechanical, anticipatable flow this paper kept pointing at. The volatility track then asks how much a market actually *moves* versus how much it was *expected* to move, and why the gap between the two is itself tradable. Both tracks are, at bottom, elaborations of two ideas from this paper: that some participants must trade regardless of price (Section 5), and that markets can be wired to damp or amplify their own moves (Section 7).

The third pillar is **method** — how to test any of these claims without fooling yourself. Its backtesting-and-hypothesis-testing paper is the discipline that keeps the rest honest: it insists that no pattern counts as real until it has been specified in advance and survived data it never saw. A beginner who is tempted, after reading Section 4, to believe they can "read the tape" should read the method pillar next, precisely to learn how easily that belief deceives.

> **The one-page map.** *This paper* tells you how a price is made and moved and who makes it move. The *options and volatility* pillar tells you why the most mechanical participant — the dealer — is forced to trade, and how movement itself is priced. The flow-landscape paper puts every forced flow on one quantitative map and a calendar. The *method* pillar tells you how to test all of it without lying to yourself. Read in that order, the library goes from "what is a price" to "which forced flows are firing today, and can I prove it."

Where to go next depends on why you came. If you want to understand *why dealers must hedge*, go to the options track. If you want the numbers behind Section 4 and Section 5, go to the flow-landscape paper in this track. If you caught yourself believing you could already trade on Section 4, go to the method pillar first. All three roads start from the same place: a price is an agreement, not a number.

## 9 Common misconceptions

A short catalogue of the errors this paper is designed to prevent. Each is stated the way a beginner tends to believe it, then corrected.

- **"There is one price."** No — there is a bid, an ask, and a last, and they differ. The bid and ask are live intentions you can act on; the last is a completed fact that is already aging (Section 2).
- **"The last price is what I can trade at right now."** No — the last price is history. What you can transact at right now is the bid (to sell) or the ask (to buy), and in a fast market those can be several ticks from the last print (Section 2.2).
- **"A market order gets me the price I see."** No — a market order takes whatever is resting in the book, best price first, then worse. If your order is bigger than the size at the best price, you pay *slippage* and your average fill is worse than the quote (Section 3.2).
- **"Big volume means a big move, small volume means a small move."** No — a large move can happen on tiny volume if liquidity *vanishes* rather than being *taken*. Volume tells you which mechanism moved the price, not how far it moved (Section 4).
- **"Every trade needs a buyer and a seller, so buying and selling always cancel out and can't move price."** True that every trade is matched — but it misses the point. What moves price is the *balance of aggression*: whether the impatient takers are hitting the bid or lifting the offer, and whether the patient makers are standing firm or fleeing (Section 4.3).
- **"The market is one big anonymous crowd with no structure."** No — it is a handful of participant families with distinct motives and, more importantly, distinct constraints. Some are free to wait for a good price; some are *forced* to trade regardless of price (Section 5).
- **"Prices move because of news and fundamentals."** Sometimes the *trigger* is news, but the *mechanism* is always the order book: news moves price only insofar as it makes takers aggressive or makers flee. And a great deal of flow — forced, mechanical, calendar-driven — has nothing to do with news at all (Section 5, Section 6).
- **"All hours of the day are the same."** No — liquidity follows a daily U-shape, with more than half the day's volume in the first and last hour and a thin, treacherous midday; and overnight liquidity is thinner still (Section 6).
- **"A price move is a single event."** No — it is the first step of a feedback loop, because the move changes behaviour that moves the price again. Whether that loop damps or amplifies depends on who is forced to do what (Section 7).

## Glossary

*Roughly forty terms, in the order a beginner meets them; each is defined again where it first appears in the text.*

- **Bid** — the highest price at which someone is currently willing to buy.
- **Ask (offer)** — the lowest price at which someone is currently willing to sell.
- **Last price** — the price at which the most recent trade actually occurred; a fact about the past.
- **Spread** — the gap between the best bid and the best ask; the width of the current disagreement and the base cost of trading with immediacy.
- **Mid (midpoint)** — the average of the best bid and best ask; a reference price at which nobody has actually agreed to trade.
- **Tick / tick size** — the smallest price increment a market allows (e.g. \$0.01).
- **Double auction** — the continuous process in which buyers bid up and sellers offer down, a trade occurring only where the two cross.
- **Price discovery** — the ongoing process by which the market finds a price at which a buyer and seller will both transact.
- **Order book (depth of market, DOM)** — the live list of all resting limit orders, stacked by price on the bid and ask sides.
- **Level** — a single price rung in the order book.
- **Depth** — the quantity of orders resting at a price (or, loosely, the size available near the market).
- **Limit order** — an order to trade at a specified price or better; it rests in the book and *provides* liquidity.
- **Market order** — an order to trade immediately at whatever price is available; it *takes* liquidity.
- **Resting order** — a limit order sitting in the book, waiting to be filled.
- **Fill** — the execution of an order; a **partial fill** is when only part of the requested size trades.
- **Average fill price** — total value transacted divided by quantity; the true price you paid across all levels touched.
- **Liquidity** — the ease of trading size without moving the price; the resting quantity available to trade against.
- **Liquidity provider / maker** — a participant who posts resting limit orders for others to trade against.
- **Liquidity taker** — a participant who sends market orders that consume resting liquidity.
- **Slippage** — the extra cost incurred when an order is larger than the size at the best price and must fill at worse levels.
- **Market impact** — the tendency of a trade to move the price against the trader; grows with order size (see Section 4.3, deferred).
- **Aggression** — the tendency to use market orders (take) rather than limit orders (provide).
- **Order-flow imbalance** — a persistent excess of taker volume (or resting size) on one side over the other.
- **Deep vs. thin book** — a book with large (small) resting size near the market, which absorbs (fails to absorb) orders with little (large) price movement.
- **Market maker** — a participant who earns the spread by quoting both sides continuously; constrained by inventory.
- **Inventory** — the position a market maker is left holding; the constraint that forces them to trade to stay flat.
- **Hedger / dealer** — a participant who trades to neutralise an unwanted risk exposure, largely regardless of price.
- **Systematic fund (CTA, vol-target)** — a rule-based fund whose entries and exits are triggered mechanically by its strategy.
- **Discretionary manager** — a human manager trading on judgment; still subject to risk limits and client redemptions.
- **Retail trader** — an individual trading their own account; small size, price-sensitive, erratically timed.
- **Passive / index fund** — a fund that tracks a benchmark as cheaply as possible; must trade inflows and rebalances, usually at the close.
- **Rebalance** — a passive or index fund's obligatory trading to re-match its benchmark when the index changes.
- **Forced / price-insensitive flow** — buying or selling driven by a mandate, rule, or risk limit rather than by an opinion about price; the origin of predictable flow.
- **Opening auction** — the batch matching that sets the day's opening price from accumulated orders.
- **Closing auction** — the batch matching that sets the official closing price; the day's single largest liquidity event.
- **Market-on-close (MOC) order** — an instruction to trade at the official closing price, whatever it turns out to be.
- **Regular trading hours (RTH)** — the main daytime session of an exchange.
- **Overnight session (Globex)** — trading outside regular hours; much thinner liquidity, larger moves per unit of volume.
- **U-shape** — the typical intraday volume profile: busy open, quiet midday, and an even busier close.
- **Three-session view** — the global day seen as an Asian, European, and US relay, each with its own character.
- **Reflexivity** — the fact that a price move changes participants' behaviour, which then moves the price.
- **Feedback loop** — a self-referring cause-and-effect chain; **positive** (amplifying) feedback trends and can run away, **negative** (stabilising) feedback damps and mean-reverts.
- **Stop-loss** — a standing order to exit a position once price reaches a set level, capping a loss; a common source of reflexive selling.

## Evidence basis

Every substantive claim in this paper rests on one of three kinds of basis, distinguished here so a reader can tell at a glance which is which — **own reproducible computation** (recomputed from free data or a self-contained model, reproducible via the cited script), **literature** (peer-reviewed article or textbook, cited inline), and **practitioner consensus** (desk practice with no clean citation, treated as the weakest). Nothing here is called *validated* on external sources alone; the stronger word requires an own out-of-sample computation.

| Claim / result | Basis |
|---|---|
| A 700-share market buy walks the book to an average fill of 100.0157, about 1.07 ticks above the mid — the price of immediacy | Own reproducible computation — `figures/fig_orderbook_schematic.py` |
| The same ten-tick move occurs on 3,500 shares when liquidity is taken versus 100 shares when it is withdrawn — a 35-to-1 volume ratio | Own reproducible computation — `figures/fig_ten_tick_move.py` |
| SPY intraday volume is U-shaped: first 30 min 14.5%, last 30 min 21.2%, first-and-last hour 51.4%, lunch bar 0.62%, closing bar 9.73% | Own reproducible computation — `figures/fig_intraday_profile.py` |
| A trade in a continuous double auction occurs only where the highest bid meets the lowest offer | Literature — (Harris 2003) |
| Price discovery happens every time a buyer and a seller interact and never truly finishes | Literature — (CME Group, Price Discovery) |
| The intraday volume U-shape is one of the most robust regularities in market microstructure | Literature — (Harris 2003) |
| Participant families are best sorted by their constraint, not their motive; the price-insensitive ones at the bottom are the source of forced flow | Practitioner consensus — not independently verified |
| Option dealers must re-hedge their delta in the underlying regardless of price — the canonical forced flow | Practitioner consensus — not independently verified |
| The three-session (Asian/European/US) handoff, with European-origin moves tending to hold better than thin Asian-hour moves | Practitioner consensus — not independently verified |

## References

- Harris, L. (2003). *Trading and Exchanges: Market Microstructure for Practitioners.* New York: Oxford University Press.
- Dalton, J. F., Jones, E. T., & Dalton, R. B. (1993). *Mind Over Markets: Power Trading with Market Generated Information.* Chicago: Probus Publishing.
- CME Group. *Introduction to Futures: Price Discovery.* CME Institute (free educational course). Open access: <https://www.cmegroup.com/education/courses/introduction-to-futures/price-discovery>.

*All references above are publicly accessible: two are published books available through any library or bookseller, and one is a free institutional educational resource with a direct link given. No proprietary, subscription, course-vendor, or trading-academy material is cited. The empirical figure uses freely available public market data; the three schematic diagrams use fictitious numbers chosen for arithmetic clarity and are labelled as such.*
