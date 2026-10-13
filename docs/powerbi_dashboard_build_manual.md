# Zomato Restaurant Market Intelligence Platform
## Complete Power BI Visual & KPI Build Manual

This document provides a step-by-step implementation guide to construct all **6 dashboards (report pages)** in Power BI Desktop for the Zomato Bangalore Restaurant Market Intelligence Platform.

---

## 🎨 Global Design System & Canvas Setup

Before building individual visuals, apply these global formatting standards across all pages:

| Property | Value / Standard |
| :--- | :--- |
| **Page Dimensions** | **16:9 widescreen** (`1280 × 720 px`) |
| **Canvas Background** | Hex `#F8F9FA` (Soft Light Gray), **Transparency: 0%** |
| **Primary Brand Accent** | Hex `#E23744` (Zomato Crimson Red) |
| **Secondary Accent / Headers** | Hex `#1C2434` (Dark Slate Navy) |
| **Positive / Shortlist / Quality** | Hex `#10B981` (Emerald Green) |
| **Engagement / Accent Color** | Hex `#0D9488` (Teal) |
| **Warning / Baseline Accent** | Hex `#F59E0B` (Amber) |
| **Visual Containers** | Background: `#FFFFFF` (Pure White), Padding: `8px`, **Effects → Shadow → On** (Soft offset) |
| **Font Family** | **Segoe UI** (Standard Power BI) or **Inter** |

### Global Slicer Ribbon (Synchronized Across Pages)
Add these slicers to a top bar or collapsible left panel:
1. `dim_price_band[price_band]` (Tile or Dropdown)
2. `fact_restaurant_listing[online_order_available]` (Button toggle / Dropdown)
3. `fact_restaurant_listing[table_booking_available]` (Button toggle / Dropdown)

> **Important:** Select each slicer $\rightarrow$ **View → Sync Slicers** $\rightarrow$ Check both **Visible** and **Sync** for Pages 1 through 5.

---

# 📊 Dashboard 1: Executive Overview
**Objective:** Deliver an executive summary of market scale, rating distribution, price band dynamics, and geographic density.

```
+---------------------------------------------------------------------------------------------------------+
| [ KPI 1: Unique Rest ] [ KPI 2: Avg Rating ] [ KPI 3: Median Cost ] [ KPI 4: Online % ] [ KPI 5: High %]|
+------------------------------------+------------------------------------+-------------------------------+
| Top 15 Localities by Density       | Market Share by Price Band         | Quality vs Density Scatter    |
| (Horizontal Clustered Bar)         | (Donut Chart)                      | (Scatter Chart)               |
+------------------------------------+------------------------------------+-------------------------------+
| ⚠️ Scope Notice: Single snapshot of 9,431 unique restaurants derived from 41,357 category listings.     |
+---------------------------------------------------------------------------------------------------------+
```

### 1.1 Top KPI Ribbon
Create 5 separate **Card** visuals (or one unified **New Card** visual):
* **Card 1: Unique Restaurants**
  * **Field:** `_Measures[Restaurant Count]`
  * **Format:** Callout font size `28`, Bold, Color `#1C2434`.
  * **Label:** `Unique Restaurants` (Target: **9,431**)
* **Card 2: Market Average Rating**
  * **Field:** `_Measures[Restaurant Rating]`
  * **Format:** Callout font size `28`, Bold, Color `#1C2434`.
  * **Label:** `Market Avg Rating` (Target: **3.63 ★**)
* **Card 3: Median Spend**
  * **Field:** `_Measures[Median Cost for Two]`
  * **Format:** Callout font size `28`, Bold, Color `#1C2434`.
  * **Label:** `Median Cost for Two` (Target: **₹400**)
* **Card 4: Delivery Adoption**
  * **Field:** `_Measures[Online Order Rate]`
  * **Format:** Callout font size `28`, Bold, Color `#0D9488`.
  * **Label:** `Online Delivery Adoption` (Target: **62.0%**)
