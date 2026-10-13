-- Databricks SQL. Run after src/01_silver_transform.py creates
-- main.zomato.silver_zomato_listings. Change the catalog/schema if needed.

CREATE OR REPLACE TABLE main.zomato.dim_restaurant AS
SELECT
  restaurant_key,
  min(canonical_url) AS canonical_url,
  min(name) AS restaurant_name,
  min(address) AS restaurant_address
FROM main.zomato.silver_zomato_listings
GROUP BY restaurant_key;

CREATE OR REPLACE TABLE main.zomato.dim_location AS
SELECT
  sha2(location_name, 256) AS location_key,
  location_name
FROM main.zomato.silver_zomato_listings
GROUP BY location_name;

CREATE OR REPLACE TABLE main.zomato.dim_restaurant_type AS
SELECT
  sha2(coalesce(restaurant_type_name, 'Unknown'), 256) AS restaurant_type_key,
  coalesce(restaurant_type_name, 'Unknown') AS restaurant_type_name
FROM main.zomato.silver_zomato_listings
GROUP BY coalesce(restaurant_type_name, 'Unknown');

CREATE OR REPLACE TABLE main.zomato.dim_price_band AS
SELECT * FROM VALUES
  ('Budget', 1),
  ('Mid-range', 2),
  ('Premium', 3)
AS price_bands(price_band, price_band_sort);

CREATE OR REPLACE TABLE main.zomato.dim_listing_type AS
SELECT
  sha2(concat_ws('||', listing_type_name, listing_city_name), 256) AS listing_type_key,
  listing_type_name,
  listing_city_name
FROM main.zomato.silver_zomato_listings
GROUP BY listing_type_name, listing_city_name;

CREATE OR REPLACE TABLE main.zomato.dim_cuisine AS
SELECT
  sha2(cuisine_name, 256) AS cuisine_key,
  cuisine_name
FROM (
  SELECT DISTINCT initcap(trim(cuisine)) AS cuisine_name
  FROM main.zomato.silver_zomato_listings
  LATERAL VIEW explode(split(cuisines, ',')) cuisine_values AS cuisine
)
WHERE cuisine_name IS NOT NULL AND cuisine_name <> '';

CREATE OR REPLACE TABLE main.zomato.bridge_restaurant_cuisine AS
SELECT DISTINCT
  listing.restaurant_key,
  sha2(initcap(trim(cuisine)), 256) AS cuisine_key
FROM main.zomato.silver_zomato_listings listing
LATERAL VIEW explode(split(listing.cuisines, ',')) cuisine_values AS cuisine
WHERE trim(cuisine) <> '';

-- Grain: one canonical restaurant, locality, listing type, and source city grouping.
-- The measures are stable across duplicate listing appearances; max avoids counting
-- the same restaurant repeatedly while retaining the observed snapshot values.
CREATE OR REPLACE TABLE main.zomato.fact_restaurant_listing AS
SELECT
  restaurant_key,
  sha2(location_name, 256) AS location_key,
  sha2(coalesce(restaurant_type_name, 'Unknown'), 256) AS restaurant_type_key,
  sha2(concat_ws('||', listing_type_name, listing_city_name), 256) AS listing_type_key,
  price_band,
  max(rate_value) AS rating,
  max(vote_count) AS vote_count,
  max(cost_for_two) AS cost_for_two,
  max(CAST(online_order_available AS INT)) = 1 AS online_order_available,
  max(CAST(table_booking_available AS INT)) = 1 AS table_booking_available,
  max(CAST(is_high_rated AS INT)) = 1 AS is_high_rated
FROM main.zomato.silver_zomato_listings
GROUP BY restaurant_key, location_name, restaurant_type_name, listing_type_name, listing_city_name, price_band;

CREATE OR REPLACE TABLE main.zomato.mart_market_opportunity AS
SELECT
  location.location_name,
  cuisine.cuisine_name,
  fact.price_band,
  count(DISTINCT fact.restaurant_key) AS restaurant_count,
  round(avg(fact.rating), 2) AS average_rating,
  round(avg(fact.cost_for_two), 2) AS average_cost_for_two,
  round(avg(fact.vote_count), 2) AS average_votes_per_restaurant,
  round(avg(CAST(fact.online_order_available AS INT)) * 100, 2) AS online_order_rate_pct,
  round(avg(CAST(fact.table_booking_available AS INT)) * 100, 2) AS table_booking_rate_pct,
  round(avg(CAST(fact.is_high_rated AS INT)) * 100, 2) AS trusted_high_rated_share_pct
FROM main.zomato.fact_restaurant_listing fact
JOIN main.zomato.dim_location location ON fact.location_key = location.location_key
JOIN main.zomato.bridge_restaurant_cuisine bridge ON fact.restaurant_key = bridge.restaurant_key
JOIN main.zomato.dim_cuisine cuisine ON bridge.cuisine_key = cuisine.cuisine_key
GROUP BY location.location_name, cuisine.cuisine_name, fact.price_band;
