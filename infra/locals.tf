# Local values — computed once, reused everywhere.
# This keeps resource names consistent and tags DRY.

data "azurerm_client_config" "current" {}

locals {
  # Naming pattern: {prefix}-{workload-short}-{env}
  name_suffix = "${var.resource_prefix}-${var.environment}"

  # Required tags — every resource must carry all four.
  # D3 governance: the pipeline will block PRs missing these.
  tags = {
    owner       = var.owner
    environment = var.environment
    cost-centre = var.cost_centre
    workload    = var.workload
  }
}
