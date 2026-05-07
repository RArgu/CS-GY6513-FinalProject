# ML Classification & Clustering — Interesting Insights

**CS-GY 6513 Big Data, Spring 2026**  
Based on outputs from `analysis/classify.ipynb`

---

## 1. The Model Assigned the Prime Suspect a Near-Zero Insider Probability

`0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e` — the wallet that dominated every resolved market in Phase 4 — received `label_probability = 0.0139` from the Random Forest. Despite being overridden to label = 1 (confirmed insider), the model scored it as 98.6% likely to be label 0.

The reason is direct: the model learned the heuristic rule (`win_rate > 0.65 AND prescience_score > 0.7`), and the prime suspect's `win_rate = 0.4532` is well below the 0.65 threshold. The win_rate is depressed because it was flagged in BOTH YES and NO spike windows during resolution day across all 3 resolved markets — the spike detector found 28 YES and 28 NO spikes on Feb 28, and a wallet trading throughout the day will appear in the look-back window of both. The win_rate formula counts (YES-spike appearances in resolved markets) / (all spike appearances in resolved markets), which penalises wallets that were continuously active rather than ones that made targeted bets.

This is the starkest demonstration that the heuristic label is wrong for this wallet, and a well-specified classifier would not use win_rate computed this way. **The prime suspect is the most suspicious wallet in the dataset by every raw metric ($116K/spike, 562 spikes, all 6 markets) but the ML model disagrees with the manual label**. For the final report this tension should be highlighted explicitly.

---

## 2. The serial_insider Cluster Has Only 56 Wallets but the Highest Win Rate

K-Means produced a `serial_insider` cluster of just 56 wallets distinguished by the highest average bet size ($4,697/spike), the highest average number of markets traded (2.88), and the highest average win rate (0.845). These are wallets with a track record — they bet correctly across multiple markets consistently, deploying meaningful capital each time.

56 out of 11,373 wallets is 0.49%. In a market with thousands of participants, fewer than 1 in 200 wallets meets the threshold of multi-market, high-win-rate, large-bet behaviour. If any of these 56 are genuine insiders, the concentration of benefit (and harm to the market) is extreme.

---

## 3. The Opportunistic Cluster Has the Highest Average Win Rate (0.993) — and It's Misleading

The `opportunistic` cluster (1,987 wallets) shows `avg_win_rate = 0.993` — apparently the most accurate traders in the dataset. This is not because they are the most informed. It is because win_rate is computed only from resolved markets, and opportunistic wallets tend to be concentrated in a single resolved market where they bet YES (the only winning side for all three). A wallet flagged on 10 YES spikes in `us-strikes-iran-feb28` and nothing else has win_rate = 1.0 by our formula, regardless of whether they were informed or just lucky.

The serial_insider cluster's lower win_rate (0.845) is actually a sign of broader market exposure — these wallets appear in more spike windows across more markets, including some NO spikes and active-market spikes where win_rate is zero by definition.

---

## 4. 455 Wallets in Active Markets Are Flagged as High-Risk — These Are the Forward Validation Set

The classifier assigned `label_probability ≥ 0.8` to 455 wallets that were active in the three unresolved markets. These are the forward validation predictions: after `us-forces-iran-mar31`, `us-iran-ceasefire-jun30`, and `china-invades-taiwan-2026` resolve, we check whether these wallets were on the winning side. Only 8 wallets scored in the medium-risk range (0.5–0.8), and 5,035 scored below 0.5. The binary separation is stark — this model does not produce many uncertain predictions, a direct consequence of the heuristic label leakage.

---

## 5. The Top Forward-Validation Wallets Have win_rate = 1.0 Across Multiple Markets

The highest-probability active-market wallets include addresses like `0xbc5b70...` and `0xd5beae...` with `label_probability ≈ 0.999`, win_rate = 1.0, and 2–3 markets traded. These wallets have not missed a single correct-side bet across every resolved market they participated in. Their perfect track record through all past resolutions, combined with active positions in the unresolved markets, makes them the strongest candidates to watch post-resolution.

