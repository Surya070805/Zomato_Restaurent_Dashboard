# Power BI Build Guide

A step-by-step plan to rebuild the dashboard as a decision-support report on top of the
Gold tables in `data/gold/`. Follow it top to bottom; every field name below exists in the
generated CSVs.

After the Databricks pipeline is running, point Power BI at the Delta/parquet tables instead of
the CSVs. The column names are identical, so nothing else in this guide changes.

---

## 1. Prerequisites

Files to import (all in `data/gold/`):

| File | Rows | Role |
| --- | ---: | --- |
| `dim_restaurant.csv` | 9,431 | Restaurant dimension |
| `dim_location.csv` | 92 | Locality dimension |
| `dim_restaurant_type.csv` | 88 | Restaurant-type dimension |
| `dim_price_band.csv` | 3 | Price-band dimension + sort order |
| `dim_listing_type.csv` | small | Listing category + listing city |
| `dim_cuisine.csv` | 105 | Cuisine dimension |
| `bridge_restaurant_cuisine.csv` | ~20k | Restaurant ↔ cuisine bridge |
| `fact_restaurant_listing.csv` | 41,357 | Fact: rating, votes, cost, service flags |
| `mart_market_opportunity.csv` | 4,878 | Pre-aggregated expansion screen |

**Why the fact table is bigger than the restaurant count:** one restaurant listed under three
listing categories produces three fact rows with the same restaurant key. That is intentional —
it preserves listing context — but it means **you must never use `COUNTROWS(fact)` as a
restaurant count.** Use `Restaurant Count = DISTINCTCOUNT(restaurant_key)`.

## 2. Import the data

For each CSV: **Home → Get Data → Text/CSV →** select file **→ Transform Data**.

In Power Query, for every table:

1. Confirm the header row is promoted and the column types are correct.
   - `restaurant_key`, `*_key`: Text
   - `rating`, `cost_for_two`, `vote_count`: Decimal Number / Whole Number
   - `online_order_available`, `table_booking_available`, `is_high_rated`: True/False
   - `is_high_rated` should read as True/False, **not** as text.
2. Remove the auto-generated "Changed Type" step if Power BI guessed a type wrong, and set the
   type manually so the model is stable on refresh.
3. **Close & Apply.**

Tip: to refresh all tables at once later, place the CSVs in one folder and use
**Get Data → Folder**, then expand each file. Keep the individual-file approach if you want the
simplest possible refresh story.

## 3. Build the model

Create these relationships (all **one-to-many, single filter direction**, dimension → fact):

| From (1) | To (*) | Column |
| --- | --- | --- |
| `dim_restaurant` | `fact_restaurant_listing` | `restaurant_key` |
| `dim_location` | `fact_restaurant_listing` | `location_key` |
| `dim_restaurant_type` | `fact_restaurant_listing` | `restaurant_type_key` |
| `dim_listing_type` | `fact_restaurant_listing` | `listing_type_key` |
| `dim_price_band` | `fact_restaurant_listing` | `price_band` |

Optional, for a locality slicer on the Expansion page:

| From (1) | To (*) | Column |
| --- | --- | --- |
| `dim_location` | `mart_market_opportunity` | `location_name` |

Do **not** relate `mart_market_opportunity` to the fact table. It is already aggregated; joining it
to the fact table would double-count and create ambiguous filter paths.

Model hygiene:

1. In `dim_price_band`, select `price_band` → **Column tools → Sort by column → `price_band_sort`**
   so price bands display Budget → Mid-range → Premium.
2. Hide all `*_key` columns and `restaurant_key` from report view.
3. Hide `canonical_url`, `restaurant_address`, `price_band_sort`.
4. Create a measure table: **Home → Enter Data**, name it `_Measures`, then move every measure
   into it. This keeps the field list clean.
5. Mark `dim_price_band` and `dim_location` as the two tables report authors may slice by; the fact
   table is facts only.

