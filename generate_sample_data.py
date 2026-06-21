"""
Generates synthetic retail + loyalty data for the Enterprise Retail &
Loyalty Intelligence Platform — the domain used to demonstrate the full
medallion pipeline locally before it's deployed as Databricks notebooks
orchestrated by Azure Data Factory and surfaced through Microsoft Fabric.

Run: python engine/generate_sample_data.py
"""
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(2026)
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

N_CUSTOMERS = 40_000
N_PRODUCTS = 2_500
N_STORES = 85
N_TRANSACTIONS = 400_000      # POS transaction line items
N_LOYALTY_EVENTS = 150_000    # points earned/redeemed events

REGIONS = ["Gauteng", "Western Cape", "KwaZulu-Natal", "Eastern Cape", "Free State"]
CATEGORIES = ["Groceries", "Electronics", "Apparel", "Home & Garden", "Health & Beauty", "Sporting Goods"]
LOYALTY_TIERS = ["Bronze", "Silver", "Gold", "Platinum"]
PAYMENT_METHODS = ["Card", "Cash", "Loyalty Points", "Mobile Wallet"]

start = datetime(2025, 1, 1)
today = datetime(2026, 6, 1)

def _random_dates(n, start, end):
    delta_days = (end - start).days
    return [start + timedelta(days=int(o)) for o in rng.integers(0, delta_days, size=n)]

# ── Dimensions ───────────────────────────────────────────────────────────────
print("Generating customers...")
customer_ids = [f"CUST{str(i).zfill(7)}" for i in range(1, N_CUSTOMERS + 1)]
customers = pd.DataFrame({
    "customer_id": customer_ids,
    "region": rng.choice(REGIONS, N_CUSTOMERS),
    "loyalty_tier": rng.choice(LOYALTY_TIERS, N_CUSTOMERS, p=[0.45, 0.30, 0.18, 0.07]),
    "signup_date": [d.strftime("%Y-%m-%d") for d in _random_dates(N_CUSTOMERS, start - timedelta(days=730), today)],
    "email_opt_in": rng.choice(["true", "false"], N_CUSTOMERS, p=[0.62, 0.38]),
})
customers.to_csv(RAW / "customers.csv", index=False)

print("Generating products...")
products = pd.DataFrame({
    "product_id": [f"PROD{str(i).zfill(6)}" for i in range(1, N_PRODUCTS + 1)],
    "category": rng.choice(CATEGORIES, N_PRODUCTS),
    "unit_price": np.round(rng.gamma(2, 180, N_PRODUCTS) + 15, 2),
    "cost_price_pct": np.round(rng.uniform(0.45, 0.75, N_PRODUCTS), 3),
})
products.to_csv(RAW / "products.csv", index=False)

print("Generating stores...")
stores = pd.DataFrame({
    "store_id": [f"STORE{str(i).zfill(3)}" for i in range(1, N_STORES + 1)],
    "region": rng.choice(REGIONS, N_STORES),
    "store_format": rng.choice(["Flagship", "Mall", "Standalone", "Express"], N_STORES, p=[0.05, 0.40, 0.35, 0.20]),
})
stores.to_csv(RAW / "stores.csv", index=False)

# ── Fact: POS transactions ───────────────────────────────────────────────────
print(f"Generating {N_TRANSACTIONS:,} transactions...")
txn_customer = rng.choice(customer_ids, N_TRANSACTIONS)
txn_product_idx = rng.integers(0, N_PRODUCTS, N_TRANSACTIONS)
txn_store = rng.choice(stores["store_id"], N_TRANSACTIONS)
txn_dates = _random_dates(N_TRANSACTIONS, start, today)
txn_qty = rng.integers(1, 6, N_TRANSACTIONS)
unit_prices = np.array(products["unit_price"])[txn_product_idx]
txn_amount = np.round(unit_prices * txn_qty * rng.uniform(0.92, 1.0, N_TRANSACTIONS), 2)  # small promo variance

transactions = pd.DataFrame({
    "transaction_id": [f"TXN{str(i).zfill(9)}" for i in range(1, N_TRANSACTIONS + 1)],
    "customer_id": txn_customer,
    "product_id": np.array(products["product_id"])[txn_product_idx],
    "store_id": txn_store,
    "transaction_date": [d.strftime("%Y-%m-%d") for d in txn_dates],
    "quantity": txn_qty,
    "amount": txn_amount,
    "payment_method": rng.choice(PAYMENT_METHODS, N_TRANSACTIONS, p=[0.55, 0.20, 0.10, 0.15]),
})
# Inject ~0.4% dirty records: negative quantity, null customer_id
n_dirty = int(N_TRANSACTIONS * 0.004)
dirty_idx = rng.choice(N_TRANSACTIONS, n_dirty, replace=False)
transactions.loc[dirty_idx[: n_dirty // 2], "quantity"] = -1
transactions.loc[dirty_idx[n_dirty // 2:], "customer_id"] = ""
transactions.to_csv(RAW / "transactions.csv", index=False)

# ── Fact: Loyalty events ─────────────────────────────────────────────────────
print(f"Generating {N_LOYALTY_EVENTS:,} loyalty events...")
loy_customer = rng.choice(customer_ids, N_LOYALTY_EVENTS)
loy_dates = _random_dates(N_LOYALTY_EVENTS, start, today)
loy_type = rng.choice(["earn", "redeem", "expire"], N_LOYALTY_EVENTS, p=[0.55, 0.35, 0.10])
loy_points = np.where(loy_type == "earn", rng.integers(10, 500, N_LOYALTY_EVENTS),
              np.where(loy_type == "redeem", -rng.integers(100, 2000, N_LOYALTY_EVENTS),
                       -rng.integers(50, 300, N_LOYALTY_EVENTS)))

loyalty_events = pd.DataFrame({
    "event_id": [f"LOY{str(i).zfill(8)}" for i in range(1, N_LOYALTY_EVENTS + 1)],
    "customer_id": loy_customer,
    "event_date": [d.strftime("%Y-%m-%d") for d in loy_dates],
    "event_type": loy_type,
    "points": loy_points,
})
loyalty_events.to_csv(RAW / "loyalty_events.csv", index=False)

total = len(customers) + len(products) + len(stores) + len(transactions) + len(loyalty_events)
print(f"\nDone. Total rows generated: {total:,}")
print(f"  customers: {len(customers):,} | products: {len(products):,} | stores: {len(stores):,}")
print(f"  transactions: {len(transactions):,} | loyalty_events: {len(loyalty_events):,}")
