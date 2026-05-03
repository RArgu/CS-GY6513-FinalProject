# Phase 5 V2 — Prescience Scoring Insights (USD-Weighted Win Rate)

**CS-GY 6513 Big Data, Spring 2026**  
Based on outputs from `analysis/score_v2.ipynb`

---

## Why V2 Exists

Phase 6 (classify.ipynb) revealed that the prime suspect `0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e` received `label_probability = 0.014` from the Random Forest despite being the most suspicious wallet in the dataset. The root cause: `win_rate = 0.4532` in Phase 5 V1, well below the 0.65 heuristic threshold.

The V1 win_rate formula counts spike-window appearances:

```
win_rate = (# YES-spike entries in resolved markets) / (# all entries in resolved markets)
```

The spike detector found 28 YES and 28 NO spikes on resolution day (Feb 28). A wallet trading throughout the day appears in the 24-hour look-back window of every spike — both YES and NO — giving count-based win_rate ≈ 0.5 for any continuously-active wallet, regardless of which side they actually had capital on.

The V2 fix: weight by `total_usd` rather than counts.

```
win_rate_v2 = (sum of total_usd where spike_side="yes" in resolved markets) /
              (sum of total_usd in all resolved market spike windows)
```

---

## 1. USD-Weighting Changes Individual Win Rates Dramatically

Looking at the top-10 wallets by prescience_score, the USD-weighting produces large shifts for directional traders:

| wallet | win_rate V1 | win_rate V2 | change |
|---|---|---|---|
| 0xfe032d... | 0.4667 | 0.8551 | +0.39 |
| 0x96489a... | 0.4444 | 0.8923 | +0.45 |
| 0xd7eee5... | 0.4375 | 0.0165 | −0.42 |
| 0x2e29fc... | 0.4000 | 0.0154 | −0.38 |

This is the correct behavior. A wallet that placed $90K on YES and $10K on NO in resolved markets has `win_rate_count = 0.5` (appeared equally in YES and NO windows) but `win_rate_usd = 0.90`. The V2 formula correctly reflects where the capital actually sat.

The overall distribution shifted to become more bimodal: more wallets now have win_rate close to 0 or 1, with fewer stuck near 0.5. This is better for the Phase 6 classifier because it separates clearly directional traders from neutral ones.

---

## 2. The Prime Suspect's Win Rate Did Not Improve — and That Is Informative

The prime suspect's win_rate went from 0.4532 (V1) to **0.4218 (V2)** — it got slightly worse. This confirms the wallet is a genuine bilateral market maker, not a directional bettor being unfairly penalized by count-based averaging.

Evidence: `avg_entry_price = 0.4984` (nearly exactly 0.5 = the midpoint of a binary market). This wallet is not betting directionally; it is providing liquidity on both YES and NO simultaneously. In the khamenei-out-feb28 market, the trace found $41,112 in a NO spike window and $11,929 in a YES spike window for the same wallet — more capital was captured in NO windows than YES windows, so USD-weighted win_rate is lower than count-based.

A market maker profits from the bid-ask spread regardless of which side wins. Their win_rate as defined here is genuinely ~0.5 and the V2 formula correctly reflects this. The metric is not broken for this wallet; the wallet is simply a different archetype.

---

## 3. The Win Rate Distribution Becomes More Spread After USD Weighting

| Metric | V1 (count) | V2 (USD-weighted) |
|---|---|---|
| mean | 0.2753 | 0.2755 |
| std dev | 0.3931 | 0.4037 |
| min | 0.0 | 0.0 |
| max | 1.0 | 1.0 |

The mean is nearly unchanged (wallets did not systematically shift toward YES or NO), but the standard deviation increased. V2 has more wallets at the extremes (win_rate close to 0 or 1) and fewer near 0.5. This is the ideal property for a classifier feature — it creates more separation between polar opposites.

The practical effect in Phase 6: wallets that are genuinely directional will now exceed the 0.65 threshold more reliably when they deserve to. V2 removes the artificial cap at ≈0.5 that count-based averaging imposed on active traders.

---

## 4. New Phase 6 Candidates: Wallets That Previously Fell Below the Threshold

With V2 win_rates, wallets like `0xfe032d6324fd345a5c0569424a0207349964f14f` (win_rate 0.47 → 0.86) and `0x96489abcb9f583d6835c8ef95ffc923d05a86825` (0.44 → 0.89) now clearly cross the 0.65 threshold. These wallets had their capital primarily on the YES side in resolved markets but were appearing in a few NO spike windows (e.g., they were trading during a window when both YES and NO prices were volatile), which artificially deflated their V1 count-based score. V2 corrects this.

Both wallets have prescience_score = 1.0 and avg_bet_size_usd > $67K. Under V2 they satisfy the heuristic label criterion and will receive label=1 in Phase 6 V2. Phase 6 V1 labelled them as 0.

---

## 5. The Prime Suspect Needs a Different Metric: Net Directional Exposure

For a market maker, win_rate is the wrong signal. The correct metric would be net directional exposure per resolved market:

```
net_yes_usd = sum(total_usd where spike_side="yes") - sum(total_usd where spike_side="no")
```

If `net_yes_usd > 0` in a YES-resolved market, the wallet had net long YES exposure — a win. This would require a different aggregation than the spike-window approach and would need Phase 4 data at the individual-position level rather than per-spike aggregate. That is a potential Phase 5 V3 or an enhancement for the final report's limitations section.

For Phase 6 V2, the prime suspect remains correctly flagged via the manual override in `config/known_suspects.jsonl`. The ML model's inability to score it highly via features is itself the finding — it tells us that win_rate and prescience_score alone are insufficient to flag sophisticated market-making insiders.

---

## 6. What V2 Fixes vs What It Cannot Fix

**V2 fixes:**
- Directional traders who appeared in a few wrong-side spike windows (artificially suppressed win_rate in V1)
- The count-based ≈0.5 ceiling for any wallet active in multiple spike windows on the same day

**V2 cannot fix:**
- Market makers whose actual USD exposure is bilateral (they genuinely have ≈0.5 win_rate by this metric)
- Wallets that correctly traded both YES and NO at different points in the market's history

**The conclusion for the final report:** V2 win_rate is a better feature than V1 for directional traders. It does not help the market-maker archetype, and that is correct behavior — a market maker should be detected via different features (bet size, market breadth, timing) rather than directional win rate.

---

## 7. BigQuery Tables Written

- `polymarket.wallet_features` — V1, count-based win_rate (preserved)
- `polymarket.wallet_features_v2` — V2, USD-weighted win_rate (this notebook)

Phase 6 V2 should read from `wallet_features_v2` to see the improved feature quality for directional traders.
