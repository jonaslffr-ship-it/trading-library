---
title: "Futures and Market Structure"
last_updated: 2026-09-20
---

# Futures and Market Structure

## Abstract

A futures contract is the plumbing beneath most of modern trading, yet it is usually taught as a payoff diagram with the mechanics left out. This paper builds the instrument from its mechanics up: what a standardised exchange-traded futures contract actually is, how the clearinghouse and daily *mark-to-market* replace counterparty trust with a margin account, and how that daily settlement turns a small deposit into leverage. We then open the *order book* — the live ledger of bids and offers, the depth-of-market a trader watches, and the matching rules that turn two intentions into a trade — because price in a futures market is not handed down but *formed* there, order by order. Finally we treat the two features that make futures more than a leveraged proxy for spot: *convergence* to the underlying at expiry, which forces the *term structure* into contango or backwardation and creates a roll yield, and the *basis* between spot and futures that makes them a hedging instrument rather than a bet. The aim is that after reading it, a price on a futures screen is no longer a number but a mechanism you can reason about.

## Keywords

Futures contract, clearinghouse, initial margin, mark-to-market, leverage, order book, depth of market, settlement, expiry, roll, contango, backwardation, basis, hedging, cost of carry

## 1 Introduction

### 1.1 Motivation and thesis

Two people can agree today on a price for a barrel of oil to be delivered in three months. Left as a private handshake, that agreement is fragile — either side can default, and neither can easily exit. A *futures contract* is what you get when an exchange standardises that agreement and a clearinghouse guarantees it, and the thesis of this paper is that almost everything distinctive about futures — the leverage, the daily cash flows, the term structure, the ability to hedge — falls out of two mechanical facts: the contract is *marked to market every day* against a margin account, and it *converges to the underlying* at expiry. Understand those two, and the rest is bookkeeping.

### 1.2 Scope, prerequisites, and intended reader

This paper assumes only that you know what a price is and what it means to buy low and sell high. Every term — margin, mark-to-market, basis, contango — is defined at first use. It is written for a reader who trades or intends to trade futures (or index and commodity products built on them) and wants to understand the mechanism they are standing on rather than a set of memorised rules. It complements the *how-markets-move* paper, which treats the auction and the participant map in general; here the focus is specifically on the futures contract and the structure of its market.

### 1.3 Sources and reproducibility

The mechanics described here are the standard, publicly documented conventions of major derivatives exchanges and the standard textbook treatment of futures pricing; contract-specific numbers (tick size, hours, limits) always live in the exchange's own public contract specification and rulebook, which is the authoritative source for any single product. No claim here depends on private or proprietary material. *This is a research and educational document, not investment advice.*

### 1.4 Organization of this paper

Section 2 defines the standardised contract and the role of the clearinghouse. Section 3 builds margin and mark-to-market, and from them, leverage. Section 4 opens the order book and shows how price is formed. Section 5 covers settlement, the last trading day, and the roll. Section 6 derives the term structure — contango and backwardation — from convergence and the cost of carry. Section 7 treats the basis and why futures are a hedging instrument. Section 8 collects the practical mechanics a live trader must know. Section 9 is the misconceptions list, Section 10 the glossary, and the references close the paper.

## 2 What a futures contract is

A *futures contract* is a standardised, legally binding agreement, traded on an exchange, to buy or sell a specified quantity of a specified underlying at a price agreed now, for settlement on a specified future date. Every term except the price is fixed by the exchange: the *underlying* (a barrel of a defined crude grade, a stock index, a government bond), the *contract size* or *multiplier* (how many units, or how many dollars per index point), the *delivery or settlement date*, and the acceptable *delivery* mechanism. Standardisation is what makes the contract *fungible* — any long can be offset by any short — which is what gives futures their liquidity, in contrast to a bespoke *forward* agreed privately between two parties.

The second defining feature is the *clearinghouse*. When a trade is struck, the clearinghouse steps between the two sides and becomes the buyer to every seller and the seller to every buyer (a process called *novation*). No trader relies on the creditworthiness of the anonymous person on the other side; each faces only the clearinghouse, which manages that risk through the margin system of Section 3. This is why a futures position can be opened and closed freely without tracking down the original counterparty: you are always trading with the clearinghouse, and closing a position simply means holding an equal and opposite contract that nets to zero.

## 3 Margin, mark-to-market, and leverage

You do not pay the full value of a futures contract to hold it. Instead you post *initial margin* — a good-faith deposit, a small fraction of the contract's notional value, sized by the exchange to cover a plausible one-day move. Each day the position is *marked to market*: the clearinghouse computes the day's gain or loss from the settlement price and moves that exact cash into or out of your margin account, every day, until you close. If losses draw the account below the *maintenance margin* level, you receive a *margin call* and must top up or be closed out. Marking to market is the mechanism that lets the clearinghouse guarantee the trade without trusting anyone: gains and losses are settled in cash daily, so no large unpaid loss is ever allowed to accumulate.

