# Azure AI Foundry — Governed AI Platform & Email Triage Assistant

ZitiGroup AI Academy capstone project (11–27 June 2026).

## Project Overview

A governed Azure AI platform built with Terraform and GitHub Actions, topped with a
working AI assistant that triages customer service emails for the customer service
desk of a UK logistics operator (Task Logistics).

For each incoming email, the assistant returns:
- A **category** (e.g. delivery status, address change, claims, complaint, needs review)
- A **priority** (High / Normal)
- A **confidence score**
- A **one-line summary**
- A **suggested department route**
- A **suggested reply** for a human agent to review

A human always reviews and approves the suggested reply before anything is sent —
no email is ever sent automatically by the AI.

## Status

- [x] Azure sandbox access confirmed
- [x] Terraform dev platform provisioned (D1)
- [x] CI/CD pipeline live — PR checks, plan comments, apply on merge (D2)
- [x] Governance pack — tfsec scanning, blocked bad PR evidence (D3)
- [ ] Production environment + promotion gate triggered (D4)
- [x] AI Foundry model deployed (`gpt-5-mini`) and connected live (D5)
- [x] LangChain + LangGraph triage pipeline working end to end (D5)
- [x] Streamlit UI with human approval and email sending (D5)
- [ ] Promotion runbook written (D4/D6)
- [ ] Demo rehearsed (D6)

## Repo Structure

```
Azure-AI-Foundry/
├── README.md                       This file
├── .gitignore
│
├── infra/                          Terraform infrastructure (D1–D4)
│   ├── main.tf                     All Azure resources
│   ├── providers.tf                Provider config + remote backend
│   ├── variables.tf                Input variable declarations
│   ├── locals.tf                   Shared tags and naming patterns
│   ├── outputs.tf                  Values printed after apply
│   ├── .terraform.lock.hcl         Provider version lock (committed)
│   ├── README.md                   Infra-specific documentation
│   └── environments/
│       ├── dev/terraform.tfvars    Dev values (gitignored)
│       └── prod/terraform.tfvars   Prod values (gitignored)
│
├── AI-Triage-Assistant/            The AI application (D5)
│   ├── streamlit_app.py            Web UI — the human review queue
│   ├── triage.py                   LangChain + LangGraph triage logic
│   ├── config.py                   Config loader (Key Vault / env vars / mock)
│   ├── sample_emails.py            9 test emails incl. edge cases
│   ├── email_sender.py             Human-approved SMTP sending
│   ├── demo.py                     CLI demo runner
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
│
└── .github/workflows/
    ├── pr-checks.yml                Runs on every PR: fmt, validate, tfsec, plan
    └── apply.yml                    Runs on merge to main: apply dev, then prod
```

## What This Provisions

| Resource | Name | Purpose |
|---|---|---|
| Resource Group | `AIE-WEP-2` | Container for all resources (pre-created by ZitiGroup) |
| Storage Account | `staqshdev` | Terraform state + future SOP documents |
| Key Vault | `kv-aqsh-dev` | Stores AI endpoint and key securely |
| AI Services | `ai-aqsh-dev` | Azure AI Foundry account |
| Foundry Hub | `hub-aqsh-dev` | Shared workspace for AI projects |
| Foundry Project | `proj-aqsh-dev` | Project scoped under the hub |
| Model Deployment | `gpt-5-mini` | The deployed LLM the assistant calls |

## Platform Rules

1. **No portal clicking** — all resources provisioned through Terraform
2. **No cowboy deploys** — every change goes through a pull request
3. **No long-lived secrets** — pipeline authenticates via OIDC (4 federated credentials: main branch, pull_request, dev environment, production environment)
4. **Shared state** — Terraform state lives in Azure Storage, not anyone's laptop
5. **Governance built in** — required tags, security scanning (tfsec), fmt/validate checks
6. **Controlled promotion** — dev applies automatically, prod requires human approval

## CI/CD Pipeline

| Workflow | Trigger | What it does |
|---|---|---|
| `pr-checks.yml` | Pull request opened | Two jobs: `static-checks` (fmt/validate/tfsec, no Azure auth needed) then `plan` (Azure-authenticated, posts Terraform plan as a PR comment) |
| `apply.yml` | Merge to main | `apply-dev` runs automatically; `apply-prod` requires human approval before running |

Authentication uses OIDC federation — no client secrets stored in GitHub. Required secrets:
- `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
- `TF_STATE_STORAGE_ACCOUNT`
- `TF_VAR_OWNER`, `TF_VAR_COST_CENTRE`

## The AI Assistant

### Architecture

```
Email IN
   │
