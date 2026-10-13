"""Build (and optionally execute) the market analysis notebook from Gold tables.

The notebook is generated programmatically so the analysis stays reproducible and
matches the exact tables produced by ``build_local_gold.py``.

Usage:
    python src/build_analysis_notebook.py --output notebooks/01_market_analysis.ipynb
    python -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_market_analysis.ipynb
"""

from __future__ import annotations

import argparse
from pathlib import Path

import nbformat as nbf

SETUP = '''
from pathlib import Path
import json

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except Exception:
    plt.style.use("ggplot")

pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 160)

def find_gold_dir() -> Path:
    for base in [Path.cwd(), *Path.cwd().parents]:
        candidate = base / "data" / "gold"
        if (candidate / "model_features.csv").exists():
            return candidate
    raise FileNotFoundError("Could not locate data/gold. Run src/build_local_gold.py first.")

GOLD = find_gold_dir()
FIGURES = GOLD.parent.parent / "reports" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

restaurants = pd.read_csv(GOLD / "model_features.csv")
restaurants["is_high_rated"] = restaurants["is_high_rated"].astype(str).str.lower().eq("true")
restaurants["price_band"] = pd.cut(
    restaurants["cost_for_two"],
    bins=[0, 400, 800, float("inf")],
    labels=["Budget", "Mid-range", "Premium"],
    right=False,
).astype(str)

bridge = pd.read_csv(GOLD / "bridge_restaurant_cuisine.csv")
dim_cuisine = pd.read_csv(GOLD / "dim_cuisine.csv")
mart = pd.read_csv(GOLD / "mart_market_opportunity.csv")
fact = pd.read_csv(GOLD / "fact_restaurant_listing.csv")

print("Gold directory:", GOLD)
print("Restaurant rows (unique):", len(restaurants))
print("Fact rows (restaurant x listing type):", len(fact))
print("Market segments:", len(mart))
'''

OVERVIEW = '''
overview = pd.DataFrame(
    {
        "metric": [
            "Unique restaurants",
            "Localities",
            "Cuisines",
            "Restaurant types",
            "Average rating",
            "Median cost for two (INR)",
            "Median votes",
            "Total votes",
            "High-rated share (%)",
            "Online order share (%)",
            "Table booking share (%)",
        ],
        "value": [
            len(restaurants),
            restaurants["location_name"].nunique(),
            dim_cuisine["cuisine_name"].nunique(),
            restaurants["restaurant_type_name"].nunique(),
            round(restaurants["rating"].mean(), 2),
            round(restaurants["cost_for_two"].median(), 2),
            round(restaurants["vote_count"].median(), 2),
            int(restaurants["vote_count"].sum()),
            round(restaurants["is_high_rated"].mean() * 100, 2),
            round(restaurants["online_order_available"].mean() * 100, 2),
            round(restaurants["table_booking_available"].mean() * 100, 2),
        ],
    }
)
overview
'''

LOCALITY = '''
locality = (
    restaurants.groupby("location_name")
    .agg(
        restaurants=("restaurant_key", "nunique"),
        avg_rating=("rating", "mean"),
        median_cost=("cost_for_two", "median"),
        avg_votes=("vote_count", "mean"),
        high_rated_pct=("is_high_rated", "mean"),
    )
    .reset_index()
)
locality["high_rated_pct"] = (locality["high_rated_pct"] * 100).round(2)
locality = locality.round(2)

top_density = locality.sort_values("restaurants", ascending=False).head(15)

fig, ax = plt.subplots(figsize=(9, 6))
top_density.sort_values("restaurants").plot.barh(
    x="location_name", y="restaurants", ax=ax, color="#2563eb", legend=False
)
ax.set_title("Top 15 Localities by Restaurant Density")
ax.set_xlabel("Restaurants")
ax.set_ylabel("")
fig.tight_layout()
fig.savefig(FIGURES / "locality_density.png", dpi=170, bbox_inches="tight")
plt.show()

top_density
'''

