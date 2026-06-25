variable "resource_prefix" {
  description = "Short unique prefix for all resource names."
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9]{3,8}$", var.resource_prefix))
    error_message = "resource_prefix must be 3-8 lowercase letters and numbers."
  }
}

variable "environment" {
  description = "Environment name — dev or prod."
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be dev or prod."
  }
}

variable "location" {
  description = "Azure region for all resources."
  type        = string
  default     = "uksouth"
  validation {
    condition     = contains(["uksouth", "ukwest", "westeurope", "eastus", "eastus2"], var.location)
    error_message = "Location must be one of the approved regions."
  }
}

variable "owner" {
  description = "Team or person responsible (required tag)."
  type        = string
}

variable "cost_centre" {
  description = "Cost centre code for billing (required tag)."
  type        = string
  default     = "zitigroup-academy"
}

variable "workload" {
  description = "Workload name (required tag)."
  type        = string
  default     = "email-triage-assistant"
}

variable "deploy_model" {
  description = "Set true only in Week 3. Keep false to avoid cost."
  type        = bool
  default     = false
}

variable "ai_model_name" {
  description = "Model to deploy in Azure AI Foundry."
  type        = string
  default     = "gpt-4o-mini"
}

variable "ai_model_version" {
  description = "Version of the model to deploy."
  type        = string
  default     = "2024-07-18"
}

variable "ai_model_capacity" {
  description = "Tokens-per-minute capacity in thousands. Keep low in dev."
  type        = number
  default     = 10
}