* **Card 5: Quality Benchmark**
  * **Field:** `_Measures[Trusted High Rated Share]`
  * **Format:** Callout font size `28`, Bold, Color `#10B981`.
  * **Label:** `High-Rated Share (≥4.0 & ≥20 votes)` (Target: **23.2%**)

### 1.2 Visual 1 — Locality Density Leaderboard
* **Visual Type:** **Clustered Bar Chart** (Horizontal)
* **Fields:**
  * **Y-axis:** `dim_location[location_name]`
  * **X-axis:** `_Measures[Restaurant Count]`
* **Filter:** In the Filters pane $\rightarrow$ `location_name` $\rightarrow$ Filter type: **Top N** $\rightarrow$ Show **Top 15** by `[Restaurant Count]`.
* **Sort:** Click 3 dots on visual $\rightarrow$ **Sort axis → Restaurant Count → Sort descending**.
* **Formatting:** Bar color = `#E23744` (Zomato Red), Data labels = **On**.

### 1.3 Visual 2 — Market Share by Price Tier
* **Visual Type:** **Donut Chart**
* **Fields:**
  * **Legend:** `dim_price_band[price_band]`
  * **Values:** `_Measures[Restaurant Count]`
* **Formatting:**
  * Slices colors: `Budget` = Soft Coral (`#FB7185`), `Mid-range` = Slate Navy (`#1C2434`), `Premium` = Emerald Green (`#10B981`).
  * Detail labels: **Category, percent of total**.

### 1.4 Visual 3 — Locality Quality vs. Density Matrix
* **Visual Type:** **Scatter Chart**
* **Fields:**
  * **X-axis:** `_Measures[Restaurant Count]`
  * **Y-axis:** `_Measures[Restaurant Rating]`
  * **Size:** `_Measures[Average Votes per Restaurant]`
  * **Values / Legend:** `dim_location[location_name]`
* **Visual Filter:** Filters pane $\rightarrow$ `_Measures[Restaurant Count]` $\rightarrow$ **is greater than or equal to `50`**.
* **Formatting:** Y-axis minimum = `3.0`, maximum = `4.5`. Add X and Y reference gridlines.

### 1.5 Analytical Context Box
* **Visual Type:** **Text Box**
* **Content:** *"⚠️ Scope Notice: Single historical snapshot of 9,431 canonical restaurants. Deduplicated across listing types. Metrics reflect platform associations rather than longitudinal growth."*

---

# 📍 Dashboard 2: Locality Intelligence
**Objective:** Evaluate geographic micro-markets to identify areas that combine customer engagement and quality without excessive saturation.

```
+---------------------------------------------------------------------------------------------------------+
| [ KPI 1: 92 Localities ] [ KPI 2: 242 Avg Votes ] [ KPI 3: Lavelle Rd 4.07★ ] [ KPI 4: Church St 878 V ]|
+----------------------------------------------------+----------------------------------------------------+
| Top 10 Localities by Composite Attractiveness      | Locality Performance & Quality Grid                |
| (Horizontal Ranked Bar Chart)                      | (Matrix / Table with In-Cell Data Bars & Colors)   |
+----------------------------------------------------+----------------------------------------------------+
```

### 2.1 Top KPI Ribbon
* **Card 1:** `_Measures[Locality Count]` $\rightarrow$ Label: `Total Localities` (**92**)
* **Card 2:** `_Measures[Average Votes per Restaurant]` $\rightarrow$ Label: `Market Avg Votes / Outlet` (**242**)
* **Card 3:** Text Card $\rightarrow$ Label: `Top Quality Hub` (**Lavelle Road — 4.07 ★, 68.6% High-Rated**)
* **Card 4:** Text Card $\rightarrow$ Label: `Top Engagement Hub` (**Church Street — 878 avg votes**)

### 2.2 Visual 1 — Top 10 Attractiveness Index
* **Visual Type:** **Clustered Bar Chart** (Horizontal)
* **Fields:**
  * **Y-axis:** `dim_location[location_name]`
  * **X-axis:** `_Measures[Locality Attractiveness]`
