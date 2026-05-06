# Phase 3 — Spike Detection: Top Insights

**CS-GY 6513 Big Data, Spring 2026**
Based on outputs from `analysis/detect.ipynb`

---

## 1. The Largest Spike in the Dataset Is in a Market That Hasn't Resolved Yet

The single highest z-score in the entire dataset is **z = 60.9** — in `us-forces-iran-mar31`, YES side, on March 26. Price jumped from **0.19 → 0.44** in one 5-minute window, backed by $8,521 in volume.

For comparison, here are the resolution-day spikes from the three markets we *know* resolved:

| Market | Z-score at resolution | Price move |
|---|---|---|
| `us-forces-iran-mar31` *(unresolved)* | **60.9** | 0.19 → 0.44 |
| `maduro-out-jan31` | 33.3 | 0.12 → 0.63 |
| `us-strikes-iran-feb28` | 12.87 | 0.24 → 0.78 |
| `khamenei-out-feb28` | 10.92 | 0.10 → 0.31 |

The unresolved market's spike is **nearly 2x larger than the cleanest confirmed resolution** in our dataset. We don't know yet if this was informed trading ahead of a real event or a false alarm — but by the numbers, it is the single most suspicious price movement we found.

---

## 2. For US Strikes Iran, the Biggest "Alarm" Rang 36 Days Before the Event

When we look at `us-strikes-iran-feb28`, the highest z-score spike did **not** happen on resolution day (Feb 28). It happened on **January 22** — 36 days earlier. Price moved from 0.45 → 0.62, z = 17.89, on just $168 in volume.

The actual Feb 28 resolution spike (price 0.24 → 0.78, $74K volume) ranks *second* for that market at z = 12.87.

**What this means:** By the time Feb 28 arrived, the move was arguably expected by the market. The more suspicious bet — small, quiet, and very early — happened over a month earlier. Someone bought at 45 cents when most of the market thought a US strike on Iran was a coin flip at best.

---

## 3. Maduro: The Early Insiders Bet Small. The Late Chasers Bet $152K.

For `maduro-out-jan31`, two spikes happened in the same morning window on January 3:

| Time (UTC) | Price move | Z-score | Volume |
|---|---|---|---|
| 01:15 AM | 0.12 → 0.63 | **33.3** | $17,930 |
| 04:20 AM | 0.375 → 0.902 | 10.35 | **$152,184** |

The first spike — the actual signal — moved price the most and had the highest z-score. But only $18K was traded. Three hours later, after the outcome was becoming clear, a second wave of $152K rushed in. That second wave has 8× the dollar volume but a much lower z-score.

**The contrast:** The *informed* money was small and early. The *big* money arrived late, after confirmation. This is a textbook split between insiders and news-chasing traders — the z-score tells them apart even when raw volume does not.

---

## 4. Khamenei vs. Maduro: Two Very Different "Insider Fingerprints"

Looking at the spike patterns for the two Feb 28 resolved markets side by side:

**Maduro** — nearly flat YES price for weeks, then a single sudden spike on Jan 3. One day, nothing; next day, resolved. The market was caught off guard.

**Khamenei** — multiple YES-side spikes spread across *several hours* on Feb 28 itself, building in steps:

| Time | Price before | Price at spike | Z-score |
|---|---|---|---|
| 04:50 AM | 0.087 | 0.137 | 10.14 |
| 04:55 AM | 0.137 | 0.191 | 7.11 |
| 08:30 AM | 0.104 | 0.312 | 10.92 |
| 08:35 AM | 0.312 | 0.444 | 6.37 |

This looks like *gradual accumulation* — multiple waves of buying throughout the day, each pushing the price higher before the next wave. Maduro was a surprise. Khamenei looks like a slow leak of information across several hours.

---

## 5. Changing the Sensitivity Threshold Barely Changes *Which* Events Get Caught

We tested the spike detector at six different z-score thresholds (2.0 through 5.0):

| Market | z=2.0 | z=3.0 | z=5.0 |
|---|---|---|---|
| `us-strikes-iran-feb28` | 604 | 177 | 25 |
| `maduro-out-jan31` | 69 | 27 | 8 |
| `khamenei-out-feb28` | 201 | 63 | 11 |
| `us-forces-iran-mar31` | 676 | 227 | 43 |

Spike counts drop sharply as the threshold rises — but the *same resolution-day events* appear at every threshold. The Maduro Jan 3 spike (z=33.3) shows up whether you use z=2 or z=5. The key spikes are not borderline cases — they clear the bar by a wide margin.

We also tested changing the rolling window size (5 to 50 buckets) for Maduro specifically:

| Window | Z-score at resolution | Total spikes |
|---|---|---|
| 5 | 99.3 | 25 |
| 20 *(our default)* | 33.3 | 27 |
| 50 | 24.8 | 19 |

The z-score number changes by 4× depending on the window, but the spike count barely moves. **The numbers change; the events don't.** This means our detector is finding real signals, not just statistical artifacts of a particular parameter choice.
