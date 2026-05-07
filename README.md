# Insider Trading Detection on Polymarket

CS-GY 6513 Big Data, Section 1, Spring 2026
**Rodrigo Arguello** (ra2646) | **Shwetanshu Raj** (sr8250)

## Abstract

We built a 6-phase batch pipeline that detects insider trading on Polymarket's geopolitical prediction markets. Trade-level data was collected from Polymarket's CLOB and Goldsky subgraph APIs across 6 contracts. The pipeline flags anomalous price spikes using PySpark window functions, traces the wallets behind large pre-spike bets, and scores those wallets against a GDELT news timeline queried via BigQuery. Wallets are then classified using Random Forest and clustered with K-Means in Spark MLlib.

3 markets resolved during the collection window, giving us real ground truth to validate against. In each case, a single wallet had placed hundreds of millions of dollars across all three — 22 to 24 hours before resolution.

### Target Markets

| Market | Volume | Status |
|--------|--------|--------|
| US Strikes Iran by Feb 28 | $89M | Resolved YES |
| Maduro Out by Jan 31 | $10M | Resolved YES |
| Khamenei Out by Feb 28 | $131M | Resolved YES |
| US Forces Enter Iran by Mar 31 | $11M | Active |
| US-Iran Ceasefire by Jun 30 | $1.1M | Active |
| China Invades Taiwan by end of 2026 | $11M | Active |

---

## Repo Structure

```
config/
  markets.json              Market IDs and collection parameters
  known_suspects.jsonl      Wallets flagged in public reporting

collect/
  fetch_metadata.py         Contract metadata from Gamma API
  fetch_prices.py           Price history from CLOB API
  fetch_trades.py           Trade records from Data API
  fetch_wallets.py          On-chain fills with wallet addresses from Goldsky subgraph
  extract_ticks.py          Derive per-trade tick prices from wallet fills

pipeline/
  ingest.py                 Phase 1 & 2 — load JSONL into BigQuery via PySpark + GCS backup

analysis/
  detect.ipynb              Phase 3 — VWAP bucketing, z-score rolling stats, spike detection
  trace.ipynb               Phase 4 — bet tracing: wallets behind large pre-spike positions
  score.ipynb               Phase 5 — prescience scoring against GDELT news timeline
  score_v2.ipynb            Phase 5 (revised) — GDELT + improved feature engineering
  classify.ipynb            Phase 6 — Random Forest classification + K-Means clustering
  charts/                   VWAP, z-score, and spike charts per market
  trace_charts/             Top-wallet bar charts from bet tracing
  score_charts/             Prescience score distributions
  classify_charts/          ML output visualizations

jars/
  spark-bigquery-with-dependencies_2.12-0.36.1.jar   BigQuery connector for Spark

docs/                       Proposal and reference materials
```

---

## Prerequisites

### Python & Java

- Python 3.9+
- Java 11+ (required for PySpark)

### Python packages

```bash
pip install -r req.txt
```

Key dependencies: `pyspark==4.1.1`, `google-cloud-bigquery`, `google-cloud-storage`, `pandas`, `matplotlib`, `numpy`, `jupyter`

### Google Cloud

- A GCP project with BigQuery and GCS enabled
- A service account key with BigQuery Data Editor + GCS Object Admin roles
- Set the environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

Update the `PROJECT`, `BUCKET`, and `DATASET` constants at the top of `pipeline/ingest.py` and each analysis notebook to match your GCP project.

The BigQuery connector JAR is already included at `jars/spark-bigquery-with-dependencies_2.12-0.36.1.jar`.

---

## Execution

Run phases in order. Each phase reads from BigQuery tables written by the previous one.

### Phase 1 & 2 — Data Collection and Ingest

```bash
# Collect raw data from APIs
python3 collect/fetch_metadata.py
python3 collect/fetch_prices.py
python3 collect/fetch_trades.py
python3 collect/fetch_wallets.py
python3 collect/extract_ticks.py

# Ingest JSONL into BigQuery and back up to GCS
python3 pipeline/ingest.py
```

For active markets, schedule incremental price and trade collection:

```bash
crontab -e
# add:
0 */6 * * * cd /path/to/CS-GY6513-FinalProject && python3 collect/fetch_prices.py && python3 collect/fetch_trades.py
```

### Phases 3–6 — Analysis Notebooks

Open JupyterLab and run cells top-to-bottom in this order:

```bash
jupyter lab
```

| Notebook | Phase | What it does |
|----------|-------|--------------|
| `analysis/detect.ipynb` | 3 | Computes 5-min VWAP buckets, rolling z-scores, flags spike events; writes `spike_events` to BigQuery |
| `analysis/trace.ipynb` | 4 | For each spike, looks back 24 hours to find large directional bets; writes `suspect_wallets` to BigQuery |
| `analysis/score_v2.ipynb` | 5 | Joins wallet trade timestamps against GDELT news events via BigQuery; computes per-wallet prescience scores |
| `analysis/classify.ipynb` | 6 | Trains Random Forest classifier and K-Means clustering on wallet features using Spark MLlib |

Each notebook writes its outputs back to BigQuery and saves charts to `analysis/charts/`, `analysis/trace_charts/`, `analysis/score_charts/`, and `analysis/classify_charts/`.

---

## Data Sources

| Source | What | Endpoint |
|--------|------|----------|
| Polymarket CLOB API | Price history | `clob.polymarket.com/prices-history` |
| Polymarket Data API | Trade records | `data-api.polymarket.com/trades` |
| Polymarket Gamma API | Contract metadata | `gamma-api.polymarket.com/events` |
| Goldsky Subgraph | Wallet addresses per fill | GraphQL |
| GDELT via BigQuery | News event timeline | BigQuery SQL (`gdelt-bq.gdeltv2.events`) |
