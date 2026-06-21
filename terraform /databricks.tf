# Databricks workspace — runs the medallion notebooks (databricks/notebooks/)
# as a scheduled Job triggered by ADF. Cluster policy enforces autoscaling
# and spot instances for cost control (see cost_optimization/).

resource "azurerm_databricks_workspace" "this" {
  name                = "dbw-${local.prefix}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  sku                 = var.databricks_sku

  custom_parameters {
    no_public_ip = true # secure cluster connectivity, no public IPs on cluster nodes
  }

  tags = local.common_tags
}

# Cluster policy: caps cluster size and enforces autoscaling + spot instances
# so a misconfigured notebook can't run away with cost. Referenced by the
# Databricks Job definition in databricks/job_config.json.
resource "databricks_cluster_policy" "medallion_job_policy" {
  name = "medallion-job-policy-${local.environment}"

  definition = jsonencode({
    "autoscale.min_workers" = {
      type     = "fixed"
      value    = 2
    }
    "autoscale.max_workers" = {
      type     = "fixed"
      value    = var.environment == "prod" ? 8 : 4
    }
    "azure_attributes.availability" = {
      type  = "fixed"
      value = "SPOT_WITH_FALLBACK_AZURE" # cost optimization: spot first, fall back to on-demand
    }
    "node_type_id" = {
      type  = "allowlist"
      values = ["Standard_DS3_v2", "Standard_DS4_v2"]
    }
    "spark_version" = {
      type  = "fixed"
      value = "14.3.x-scala2.12" # LTS runtime
    }
    "autotermination_minutes" = {
      type  = "fixed"
      value = 15 # cost optimization: kill idle clusters fast
    }
  })
}
