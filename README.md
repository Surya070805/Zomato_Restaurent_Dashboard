# 🍽️ Zomato Restaurant Analytics & Recommendation System

## 📌 Overview

This project delivers an end-to-end data solution combining **Big Data processing, Machine Learning, and Business Intelligence** to extract actionable insights from Zomato’s Bangalore restaurant dataset.

The objective is to analyze restaurant performance and predict factors that contribute to **high customer ratings (≥ 4.0)**, enabling data-driven decision-making in the food and hospitality domain.

---
## 📸 Dashboard Preview

<img width="1182" height="662" alt="image" src="https://github.com/user-attachments/assets/4ba87b5b-1cba-4746-97cd-71c9f2b76fc7" />
---

## 🎯 Objectives

* Analyze restaurant distribution across Bangalore locations
* Identify factors influencing high ratings
* Predict whether a restaurant will achieve a rating ≥ 4.0
* Build an interactive dashboard for business insights
* Enable location- and cuisine-based decision support

---

## 🗂️ Dataset

The dataset is sourced from Kaggle:

🔗 https://www.kaggle.com/datasets/suryamitra/zomato-bangalore-restaurent-datasets

### Key Features:

* Restaurant name, location, and category
* Cuisines offered (multi-valued)
* Ratings and number of votes
* Approximate cost for two
* Online ordering and table booking availability

---

## ⚙️ Tech Stack

* **PySpark (Databricks):** Big data processing and ETL
* **Scikit-learn:** Machine learning modeling
* **Power BI:** Data visualization and dashboarding

---

## 🧱 Project Architecture

```
Raw Data (CSV ~600MB)
        ↓
PySpark ETL (Cleaning + Feature Engineering)
        ↓
Processed Dataset
        ↓
Machine Learning Model (Classification)
        ↓
Power BI Dashboard (Insights & Visualization)
```

---

## 🔧 Data Engineering (PySpark)

* Processed a **600MB dataset** using distributed computing
* Cleaned and transformed raw fields:

  * Extracted numerical ratings using regex
  * Converted cost fields to numeric format
* Engineered features:

  * Service availability (online order, table booking)
  * Location-based aggregation
* Generated a clean dataset for downstream analytics

---

## 🤖 Machine Learning

### Problem:

Predict whether a restaurant will receive a **high rating (≥ 4.0)**

### Approach:

* Feature selection: cost, location, services, categories
* Data preprocessing:

  * Handling missing values
  * Encoding categorical variables
* Model: Classification (e.g., Random Forest / Logistic Regression)

### Outcome:

* Identified key drivers of high ratings:

  * Online ordering availability
  * Table booking support
  * Location and cuisine diversity

---

## 📊 Power BI Dashboard

An interactive dashboard was developed to provide business insights.

### Key Metrics:

* Total Restaurants
* Average Rating
* Total Votes
* Number of Cuisines

### Features:

* Location-based filtering (e.g., Indiranagar, HSR Layout)
* Cuisine and restaurant type drill-down
* Online ordering and table booking distribution

### Insights:

* High-rated restaurants are more likely to offer **online ordering and booking services**
* Certain locations exhibit **higher engagement and cuisine diversity**
* Customer votes strongly correlate with restaurant ratings

---

## 📈 Key Business Insights

* Restaurants with both **online ordering and table booking** tend to achieve higher ratings
* High-density locations offer **greater cuisine variety and customer engagement**
* Customer voting behavior is a strong indicator of restaurant popularity

---

## 🚀 Future Improvements

* Add recommendation system for optimal location + cuisine selection
* Incorporate advanced models (XGBoost, Gradient Boosting)
* Deploy as a web-based analytics application
* Integrate real-time data pipelines

---

## 📂 Repository Structure

```
├── Zomato Big Data Analysis.py        # PySpark ETL pipeline
├── Zomato_Predictive_analysis.ipynb  # Machine Learning model
├── Zomato insights.pbix             # Power BI dashboard
├── zomato_dashboard.png             # Dashboard preview
├── README.md
```

---

## 🧠 Key Learnings

* Handling large-scale datasets using distributed systems
* Feature engineering for real-world business problems
* Bridging data engineering, ML, and BI into one pipeline
* Translating data insights into actionable business decisions

---

## 👤 Author

**Surya**

---

## ⭐ If you found this project useful, consider giving it a star!
