# Project Checklist: Insider Trading Detection on Polymarket

CS-GY 6513 Big Data, Spring 2026 — Rodrigo Arguello (ra2646) | Shwetanshu Raj (sr8250)

---

## Phase 0 — Infrastructure & Environment Setup

### GCP Account
- [x] Create GCP account and project (`sr8250-cs6513-polymarket`)
- [ ] Add partner as Editor via IAM
- [x] Enable BigQuery and Cloud Storage APIs
- [x] Confirm $300 free credits activated (or Azure for Students as fallback)

### Google Cloud Storage
- [x] Create GCS bucket (`cs6513-polymarket`, region `us-east1`)
- [x] Create `raw-backup/` folder
- [x] Create `spark-temp/` folder (used internally by BigQuery Spark connector)

### BigQuery
- [x] Create dataset `polymarket` (region `us-east1`)
- [x] Create table `polymarket.markets`
- [x] Create table `polymarket.wallet_fills`
- [x] Create table `polymarket.ticks`
- [x] Create table `polymarket.prices`
- [ ] Verify both students can query tables from their accounts

### Python Environment
- [x] Create Python venv and install ipykernel + dependencies
- [ ] Register venv as Jupyter kernel in VSCode
- [x] Install BigQuery Spark connector JAR
- [x] Verify PySpark session connects to BigQuery successfully

---

## Phase 1 — Data Collection

### Scripts
- [x] `collect/fetch_metadata.py` — Gamma API, market reference data
- [x] `collect/fetch_prices.py` — CLOB API, hourly/6h price history (YES + NO per market)
- [x] `collect/fetch_trades.py` — Data API, trade records (supplementary only)
- [x] `collect/fetch_wallets.py` — Goldsky subgraph, real maker/taker wallet addresses
- [x] `collect/extract_ticks.py` — derive per-trade tick prices from wallet fills

### Config
- [x] `config/markets.json` — 6 market definitions with token IDs and collection params
- [x] `config/known_suspects.jsonl` — ground truth insider wallets from public reporting

### Data Collected
- [x] `data/metadata/` — 6 files, 12 records
- [x] `data/prices/` — 6 files, 5,102 records, 428 KB
- [x] `data/trades/` — 6 files, 7,912 records, 8.1 MB
- [x] `data/wallets/` — 6 files, 333,363 records, 199 MB
- [x] `data/ticks/` — 6 files, 333,363 records, 94 MB

### Active Market Cron (ongoing)
- [ ] Set up cron job: `0 */6 * * *` for `fetch_prices.py` + `fetch_trades.py`
- [ ] Set up cron job for `fetch_wallets.py` (daily is sufficient)

---

## Phase 2 — Data Ingestion & Storage

### Script: `pipeline/ingest.py`
- [x] Spark session setup with BigQuery connector (`writeMethod=direct`, no GCS temp bucket needed)
- [x] Back up all JSONL files to `gs://cs6513-polymarket/raw-backup/`
- [x] **Clean and load `metadata`** → `polymarket.markets`
  - [x] Filter `type = "event"` only (drop stale Biden/Coronavirus artifact on line 2)
  - [x] Match sub-market by `conditionId` (not `markets[0]` — event has 65+ sub-markets)
  - [x] `yes_token_id`, `no_token_id` taken from `config/markets.json` (already curated)
  - [x] `start_date` from metadata sub-market; `end_date` from config `resolution_date`
- [x] **Clean and load `wallet_fills`** → `polymarket.wallet_fills`
  - [x] Deduplicate by `id`
  - [x] Cast `timestamp` string → long → TIMESTAMP
  - [x] Cast `makerAmountFilled`, `takerAmountFilled`, `fee` strings → long → ÷ 1e6 (USD)
  - [x] Compute `implied_price = taker_amount_usd / maker_amount_usd`
  - [x] Filter: drop rows where `maker` is null
- [x] **Clean and load `ticks`** → `polymarket.ticks`
  - [x] Cast `t` int → TIMESTAMP
  - [x] Validate `p` between 0 and 1 (drops 3,990 resolution-price fills)
  - [x] Validate `size` > 0
- [x] **Clean and load `prices`** → `polymarket.prices`
  - [x] Cast `t` int → TIMESTAMP
  - [x] Validate `p` between 0 and 1
  - [x] Deduplicate by (`market_slug`, `t`, `side`)
- [x] Verify row counts in BigQuery: markets=6, wallet_fills=333,363, ticks=329,373, prices=5,102

---

## Phase 3 — Spike Detection

### Notebook: `analysis/detect.ipynb`
- [x] Read `polymarket.ticks` from BigQuery via Spark connector
- [x] Aggregate into 5-minute VWAP buckets per (`market_slug`, `side`, time window)
- [x] Write intermediate `polymarket.price_aggregates` to BigQuery
- [x] Apply Spark SQL window function: rolling mean + std dev over last 20 buckets
  - [x] `PARTITION BY market_slug, side ORDER BY window_start`
  - [x] `ROWS BETWEEN 20 PRECEDING AND CURRENT ROW`
- [x] Compute z-score: `(vwap - rolling_mean) / rolling_std`
- [x] Flag spikes: `z_score > 3` (tunable threshold)
- [x] Filter noise: require minimum volume per bucket (thin market filter)
- [x] Write `polymarket.spike_events` to BigQuery
  - Fields: `market_slug`, `spike_timestamp`, `side`, `price_before`, `price_after`, `z_score`, `volume_usd`
- [x] Sanity check: verify spikes align with known resolution events
  - [x] US Strikes Iran — Feb 28, 06:00 UTC (6.5% → 98.5% in one hour)
  - [x] Khamenei Out — Feb 28, multi-hour climb
  - [x] Maduro Out — Jan 3 (tick data only, CLOB gap)