Optional advanced step (cuisine slicer on the fact table): create a many-to-many relationship
`dim_cuisine[cuisine_key] → bridge_restaurant_cuisine[cuisine_key]` (1:*) and
`bridge_restaurant_cuisine[restaurant_key] → fact_restaurant_listing[restaurant_key]` (M:N, single
direction). Only do this after the report works, because multi-cuisine restaurants make
cuisine-level counts sum to more than the restaurant total. Cuisine analysis is easier and safer on
the pre-aggregated `mart_market_opportunity` table.

## 4. Add the measures

Paste the contents of `powerbi/measures.dax` into a new measure table, or add them one at a time
with **New measure**. The measures to build first:

| Measure | What it answers |
| --- | --- |
| `Restaurant Count` | How many restaurants are in scope |
| `Restaurant Rating` | Average observed rating |
| `Median Cost for Two` | Typical price point |
| `Average Votes per Restaurant` | Engagement proxy |
| `Online Order Rate` | Share offering delivery |
| `Table Booking Rate` | Share offering reservations |
| `Trusted High Rated Share` | Share rated ≥ 4.0 with ≥ 20 votes |
| `Locality Attractiveness` | Composite locality proxy |
| `Shortlisted Segments` | Segments flagged for validation |

Sanity check: with no filters, `[Restaurant Count]` must equal **9,431** and
`QA Ratings Out Of Range` must be **0**. If the count is 41,357 you used `COUNTROWS` by mistake.

## 5. Report pages

Build five pages. Each one answers a decision, not a chart type.

### Page 1 — Executive Overview

Question: *what does the Bangalore restaurant market look like?*

- Five KPI cards across the top: `Restaurant Count`, `Restaurant Rating`, `Median Cost for Two`,
  `Online Order Rate`, `Trusted High Rated Share`.
- Bar chart: `dim_location[location_name]` by `Restaurant Count`, Top 15, sorted descending.
- Donut: `dim_price_band[price_band]` by `Restaurant Count`.
- Scatter: X = `Restaurant Count`, Y = `Restaurant Rating`, size = `Average Votes per Restaurant`,
  legend = `dim_location[location_name]`. Filter to localities with at least 50 restaurants so the
  visual is not dominated by one-restaurant localities.
- Text box with the scope caveat: one historical snapshot, no time dimension, associations only.

### Page 2 — Locality Intelligence

Question: *which localities combine quality, engagement and manageable density?*

- Decomposition tree or matrix: rows = `dim_location[location_name]`, values =
  `Restaurant Count`, `Restaurant Rating`, `Average Votes per Restaurant`,
  `Trusted High Rated Share`, `Locality Attractiveness`.
- Conditional formatting (data bars on `Restaurant Count`, colour scale on `Restaurant Rating`).
- Bar chart of the Top 10 localities by `Locality Attractiveness`.
- Drill-through target: right-click a locality → locality detail page.

Do not add a map visual. The dataset has locality names but no latitude/longitude, so a filled map
would place points incorrectly and is worse than a bar chart.

### Page 3 — Cuisine and Pricing

Question: *which cuisine-price combinations are crowded, premium or underserved?*

Source: `mart_market_opportunity` (pre-aggregated).

- Treemap: `cuisine_name` by `SUM(restaurant_count)`.
- Bar chart: Top 15 `cuisine_name` by `AVERAGE(average_rating)`, filtered to
  `SUM(restaurant_count) >= 30` so small cuisines do not dominate.
- Matrix heatmap: rows = `price_band`, columns = `cuisine_name` (Top 10 by count),
  values = `AVERAGE(average_rating)` with a colour scale.
- Scatter: X = `SUM(restaurant_count)` (competition), Y = `AVERAGE(average_rating)` (quality),
  size = `AVERAGE(average_votes_per_restaurant)` (engagement), details = `cuisine_name`.

### Page 4 — Service Impact

Question: *how do online ordering and table booking relate to observed ratings?*

