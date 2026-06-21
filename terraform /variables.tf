variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "South Africa North"
}

variable "cost_center" {
  description = "Cost center tag for chargeback/showback reporting"
  type        = string
  default     = "data-engineering"
}

variable "owner_email" {
  description = "Resource owner, used for tagging and budget alert notifications"
  type        = string
  default     = "andiswacebekhulu1@gmail.com"
}

variable "databricks_sku" {
  description = "Databricks workspace pricing tier"
  type        = string
  default     = "premium" # premium required for Unity Catalog + cluster policies
}

variable "adf_min_ir_nodes" {
  description = "Minimum Azure-SSIS Integration Runtime nodes (0 = use serverless Azure IR for Copy activities)"
  type        = number
  default     = 0
}

variable "monthly_budget_zar" {
  description = "Monthly spend budget in ZAR before cost alerts fire"
  type        = number
  default     = 25000
}

variable "log_retention_days" {
  description = "Log Analytics workspace data retention in days"
  type        = number
  default     = 30
}

variable "storage_account_replication" {
  description = "ADLS Gen2 replication type"
  type        = string
  default     = "LRS" # dev/staging; use GRS or RA-GRS for prod DR requirements
}
