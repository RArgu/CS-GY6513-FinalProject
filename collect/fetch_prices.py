"""Fetch price history from Polymarket CLOB API for all configured markets.

Resolved markets: one-shot collection for the configured time window, 12h fidelity.
Active markets: incremental collection, 6h fidelity. Appends new data on each run.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

CONFIG_PATH = Path(__file__).parent.parent / "config" / "markets.json"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "prices"

CLOB_BASE = "https://clob.polymarket.com"
CHUNK_DAYS = 15  # resolved markets: chunk requests to avoid empty responses
RATE_LIMIT_DELAY = 0.1  # 1000 req/10s limit


def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = Request(url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except Exception:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise


def ts(date_str):
    return int(datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def fetch_price_chunk(token_id, start_ts, end_ts, fidelity):
    url = (
        f"{CLOB_BASE}/prices-history"
        f"?market={token_id}&startTs={start_ts}&endTs={end_ts}&fidelity={fidelity}"
    )
    data = fetch_json(url)
    return data.get("history", [])


def get_last_timestamp(out_path):
    """For incremental collection: find the latest timestamp already downloaded."""
    if not out_path.exists():
        return None
    last_t = None
    with open(out_path) as f:
        for line in f:
            record = json.loads(line)
            t = record.get("t")
            if t and (last_t is None or t > last_t):
                last_t = t
    return last_t


def collect_resolved(market):
    """One-shot: fetch full price history in 15-day chunks."""
    slug = market["slug"]
    fidelity = market["collection"]["price_fidelity_minutes"]
    start = ts(market["collection"]["collect_from"])
    end = ts(market["collection"]["collect_to"])
    out_path = OUTPUT_DIR / f"{slug}.jsonl"

    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"  {slug}: already collected, skipping (delete file to re-collect)", file=sys.stderr)
        return

    all_points = []
    for side_label, token_id in [("yes", market["clob_token_ids"]["yes"]), ("no", market["clob_token_ids"]["no"])]:
        chunk_start = start
        while chunk_start < end:
            chunk_end = min(chunk_start + CHUNK_DAYS * 86400, end)
            points = fetch_price_chunk(token_id, chunk_start, chunk_end, fidelity)
            for p in points:
                p["side"] = side_label
                p["market_slug"] = slug
            all_points.extend(points)
            print(f"  {side_label} chunk {datetime.fromtimestamp(chunk_start, tz=timezone.utc).date()} -> "
                  f"{datetime.fromtimestamp(chunk_end, tz=timezone.utc).date()}: {len(points)} points", file=sys.stderr)
            chunk_start = chunk_end
            time.sleep(RATE_LIMIT_DELAY)

    all_points.sort(key=lambda x: x["t"])
    with open(out_path, "w") as f:
        for point in all_points:
            f.write(json.dumps(point) + "\n")

    print(f"  -> {out_path} ({len(all_points)} total price points)", file=sys.stderr)


def fetch_price_interval(token_id, interval, fidelity):
    """Fetch price history using interval param (works for active markets)."""
    url = f"{CLOB_BASE}/prices-history?market={token_id}&interval={interval}&fidelity={fidelity}"
    data = fetch_json(url)
    return data.get("history", [])


def collect_active(market):
    """Incremental: fetch last month of data via interval param, deduplicate with existing."""
    slug = market["slug"]
    fidelity = market["collection"]["price_fidelity_minutes"]
    out_path = OUTPUT_DIR / f"{slug}.jsonl"

    # load existing timestamps to deduplicate
    existing_keys = set()
    if out_path.exists():
        with open(out_path) as f:
            for line in f:
                record = json.loads(line)
                existing_keys.add((record["t"], record["side"]))
        print(f"  {slug}: {len(existing_keys)} existing points, checking for new data", file=sys.stderr)
    else:
        print(f"  {slug}: first run", file=sys.stderr)

    new_points = []
    for side_label, token_id in [("yes", market["clob_token_ids"]["yes"]), ("no", market["clob_token_ids"]["no"])]:
        points = fetch_price_interval(token_id, "1m", fidelity)
        for p in points:
            if (p["t"], side_label) not in existing_keys:
                p["side"] = side_label
                p["market_slug"] = slug
                new_points.append(p)
        time.sleep(RATE_LIMIT_DELAY)

    if not new_points:
        print(f"  {slug}: no new data", file=sys.stderr)
        return

    new_points.sort(key=lambda x: x["t"])
    with open(out_path, "a") as f:
        for point in new_points:
            f.write(json.dumps(point) + "\n")

    print(f"  -> {out_path} (+{len(new_points)} new price points)", file=sys.stderr)


def main():
    config = json.loads(CONFIG_PATH.read_text())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for market in config["markets"]:
        print(f"Fetching prices for {market['slug']}...", file=sys.stderr)
        if market["status"] == "resolved":
            collect_resolved(market)
        else:
            collect_active(market)

    print("Price fetch complete.", file=sys.stderr)


if __name__ == "__main__":
    main()
