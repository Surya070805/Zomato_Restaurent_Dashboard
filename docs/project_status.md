# Upgrade Status

## What the original project had

- A local restaurant-listing CSV.
- A PySpark script that parsed rating and cost and exported five columns.
- A Power BI `.pbix` with one flat table (`zomato_cleaned`) and one aggregate (`Cuisine_Stats`).
- A notebook with a first logistic-regression attempt that reported accuracy only.

## What this upgrade completed

| Phase | Artifact | Status |
| --- | --- | --- |
| Data contracts | `src/quality_audit.py`, `reports/data_quality_report.md` | Done |
| Data contracts | `docs/data_dictionary.md`, `docs/data_model.md` | Done |
| Pipeline | `src/01_silver_transform.py` (Databricks/PySpark Silver) | Done |
| Pipeline | `sql/02_gold_star_schema.sql`, `sql/03_opportunity_score.sql` | Done |
| Pipeline | `src/build_local_gold.py` -> `data/gold/*.csv` | Done |
| Insights | `src/market_insights.py` -> `reports/market_insights.md` | Done |
| Analysis | `notebooks/01_market_analysis.ipynb`, executed with 9 charts | Done |
| ML | `src/train_rating_model.py` (LR vs RF, PR-AUC, permutation importance) | Done |
| ML | `src/train_rating_model_mlflow.py` (MLflow experiment tracking) | Done |
| BI | `powerbi/measures.dax` (deduplicated KPI library) | Done |
| BI | `docs/powerbi_build_guide.md` (5-page build plan) | Done |
| Decision layer | `docs/business_recommendations.md` | Done |
| Platform | `docs/databricks_runbook.md` | Done |
| Positioning | `docs/interview_guide.md` | Done |

## Verified state of the data

| Check | Value |
| --- | ---: |
| Source listing rows | 41,418 |
| Unique restaurants | 9,431 |
| Rows that are repeat appearances | 39,953 (96.46%) |
| Fact rows (restaurant x listing type) | 41,357 |
| Localities | 92 |
| Cuisines | 105 |
| Market segments | 4,878 |
| Scored segments (>= 5 restaurants) | 1,207 |

Model results are reproducible from `data/gold/model_features.csv`: random forest ROC-AUC 0.8324,
PR-AUC 0.6753.

## Remaining work (optional, highest value first)

1. **Power BI execution.** The build guide is complete; the five pages still need to be built in
   Power BI Desktop and screenshotted into `screenshots/` for the portfolio.
2. **Databricks execution.** Run the runbook once so the MLflow experiment exists and the resume
   claim about tracked experiments is literally true.
3. **A second data snapshot.** Converts the report from descriptive to growth-aware and is the
   single biggest analytical upgrade available.
4. **Voice-of-customer module.** TF-IDF plus NMF or sentence embeddings over `reviews_list`, kept
   strictly separate from the rating model to avoid leakage.
5. **Expansion score calibration.** Give the opportunity score weights an explicit rationale and a
   sensitivity test showing how the shortlist changes when weights move.

## Current truthful positioning

> Restaurant analytics project with data cleaning, a documented star schema, KPI reporting,
> executed market analysis, and a leakage-aware rating classifier.

## Position after the Power BI and Databricks steps are done

> Restaurant market intelligence platform with a Bronze/Silver/Gold pipeline, dimensional modelling,
> a KPI framework, locality and cuisine analysis, pricing and service insights, MLflow-tracked
> models, and a transparent expansion screening layer.
