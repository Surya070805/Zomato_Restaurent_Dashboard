-- Databricks SQL. Run after sql/02_gold_star_schema.sql.
-- Adds the transparent opportunity screening score to mart_market_opportunity so the
-- Databricks Gold layer reaches parity with the local build in src/build_local_gold.py.
--
-- Score = 40% demand proxy + 25% quality + 25% whitespace + 10% service fit
-- Only segments with at least 5 restaurants are scored, so a segment is never ranked
-- on a single data point.
--
-- Note: this uses PERCENT_RANK(), which is (rank - 1) / (n - 1). The local pandas build
-- uses rank(pct=True), which is rank / n. The two conventions place segments in almost
-- the same order but the scores are comparable rather than bit-identical. Pick one
-- implementation as the system of record and use it everywhere.

CREATE OR REPLACE TABLE main.zomato.mart_market_opportunity AS
WITH eligible AS (
  SELECT
    location_name,
    cuisine_name,
    price_band,
    restaurant_count,
    average_rating,
    average_cost_for_two,
    average_votes_per_restaurant,
    online_order_rate_pct,
    table_booking_rate_pct,
    trusted_high_rated_share_pct,
    PERCENT_RANK() OVER (ORDER BY average_votes_per_restaurant) AS demand_proxy_score,
    PERCENT_RANK() OVER (ORDER BY average_rating) AS quality_score,
    1 - PERCENT_RANK() OVER (ORDER BY restaurant_count) AS whitespace_score,
    PERCENT_RANK() OVER (ORDER BY online_order_rate_pct) AS service_fit_score
  FROM main.zomato.mart_market_opportunity
  WHERE restaurant_count >= 5
),
scored AS (
  SELECT
    *,
    ROUND(
      100 * (0.40 * demand_proxy_score
           + 0.25 * quality_score
           + 0.25 * whitespace_score
           + 0.10 * service_fit_score),
      1
    ) AS opportunity_score
  FROM eligible
)
SELECT
  base.location_name,
  base.cuisine_name,
  base.price_band,
  base.restaurant_count,
  base.average_rating,
  base.average_cost_for_two,
  base.average_votes_per_restaurant,
  base.online_order_rate_pct,
  base.table_booking_rate_pct,
  base.trusted_high_rated_share_pct,
  scored.opportunity_score,
  CASE
    WHEN scored.opportunity_score >= 85 THEN 'Shortlist'
    WHEN scored.opportunity_score >= 70 THEN 'High priority'
    WHEN scored.opportunity_score >= 50 THEN 'Promising'
    WHEN scored.opportunity_score IS NOT NULL THEN 'Explore'
    ELSE NULL
  END AS opportunity_tier
FROM main.zomato.mart_market_opportunity base
LEFT JOIN scored
  ON  base.location_name = scored.location_name
  AND base.cuisine_name  = scored.cuisine_name
  AND base.price_band    = scored.price_band
ORDER BY scored.opportunity_score DESC NULLS LAST;
