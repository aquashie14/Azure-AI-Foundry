output "resource_group_name" {
  description = "Name of the resource group."
  value       = data.azurerm_resource_group.main.name
}

output "storage_account_name" {
  description = "Name of the storage account."
  value       = azurerm_storage_account.main.name
}

output "key_vault_name" {
  description = "Name of the Key Vault."
  value       = azurerm_key_vault.main.name
}

output "key_vault_url" {
  description = "URL of the Key Vault — set as AZURE_KEY_VAULT_URL in the triage assistant."
  value       = azurerm_key_vault.main.vault_uri
}

output "ai_services_name" {
  description = "Name of the Azure AI Services account."
  value       = azurerm_ai_services.main.name
}

output "ai_services_endpoint" {
  description = "Endpoint URL for the AI Services account."
  value       = azurerm_ai_services.main.endpoint
}

output "foundry_hub_name" {
  description = "Name of the AI Foundry hub."
  value       = azapi_resource.foundry_hub.name
}

output "foundry_project_name" {
  description = "Name of the AI Foundry project."
  value       = azapi_resource.foundry_project.name
}

output "model_deployment_name" {
  description = "Name of the deployed model (empty if deploy_model = false)."
  value       = var.deploy_model ? azapi_resource.model_deployment[0].name : "not deployed yet"
}