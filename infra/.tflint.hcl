# Configure TFLint configuration file (.tflint.hcl), a linting tool for Terraform code. 
# To defines plugins and rules to enforce best practices and catch errors in your Terraform configurations. 

plugin "azurerm" {
  enabled = true
  version = "0.27.0"
  source  = "registry.terraform.io/terraform-linters/tflint-ruleset-azurerm"
}

rule "terraform_naming_convention" {
  enabled = true
}

rule "terraform_required_version" {
  enabled = true
}

rule "terraform_unused_declarations" {
  enabled = true
}
