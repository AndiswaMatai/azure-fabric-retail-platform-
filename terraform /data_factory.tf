# Azure Data Factory — orchestrates the medallion pipeline: triggers the
# landing-zone copy activities, then invokes the Databricks Job that runs
# the notebooks in databricks/notebooks/ against Delta tables on OneLake.

resource "azurerm_data_factory" "this" {
  name                = "adf-${local.prefix}"
  location             = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

# Grant ADF's managed identity access to the lake — no stored credentials
resource "azurerm_role_assignment" "adf_storage_contributor" {
  scope                = azurerm_storage_account.lake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.this.identity[0].principal_id
}

# Linked service: Databricks, authenticated via ADF managed identity (no PAT tokens)
resource "azurerm_data_factory_linked_service_azure_databricks" "this" {
  name                = "ls_databricks"
  data_factory_id     = azurerm_data_factory.this.id
  description         = "Linked service to the Databricks workspace running the medallion notebooks"
  adb_domain          = "https://${azurerm_databricks_workspace.this.workspace_url}"
  msi_work_space_resource_id = azurerm_databricks_workspace.this.id

  existing_cluster_id = "" # left blank intentionally; production uses a Job cluster defined in databricks/job_config.json
}

# Trigger: scheduled daily run, mirrors the medallion pipeline's batch cadence.
# Real-time ingestion (loyalty events at POS) is handled separately via
# Event Hubs -> Fabric Eventstream, documented in docs/architecture.md
resource "azurerm_data_factory_trigger_schedule" "daily" {
  name            = "trg_daily_medallion_refresh"
  data_factory_id = azurerm_data_factory.this.id
  pipeline_name   = "pl_medallion_refresh" # defined in adf/pipelines/pl_medallion_refresh.json

  interval  = 1
  frequency = "Day"
  start_time = "2026-01-01T02:00:00Z" # off-peak, before business hours in SAST

  activated = var.environment == "prod" ? true : false
}
