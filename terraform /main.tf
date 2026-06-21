# Enterprise Retail & Loyalty Intelligence Platform — Azure Infrastructure
#
# Provisions the full Azure footprint for the platform: resource group,
# ADLS Gen2 storage (OneLake-backed via Fabric capacity), Azure Data Factory,
# Databricks workspace, Key Vault for secrets, Log Analytics for monitoring,
# and budget alerts for cost control.
#
# Usage:
#   terraform init
#   terraform plan -var-file="environments/dev.tfvars"
#   terraform apply -var-file="environments/dev.tfvars"

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.95"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.40"
    }
  }

  backend "azurerm" {
    # Configure via -backend-config flags or a backend.hcl file per environment.
    # Kept empty here intentionally — never hardcode backend state credentials.
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false
    }
  }
}

locals {
  project     = "retailloyalty"
  environment = var.environment
  prefix      = "${local.project}-${local.environment}"

  common_tags = {
    project     = "enterprise-retail-loyalty-platform"
    environment = var.environment
    managed_by  = "terraform"
    cost_center = var.cost_center
    owner       = var.owner_email
  }
}

resource "azurerm_resource_group" "this" {
  name     = "rg-${local.prefix}"
  location = var.location
  tags     = local.common_tags
}
