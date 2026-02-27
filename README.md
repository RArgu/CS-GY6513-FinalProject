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

### Idea 4: Ideas from a security / fraud detection pov
### 4A - Detecting Wash Trading
How much of a prediction market’s volume is "fake" (wash trading) and can we detect these manipulative clusters using graph-based transaction analysis?
In decentralized markets (like Polymarket) users often trade with themselves to create a false sense of liquidity. We can build a detection engine that identifies these circular trading patterns.
Technologies & Tools:
- Spark GraphX (via Spark SQL/DataFrames): To treat traders as "nodes" and transactions as "edges” we can then search for closed loops (A -> B -> C -> A).
- Cassandra: To store the blacklist of suspicious wallets for sub-millisecond querying. (Question - do we really need cassandra here ??)
- HDFS & MapReduce: To process raw blockchain transaction logs to find historical patterns of volume manipulation (Question - can we do this with apache spark rather than hdfs/map reduce)
m
### 4B - Detecting Multi Account Collusion
Can we use graph based clustering to find groups of accounts that always bet together to manipulate the price? (basically find coordination clusters).
Technical logic - look for temporal and behavioral Synchronicity. If 4 accounts always trade the same geopolitical event within milliseconds of each othe, or if they were all funded by the same master wallet they are colluding.
Technologies & Tools (Need to think on this but a rough idea - )
- HDFS & MapReduce: To perform a "Self-Join" on terabytes of transaction data to find accounts with >90% temporal overlap in their trades.
- Apache Tez & Hive: To create a "Risk Score" table for every wallet address based on their proximity to known bad actors.
- WEKA: To use the SimpleKMeans algorithm to cluster wallets based on bet size, timing, and asset choice


---
## Tools and Technologies that will be taught in class - 
1. HDFS, Map Reduce: Hadoop
2. Apache Spark - Saprk SQL, Spark Data Frame, Map Reduce, Streaming (Jupyter Hub)
3. DASK - an acronym for Dansk Aritmetisk Sekvens Kalkulator or Danish Arithmetic Sequence Calculator. (Jupyter Hub)
4. Virtualization and No-SQL Database-Docker and Cassandra Database
5. HIVE – Hive SQL (Data Warehouse env. - (NYU Dataproc Hadoop Ecosystem)
6. Apache Tez and DAG - (NYU Dataproc Hadoop Ecosystem)
7. Document Databases ( Mongo DB and Compass, Mongo query )
8. Apache Spark Data Visualization: Matplotlib (JypyterHub)
9. Apache Spark ML: MLlib (Jupyter Hub)
10. Data Mining with Big Data : WEKA


## Next Steps

- **Wednesday:** Discuss ideas with teammate and select direction.
- Choose primary data sources and verify API access/rate limits.
- Define project scope and deliverables.
