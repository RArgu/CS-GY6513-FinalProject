"""
test file to check if the gcp auth is working properly or not
"""

from google.cloud import bigquery
client = bigquery.Client(project="sr8250-cs6513-polymarket")
result = client.query("SELECT COUNT(*) as n FROM polymarket.wallet_fills").result()
for row in result:
    print(row.n)  # should print 0 if no rows or number of rows otherwise