---

## 6. Label-0 Wallets With High Insider Probability Are the Real Hidden Suspects

The label-0 wallet with the highest insider probability is `0xb5b539...` at `label_probability = 0.6512`. It has `win_rate = 0.7143` — above the 0.65 threshold — but was labelled 0 because `prescience_score` is just below 0.7. A single additional bet placed before a news mention would flip its label.

Several label-0 wallets scored above 0.5: three have win_rate = 1.0 (correct every single time in resolved markets) but miss on the prescience threshold. These are wallets the heuristic rule missed — the model correctly identifies them as borderline but the hard threshold sent them to label 0. In a more careful analysis, wallets with label_probability > 0.5 and label = 0 deserve manual review.

---

## 7. The RF Model Separates Labels Almost Perfectly — Which Is the Problem

Average `label_probability` for label-1 wallets: 0.971. For label-0: 0.008. The model produces a near-bimodal distribution — most wallets are either very confidently insider or very confidently not. This is expected when the training labels are derived from the features themselves, but it has a practical implication: the classifier's probabilities are not well-calibrated. A wallet scoring 0.97 does not necessarily have a 97% chance of being a genuine insider — it has a 97% chance of satisfying the heuristic rule. These are different things.

For the final report, it is worth framing this as: the RF is a feature-weighting exercise, not a fully independent classifier. Its value is showing that `win_rate` and `avg_hours_before_spike` are the dominant discriminators — not that any specific probability value means a wallet is definitely an insider.

---

## 8. Feature Importance Will Show win_rate Dominates — This Is Not a Surprise

Given how the labels are constructed, `win_rate` will rank first or second in the Random Forest's Gini importance. The more interesting question is which features rank third and fourth — those are the behavioral signals that add predictive power *beyond* the labelling rule. Based on what we know from the data, the likely ranking below win_rate is:

1. `win_rate` — defines most of the label
2. `prescience_score` — the other half of the label definition
3. `avg_bet_size_usd` — high-stakes wallets are more suspicious
4. `avg_hours_before_spike` — earlier bettors are more suspicious
5. `num_markets_traded` — multi-market activity is a strong behavioural signal

Items 3–5 are the genuine behavioral features. If the importances show a steep drop-off after items 1–2, it means the classifier adds little beyond the threshold rule. If items 3–5 have substantial importance, it means betting size, timing, and market breadth carry real information.

---

## 9. K-Means Was Asked to Cluster Insiders but the Insiders Are Mostly Homogeneous

The `opportunistic` cluster has 1,987 wallets — 80% of all label-1 wallets. The `serial_insider` cluster has only 56 (2.2%) and `high_stakes` has 444 (17.8%). This lopsided distribution suggests the insider population is not naturally organised into three distinct archetypes. Most insider-labelled wallets look similar: moderate bet size, single market, win_rate above 0.65.

The small `serial_insider` cluster is genuinely distinct — its members stand out on bet size and multi-market reach. The `high_stakes` cluster is a gradient between serial and opportunistic. If the silhouette score is low (< 0.3), this confirms that the insider group lacks strong sub-structure. The K-Means result is useful for characterising the most unusual wallets (the 56 serial insiders) even if the cluster boundaries are not sharp.

---

## 10. Q: Does This Pipeline Actually Prove Anyone Committed Insider Trading?

No. The pipeline identifies wallets whose trading behaviour is statistically consistent with having non-public information — large bets placed early, correct across multiple markets, before news appeared. That is a necessary but not sufficient condition for insider trading.

What the pipeline cannot determine: whether the wallet owner had access to classified or non-public information, whether the trades were the result of sophisticated public-information analysis (e.g., expert reading of geopolitical signals), or whether the pattern is coincidental. The wallet `0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e` places $116K per spike across 6 markets with 23-hour advance timing. That is an extraordinary pattern. But "extraordinary" is not the same as "criminal." The purpose of this project is detection and flagging — what happens after that flag requires legal investigation, subpoenas, and on-chain forensics that are beyond the scope of a data pipeline.
