# Key Vault — secrets for the platform (storage keys, service principal
# credentials). Referenced as a Databricks secret scope and an ADF
# linked-service Key Vault reference, so no credential is ever stored in
# plain text in a notebook, pipeline JSON, or this repo.

resource "azurerm_key_vault" "this" {
  name                       = "kv-${substr(local.prefix, 0, 18)}" # Key Vault names are capped at 24 chars
  location                   = azurerm_resource_group.this.location
  resource_group_name        = azurerm_resource_group.this.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 90

  tags = local.common_tags
}

resource "azurerm_key_vault_access_policy" "adf" {
  key_vault_id = azurerm_key_vault.this.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_data_factory.this.identity[0].principal_id

  secret_permissions = ["Get", "List"]
}

data "azurerm_client_config" "current" {}

# Log Analytics — central destination for ADF pipeline run logs, Databricks
# job/cluster logs, and storage diagnostics. Queried by the KQL alert rules
# in monitoring/alert_rules.tf
resource "azurerm_log_analytics_workspace" "this" {
  name                = "log-${local.prefix}"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days

  tags = local.common_tags
}

resource "azurerm_monitor_diagnostic_setting" "adf" {
  name                       = "diag-adf"
  target_resource_id         = azurerm_data_factory.this.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

  enabled_log {
    category = "PipelineRuns"
  }
  enabled_log {
    category = "ActivityRuns"
  }
  enabled_log {
    category = "TriggerRuns"
  }

  metric {
    category = "AllMetrics"
  }
}

resource "azurerm_monitor_diagnostic_setting" "storage" {
  name                       = "diag-storage"
  target_resource_id         = "${azurerm_storage_account.lake.id}/blobServices/default"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

  metric {
    category = "Transaction"
  }
}

# ── Outputs ──────────────────────────────────────────────────────────────────
output "resource_group_name" {
  value = azurerm_resource_group.this.name
}

output "storage_account_name" {
  value = azurerm_storage_account.lake.name
}

output "data_factory_name" {
  value = azurerm_data_factory.this.name
}

output "databricks_workspace_url" {
  value = azurerm_databricks_workspace.this.workspace_url
}

output "log_analytics_workspace_id" {
  value = azurerm_log_analytics_workspace.this.workspace_id
}
