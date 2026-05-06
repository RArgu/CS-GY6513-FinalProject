"""Extract tick-by-tick price series from wallet fill data.

Reads JSONL wallet fills (from fetch_wallets.py) and derives an implied price
for each trade: takerAmountFilled / makerAmountFilled. Both amounts are in
microunits (divide by 1e6 for dollars).

This gives per-trade resolution (vs CLOB's hourly/6h snapshots) and directly
ties each price point to maker/taker wallets, so spike detection and wallet
attribution happen on the same dataset.

Fills the Maduro CLOB gap where prices end Jan 2 but the Jan 3 resolution
spike is fully captured in subgraph fills.
"""

import json
import sys
from pathlib import Path

INPUT_DIR = Path(__file__).parent.parent / "data" / "wallets"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "ticks"


def extract_ticks(input_path, output_path):
    ticks = []

    with open(input_path) as f:
        for line_num, line in enumerate(f, 1):
            fill = json.loads(line)

            maker_amt = int(fill["makerAmountFilled"])
            taker_amt = int(fill["takerAmountFilled"])

            if maker_amt == 0:
                continue

            price = taker_amt / maker_amt
            size_usd = taker_amt / 1e6

            ticks.append({
                "t": int(fill["timestamp"]),
                "p": round(price, 6),
                "size": round(size_usd, 2),
                "side": fill["side"],
                "maker": fill["maker"],
                "taker": fill["taker"],
                "tx": fill["transactionHash"],
                "market_slug": fill["market_slug"],
            })

    ticks.sort(key=lambda x: x["t"])

    with open(output_path, "w") as f:
        for tick in ticks:
            f.write(json.dumps(tick) + "\n")

    return len(ticks)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    input_files = sorted(INPUT_DIR.glob("*.jsonl"))
    if not input_files:
        print("No wallet fill files found in data/wallets/", file=sys.stderr)
        return

    for input_path in input_files:
        slug = input_path.stem
        output_path = OUTPUT_DIR / f"{slug}.jsonl"

        count = extract_ticks(input_path, output_path)
        size_kb = output_path.stat().st_size / 1024

        # time range
        with open(output_path) as f:
            first = json.loads(f.readline())
        with open(output_path, "rb") as f:
            f.seek(max(0, f.seek(0, 2) - 4096), 0)
            last_line = f.read().decode().strip().split("\n")[-1]
            last = json.loads(last_line)

        print(
            f"  {slug}: {count} ticks, "
            f"t=[{first['t']}..{last['t']}], "
            f"{size_kb:.0f} KB",
            file=sys.stderr,
        )

    print("Tick extraction complete.", file=sys.stderr)


if __name__ == "__main__":
    main()