- Create a calculated column in `fact_restaurant_listing`:

  ```dax
  Service Combination =
  IF ( fact_restaurant_listing[online_order_available], "Online", "No online" )
      & " + "
      & IF ( fact_restaurant_listing[table_booking_available], "Booking", "No booking" )
  ```

  Note: because a restaurant can appear in several fact rows, this column is listing-level. For a
  restaurant-level version, add the same logic as a calculated column in `dim_restaurant` after
  aggregating, or read it from the notebook output. For a portfolio report the listing-level
  version is acceptable as long as the caption says "listing rows".

- Clustered bar: `Service Combination` by `Restaurant Rating`.
- Line or reference line: market average rating, so each bar is read against the baseline.
- Bar: `Service Combination` by `Average Votes per Restaurant`.
- Card: `Online Order Rate`, `Table Booking Rate`.
- A callout box: this is an association in one snapshot, not evidence that adding table booking
  raises a rating.

### Page 5 — Expansion Scenario Explorer

Question: *which locality-cuisine-price scenarios are worth validating first?*

- Slicers: `location_name`, `cuisine_name`, `price_band`, `opportunity_tier`.
- Table (visual-level filters: `opportunity_score` is not blank), sorted descending:
  `location_name`, `cuisine_name`, `price_band`, `restaurant_count`, `average_rating`,
  `average_votes_per_restaurant`, `opportunity_score`, `opportunity_tier`.
- Cards: `Scored Segments`, `Shortlisted Segments`, `Average Opportunity Score`.
- Bar: `opportunity_tier` by segment count.
- Methodology text box:

  > Opportunity score = 40% demand proxy + 25% quality + 25% whitespace + 10% service fit.
  > Only segments with at least 5 restaurants are scored. This is a screening heuristic for
  > further validation, not a validated investment recommendation.

### Extra page — Data Quality and Methodology

- Text boxes stating: source snapshot, grain, 41,418 listing rows → 9,431 restaurants, missing
  `dish_liked`, the excluded fields, and the fact that votes are an engagement proxy.
- Cards: `Listing Rows`, `Restaurant Count`, `Listing Types per Restaurant`, `QA Ratings Out Of Range`.

## 6. Interaction and polish

- **Slicers:** on every page add `dim_price_band[price_band]`, `online_order_available`,
  `table_booking_available` as a collapsible slicer panel; keep them synced across pages
  (**View → Sync slicers**).
- **Drill-through:** create a hidden page `Restaurant Detail` with a table of `restaurant_name`,
  address, rating, votes, cost and service flags, and add drill-through fields
  `dim_location[location_name]` and `dim_restaurant_type[restaurant_type_name]`.
- **Tooltips:** build one custom tooltip page with `Restaurant Count`, `Restaurant Rating` and
  `Average Votes per Restaurant` and attach it to the locality and cuisine visuals.
- **Bookmarks:** add two bookmarks, "Saturated markets" and "Premium opportunities", that set the
  slicers differently, and expose them as buttons on the Overview page.
- **What-if:** add a numeric parameter for the minimum restaurant count (5–50) and drive the
  expansion table filter from it. This gives the report an interactive scenario element without
  changing the underlying data.
- **Theme:** apply a light theme; use one accent colour for quality and one for volume so the two
  can be told apart at a glance.

## 7. Validate before you present

| Check | Expected |
| --- | --- |
| `[Restaurant Count]`, no filters | 9,431 |
| `[Listing Rows]`, no filters | 41,357 |
| `QA Ratings Out Of Range` | 0 |
| `dim_location` rows | 92 |
| `dim_cuisine` rows | 105 |
| `mart_market_opportunity` rows | 4,878 |
| Scored segments | 1,207 |
| Price band order in visuals | Budget, Mid-range, Premium |

## 8. Package it for your portfolio

1. Add a `screenshots/` folder with one PNG per page (use **File → Export → Export current page**
   or a screenshot tool).
2. Export the `.pbix` with the data model included, or publish a sanitized version to Power BI
   Service and capture the share link if your account allows public sharing.
3. Put the screenshots and the page list in the README so a reviewer sees the work without opening
   Power BI.
4. Write down the two or three decisions each page supports, because that is what an interviewer
   will ask about.
