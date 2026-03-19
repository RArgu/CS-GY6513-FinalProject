# Polymarket API Exploration

Quick reference for the four APIs we're using to download data. No auth needed for any read-only endpoints.

## API Overview

| API | Base URL | What we use it for |
|-----|----------|--------------------|
| **Gamma API** | `https://gamma-api.polymarket.com` | Market/event discovery, metadata, tags |
| **CLOB API** | `https://clob.polymarket.com` | Price history, order books, current prices |
| **Data API** | `https://data-api.polymarket.com` | Trade-level records with wallet pseudonyms |
| **Subgraph (Goldsky)** | See below | On-chain order fills with maker/taker wallet addresses |

## ID Hierarchy

This is confusing at first, so worth spelling out:

- **Event**: top-level container (e.g., "US strikes Iran by...?"). Has an integer `id` and a `slug`. Contains one or more markets.
- **Market**: a single binary outcome within an event. Has:
  - `id` (integer, used in Gamma API)
  - `conditionId` (hex string, used to query trades on Data API and subgraph)
  - `slug` (URL-friendly name)
- **Token IDs**: each market has exactly two ERC1155 token IDs (YES and NO). Found in `clobTokenIds` field on Gamma responses. These are what you pass to CLOB endpoints like `/prices-history`.

So the flow is: Gamma gives you `conditionId` and `clobTokenIds` per market. You use token IDs for price data (CLOB) and conditionId for trade data (Data API).

---

## 1. Gamma API (Market Discovery)

### List events by tag
```
GET https://gamma-api.polymarket.com/events?tag_slug=geopolitics&active=true&limit=100
```

Key params: `tag_slug`, `active`, `closed`, `archived`, `volume_min`, `liquidity_min`, `limit`, `offset`, `order` (e.g. `volume_24hr`).

### Get single market
```
GET https://gamma-api.polymarket.com/markets/{id}
```

Response includes: `id`, `question`, `conditionId`, `slug`, `outcomes`, `outcomePrices`, `clobTokenIds` (JSON string of `[YES_token_id, NO_token_id]`), `volume`, `volumeNum`, `liquidity`, `startDate`, `endDate`, `closed`, `tags`.

### List available tags
```
GET https://gamma-api.polymarket.com/tags
```

### Rate limits
- General: 4,000 / 10s
- `/markets`: 300 / 10s
- `/events`: 500 / 10s

---

## 2. CLOB API (Price History)

### Price history
```
GET https://clob.polymarket.com/prices-history?market={TOKEN_ID}&startTs={unix}&endTs={unix}&fidelity={minutes}
```

The `market` param here is a **token ID**, not a Gamma market ID or conditionId. Confusing naming.

Response:
```json
{
  "history": [
    {"t": 1700000000, "p": 0.65},
    {"t": 1700003600, "p": 0.67}
  ]
}
```

**The rolling window issue**: using `interval=1m` gives last 1 month only. Using `interval=max` or explicit `startTs/endTs` can go further back, but for resolved markets with fine granularity, data comes back empty if the window is too wide. Workaround: chunk requests into ~15-day windows.

`fidelity` is granularity in minutes. `fidelity=1` = per-minute data. `fidelity=60` = hourly. Default is 1.

### Current prices
```
GET https://clob.polymarket.com/midpoint?token_id={TOKEN_ID}
GET https://clob.polymarket.com/price?token_id={TOKEN_ID}&side=BUY
GET https://clob.polymarket.com/last-trade-price?token_id={TOKEN_ID}
```

### Order book
```
GET https://clob.polymarket.com/book?token_id={TOKEN_ID}
```

### Rate limits
- General: 9,000 / 10s
- `/prices-history`: 1,000 / 10s
- `/price`, `/midpoint`: 1,500 / 10s

---

## 3. Data API (Trade Records)

### Get trades
```
GET https://data-api.polymarket.com/trades?market={CONDITION_ID}&limit=10000
```

Params: `limit` (max 10000), `offset` (max 10000), `market` (conditionId), `eventId`, `user` (wallet address), `side` (BUY/SELL), `takerOnly` (default true), `filterAmount` (min dollar amount).

Response fields per trade: `proxyWallet`, `side`, `asset`, `conditionId`, `size`, `price`, `timestamp`, `title`, `slug`, `outcome`, `outcomeIndex`, `transactionHash`, `name`, `pseudonym`.

Note: `proxyWallet` is a proxy, not the user's real wallet. For real maker/taker addresses, use the subgraph.

### Limitations for resolved markets