*Leverage* is a direct consequence, not a separate feature. Because you control a large notional with a small margin deposit, a given percentage move in the underlying is a much larger percentage move in your posted capital. If a contract's notional is fifty times its initial margin, a 1% move in the underlying is roughly a 50% move in your margin — in either direction. This is the double edge that makes futures efficient for hedgers and dangerous for the undercapitalised: the leverage is built into the margin mechanism itself, and it magnifies the daily mark-to-market cash flows, so a futures trader must size positions against the *notional* and the daily move, never against the margin deposit.

## 4 The order book and how price is formed

A futures price is not announced; it is *discovered* in a continuous double auction. The *order book* is the live, ordered ledger of resting *limit orders*: bids (offers to buy at a stated price or lower) stacked below the market and offers (to sell at a stated price or higher) stacked above, each with a quantity. The best bid and best offer, and the *depth* behind them at each price level, are what a trader sees as the *depth of market* (DOM). A *market order* crosses the spread and executes immediately against the best resting orders on the other side, *taking* liquidity; a *limit order* joins the book and waits, *providing* liquidity. Every trade is one impatient order meeting one or more patient resting ones, and price moves only when incoming orders consume a price level and reach the next.

Two mechanics of the book matter in practice. First, *queue priority*: at a given price, resting orders are generally filled in the order they arrived (price–time priority), so being early in the queue at a level is itself worth something. Second, *displayed versus real liquidity*: the visible depth can be thinner than it looks, because some size is hidden and some evaporates the instant it is hit, so the price at which a large order actually fills — after *slippage* — can be worse than the top of the book suggests. These are the microstructure facts behind the cost figures that any honest strategy must budget for, and they are treated further in the market-mechanics paper.

## 5 Settlement, expiry, and the roll

Every futures contract has a *last trading day* and a defined *settlement*. Under *physical settlement*, an open position at expiry obliges actual delivery of the underlying (barrels, bushels, bonds) against payment; under *cash settlement*, common for index and many financial futures, no goods change hands and the final mark is simply computed against a defined settlement value of the underlying. The overwhelming majority of speculative and hedging positions are never delivered: traders *offset* before expiry by taking the opposite contract, so that their net position is flat when the last trading day arrives.

To maintain exposure beyond one contract's life, a trader *rolls*: close the expiring contract and open the next-dated one. The roll is not free — it crosses the spread twice and is exposed to the price difference between the two contract months, the *calendar spread* — and for a continuously held position it recurs on a schedule, so its cost compounds. Any product that holds futures for you (an index or commodity exchange-traded product, for instance) is rolling on your behalf, and the cumulative cost or benefit of that roll is often the dominant driver of its long-run return, for the reason developed next.

## 6 The term structure: contango and backwardation

At expiry a futures price must equal the spot price of the underlying, because at that moment the contract *is* the underlying — this is *convergence*, and it is forced by arbitrage. Away from expiry, the futures price reflects the *cost of carry*: holding the physical underlying instead of the future costs financing and storage and may earn a yield or convenience, and the futures price adjusts so that the two ways of obtaining the asset at the future date cost the same. When futures for later delivery are *higher* than spot — typically when financing and storage dominate — the curve is in *contango*; when they are *lower* than spot — typically when there is a premium for holding the physical now, a *convenience yield* — it is in *backwardation*.

The term structure is not a curiosity; it is a return, through the roll. A long position in a contango market rolls from a cheaper expiring contract into a more expensive next one and pays that difference repeatedly as each contract converges down toward spot — a persistent *roll cost*. In backwardation the same mechanics run in reverse and pay the holder a *roll yield*. This is why two products tracking the "same" underlying can diverge dramatically over time purely through the shape of the curve, and why a futures trader must read the term structure as part of the position, not as background — the convergence that guarantees the contract also guarantees that the curve's shape is continuously monetised.

## 7 Basis and hedging

The *basis* is the difference between the spot price of the underlying and the futures price, and its behaviour is why futures exist. A producer who will sell a commodity in three months can *hedge* by selling futures now: if the spot price falls, the loss on the eventual physical sale is offset by a gain on the short futures, and vice versa. The hedge is not perfect, because the basis can move — the spot and the future need not travel in lockstep until convergence — and that residual is *basis risk*, usually far smaller than the outright price risk it replaces. The mirror trade lets a consumer lock in a purchase price, and the same mechanism lets a portfolio manager adjust equity or rate exposure quickly and cheaply through index and bond futures rather than trading the underlying basket.

