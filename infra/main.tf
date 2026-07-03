# =============================================================
# RESOURCE GROUP
# Already created by ZitiGroup — we reference it, not create it.
# =============================================================
data "azurerm_resource_group" "main" {
  name = "AIE-WEP-2"
}

# =============================================================
# STORAGE ACCOUNT
# =============================================================
# Test: triggering the CI/CD pipeline via pull request 

resource "azurerm_storage_account" "main" {
  name                     = substr(lower("st${var.resource_prefix}${var.environment}"), 0, 24)
  resource_group_name      = data.azurerm_resource_group.main.name
  location                 = data.azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "GRS"

  https_traffic_only_enabled      = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  tags = {
    owner       = var.owner
    environment = var.environment
    # cost-centre and workload tags deliberately removed
    # This PR should be flagged by the governance scanner
  }
}

resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# =============================================================
# KEY VAULT
# =============================================================
resource "azurerm_key_vault" "main" {
  name                       = "kv-${local.name_suffix}"
  resource_group_name        = data.azurerm_resource_group.main.name
  location                   = data.azurerm_resource_group.main.location
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  # Your local identity (aquashie14)
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = "bc109473-a2e2-42ca-a8e9-189eb371c25e"

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Recover", "Backup", "Restore", "Purge"
    ]
  }

  # The GitHub Actions pipeline's service principal
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = "10aef510-2596-4122-9a65-c0d06ecc755f"

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Recover", "Backup", "Restore", "Purge"
    ]
  }

  tags = local.tags
}

# =============================================================
# AZURE AI FOUNDRY
# =============================================================
resource "azurerm_ai_services" "main" {
  name                = "ai-${local.name_suffix}"
  resource_group_name = data.azurerm_resource_group.main.name
  location            = data.azurerm_resource_group.main.location
  sku_name            = "S0"

  tags = local.tags
}

resource "azapi_resource" "foundry_hub" {
  type      = "Microsoft.MachineLearningServices/workspaces@2024-04-01"
  name      = "hub-${local.name_suffix}"
  location  = data.azurerm_resource_group.main.location
  parent_id = data.azurerm_resource_group.main.id

  body = jsonencode({
    kind = "Hub"
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      description    = "Foundry hub — ZitiGroup AI Academy capstone"
      friendlyName   = "hub-${local.name_suffix}"
      storageAccount = azurerm_storage_account.main.id
      keyVault       = azurerm_key_vault.main.id
    }
  })

  tags = local.tags

  depends_on = [
    azurerm_storage_account.main,
    azurerm_key_vault.main,
    azurerm_ai_services.main,
  ]
}

resource "azapi_resource" "foundry_project" {
  type      = "Microsoft.MachineLearningServices/workspaces@2024-04-01"
  name      = "proj-${local.name_suffix}"
  location  = data.azurerm_resource_group.main.location
  parent_id = data.azurerm_resource_group.main.id

  body = jsonencode({
    kind = "Project"
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      description   = "Email triage assistant — ZitiGroup AI Academy capstone"
      friendlyName  = "proj-${local.name_suffix}"
      hubResourceId = azapi_resource.foundry_hub.id
    }
  })

  tags = local.tags

  depends_on = [azapi_resource.foundry_hub]
}

# =============================================================
# MODEL DEPLOYMENT
# Keep deploy_model = false until Week 3
# =============================================================
resource "azapi_resource" "model_deployment" {
  count = var.deploy_model ? 1 : 0

  type      = "Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview"
  name      = var.ai_model_name
  parent_id = azurerm_ai_services.main.id

  body = jsonencode({
    sku = {
      name     = "GlobalStandard"
      capacity = var.ai_model_capacity
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = var.ai_model_name
        version = var.ai_model_version
      }
    }
  })

  depends_on = [azurerm_ai_services.main]
}

# =============================================================
# KEY VAULT SECRETS
# Only written when deploy_model = true
# =============================================================
resource "azurerm_key_vault_secret" "ai_endpoint" {
  count        = var.deploy_model ? 1 : 0
  name         = "ai-foundry-endpoint"
  value        = azurerm_ai_services.main.endpoint
  key_vault_id = azurerm_key_vault.main.id
  tags         = local.tags
  depends_on   = [azurerm_key_vault.main]
}

resource "azurerm_key_vault_secret" "ai_key" {
  count        = var.deploy_model ? 1 : 0
  name         = "ai-foundry-key"
  value        = azurerm_ai_services.main.primary_access_key
  key_vault_id = azurerm_key_vault.main.id
  tags         = local.tags
  depends_on   = [azurerm_key_vault.main]
}