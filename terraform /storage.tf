# ADLS Gen2 storage account — the landing zone that Fabric OneLake shortcuts
# point to, and that Databricks Auto Loader watches for new files arriving
# from Azure Data Factory copy activities.

resource "azurerm_storage_account" "lake" {
  name                     = "st${local.project}${local.environment}"
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = var.storage_account_replication
  account_kind             = "StorageV2"
  is_hns_enabled           = true # required for ADLS Gen2 hierarchical namespace

  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = 14
    }
  }

  tags = local.common_tags
}

# Medallion containers — one per layer, matching engine/medallion_pipeline.py
resource "azurerm_storage_container" "bronze" {
  name                  = "bronze"
  storage_account_name  = azurerm_storage_account.lake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = "silver"
  storage_account_name  = azurerm_storage_account.lake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "gold" {
  name                  = "gold"
  storage_account_name  = azurerm_storage_account.lake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "landing" {
  name                  = "landing"
  storage_account_name  = azurerm_storage_account.lake.name
  container_access_type = "private"
}

# Lifecycle management — cost optimization: move cold Bronze data to cool/archive tier
resource "azurerm_storage_management_policy" "lifecycle" {
  storage_account_id = azurerm_storage_account.lake.id

  rule {
    name    = "bronze-tiering"
    enabled = true

    filters {
      prefix_match = ["bronze/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than    = 30
        tier_to_archive_after_days_since_modification_greater_than = 90
        delete_after_days_since_modification_greater_than          = 730
      }
    }
  }

  rule {
    name    = "expire-old-versions"
    enabled = true

    filters {
      prefix_match = ["bronze/", "silver/", "gold/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      version {
        delete_after_days_since_creation = 90
      }
    }
  }
}
