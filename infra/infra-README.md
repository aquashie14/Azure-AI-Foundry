# Infrastructure — Azure AI Foundry Platform

Terraform configuration for the governed Azure AI platform built as part of the
ZitiGroup AI Academy capstone (11–27 June 2026).

---

## What This Provisions

| Resource | Name | Purpose |
|---|---|---|
| Resource Group | `AIE-WEP-2` | Container for all resources (pre-created by ZitiGroup) |
| Storage Account | `staqshdev` | Terraform state + SOP documents (stretch goal) |
| Key Vault | `kv-aqsh-dev` | Stores AI endpoint and key securely |
| AI Services | `ai-aqsh-dev` | Azure AI Foundry account |
| Foundry Hub | `hub-aqsh-dev` | Shared workspace for AI projects |
| Foundry Project | `proj-aqsh-dev` | Project scoped under the hub |

---

## Folder Structure

```
infra/
├── main.tf                     All Azure resources
├── providers.tf                Azure provider + remote backend config
├── variables.tf                Input variable declarations
├── locals.tf                   Shared tags and naming patterns
├── outputs.tf                  Values printed after apply
├── .terraform.lock.hcl         Provider version lock — commit this
└── environments/
    ├── dev/terraform.tfvars    Dev variable values (gitignored)
    └── prod/terraform.tfvars   Prod variable values (gitignored)
```

---

## Platform Rules

1. **No portal clicking** — all resources provisioned through Terraform
2. **No cowboy deploys** — every change goes through a pull request
3. **No long-lived secrets** — pipeline authenticates via OIDC
4. **Shared state** — Terraform state lives in Azure Storage, not anyone's laptop
5. **Governance built in** — required tags, approved regions, security scanning
6. **Controlled promotion** — dev applies automatically, prod requires human approval

---

## Prerequisites

Before running any Terraform commands make sure you have:

- Terraform 1.6 or later — `terraform -version`
- Azure CLI — `az --version`
- Logged into Azure — `az login`
- Contributor access to the `AIE-WEP-2` resource group

---

## One-Time Backend Setup

The Terraform state storage account and container were created manually
before `terraform init` could run (chicken-and-egg problem — Terraform
needs somewhere to store state before it can manage anything).

```bash
# Create the blob container inside the existing storage account
az storage container create --name tfstate --account-name staqshtfstate --auth-mode login
```

This only needs to be done once. After this, `terraform init` connects
to the remote backend automatically.

---

## Usage

### Initialise
```bash
cd infra
terraform init
```

### Validate
```bash
terraform validate
```

### Plan — dev
```bash
terraform plan -var-file="environments/dev/terraform.tfvars"
```

### Apply — dev
```bash
terraform apply -var-file="environments/dev/terraform.tfvars"
```

### Plan — prod (requires human approval gate in GitHub Actions)
```bash
terraform plan -var-file="environments/prod/terraform.tfvars"
```

### Apply — prod
```bash
terraform apply -var-file="environments/prod/terraform.tfvars"
```

### Destroy dev environment when done
```bash
terraform plan -destroy -out main.destroy.tfplan -var-file="environments/dev/terraform.tfvars"
terraform apply main.destroy.tfplan
```

---

## Required Tags

Every resource must carry all four of these tags or the governance
scanner will block the PR:

| Tag | Value |
|---|---|
| `owner` | `aquashie14` |
| `environment` | `dev` or `prod` |
| `cost-centre` | `zitigroup-academy` |
| `workload` | `email-triage-assistant` |

---

## Key Outputs After Apply

Run `terraform output` to see these values after a successful apply:

| Output | Value |
|---|---|
| `resource_group_name` | `AIE-WEP-2` |
| `storage_account_name` | `staqshdev` |
| `key_vault_name` | `kv-aqsh-dev` |
| `key_vault_url` | `https://kv-aqsh-dev.vault.azure.net/` |
| `ai_services_name` | `ai-aqsh-dev` |
| `ai_services_endpoint` | `https://uksouth.api.cognitive.microsoft.com/` |
| `foundry_hub_name` | `hub-aqsh-dev` |
| `foundry_project_name` | `proj-aqsh-dev` |
| `model_deployment_name` | `not deployed yet` (until Week 3) |

---

## Connecting the Triage Assistant

After `deploy_model = true` is applied in Week 3, update
`AI-Triage-Assistant/.env` with:

```
TRIAGE_MOCK_MODE=false
AZURE_KEY_VAULT_URL=https://kv-aqsh-dev.vault.azure.net/
```

The Python assistant will then read the AI endpoint and key directly
from Key Vault at runtime — no secrets ever stored in source code.

---

## Cost Controls

- `deploy_model = false` is the default — model deployments are the
  main cost line, keep this false until Week 3
- One unique `resource_prefix` per team (`aqsh`) to avoid name collisions
- Destroy dev resources at the end of the programme:
  `terraform plan -destroy -out main.destroy.tfplan`
- Never leave unused resources running

---

## CI/CD Pipeline (D2)

GitHub Actions workflows live in `.github/workflows/`:

| Workflow | Trigger | What it does |
|---|---|---|
| `pr-checks.yml` | Pull request opened | fmt, validate, security scan, plan posted as PR comment |
| `apply.yml` | Merge to main | Apply to dev automatically, prod requires approval |

Authentication to Azure uses OIDC federation — no client secrets
stored in GitHub. Only these secrets are needed:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `TF_STATE_STORAGE_ACCOUNT`

---

## Contacts

| Role | Name |
|---|---|
| Mentor | Ayodele Ajayi |
| Weekday build support | Ukachi |
| Programme contact | Ebelechukwu Anaoji (ZitiGroup) |

---

*ZitiGroup AI Academy — AI Engineering Work Experience Programme, June 2026*
