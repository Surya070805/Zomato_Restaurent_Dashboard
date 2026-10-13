"""Generate business-facing market insights from the Gold tables.

Reads the restaurant-level and mart tables built by ``build_local_gold.py`` and
writes machine-readable and human-readable insight reports. Every number quoted
in the project documentation comes from this script so no claim is invented.

Usage:
    python src/market_insights.py --gold-dir data/gold --output-dir reports
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def pct(value: float) -> float:
    return round(float(value) * 100, 2)


def r2(value: float) -> float:
    return round(float(value), 2)


def table_markdown(frame: pd.DataFrame) -> str:
    """Render a DataFrame as a markdown table without extra dependencies."""
    columns = [str(column) for column in frame.columns]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for record in frame.itertuples(index=False):
        rows.append("| " + " | ".join("" if pd.isna(value) else str(value) for value in record) + " |")
    return "\n".join([header, separator, *rows])


def build_insights(gold_dir: Path) -> dict:
    restaurants = pd.read_csv(gold_dir / "model_features.csv")
    restaurants["is_high_rated"] = restaurants["is_high_rated"].astype(str).str.lower().eq("true")
    # model_features.csv is restaurant grain and omits the price band, so apply
    # the same documented rule used in build_local_gold.py.
    restaurants["price_band"] = pd.cut(
        restaurants["cost_for_two"],
        bins=[0, 400, 800, float("inf")],
        labels=["Budget", "Mid-range", "Premium"],
        right=False,
    ).astype(str)

    bridge = pd.read_csv(gold_dir / "bridge_restaurant_cuisine.csv")
    cuisine_names = pd.read_csv(gold_dir / "dim_cuisine.csv")
    mart = pd.read_csv(gold_dir / "mart_market_opportunity.csv")

    cuisine_frame = bridge.merge(cuisine_names, on="cuisine_key")

    insights: dict = {}

    # ---------------------------------------------------------------- overview
    insights["overview"] = {
        "unique_restaurants": int(len(restaurants)),
        "localities": int(restaurants["location_name"].nunique()),
        "cuisines": int(cuisine_names["cuisine_name"].nunique()),
        "restaurant_types": int(restaurants["restaurant_type_name"].nunique()),
        "average_rating": r2(restaurants["rating"].mean()),
        "median_cost_for_two": r2(restaurants["cost_for_two"].median()),
        "median_votes": r2(restaurants["vote_count"].median()),
        "total_votes": int(restaurants["vote_count"].sum()),
        "high_rated_share_pct": pct(restaurants["is_high_rated"].mean()),
        "online_order_share_pct": pct(restaurants["online_order_available"].mean()),
        "table_booking_share_pct": pct(restaurants["table_booking_available"].mean()),
    }

    # ---------------------------------------------------------------- locality
    locality = (
        restaurants.groupby("location_name")
        .agg(
            restaurant_count=("restaurant_key", "nunique"),
            average_rating=("rating", "mean"),
            median_cost_for_two=("cost_for_two", "median"),
            average_votes=("vote_count", "mean"),
            high_rated_share=("is_high_rated", "mean"),
        )
        .reset_index()
    )
    locality["high_rated_share_pct"] = (locality["high_rated_share"] * 100).round(2)
    locality = locality.round(2)
    top_dense = locality.sort_values("restaurant_count", ascending=False).head(15)
    insights["top_localities_by_density"] = top_dense[
        ["location_name", "restaurant_count", "average_rating", "median_cost_for_two", "average_votes", "high_rated_share_pct"]
    ].to_dict("records")

    qualified = locality.loc[locality["restaurant_count"] >= 50]
    top_quality = qualified.sort_values("average_rating", ascending=False).head(15)
    insights["top_localities_by_rating_min50"] = top_quality[
        ["location_name", "restaurant_count", "average_rating", "high_rated_share_pct", "average_votes"]
    ].to_dict("records")

    # ---------------------------------------------------------------- cuisine
    cuisine = (
        cuisine_frame.groupby("cuisine_name")
        .agg(
            restaurant_count=("restaurant_key", "nunique"),
        )
        .reset_index()
    )
    cuisine_quality = (
        cuisine_frame.merge(
            restaurants[["restaurant_key", "rating", "vote_count", "cost_for_two", "is_high_rated"]],
            on="restaurant_key",
        )
        .groupby("cuisine_name")
        .agg(
            restaurant_count=("restaurant_key", "nunique"),
            average_rating=("rating", "mean"),
            average_votes=("vote_count", "mean"),
            median_cost_for_two=("cost_for_two", "median"),
            high_rated_share=("is_high_rated", "mean"),
        )
        .reset_index()
    )
    cuisine_quality["high_rated_share_pct"] = (cuisine_quality["high_rated_share"] * 100).round(2)
    cuisine_quality = cuisine_quality.round(2)
    top_cuisine_density = cuisine_quality.sort_values("restaurant_count", ascending=False).head(15)
    insights["top_cuisines_by_density"] = top_cuisine_density[
        ["cuisine_name", "restaurant_count", "average_rating", "high_rated_share_pct"]
    ].to_dict("records")

    niche_cuisine = cuisine_quality.loc[cuisine_quality["restaurant_count"] >= 30].sort_values(
        "average_rating", ascending=False
    ).head(15)
    insights["top_cuisines_by_rating_min30"] = niche_cuisine[
        ["cuisine_name", "restaurant_count", "average_rating", "average_votes", "high_rated_share_pct"]
    ].to_dict("records")

    # cuisine concentration: share of distinct restaurants serving any of the top 5
    # cuisines. Counts are distinct restaurants, not summed cuisine rows, because a
    # restaurant serving two top cuisines would otherwise be counted twice.
    cuisine_sorted = cuisine_quality.sort_values("restaurant_count", ascending=False)
    top5_names = cuisine_sorted.head(5)["cuisine_name"].tolist()
    top5_keys = cuisine_names.loc[cuisine_names["cuisine_name"].isin(top5_names), "cuisine_key"]
    top5_restaurants = bridge.loc[bridge["cuisine_key"].isin(top5_keys), "restaurant_key"].nunique()
    insights["top5_cuisine_share_pct"] = pct(top5_restaurants / len(restaurants))
    insights["top5_cuisines"] = top5_names
    insights["top5_cuisine_restaurants"] = int(top5_restaurants)

    # ---------------------------------------------------------------- pricing
    price = (
        restaurants.groupby("price_band")
        .agg(
            restaurant_count=("restaurant_key", "nunique"),
            average_rating=("rating", "mean"),
            average_votes=("vote_count", "mean"),
            high_rated_share=("is_high_rated", "mean"),
            table_booking_share=("table_booking_available", "mean"),
            online_order_share=("online_order_available", "mean"),
        )
        .reset_index()
    )
    price["share_pct"] = (price["restaurant_count"] / len(restaurants) * 100).round(2)
    for column in ["high_rated_share", "table_booking_share", "online_order_share"]:
        price[column + "_pct"] = (price[column] * 100).round(2)
    price = price.round(2)
    price["order"] = price["price_band"].map({"Budget": 1, "Mid-range": 2, "Premium": 3})
    price = price.sort_values("order")
    insights["price_bands"] = price[
        [
            "price_band",
            "restaurant_count",
            "share_pct",
            "average_rating",
            "average_votes",
            "high_rated_share_pct",
            "table_booking_share_pct",
            "online_order_share_pct",
        ]
    ].to_dict("records")

    # ---------------------------------------------------------------- service
    restaurants["service_combo"] = (
        restaurants["online_order_available"].map({True: "Online", False: "No online"})
        + " + "
        + restaurants["table_booking_available"].map({True: "Booking", False: "No booking"})
    )
    service = (
        restaurants.groupby("service_combo")
        .agg(
            restaurant_count=("restaurant_key", "nunique"),
            average_rating=("rating", "mean"),
            average_votes=("vote_count", "mean"),
            high_rated_share=("is_high_rated", "mean"),
        )
        .reset_index()
    )
    service["share_pct"] = (service["restaurant_count"] / len(restaurants) * 100).round(2)
    service["high_rated_share_pct"] = (service["high_rated_share"] * 100).round(2)
    service = service.round(2).sort_values("average_rating", ascending=False)
    insights["service_combinations"] = service[
        ["service_combo", "restaurant_count", "share_pct", "average_rating", "average_votes", "high_rated_share_pct"]
    ].to_dict("records")

    # ---------------------------------------------------------------- relationships
    corr_frame = restaurants[["rating", "cost_for_two", "vote_count"]].copy()
    correlations = {
        "rating_vs_cost": r2(corr_frame["rating"].corr(corr_frame["cost_for_two"], method="spearman")),
        "rating_vs_votes": r2(corr_frame["rating"].corr(corr_frame["vote_count"], method="spearman")),
        "cost_vs_votes": r2(corr_frame["cost_for_two"].corr(corr_frame["vote_count"], method="spearman")),
    }
    insights["spearman_correlations"] = correlations

    # ---------------------------------------------------------------- opportunity
    scored = mart.dropna(subset=["opportunity_score"]).sort_values("opportunity_score", ascending=False)
    insights["opportunity_segments_total"] = int(len(mart))
    insights["opportunity_segments_scored"] = int(len(scored))
    insights["top_opportunity_segments"] = scored.head(15)[
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
    ].to_dict("records")
    insights["opportunity_tier_counts"] = (
        scored["opportunity_tier"].value_counts().to_dict()
    )
    insights["top_shortlist_localities"] = (
        scored.loc[scored["opportunity_tier"].isin(["Shortlist", "High priority"]), "location_name"]
        .value_counts()
        .head(10)
        .to_dict()
    )

    return insights


def write_reports(insights: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "market_insights.json").write_text(json.dumps(insights, indent=2), encoding="utf-8")

    overview = insights["overview"]
    lines: list[str] = []
    lines.append("# Market Insights")
    lines.append("")
    lines.append("Generated automatically from the Gold tables by `src/market_insights.py`.")
    lines.append("All values are descriptive statistics from one historical Zomato Bangalore snapshot.")
    lines.append("")
    lines.append("## Market Overview")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | ---: |")
    for label, key in [
        ("Unique restaurants", "unique_restaurants"),
        ("Localities", "localities"),
        ("Cuisines", "cuisines"),
        ("Restaurant types", "restaurant_types"),
        ("Average rating", "average_rating"),
        ("Median cost for two (INR)", "median_cost_for_two"),
        ("Median votes", "median_votes"),
        ("Total votes", "total_votes"),
        ("High-rated share (%)", "high_rated_share_pct"),
        ("Online order share (%)", "online_order_share_pct"),
        ("Table booking share (%)", "table_booking_share_pct"),
    ]:
        lines.append(f"| {label} | {overview[key]} |")

    sections = [
        ("Top Localities By Restaurant Density", "top_localities_by_density"),
        ("Top Localities By Average Rating (min 50 restaurants)", "top_localities_by_rating_min50"),
        ("Top Cuisines By Restaurant Density", "top_cuisines_by_density"),
        ("Top Cuisines By Average Rating (min 30 restaurants)", "top_cuisines_by_rating_min30"),
        ("Price Band Performance", "price_bands"),
        ("Service Combination Performance", "service_combinations"),
    ]
    for title, key in sections:
        lines.append("")
        lines.append(f"## {title}")
        lines.append("")
        lines.append(table_markdown(pd.DataFrame(insights[key])))

    lines.append("")
    lines.append("## Cuisine Concentration")
    lines.append("")
    lines.append(
        f"{insights['top5_cuisine_restaurants']} distinct restaurants "
        f"({insights['top5_cuisine_share_pct']}% of all restaurants) serve at least one of the top 5 "
        f"cuisines ({', '.join(insights['top5_cuisines'])}), confirming the market skews to a few "
        "high-volume cuisines."
    )

    lines.append("")
    lines.append("## Rank Correlations (Spearman)")
    lines.append("")
    lines.append("| Pair | Correlation |")
    lines.append("| --- | ---: |")
    labels = {
        "rating_vs_cost": "Rating vs Cost for two",
        "rating_vs_votes": "Rating vs Votes",
        "cost_vs_votes": "Cost for two vs Votes",
    }
    for key, label in labels.items():
        lines.append(f"| {label} | {insights['spearman_correlations'][key]} |")

    lines.append("")
    lines.append("## Expansion Screening")
    lines.append("")
    lines.append(
        f"{insights['opportunity_segments_scored']} of {insights['opportunity_segments_total']} "
        "locality-cuisine-price segments had at least 5 restaurants and received an opportunity score."
    )
    lines.append("")
    lines.append("### Top 15 Opportunity Segments")
    lines.append("")
    lines.append(table_markdown(pd.DataFrame(insights["top_opportunity_segments"])))
    lines.append("")
    lines.append(
        "The score is a transparent screening heuristic (demand proxy 40%, quality 25%, "
        "whitespace 25%, service fit 10%), not a validated investment recommendation."
    )
    lines.append("")

    (output_dir / "market_insights.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate market insight reports.")
    parser.add_argument("--gold-dir", type=Path, default=Path("data/gold"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()
    insights = build_insights(args.gold_dir)
    write_reports(insights, args.output_dir)
    print(json.dumps(insights["overview"], indent=2))


if __name__ == "__main__":
    main()
