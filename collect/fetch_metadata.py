"""Fetch contract metadata from Polymarket Gamma API for all configured markets."""

import json
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

CONFIG_PATH = Path(__file__).parent.parent / "config" / "markets.json"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "metadata"

GAMMA_BASE = "https://gamma-api.polymarket.com"
RATE_LIMIT_DELAY = 0.5  # conservative, 300 req/10s limit


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


def fetch_event_metadata(event_slug):
    url = f"{GAMMA_BASE}/events?slug={event_slug}"
    data = fetch_json(url)
    if data:
        return data[0] if isinstance(data, list) else data
    return None


def fetch_market_metadata(condition_id):
    url = f"{GAMMA_BASE}/markets?condition_id={condition_id}"
    data = fetch_json(url)
    if data:
        return data[0] if isinstance(data, list) else data
    return None


def main():
    config = json.loads(CONFIG_PATH.read_text())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for market in config["markets"]:
        slug = market["slug"]
        out_path = OUTPUT_DIR / f"{slug}.jsonl"
        print(f"Fetching metadata for {slug}...", file=sys.stderr)

        records = []

        # Fetch event-level metadata
        event_data = fetch_event_metadata(market["event_slug"])
        if event_data:
            records.append({"type": "event", "data": event_data})
        time.sleep(RATE_LIMIT_DELAY)

        # Fetch market-level metadata
        market_data = fetch_market_metadata(market["condition_id"])
        if market_data:
            records.append({"type": "market", "data": market_data})
        time.sleep(RATE_LIMIT_DELAY)

        with open(out_path, "w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        print(f"  -> {out_path} ({len(records)} records)", file=sys.stderr)

    print("Metadata fetch complete.", file=sys.stderr)


if __name__ == "__main__":
    main()
