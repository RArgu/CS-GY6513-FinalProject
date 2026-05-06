# Phase 4 — Bet Tracing: Top Insights

**CS-GY 6513 Big Data, Spring 2026**
Based on outputs from `analysis/trace.ipynb`

---

## 1. One Wallet Spent the Most Money Before Every Resolved Market — Always Starting ~24 Hours Early

`0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e` was the largest spender in the 24 hours before the price spike in all three markets that resolved.

| Market | Total USD | Fills | Avg price paid | Hours before spike |
|---|---|---|---|---|
| Khamenei Out | $4,451,215 | 7,162 | $0.797 | 23.8h |
| US Strikes Iran | $450,445 | 2,870 | $0.174 | 22.2h |
| Maduro Out | $237,497 | 528 | $0.610 | 23.8h |

These three markets resolved months apart, on different topics. The same wallet showed up in each one, started buying around 22–24 hours before the spike, and was the biggest spender each time. That timing and consistency across unrelated events is what makes this wallet the strongest suspect in the dataset.

**Attach:** `analysis/trace_charts/top_wallets_khamenei-out-feb28.png`, `top_wallets_us-strikes-iran-feb28.png`, `top_wallets_maduro-out-jan31.png`

---

## 2. The Prime Suspect Bought US Strikes Iran at 17 Cents — Months Before Anyone Cared

In the Maduro and Khamenei markets, the prime suspect was buying YES at relatively high prices (61¢ and 80¢) — the market had already assigned meaningful probability to those outcomes.

In `us-strikes-iran-feb28`, the wallet was buying YES at an **average of 17 cents** — 2,870 fills over 22 hours starting January 21, when the market was pricing a US strike on Iran as a 1-in-6 chance.

That 17¢ position paid out at $1.00 when the market resolved YES — a **nearly 6× return**. Buying at 17 cents is not the behaviour of someone who read a news article and made a bet; it is the behaviour of someone who knew the outcome while the rest of the market thought it was unlikely.

**No image needed** — the number (avg_price = 0.174) from the sanity check output tells the story directly.

---

## 3. Thin Market, Loud Signal: Maduro Had 843 Suspects vs. 10,972 for Khamenei

Despite Maduro having the second-largest z-score spike in the entire dataset (z=33.3), it had by far the fewest suspects:

| Market | Suspect wallets | Total USD in window |
|---|---|---|
| Maduro Out YES | **843** | $2,448,768 |
| Khamenei Out YES | 2,691 | $39,151,577 |
| US Strikes Iran YES | 2,825 | $63,243,762 |

Maduro was a thin, low-activity market. Only 843 wallets were present in the 24 hours before the spike. In that tiny pool, the prime suspect's $237K is an enormous share of total pre-spike volume — it stands out far more than it would in Khamenei's crowd of nearly 11,000. A needle is easier to find in a smaller haystack.

**Attach:** `analysis/trace_charts/suspects_per_market.png`

---

## 4. Two Completely Different Strategies Visible Side by Side in Maduro

The Maduro sanity check shows two wallets at opposite extremes of the timing spectrum:

| Wallet | Avg price | Hours before spike | Total USD | What they did |
|---|---|---|---|---|
| `0x4bfb41d5b3570...` | $0.61 | **23.8h** | $237,497 | Bought early at mid-price, built up over a full day |
| `0xc5adc0dc256fb9...` | $0.98 | **0.1h** | $47,664 | Bought 6 minutes before the spike at near-resolution price |

The first wallet took real risk — buying YES at 61 cents when the market still thought Maduro staying in power was a real possibility. The second wallet bought at 98 cents, just 6 minutes before resolution, with almost no risk and almost no upside (2 cents profit per dollar). They are two completely different types of actors: one potentially informed, one simply reacting to a move already in progress.

**Attach:** `analysis/charts/zoom_maduro_jan03.png` — the zoomed-in Jan 3 chart shows both these wallets' activity in the same narrow window.

---

## 5. Two-Thirds of All Wallet Activity Around Spikes Was Under $100 — The Market Is Mostly Retail

The raw join produced 389,278 wallet-spike pairs. After applying a $100 minimum filter, only 128,096 remained.

**261,182 entries — 67% of all activity — were wallets that placed less than $100** in the 24 hours before a spike.

This means the typical participant around a price spike is a small retail bettor, not an informed actor. The insider signal, if it exists, is buried inside a large population of people placing $10 and $20 bets. The $100 filter is not a high bar — it is less than two dinner bills — and yet it eliminates two thirds of the noise. This highlights how concentrated the suspicious activity is: a handful of wallets deploying millions of dollars at the right time, surrounded by thousands of people doing almost nothing.

**No image needed** — the numbers (389,278 raw → 128,096 filtered → 13,068 distinct wallets) from the summary output make this point clearly.
