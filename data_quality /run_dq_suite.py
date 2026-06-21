"""
Runs the full data quality suite against the Silver layer produced by
engine/medallion_pipeline.py. Run this after the pipeline:

    python engine/medallion_pipeline.py
    python data_quality/run_dq_suite.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

import pandas as pd
from dq_framework import check_completeness, check_uniqueness, check_referential_integrity, check_freshness, run_suite

SILVER = Path(__file__).resolve().parent.parent / "data" / "lakehouse" / "silver"


def main():
    transactions = pd.read_csv(SILVER / "transactions.csv")
    customers = pd.read_csv(SILVER / "dim_customer.csv")
    loyalty = pd.read_csv(SILVER / "loyalty_events.csv")
    valid_customer_ids = set(customers["customer_id"])

    checks = [
        check_completeness(transactions, "transactions", ["customer_id", "product_id", "amount"]),
        check_uniqueness(transactions, "transactions", "transaction_id"),
        check_referential_integrity(transactions, "transactions", "customer_id", valid_customer_ids),
        check_freshness(transactions, "transactions", "transaction_date", max_age_days=3650),  # demo data is historical
        check_uniqueness(customers, "dim_customer", "customer_id"),
        check_referential_integrity(loyalty, "loyalty_events", "customer_id", valid_customer_ids),
    ]

    results, failed = run_suite(checks)

    print("=" * 60)
    print("DATA QUALITY SUITE RESULTS")
    print("=" * 60)
    for _, row in results.iterrows():
        flag = "✓" if row["status"] == "PASS" else "✗"
        print(f"  [{flag}] {row['table']}.{row['check_name']}: {row['metric_value']} (threshold {row['threshold']})")
        print(f"        {row['detail']}")

    print(f"\n{len(failed)} of {len(results)} checks failed.")
    if len(failed) > 0:
        print("\nIn production: this would fail the Databricks Job and trigger the")
        print("Azure Monitor alert defined in monitoring/alert_rules.tf")
        sys.exit(1)
    else:
        print("All checks passed — Gold layer is safe to publish to Power BI.")


if __name__ == "__main__":
    main()