* **Filter:** Top N filter on `location_name` $\rightarrow$ **Top 10** by `[Locality Attractiveness]`.
* **Sort:** Sort descending.
* **Formatting:** Bars color = `#0D9488` (Teal), Data labels = **On** (Display units: 3 decimal places).

### 2.3 Visual 2 — Locality Performance Grid
* **Visual Type:** **Table** or **Matrix**
* **Fields:**
  * **Rows / Columns:** `dim_location[location_name]`
  * **Values:**
    1. `_Measures[Restaurant Count]`
    2. `_Measures[Restaurant Rating]`
    3. `_Measures[Average Votes per Restaurant]`
    4. `_Measures[Trusted High Rated Share]`
    5. `_Measures[Locality Attractiveness]`
* **Conditional Formatting (Format visual → Cell elements):**
  * `[Restaurant Count]`: **Data bars → On** (Color: `#3B82F6` Soft Blue).
  * `[Restaurant Rating]`: **Background color → On** (Gradient from `#FDE68A` Light Amber at 3.4 to `#10B981` Emerald at 4.1).
  * `[Trusted High Rated Share]`: **Font color → On** (Green gradient).
* **Sort:** Click header `Locality Attractiveness` to sort descending.

---

# 🍜 Dashboard 3: Cuisine & Pricing Landscape
**Objective:** Reveal cuisine concentration, pricing distribution, and whitespace segments.

```
+---------------------------------------------------------------------------------------------------------+
| [ KPI 1: 105 Cuisines ] [ KPI 2: 71.6% Top 5 Share ] [ KPI 3: Japanese 4.21★ ] [ KPI 4: Continental 48% ]|
+------------------------------------+------------------------------------+-------------------------------+
| Cuisine Volume Distribution        | Quality Leaderboard (Rating)       | Rating Heatmap: Price x Cuisine
| (Treemap)                          | (Clustered Bar Chart)              | (Matrix Table)                |
+------------------------------------+------------------------------------+-------------------------------+
| Cuisine Competition vs Quality Bubble Chart (Scatter Chart)                                             |
+---------------------------------------------------------------------------------------------------------+
```

### 3.1 Top KPI Ribbon
* **Card 1:** Distinct count `dim_cuisine[cuisine_name]` $\rightarrow$ Label: `Active Cuisines` (**105**)
* **Card 2:** Static Card $\rightarrow$ Label: `Top 5 Cuisine Share` (**71.6%** — North Indian, Chinese, Fast Food, South Indian, Biryani)
* **Card 3:** Static Card $\rightarrow$ Label: `Highest Rated Cuisine` (**Japanese — 4.21 ★**)
* **Card 4:** Static Card $\rightarrow$ Label: `Top Premium Volume` (**Continental — 47.9% High-Rated**)

### 3.2 Visual 1 — Cuisine Volume Share
* **Visual Type:** **Treemap**
* **Source Table:** `mart_market_opportunity`
* **Fields:**
  * **Category:** `cuisine_name`
  * **Values:** `restaurant_count` (Sum)
* **Filters:** Filter to Top 15 cuisines by count.

### 3.3 Visual 2 — Highest Rated Cuisines (Quality Leaderboard)
* **Visual Type:** **Clustered Bar Chart** (Horizontal)
* **Source Table:** `mart_market_opportunity`
* **Fields:**
  * **Y-axis:** `cuisine_name`
  * **X-axis:** `average_rating` (Average)
* **Filters:**
  * Visual Filter on `restaurant_count` $\rightarrow$ **is greater than or equal to `30`**.
  * Top N on `cuisine_name` $\rightarrow$ **Top 15** by Average Rating.
* **Formatting:** Bar color = `#10B981` (Green), X-axis min = `3.5`, max = `4.5`.

