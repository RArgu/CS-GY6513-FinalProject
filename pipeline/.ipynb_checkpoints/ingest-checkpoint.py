import json
import subprocess
from pathlib import Path

from google.cloud import bigquery
from pyspark.sql import SparkSession, functions as F

PROJECT = "sr8250-cs6513-polymarket"
BUCKET = "cs6513-polymarket"
DATASET = "polymarket"

ROOT = Path(__file__).parent.parent
JAR = str(ROOT / "jars" / "spark-bigquery-with-dependencies_2.12-0.36.1.jar")
DATA = ROOT / "data"
CONFIG = ROOT / "config" / "markets.json"


def get_spark():
    """
    Creates a local SparkSession configured with the BigQuery connector JAR

    Returns:
        A configured SparkSession
    """
    return (
        SparkSession.builder
        .appName("polymarket-ingest")
        .config("spark.jars", JAR)
        .getOrCreate()
    )


def write_bq(df, table):
    """
    Writes a Spark DataFrame to a BigQuery table, overwriting any existing data

    Args:
        df: The Spark DataFrame to write
        table: The BigQuery table name within the configured dataset
    """
    # 2 partitions = 2 concurrent write streams; 9 (default) overwhelms the BQ Storage Write API
    (
        df.repartition(2)
        .write
        .format("bigquery")
        .option("table", f"{PROJECT}.{DATASET}.{table}")
        .option("writeMethod", "direct")
        .mode("overwrite")
        .save()
    )


def backup_to_gcs():
    """
    Uploads all JSONL files from data/ to gs://cs6513-polymarket/raw-backup/,
    preserving the subdirectory structure
    """
    # rsync copies contents of DATA into raw-backup/ (cp -r would add an extra data/ level)
    subprocess.run(
        ["gsutil", "-m", "rsync", "-r", str(DATA), f"gs://{BUCKET}/raw-backup/"],
        check=True
    )


def ingest_markets():
    """
    Builds the markets reference table from config/markets.json, enriched with
    title, description, and start_date pulled from the corresponding metadata files.
    Loads 6 rows into polymarket.markets via the BigQuery Python client
    """
    with open(CONFIG) as f:
        cfg = json.load(f)

    rows = []
    for m in cfg["markets"]:
        meta_file = DATA / "metadata" / f"{m['slug']}.jsonl"
        title = description = start_date = None

        if meta_file.exists():
            with open(meta_file) as f:
                for line in f:
                    rec = json.loads(line.strip())
                    # each file has one "event" line and one stale artifact line (Biden/Coronavirus)
                    if rec.get("type") != "event":
                        continue
                    e = rec["data"]
                    title = e.get("title")
                    description = e.get("description")
                    # event contains 65+ sub-markets for different dates; match on conditionId
                    for sub in e.get("markets", []):
                        if sub.get("conditionId") == m["condition_id"]:
                            start_date = sub.get("startDate")
                            break

        # metadata endDate is per sub-market window and doesn't match resolution; use config value
        rd = m.get("resolution_date")
        end_date = f"{rd}T00:00:00Z" if rd else None

        tokens = m["clob_token_ids"]
        rows.append({
            "market_slug": m["slug"],
            "condition_id": m["condition_id"],
            "event_slug": m["event_slug"],
            "title": title,
            "question": m["question"],
            "description": description,
            "status": m["status"],
            "start_date": start_date,
            "end_date": end_date,
            "resolution_outcome": m.get("outcome"),
            "volume_usd": float(m["volume"]),
            "open_interest": None,
            "liquidity": None,
            "yes_token_id": tokens["yes"],
            "no_token_id": tokens["no"],
        })

    bq = bigquery.Client(project=PROJECT)
    table_ref = f"{PROJECT}.{DATASET}.markets"
    job_cfg = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    bq.load_table_from_json(rows, table_ref, job_config=job_cfg).result()
    print(f"  markets: {len(rows)} rows")


def ingest_wallet_fills(spark):
    """
    Reads wallet fill JSONL files, converts amounts from raw integer strings to USD floats,
    deduplicates by id, and loads the result into polymarket.wallet_fills

    Args:
        spark: The active SparkSession
    """
    df = spark.read.json(f"file://{DATA}/wallets/*.jsonl")

    maker_amt = F.col("makerAmountFilled").cast("long")
    taker_amt = F.col("takerAmountFilled").cast("long")

    df = (
        df.select(
            F.col("id"),
            F.col("transactionHash").alias("transaction_hash"),
            F.col("market_slug"),
            # timestamp is a unix epoch string, not ISO format
            F.col("timestamp").cast("long").cast("timestamp").alias("timestamp"),
            F.col("maker"),
            F.col("taker"),
            F.col("makerAssetId").alias("maker_asset_id"),
            F.col("takerAssetId").alias("taker_asset_id"),
            (maker_amt / 1e6).alias("maker_amount_usd"),
            (taker_amt / 1e6).alias("taker_amount_usd"),
            (taker_amt / maker_amt).alias("implied_price"),
            (F.col("fee").cast("long") / 1e6).alias("fee_usd"),
            F.col("side"),
        )
        .dropDuplicates(["id"])
        .filter(F.col("maker").isNotNull())
    )

    print(f"  wallet_fills: {df.count()} rows")
    write_bq(df, "wallet_fills")


def ingest_ticks(spark):
    """
    Reads tick JSONL files, converts unix epoch to TIMESTAMP, filters out
    invalid prices and zero-size trades, and loads into polymarket.ticks

    Args:
        spark: The active SparkSession
    """
    df = spark.read.json(f"file://{DATA}/ticks/*.jsonl")

    df = (
        df.select(
            F.col("market_slug"),
            F.col("t").cast("timestamp").alias("timestamp"),
            F.col("p").alias("implied_price"),
            F.col("size").alias("size_usd"),
            F.col("side"),
            F.col("maker"),
            F.col("taker"),
            F.col("tx").alias("transaction_hash"),
        )
        .filter((F.col("implied_price") > 0) & (F.col("implied_price") < 1))
        .filter(F.col("size_usd") > 0)
    )

    print(f"  ticks: {df.count()} rows")
    write_bq(df, "ticks")


def ingest_prices(spark):
    """
    Reads price JSONL files, converts unix epoch to TIMESTAMP, filters invalid prices,
    deduplicates by (market_slug, timestamp, side), and loads into polymarket.prices

    Args:
        spark: The active SparkSession
    """
    df = spark.read.json(f"file://{DATA}/prices/*.jsonl")

    df = (
        df.select(
            F.col("market_slug"),
            F.col("t").cast("timestamp").alias("timestamp"),
            F.col("p").alias("price"),
            F.col("side"),
        )
        .filter((F.col("price") > 0) & (F.col("price") < 1))
        .dropDuplicates(["market_slug", "timestamp", "side"])
    )

    print(f"  prices: {df.count()} rows")
    write_bq(df, "prices")


if __name__ == "__main__":
    spark = get_spark()
    spark.sparkContext.setLogLevel("WARN")

    print("Backing up to GCS...")
    backup_to_gcs()

    print("\nIngesting markets...")
    ingest_markets()

    print("\nIngesting wallet_fills...")
    ingest_wallet_fills(spark)

    print("\nIngesting ticks...")
    ingest_ticks(spark)

    print("\nIngesting prices...")
    ingest_prices(spark)

    spark.stop()
    print("\nDone")
