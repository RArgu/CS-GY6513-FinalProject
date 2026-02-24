# CS-GY 6513 Final Project

Big Data final project — NYU Spring 2026.

## Topic: Prediction Markets

We are exploring prediction market data as our project domain. Prediction markets offer rich, high-frequency datasets with clear ground-truth resolution, making them well-suited for large-scale analysis. Below are three candidate directions.

---

### Idea 1: Geopolitical Crisis Markets — Sentiment & News Analysis

Prediction markets price contracts on geopolitical events — missile strikes, ceasefires, troop movements, sanctions, etc. — often with date-specific resolution (e.g., "Will X happen by Y date?"). Markets currently cover Iran, Ukraine, Mexico/border, and other hotspots.

**Core questions:**
- Do prediction markets overreact or underreact to breaking news? How quickly do prices stabilize after a shock?
- Does news lead markets or do markets lead news? (i.e., do informed traders move prices before headlines break?)
- Are certain news sources (AP, Reuters, OSINT Twitter accounts, government briefings) more correlated with price movement than others?
- Can we quantify a "sentiment score" from news text and correlate it with market price changes over time?

**Data sources:** Polymarket, Kalshi, and Metaculus contract prices; news APIs (GDELT, NewsAPI, MediaCloud); social media sentiment (Twitter/X firehose or filtered feeds).

**Big Data angle:** High-volume time-series joins between tick-level market data and a continuous stream of news/social content. NLP pipelines for sentiment extraction at scale.

---

### Idea 2: US Politics & Midterms — Polling, News, and Market Convergence

The 2026 midterm cycle generates a massive volume of structured data: polling aggregates, candidate announcements, fundraising filings, and prediction market contracts on races, chamber control, and margins.

**Core questions:**
- How do prediction market prices compare to polling aggregates as forecasting tools? Which converges to the true outcome faster?
- When polling and markets diverge, which signal tends to be correct?
- Can we identify leading indicators (fundraising spikes, endorsement events, scandal coverage) that move markets before they show up in polls?
- Are there systematic biases in prediction markets for political races (e.g., partisan over-trading, favorite-longshot bias)?

**Data sources:** Polymarket/Kalshi/PredictIt political contracts; FiveThirtyEight / RCP / 538-style polling aggregates; FEC fundraising data; news APIs.

**Big Data angle:** Merging heterogeneous structured datasets (polls, FEC filings, market prices) with unstructured text (news, debate transcripts). Panel analysis across dozens or hundreds of individual race contracts.

---

### Idea 3: BTC/Crypto — Price Analysis & Prediction Market Contracts

Two sub-directions here:

**3A — BTC price action analysis.** Gather high-frequency BTC (and possibly altcoin) price and volume data across exchanges and attempt to find actionable patterns or correlations with external signals (macro announcements, whale wallet movements, social sentiment). Validate findings via paper trading as a proof of concept.

**3B — Crypto prediction market contracts.** Instead of raw price data, focus on prediction market contracts that bet on crypto milestones (e.g., "Will BTC exceed $X by date Y?", "Will ETH hit $Z market cap?"). Analyze how these contract prices relate to spot prices, implied volatility, and news flow — essentially treating the prediction market as a derivative layer on top of the underlying asset.

**Core questions:**
- (3A) Can we extract any statistically significant short-term signals from the noise, or does the efficient market hypothesis hold?
- (3B) Do crypto prediction market prices efficiently embed spot-price information, or are there persistent mispricings?
- How does social media sentiment (Crypto Twitter, Reddit) correlate with both spot prices and prediction contract prices?

**Data sources:** Exchange APIs (Binance, Coinbase); on-chain data (Glassnode, Dune Analytics); Polymarket crypto contracts; Reddit/Twitter sentiment.

**Big Data angle:** Very high-frequency tick data across multiple exchanges, on-chain transaction volumes, and social media streams. Potential for real-time or near-real-time pipeline if paper trading is pursued.

---

## Next Steps

- **Wednesday:** Discuss ideas with teammate and select direction.
- Choose primary data sources and verify API access/rate limits.
- Define project scope and deliverables.
