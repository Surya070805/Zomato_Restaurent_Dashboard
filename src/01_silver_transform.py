"""Databricks PySpark job for the cleaned, typed Zomato Silver layer.

Run after uploading the source CSV to a Databricks volume or DBFS. Set the
input and output paths in the job parameters; the default paths are examples.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def clean_yes_no(column: str) -> F.Column:
    return (
        F.when(F.lower(F.trim(F.col(column))) == "yes", F.lit(True))
        .when(F.lower(F.trim(F.col(column))) == "no", F.lit(False))
        .otherwise(F.lit(None).cast("boolean"))
    )


def transform(raw: DataFrame) -> DataFrame:
    """Keep listing grain while creating typed, reusable fields."""
    canonical_url = F.regexp_replace(F.trim(F.col("url")), r"\\?.*$", "")
    cleaned = (
        raw.select(*[F.trim(F.col(column)).alias(column) for column in raw.columns])
        .withColumn("canonical_url", canonical_url)
        .withColumn("restaurant_key", F.sha2(F.col("canonical_url"), 256))
        .withColumn("rate_value", F.col("rate_clean").cast("double"))
        .withColumn("cost_for_two", F.col("cost_clean").cast("double"))
        .withColumn("vote_count", F.col("votes").cast("long"))
        .withColumn("online_order_available", clean_yes_no("online_order"))
        .withColumn("table_booking_available", clean_yes_no("book_table"))
        .withColumn("location_name", F.initcap(F.col("location")))
        .withColumn("restaurant_type_name", F.initcap(F.col("rest_type")))
        .withColumn("listing_type_name", F.initcap(F.col("listed_in(type)")))
        .withColumn("listing_city_name", F.initcap(F.col("listed_in(city)")))
        .withColumn(
            "price_band",
            F.when(F.col("cost_for_two") < 400, "Budget")
            .when(F.col("cost_for_two") < 800, "Mid-range")
            .otherwise("Premium"),
        )
        .withColumn("is_valid_rating", F.col("rate_value").between(1.0, 5.0))
        .withColumn("is_valid_cost", F.col("cost_for_two") > 0)
        .withColumn("is_high_rated", (F.col("rate_value") >= 4.0) & (F.col("vote_count") >= 20))
    )
    return cleaned.filter(
        F.col("restaurant_key").isNotNull()
        & F.col("location_name").isNotNull()
        & F.col("is_valid_rating")
        & F.col("is_valid_cost")
        & (F.col("vote_count") >= 0)
    )


def main() -> None:
    spark = SparkSession.builder.getOrCreate()
    dbutils.widgets.text("input_path", "/Volumes/main/zomato/raw/zomato_cleaned.csv")
    dbutils.widgets.text("output_table", "main.zomato.silver_zomato_listings")
    input_path = dbutils.widgets.get("input_path")
    output_table = dbutils.widgets.get("output_table")

    raw = (
        spark.read.option("header", True)
        .option("multiLine", True)
        .option("escape", '"')
        .option("quote", '"')
        .csv(input_path)
    )
    (
        transform(raw)
        .write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", True)
        .saveAsTable(output_table)
    )


if __name__ == "__main__":
    main()
