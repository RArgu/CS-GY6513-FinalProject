# Prescience Scoring — Interesting Insights

**CS-GY 6513 Big Data, Spring 2026**  
Based on outputs from `analysis/score.ipynb`

---

## 1. Switching from Events to Eventmentions Fixed the Prescience Score

The first attempt used `gdelt-bq.gdeltv2.events` which provides `SQLDATE` as a date-only integer (YYYYMMDD). Because GDELT covers Iran, Khamenei, and Taiwan in dozens of articles every single day, any bet placed on date D would always find a "next GDELT event" on date D+1 — meaning 99.93% of wallets scored 1.0, making the feature useless.

Switching to `gdelt-bq.gdeltv2.eventmentions` gave article-level timestamps (`MentionTimeDate` = YYYYMMDDHHMMSS, 15-minute crawl precision). Now a bet placed at 10am is correctly compared against a news mention that appeared at 9am the same day — a fundamentally different result. The score's standard deviation went from near-zero to **0.098**, and 410 wallets (3.6%) now have score < 1.0 including 102 confirmed reactors below 0.3.

---

## 2. Prescience Score Distribution Is Still Right-Skewed — and That Makes Sense

After the fix, 10,963 out of 11,373 wallets (96.4%) still have `prescience_score = 1.0`. This is not a bug. GDELT's eventmentions table has dense coverage for these high-profile geopolitical topics — for Iran and Taiwan markets, there is almost always a relevant article crawled within 1–2 hours of any given moment during the collection window. Wallets betting inside a 24-hour look-back window will nearly always find a subsequent article within that window.

The score's value is less in distinguishing most wallets from each other and more in **identifying the 102 confirmed reactors** (score < 0.3) who were consistently betting after news appeared. Those are the cleanest negative examples for Phase 6 ML — wallets we know were reacting to public information, not anticipating it.

---

## 3. The Prime Suspect's avg_hours_before_news Dropped From 12.6h to 1.9h

`0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e` now shows `avg_hours_before_news = 1.9h` with `prescience_score = 0.991`. The old 12.6h figure was an artifact of the date-only comparison. The true picture: this wallet's bets are typically about 2 hours before the next GDELT crawl on the same topic. Given GDELT's 15-minute crawl cadence, being 1.9h ahead of the next crawl means they bet during a ~2-hour gap in coverage — not 12 hours before any news.

This is actually a more damning finding in one sense: the wallet isn't betting days before news breaks. It's betting into brief windows where no new articles have appeared in the last couple of hours. That pattern is consistent with acting on information that hasn't been published yet, but the information gap is shorter than the date-only analysis suggested.

---

## 4. 102 Confirmed Reactors Are the Most Valuable Phase 6 Training Signal

Wallets with `prescience_score < 0.3` were flagged in 2+ spike windows and consistently placed their bets *after* relevant news was already in GDELT. These are not insiders — they are traders who read the news and placed a position. Examples:

- `0xd975bd5c9aa08e9cb5729ff8ac0f5b92f4e2a205`: score = 0.0, avg bet $8,200, 16.3h before spike — this wallet placed both entries after news had appeared, but still 16 hours before the market spike, meaning they were early in market terms but late in information terms
- `0xd7cbd93f27cf90be3e34c6e867b52f21746dea3e`: score = 0.2, win_rate = 1.0 — correctly bet the winning side in every resolved market entry, but always after news broke; a sophisticated news-driven trader, not an insider

These reactors get label = 0 in Phase 6, giving the classifier concrete negative examples rather than relying purely on heuristic cutoffs.

---

## 5. avg_hours_before_Spike Remains the Strongest Feature

Across all 11,373 wallets, `avg_hours_before_spike` (mean 10.34h, std ~6h) discriminates more cleanly than prescience_score. The prime suspect is at 23.13h — essentially always at the maximum of the 24-hour look-back window. The 102 confirmed reactors range from 6–17h before spike. Both groups can have prescience scores near 1.0 (if GDELT happened to have a gap in coverage), but their hours_before_spike profiles are very different.

This matters for Phase 6 feature importance: we expect `avg_hours_before_spike` and `avg_bet_size_usd` to rank higher than `prescience_score` in the Random Forest.

---

## 6. Only 4 Wallets Traded Across All 6 Markets — avg Bet $32K Per Spike

Of 11,373 wallets, only 4 were active (≥$100, ≥2 spikes) in all 6 markets. These 4 are not casual bettors. They have systematic positions in every geopolitical contract on Polymarket simultaneously. Their average bet per spike is $32K, vs $1.1K for the broader population.

The prime suspect alone averages $116K per spike entry with 562 total spike appearances. The next three 6-market wallets have not been individually identified yet but will all receive the highest insider probability from the Phase 6 classifier.

---

## 7. The 22 Five-Market Wallets Show the Clearest Insider Profile

22 wallets traded across exactly 5 markets with avg bet size $2,792. Several have win_rate ≥ 0.84 — correctly betting the winning side in 84%+ of their resolved-market spike windows. At 5 distinct geopolitical contracts with consistent win rates, this cannot be attributed to one lucky read on public information. The strongest candidates: `0x4b7410aef...` (5 markets, win_rate 0.848, $3.9K avg), `0xf1f9a438...` (5 markets, win_rate 0.857, $3.6K avg), and `0x47ab0267...` (5 markets, win_rate 1.0, $1.4K avg over 40 spike entries).

---

## 8. avg_hours_before_news and prescience_score Are Not Redundant

Despite both measuring the relationship between bets and news, the two features capture different things. `prescience_score` is binary per entry (was there any news after the bet at all?). `avg_hours_before_news` is continuous (how many hours until the next article appeared?). A wallet betting into a news gap scores 1.0 on prescience and a low hours_before_news if the gap is short. A wallet betting hours before a major exclusive breaks could score 1.0 with a high hours_before_news.

In practice, the Pearson correlation between the two in our feature set is moderate, not near 1.0, confirming they should both enter the Phase 6 feature vector independently.

---

## 9. Khamenei Market Has the Fewest Mention Timestamps — and the Strongest Edge

The eventmentions query returned far fewer distinct timestamps for `khamenei-out-feb28` than for the Iran or Taiwan markets (sparse GDELT coverage, even at min_articles = 3). This means Khamenei market suspects had longer genuine gaps between news mentions — a bet placed in one of these gaps was further ahead of public information than an equivalent bet in the Iran markets where there is always a new article within minutes.

Wallets with high prescience in the Khamenei market had a harder task than wallets scoring 1.0 in the Iran markets where the dense GDELT coverage makes any bet trivially "before the next mention." Phase 6 could weight Khamenei prescience more heavily, though the Random Forest will likely discover this automatically through feature interactions.

---

## 10. 2,486 Wallets Meet the Dual Heuristic Threshold — win_rate Is the Real Filter

`prescience_score > 0.7 AND win_rate > 0.65` flags 2,486 wallets (21.9%) as potential insiders. Since prescience_score is near-universal at 1.0, the effective filter is `win_rate > 0.65`. Win rate above 0.65 means betting the correct side (YES in all 3 resolved markets) in 65%+ of resolved-market spike windows — above chance in a binary market, but not definitive on its own. Phase 6 adds bet size, timing, and multi-market dimensions to sharpen this into a classifier score rather than a binary threshold.
