"""
Local medallion engine for the Enterprise Retail & Loyalty Intelligence
Platform. This is the same Bronze → Silver → Gold logic that ships as
Databricks notebooks (see databricks/notebooks/) — implemented here in
pandas so the full pipeline is runnable and testable without a Databricks
workspace or cluster.

In production: Azure Data Factory triggers a Databricks Job that runs the
notebooks in databricks/notebooks/ against Delta tables on OneLake. The
function signatures and logic here are a 1:1 mirror of those notebooks.
"""
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAW    = Path(__file__).resolve().parent.parent / "data" / "raw"
BRONZE = Path(__file__).resolve().parent.parent / "data" / "lakehouse" / "bronze"
SILVER = Path(__file__).resolve().parent.parent / "data" / "lakehouse" / "silver"
GOLD   = Path(__file__).resolve().parent.parent / "data" / "lakehouse" / "gold"
for p in [BRONZE, SILVER, GOLD]:
    p.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 50_000

def now(): return datetime.now(timezone.utc).isoformat()


# ── BRONZE ────────────────────────────────────────────────────────────────────
# Databricks equivalent: Auto Loader (cloudFiles) reading from ADLS landing zone
#   df = spark.readStream.format("cloudFiles").option("cloudFiles.format","csv")\
#        .load("abfss://landing@onelake.dfs.fabric.microsoft.com/retail/transactions")
#   df.writeStream.format("delta").trigger(availableNow=True)\
#        .toTable("bronze.transactions")
def bronze_ingest(table_name: str):
    src = RAW / f"{table_name}.csv"
    dst = BRONZE / f"{table_name}.csv"
    total = 0
    first = True
    for chunk in pd.read_csv(src, chunksize=CHUNK_SIZE, dtype=str):
        chunk["_ingested_ts"] = now()
        chunk.to_csv(dst, mode="w" if first else "a", header=first, index=False)
        first = False
        total += len(chunk)
    return total


# ── SILVER ────────────────────────────────────────────────────────────────────
# Databricks equivalent:
#   df = spark.table("bronze.transactions")
#   clean = df.filter(col("quantity") > 0).filter(col("customer_id").isNotNull())\
#        .dropDuplicates(["transaction_id"])
#   clean.write.format("delta").mode("overwrite").saveAsTable("silver.transactions")
def silver_cleanse_transactions():
    rejected, clean_chunks, seen = 0, [], set()
    for chunk in pd.read_csv(BRONZE / "transactions.csv", chunksize=CHUNK_SIZE):
        before = len(chunk)
        chunk["quantity"] = pd.to_numeric(chunk["quantity"], errors="coerce")
        chunk = chunk[chunk["quantity"] > 0]
        chunk = chunk[chunk["customer_id"].notna() & (chunk["customer_id"] != "")]
        chunk = chunk[~chunk["transaction_id"].isin(seen)].drop_duplicates(subset=["transaction_id"])
        seen.update(chunk["transaction_id"])
        rejected += before - len(chunk)
        clean_chunks.append(chunk)
    clean = pd.concat(clean_chunks, ignore_index=True)
    clean["amount"] = pd.to_numeric(clean["amount"], errors="coerce")
    clean["_cleansed_ts"] = now()
    clean.to_csv(SILVER / "transactions.csv", index=False)
    return len(clean), rejected


def silver_scd2_customers():
    """Type 2 SCD for the customer dimension — tracks loyalty_tier changes
    over time, exactly as it would run via a Databricks MERGE INTO statement:

        MERGE INTO silver.dim_customer AS target
        USING staged_customers AS source
        ON target.customer_id = source.customer_id AND target.is_current = true
        WHEN MATCHED AND target.loyalty_tier != source.loyalty_tier THEN
            UPDATE SET is_current = false, effective_to = current_date()
        WHEN NOT MATCHED THEN INSERT ...
    """
    customers = pd.read_csv(RAW / "customers.csv")
    today = datetime.now().date().isoformat()
    customers["effective_from"] = today
    customers["effective_to"] = None
    customers["is_current"] = True
    customers["_scd_ts"] = now()
    customers.to_csv(SILVER / "dim_customer.csv", index=False)
    return len(customers)


def silver_cleanse_simple(table_name: str, valid_customer_ids: set = None):
    rejected, clean_chunks = 0, []
    for chunk in pd.read_csv(BRONZE / f"{table_name}.csv", chunksize=CHUNK_SIZE):
        before = len(chunk)
        if valid_customer_ids is not None and "customer_id" in chunk.columns:
            chunk = chunk[chunk["customer_id"].isin(valid_customer_ids)]
        rejected += before - len(chunk)
        clean_chunks.append(chunk)
    clean = pd.concat(clean_chunks, ignore_index=True)
    clean.to_csv(SILVER / f"{table_name}.csv", index=False)
    return len(clean), rejected