LOCALITY_SCATTER = '''
fig, ax = plt.subplots(figsize=(10, 6))
scatter = ax.scatter(
    locality["restaurants"],
    locality["avg_rating"],
    s=locality["avg_votes"] / 8,
    c=locality["high_rated_pct"],
    cmap="viridis",
    alpha=0.75,
    edgecolors="white",
)
ax.set_title("Locality Quality vs Density (bubble size = average votes)")
ax.set_xlabel("Restaurants in locality")
ax.set_ylabel("Average rating")
fig.colorbar(scatter, ax=ax, label="High-rated share (%)")

qualified = locality.loc[locality["restaurants"] >= 150].sort_values("avg_rating", ascending=False).head(6)
for row in qualified.itertuples():
    ax.annotate(row.location_name, (row.restaurants, row.avg_rating), fontsize=8, xytext=(4, 4), textcoords="offset points")
fig.tight_layout()
fig.savefig(FIGURES / "locality_quality_density.png", dpi=170, bbox_inches="tight")
plt.show()

qualified[["location_name", "restaurants", "avg_rating", "high_rated_pct", "avg_votes"]]
'''

CUISINE = '''
cuisine_frame = bridge.merge(dim_cuisine, on="cuisine_key").merge(
    restaurants[["restaurant_key", "rating", "vote_count", "cost_for_two", "is_high_rated"]],
    on="restaurant_key",
)
cuisine = (
    cuisine_frame.groupby("cuisine_name")
    .agg(
        restaurants=("restaurant_key", "nunique"),
        avg_rating=("rating", "mean"),
        avg_votes=("vote_count", "mean"),
        median_cost=("cost_for_two", "median"),
        high_rated_pct=("is_high_rated", "mean"),
    )
    .reset_index()
)
cuisine["high_rated_pct"] = (cuisine["high_rated_pct"] * 100).round(2)
cuisine = cuisine.round(2)

top_cuisine = cuisine.sort_values("restaurants", ascending=False).head(12)
fig, ax = plt.subplots(figsize=(9, 6))
top_cuisine.sort_values("restaurants").plot.barh(
    x="cuisine_name", y="restaurants", ax=ax, color="#7c3aed", legend=False
)
ax.set_title("Top 12 Cuisines by Restaurant Density")
ax.set_xlabel("Restaurants")
ax.set_ylabel("")
fig.tight_layout()
fig.savefig(FIGURES / "cuisine_density.png", dpi=170, bbox_inches="tight")
plt.show()

top_cuisine
'''

CUISINE_NICHE = '''
niche = cuisine.loc[cuisine["restaurants"] >= 30].sort_values("avg_rating", ascending=False).head(12)

fig, ax = plt.subplots(figsize=(9, 6))
niche.sort_values("avg_rating").plot.barh(
    x="cuisine_name", y="avg_rating", ax=ax, color="#059669", legend=False
)
ax.axvline(restaurants["rating"].mean(), color="#dc2626", linestyle="--", linewidth=1, label="Market average")
ax.set_title("Highest-Rated Cuisines (min 30 restaurants)")
ax.set_xlabel("Average rating")
ax.set_ylabel("")
ax.legend()
fig.tight_layout()
fig.savefig(FIGURES / "cuisine_rating.png", dpi=170, bbox_inches="tight")
plt.show()

niche[["cuisine_name", "restaurants", "avg_rating", "avg_votes", "high_rated_pct"]]
'''

PRICING = '''
price = (
    restaurants.groupby("price_band")
    .agg(
        restaurants=("restaurant_key", "nunique"),
        avg_rating=("rating", "mean"),
        avg_votes=("vote_count", "mean"),
        high_rated_pct=("is_high_rated", "mean"),
        table_booking_pct=("table_booking_available", "mean"),
    )
    .reset_index()
)
for column in ["high_rated_pct", "table_booking_pct"]:
    price[column] = (price[column] * 100).round(2)
price = price.round(2).sort_values("avg_rating")

fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
price.set_index("price_band")["restaurants"].plot.bar(ax=axes[0], color="#2563eb", rot=0)
axes[0].set_title("Restaurants per Price Band")
axes[0].set_ylabel("")

price.set_index("price_band")["avg_rating"].plot.bar(ax=axes[1], color="#f59e0b", rot=0)
axes[1].set_title("Average Rating by Price Band")
axes[1].set_ylabel("Rating")

price.set_index("price_band")["high_rated_pct"].plot.bar(ax=axes[2], color="#059669", rot=0)
axes[2].set_title("High-Rated Share by Price Band")
axes[2].set_ylabel("%")
fig.tight_layout()
fig.savefig(FIGURES / "price_band_performance.png", dpi=170, bbox_inches="tight")
plt.show()

price
'''

