# Monitoring & Alerting — Azure Monitor alert rules wired to the Log
# Analytics workspace provisioned in terraform/security_and_monitoring.tf.
# These are the "what wakes someone up" rules for the platform.
#
# Apply alongside the main Terraform config:
#   terraform apply -var-file="../terraform/environments/prod.tfvars"
#
# (kept in its own file/folder so monitoring can be reasoned about and
# reviewed independently of the core infrastructure changes)

resource "azurerm_monitor_action_group" "platform_oncall" {
  name                = "ag-retailloyalty-oncall"
  resource_group_name = var.resource_group_name
  short_name          = "rl-oncall"

  email_receiver {
    name          = "platform-owner"
    email_address = var.owner_email
  }

  webhook_receiver {
    name        = "teams-channel"
    service_uri = var.teams_webhook_url
  }
}

# Alert 1: ADF pipeline failure (any activity in pl_medallion_refresh.json)
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "pipeline_failure" {
  name                = "alert-adf-pipeline-failure"
  resource_group_name = var.resource_group_name
  location            = var.location

  evaluation_frequency = "PT15M"
  window_duration       = "PT15M"
  scopes                = [var.log_analytics_workspace_id]
  severity              = 1 # critical — Gold tables may be stale or wrong

  criteria {
    query                   = <<-KQL
      ADFPipelineRun
      | where Status == "Failed"
      | where PipelineName == "pl_medallion_refresh"
    KQL
    time_aggregation_method = "Count"
    threshold               = 0
    operator                = "GreaterThan"

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  action {
    action_groups = [azurerm_monitor_action_group.platform_oncall.id]
  }

  description = "Fires when pl_medallion_refresh fails for any reason — landing copy, Databricks Job, or the DQ gate (run_dq_suite_gate activity)."
}

# Alert 2: Data quality gate failure specifically — distinguishes "DQ caught
# something real" from "infrastructure broke", since the response differs.
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "dq_gate_failure" {
  name                = "alert-data-quality-gate-failure"
  resource_group_name = var.resource_group_name
  location            = var.location

  evaluation_frequency = "PT15M"
  window_duration       = "PT15M"
  scopes                = [var.log_analytics_workspace_id]
  severity              = 2

  criteria {
    query                   = <<-KQL
      ADFActivityRun
      | where ActivityName == "run_dq_suite_gate"
      | where Status == "Failed"
    KQL
    time_aggregation_method = "Count"
    threshold               = 0
    operator                = "GreaterThan"

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  action {
    action_groups = [azurerm_monitor_action_group.platform_oncall.id]
  }

  description = "Fires specifically when data_quality/run_dq_suite.py-equivalent checks fail in production, e.g. referential integrity broke after an upstream schema change."
}

# Alert 3: Databricks job runtime anomaly — catches cost runaways and stuck clusters
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "databricks_runtime_anomaly" {
  name                = "alert-databricks-runtime-exceeded"
  resource_group_name = var.resource_group_name
  location            = var.location

  evaluation_frequency = "PT30M"
  window_duration       = "PT30M"
  scopes                = [var.log_analytics_workspace_id]
  severity              = 3

  criteria {
    query                   = <<-KQL
      DatabricksJobs
      | where JobName == "medallion_daily_refresh"
      | where DurationMinutes > 90
    KQL
    time_aggregation_method = "Count"
    threshold               = 0
    operator                = "GreaterThan"

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  action {
    action_groups = [azurerm_monitor_action_group.platform_oncall.id]
  }

  description = "Expected runtime for the medallion Job is ~25-35 minutes against current data volumes. >90 minutes usually means a cluster failed to autoscale, fell back off spot capacity, or upstream data volume spiked unexpectedly."
}
