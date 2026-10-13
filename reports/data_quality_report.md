# Zomato Dataset Quality Report

## Scope

The source is a historical Zomato restaurant-listing snapshot. It has no date field, so it cannot support time-series growth or demand-forecasting claims.

## Dataset And Grain

- Rows read: **41,418**
- Columns: **19**
- Raw grain: one restaurant listing record, not necessarily one unique restaurant. Listing category and Zomato URL context can create repeat appearances.
- Distinct canonical restaurant URLs: **9,431**
- Rows with a repeated canonical URL: **39,953** (96.46%)

## High-Signal Checks

- Exact duplicate rows: **0** (0.0%)
- Ratings outside 1.0-5.0: **0**
- Costs less than or equal to zero: **0**
- Negative votes: **0**
- Unexpected online-order values: **0**
- Unexpected table-booking values: **0**

## Missingness

| Field | Missing rows | Missing rate |
| --- | ---: | ---: |
| dish_liked | 18,091 | 43.68% |
| phone | 578 | 1.4% |
| rest_type | 147 | 0.35% |
| cuisines | 8 | 0.02% |
| url | 0 | 0.0% |
| address | 0 | 0.0% |
| name | 0 | 0.0% |
| online_order | 0 | 0.0% |
| book_table | 0 | 0.0% |
| rate | 0 | 0.0% |
| votes | 0 | 0.0% |
| location | 0 | 0.0% |
| approx_cost(for two people) | 0 | 0.0% |
| reviews_list | 0 | 0.0% |
| menu_item | 0 | 0.0% |
| listed_in(type) | 0 | 0.0% |
| listed_in(city) | 0 | 0.0% |
| rate_clean | 0 | 0.0% |
| cost_clean | 0 | 0.0% |

## Numeric Distribution

| Field | Valid rows | Min | Median | Mean | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| rate_clean | 41,418 | 1.8 | 3.7 | 3.7 | 4.9 |
| cost_clean | 41,418 | 40.0 | 500.0 | 603.27 | 6000.0 |
| votes | 41,418 | 0.0 | 73.0 | 351.73 | 16832.0 |

## Decision For The Pipeline

1. Keep the raw listing table for listing-level analysis.
2. Create a canonical restaurant key from the URL without its query string for distinct restaurant counts and ML train/test grouping.
3. Do not drop every row with a null. Apply field-specific rules: ratings are required for rating analysis, while missing dish and review text should not remove a restaurant from market analysis.
4. Use a cuisine bridge table because one restaurant can serve multiple cuisines.
5. Treat votes as an engagement proxy and observed ratings as platform snapshot outcomes, not demand, revenue, or causal performance measures.

The machine-readable version of this report is `reports/data_quality_summary.json`.
