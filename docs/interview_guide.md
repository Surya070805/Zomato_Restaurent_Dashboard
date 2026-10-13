# Interview and Portfolio Guide

How to present this project honestly and strongly for Data Analyst, Data Scientist and ML
internship/full-time roles. Everything here is supported by something in the repository — if you
cannot point at the artifact, do not claim it.

---

## 1. Your 60-second pitch

> "I built a restaurant market intelligence platform on a Zomato Bangalore snapshot. The raw file
> had 41,418 listing rows, but only 9,431 unique restaurants, because a restaurant can appear under
> several listing categories. If you count rows, every market metric is wrong — so the first thing I
> built was a data-quality audit and an identity key.
>
> From there I built a Bronze/Silver/Gold pipeline in PySpark and SQL that produces a star schema
> with a cuisine bridge table, then a Power BI report with five decision pages: market overview,
> locality intelligence, cuisine and pricing, service impact, and an expansion scenario explorer.
> On top of that I trained a leakage-aware classifier for high observed ratings with a grouped
> split, compared logistic regression against random forest, and selected on PR-AUC rather than
> accuracy.
>
> The part I'd emphasise is the judgement calls: I excluded votes and review text from the model
> because they leak the outcome, I labelled votes as an engagement proxy rather than demand, and I
> framed the expansion score as a transparent screening heuristic rather than an AI recommendation."

## 2. Five numbers to know cold

| Number | Why it matters |
| --- | --- |
| 41,418 listing rows → 9,431 restaurants | The duplication problem that drives the whole design |
| 22.34% high-rated share | The target base rate; explains why PR-AUC, not accuracy |
| PR-AUC 0.6753 / ROC-AUC 0.8324 | Your model's headline result |
| 4,878 segments, 1,207 scored | The expansion screen's coverage and its own limitation |
| 71.6% of restaurants serve one of five cuisines | Proves the market is concentrated, not fragmented |

## 3. Resume bullets

Pick the set that matches the role. Do not use all of them.

**Data Analyst version**

- Built an end-to-end restaurant market intelligence platform on a 41k-row Zomato Bangalore
  snapshot; diagnosed a 4.4:1 listing-to-restaurant duplication issue and designed a canonical
  restaurant key that corrected all downstream counts.
- Modelled a star schema (restaurant, location, cuisine bridge, restaurant type, price band,
  listing type) in SQL/PySpark, replacing a flat table and an ad-hoc aggregate in the original
  report.
- Delivered a five-page Power BI decision report covering locality performance, cuisine-price
  positioning, service adoption and expansion screening, with a documented DAX KPI layer.
- Translated analysis into a recommendation brief ranking 1,207 locality-cuisine-price segments,
  explicitly labelled as validation candidates with stated limitations.

**Data Scientist / ML version**

- Engineered a leakage-aware high-rating classifier on 9,431 restaurants using a grouped train/test
  split by restaurant key; excluded votes and review text because they encode or post-date the
  outcome.
- Compared logistic regression and random forest across cross-validated ROC-AUC, PR-AUC, F1,
  precision and recall; selected on PR-AUC (0.6753) given a 22% positive base rate, and explained
  the winner with permutation importance.
- Identified that cuisine mix, table-booking capability and price point dominate predictive signal,
  while locality and online ordering add little — reported as association, not causation.
- Tracked all experiments in MLflow with parameters, metrics, model artifacts and feature-importance
  evidence.

**One-line version**

> Built a PySpark/SQL/Power BI restaurant market intelligence platform with a documented star
> schema, a deduplicated restaurant identity model, and a leakage-aware, MLflow-tracked rating
> classifier evaluated on PR-AUC.

## 4. Questions you will get, and how to answer

**"Why is the restaurant count different from the row count?"**
A restaurant can be listed under several categories — Dine-out, Delivery, Buffet — so it appears in
multiple rows with the same URL. I strip the URL query string, hash it into a restaurant key, and
every restaurant-level metric uses `DISTINCTCOUNT`. Only 1,465 of 41,418 rows were not a repeat of
an existing restaurant.