The Data API has a **hard offset cap of 3000** for resolved markets. With `limit=10000`, you can reach at most ~13,000 trades (offset 0-3000). Beyond that you get `"max historical activity offset of 3000 exceeded"`. No `startDate`/`endDate`/`before`/`after` params exist.

For markets that resolved more than ~2-3 weeks ago (Iran strikes, Maduro), this returns 0 or very few results. The Data API is **supplementary** for our use case; the subgraph is the primary source for trade-level data.

### Rate limits
- General: 1,000 / 10s
- `/trades`: 200 / 10s

---

## 4. Goldsky Subgraph (On-Chain Wallet Attribution)

This is how we get actual wallet addresses for trades. Five subgraphs, all queried via POST with `{"query": "..."}`:

| Subgraph | Endpoint |
|----------|----------|
| **Orders** | `https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/0.0.1/gn` |
| **Positions** | `.../positions-subgraph/0.0.7/gn` |
| **Activity** | `.../activity-subgraph/0.0.4/gn` |
| **PnL** | `.../pnl-subgraph/0.0.14/gn` |

### This is our primary data source for trade-level analysis

The subgraph has **complete historical data** (no rolling window), includes wallet addresses, and works for all resolved markets. It's the single most important API for the insider detection pipeline.

### Schema: `orderFilledEvent`
Fields: `id`, `transactionHash`, `timestamp`, `maker`, `taker`, `makerAssetId`, `takerAssetId`, `makerAmountFilled`, `takerAmountFilled`, `fee`.

Note: there is **no `price` or `side` field**. Derive implied price as `takerAmountFilled / makerAmountFilled` (both in microunits, divide by 1e6 for dollars). The `maker` and `taker` are real on-chain wallet addresses. Filter by `makerAssetId` using the token ID (not conditionId).

### Pagination

**Do NOT use `skip`-based pagination.** It times out on high-volume markets. Use cursor-based pagination:

For active/moderate markets, use `timestamp_gt`:
```graphql
{
  orderFilledEvents(
    first: 1000, orderBy: timestamp, orderDirection: asc,
    where: { makerAssetId: "TOKEN_ID", timestamp_gt: "LAST_TS" }
  ) { id transactionHash timestamp maker taker makerAssetId takerAssetId makerAmountFilled takerAmountFilled fee }
}
```

For high-volume resolved markets (e.g., Iran strikes, $89M volume), unbounded `timestamp_gt` also times out. Use **bounded day-chunked windows**:
```graphql
where: { makerAssetId: "TOKEN_ID", timestamp_gt: "DAY_START", timestamp_lte: "DAY_END" }
```

If a single day still times out (Feb 28 for Iran strikes YES had 5,550+ fills in 6 hours), shrink chunks to 6 hours.

### Account info
```graphql
{
  account(id: "0xWALLET_ADDRESS") {
    tradesQuantity
    totalVolume
    totalFees
    firstTrade
    lastTrade
    isActive
  }
}
```

---

## Python Client

```bash
pip install py-clob-client
```

```python
from py_clob_client.client import ClobClient

client = ClobClient("https://clob.polymarket.com")

# Price history
history = client.get_prices_history(
    market="TOKEN_ID",
    interval="1d",
    fidelity=60
)

# Current midpoint
mid = client.get_midpoint(token_id="TOKEN_ID")
```

No auth needed for read-only operations.

---

## Download Strategy (Our Pipeline)

1. **Discover**: Gamma API `/events?tag_slug=geopolitics` to get events with nested markets and token IDs
2. **Metadata**: extract `conditionId`, `clobTokenIds`, `outcomes`, `outcomePrices` per market
3. **Price history**: CLOB `/prices-history` per token ID, 15-day chunks, hourly fidelity (`fidelity=60`)
4. **Trades (supplementary)**: Data API `/trades?market=CONDITION_ID` (limited for resolved markets, 3K offset cap)
5. **Wallet fills (primary)**: Subgraph `orderFilledEvents` filtered by `makerAssetId`, day-chunked pagination for resolved markets, `timestamp_gt` cursor for active markets
6. **Wallet profiles**: Subgraph `account` query per flagged wallet (built later)

### Key lesson learned

For resolved markets, **the subgraph is the only reliable source** of complete trade-level data. The CLOB API gives hourly price snapshots but not individual trades. The Data API has a hard offset cap that makes full historical retrieval impossible. The subgraph has everything, but high-volume days require small time-window chunks to avoid query timeouts.

Price can be derived from subgraph fills (`takerAmountFilled / makerAmountFilled`) to reconstruct per-trade price series even when the CLOB API has gaps (e.g., the Maduro market's resolution spike is missing from CLOB but fully captured in the subgraph).
