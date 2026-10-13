# Databricks Runbook

Runbook for rebuilding this project on Databricks end to end, so the pipeline is reproducible on a
real platform rather than only as local scripts. Budget about 60–90 minutes the first time.

**Why Databricks for this project.** The dataset is a 560 MB CSV, which is small. PySpark is used
here as a deliberate engineering choice — typed ingestion, a Bronze/Silver/Gold contract, Delta
tables and MLflow tracking — not because the data volume demands a cluster. Say that plainly in an
interview; claiming "big data scale" for a 560 MB file is the fastest way to lose credibility.

---

## 0. What you will have at the end

| Layer | Object | Rows |
| --- | --- | ---: |
| Bronze | raw CSV in a volume | 41,418 |
| Silver | `silver_zomato_listings` (typed, keyed) | 41,418 |
| Gold | `dim_*`, `bridge_restaurant_cuisine`, `fact_restaurant_listing` | 41,357 |
| Gold | `mart_market_opportunity` (scored) | 4,878 |
| ML | tracked model runs in MLflow | 2 experiments |

## 1. Prerequisites

- A Databricks workspace. Unity Catalog workspaces use the catalog path below; **Community
  Edition** has no Unity Catalog — see section 8 for the substitutions.
- A cluster with a Databricks Runtime **ML** version (13.3 LTS ML or later) so `mlflow` and
  `scikit-learn` are preinstalled.
- The file `zomato_cleaned.csv` from this repository (~560 MB).
- Repository files to paste into notebooks: `src/01_silver_transform.py`, `sql/02_gold_star_schema.sql`,
  `sql/03_opportunity_score.sql`, `src/train_rating_model_mlflow.py`.

## 2. Create the storage location

In the Databricks SQL editor or a notebook:

```sql
CREATE CATALOG IF NOT EXISTS main;
CREATE SCHEMA IF NOT EXISTS main.zomato;
CREATE VOLUME IF NOT EXISTS main.zomato.raw;
```

Upload the CSV: **Catalog → main → zomato → raw → Upload to this volume**, or
**Workspace → Create → File upload**. Target path:

```
/Volumes/main/zomato/raw/zomato_cleaned.csv
```

Expect the upload to take a few minutes at 560 MB.

## 3. Silver — typed, keyed listings

1. **Workspace → Create → Notebook.** Name it `01_silver_transform`. Language: Python.
2. Paste the full contents of `src/01_silver_transform.py`.
3. Attach the ML cluster and **Run all**.

The job creates `main.zomato.silver_zomato_listings`. It:

- creates `restaurant_key` = SHA-256 of the URL with its query string removed;
- parses `rate_clean`, `cost_clean` and `votes` into typed columns;
- normalises Yes/No flags into booleans;
- derives `price_band` (Budget < ₹400, Mid-range ₹400–799, Premium ₹800+);
- derives `is_high_rated` = rating ≥ 4.0 **and** votes ≥ 20;
- drops rows with an invalid rating, non-positive cost, negative votes or a missing locality.

**Pitfall this already handles.** `reviews_list` contains embedded newlines and quoted text, so the
reader is configured with `multiLine`, `quote` and `escape`. If you rewrite the loader without
those options, Spark will split review text across rows and every downstream count will be wrong.
This is the single most common way to break this pipeline.

## 4. Gold — star schema

1. Create a notebook named `02_gold_star_schema`, language **SQL**.
2. Paste `sql/02_gold_star_schema.sql` and run it.

Creates: `dim_restaurant`, `dim_location`, `dim_restaurant_type`, `dim_price_band`,
`dim_listing_type`, `dim_cuisine`, `bridge_restaurant_cuisine`, `fact_restaurant_listing`,
`mart_market_opportunity`.

## 5. Gold — opportunity score

1. Create a notebook named `03_opportunity_score`, language **SQL**.
2. Paste `sql/03_opportunity_score.sql` and run it.

This rewrites `mart_market_opportunity` with `opportunity_score` and `opportunity_tier` on top of
the base aggregates, so it matches the local build in `src/build_local_gold.py`.

## 6. Validate before moving on

Run this in a SQL notebook. Every number should match, because these are the same figures the local
build produced from the same source file.

```sql
SELECT 'restaurants'      AS check_name, COUNT(*) AS value FROM main.zomato.dim_restaurant
UNION ALL SELECT 'silver rows',      COUNT(*) FROM main.zomato.silver_zomato_listings
UNION ALL SELECT 'fact rows',        COUNT(*) FROM main.zomato.fact_restaurant_listing
UNION ALL SELECT 'cuisines',         COUNT(*) FROM main.zomato.dim_cuisine
UNION ALL SELECT 'localities',       COUNT(*) FROM main.zomato.dim_location
UNION ALL SELECT 'market segments',  COUNT(*) FROM main.zomato.mart_market_opportunity
UNION ALL SELECT 'scored segments',  COUNT(*) FROM main.zomato.mart_market_opportunity WHERE opportunity_score IS NOT NULL;
```