### 3.4 Visual 3 — Price Tier $\times$ Cuisine Heatmap
* **Visual Type:** **Matrix**
* **Fields:**
  * **Rows:** `dim_price_band[price_band]`
  * **Columns:** `mart_market_opportunity[cuisine_name]`
  * **Values:** `mart_market_opportunity[average_rating]` (Average)
* **Filter:** Filter `cuisine_name` to Top 10 by volume.
* **Formatting:** In **Cell elements** $\rightarrow$ **Background color gradient** (Light Cream for 3.4 $\rightarrow$ Deep Forest Green for 4.3).

### 3.5 Visual 4 — Competition vs. Quality Scatter
* **Visual Type:** **Scatter Chart**
* **Source Table:** `mart_market_opportunity`
* **Fields:**
  * **X-axis:** `restaurant_count` (Sum)
  * **Y-axis:** `average_rating` (Average)
  * **Size:** `average_votes_per_restaurant` (Average)
  * **Values:** `cuisine_name`

---

# 🛵 Dashboard 4: Service Impact & Channel Dynamics
**Objective:** Evaluate how digital channels (Online Delivery vs. Table Booking) correlate with customer ratings and engagement.

```
+---------------------------------------------------------------------------------------------------------+
| [ KPI 1: Online 62.0% ] [ KPI 2: Booking 10.0% ] [ KPI 3: Booking Lift +0.64★ ] [ KPI 4: High-Rated 5.8x]|
+----------------------------------------------------+----------------------------------------------------+
| Rating by Service Channel vs Baseline (3.63)       | Engagement (Avg Votes) by Service Channel          |
| (Clustered Column Chart + Reference Line)          | (Clustered Column Chart)                           |
+----------------------------------------------------+----------------------------------------------------+
| Table Booking Availability across Price Bands      | Analytical Finding & Structural Marker Callout Box |
| (100% Horizontal Stacked Bar Chart)                | (Card / Text Box with Border)                      |
+----------------------------------------------------+----------------------------------------------------+
```

### 4.1 Top KPI Ribbon
* **Card 1:** `_Measures[Online Order Rate]` $\rightarrow$ Label: `Online Delivery Share` (**62.0%**)
* **Card 2:** `_Measures[Table Booking Rate]` $\rightarrow$ Label: `Table Reservation Share` (**10.0%**)
* **Card 3:** Static / Calculated Card $\rightarrow$ Label: `Booking Rating Lift` (**+0.64 Stars** — 4.15 vs 3.51)
* **Card 4:** Static / Calculated Card $\rightarrow$ Label: `High-Rated Advantage` (**5.8× Higher** — 77.6% vs 13.4%)

### 4.2 Visual 1 — Observed Rating by Service Channel
* **Visual Type:** **Clustered Column Chart**
* **Fields:**
  * **X-axis:** `fact_restaurant_listing[Service Combination]`
  * **Y-axis:** `_Measures[Restaurant Rating]`
* **Reference Line (Analytics Pane):**
  * Click **Constant Line** $\rightarrow$ Value: `3.63`.
  * Style: **Dashed**, Color: `#E23744`, Data label = `"Market Baseline: 3.63"`.
* **Formatting:** Column colors:
  * `No online + Booking`: `#4338CA` (Deep Indigo)
  * `Online + Booking`: `#6366F1`
  * `Online + No booking`: `#0EA5E9`
  * `No online + No booking`: `#94A3B8`

### 4.3 Visual 2 — Customer Engagement by Service Channel
* **Visual Type:** **Clustered Column Chart**
* **Fields:**
  * **X-axis:** `fact_restaurant_listing[Service Combination]`
  * **Y-axis:** `_Measures[Average Votes per Restaurant]`
* **Formatting:** Data labels = **On**. (Shows ~1,008 votes for booking channels vs ~150 votes without).

### 4.4 Visual 3 — Booking Adoption by Price Band
* **Visual Type:** **100% Stacked Bar Chart**
* **Fields:**
  * **Y-axis:** `dim_price_band[price_band]`
  * **X-axis:** `_Measures[Restaurant Count]`
  * **Legend:** `fact_restaurant_listing[table_booking_available]`
