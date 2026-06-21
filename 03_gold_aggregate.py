# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer — Business Aggregates for Power BI DirectLake
# MAGIC
# MAGIC Mirrors `engine/medallion_pipeline.py::gold_aggregate()`. These tables are
# MAGIC consumed directly by the Power BI semantic model in `powerbi/` via
# MAGIC DirectLake — a zero-copy read straight off OneLake with no import/refresh
# MAGIC step, so Gold table writes here are what "publishes" new numbers to the
# MAGIC business.

# COMMAND ----------

from pyspark.sql import functions as F

catalog = dbutils.widgets.get("catalog") if "catalog" in [w.name for w in dbutils.widgets.getAll()] else "retail_loyalty"
spark.sql(f"USE CATALOG {catalog}")
spark.sql("CREATE SCHEMA IF NOT EXISTS gold")

txns = spark.table("silver.transactions")
products = spark.table("silver.products")
stores = spark.table("silver.stores")
customers = spark.table("silver.dim_customer").filter("is_current = true")
loyalty = spark.table("silver.loyalty_events")

enriched = (
    txns
    .join(products.select("product_id", "category", "cost_price_pct"), "product_id", "left")
    .join(stores.select("store_id", "region", "store_format"), "store_id", "left")
    .join(customers.select("customer_id", "loyalty_tier"), "customer_id", "left")
    .withColumn("gross_margin", F.round(F.col("amount") * (1 - F.col("cost_price_pct")), 2))
    .withColumn("month", F.date_format("transaction_date", "yyyy-MM"))
)
enriched.cache()

# COMMAND ----------

# MAGIC %md ## fact_sales — the grain for the Power BI semantic model's central fact table

# COMMAND ----------

sales_by_region_category_month = (
    enriched.groupBy("month", "region", "category")
    .agg(
        F.sum("amount").alias("revenue"),
        F.sum("quantity").alias("units"),
        F.sum("gross_margin").alias("gross_margin"),
        F.count("transaction_id").alias("transactions"),
    )
)
sales_by_region_category_month.write.format("delta").mode("overwrite").saveAsTable("gold.sales_by_region_category_month")

# COMMAND ----------

# MAGIC %md ## Loyalty tier value — feeds the Loyalty Program Power BI page

# COMMAND ----------

loyalty_tier_value = (
    enriched.groupBy("loyalty_tier")
    .agg(
        F.countDistinct("customer_id").alias("customers"),
        F.sum("amount").alias("revenue"),
        F.round(F.avg("amount"), 2).alias("avg_basket"),
    )
)
loyalty_tier_value.write.format("delta").mode("overwrite").saveAsTable("gold.loyalty_tier_value")

# COMMAND ----------

# MAGIC %md ## Store performance leaderboard

# COMMAND ----------

store_performance = (
    enriched.groupBy("store_id", "store_format", "region")
    .agg(
        F.sum("amount").alias("revenue"),
        F.sum("gross_margin").alias("gross_margin"),
        F.count("transaction_id").alias("transactions"),
    )
    .orderBy(F.desc("revenue"))
)
store_performance.write.format("delta").mode("overwrite").saveAsTable("gold.store_performance")

# COMMAND ----------

# MAGIC %md ## Loyalty points liability — finance needs this for the points-outstanding accrual

# COMMAND ----------

points_liability = loyalty.groupBy("event_type").agg(F.sum("points").alias("points"))
points_liability.write.format("delta").mode("overwrite").saveAsTable("gold.loyalty_points_liability")

print("Gold layer published. Power BI DirectLake dataset will reflect these numbers immediately — no refresh needed.")
