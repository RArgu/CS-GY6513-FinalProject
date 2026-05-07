"""
Quick smoke-test for GDELT access via the BigQuery Python client.

Checks:
  1. Can we read the events table at all?
  2. What columns are available?
  3. Do Iran/Khamenei/Maduro/Taiwan events exist in our date ranges?
  4. What does the NumArticles distribution look like (to pick a noise threshold)?

Run from the project root:
    source venv/bin/activate
    python test_scripts/test_gdelt.py
"""

from google.cloud import bigquery

PROJECT = "sr8250-cs6513-polymarket"
client = bigquery.Client(project=PROJECT)

# Try both known GDELT table paths
GDELT_CANDIDATES = [
    "gdelt-bq.gdeltv2.events",
    "gdelt-bq.full.events",
    "bigquery-public-data.gdelt_v2.events",
]


def run(label, sql):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    df = client.query(sql).to_dataframe()
    print(df.to_string(index=False))
    return df


# ── 0. Find the correct GDELT table path ─────────────────────────────────────
GDELT = None
for candidate in GDELT_CANDIDATES:
    try:
        df = client.query(f"SELECT SQLDATE FROM `{candidate}` WHERE SQLDATE = 20260201 LIMIT 1").to_dataframe()
        print(f"GDELT table found: {candidate}")
        GDELT = candidate
        break
    except Exception as e:
        print(f"NOT accessible: {candidate}  ({type(e).__name__})")

if GDELT is None:
    raise SystemExit("No accessible GDELT table found. Check project permissions.")

# ── 1. Schema — sample row to see available columns ───────────────────────────
run("Sample row from GDELT events (schema probe)", f"""
SELECT *
FROM `{GDELT}`
WHERE SQLDATE = 20260201
LIMIT 1
""")

# ── 2. Iran events around US Strikes resolution (Feb 2026) ────────────────────
run("Iran events Feb 25–Mar 01 2026 (sample)", f"""
SELECT SQLDATE, Actor1Name, Actor2Name, EventRootCode,
       GoldsteinScale, AvgTone, NumArticles
FROM `{GDELT}`
WHERE SQLDATE BETWEEN 20260225 AND 20260301
  AND (Actor1Name LIKE '%IRAN%' OR Actor2Name LIKE '%IRAN%')
  AND NumArticles >= 3
ORDER BY NumArticles DESC
LIMIT 20
""")

# ── 3. Khamenei events around resolution ──────────────────────────────────────
run("Khamenei events Feb 2026", f"""
SELECT SQLDATE, Actor1Name, Actor2Name, EventRootCode,
       GoldsteinScale, AvgTone, NumArticles
FROM `{GDELT}`
WHERE SQLDATE BETWEEN 20260201 AND 20260301
  AND (Actor1Name LIKE '%KHAMENEI%' OR Actor2Name LIKE '%KHAMENEI%')
ORDER BY NumArticles DESC
LIMIT 15
""")

# ── 4. Maduro / Venezuela events around Jan 2026 ──────────────────────────────
run("Maduro/Venezuela events Dec 2025 – Jan 2026", f"""
SELECT SQLDATE, Actor1Name, Actor2Name, EventRootCode,
       GoldsteinScale, AvgTone, NumArticles
FROM `{GDELT}`
WHERE SQLDATE BETWEEN 20251215 AND 20260110
  AND (Actor1Name LIKE '%MADURO%' OR Actor2Name LIKE '%MADURO%'
    OR Actor1Name LIKE '%VENEZUELA%' OR Actor2Name LIKE '%VENEZUELA%')
  AND NumArticles >= 3
ORDER BY SQLDATE, NumArticles DESC
LIMIT 20
""")

# ── 5. China / Taiwan events (long window) ────────────────────────────────────
run("China/Taiwan events Jan–Apr 2026 (top by articles)", f"""
SELECT SQLDATE, Actor1Name, Actor2Name, EventRootCode,
       GoldsteinScale, AvgTone, NumArticles
FROM `{GDELT}`
WHERE SQLDATE BETWEEN 20260101 AND 20260430
  AND (Actor1Name LIKE '%TAIWAN%' OR Actor2Name LIKE '%TAIWAN%'
    OR (Actor1CountryCode = 'CHN' AND Actor2CountryCode = 'TWN')
    OR (Actor1CountryCode = 'TWN' AND Actor2CountryCode = 'CHN'))
  AND NumArticles >= 5
ORDER BY NumArticles DESC
LIMIT 15
""")

# ── 6. NumArticles distribution for Iran events in our window ─────────────────
run("NumArticles distribution — Iran events Oct 2025 – Mar 2026", f"""
SELECT
  CASE
    WHEN NumArticles = 1 THEN '1'
    WHEN NumArticles BETWEEN 2 AND 5 THEN '2-5'
    WHEN NumArticles BETWEEN 6 AND 20 THEN '6-20'
    WHEN NumArticles BETWEEN 21 AND 100 THEN '21-100'
    ELSE '100+'
  END AS articles_bucket,
  COUNT(*) AS event_count
FROM `{GDELT}`
WHERE SQLDATE BETWEEN 20251001 AND 20260301
  AND (Actor1Name LIKE '%IRAN%' OR Actor2Name LIKE '%IRAN%')
GROUP BY 1
ORDER BY MIN(NumArticles)
""")

print("\nGDELT test complete.")