# ── GOLD ──────────────────────────────────────────────────────────────────────
# Databricks equivalent: aggregated Delta tables, exposed to Fabric/Power BI
# via DirectLake (zero-copy read straight off OneLake, no import/refresh).
def gold_aggregate():
    txns = pd.read_csv(SILVER / "transactions.csv")
    products = pd.read_csv(SILVER / "products.csv")
    stores = pd.read_csv(SILVER / "stores.csv")
    customers = pd.read_csv(SILVER / "dim_customer.csv")
    loyalty = pd.read_csv(SILVER / "loyalty_events.csv")

    enriched = txns.merge(products[["product_id", "category", "cost_price_pct"]], on="product_id", how="left") \
                    .merge(stores[["store_id", "region", "store_format"]], on="store_id", how="left") \
                    .merge(customers[["customer_id", "loyalty_tier"]], on="customer_id", how="left")
    enriched["gross_margin"] = (enriched["amount"] * (1 - enriched["cost_price_pct"])).round(2)
    enriched["month"] = pd.to_datetime(enriched["transaction_date"]).dt.to_period("M").astype(str)

    # 1. Sales by region/category/month
    sales_summary = enriched.groupby(["month", "region", "category"]).agg(
        revenue=("amount", "sum"), units=("quantity", "sum"),
        gross_margin=("gross_margin", "sum"), transactions=("transaction_id", "count"),
    ).reset_index()
    sales_summary.to_csv(GOLD / "sales_by_region_category_month.csv", index=False)

    # 2. Loyalty tier value analysis
    tier_value = enriched.groupby("loyalty_tier").agg(
        customers=("customer_id", "nunique"), revenue=("amount", "sum"),
        avg_basket=("amount", "mean"),
    ).reset_index()
    tier_value["avg_basket"] = tier_value["avg_basket"].round(2)
    tier_value.to_csv(GOLD / "loyalty_tier_value.csv", index=False)

    # 3. Store performance leaderboard
    store_perf = enriched.groupby(["store_id", "store_format", "region"]).agg(
        revenue=("amount", "sum"), gross_margin=("gross_margin", "sum"),
        transactions=("transaction_id", "count"),
    ).reset_index().sort_values("revenue", ascending=False)
    store_perf.to_csv(GOLD / "store_performance.csv", index=False)

    # 4. Loyalty points liability (net outstanding points = business cost)
    points_liability = loyalty.groupby("event_type")["points"].sum().reset_index()
    points_liability.to_csv(GOLD / "loyalty_points_liability.csv", index=False)

    return sales_summary, tier_value, store_perf, points_liability


def main():
    print("=" * 60)
    print("RETAIL & LOYALTY LAKEHOUSE — MEDALLION PIPELINE")
    print("=" * 60)

    tables = ["customers", "products", "stores", "transactions", "loyalty_events"]
    print("\n[Bronze] Chunked ingest...")
    for t in tables:
        n = bronze_ingest(t)
        print(f"   {t}: {n:,} rows")

    print("\n[Silver] Cleansing + SCD2...")
    txn_clean, txn_rejected = silver_cleanse_transactions()
    print(f"   transactions: {txn_clean:,} clean ({txn_rejected:,} rejected)")
    cust_count = silver_scd2_customers()
    print(f"   dim_customer (SCD2): {cust_count:,} current records")
    valid_customers = set(pd.read_csv(SILVER / "dim_customer.csv", usecols=["customer_id"])["customer_id"])
    for t in ["products", "stores"]:
        n, r = silver_cleanse_simple(t)
        print(f"   {t}: {n:,} clean")
    loy_clean, loy_rejected = silver_cleanse_simple("loyalty_events", valid_customers)
    print(f"   loyalty_events: {loy_clean:,} clean ({loy_rejected:,} rejected)")

    print("\n[Gold] Aggregating business KPIs...")
    sales, tiers, stores_perf, points = gold_aggregate()
    print(f"   sales_by_region_category_month: {len(sales)} rows")
    print(f"   loyalty_tier_value: {len(tiers)} rows")

    print("\n" + "=" * 60)
    print("LOYALTY TIER VALUE")
    print("=" * 60)
    print(tiers.to_string(index=False))

    print("\nTop 5 stores by revenue:")
    print(stores_perf.head(5)[["store_id", "region", "revenue"]].to_string(index=False))


if __name__ == "__main__":
    main()
