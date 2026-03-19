# Insider Trading Detection on Polymarket: Identifying Informed Betting in Geopolitical Prediction Markets

CS-GY 6513, Big Data, Section 1, Spring 2026

**Rodrigo Arguello** (ra2646)
**Shwetanshu Raj** (sr8250)

## Abstract

We're building a batch pipeline to detect insider trading on Polymarket's geopolitical prediction markets. The idea is straightforward: pull trade data from Polymarket's CLOB API for a rolling one-month window of active geopolitical contracts, detect price spikes, trace back the large directional bets that preceded them, identify the wallets behind those bets via the Polymarket Orders subgraph, and then score each wallet against a public news timeline built from GDELT (queried via BigQuery) to measure how consistently they traded on information before it was public. The stack is PySpark for ingestion, cleaning, and per-market price aggregation into HDFS, Spark SQL for spike detection and prescience scoring via window functions, Hive and Tez for warehousing, Spark MLlib for classification and clustering, and Matplotlib for visualization. All in Python.

## Problem Statement and Objectives

Polymarket did over $9 billion in volume during the 2024 U.S. election cycle. Users buy shares in outcomes they think will happen, the market price reflects something like a probability estimate, and when the event resolves the correct side gets paid. It runs on the Polygon blockchain, so all wallets are pseudonymous (no identity verification, no regulatory oversight in the way traditional finance has it).

This creates an obvious opening for insider trading. Someone with advance knowledge of a geopolitical event (a military strike, a policy decision, a diplomatic outcome) can place large bets on the correct side of a contract before the news breaks publicly. In traditional finance this is illegal and monitored. On Polymarket it's unregulated but still detectable, because the trades are all on-chain and timestamped.

We're focusing specifically on geopolitical markets because they have clear information asymmetries. A contract like "Will Country X impose sanctions by April 30?" resolves based on a discrete event with a specific timestamp, and the gap between when insiders know the outcome and when the public learns about it is measurable. That gap is what we're exploiting.

The pipeline works in four stages:

**1. Price spike detection.** We pull trade-level data from Polymarket's CLOB API across active geopolitical markets and compute rolling price aggregates. PySpark handles ingestion and the raw per-market price aggregation across the full dataset, and Spark SQL runs window functions over those aggregates to flag statistically significant price movements, moments where the market shifted sharply in one direction.

**2. Bet tracing.** For each detected spike, we look backward in time and identify the large directional bets that preceded it. We're looking for wallets that placed outsized bets on the correct side of the market shortly before the price moved, the kind of positioning that's consistent with informed trading.

**3. Prescience scoring.** We join trade timestamps against a news event timeline assembled from GDELT (queried through Google BigQuery) to compute a per-wallet "prescience score." This measures how often a wallet was early and correct relative to when information became publicly available. A wallet that consistently bets right before relevant news breaks, across multiple contracts, is statistically distinguishable from a lucky trader.

**4. Classification and clustering.** We train a Spark MLlib classifier (random forest or gradient-boosted trees) to separate normal traders from likely insiders using features like prescience score, win rate, average time-before-news, bet sizing, and number of contracts traded. We then run K-Means clustering on flagged wallets to see whether insider behavior falls into distinct categories (serial insiders vs. one-time leakers vs. front-runners). For validation, we apply the model to currently open contracts and check after resolution whether the wallets we flagged were in fact correct.

## Data Sources

**Polymarket CLOB API.** This is the main data source, trade-level records for active geopolitical markets, so contract ID, which side (YES or NO), amount, price, and timestamp for every fill. The CLOB API gives us a rolling one-month window of historical data, which is a limitation but fine for what we're doing since we care about recent trading patterns, not years of history. We're planning on pulling from roughly 20-50 active geopolitical contracts at any given time. Estimating somewhere around **1-2 GB** of trade data, tens of thousands to low hundreds of thousands of individual trades.

