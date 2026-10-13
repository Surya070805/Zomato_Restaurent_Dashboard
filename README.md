# Zomato Bangalore Restaurant Market Intelligence & Expansion Analytics Platform

[![Power BI](https://img.shields.io/badge/Power_BI-PBIP_Developer_Mode-F2C811?logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![Semantic Model](https://img.shields.io/badge/Model-TMDL_Format-2563EB)](https://learn.microsoft.com/power-bi/)
[![Architecture](https://img.shields.io/badge/Architecture-Medallion_Star_Schema-10B981)](#data-pipeline--medallion-architecture)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Machine Learning](https://img.shields.io/badge/ML-Scikit_Learn_Classifier-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Visual Standard](https://img.shields.io/badge/UI_Standard-100%25_Native_Visuals-E23744)](#power-bi-dashboard-architecture)

An end-to-end enterprise analytics and machine learning platform engineered on **Zomato Bangalore restaurant listing data**. This solution transforms raw, unstructured directory data into a decision-support system featuring a **6-page Power BI executive dashboard**, a **TMDL semantic star schema**, an **Opportunity Scoring Engine**, and a **leakage-aware predictive classifier**.

Built using Microsoft Fabric **PBIR (Power BI Enhanced Report Format)** and **TMDL (Tabular Model Definition Language)**, ensuring 100% version control compatibility, modularity, and reproducible data modeling.

---

## Executive Summary & Strategic Value

In hyper-competitive food and beverage markets, capital allocation for restaurant expansion carries high downside risk. Traditional directory extracts are plagued by duplicate listings, inconsistent pricing attributes, concatenated multi-value strings, and uncurated metrics. 

This platform establishes:
1. **Canonical Restaurant Deduplication**: Collapses 41,418 noisy listing entries into **9,431 distinct physical restaurants**, preventing 4.4x market inflation.
2. **Medallion Data Architecture**: Automates transformation from Raw CSV &rarr; Bronze Landing &rarr; Silver Cleansed &rarr; Gold Star Schema with a normalized many-to-many cuisine bridge table.
3. **Multi-Criteria Opportunity Scoring**: Quantitative heuristic evaluating 1,207 market micro-segments across Demand Proxy (40%), Observed Quality (25%), Market Whitespace (25%), and Service Fit (10%).
4. **High-Rating Predictive Model**: Group-aware Random Forest classifier predicting the probability of establishing a trusted, high-rated venue while strictly preventing post-outcome data leakage.
5. **100% Native Executive Dashboard**: 6-page responsive developer suite built entirely with native Power BI visual primitives (zero static background templates).

---

## Headline Findings

- **Market Deduplication Ratio (4.4x)**: 41,418 raw listing rows represent only 9,431 unique physical restaurants. Approximately 82% of records are duplicate category listings for existing restaurants.
- **Strict Quality Ceiling (22.34%)**: Only 2,107 restaurants meet the threshold for a trusted high-rating (`rating >= 4.0` with `votes >= 20`).
- **Premium Segment Outperformance**: Premium dining establishments are **~5x more likely** to achieve high ratings than budget establishments (54.90% vs 11.51%), though premium outlets account for only 16.79% of total supply.
- **Table Booking as a Quality Marker**: Venues offering table reservation services demonstrate a **4.15 average rating** and **77.60% high-rated share**, compared to 3.51 and 13.43% for venues without reservations.
- **Cuisine Concentration**: 71.6% of restaurants (6,753 outlets) serve at least one of the top 5 cuisines (North Indian, Chinese, South Indian, Fast Food, Biryani).
- **Engagement Driver**: Customer votes correlate far more strongly with observed rating ($r_s = 0.63$) than cost for two ($r_s = 0.28$).

---

## Power BI Dashboard Architecture

The dashboard is engineered with **100% native visuals** at a high-definition **1920 &times; 1080** canvas, incorporating the official Zomato corporate design system (Zomato Red `#E23744`, Charcoal `#1C1C1C`, Slate `#64748B`, Neutral Canvas `#F4F6F9`).

| Page # | Page Name | File Path | Focus & Strategic Capabilities |
| :---: | :--- | :--- | :--- |
| **1** | **Executive Overview** | [`pages/73ef1004c74378e55b0b`](Zomato%20insights.Report/definition/pages/73ef1004c74378e55b0b) | Macro market metrics (9,431 restaurants, 3.70 avg rating, ₹556 avg cost, 22.3% high-rated share), price band mix, dining segment rating trends, and delivery vs. dining adoption. |
| **2** | **Locality Intelligence** | [`pages/df89f9b1fc5ad7324e4f`](Zomato%20insights.Report/definition/pages/df89f9b1fc5ad7324e4f) | Micro-market screening across 92 localities. Locality Attractiveness Index, Top 15 density ranking, and Volume vs. Quality quadrant analysis. |
| **3** | **Cuisine Landscape** | [`pages/f95806c8d1cba57e1b2e`](Zomato%20insights.Report/definition/pages/f95806c8d1cba57e1b2e) | Taxonomy breakdown over 105 cuisines via bridge table. Footprint ranking, cost vs. rating scatter, and price tier segmentation across core cuisines. |
| **4** | **Service Impact** | [`pages/4c04545cc792e0277f43`](Zomato%20insights.Report/definition/pages/4c04545cc792e0277f43) | Operational channel analysis (Online Ordering &times; Table Booking). Rating uplifts, engagement multiples, and market penetration analysis. |
| **5** | **Restaurant Expansion** | [`pages/7f53c490fba314969e23`](Zomato%20insights.Report/definition/pages/7f53c490fba314969e23) | Interactive Scenario Explorer with dynamic slicers. 1,207 scored segments, Shortlist pipeline table (Score &ge; 85), and opportunity tier distribution column chart. |
| **6** | **Model Governance** | [`pages/bd08750c87e3cc800f83`](Zomato%20insights.Report/definition/pages/bd08750c87e3cc800f83) | Data flow architecture from Raw CSV &rarr; Gold Star Schema, Star Schema entity badges, Dimensional Entity Integrity Summary table, and 4 Analytical Boundary Conditions. |

---

## Data Pipeline & Medallion Architecture

```text
+-----------------------------------------------------------------------------------+
|                                 SOURCE EXTRACT                                    |
|              Raw Zomato Bangalore Dataset (41,418 listing-category rows)          |
+-----------------------------------------------------------------------------------+
                                          |
                                          v  [src/01_silver_transform.py]
+-----------------------------------------------------------------------------------+
|                                  BRONZE LAYER                                     |
|  - Schema validation & type casting                                               |
|  - Initial data profiling & null audits                                           |
|  - Unaltered raw landing audit trail                                              |
+-----------------------------------------------------------------------------------+
                                          |
                                          v  [src/build_local_gold.py]
+-----------------------------------------------------------------------------------+
|                                  SILVER LAYER                                     |
|  - URL normalization & canonical hashing (restaurant_key)                         |
|  - 4.4x deduplication logic across repeated category appearances                  |
|  - Text cleaning: ratings extraction, numeric cost casting, address parsing       |
|  - Multi-value cuisine unnesting & standardization                                |
+-----------------------------------------------------------------------------------+
                                          |
                                          v  [sql/02_gold_star_schema.sql]
+-----------------------------------------------------------------------------------+
|                                   GOLD LAYER                                      |
|  Curated Star Schema Dimensional Model:                                           |
|    - Fact Table:      fact_restaurant_listing (41,357 rows)                       |
|    - Dimension Tables: dim_restaurant (9,431), dim_location (92),                 |
|                        dim_cuisine (105), dim_price_band (3),                     |
|                        dim_service (4), dim_listing_type, dim_restaurant_type     |
|    - Bridge Table:    bridge_restaurant_cuisine (25,627 rows)                     |
|    - Analytical Mart: mart_market_opportunity (1,207 segments)                    |
+-----------------------------------------------------------------------------------+
```

---

## Semantic Data Model & Key DAX Formulations

The semantic layer is authored in **TMDL (Tabular Model Definition Language)**, defining explicit business relationships, display folders, and calculated tables.

### 1. Restaurant Count (Deduplicated Identity)
```dax
Restaurant Count = 
DISTINCTCOUNT ( fact_restaurant_listing[restaurant_key] )
```
*Guarantees accurate venue counts without row-level inflation.*

### 2. Collapsed Venue Rating
```dax
Restaurant Rating = 
AVERAGEX (
    VALUES ( fact_restaurant_listing[restaurant_key] ),
    CALCULATE ( MAX ( fact_restaurant_listing[rating] ) )
)
```

### 3. Locality Attractiveness Index
```dax
Locality Attractiveness = 
VAR Engagement = 
    DIVIDE ( 
        [Average Votes per Restaurant], 
        MAXX ( ALL ( dim_location[location_name] ), [Average Votes per Restaurant] ) 
    )
VAR Quality = DIVIDE ( [Restaurant Rating], 5 )
RETURN
    0.6 * Engagement + 0.4 * Quality
```

### 4. Opportunity Scoring Model
For each (Locality &times; Cuisine &times; Price Band) market segment with &ge; 5 outlets:
$$\text{Opportunity Score} = 0.40 \times S_{\text{demand}} + 0.25 \times S_{\text{quality}} + 0.25 \times S_{\text{whitespace}} + 0.10 \times S_{\text{service}}$$
Segments are classified into four tiers:
- **Shortlist** ($\text{Score} \ge 85$): 27 segments
- **High** ($70 \le \text{Score} < 85$): 184 segments
- **Moderate** ($50 \le \text{Score} < 70$): 540 segments
- **Low** ($\text{Score} < 50$): 456 segments

---

## Machine Learning Classifier

A predictive machine learning classifier was trained to estimate the probability of an outlet achieving a high platform rating (`rating >= 4.0` AND `votes >= 20`).

### Feature Selection & Leakage Prevention
To prevent target leakage, post-outcome metrics were strictly excluded:
- **Excluded**: Raw vote counts, review texts, dish mentions, restaurant names, URLs, phone numbers.
- **Included Features**: Locality, cuisine mix, price band, approximate cost for two, online ordering flag, table booking flag, restaurant type.

### Model Evaluation Results
Evaluated using a **Grouped 75/25 Split** grouped by `restaurant_key` to ensure outlets never appear in both training and test sets.

| Model Algorithm | ROC-AUC | PR-AUC (Selection Metric) | F1-Score | Precision | Recall |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Baseline Logistic Regression | 0.8207 | 0.6493 | 0.5657 | 0.4890 | 0.6711 |
| **Random Forest Classifier (Selected)** | **0.8324** | **0.6753** | **0.6019** | **0.5898** | **0.6144** |

*PR-AUC is prioritized because positive high-rated venues comprise only 22.34% of the population.*

### Permutation Feature Importance
1. **Cuisine Classification**: 0.156
2. **Table Booking Availability**: 0.144
3. **Cost for Two**: 0.069
4. **Restaurant Type**: 0.029
5. **Locality / Area**: 0.014
6. **Online Ordering Flag**: 0.005

---

## Repository Structure

```text
├── .gitignore
├── README.md
├── Zomato Big Data Analysis.py
├── Zomato insights.pbip              # Power BI Developer Project entrypoint
├── Zomato insights.pbix              # Compiled Power BI Desktop binary
├── Zomato_Predictive_analysis.ipynb  # ML notebook with models and metrics
│
├── Zomato insights.Report/           # PBIR Enhanced Report definition
│   ├── definition.pbir
│   └── definition/
│       ├── report.json
│       ├── version.json
│       └── pages/
│           ├── 73ef1004c74378e55b0b/ # Page 1: Executive Overview
│           ├── df89f9b1fc5ad7324e4f/ # Page 2: Locality Intelligence
│           ├── f95806c8d1cba57e1b2e/ # Page 3: Cuisine Landscape
│           ├── 4c04545cc792e0277f43/ # Page 4: Service Impact
│           ├── 7f53c490fba314969e23/ # Page 5: Restaurant Expansion Explorer
│           └── bd08750c87e3cc800f83/ # Page 6: Model Governance
│
├── Zomato insights.SemanticModel/    # TMDL Semantic Model definition
│   ├── definition.pbism
│   └── definition/
│       ├── model.tmdl
│       ├── expressions.tmdl
│       ├── relationships.tmdl
│       └── tables/
│           ├── _Measures.tmdl
│           ├── fact_restaurant_listing.tmdl
│           ├── dim_restaurant.tmdl
│           ├── dim_location.tmdl
│           ├── dim_cuisine.tmdl
│           ├── bridge_restaurant_cuisine.tmdl
│           ├── dim_price_band.tmdl
│           ├── dim_service.tmdl
│           ├── mart_market_opportunity.tmdl
│           └── governance_entity_summary.tmdl
│
├── data/gold/                        # Curated Gold tables (CSVs)
│   ├── dim_restaurant.csv
│   ├── dim_location.csv
│   ├── dim_cuisine.csv
│   ├── bridge_restaurant_cuisine.csv
│   ├── fact_restaurant_listing.csv
│   └── mart_market_opportunity.csv
│
├── src/                              # Python & PySpark pipeline scripts
│   ├── quality_audit.py              # Raw data profiling & validation
│   ├── 01_silver_transform.py        # PySpark Silver transformation
│   ├── build_local_gold.py           # Pandas local Gold generation
│   ├── market_insights.py            # Automated insight generation
│   └── train_rating_model.py         # ML training & model evaluation
│
├── sql/                              # Dimensional modeling DDL & SQL
│   ├── 02_gold_star_schema.sql
│   └── 03_opportunity_score.sql
│
├── notebooks/                        # Executed Jupyter analysis
│   └── 01_market_analysis.ipynb
│
├── reports/                          # Audit summaries and figures
│   ├── quality_audit.md
│   └── market_insights.md
│
└── docs/                             # Data architecture & governance docs
    ├── data_dictionary.md
    ├── data_model.md
    └── powerbi_build_guide.md
```

---

## Quick Start & Execution Guide

### 1. Environment Setup
```powershell
# Clone the repository
git clone https://github.com/Surya070805/Zomato_Restaurent_Dashboard.git
cd Zomato_Restaurent_Dashboard

# Install Python dependencies
pip install pandas scikit-learn matplotlib joblib nbformat
```

### 2. Run Data Pipeline & Model Training
```powershell
# Profile raw listing data
python src/quality_audit.py --input zomato_cleaned.csv --output-dir reports

# Build local Gold dimensional star schema & opportunity mart
python src/build_local_gold.py --input zomato_cleaned.csv --output-dir data/gold

# Generate quantitative insight summaries
python src/market_insights.py --gold-dir data/gold --output-dir reports

# Train and evaluate the high-rating predictive classifier
python src/train_rating_model.py --input data/gold/model_features.csv --output-dir reports
```

### 3. Open in Power BI Desktop
Open [`Zomato insights.pbip`](Zomato%20insights.pbip) directly in **Power BI Desktop** (Developer Mode enabled) or launch [`Zomato insights.pbix`](Zomato%20insights.pbix). All visuals, measures, and data model relationships load automatically.

---

## Analytical Boundary Conditions

1. **Single Historical Snapshot**: Data reflects a point-in-time snapshot of the Bangalore restaurant ecosystem. Trends over time, revenue velocity, and seasonal churn are not captured.
2. **Customer Votes as Engagement Proxy**: Review votes serve as a proxy for platform engagement and attention, not actual sales or monetary order volumes.
3. **No Causal Claims**: Observed relationships (e.g., higher average ratings among table-booking venues) represent segment correlations and do not imply operational causation.
4. **Data Coverage**: Analysis reflects cataloged restaurants on the platform and does not include unlisted informal dining vendors.

---

## License & Attribution
Developed for analytical research and decision-support modeling on public restaurant intelligence datasets. All brand trademarks belong to Zomato Ltd.