[classify]  → category + priority + confidence   (LangGraph node 1)
   │
[route]     → needs_human_review? → [flag] → OUT
   │           clear category?    → continue
   │
[summarise] → one-line summary                    (LangGraph node 3)
   │
[reply]     → drafted reply for agent review       (LangGraph node 4)
   │
   OUT → Streamlit UI → human reviews/edits → Approve & Send → email_sender.py
```

Built with **LangChain** (prompt templates, output parsing) and **LangGraph**
(multi-step state machine) rather than a single prompt — each step is isolated,
testable, and can fail safely into `needs_human_review` without crashing the app.

### Three run modes

1. **Mock mode** (`TRIAGE_MOCK_MODE=true`) — rule-based keyword matching, no Azure
   call, works with zero setup. Used for local development and CI.
2. **Direct env var mode** — reads `AZURE_AI_ENDPOINT` / `AZURE_AI_KEY` straight
   from `.env`.
3. **Key Vault mode** (production pattern) — reads `AZURE_KEY_VAULT_URL`, pulls
   secrets at runtime using the caller's Azure identity. No secret ever touches
   a file. This is the mode used for the live demo.

### Human-in-the-loop email sending

`email_sender.py` sends the agent-approved reply via SMTP. It is **only ever
called from the "Approve & Send" button click** — nothing in the triage pipeline
can trigger it. If SMTP isn't configured it runs in simulate mode, logging what
would be sent instead of failing, so the full flow can be demoed without real
email credentials.

## Setup

### Prerequisites
- Terraform 1.6.6, Azure CLI, Python 3.11+, `az login` completed
- Contributor access to the `AIE-WEP-2` resource group

### Infrastructure
```bash
cd infra
terraform init
terraform plan -var="environment=dev" -var="deploy_model=true" \
  -var="resource_prefix=aqsh" -var="owner=aquashie14" \
  -var="cost_centre=zitigroup-academy" -var="workload=email-triage-assistant" \
  -var="ai_model_name=gpt-5-mini" -var="ai_model_version=2025-08-07" \
  -var="ai_model_capacity=3"
terraform apply   # add the same -var flags, then type yes
```

### AI Assistant
```bash
cd AI-Triage-Assistant
pip install -r requirements.txt
cp .env.example .env
```
Edit `.env`:
```
TRIAGE_MOCK_MODE=false
AZURE_KEY_VAULT_URL=https://kv-aqsh-dev.vault.azure.net/
AZURE_AI_MODEL_NAME=gpt-5-mini
```
Then:
```bash
streamlit run streamlit_app.py
```
Sidebar should show **"Azure AI Foundry connected."** Select an email, click
Analyse, wait ~10–15 seconds (the model runs 3 sequential calls: classify,
summarise, reply).

## Key Lessons Learned

- **OIDC needs one federated credential per context** — pull requests, pushes
  to main, and each GitHub Environment (`dev`, `production`) each present a
  different `subject` claim to Azure AD and needed their own credential.
- **`terraform.tfvars` is gitignored**, so the pipeline reads all variables as
  `TF_VAR_*` environment variables instead — sensitive ones from GitHub
  Secrets, non-sensitive ones inline in the workflow.
- **Key Vault access policies must include every identity that touches it** —
  local developer and pipeline service principal both need their own policy
  block, or switching between local and pipeline runs revokes the other's access.
- **`gpt-5-mini` is a reasoning model** — it spends tokens on invisible internal
  reasoning before writing visible output. A `max_tokens=500` budget silently
  produced empty replies because reasoning alone consumed the full budget;
  raising it to `2000` fixed this. Reasoning models also only support the
  default `temperature` value (no custom temperature allowed).
- **`gpt-4o-mini` was deprecated mid-project** and could no longer accept new
  deployments — required switching to `gpt-5-mini` and updating the API version
  used by the LangChain client accordingly.

## Contacts

| Role | Name |
|---|---|
| Mentor | Ayodele Ajayi |
| Weekday build support | Ukachi |
| Programme contact | Ebelechukwu Anaoji (ZitiGroup) |

## Timeline

| Date | Milestone |
|---|---|
| Thu 11 Jun | Kickoff |
| Sat 13 Jun | Check-in 1 — foundations ready |
| Sat 20 Jun | Check-in 2 — platform live |
| Sat 4 Jul | Final demo |

---

*ZitiGroup AI Academy — AI Engineering Work Experience Programme, June 2026*