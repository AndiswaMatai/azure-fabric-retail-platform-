# 🏢 Enterprise Retail & Loyalty Intelligence Platform

![Sector](https://img.shields.io/badge/Sector-Flagship%20%C2%B7%20Azure%20%2F%20Fabric-1F3864?style=flat)
![CI](https://img.shields.io/badge/CI-passing-0f7a4b?style=flat&logo=githubactions)
![IaC](https://img.shields.io/badge/IaC-Terraform-7B42BC?style=flat&logo=terraform)
![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat&logo=python)

**[← Back to live portfolio](https://andiswamatai.github.io)**

## 🚀 Overview

A full end-to-end enterprise data platform that demonstrates how modern retail and loyalty systems are engineered on Azure using a governed Lakehouse architecture.

The platform integrates Azure Data Factory, Databricks (Medallion architecture), and Microsoft Fabric to deliver curated, analytics-ready datasets exposed through Power BI DirectLake semantic models.

It represents a complete production-style data ecosystem — including ingestion, transformation, data quality, monitoring, CI/CD, and cost governance.

---

## 🧠 Why this exists

Most data engineering portfolios demonstrate pipelines.

Very few demonstrate **platform thinking**.

This repository goes beyond pipeline design to answer real enterprise questions:

- How does data move safely from ingestion to executive dashboards?
- How is data quality enforced before business consumption?
- What prevents bad data from reaching board-level reporting?
- How is infrastructure deployed, governed, and cost-optimised?
- How does a change move from code → test → production safely?

This project models those realities end-to-end.

## Architecture

📡 Data Sources
- Retail Transactions
- Loyalty Systems
- Customer Behaviour Events

        ↓

🟦 Azure Data Factory
- Orchestration layer
- Pipeline scheduling
- Ingestion coordination

        ↓

🟨 Databricks (Medallion Architecture)

    🥉 Bronze Layer
    - Raw ingested data

    🥈 Silver Layer
    - Cleansed + standardized + conformed data

    🥇 Gold Layer
    - Business-ready loyalty + retail analytics models

        ↓

🟪 Microsoft Fabric
- Lakehouse exposure layer
- Eventstream integration
- Semantic modelling

        ↓

📊 Power BI (DirectLake)
- Loyalty dashboards
- Customer analytics
- Executive reporting layer

---
## What's actually runnable vs. what's reference architecture

Being upfront about this, the same way I would in an interview:

| Component | Status |
|---|---|
| `engine/` — full medallion pipeline (Bronze→Silver→Gold) | **Runs locally**, pandas, no cloud account needed |
| `data_quality/` — completeness, uniqueness, referential integrity, freshness | **Runs locally**, tested |
| `cost_optimization/cost_calculator.py` | **Runs locally**, models real savings from the Terraform config |
| `tests/` | **Runs locally**, 8 passing unit tests |
| `terraform/*.tf` | **Valid HCL**, `terraform validate`-able, not applied (no Azure subscription) |
| `databricks/notebooks/*.py` | **Valid PySpark**, written exactly as it would run in a Databricks workspace, mirrors `engine/` 1:1 |
| `adf/`, `fabric/` JSON | **Valid JSON**, matches the real ADF/Fabric REST API schema |
| `monitoring/alert_rules.tf` | **Valid HCL**, KQL queries written against real Log Analytics table schemas |
| `.github/workflows/cd.yml` | **Documents the real deployment commands**, doesn't execute them against live infra |

## Repository Structure

```
engine/                  Local medallion pipeline (portable version of Databricks logic)
databricks/notebooks/    Production PySpark notebooks (1:1 mirror of engine)
adf/                     Azure Data Factory pipelines + linked services
fabric/                  Microsoft Fabric Lakehouse + eventstream configs
terraform/               Full infrastructure-as-code (ADF, Databricks, Storage, IAM)
monitoring/              Azure Monitor alerts + KQL queries
powerbi/                 Semantic model (TMDL + DAX measures)
data_quality/            Data quality framework (DQ gates + rules engine)
cost_optimization/       Cost modelling (compute + storage + efficiency gains)
tests/                   Unit tests for pipeline + DQ + transformations
.github/workflows/       CI/CD pipelines (test → plan → deploy simulation)
```

## Engineering Design Principle

This platform demonstrates enterprise-grade data architecture principles:

- Medallion architecture (Bronze → Silver → Gold)
- Separation of ingestion, transformation, and consumption layers
- Data quality enforced as a pipeline gate (not a downstream fix)
- Event-driven + batch convergence into unified Silver layer
- Infrastructure-as-Code (Terraform) for reproducibility
- CI/CD-driven deployment lifecycle
- Cost-aware cloud architecture design
- Semantic modelling for BI consumption (Power BI DirectLake)

## Sample Output

```
LOYALTY TIER PERFORMANCE

loyalty_tier | customers | revenue        | avg_basket
-------------|-----------|----------------|------------
Bronze       | 18177     | 199,371,054.25 | 1099.40
Silver       | 11976     | 131,510,358.18 | 1101.66
Gold         | 7139      | 78,011,617.73  | 1100.26
Platinum     | 2708      | 29,456,431.62  | 1100.11
```

## Data Quality Layer

All Gold-layer datasets are validated before publication using:

- Completeness checks
- Uniqueness constraints
- Referential integrity validation
- Freshness SLAs

Result:

✔ 0 of 6 data quality checks failed  
✔ Gold layer approved for Power BI consumption


## COST OPTIMISATION RESULTS

- Storage lifecycle tiering savings: 55.9%
- Databricks spot instance savings: 59.5%
- Estimated annual savings: R76,196.40

Includes:
- Auto-termination policies
- Storage tiering (hot → cool → archive)
- Spot compute usage strategy
---
## Business Value

This platform enables retail organisations to:

- Understand customer lifetime value and segmentation
- Improve loyalty program effectiveness
- Reduce cloud infrastructure costs through optimisation
- Ensure data governance and compliance
- Deliver trusted executive-level reporting
---
## Production Enhancement

If deployed in enterprise environments:

- Azure Data Factory for orchestration
- Databricks jobs for scalable transformation
- Microsoft Fabric for unified analytics layer
- Power BI DirectLake for real-time dashboards
- Key Vault for secrets management
- Azure Monitor for alerting and observability
- Terraform for full infrastructure lifecycle management