Seen this way, the two populations in a futures market fit together. *Hedgers* come to transfer a price risk they are naturally exposed to and are willing to pay to shed; *speculators* come to take on that risk in search of return and to provide the liquidity the hedgers need. The clearinghouse, margin, and convergence machinery of the previous sections is exactly what makes that transfer trustworthy and continuous, which is the quiet economic purpose beneath the leverage and the flashing prices.

## 8 Practical mechanics a live trader must know

Beyond the concepts, a handful of exchange-set details govern day-to-day trading and live in each product's public specification. The *tick* is the minimum price increment, and the *tick value* is what one tick is worth in cash given the multiplier — together they set the granularity of every profit and loss. *Trading hours* and the *daily settlement time* define when the mark-to-market of Section 3 is struck and when liquidity is deep or thin. *Price limits* and *circuit breakers* halt or band trading after extreme moves, so a position cannot always be exited at will during a shock. *Position limits* cap how much of a contract one participant may hold. None of these is optional knowledge: the tick value determines your risk per contract, the settlement time determines when losses become cash calls, and the limits determine whether you can act in exactly the moments that matter most — which is why the authoritative source for any live decision is the exchange's own current contract spec and rulebook, not a remembered rule of thumb.

## 9 Common misconceptions

- **"Margin is the cost of the contract."** Margin is a good-faith deposit, not a price; the position is marked to market daily and its risk is the full notional, not the deposit (Section 3).
- **"Futures are just leveraged spot."** They also converge at expiry, which forces a term structure whose roll cost or yield can dominate long-run returns (Sections 5–6).
- **"The visible depth is the liquidity."** Displayed size can be thinner than it looks; a large order fills after slippage, worse than the top of book (Section 4).
- **"Contango and backwardation are jargon I can ignore."** They are a recurring cost or income through the roll, often the biggest driver of a held position's return (Section 6).
- **"A hedge removes all risk."** It replaces price risk with the usually much smaller basis risk (Section 7).
- **"I can always get out."** Price limits and circuit breakers can halt trading in exactly the shocks when you most want to exit (Section 8).

## 10 Glossary

- **Backwardation** — a term structure where longer-dated futures are below spot; pays a roll yield to a long.
- **Basis** — spot price minus futures price; its movement is basis risk.
- **Clearinghouse** — the central counterparty that guarantees every futures trade via novation and margin.
- **Contango** — a term structure where longer-dated futures are above spot; imposes a roll cost on a long.
- **Convergence** — the forced equality of futures and spot at expiry.
- **Cost of carry** — financing plus storage minus any yield/convenience of holding the physical.
- **Depth of market (DOM)** — the resting bid and offer quantities at each price level in the order book.
- **Initial / maintenance margin** — the deposit to open a position / the floor below which a margin call is triggered.
- **Mark-to-market** — the daily settlement of a position's gain or loss in cash against the margin account.
- **Multiplier / contract size** — the units of underlying, or dollars per point, that one contract represents.
- **Roll** — closing an expiring contract and opening a later-dated one to maintain exposure.
- **Tick / tick value** — the minimum price increment and its cash worth given the multiplier.

## References

- Hull, J. C. (2022). *Options, Futures, and Other Derivatives* (11th ed.). Hoboken, NJ: Pearson. (Standard treatment of futures mechanics, margining, and the cost-of-carry term structure.)
- Kolb, R. W., & Overdahl, J. A. (2007). *Futures, Options, and Swaps* (5th ed.). Malden, MA: Blackwell. (Contract mechanics, hedging, and the basis.)
- Harris, L. (2003). *Trading and Exchanges: Market Microstructure for Practitioners.* New York: Oxford University Press. (The order book, liquidity, and price formation.)

*All references above are publicly accessible: widely held published books. No proprietary, course, or trading-academy material is cited or used anywhere in this paper; product-specific figures should be taken from the relevant exchange's public contract specification.*

## Evidence basis

| Claim | Basis |
|---|---|
| Standardisation and the clearinghouse (novation) make futures fungible and default-remote | Literature — (Hull 2022; Kolb & Overdahl 2007) |
| Leverage follows mechanically from small margin against large notional marked to market daily | Own derivation from the margin mechanism (Section 3) |
| Price is formed in a continuous double auction with price–time priority; fills slip past top of book | Literature — (Harris 2003) |
| Futures converge to spot at expiry, forcing contango/backwardation via the cost of carry | Literature — (Hull 2022) |
| The roll monetises the term structure and can dominate a held position's long-run return | Own derivation from convergence and the roll (Sections 5–6) |
| Hedging replaces outright price risk with the smaller basis risk | Literature — (Kolb & Overdahl 2007) |
