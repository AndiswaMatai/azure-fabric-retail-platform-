# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer — Retail & Loyalty Raw Ingestion
# MAGIC
# MAGIC Reads landing-zone files (delivered by the ADF copy activity in
# MAGIC `adf/pipelines/pl_medallion_refresh.json`) using Databricks Auto Loader
# MAGIC and writes them as Delta tables in the `bronze` schema on OneLake.
# MAGIC
# MAGIC This is the production Spark equivalent of `engine/medallion_pipeline.py::bronze_ingest()`
# MAGIC — same contract (append-only, metadata-stamped), different execution engine.

# COMMAND ----------

from pyspark.sql import functions as F

dbutils.widgets.text("catalog", "retail_loyalty", "Unity Catalog name")
dbutils.widgets.text("landing_path", "abfss://landing@stretailloyaltyprod.dfs.core.windows.net/", "Landing zone path")

catalog = dbutils.widgets.get("catalog")
landing_path = dbutils.widgets.get("landing_path")

spark.sql(f"USE CATALOG {catalog}")
spark.sql("CREATE SCHEMA IF NOT EXISTS bronze")

# COMMAND ----------

TABLES = ["customers", "products", "stores", "transactions", "loyalty_events"]

for table in TABLES:
    print(f"Ingesting {table} via Auto Loader...")

    df = (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.schemaLocation", f"{landing_path}/_schemas/{table}")
        .option("header", "true")
        .load(f"{landing_path}/{table}/")
        .withColumn("_ingested_ts", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

    query = (
        df.writeStream
        .format("delta")
        .option("checkpointLocation", f"{landing_path}/_checkpoints/{table}")
        .trigger(availableNow=True)  # batch-style trigger: process what's there, then stop
        .toTable(f"bronze.{table}")
    )
    query.awaitTermination()

    count = spark.table(f"bronze.{table}").count()
    print(f"  bronze.{table}: {count:,} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next step
# MAGIC Hand off to `02_silver_cleanse.py`, which applies the same validation
# MAGIC rules as `engine/medallion_pipeline.py::silver_cleanse_transactions()`.
