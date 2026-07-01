terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
    azapi = {
      source  = "azure/azapi"
      version = "~> 1.13"
    }
  }

  # Remote state backend — lives in Azure Storage, not on anyone's laptop.
  # The storage account and container must exist BEFORE you run terraform init.
  # See the README for the one-time bootstrap commands to create them.
  backend "azurerm" {
    resource_group_name  = "AIE-WEP-2"
    storage_account_name = "staqshtfstate"
    container_name       = "tfstate"
    key                  = "dev.terraform.tfstate"
  }
}

# Azure provider — authenticates via OIDC in the pipeline (no stored secrets),
# or via 'az login' locally.
provider "azurerm" {
  skip_provider_registration = true

  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}

provider "azapi" {}
