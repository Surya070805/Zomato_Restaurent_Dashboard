# Business Recommendations

A decision brief for a restaurant expansion team, derived entirely from the Gold tables in this
repository. Every figure quoted here is produced by `src/market_insights.py` (see
`reports/market_insights.md`) or by `src/train_rating_model.py` (see
`reports/rating_model_metrics.json`). Nothing is estimated from outside knowledge.

**Read this first.** The source is one historical Zomato Bangalore snapshot with no date field,
no revenue, no customer-level data and no footfall. Everything below is descriptive and
associative. Locality-level statements describe where restaurants *are*, not where demand *will*
be. Recommendations are screening candidates for further validation, not investment decisions.

---

## 1. Market summary

| Metric | Value |
| --- | ---: |
| Unique restaurants | 9,431 |
| Localities | 92 |
| Cuisines | 105 |
| Average rating | 3.62 / 5 |
| Median cost for two | ₹400 |
| Median votes | 51 |
| High-rated share (rating ≥ 4.0 and votes ≥ 20) | 22.34% |
| Share offering online ordering | 61.51% |
| Share offering table booking | 9.86% |

The market is wide but shallow at the top: only 22.34% of restaurants clear both the rating and the
engagement bar. 6,753 distinct restaurants (71.6%) serve at least one of five
cuisines — North Indian, Chinese, Fast Food, South Indian, Biryani — so positioning, not category
novelty, is the main differentiator.

## 2. Locality findings

**Saturated, lower-quality localities.** Whitefield (627 restaurants), BTM (535), HSR (524),
Marathahalli (510) and Electronic City (458) carry the highest restaurant density. Several combine
high density with a below-market high-rated share — Electronic City at 10.26% and BTM at 12.90%
against a 22.34% market baseline. High volume alone is not evidence of a healthy market.

**Quality-dense pockets.** Lavelle Road (4.07 average rating, 68.63% high-rated across 51
restaurants), Koramangala 5th Block (3.91, 50.62% across 241) and Church Street (3.89, 58.18% across
55) pair strong ratings with strong engagement. Koramangala 5th Block and Church Street average 732
and 877 votes respectively, against a market median of 51: these are busy, high-quality markets
rather than thin niches.

**Reading it correctly.** A locality can be dense and low-rated (many players, weak signals) or
sparse and high-rated (few players, strong signals). These are different commercial situations and
the dashboard keeps them separate rather than collapsing them into one "best locality" score.

## 3. Cuisine findings

**Crowded core.** North Indian (3,940 restaurants), Chinese (2,915), Fast Food (1,672),
South Indian (1,670) and Biryani (1,317) dominate by volume, and all five sit at or below the
market's high-rated share.

**Underserved premium niches.** The highest-rated cuisines with meaningful sample sizes are
Japanese (4.21 from 45 restaurants), Mediterranean (4.20 from 87, averaging 1,593 votes),
European (4.17 from 103), Asian (4.07 from 197) and Steak (4.04 from 73). These combine high
observed quality with high engagement while remaining small in count — the shape of a category
where quality supply is scarce relative to demonstrated interest.

**What this does not say.** High ratings in a small category can reflect selection (only
well-capitalised operators enter) rather than proven unmet demand. Treat as a hypothesis.

## 4. Pricing findings

| Price band | Restaurants | Share | Average rating | High-rated share | Table booking |
| --- | ---: | ---: | ---: | ---: | ---: |
| Budget (< ₹400) | 3,624 | 38.43% | 3.54 | 11.51% | 0.22% |
| Mid-range (₹400–799) | 4,224 | 44.79% | 3.58 | 19.44% | 3.22% |
| Premium (₹800+) | 1,583 | 16.79% | 3.93 | 54.90% | 49.65% |

Premium restaurants are roughly five times more likely to be high-rated than budget restaurants
(54.90% vs 11.51%) and carry far more engagement. But premium is only 16.79% of the market, and
the rank correlation between cost and rating is weak-to-moderate (Spearman 0.28). Price band is an
*ordering* signal, not a quality guarantee, and it is entangled with table booking, which is far
more common in this band.

Remember the target definition: a high-rated restaurant needs votes ≥ 20 as well as rating ≥ 4.0.
Premium restaurants accumulate votes faster, so part of this gap is engagement mechanics, not
service quality.

## 5. Service findings

| Service combination | Restaurants | Average rating | High-rated share | Average votes |
| --- | ---: | ---: | ---: | ---: |
| No online + Booking | 442 | 4.15 | 77.60% | 1,009 |
| Online + Booking | 488 | 4.08 | 71.11% | 1,009 |
| Online + No booking | 5,313 | 3.61 | 18.61% | 171 |
| No online + No booking | 3,188 | 3.51 | 13.43% | 127 |

