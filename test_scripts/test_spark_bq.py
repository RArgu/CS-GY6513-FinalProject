"""
To verify PySpark connects to BigQuery
"""

from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("test-bq-connection") \
    .config("spark.jars", "../jars/spark-bigquery-with-dependencies_2.12-0.36.1.jar") \
    .getOrCreate()

df = spark.read \
    .format("bigquery") \
    .option("table", "sr8250-cs6513-polymarket.polymarket.wallet_fills") \
    .load()

print(f"Connected. Row count: {df.count()}")  # should print 0
spark.stop()