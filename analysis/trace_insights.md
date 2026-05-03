# Bet Tracing — Interesting Insights

**CS-GY 6513 Big Data, Spring 2026**  
Based on outputs from `analysis/trace.ipynb`

---

## 1. One Wallet Appears at the Top of All Three Resolved Markets

`0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e` is the highest-spending suspect in every resolved market:

| Market | Total USD | Fills | Avg price paid | Hours before spike |
|---|---|---|---|---|
| Khamenei Out | $4,451,215 | 7,162 | 0.797 | 23.8h |
| US Strikes Iran | $450,445 | 2,870 | 0.174 | 22.2h |
| Maduro Out | $237,497 | 528 | 0.610 | 23.8h |

The same address, consistently buying YES, consistently starting ~22–24 hours before each spike, in three separate markets that resolved on different dates months apart. A single wallet being the top spender across all three confirmed insider-signal markets is the strongest finding of this phase. Phase 6 ML classification will assign this wallet a high prescience score by construction.

---

## 2. This Wallet Traded 7,162 Times in 24 Hours for One Position

The 7,162 fills for the Khamenei market in a single 24-hour window is not a few large insider bets — it is thousands of small fills placed systematically across the entire window. This is algorithmic or scripted trading, not a person clicking a button. The wallet was dollar-cost averaging into a YES position throughout the day at prices ranging (based on the avg of 0.797 across the window) from likely 0.40 to near 1.0 by the time of the spike. Insider or not, this is a sophisticated automated strategy.

The 2,870 fills for US Strikes Iran (avg price 0.174) tells a different story — they were accumulating when YES was cheap (17 cents), not when it was expensive. Buying 2,870 times at an average of $0.174 over 22 hours means they were building a large position before the market had any strong signal. That pattern is harder to explain as noise.

---

## 3. 67% of Wallet-Spike Pairs Were Below $100 — The Market Is Full of Tiny Bets

The raw join produced 389,278 wallet-spike pairs. After the $100 minimum filter, 128,096 remained — meaning **261,182 entries (67%) were wallets that traded less than $100** in the 24 hours before a spike. Prediction markets have a long tail of small retail bettors. The $100 floor is not a high bar, yet two thirds of activity falls below it. This implies that most wallets engaging around price spikes are small players, not informed actors with capital to deploy.

---

## 4. Taker and Maker Match Counts Are Nearly Equal (720K vs 711K)

The taker join produced 720,622 match rows and the maker join 711,314 — a difference of less than 1.3%. In a normal market you might expect takers to dominate (they cross the spread to trade), but the near-equal ratio here suggests that liquidity provision on the opposite side was as active as directional buying ahead of spikes. This could mean the market had efficient two-sided activity, or it could mean a significant portion of the "maker" suspects were professional market makers who happened to be on the profitable side — not necessarily informed actors.

Phase 5 will help distinguish: a truly informed maker would have placed their limit orders early at specific price levels and pulled them right before the spike. A passive market maker would have been filling orders throughout the window at any price.

---

## 5. Maduro Had 843 Suspect Wallets on Resolution Day vs 10,972 for Khamenei

Maduro's resolution involved far fewer suspect wallets than Khamenei's despite being the cleanest spike (z=33.3, the highest in the dataset). This is consistent with Maduro being a thin market — there simply were not many traders present at all in the 24 hours before the Jan 3 spike. A smaller pool of suspects in a thin market is actually a stronger signal: if only 843 wallets were active and one of them (`0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e`) placed $237K, that one wallet represents an outsized share of total pre-spike volume.

Khamenei's 10,972 suspects reflects a $131M market with extremely high activity on resolution day — the spike attracted thousands of traders, most of whom were probably reacting to public news rather than acting on inside information.

---

## 6. Maduro Suspects Have the Lowest Average Hours Before Spike (5.1h)

Across all markets, the `avg_hours_before` for Maduro YES suspects is only **5.1 hours** — far lower than Khamenei (7.2h), US Strikes Iran (12.7h), or the active markets (12–14h). This makes sense given the Maduro market's history: YES sat at 8–12% for weeks with almost no activity, then jumped suddenly. There was no gradual price climb to trade against. Suspects in this market had a narrow window in which the price was rising to bet into. The 5.1h average says most of the pre-spike YES buying happened in the last few hours before the Jan 3 spike — consistent with the market only becoming interesting once some news started leaking.

---

## 7. A Maker With avg_price 0.982 Appears in the Khamenei Sanity Check

`0x96489abcb9f583d6835c8ef95ffc923d05a86825` appears as a maker suspect for Khamenei with avg_price 0.982 and $232,867 deployed. This wallet was a maker in NO-side fills — meaning the takers who matched against them were buying NO tokens at 0.982 per token. Since YES + NO = $1, an NO price of 0.982 implies the market was pricing YES at only **1.8%** at the time of these fills. This maker was selling NO when the market thought YES was nearly impossible, collecting 98.2 cents per NO token. When YES resolved, NO went to zero and they kept every cent. Whether this was informed trading or aggressive market-making at near-certainty prices is exactly the kind of question Phase 5 will try to answer by looking at when this happened relative to GDELT news.

---

## 8. Two Different Strategies Are Visible in the Maduro Sanity Check

The Maduro resolution window shows two completely different wallet profiles side by side:

- `0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e`: avg_price 0.61, 23.8h before spike — bought early at mid-range prices, started almost a full day before
- `0xc5adc0dc256fb943da868b2f8f6e63f13921b0cf`: avg_price 0.98, 0.1h before spike — bought 6 minutes before the spike at near-resolution prices

The second wallet was chasing a confirmed move, not anticipating it. At avg_price 0.98 on a YES contract that's about to resolve to 1.0, they made a 2-cent profit per dollar. This is a news reactor. The first wallet bought at 0.61 and held through the spike to resolution — a very different risk-reward profile that implies either inside knowledge or a very well-timed informed read on public information.

Phase 5 will formalize this distinction: wallets that traded before relevant GDELT news events get flagged as potential insiders; wallets that traded after get labelled as news reactors.

---

## 9. Q: Are the 13,068 Suspect Wallets All Different Actors?

Almost certainly not. A single person or organization can control multiple wallet addresses on Polymarket. The 13,068 distinct addresses is an upper bound on unique actors. The `0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e` address appearing across all three resolved markets is one address — but the same person could also operate other addresses that show up lower in the rankings. Wallet clustering (same on-chain funding source, similar trade timing, correlated position sizes) is a technique for de-anonymizing these, though it is beyond our current pipeline scope.

---

## 10. Q: Why Does the Same Wallet Have Multiple Entries Per Market in the Sanity Check?

In the Khamenei sanity check, `0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e` appears four times with total_usd values of $4.45M, $1.46M, $1.37M, and $539K. These are not the same amount counted four times — each row is a different (wallet, spike) pair. Khamenei had 28 YES spikes on Feb 28 alone (from the spike distribution table). Since the look-back window for each spike is independent, the wallet appears once for every spike whose 24-hour look-back window it falls into. A wallet that traded throughout the day will match many overlapping windows. Phase 5 aggregates across spikes per wallet to avoid double-counting when computing the final prescience score.