Restaurants that accept table bookings average markedly higher ratings and roughly six times the
votes. This is the strongest single split in the data and the same signal the model picks up
(table booking is the second most important feature by permutation importance).

**Interpretation guardrail.** Table booking is almost certainly a proxy for the segment a
restaurant already occupies — full-service, higher-ticket, dine-in venues. Nothing here shows that
adding a booking feature would raise a rating. Report it as a segment marker, never as a lever.

Rank correlations (Spearman): rating vs votes 0.63, cost vs votes 0.45, rating vs cost 0.28.
Engagement tracks quality far more closely than price does.

## 6. What associates with a high observed rating

Two models were trained on 9,431 restaurants with a grouped 75/25 split by restaurant key, using
only pre-outcome features (cost, locality, restaurant type, online ordering, table booking,
cuisine). Votes and review text were deliberately excluded because they form part of the target
rule or leak post-outcome information.

| Model | ROC-AUC | PR-AUC | F1 | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Logistic regression | 0.8207 | 0.6493 | 0.5657 | 0.4890 | 0.6711 |
| **Random forest (selected)** | **0.8324** | **0.6753** | **0.6019** | 0.5898 | 0.6144 |

PR-AUC is the selection metric because only ~22% of restaurants are positive; accuracy alone would
be misleading. Permutation importance (PR-AUC decrease): cuisine mix 0.156, table booking 0.144,
cost for two 0.069, restaurant type 0.029, locality 0.014, online ordering 0.005.

Reading: cuisine mix, booking capability and price point carry most of the signal; locality adds
little once the other features are present, and online ordering adds almost nothing. A PR-AUC of
0.675 means the model is a usable *screening* aid, not a decision authority.

## 7. Recommended scenarios to validate

Ranked by the opportunity score (`40% demand proxy + 25% quality + 25% whitespace + 10% service
fit`, applied only to segments with at least 5 restaurants). 1,207 of 4,878 segments were scored:
27 Shortlist, 200 High priority, 346 Promising, 634 Explore.

| # | Scenario | Locality / cuisine / price band | Segment size | Segment avg rating | Avg votes |
| --- | --- | --- | ---: | ---: | ---: |
| 1 | Premium Chinese, central business district | Church Street / Chinese / Premium | 5 | 4.11 | 3,143 |
| 2 | Premium burger, tech corridor | Whitefield / Burger / Premium | 5 | 4.35 | 958 |
| 3 | Premium Asian, south-east growth belt | Sarjapur Road / Asian / Premium | 5 | 4.31 | 1,560 |
| 4 | Premium pizza, southern corridor | Bannerghatta Road / Pizza / Premium | 5 | 4.03 | 1,428 |
| 5 | Premium finger food / small plates | Sarjapur Road / Finger Food / Premium | 5 | 4.44 | 4,099 |

Localities contributing most Shortlist and High-priority segments: Indiranagar (28),
Koramangala 5th Block (19), Whitefield (15), Sarjapur Road (13), HSR (13).

**How to use these.** Each is a segment where the existing handful of players is well-rated and
well-engaged while the field is thin. The next step is not "open a restaurant" — it is validation:
site visit, competitor audited pricing, rent and licence check, and a demand test. The score
deliberately includes a whitespace term, which means a thin segment can score highly even when thin
because demand is weak; that ambiguity is the point of a screening score.

## 8. What would strengthen this analysis

Ordered by value per unit of effort:

1. **A second snapshot.** Two periods would convert descriptive density into actual growth and let
   the dashboard answer "which localities are growing" instead of "which are large".
2. **Latitude/longitude.** Enables true catchment analysis instead of locality-name grouping.
3. **External demand data.** Footfall, delivery-order volume or rent indices would let the demand
   proxy be replaced by something measured.
4. **Price parsing at dish level.** The `menu_item` field is unused; dish pricing would separate
   "expensive" from "premium positioned".
5. **Review-text themes.** The `reviews_list` field is excluded from the model for leakage reasons
   but is a legitimate separate voice-of-customer analysis.

## 9. Limitations to state out loud

- One snapshot, no time dimension: no growth, trend or forecast claims.
- Ratings are platform outcomes subject to selection and volume effects, not satisfaction measures.
- Votes are an engagement proxy and are heavily skewed (median 51, maximum 16,832).
- Cuisine is multi-valued, so cuisine-level counts sum to more than the restaurant total.
- Locality is a Zomato grouping label; its boundary is not defined.
- The opportunity score is a weighted heuristic with assumed weights, not a fitted or validated
  model.
