"""Build local Power BI-ready Gold tables from the Zomato source snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


SOURCE_COLUMNS = [
    "url",
    "address",
    "name",
    "online_order",
    "book_table",
    "votes",
    "location",
    "rest_type",
    "cuisines",
    "listed_in(type)",
    "listed_in(city)",
    "rate_clean",
    "cost_clean",
]


def key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.replace(r"\s+", " ", regex=True)


def write_csv(frame: pd.DataFrame, name: str, output_dir: Path) -> None:
    frame.to_csv(output_dir / f"{name}.csv", index=False, encoding="utf-8")


def build(input_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(input_path, usecols=SOURCE_COLUMNS, low_memory=False)
    raw["canonical_url"] = normalize_text(raw["url"]).str.replace(r"\?.*$", "", regex=True)
    raw["restaurant_key"] = raw["canonical_url"].map(key)
    raw["restaurant_name"] = normalize_text(raw["name"])
    raw["restaurant_address"] = normalize_text(raw["address"])
    raw["location_name"] = normalize_text(raw["location"]).str.title()
    raw["restaurant_type_name"] = normalize_text(raw["rest_type"]).replace("", "Unknown").str.title()
    raw["listing_type_name"] = normalize_text(raw["listed_in(type)"]).str.title()
    raw["listing_city_name"] = normalize_text(raw["listed_in(city)"]).str.title()
    raw["rating"] = pd.to_numeric(raw["rate_clean"], errors="coerce")
    raw["cost_for_two"] = pd.to_numeric(raw["cost_clean"], errors="coerce")
    raw["vote_count"] = pd.to_numeric(raw["votes"], errors="coerce")
    raw["online_order_available"] = normalize_text(raw["online_order"]).str.lower().eq("yes")
    raw["table_booking_available"] = normalize_text(raw["book_table"]).str.lower().eq("yes")

    valid = raw.loc[
        raw["rating"].between(1, 5)
        & raw["cost_for_two"].gt(0)
        & raw["vote_count"].ge(0)
        & raw["location_name"].ne("")
    ].copy()
    valid["price_band"] = pd.cut(
        valid["cost_for_two"],
        bins=[0, 400, 800, float("inf")],
        labels=["Budget", "Mid-range", "Premium"],
        right=False,
    ).astype(str)
    valid["is_high_rated"] = valid["rating"].ge(4.0) & valid["vote_count"].ge(20)
    valid["location_key"] = valid["location_name"].map(key)
    valid["restaurant_type_key"] = valid["restaurant_type_name"].map(key)
    valid["listing_type_key"] = (
        valid["listing_type_name"] + "||" + valid["listing_city_name"]
    ).map(key)

    dim_restaurant = (
        valid.sort_values("restaurant_key")
        .drop_duplicates("restaurant_key")
        [["restaurant_key", "canonical_url", "restaurant_name", "restaurant_address"]]
    )
    dim_location = valid[["location_key", "location_name"]].drop_duplicates().sort_values("location_name")
    dim_restaurant_type = (
        valid[["restaurant_type_key", "restaurant_type_name"]]
        .drop_duplicates()
        .sort_values("restaurant_type_name")
    )
    dim_price_band = pd.DataFrame(
        {"price_band": ["Budget", "Mid-range", "Premium"], "price_band_sort": [1, 2, 3]}
    )
    dim_listing_type = (
        valid[["listing_type_key", "listing_type_name", "listing_city_name"]]
        .drop_duplicates()
        .sort_values(["listing_type_name", "listing_city_name"])
    )

    cuisine_rows = valid[["restaurant_key", "cuisines"]].copy()
    cuisine_rows["cuisine_name"] = cuisine_rows["cuisines"].fillna("").str.split(",")
    cuisine_rows = cuisine_rows.explode("cuisine_name")
    cuisine_rows["cuisine_name"] = normalize_text(cuisine_rows["cuisine_name"]).str.title()
    cuisine_rows = cuisine_rows.loc[cuisine_rows["cuisine_name"].ne("")]
    cuisine_rows["cuisine_key"] = cuisine_rows["cuisine_name"].map(key)
    dim_cuisine = cuisine_rows[["cuisine_key", "cuisine_name"]].drop_duplicates().sort_values("cuisine_name")
    bridge_restaurant_cuisine = cuisine_rows[["restaurant_key", "cuisine_key"]].drop_duplicates()

    fact_group = [
        "restaurant_key",
        "location_key",
        "restaurant_type_key",
        "listing_type_key",
        "price_band",
    ]
    fact_restaurant_listing = (
        valid.groupby(fact_group, as_index=False)
        .agg(
            rating=("rating", "max"),
            vote_count=("vote_count", "max"),
            cost_for_two=("cost_for_two", "max"),
            online_order_available=("online_order_available", "max"),
            table_booking_available=("table_booking_available", "max"),
            is_high_rated=("is_high_rated", "max"),
        )
        .sort_values(fact_group)
    )

    market_base = (
        fact_restaurant_listing.merge(dim_location, on="location_key")
        .merge(bridge_restaurant_cuisine, on="restaurant_key")
        .merge(dim_cuisine, on="cuisine_key")
    )
    mart_market_opportunity = (
        market_base.groupby(["location_name", "cuisine_name", "price_band"], as_index=False)
        .agg(
            restaurant_count=("restaurant_key", "nunique"),
            average_rating=("rating", "mean"),
            average_cost_for_two=("cost_for_two", "mean"),
            average_votes_per_restaurant=("vote_count", "mean"),
            online_order_rate_pct=("online_order_available", "mean"),
            table_booking_rate_pct=("table_booking_available", "mean"),
            trusted_high_rated_share_pct=("is_high_rated", "mean"),
        )
        .round(2)
    )
    for column in ["online_order_rate_pct", "table_booking_rate_pct", "trusted_high_rated_share_pct"]:
        mart_market_opportunity[column] = (mart_market_opportunity[column] * 100).round(2)

    eligible = mart_market_opportunity["restaurant_count"].ge(5)
    opportunity = mart_market_opportunity.loc[eligible].copy()
    opportunity["demand_proxy_score"] = opportunity["average_votes_per_restaurant"].rank(pct=True)
    opportunity["quality_score"] = opportunity["average_rating"].rank(pct=True)
    opportunity["whitespace_score"] = 1 - opportunity["restaurant_count"].rank(pct=True)
    opportunity["service_fit_score"] = opportunity["online_order_rate_pct"].rank(pct=True)
    opportunity["opportunity_score"] = (
        100
        * (
            0.40 * opportunity["demand_proxy_score"]
            + 0.25 * opportunity["quality_score"]
            + 0.25 * opportunity["whitespace_score"]
            + 0.10 * opportunity["service_fit_score"]
        )
    ).round(1)
    opportunity["opportunity_tier"] = pd.cut(
        opportunity["opportunity_score"],
        bins=[-1, 50, 70, 85, 100],
        labels=["Explore", "Promising", "High priority", "Shortlist"],
    ).astype(str)
    mart_market_opportunity = mart_market_opportunity.merge(
        opportunity[
            [
                "location_name",
                "cuisine_name",
                "price_band",
                "opportunity_score",
                "opportunity_tier",
            ]
        ],
        on=["location_name", "cuisine_name", "price_band"],
        how="left",
    ).sort_values("opportunity_score", ascending=False, na_position="last")

    model_features = (
        valid.sort_values("restaurant_key")
        .drop_duplicates("restaurant_key")
        [[
            "restaurant_key",
            "rating",
            "vote_count",
            "cost_for_two",
            "location_name",
            "restaurant_type_name",
            "online_order_available",
            "table_booking_available",
            "cuisines",
            "is_high_rated",
        ]]
    )

    tables = {
        "dim_restaurant": dim_restaurant,
        "dim_location": dim_location,
        "dim_restaurant_type": dim_restaurant_type,
        "dim_price_band": dim_price_band,
        "dim_listing_type": dim_listing_type,
        "dim_cuisine": dim_cuisine,
        "bridge_restaurant_cuisine": bridge_restaurant_cuisine,
        "fact_restaurant_listing": fact_restaurant_listing,
        "mart_market_opportunity": mart_market_opportunity,
        "model_features": model_features,
    }
    for name, frame in tables.items():
        write_csv(frame, name, output_dir)

    summary = {
        "source_rows": int(len(raw)),
        "valid_listing_rows": int(len(valid)),
        "unique_restaurants": int(dim_restaurant["restaurant_key"].nunique()),
        "fact_rows": int(len(fact_restaurant_listing)),
        "cuisines": int(len(dim_cuisine)),
        "market_segments": int(len(mart_market_opportunity)),
        "scored_market_segments": int(mart_market_opportunity["opportunity_score"].notna().sum()),
    }
    (output_dir / "gold_build_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build local Gold CSV tables.")
    parser.add_argument("--input", type=Path, default=Path("zomato_cleaned.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/gold"))
    args = parser.parse_args()
    summary = build(args.input, args.output_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
