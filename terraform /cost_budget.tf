# Cost control — an Azure Consumption Budget that alerts at 80% and 100%
# of monthly spend, sent straight to the platform owner. Paired with the
# storage lifecycle rules (storage.tf) and Databricks autoscaling/spot
# policy (databricks.tf), this is the full cost-optimization control set
# documented in cost_optimization/README.md.

resource "azurerm_consumption_budget_resource_group" "this" {
  name              = "budget-${local.prefix}"
  resource_group_id = azurerm_resource_group.this.id

  amount     = var.monthly_budget_zar
  time_grain = "Monthly"

  time_period {
    start_date = "2026-01-01T00:00:00Z"
  }

  notification {
    enabled        = true
    threshold      = 80.0
    operator       = "GreaterThan"
    threshold_type = "Actual"

    contact_emails = [
      var.owner_email,
    ]
  }

  notification {
    enabled        = true
    threshold      = 100.0
    operator       = "GreaterThan"
    threshold_type = "Forecasted"

    contact_emails = [
      var.owner_email,
    ]
  }
}