One thing worth noting: the CLOB API doesn't actually expose wallet addresses on public trades. It gives you the trade itself but not who placed it. So for wallet-level attribution (which is kind of the whole point of the bet tracing step) we're querying the **Polymarket Orders Subgraph**, hosted by Goldsky. It's a GraphQL API that indexes order fills and matches on-chain, and it does include maker/taker wallet addresses. Same underlying trades, just enriched with the wallet data we need.

**Polymarket API.** Contract metadata: title, description, resolution source, resolution timestamp, outcome. A few thousand contracts total. We use this to figure out which contracts are geopolitics and to connect raw trades back to real-world events.

**GDELT via Google BigQuery.** This is how we build the news timeline that the prescience score depends on. GDELT is a global event database (timestamps, source URLs, actors, tone scores) and it's natively available on BigQuery, so we can filter millions of news events down to the subset relevant to our selected Polymarket contracts without having to bulk download anything; it's just a SQL query. We're estimating **1-2 GB** of filtered event data once you account for all the contracts we're tracking.

**Total estimated dataset size: 2-4 GB** across all sources, records in the tens of thousands to low millions range.

## Proposed Technologies

**HDFS and PySpark.** PySpark handles the first pass over the data: pulling from the APIs, cleaning, and per-market aggregation (computing rolling price averages across the full historical window for each contract). Everything gets written to HDFS and then loaded into the warehouse. Using PySpark as the single framework for ingestion and processing means Spark SQL, MLlib, and the ingestion layer all share the same runtime, which keeps the codebase simpler than splitting between separate MapReduce jobs and Spark scripts.

**Hive and Apache Tez.** Warehouse layer. Cleaned trade data, contract metadata, news event timestamps, per-wallet scoring tables: everything lands here. The reason we're using Hive specifically (rather than just keeping it all in Spark) is that the joins between trades, contracts, and the GDELT news timeline are complex enough that having a proper warehouse with Tez's DAG execution underneath makes the query patterns a lot more manageable.

**Spark SQL.** This is where most of the actual detection logic lives. Window functions for price spike detection (rolling averages, standard deviation bands over the price series), temporal joins between trade timestamps and GDELT news timestamps to compute prescience scores, and then all the feature engineering that feeds into the classifier. The spike detection piece alone has a few layers to it; we're computing a rolling mean and standard deviation per contract, flagging moments where price moved more than some threshold number of standard deviations in a short window, and then looking at the volume profile around those moments to filter out thin-market noise. Spark SQL's window functions are basically built for this kind of thing.

**Google BigQuery.** Just for GDELT. GDELT is natively hosted on BigQuery so we query it there, filter down to relevant events, and pull the results into our pipeline. No point downloading the whole dataset when we only need a slice.

**Spark MLlib.** Random forest or gradient-boosted trees for the insider vs. normal trader classifier, using features like prescience score, win rate, average time-before-news, bet sizing, number of contracts traded. Then K-Means clustering on the flagged wallets to see if insider behavior falls into distinct patterns (serial insiders who show up across many contracts vs. one-time leakers vs. front-runners). We're planning on validating by applying the model to currently open contracts and checking after resolution whether the wallets we flagged were actually correct.

**Matplotlib** for visualization: per-contract timeline charts showing price, volume, news event markers, and flagged wallet activity overlaid.

Everything is in Python. One thing worth mentioning: since the entire pipeline already runs on PySpark, the ingestion layer could swap to Spark Structured Streaming for near-real-time detection (polling the Polymarket API in micro-batches) without changing the downstream processing, storage, or ML logic. That's not part of the core deliverable (the batch pipeline is the project) but it's a natural extension if we finish early.

## References

1. Polymarket: https://polymarket.com
2. Polymarket CLOB API Documentation: https://docs.polymarket.com
3. Polymarket Subgraph Documentation: https://docs.polymarket.com/market-data/subgraph
4. GDELT Project: https://www.gdeltproject.org
5. GDELT on BigQuery: https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/
6. Google BigQuery: https://cloud.google.com/bigquery
7. Apache Spark Documentation: https://spark.apache.org/docs/latest/
