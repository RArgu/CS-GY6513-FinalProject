# ML Classification & Clustering V2 — Insights

**CS-GY 6513 Big Data, Spring 2026**  
Based on `analysis/classify.ipynb` (v2 run) reading from `polymarket.wallet_features_v2`

---

## What Changed from V1

The only input change is the feature table: `wallet_features_v2` uses a USD-weighted `win_rate` instead of the count-based formula from V1. Everything else — labeling logic, RF hyperparameters, K-Means K selection, forward validation — is identical.

| Metric | V1 | V2 |
|---|---|---|
| Label-1 wallets | 2,486 (21.9%) | 2,694 (23.7%) |
| RF accuracy | 0.9903 | 0.9903 |
| AUC-ROC | 0.9995 | 0.9995 |
| Label-1 avg probability | 0.971 | 0.954 |
| Label-0 avg probability | 0.008 | 0.014 |
| Label-0 max probability | 0.6512 | 0.8983 |
| serial_insider wallets | 56 | 64 |
| high_stakes wallets | 444 | 487 |
| Forward high-risk wallets | 455 | 463 |
| Prime suspect probability | 0.0139 | 0.024 |

---

## 1. 208 More Wallets Now Labeled as Insiders

V2 labels 2,694 wallets as label-1 vs 2,486 in V1 — an increase of 208. These are wallets whose count-based win_rate was below 0.65 in V1 but whose USD-weighted win_rate is above 0.65 in V2. They had capital predominantly on the YES side (correct for all 3 resolved markets) but appeared in a few NO spike windows, which artificially suppressed their V1 score.

These 208 wallets are genuine additions to the insider candidate pool: their actual directional exposure was correctly aligned with the outcomes, and V2 captures this.

---

## 2. The Prime Suspect's Probability Barely Improved: 0.0139 → 0.024

The prime suspect `0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e` improved from `label_probability = 0.0139` (V1) to `0.024` (V2) — still well below any meaningful threshold. The USD-weighting gave the RF a slightly more ambiguous signal (win_rate went from 0.4532 to 0.4218, actually lower), and the model remains 97.6% confident this wallet is label-0 despite it being label-1 by manual override.

The conclusion is the same as in V1, now confirmed by a second independent run: the prime suspect is a market maker whose bilateral exposure is correctly measured by win_rate as ~0.42 under any weighting scheme. Win_rate is the wrong feature for this archetype. The manual override in `known_suspects.jsonl` is the only mechanism that correctly labels it.

---

## 3. The Label-0 Max Probability Jumped from 0.65 to 0.90

In V1, the highest-scoring label-0 wallet had `label_probability = 0.6512`. In V2 that maximum is `0.8983` — and five label-0 wallets now exceed 0.79. These are wallets that narrowly missed the dual threshold in V1 but whose USD-weighted win_rate in V2 now puts them very close to the boundary.

The top borderline label-0 wallet (`0xb9a72de...`, probability 0.90) is a stronger hidden suspect than anything V1 surfaced. It passed the prescience threshold but not win_rate under count-based scoring; under USD-weighting it is functionally indistinguishable from a label-1 wallet by feature values.

For the final report: wallets with `label=0, label_probability > 0.7` in V2 deserve more scrutiny than those in V1, because V2 filtered out the artificial count-suppression effect.

---

## 4. Feature Importance: win_rate Dominates Even More

V2 feature importances (ranked):

| Feature | Importance |
|---|---|
| win_rate | 0.8996 |
| avg_entry_price | 0.0243 |
| taker_fraction | 0.0149 |
| num_markets_traded | 0.0140 |
| prescience_score | 0.0118 |
| avg_hours_before_news | 0.0110 |
| num_spikes_flagged | 0.0093 |
| avg_hours_before_spike | 0.0086 |
| avg_bet_size_usd | 0.0066 |

`win_rate` now holds 89.96% of total feature importance (vs a similar dominance in V1). The USD-weighted win_rate is an even more decisive feature than the count-based version — it creates a sharper boundary between label-1 and label-0, which the RF exploits almost exclusively.

The practical implication: the V2 model is still primarily reproducing the heuristic rule (`win_rate > 0.65`), not an independent classifier. Features 2–9 contribute only 10% combined. This is unchanged from V1 and is expected given label leakage — the training labels are derived from the features themselves.

---

## 5. K-Means: Serial Insider Cluster Grew from 56 to 64

K (still 4, best silhouette) produced:
- `serial_insider`: 64 wallets (avg bet $4,907, avg markets 2.95)
- `high_stakes`: 487 wallets (avg bet $2,633, avg markets 1.98)
- `opportunistic`: 2,143 wallets across two clusters (avg bet $1,264–$1,544)

The serial_insider cluster grew by 8 wallets — the newly labeled wallets that crossed the win_rate threshold under V2 and had multi-market, high-bet profiles were absorbed into this cluster rather than high_stakes or opportunistic. The archetype is the same: a small group of wallets with consistent multi-market track records betting meaningful capital.

The total labeled insider population is 2,694, so serial_insider is still just 2.4% of the label-1 group — but the most distinctive by avg bet size and market breadth.

---

## 6. Forward Validation: 463 High-Risk Wallets (Up from 455)

The classifier flagged 463 active-market wallets as high-risk (probability ≥ 0.8) compared to 455 in V1. The additional 8 are wallets whose USD-weighted win_rate in resolved markets now exceeds the threshold, making them eligible for label-1 classification and high probability scores.

The top forward-validation wallets are unchanged at the very top: wallets with `win_rate = 1.0` across 2+ resolved markets continue to score ≥ 0.99. The marginal additions are in the 0.80–0.85 probability range — wallets that were borderline in V1 and are now solidly high-risk in V2.

---

## 7. Overall V2 Assessment

V2 is directionally better than V1 for most wallets: the USD-weighted win_rate correctly reflects directional exposure rather than activity level. The 208 new label-1 wallets and the 8 new serial_insiders are genuine improvements.

For the specific problem of flagging the prime suspect via ML features alone, V2 makes no material difference: the wallet is a market maker, and market makers cannot be detected by win_rate regardless of weighting method. The manual override remains necessary.

The final report should present V2 as the canonical result and note V1 in a methodology section as the baseline that motivated the USD-weighting fix.
