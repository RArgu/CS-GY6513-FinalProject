# Data Snapshot (2026-03-18)

Current state of all collected data across the 6 target markets.

## Summary

| Data Type | Records | Size | Source | Coverage |
|-----------|---------|------|--------|----------|
| Prices | 4,820 hourly points | 391 KB | CLOB API | Hourly for resolved, 6h for active |
| Trades | 3,912 | 3.3 MB | Data API | Only recent/active markets |
| Wallet fills | 226,511 | 134 MB | Goldsky subgraph | Complete historical for all 6 markets |
| Metadata | 12 records | 408 KB | Gamma API | All 6 markets |

**Total: ~138 MB, 226K+ on-chain fills with wallet addresses.**

## Per-Market Breakdown

### Resolved Markets (Ground Truth)

**US Strikes Iran by Feb 28** (resolved YES, $89M volume)
- Prices: 1,890 hourly points, Jan 19 to Feb 28
- Wallet fills: 78,314 (39,920 YES / 38,394 NO), 12,751 unique wallets
- Spike: price went from 6.5% to 98.5% in a single hour (Feb 28, 06:00-07:00 UTC)
- Gap: YES token fills for Feb 26 are missing (subgraph timeout on that day). Feb 27-28 recovered via 6h chunking.
- Data API: 0 trades (too old for rolling window)

**Khamenei Out by Feb 28** (resolved YES, $131M volume)
- Prices: 1,338 hourly points, Feb 4 to Mar 3
- Wallet fills: 72,183 (33,949 YES / 38,234 NO), 13,841 unique wallets
- Spike: multi-hour climb on Feb 28, 6.35% -> 46.1% (14:00) -> 94.1% (20:00)
- Data API: 912 trades (recent enough for partial coverage)

**Maduro Out by Jan 31** (resolved YES, $10M volume)
- Prices: 1,052 hourly points, Dec 12 to Jan 2
- Wallet fills: 8,372 (4,174 YES / 4,198 NO), 1,510 unique wallets
- Spike: CLOB price data ends at 6.5% on Jan 2. The spike to 99.9% on Jan 3 is NOT in CLOB data but IS captured in subgraph fills (implied price from fill amounts).
- Data API: 0 trades (too old)

### Active Markets (Ongoing Collection)

**US Forces Enter Iran by Mar 31** ($11M volume, 27.5% YES)
- Prices: 186 points (6h fidelity), Feb 18 to Mar 18
- Wallet fills: 31,734 (16,197 YES / 15,537 NO), 5,960 unique wallets
- Data API: 1,000 trades

**US-Iran Ceasefire by Jun 30** ($1.1M volume, 55.5% YES)
- Prices: 128 points (6h fidelity), Mar 3 to Mar 18
- Wallet fills: 3,574 (1,914 YES / 1,660 NO), 844 unique wallets
- Data API: 1,000 trades

**China Invades Taiwan by end of 2026** ($11M volume, 10.9% YES)
- Prices: 226 points (6h fidelity), Feb 18 to Mar 18
- Wallet fills: 32,334 (12,330 YES / 20,004 NO), 7,647 unique wallets
- Data API: 1,000 trades

## Data Sources and Reliability

### What works

| Source | Resolved Markets | Active Markets |
|--------|-----------------|----------------|
| CLOB API (prices) | Hourly data via 15-day chunked `startTs/endTs`. Use `fidelity=60`. | `interval=1m&fidelity=360` for last 30 days. `startTs/endTs` returns 400 for some active markets. |
| Goldsky subgraph (fills) | Complete historical data. Day-chunked bounded queries for high-volume markets. 6h chunks when daily times out. | `timestamp_gt` cursor pagination works fine. |
| Data API (trades) | Hard offset cap of 3000. Returns 0 for markets resolved >3 weeks ago. | Works, max 10K per page. |

### Known gaps

1. **Maduro CLOB price data** ends Jan 2; the resolution spike on Jan 3 is only in subgraph fills.
2. **Iran strikes YES fills for Feb 26** timed out in both daily and 6h chunk attempts. (~1,300 fills estimated from surrounding days' pattern). All other days recovered.
3. **Data API** is essentially useless for the two oldest resolved markets. The subgraph is the authoritative source.

### Deriving price from subgraph fills

When CLOB price data has gaps, we can reconstruct per-trade price from subgraph fills:
```
implied_price = takerAmountFilled / makerAmountFilled
```
Both amounts are in microunits (divide by 1e6 for dollars). This gives per-second price resolution, much finer than CLOB's hourly snapshots.

## Collection Schedule

- **Resolved markets**: one-shot collection, complete (re-run by deleting files in `data/`)
- **Active markets**: every 6 hours via cron
  ```
  0 */6 * * * cd /path/to/CS-GY6513-FinalProject && python3 collect/fetch_prices.py && python3 collect/fetch_trades.py
  ```
  Wallet fills (`fetch_wallets.py`) can be run less frequently since the subgraph retains all historical data.