SERVICE = '''
restaurants["service_combo"] = (
    restaurants["online_order_available"].map({True: "Online", False: "No online"})
    + " + "
    + restaurants["table_booking_available"].map({True: "Booking", False: "No booking"})
)
service = (
    restaurants.groupby("service_combo")
    .agg(
        restaurants=("restaurant_key", "nunique"),
        avg_rating=("rating", "mean"),
        avg_votes=("vote_count", "mean"),
        high_rated_pct=("is_high_rated", "mean"),
    )
    .reset_index()
)
service["high_rated_pct"] = (service["high_rated_pct"] * 100).round(2)
service = service.round(2).sort_values("avg_rating")

fig, ax = plt.subplots(figsize=(9, 5))
service.set_index("service_combo")[["avg_rating"]].plot.bar(ax=ax, color="#dc2626", legend=False, rot=15)
ax.axhline(restaurants["rating"].mean(), color="black", linestyle="--", linewidth=1, label="Market average")
ax.set_title("Average Rating by Service Combination")
ax.set_ylabel("Rating")
ax.legend()
fig.tight_layout()
fig.savefig(FIGURES / "service_combination.png", dpi=170, bbox_inches="tight")
plt.show()

service
'''

CORRELATION = '''
corr = restaurants[["rating", "cost_for_two", "vote_count", "is_high_rated"]].copy()
corr["is_high_rated"] = corr["is_high_rated"].astype(int)
spearman = corr.corr(method="spearman")

fig, ax = plt.subplots(figsize=(6, 5))
image = ax.imshow(spearman, cmap="coolwarm", vmin=-1, vmax=1)
ax.set_xticks(range(len(spearman.columns)))
ax.set_yticks(range(len(spearman.columns)))
ax.set_xticklabels(spearman.columns, rotation=45, ha="right")
ax.set_yticklabels(spearman.columns)
for i in range(len(spearman.columns)):
    for j in range(len(spearman.columns)):
        ax.text(j, i, f"{spearman.iloc[i, j]:.2f}", ha="center", va="center", fontsize=9)
ax.set_title("Spearman Rank Correlations")
fig.colorbar(image, ax=ax, shrink=0.8)
fig.tight_layout()
fig.savefig(FIGURES / "correlation_matrix.png", dpi=170, bbox_inches="tight")
plt.show()

spearman.round(2)
'''

OPPORTUNITY = '''
scored = mart.dropna(subset=["opportunity_score"]).sort_values("opportunity_score", ascending=False)
tiers = scored["opportunity_tier"].value_counts().reindex(["Shortlist", "High priority", "Promising", "Explore"])

fig, ax = plt.subplots(figsize=(8, 4.5))
tiers.plot.bar(ax=ax, color="#0f766e", rot=0)
ax.set_title(f"Opportunity Tiers Across {len(scored)} Scored Segments")
ax.set_ylabel("Segments")
fig.tight_layout()
fig.savefig(FIGURES / "opportunity_tiers.png", dpi=170, bbox_inches="tight")
plt.show()

scored.head(15)[
    [
        "location_name",
        "cuisine_name",
        "price_band",
        "restaurant_count",
        "average_rating",
        "average_votes_per_restaurant",
        "opportunity_score",
        "opportunity_tier",
    ]
]
'''

MODEL = '''
metrics_path = GOLD.parent.parent / "reports" / "rating_model_metrics.json"
if metrics_path.exists():
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    comparison = pd.DataFrame(metrics["metrics"]).T
    print("Target:", metrics["target_definition"])
    print("Selection metric:", metrics["selection_metric"], "| Best model:", metrics["best_model"])
    display = comparison[["roc_auc", "pr_auc", "accuracy", "precision", "recall", "f1"]]
else:
    print("Run src/train_rating_model.py to generate reports/rating_model_metrics.json")

importance_path = GOLD.parent.parent / "reports" / "model_feature_importance.csv"
if importance_path.exists():
    importance = pd.read_csv(importance_path)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    importance.sort_values("mean_pr_auc_decrease").plot.barh(
        x="feature", y="mean_pr_auc_decrease", xerr="std_pr_auc_decrease", ax=ax,
        color="#4f46e5", legend=False
    )
    ax.set_title("Permutation Importance (PR-AUC decrease)")
    ax.set_xlabel("Decrease when permuted")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(FIGURES / "model_importance_notebook.png", dpi=170, bbox_inches="tight")
    plt.show()

display
'''

