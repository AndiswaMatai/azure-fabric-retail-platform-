# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer — Cleansing, SCD2, and Data Quality Expectations
# MAGIC
# MAGIC Mirrors `engine/medallion_pipeline.py::silver_cleanse_transactions()` and
# MAGIC `silver_scd2_customers()` in PySpark, plus enforces the same checks as
# MAGIC `data_quality/dq_framework.py` using Delta Live Tables-style expectations.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

catalog = dbutils.widgets.get("catalog") if "catalog" in [w.name for w in dbutils.widgets.getAll()] else "retail_loyalty"
spark.sql(f"USE CATALOG {catalog}")
spark.sql("CREATE SCHEMA IF NOT EXISTS silver")

# COMMAND ----------

# MAGIC %md ## Transactions: cleanse + dedupe + DQ expectations

# COMMAND ----------

bronze_txns = spark.table("bronze.transactions")

clean_txns = (
    bronze_txns
    .withColumn("quantity", F.col("quantity").cast("int"))
    .withColumn("amount", F.col("amount").cast("double"))
    .filter(F.col("quantity") > 0)
    .filter((F.col("customer_id").isNotNull()) & (F.col("customer_id") != ""))
    .dropDuplicates(["transaction_id"])
    .withColumn("_cleansed_ts", F.current_timestamp())
)

# DQ expectations — equivalent to data_quality/dq_framework.py checks,
# expressed as Delta Live Tables-style constraints. In a real DLT pipeline
# these would be @dlt.expect_or_fail decorators; written explicitly here
# so the logic is visible without the DLT runtime.
total = bronze_txns.count()
clean_count = clean_txns.count()
rejected = total - clean_count
completeness = clean_count / total if total else 0

assert completeness >= 0.95, f"DQ FAILURE: transactions completeness {completeness:.2%} below 95% threshold"
print(f"transactions: {clean_count:,} clean / {total:,} total ({rejected:,} rejected, {completeness:.2%} pass rate)")

clean_txns.write.format("delta").mode("overwrite").saveAsTable("silver.transactions")

# COMMAND ----------

# MAGIC %md ## Customers: Type 2 Slowly Changing Dimension via MERGE

# COMMAND ----------

from delta.tables import DeltaTable

staged = spark.table("bronze.customers").withColumn("effective_from", F.current_date())

if not spark.catalog.tableExists("silver.dim_customer"):
    (staged
     .withColumn("effective_to", F.lit(None).cast("date"))
     .withColumn("is_current", F.lit(True))
     .write.format("delta").saveAsTable("silver.dim_customer"))
else:
    target = DeltaTable.forName(spark, "silver.dim_customer")

    # Step 1: close out rows whose tracked attribute (loyalty_tier) changed
    (target.alias("t")
     .merge(staged.alias("s"), "t.customer_id = s.customer_id AND t.is_current = true")
     .whenMatchedUpdate(
         condition="t.loyalty_tier <> s.loyalty_tier",
         set={"is_current": "false", "effective_to": "current_date()"}
     )
     .execute())

    # Step 2: insert new current rows for new customers and changed customers
    changed_or_new = staged.join(
        spark.table("silver.dim_customer").filter("is_current = true"),
        on="customer_id", how="left_anti"
    )
    (changed_or_new
     .withColumn("effective_to", F.lit(None).cast("date"))
     .withColumn("is_current", F.lit(True))
     .write.format("delta").mode("append").saveAsTable("silver.dim_customer"))

print(f"silver.dim_customer: {spark.table('silver.dim_customer').filter('is_current = true').count():,} current records")

# COMMAND ----------

# MAGIC %md ## Loyalty events, products, stores: referential-integrity-checked passthrough

# COMMAND ----------

valid_customers = spark.table("silver.dim_customer").filter("is_current = true").select("customer_id")

clean_loyalty = (
    spark.table("bronze.loyalty_events")
    .join(F.broadcast(valid_customers), "customer_id", "inner")
)
clean_loyalty.write.format("delta").mode("overwrite").saveAsTable("silver.loyalty_events")

for t in ["products", "stores"]:
    spark.table(f"bronze.{t}").write.format("delta").mode("overwrite").saveAsTable(f"silver.{t}")

print("Silver layer complete. Handing off to 03_gold_aggregate.py")