* **Insight:** Graphically proves table booking jumps from **0.2% in Budget** to **49.7% in Premium**.

### 4.5 Analytical Takeaway Card
* **Visual Type:** **Text Box** with an amber border:
* **Content:** *"Analytical Finding: Table booking availability correlates strongly with higher observed ratings and engagement, acting primarily as a marker of the upscale dining segment rather than an independent rating driver."*

---

# 🚀 Dashboard 5: Expansion Scenario Explorer
**Objective:** A decision-support interface for restaurant investors, founders, and franchise operators to screen expansion candidates.

```
+---------------------------------------------------------------------------------------------------------+
| [ Slicers: Locality Dropdown ] [ Cuisine Dropdown ] [ Price Band Tile ] [ Tier: Shortlist Pre-Selected ] |
+---------------------------------------------------------------------------------------------------------+
| [ KPI 1: 1,207 Scored ] [ KPI 2: 27 Shortlisted ] [ KPI 3: Avg Score 50.02 ] [ KPI 4: Church St / Chin ]|
+--------------------------------------------------------------------+------------------------------------+
| Priority Expansion Shortlist Grid                                 | Segments by Opportunity Tier       |
| (Table with Green Data Bars on Opportunity Score)                  | (Clustered Column Chart)           |
+--------------------------------------------------------------------+------------------------------------+
| Methodology: Score = 40% Demand + 25% Quality + 25% Whitespace + 10% Service Fit. Min 5 outlets.         |
+---------------------------------------------------------------------------------------------------------+
```

### 5.1 Interactive Slicer Ribbon
Add 4 dropdown slicers:
1. `mart_market_opportunity[location_name]`
2. `mart_market_opportunity[cuisine_name]`
3. `dim_price_band[price_band]`
4. `mart_market_opportunity[opportunity_tier]` (Set default filter to **"Shortlist"**)

### 5.2 Top KPI Ribbon
* **Card 1:** `_Measures[Scored Segments]` $\rightarrow$ Label: `Scored Segments (≥5 Outlets)` (**1,207**)
* **Card 2:** `_Measures[Shortlisted Segments]` $\rightarrow$ Label: `Shortlisted Prime Targets` (**27**)
* **Card 3:** `_Measures[Average Opportunity Score]` $\rightarrow$ Label: `Avg Opportunity Score` (**50.02 / 100**)
* **Card 4:** `_Measures[Top Segment]` $\rightarrow$ Label: `Top Opportunity` (**Church Street / Chinese**)

### 5.3 Visual 1 — Priority Opportunity Pipeline Table
* **Visual Type:** **Table**
* **Fields from `mart_market_opportunity`:**
  1. `location_name` (Locality)
  2. `cuisine_name` (Cuisine)
  3. `price_band` (Price Tier)
  4. `restaurant_count` (Existing Competitors)
  5. `average_rating` (Observed Rating, format `0.00`)
  6. `average_votes_per_restaurant` (Avg Votes)
  7. `opportunity_score` (Opportunity Score, format `0.0`)
  8. `opportunity_tier` (Tier Badge)
* **Visual Filter:** `opportunity_score` is not blank.
* **Sort:** Click `opportunity_score` $\rightarrow$ Sort descending.
* **Conditional Formatting:** `opportunity_score` $\rightarrow$ **Cell elements → Data bars → On** (Emerald Green `#10B981`).

### 5.4 Visual 2 — Opportunity Distribution by Tier
* **Visual Type:** **Clustered Column Chart**
* **Fields:**
  * **X-axis:** `mart_market_opportunity[opportunity_tier]`
  * **Y-axis:** Count of `mart_market_opportunity[opportunity_score]`
* **Formatting:** Sort X-axis: `Shortlist (27)`, `High (184)`, `Moderate (540)`, `Low (456)`.

