"""Fetch on-chain order fills from Polymarket's Goldsky subgraph.

This gives us maker/taker wallet addresses for each trade, which the Data API
doesn't expose (it only shows proxy wallets).

Resolved markets use day-chunked queries (bounded timestamp windows) to avoid
subgraph timeouts on high-volume markets. Active markets use unbounded
timestamp_gt cursor pagination.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

CONFIG_PATH = Path(__file__).parent.parent / "config" / "markets.json"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "wallets"

SUBGRAPH_URL = (
    "https://api.goldsky.com/api/public/"
    "project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/0.0.1/gn"
)

FIELDS = "id transactionHash timestamp maker taker makerAssetId takerAssetId makerAmountFilled takerAmountFilled fee"
PAGE_SIZE = 1000  # subgraph max
CHUNK_DAYS = 1  # resolved markets: query one day at a time
RATE_LIMIT_DELAY = 1.0


def query_subgraph(query, retries=3):
    payload = json.dumps({"query": query}).encode()
    for attempt in range(retries):
        try:
            req = Request(
                SUBGRAPH_URL,
                data=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Mozilla/5.0"},
            )
            with urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
            if "errors" in result:
                print(f"  Subgraph error: {result['errors'][0]['message'][:120]}", file=sys.stderr)
                return []
            return result.get("data", {}).get("orderFilledEvents", [])
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


def fetch_fills_chunked(token_id, start_ts, end_ts):
    """Fetch fills in day-sized bounded windows. Works for high-volume resolved markets."""
    all_fills = []
    chunk_start = start_ts

    while chunk_start < end_ts:
        chunk_end = min(chunk_start + CHUNK_DAYS * 86400, end_ts)
        cursor_ts = str(chunk_start - 1)

        while True:
            query = (
                f'{{orderFilledEvents(first: {PAGE_SIZE}, orderBy: timestamp, orderDirection: asc, '
                f'where: {{makerAssetId: "{token_id}", timestamp_gt: "{cursor_ts}", timestamp_lte: "{chunk_end}"}}'
                f') {{ {FIELDS} }}}}'
            )
            fills = query_subgraph(query)
            if not fills:
                break
            all_fills.extend(fills)
            if len(fills) < PAGE_SIZE:
                break
            cursor_ts = fills[-1]["timestamp"]
            time.sleep(RATE_LIMIT_DELAY)

        day_label = datetime.fromtimestamp(chunk_start, tz=timezone.utc).strftime("%Y-%m-%d")
        print(f"    {day_label}: {len(all_fills)} cumulative fills", file=sys.stderr)
        chunk_start = chunk_end
        time.sleep(RATE_LIMIT_DELAY)

    return all_fills


def fetch_fills_incremental(token_id, last_timestamp="0"):
    """Unbounded timestamp_gt pagination for active markets."""
    all_fills = []
    cursor_ts = last_timestamp

    while True:
        query = (
            f'{{orderFilledEvents(first: {PAGE_SIZE}, orderBy: timestamp, orderDirection: asc, '
            f'where: {{makerAssetId: "{token_id}", timestamp_gt: "{cursor_ts}"}}'
            f') {{ {FIELDS} }}}}'
        )
        fills = query_subgraph(query)
        if not fills:
            break
        all_fills.extend(fills)
        print(f"    {len(all_fills)} fills so far...", file=sys.stderr)
        if len(fills) < PAGE_SIZE:
            break
        cursor_ts = fills[-1]["timestamp"]
        time.sleep(RATE_LIMIT_DELAY)

    return all_fills


def get_last_timestamp(out_path):
    if not out_path.exists():
        return "0"
    last_t = "0"
    with open(out_path) as f:
        for line in f:
            record = json.loads(line)
            t = record.get("timestamp", "0")
            if int(t) > int(last_t):
                last_t = t
    return last_t


def collect_market(market):
    slug = market["slug"]
    out_path = OUTPUT_DIR / f"{slug}.jsonl"
    is_resolved = market["status"] == "resolved"

    if is_resolved and out_path.exists() and out_path.stat().st_size > 0:
        print(f"  {slug}: already collected, skipping (delete to re-collect)", file=sys.stderr)
        return

    all_fills = []
    for side_label, token_id in [("yes", market["clob_token_ids"]["yes"]), ("no", market["clob_token_ids"]["no"])]:
        print(f"  {slug} ({side_label} token)...", file=sys.stderr)

        if is_resolved:
            start = ts(market["collection"]["collect_from"])
            end = ts(market["collection"]["collect_to"])
            fills = fetch_fills_chunked(token_id, start, end)
        else:
            last_ts = get_last_timestamp(out_path)
            if last_ts != "0":
                print(f"    resuming from timestamp={last_ts}", file=sys.stderr)
            fills = fetch_fills_incremental(token_id, last_timestamp=last_ts)

        for f in fills:
            f["side"] = side_label
            f["market_slug"] = slug
        all_fills.extend(fills)

    if not all_fills:
        print(f"  {slug}: no fills found", file=sys.stderr)
        return

    all_fills.sort(key=lambda x: int(x.get("timestamp", 0)))
    mode = "w" if is_resolved else "a"
    with open(out_path, mode) as f:
        for fill in all_fills:
            f.write(json.dumps(fill) + "\n")

    print(f"  -> {out_path} ({'+' if not is_resolved else ''}{len(all_fills)} fills)", file=sys.stderr)


def main():
    config = json.loads(CONFIG_PATH.read_text())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for market in config["markets"]:
        print(f"Fetching wallet fills for {market['slug']}...", file=sys.stderr)
        collect_market(market)

    print("Wallet fill fetch complete.", file=sys.stderr)


if __name__ == "__main__":
    main()
