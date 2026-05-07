"""Fetch trade records from Polymarket Data API for all configured markets.

Resolved markets: one-shot, paginate by timestamp to collect all trades in the
configured window (1 month back from resolution).
Active markets: incremental, append trades newer than the last collected timestamp.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import urlencode

CONFIG_PATH = Path(__file__).parent.parent / "config" / "markets.json"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "trades"

DATA_API_BASE = "https://data-api.polymarket.com"
PAGE_SIZE = 10000  # max allowed
RATE_LIMIT_DELAY = 0.5  # 200 req/10s limit


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


def get_last_timestamp(out_path):
    if not out_path.exists():
        return None
    last_t = None
    with open(out_path) as f:
        for line in f:
            record = json.loads(line)
            t = record.get("timestamp")
            if t and (last_t is None or t > last_t):
                last_t = t
    return last_t


def fetch_trades_page(condition_id, offset=0, before_ts=None, after_ts=None):
    params = {
        "market": condition_id,
        "limit": PAGE_SIZE,
        "offset": offset,
    }
    if before_ts:
        params["before"] = before_ts
    if after_ts:
        params["after"] = after_ts
    url = f"{DATA_API_BASE}/trades?{urlencode(params)}"
    return fetch_json(url)


def collect_resolved(market):
    """Paginate through all trades in the configured time window."""
    slug = market["slug"]
    condition_id = market["condition_id"]
    out_path = OUTPUT_DIR / f"{slug}.jsonl"
    window_start = ts(market["collection"]["collect_from"])
    window_end = ts(market["collection"]["collect_to"])

    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"  {slug}: already collected, skipping", file=sys.stderr)
        return

    all_trades = []
    offset = 0

    while True:
        trades = fetch_trades_page(condition_id, offset=offset)
        if not trades:
            break

        # filter to our time window
        in_window = [t for t in trades if window_start <= t.get("timestamp", 0) <= window_end]
        all_trades.extend(in_window)

        # if we got trades older than our window start, we're done
        oldest = min(t.get("timestamp", float("inf")) for t in trades)
        if oldest < window_start:
            break

        # if we got fewer than PAGE_SIZE, no more pages
        if len(trades) < PAGE_SIZE:
            break

        # Data API caps offset at 10000, so paginate by timestamp instead
        if offset + PAGE_SIZE >= 10000:
            # use the oldest timestamp from this batch as the new "before" cursor
            oldest_ts = min(t.get("timestamp", 0) for t in trades)
            print(f"  Offset limit reached, cursor-paginating from ts={oldest_ts}", file=sys.stderr)
            offset = 0
            cursor_trades = fetch_trades_page(condition_id, offset=0, before_ts=oldest_ts)
            if not cursor_trades:
                break
            in_window = [t for t in cursor_trades if window_start <= t.get("timestamp", 0) <= window_end]
            all_trades.extend(in_window)
            if len(cursor_trades) < PAGE_SIZE:
                break
            continue

        offset += PAGE_SIZE
        print(f"  {slug}: {len(all_trades)} trades so far...", file=sys.stderr)
        time.sleep(RATE_LIMIT_DELAY)

    # deduplicate by transaction hash
    seen = set()
    unique_trades = []
    for t in all_trades:
        tx = t.get("transactionHash", "")
        key = f"{tx}_{t.get('outcome', '')}_{t.get('timestamp', '')}"
        if key not in seen:
            seen.add(key)
            unique_trades.append(t)

    unique_trades.sort(key=lambda x: x.get("timestamp", 0))
    with open(out_path, "w") as f:
        for trade in unique_trades:
            trade["market_slug"] = slug
            f.write(json.dumps(trade) + "\n")

    print(f"  -> {out_path} ({len(unique_trades)} trades)", file=sys.stderr)


def collect_active(market):
    """Incremental: fetch trades newer than the last collected one."""
    slug = market["slug"]
    condition_id = market["condition_id"]
    out_path = OUTPUT_DIR / f"{slug}.jsonl"

    last_t = get_last_timestamp(out_path)
    after_ts = last_t if last_t else int(datetime.now(timezone.utc).timestamp()) - 30 * 86400

    if last_t:
        print(f"  {slug}: resuming from {datetime.fromtimestamp(after_ts, tz=timezone.utc).isoformat()}", file=sys.stderr)
    else:
        print(f"  {slug}: first run, collecting last 30 days", file=sys.stderr)

    new_trades = []
    offset = 0

    while True:
        trades = fetch_trades_page(condition_id, offset=offset, after_ts=after_ts)
        if not trades:
            break
        new_trades.extend(trades)
        if len(trades) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        if offset >= 10000:
            break
        time.sleep(RATE_LIMIT_DELAY)

    if not new_trades:
        print(f"  {slug}: no new trades", file=sys.stderr)
        return

    # deduplicate
    seen = set()
    unique = []
    for t in new_trades:
        tx = t.get("transactionHash", "")
        key = f"{tx}_{t.get('outcome', '')}_{t.get('timestamp', '')}"
        if key not in seen:
            seen.add(key)
            unique.append(t)

    unique.sort(key=lambda x: x.get("timestamp", 0))
    with open(out_path, "a") as f:
        for trade in unique:
            trade["market_slug"] = slug
            f.write(json.dumps(trade) + "\n")

    print(f"  -> {out_path} (+{len(unique)} new trades)", file=sys.stderr)


def main():
    config = json.loads(CONFIG_PATH.read_text())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for market in config["markets"]:
        print(f"Fetching trades for {market['slug']}...", file=sys.stderr)
        if market["status"] == "resolved":
            collect_resolved(market)
        else:
            collect_active(market)

    print("Trade fetch complete.", file=sys.stderr)


if __name__ == "__main__":
    main()
