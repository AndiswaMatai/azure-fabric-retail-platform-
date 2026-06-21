variable "resource_group_name" {
  description = "Resource group containing the platform resources (output from the root module: terraform/security_and_monitoring.tf)"
  type        = string
}

variable "location" {
  type    = string
  default = "South Africa North"
}

variable "log_analytics_workspace_id" {
  description = "Output from terraform/security_and_monitoring.tf: azurerm_log_analytics_workspace.this.id"
  type        = string
}

variable "owner_email" {
  type = string
}

variable "teams_webhook_url" {
  description = "Microsoft Teams incoming webhook URL for the on-call channel"
  type        = string
  sensitive   = true
}