| check_name | expected |
| --- | ---: |
| restaurants | 9,431 |
| silver rows | 41,418 |
| fact rows | 41,357 |
| cuisines | 105 |
| localities | 92 |
| market segments | 4,878 |
| scored segments | 1,207 |

Also confirm no restaurant is double counted in a top-level KPI:

```sql
SELECT COUNT(DISTINCT restaurant_key) AS restaurants FROM main.zomato.fact_restaurant_listing;
-- 9431
```

## 7. ML layer with MLflow tracking

1. Create a notebook named `04_rating_model`, language **Python**.
2. Paste `src/train_rating_model_mlflow.py`, or open `notebooks/01_market_analysis.ipynb` for the
   analysis narrative.
3. Set the widget `feature_table` to `main.zomato.model_features` and run.

If you have not created `model_features` yet, add it to the Gold layer — it is the restaurant-grain
feature table (one row per `restaurant_key`):

```sql
CREATE OR REPLACE TABLE main.zomato.model_features AS
SELECT
  f.restaurant_key,
  MAX(f.rating)            AS rating,
  MAX(f.vote_count)        AS vote_count,
  MAX(f.cost_for_two)      AS cost_for_two,
  l.location_name,
  t.restaurant_type_name,
  MAX(CAST(f.online_order_available AS INT)) = 1 AS online_order_available,
  MAX(CAST(f.table_booking_available AS INT)) = 1 AS table_booking_available,
  MAX(f.is_high_rated)     AS is_high_rated
FROM main.zomato.fact_restaurant_listing f
JOIN main.zomato.dim_location l ON f.location_key = l.location_key
JOIN main.zomato.dim_restaurant_type t ON f.restaurant_type_key = t.restaurant_type_key
GROUP BY f.restaurant_key, l.location_name, t.restaurant_type_name;
```

Then add the cuisine text:

```sql
CREATE OR REPLACE TABLE main.zomato.model_features AS
SELECT mf.*, cu.cuisines
FROM main.zomato.model_features mf
LEFT JOIN (
  SELECT b.restaurant_key,
         concat_ws(', ', sort_array(collect_set(c.cuisine_name))) AS cuisines
  FROM main.zomato.bridge_restaurant_cuisine b
  JOIN main.zomato.dim_cuisine c ON b.cuisine_key = c.cuisine_key
  GROUP BY b.restaurant_key
) cu ON mf.restaurant_key = cu.restaurant_key;
```

The notebook logs parameters, metrics (ROC-AUC, PR-AUC, F1, precision, recall), the model artifact,
and the feature-importance table into the experiment `zomato_rating_model`. Open
**Experiments** in the sidebar to see the runs and compare them.

Local reference results from the same data: logistic regression ROC-AUC 0.8207 / PR-AUC 0.6493;
random forest ROC-AUC 0.8324 / PR-AUC 0.6753. Small differences on a cluster are expected because
of the library versions.

## 8. Community Edition substitutions

Community Edition has no Unity Catalog and no volumes:

```sql
CREATE DATABASE IF NOT EXISTS zomato;
-- use table names like zomato.silver_zomato_listings
```

- Upload the CSV and read it from `dbfs:/FileStore/tables/zomato_cleaned.csv`.
- Set the Silver widget `input_path` to that path and `output_table` to
  `zomato.silver_zomato_listings`.
- Replace `main.zomato.` with `zomato.` in both SQL files.
- MLflow works, but experiment tracking is limited to the workspace.

## 9. Connect Power BI

Two options:

1. **Partner Connect (recommended).** **Compute → your cluster → Advanced options → JDBC/ODBC →
   Partner Connect → Power BI.** Then in Power BI choose **Get Data → Azure Databricks** and
   select the `main.zomato` tables. Import mode is fine at this size.
2. **CSV export (simplest for a portfolio).** Export each Gold table to `data/gold/*.csv` and
   import those, exactly as `docs/powerbi_build_guide.md` describes.

Either way, build the report using the page plan in `docs/powerbi_build_guide.md`.

## 10. Cost and teardown

- Use a single-node or small cluster; terminate it when you finish. A few hours of small-cluster
  work is normally within free or trial credit, but check your own plan.
- Keep the Delta tables — they are cheap and let you refresh Power BI without re-running ingestion.

## 11. Common pitfalls

| Symptom | Cause | Fix |
| --- | --- | --- |
| Row count far above 41,418 | CSV read without `multiLine` | Add `multiLine`, `quote`, `escape` |
| Restaurant count = 41,357 | `COUNT(*)` on the fact table | Use `COUNT(DISTINCT restaurant_key)` |
| Cuisine counts exceed restaurant total | Multi-cuisine restaurants via the bridge | Expected; use `DISTINCTCOUNT` |
| `PermissionError` writing MLflow artifacts | Path is not a volume | Log artifacts to a volume path |
| Power BI refresh fails after renaming a column | Report bound to old name | Update the query, not the report field names |
