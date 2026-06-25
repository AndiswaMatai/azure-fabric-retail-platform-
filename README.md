# 🏢 Enterprise Retail & Loyalty Intelligence Platform

![Azure](https://img.shields.io/badge/Cloud-Azure-blue?logo=microsoftazure)
![Databricks](https://img.shields.io/badge/Platform-Databricks-orange?logo=databricks)
![Microsoft Fabric](https://img.shields.io/badge/Platform-Microsoft%20Fabric-purple?logo=microsoft)
![Python](https://img.shields.io/badge/Language-Python-yellow?logo=python)
![Terraform](https://img.shields.io/badge/IaC-Terraform-purple?logo=terraform)
![Power BI](https://img.shields.io/badge/BI-Power%20BI-yellow?logo=powerbi)
![CI/CD](https://img.shields.io/badge/DevOps-CI%2FCD-green?logo=githubactions)

---

## 🚀 Overview
A full end-to-end enterprise data platform demonstrating how modern **retail and loyalty systems** are engineered on Azure using a governed Lakehouse architecture.  
Integrates **Azure Data Factory**, **Databricks (Medallion)**, and **Microsoft Fabric** to deliver curated datasets exposed through **Power BI DirectLake** semantic models.  
Represents a complete production-style ecosystem: ingestion, transformation, data quality, monitoring, CI/CD, and cost governance.

---

## 🧠 Why This Exists
Most portfolios show pipelines. Few show **platform thinking**.  
This repository answers enterprise questions:
- How does data move safely from ingestion to dashboards?  
- How is data quality enforced before business consumption?  
- What prevents bad data from reaching executives?  
- How is infrastructure deployed, governed, and cost-optimised?  
- How does code move safely from dev → test → prod?  

---

## 🏗️ Architecture
📡 **Data Sources** → 🟦 **ADF** → 🟨 **Databricks (Bronze/Silver/Gold)** → 🟪 **Fabric** → 📊 **Power BI DirectLake**

- **ADF:** Orchestration, scheduling, ingestion coordination  
- **Databricks:** Bronze (raw), Silver (cleaned/conformed), Gold (business-ready loyalty + retail models)  
- **Fabric:** Lakehouse exposure, eventstream integration, semantic modelling  
- **Power BI:** Loyalty dashboards, customer analytics, executive reporting  

---

## 📂 Repository Structure
retail-loyalty-intelligence/
├── engine/             # Local medallion pipeline (portable Databricks logic)
├── databricks/         # Production PySpark notebooks (1:1 mirror of engine)
├── adf/                # Azure Data Factory pipelines + linked services
├── fabric/             # Microsoft Fabric configs (Lakehouse + eventstream)
├── terraform/          # Infrastructure-as-Code (ADF, Databricks, Storage, IAM)
├── monitoring/         # Azure Monitor alerts + KQL queries
├── powerbi/            # Semantic model (TMDL + DAX measures)
├── data_quality/       # Data quality framework (DQ gates + rules engine)
├── cost_optimization/  # Cost modelling (compute + storage savings)
├── tests/              # Unit tests for pipeline + DQ + transformations
├── .github/workflows/  # CI/CD pipelines (test → plan → deploy simulation)
└── README.md           # Documentation


---

## ⚙️ Engineering Design Principles
- Medallion architecture (Bronze → Silver → Gold)  
- Separation of ingestion, transformation, consumption layers  
- Data quality enforced as pipeline gates  
- Event-driven + batch convergence into unified Silver layer  
- Infrastructure-as-Code (Terraform) for reproducibility  
- CI/CD-driven deployment lifecycle  
- Cost-aware cloud architecture design  
- Semantic modelling for BI consumption (Power BI DirectLake)  

---

## 📊 Sample Output
**Loyalty Tier Performance**
| Tier      | Customers | Revenue        | Avg Basket |
|-----------|-----------|----------------|------------|
| Bronze    | 18,177    | 199,371,054.25 | 1099.40    |
| Silver    | 11,976    | 131,510,358.18 | 1101.66    |
| Gold      | 7,139     | 78,011,617.73  | 1100.26    |
| Platinum  | 2,708     | 29,456,431.62  | 1100.11    |

---

## ✅ Data Quality Layer
- Completeness checks  
- Uniqueness constraints  
- Referential integrity validation  
- Freshness SLAs  

Result: **0 of 6 checks failed → Gold layer approved for Power BI consumption**

---

## 💰 Cost Optimisation Results
- Storage lifecycle tiering savings: **55.9%**  
- Databricks spot instance savings: **59.5%**  
- Estimated annual savings: **R76,196.40**  

Includes: auto-termination policies, storage tiering, spot compute usage strategy.

---

## 💡 Business Impact
- **Customer Insights:** Delivered loyalty segmentation + lifetime value analysis.  
- **Operational Efficiency:** Reduced reporting latency with DirectLake semantic models.  
- **Cost Savings:** Achieved >50% infra savings via tiering + spot compute.  
- **Governance:** Enforced data quality gates before executive reporting.  
- **Scalability:** CI/CD + Terraform ensured reproducible, enterprise-ready deployments.  

---

## 📜 License
MIT — synthetic data used