---

## Phase 4 — Bet Tracing

### Notebook: `analysis/trace.ipynb`
- [x] Read `polymarket.ticks` + `polymarket.spike_events` from BigQuery
- [x] For each spike, define look-back window: `[spike_timestamp − 24h, spike_timestamp]`
- [x] Temporal join: ticks within look-back window per market + side
- [x] Aggregate by `taker` wallet per spike window
  - [x] `total_taker_usd` = sum of `size_usd`
  - [x] `fill_count`, `avg_price`, `first_bet_timestamp`
- [x] Aggregate by `maker` wallet per spike window (selling correct side = also suspicious)
- [x] Filter: wallets above size threshold (`MIN_WALLET_USD = $100`)
- [x] Filter: correct side only (matching spike direction)
- [x] Write `polymarket.suspect_wallets` to BigQuery
  - Fields: `wallet_address`, `role` (maker/taker), `market_slug`, `spike_id`, `total_usd`, `fill_count`, `avg_price`, `hours_before_spike`

---

## Phase 5 — Prescience Scoring & Feature Engineering

### Notebook: `analysis/score.ipynb`
- [x] Read `polymarket.suspect_wallets` from BigQuery
- [x] Query GDELT: `gdelt-bq.gdeltv2.eventmentions` joined with `gdelt-bq.gdeltv2.events`
  - [x] Define keyword mapping per market (`iran`, `khamenei`, `maduro`, `taiwan`)
  - [x] Filter by keyword + time range per market
  - [x] Use `MentionTimeDate` (YYYYMMDDHHMMSS, 15-min precision) instead of date-only `SQLDATE`
- [x] Temporal join: for each wallet's pre-spike trade → find nearest GDELT mention AFTER trade timestamp (full timestamp, not date-only)
- [x] Compute `time_before_news_hours = mention_timestamp − trade_timestamp`
- [x] Flag `bet_before_news = True` where trade was before news mention
- [x] Aggregate feature vector per wallet:
  - [x] `prescience_score` = bets_before_news / total_bets
  - [x] `win_rate` = correct_bets / total_bets (resolved markets only)
  - [x] `avg_time_before_news_hours`
  - [x] `avg_bet_size_usd`
  - [x] `num_contracts_traded` (as `num_fills_total`)
- [x] Write `polymarket.wallet_features` to BigQuery
  - 11,373 rows; filtered to wallets appearing in ≥ 2 spikes

---

## Phase 6 — ML Classification & Clustering

### Notebook: `analysis/classify.ipynb`
- [x] Read `polymarket.wallet_features` from BigQuery via Spark connector
- [x] **Label training data**
  - [x] Heuristic: `prescience_score > 0.7 AND win_rate > 0.65` → label 1 (2,486 wallets)
  - [x] Override with `config/known_suspects.jsonl` → confirmed label 1 (prime suspect confirmed)
  - [x] All others → label 0 (8,887 wallets)
- [x] **Random Forest Classifier** (`pyspark.ml.classification.RandomForestClassifier`)
  - [x] Assemble feature vector (`VectorAssembler`, 9 features; nulls imputed)
  - [x] Train/test split (70/30, seed=42)
  - [x] Train model (100 trees, max depth 8)
  - [x] Evaluate: accuracy, precision, recall, F1, AUC-ROC
  - [x] Extract feature importances → `classify_charts/feature_importance.png`
- [x] **K-Means Clustering** (`pyspark.ml.clustering.KMeans`)
  - [x] Run on insider-labelled wallets only (2,486 wallets, StandardScaler applied)
  - [x] Try K = 2..5; select best by silhouette score
  - [x] Evaluate with silhouette score
  - [x] Cluster labels: serial_insider (56), high_stakes (444), opportunistic (1,987)
- [x] **Forward validation**
  - [x] Run classifier on wallets active in open markets
  - [x] Risk categories: high_risk (p≥0.8), medium_risk, low_risk
- [x] Write `polymarket.ml_results` to BigQuery (11,373 rows)
  - Fields: `wallet_address`, `label`, `label_probability`, `cluster`, `cluster_label`

---

## Phase 7 — Visualization

### Notebook: `analysis/visualize.ipynb`
- [ ] Read final tables from BigQuery → Pandas (data is small at this stage)
- [ ] Per-contract timeline chart (one per resolved market):
  - [ ] Price over time (tick-derived VWAP or CLOB prices)
  - [ ] Volume bars
  - [ ] Vertical lines for detected spike events
  - [ ] Vertical lines for GDELT news events
  - [ ] Scatter points for flagged wallet activity
- [ ] Wallet cluster scatter plot (feature space coloured by cluster assignment)
- [ ] Feature importance bar chart (from Random Forest)
- [ ] Save all charts to `analysis/charts/`

---

## Phase 8 — Validation & Final Report

### Retrospective Validation (resolved markets)
- [ ] Verify all 3 resolved markets have spike events detected at correct timestamps
- [ ] Verify flagged wallets were on the correct side (YES for all 3)
- [ ] Cross-check top flagged wallets against `config/known_suspects.jsonl`

### Forward Validation (active markets)
- [ ] Record model predictions on active markets before resolution
- [ ] After resolution, compute precision on flagged wallets

### Final Report
- [ ] Pipeline architecture diagram
- [ ] Spike detection results per market
- [ ] Bet tracing results (suspect wallets per spike)
- [ ] Top wallets by prescience score with timeline evidence
- [ ] ML classifier accuracy + feature importances
- [ ] Cluster descriptions (serial insider / one-time leaker / front-runner)
- [ ] Visualization charts
- [ ] Limitations section (Data API gaps, Maduro CLOB gap, GDELT keyword matching)
