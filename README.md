# Insider Trading Detection on Polymarket

CS-GY 6513 Big Data, Section 1, Spring 2026
**Rodrigo Arguello** (ra2646) | **Shwetanshu Raj** (sr8250)

Batch pipeline that detects insider trading on Polymarket's geopolitical prediction markets. We pull trade data, detect price spikes, trace the wallets behind large pre-spike bets, and score them against a public news timeline to measure how consistently they traded on non-public information.

## Target Markets

Three resolved markets with documented insider activity (ground truth):
- **US Strikes Iran by Feb 28** ($89M volume, resolved YES)
- **Maduro Out by Jan 31** ($10M volume, resolved YES)
- **Khamenei Out by Feb 28** ($131M volume, resolved YES)

Three active markets for ongoing collection:
- **US Forces Enter Iran by Mar 31** ($11M volume)
- **US-Iran Ceasefire by Jun 30** ($1.1M volume)
- **China Invades Taiwan by end of 2026** ($11M volume)

Market IDs and collection parameters are in `config/markets.json`.
Known suspicious wallets (from public reporting) are in `config/known_suspects.jsonl`.

## Repo Structure

```
config/              Market definitions and known suspect wallets
collect/             Data download scripts (one per data source)
  fetch_metadata.py    Contract metadata from Gamma API
  fetch_prices.py      Price history from CLOB API
  fetch_trades.py      Trade records from Data API
  fetch_wallets.py     On-chain fills with wallet addresses from Goldsky subgraph
data/                Raw downloads (gitignored), one .jsonl per market per type
sync/                Data storage and sync between teammates (Shwetanshu)
pipeline/            PySpark processing (spike detection, scoring)
analysis/            ML, clustering, visualization
docs/                Proposal, API docs, reference materials
```

## Collecting Data

All scripts read from `config/markets.json` and write JSONL to `data/`.

```bash
# one-time setup
pip install py-clob-client  # optional, scripts use urllib directly

# fetch everything (resolved markets are one-shot, active markets are incremental)
python collect/fetch_metadata.py
python collect/fetch_prices.py
python collect/fetch_trades.py
python collect/fetch_wallets.py
```

For active markets, run price and trade collection every 6 hours:
```bash
crontab -e
# add:
0 */6 * * * cd /path/to/CS-GY6513-FinalProject && python collect/fetch_prices.py && python collect/fetch_trades.py
```

## Pipeline (4 stages)

1. **Price spike detection** - PySpark rolling averages + Spark SQL window functions to flag significant price movements
2. **Bet tracing** - for each spike, identify large directional bets that preceded it
3. **Prescience scoring** - join trade timestamps against GDELT news timeline (BigQuery) to compute per-wallet scores
4. **Classification & clustering** - Spark MLlib to cluster wallet behaviors and surface outliers

## Data Sources

| Source | What | API |
|--------|------|-----|
| Polymarket CLOB API | Price history | `clob.polymarket.com/prices-history` |
| Polymarket Data API | Trade records | `data-api.polymarket.com/trades` |
| Polymarket Gamma API | Contract metadata | `gamma-api.polymarket.com/events` |
| Goldsky Subgraph | Wallet addresses per trade | GraphQL (see `docs/api_exploration.md`) |
| GDELT via BigQuery | News event timeline | BigQuery SQL |

API details in `docs/api_exploration.md`.
