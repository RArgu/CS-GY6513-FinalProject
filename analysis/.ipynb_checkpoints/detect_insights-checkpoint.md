# Spike Detection — Interesting Insights

**CS-GY 6513 Big Data, Spring 2026**  
Based on outputs from `analysis/detect.ipynb`

---

## 1. The Biggest Spike in the Dataset Is From an Unresolved Market

The highest z-score in the entire dataset is **z = 60.9** — on `us-forces-iran-mar31`, YES side, March 26, 2026. Price jumped from 0.19 to 0.439 in a single 5-minute window, backed by $8,521 in volume.

This market has not resolved yet. The spike is larger than anything we see at the resolution of the three confirmed markets (Maduro z=33.3, US Strikes z=12.87, Khamenei z=10.92). We do not know yet whether this was informed trading ahead of a real event or a false signal. This is the highest-priority target for Phase 4 bet tracing.

---

## 2. US Strikes Iran: The Biggest Pre-Resolution Spike Is Not on Resolution Day

For `us-strikes-iran-feb28`, the highest z-score spike (z=17.89) landed on **January 22, 2026** — 36 days before the February 28 resolution. Price moved from 0.45 to 0.621 in one 5-minute window.

The actual resolution spike on Feb 28 (z=12.87) ranks second for that market. Someone made an unusually large and accurate bet more than a month early. This is a stronger candidate for insider activity than the resolution-day trading, because by Feb 28 the event was essentially public.

---

## 3. The Maduro Market Resolved a Month Before Its Slug Said It Would

The market is named `maduro-out-jan31` — implying a January 31 resolution date. The actual spike happened on **January 3, 2026**, nearly a month early. The market resolved on a completely different date than the one in its name. This is not unusual for Polymarket (markets resolve when the event happens, not on the nominal date), but it's a useful reminder that market slugs are not always reliable as event timestamps.

---

## 4. Maduro Had Pre-Resolution Buying 2.5 Hours Before the Spike

In the sanity check output, `maduro-out-jan31` YES shows a spike at **Jan 2, 22:40 UTC** (z=6.58, price 0.08→0.14) — approximately 2.5 hours before the dominant resolution spike at Jan 3, 01:15 UTC (z=33.3). At the time of the early spike, the market was pricing YES at only 8%. Someone bet at 8% with $1,931, then two hours later the market confirmed the outcome and price hit 63%. That is the kind of timing that Phase 4 is designed to catch.

---

## 5. The Two Iran Markets Spiked at Nearly the Same Time

`us-forces-iran-mar31` (YES, z=60.9 on March 26) and `us-iran-ceasefire-jun30` (YES, z=15.7 on March 23) both show their largest spikes within three days of each other in late March 2026. These are separate markets on related geopolitical questions.

A single piece of information — say, leaked intelligence about US-Iran negotiations — could rationally cause someone to buy YES on both. If Phase 4 shows the same wallet addresses appearing in both markets in the same week, that is a much stronger insider signal than a single-market bet.

---

## 6. Khamenei's Price Signature Looks Very Different From Maduro's

`maduro-out-jan31`: nearly flat YES price (8–12%) for weeks, then a single sharp spike to 63% on resolution day. The pattern is: nothing, then event.

`khamenei-out-feb28`: gradual YES price climb over multiple days leading into Feb 28, with several z>3 spikes spread across the pre-resolution period. The pattern is: slow accumulation, then confirmation.

These are two different trading signatures. The Maduro pattern suggests the resolution was a surprise. The Khamenei pattern suggests at least some traders had growing conviction before the event — which could be informed accumulation or just the market gradually updating on public news.

---

## 7. 329,373 Trades Collapse to ~5 Trades Per 5-Minute Window on Average

329,373 ticks → 65,985 five-minute buckets. That is roughly 5 trades per bucket across all markets and sides. But this average hides wide variation:

- `us-forces-iran-mar31` alone had 102,963 ticks across roughly 10,000 buckets (YES + NO)
- `maduro-out-jan31` had 8,356 ticks across far fewer buckets

The Maduro market was so thin that many of its buckets contained a single trade. This is why the MIN_STD guard mattered — in a thinly traded market, a single off-market fill could produce a fake z-score of thousands without the guard in place.

---

## 8. The Second-Biggest Maduro Spike Was $152,000 AFTER the Resolution Spike

The top Maduro spike (z=33.3) was at 01:15 UTC on Jan 3 with $17,930 in volume — price went from 0.12 to 0.63. The second spike (z=10.35) was at 04:20 UTC the same day, with **$152,184** in volume — price went from 0.375 to 0.902.

The largest single-bucket dollar volume in the Maduro market came three hours after the initial resolution spike, not before it. This is a different kind of trader — chasing a confirmed move, not anticipating it. Distinguishing between these two types is part of what Phase 5 is designed to do.

---

## 9. Window Size Changes Z-Score More Than It Changes Which Spikes Get Flagged

In Experiment B (Maduro, window sizes 5 to 50), the z-score at resolution ranged from 99.3 (window=5) to 24.8 (window=50) — a 4x difference. But the total spike count for the market only changed from 27 to 19. Changing the window size primarily controls how dramatic the numbers look, not how many events get flagged. For this dataset, window=20 is a good balance — stable enough to not be thrown off by short-term drift, reactive enough to catch the onset of genuine spikes.

---

## 10. China Invades Taiwan Has Been Running Since July 2025

The earliest tick in the dataset for `china-invades-taiwan-2026` is July 24, 2025 — over 9 months before the other markets started collecting. This is a long-horizon, low-probability market. The YES price sat in the 20–30% range for most of that period with the NO side correspondingly high.

This market has 59,793 ticks, more than the two smaller Iran markets combined. But its spikes, when they occur, come from a market that has a well-established baseline — which makes any genuine z>3 event here a more reliable signal than the same z-score in a market that has only been running for a few weeks.

---

## 11. At z=2.0, US Forces Iran Had 676 Flagged Spikes — This Market Is Not Normal

The threshold sensitivity experiment showed that lowering the threshold to z=2.0 produces 604 spikes for `us-strikes-iran-feb28` and 676 for `us-forces-iran-mar31`. For comparison, `maduro-out-jan31` had only 82 at z=2.0.

US Forces Iran is the most actively traded and the most volatile market in our dataset. Its sheer trading volume means that even "normal" fluctuations cross z=2 frequently. At z=3.0, it still has the most spikes of any market (more than twice the resolved markets). This market needs either a higher threshold applied specifically to it, or volume-weighted filtering in Phase 4 to separate the signal from the noise.