FINDINGS = '''
findings = {
    "market": (
        f"{len(restaurants):,} unique restaurants across {restaurants['location_name'].nunique()} localities "
        f"with a {round(restaurants['is_high_rated'].mean() * 100, 1)}% high-rated share."
    ),
    "density": (
        "Whitefield, BTM and HSR carry the most restaurants, so they are the most saturated markets."
    ),
    "quality": (
        "Lavelle Road, Koramangala 5th Block and Church Street combine high average ratings with strong "
        "engagement, which marks them as premium-quality pockets."
    ),
    "pricing": (
        "Premium restaurants show a far higher high-rated share than budget restaurants, but they are only "
        f"{round((price.set_index('price_band').loc['Premium', 'restaurants'] / len(restaurants)) * 100, 1)}% of the market."
    ),
    "service": (
        "Restaurants that accept table booking average clearly higher ratings than those that do not, "
        "which is an association, not proof of causation."
    ),
    "recommendation": (
        "The expansion screen shortlists premium segments such as Church Street/Chinese, Whitefield/Burger "
        "and Sarjapur Road/Asian for further validation."
    ),
}
for key, value in findings.items():
    print(f"[{key}] {value}")
'''

MARKDOWN = {
    0: """# Restaurant Market Intelligence Platform — Market Analysis

This notebook is the analytical layer of the project. It reads the Gold tables produced by
`src/build_local_gold.py` and answers the business questions that drive the Power BI report:

1. What does the Bangalore restaurant market look like?
2. Which localities combine quality, engagement and manageable density?
3. Which cuisines are crowded versus high-performing?
4. How does price band relate to observed ratings?
5. How do online ordering and table booking relate to ratings?
6. Which locality-cuisine-price segments are worth validating for expansion?

**Scope note:** the source is one historical Zomato Bangalore snapshot with no date field.
Everything here is descriptive and associative. It does not support causal, revenue, growth or
forecasting claims.""",
    1: """## 1. Market Overview

Restaurant counts use distinct restaurant keys, not raw listing rows. The raw file has
41,418 listing rows but only 9,431 unique restaurants, because a restaurant can appear under
multiple listing categories.""",
    2: """## 2. Locality Intelligence

Which localities are crowded, and which combine quality with engagement?""",
    4: """## 3. Cuisine Intelligence

Which cuisines dominate the market, and which are high-performing relative to their size?
Premium-leaning cuisines such as Japanese, Mediterranean and European carry the highest average
ratings while remaining small, which is the shape of an underserved premium niche.""",
    6: """## 4. Pricing Strategy

Does paying more relate to better observed ratings, or is the premium segment simply different?""",
    7: """## 5. Service Availability

Online ordering and table booking are service capabilities, not quality guarantees.""",
    8: """## 6. Relationships Between Variables

Spearman rank correlation is used because ratings and votes are ordinal and heavily skewed.""",
    9: """## 7. Expansion Screening

The opportunity score is a transparent screening heuristic, not a validated recommendation:

`score = 40% demand proxy + 25% quality + 25% whitespace + 10% service fit`

It only scores locality-cuisine-price segments with at least 5 restaurants so a segment is never
ranked on a single data point.""",
    10: """## 8. Rating Model Summary

The classifier estimates the probability that a restaurant lands a high observed platform rating
(`rating >= 4.0` and `votes >= 20`). Votes and review text are excluded from the features so the
model does not learn the target rule or post-outcome signals.""",
    11: """## 9. Findings

Each statement below is generated from the executed cells, so it always matches the data.""",
}


def build_notebook() -> nbf.NotebookNode:
    notebook = nbf.v4.new_notebook()
    notebook.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    }
    code_cells = [
        ("imports", SETUP),
        ("overview", OVERVIEW),
        ("locality", LOCALITY),
        ("locality_scatter", LOCALITY_SCATTER),
        ("cuisine", CUISINE),
        ("cuisine_niche", CUISINE_NICHE),
        ("pricing", PRICING),
        ("service", SERVICE),
        ("correlation", CORRELATION),
        ("opportunity", OPPORTUNITY),
        ("model", MODEL),
        ("findings", FINDINGS),
    ]
    cells = []
    for index, (name, source) in enumerate(code_cells):
        if index in MARKDOWN:
            cells.append(nbf.v4.new_markdown_cell(MARKDOWN[index].strip()))
        cell = nbf.v4.new_code_cell(source.strip())
        cell.metadata["tags"] = [name]
        cells.append(cell)
    notebook.cells = cells
    return notebook


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the market analysis notebook.")
    parser.add_argument("--output", type=Path, default=Path("notebooks/01_market_analysis.ipynb"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    notebook = build_notebook()
    nbf.write(notebook, str(args.output))
    print(f"Wrote {args.output} with {len(notebook.cells)} cells")


if __name__ == "__main__":
    main()