### 5.5 Methodology Note
* **Visual Type:** **Text Box**
* **Content:** *"Opportunity Score Heuristic: 40% Demand Proxy + 25% Quality + 25% Market Whitespace + 10% Service Fit. Scored only for segments with $\ge 5$ restaurants. Screening tool for concept validation, not a guaranteed return."*

---

# 🛡️ Dashboard 6: Data Governance & Quality Audit (QA Page)
**Objective:** Deliver data integrity proof, model sanity checks, and pipeline documentation.

```
+---------------------------------------------------------------------------------------------------------+
| [ KPI 1: 41,418 Raw Rows ] [ KPI 2: 9,431 Deduplicated ] [ KPI 3: 4.39x Multiplier ] [ KPI 4: 0 Out Range ]|
+---------------------------------------------------------------------------------------------------------+
| Data Pipeline Architecture Flow (Raw CSV -> Silver Transformation -> Gold Dimensional Model)            |
+----------------------------------------------------+----------------------------------------------------+
| Dimensional Entity Integrity Summary               | Analytical Boundary Conditions & Governance Notes  |
| (Table Listing Row Counts & Storage Mode)          | (Governance Callout Card)                          |
+----------------------------------------------------+----------------------------------------------------+
```

### 6.1 Top Audit KPI Ribbon
* **Card 1 (Raw Ingestion):** Static Card $\rightarrow$ `41,418` (Label: `Raw Listing Rows Intake`)
* **Card 2 (Deduplication Proof):** `_Measures[Restaurant Count]` $\rightarrow$ `9,431` (Label: `Unique Canonical Restaurants`)
* **Card 3 (Category Multiplier):** `_Measures[Listing Types per Restaurant]` $\rightarrow$ `4.39×` (Label: `Listings per Restaurant`)
* **Card 4 (Sanity Validation):** `_Measures[QA Ratings Out Of Range]` $\rightarrow$ `0` (Label: `Ratings Out of Range (<1 or >5) — Pass`)

### 6.2 Visual 1 — Data Pipeline Architecture Flow
* Insert a **Shape / Smart Diagram** illustrating:
  $$\text{Raw Zomato CSV (41,418 rows)} \longrightarrow \text{Silver Layer (PySpark/URL Key Hashing)} \longrightarrow \text{Gold Layer (6 Dims + 1 Bridge + 1 Fact + 1 Mart)}$$

### 6.3 Visual 2 — Entity Integrity Audit Summary
* **Visual Type:** **Table**
* Display entity row counts:
  * `dim_restaurant`: **9,431 rows** (1:1 restaurant master)
  * `dim_location`: **92 rows**
  * `dim_cuisine`: **105 rows**
  * `dim_price_band`: **3 rows** (Budget, Mid-range, Premium)
  * `dim_restaurant_type`: **88 rows**
  * `dim_listing_type`: **14 rows**
  * `bridge_restaurant_cuisine`: **~20k rows**
  * `fact_restaurant_listing`: **41,357 rows**
  * `mart_market_opportunity`: **4,878 rows** (1,207 scored)

### 6.4 Visual 3 — Governance & Boundaries Callout
* **Visual Type:** **Text Box**
* **Content:**
  * *Single historical snapshot: does not represent longitudinal revenue growth or trend.*
  * *Review votes function as an engagement proxy, not transactional volume.*
  * *Deduplication logic: Always aggregate on `DISTINCTCOUNT(restaurant_key)`, never `COUNTROWS(fact)`.*

---

## ✅ Final Pre-Publish Validation Checklist

Before sharing or exporting the report, verify the following benchmarks:
1. `_Measures[Restaurant Count]` without any visual filters = **9,431**.
2. `_Measures[Listing Rows]` = **41,357**.
3. `_Measures[QA Ratings Out Of Range]` = **0**.
4. Slicer sync is active across Pages 1–5.
5. All surrogate key columns (`*_key`) remain hidden from user view.
6. `dim_price_band` is sorted by `price_band_sort` (Budget $\rightarrow$ Mid-range $\rightarrow$ Premium).
