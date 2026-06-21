"""
Cost Optimization Calculator

Models the actual savings from the cost controls implemented across this
platform's Terraform config, so the impact is a number, not just a claim:

  1. ADLS Gen2 lifecycle tiering (terraform/storage.tf)        -> storage cost
  2. Databricks autoscaling + spot instances (terraform/databricks.tf) -> compute cost
  3. Auto-termination (15 min idle)                            -> wasted compute

Run: python cost_optimization/cost_calculator.py
"""
from dataclasses import dataclass

# Approximate Azure South Africa North pricing (ZAR), illustrative for the model —
# always re-check against the Azure Pricing Calculator before using in a real budget.
HOT_GB_MONTH = 0.38
COOL_GB_MONTH = 0.21
ARCHIVE_GB_MONTH = 0.04
DATABRICKS_DBU_HOUR_ON_DEMAND = 9.20
DATABRICKS_SPOT_DISCOUNT = 0.70   # spot typically ~70% cheaper than on-demand


@dataclass
class StorageProfile:
    total_gb: float
    pct_hot: float       # 0-30 days old
    pct_cool: float       # 30-90 days old
    pct_archive: float    # 90+ days old


def storage_cost_without_tiering(profile: StorageProfile) -> float:
    """Naive baseline: everything stays in Hot tier forever."""
    return profile.total_gb * HOT_GB_MONTH


def storage_cost_with_tiering(profile: StorageProfile) -> float:
    """With the lifecycle policy in terraform/storage.tf applied."""
    hot_gb = profile.total_gb * profile.pct_hot
    cool_gb = profile.total_gb * profile.pct_cool
    archive_gb = profile.total_gb * profile.pct_archive
    return hot_gb * HOT_GB_MONTH + cool_gb * COOL_GB_MONTH + archive_gb * ARCHIVE_GB_MONTH


def databricks_cost_on_demand(dbu_hours_per_month: float) -> float:
    return dbu_hours_per_month * DATABRICKS_DBU_HOUR_ON_DEMAND


def databricks_cost_with_spot(dbu_hours_per_month: float, spot_success_rate: float = 0.85) -> float:
    """spot_success_rate models that the cluster policy's SPOT_WITH_FALLBACK_AZURE
    occasionally falls back to on-demand when spot capacity is unavailable."""
    spot_hours = dbu_hours_per_month * spot_success_rate
    on_demand_hours = dbu_hours_per_month * (1 - spot_success_rate)
    spot_cost = spot_hours * DATABRICKS_DBU_HOUR_ON_DEMAND * (1 - DATABRICKS_SPOT_DISCOUNT)
    on_demand_cost = on_demand_hours * DATABRICKS_DBU_HOUR_ON_DEMAND
    return spot_cost + on_demand_cost


def autotermination_savings(jobs_per_month: int, avg_idle_minutes_saved: float) -> float:
    """The 15-minute autotermination_minutes setting in terraform/databricks.tf
    saves roughly avg_idle_minutes_saved of otherwise-billed idle cluster time
    per job run."""
    idle_hours_saved = (jobs_per_month * avg_idle_minutes_saved) / 60
    return idle_hours_saved * DATABRICKS_DBU_HOUR_ON_DEMAND


def main():
    # Profile matching this platform's actual data volumes (engine/generate_sample_data.py)
    profile = StorageProfile(total_gb=2_400, pct_hot=0.20, pct_cool=0.35, pct_archive=0.45)

    print("=" * 60)
    print("COST OPTIMIZATION IMPACT — ENTERPRISE RETAIL PLATFORM")
    print("=" * 60)

    no_tier = storage_cost_without_tiering(profile)
    with_tier = storage_cost_with_tiering(profile)
    print(f"\nStorage (ADLS Gen2, {profile.total_gb:,.0f} GB):")
    print(f"  Without lifecycle tiering: R{no_tier:,.2f}/month")
    print(f"  With lifecycle tiering:    R{with_tier:,.2f}/month")
    print(f"  Monthly savings:           R{no_tier - with_tier:,.2f} ({(1 - with_tier/no_tier):.1%})")

    dbu_hours = 35 * 30  # ~35 DBU-hours/day average across the daily Job
    on_demand = databricks_cost_on_demand(dbu_hours)
    spot = databricks_cost_with_spot(dbu_hours)
    print(f"\nDatabricks compute (~{dbu_hours:,.0f} DBU-hours/month):")
    print(f"  100% on-demand:            R{on_demand:,.2f}/month")
    print(f"  Spot with fallback:        R{spot:,.2f}/month")
    print(f"  Monthly savings:           R{on_demand - spot:,.2f} ({(1 - spot/on_demand):.1%})")

    autoterm_savings = autotermination_savings(jobs_per_month=30, avg_idle_minutes_saved=20)
    print(f"\nAuto-termination (15 min idle timeout, 30 job runs/month):")
    print(f"  Estimated savings:         R{autoterm_savings:,.2f}/month")

    total_savings = (no_tier - with_tier) + (on_demand - spot) + autoterm_savings
    print(f"\n{'TOTAL ESTIMATED MONTHLY SAVINGS:':<28} R{total_savings:,.2f}")
    print(f"{'TOTAL ESTIMATED ANNUAL SAVINGS:':<28} R{total_savings * 12:,.2f}")


if __name__ == "__main__":
    main()
