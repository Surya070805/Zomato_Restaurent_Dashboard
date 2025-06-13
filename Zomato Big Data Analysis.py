# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC ## Overview
# MAGIC
# MAGIC This notebook will show you how to create and query a table or DataFrame that you uploaded to DBFS. [DBFS](https://docs.databricks.com/user-guide/dbfs-databricks-file-system.html) is a Databricks File System that allows you to store data for querying inside of Databricks. This notebook assumes that you have a file already inside of DBFS that you would like to read from.
# MAGIC
# MAGIC This notebook is written in **Python** so the default cell type is Python. However, you can use different languages by using the `%LANGUAGE` syntax. Python, Scala, SQL, and R are all supported.

# COMMAND ----------

# File location and type
file_location = "/FileStore/tables/zomato-1.csv"
file_type = "csv"

# CSV options
infer_schema = "false"
first_row_is_header = "true"
delimiter = ","

# The applied options are for CSV files. For other file types, these will be ignored.
df = spark.read.format(file_type) \
  .option("inferSchema", infer_schema) \
  .option("header", first_row_is_header) \
  .option("sep", delimiter) \
  .load(file_location)

display(df)

# COMMAND ----------

df.printSchema()

# COMMAND ----------

from pyspark.sql.functions import regexp_extract, col
from pyspark.sql.functions import regexp_replace

df = df.withColumn(
    "cost_clean",
    regexp_replace(col("approx_cost(for two people)"), ",", "").cast("double")
)

# COMMAND ----------

df_clean=df.withColumn("rate_clean", regexp_extract(col("rate"), r"([0-9.]+)", 1).cast("double"))
df_filtered = df_clean.filter(col("rate_clean").isNotNull())

# COMMAND ----------

# Top locations by number of restaurants
df_filtered.groupBy("location").count().orderBy("count", ascending=False).show()

# COMMAND ----------

# Average rating by city
df_filtered.groupBy("listed_in(city)").avg("rate_clean").orderBy("avg(rate_clean)", ascending=False).show()

# COMMAND ----------

from pyspark.sql.functions import avg

# Group by city and calculate average rating
city_ratings = df_filtered.groupBy("listed_in(city)") \
    .agg(avg("rate_clean").alias("average_rating")) \
    .orderBy(col("average_rating").desc())

# Show top cities with best-rated restaurants
city_ratings.show(truncate=False)

# COMMAND ----------

df_cleaned = df_filtered.select("rate_clean", "cost_clean", "online_order", "book_table", "listed_in(city)")
df_cleaned.write.csv("dbfs:/FileStore/cleaned_zomato1.csv", header=True)