**"Why did you use PR-AUC instead of accuracy?"**
Only 22.34% of restaurants are high-rated. A model that predicts "not high-rated" for everything
would score 77.7% accuracy while being useless. PR-AUC measures performance on the positive class,
which is the class the business actually cares about.

**"Isn't excluding votes and reviews cheating?"**
It is the opposite — including them would be cheating. The target is rating ≥ 4.0 **and** votes ≥ 20,
so votes are part of the label; using them would make the model trivially accurate and worthless.
Review text is written after the rating, so it leaks the outcome. I restricted the model to
pre-outcome attributes a new restaurant could actually decide on: cuisine, price, locality,
restaurant type, and service capability.

**"Why a bridge table for cuisines?"**
Cuisine is multi-valued — one restaurant can serve North Indian, Chinese and Biryani. Joining the
comma-separated string directly to a dimension is wrong and inflates counts. The bridge holds one
row per restaurant-cuisine pair, so a cuisine count is `DISTINCTCOUNT(restaurant_key)` through the
bridge.

**"What does the opportunity score actually do?"**
It is a weighted rank score: 40% demand proxy (average votes per restaurant), 25% quality
(average rating), 25% whitespace (inverse density) and 10% service fit. It is applied only to
segments with at least 5 restaurants so nothing is ranked on one data point. I deliberately chose
transparent weights over a fitted model, because a fitted score would imply a validation the data
cannot support — there is no outcome variable for "a new restaurant succeeded".

**"What is the biggest weakness?"**
One snapshot with no date field. That means I can describe density and association but cannot say
anything about growth, trend or causation. Adding a second period would be my first priority,
because it converts the whole dashboard from descriptive to diagnostic.

**"Why Databricks for 560 MB?"**
It is not about volume, and I say so in the README. It is about the engineering contract: typed
ingestion, Delta tables, a Bronze/Silver/Gold boundary, SQL marts and MLflow tracking in one place.
For this data size pandas would be faster to run; the pipeline is a demonstration of the pattern.

**"What would you do differently next?"**
Add a time dimension, add latitude/longitude for real catchment analysis, replace the votes-based
demand proxy with actual order volume, and use the unused `menu_item` field for dish-level pricing.

## 5. What not to claim

Do not say any of these — none is supported by the data, and a probing interviewer will find out:

- "Predicts restaurant success" — it predicts an observed platform rating band.
- "Forecasts demand" or "time-series analysis" — there is no time field.
- "Customer segmentation" — there is no customer-level data.
- "Increased revenue by X%" — there is no revenue data.
- "AI-powered recommendation engine" — the score is a weighted ranking heuristic.
- "Handled big data at scale" — 560 MB is not big data. Say "PySpark pipeline" instead.

## 6. Five-minute demo script

1. **The problem (30s).** Open the quality report. Show 41,418 → 9,431. Explain why this matters.
2. **The model (60s).** Open `docs/data_model.md`, walk the star schema and the bridge table.
3. **The analysis (90s).** Open the notebook. Show the locality quality-vs-density scatter, then the
   price band and service tables. Land on: premium is 16.8% of the market but 54.9% high-rated, and
   table booking splits the data more sharply than anything else.
4. **The model (60s).** Show the ROC/PR figure and the feature importance chart. Give the
   leakage explanation before they ask.
5. **The decision layer (60s).** Open the expansion table. Show one segment in detail and explain
   what the next validation step would be. Finish with the limitations slide.

## 7. Repository tour for a reviewer

Point them at these, in this order:

1. `README.md` — scope, architecture and the explicit "current vs target" honesty
2. `reports/data_quality_report.md` — the finding that shaped everything
3. `docs/data_model.md` — grain, relationships, counting rules
4. `docs/business_recommendations.md` — the decision layer
5. `notebooks/01_market_analysis.ipynb` — executed analysis with charts
6. `docs/powerbi_build_guide.md` — proof the dashboard is reproducible, not hand-built
7. `docs/databricks_runbook.md` — proof the pipeline is reproducible on a real platform
