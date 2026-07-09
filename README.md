# Azure AI Foundry — Governed AI Platform & Email Triage Assistant

ZitiGroup AI Academy capstone project (11 June – 4 July 2026).

## Live Demo

**Hosted app:** https://tasklogisticsassistant.streamlit.app

Runs fully on Streamlit Community Cloud — no local setup required to view it.
Authenticates to Azure using its own dedicated Service Principal via
`DefaultAzureCredential()`, with no credentials stored in code.

## Project Overview

A governed Azure AI platform built with Terraform and GitHub Actions, topped with a
working, hosted AI assistant that triages customer service emails for the customer
service desk of a UK logistics operator (Task Logistics).

For each incoming email, the assistant returns:
- A **category** (e.g. delivery status, address change, claims, complaint, needs review)
- A **priority** (High / Normal)
- A **confidence score**
- A **one-line summary**
- A **suggested department route**
- A **suggested reply** for a human agent to review

A human always reviews and approves the suggested reply before anything is sent —
no email is ever sent automatically by the AI. Approved replies are delivered via
Resend, proving the full human-in-the-loop pipeline works end to end with real
email delivery.

## Status — All Core Deliverables Complete

- [x] D1 — Terraform dev platform provisioned and confirmed stable
- [x] D2 — CI/CD pipeline live: PR checks, plan comments, apply on merge
- [x] D3 — Governance pack: tfsec scanning, blocked bad PR evidence preserved
- [x] D4 — Production approval gate: triggered and approved live
- [x] D5 — AI Foundry model deployed (`gpt-5.1`) and connected live
- [x] D5 — LangChain + LangGraph triage pipeline working end to end
- [x] D5 — Streamlit UI with human approval and real email sending (Resend)
- [x] D5 — Application hosted on Streamlit Community Cloud (not local)
- [x] D6 — Promotion runbook written and merged
- [x] D6 — README (this file) updated and merged
- [ ] D6 — Demo rehearsed with full team

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
│   ├── PROMOTION_RUNBOOK.md        How a change travels dev → prod
│   └── environments/
│       ├── dev/terraform.tfvars    Dev values (gitignored)
│       └── prod/terraform.tfvars   Prod values (gitignored)
│
├── AI-Triage-Assistant/            The AI application (D5)
│   ├── streamlit_app.py            Web UI — the human review queue
│   ├── triage.py                   LangChain + LangGraph triage logic
│   ├── config.py                   Config loader (Key Vault / env vars / mock)
│   ├── sample_emails.py            9 test emails incl. edge cases
│   ├── email_sender.py             Human-approved sending via Resend
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
| Model Deployment | `gpt-5.1` | The deployed LLM the assistant calls |

## Identities and Access

Three separate identities have scoped Key Vault access, each for a different context:

| Identity | Object ID | Purpose | Scope |
|---|---|---|---|
| Local developer | `bc109473-...` | Local dev/testing | Full secret permissions |
| GitHub Actions pipeline | `10aef510-...` | CI/CD deployments | Full secret permissions |
| Streamlit Cloud app | `74262430-...` | Hosted app | `Get`, `List` only (minimal) |

The hosted app's Service Principal (`streamlit-triage-app`) was deliberately scoped
to the minimum permissions it actually needs — read-only secret access — rather
than broad Contributor rights, since it only ever needs to fetch the AI endpoint
and key at runtime.

## Platform Rules

1. **No portal clicking** — all resources provisioned through Terraform
2. **No cowboy deploys** — every change goes through a pull request
3. **No long-lived secrets** — pipeline authenticates via OIDC (4 federated
   credentials: main branch, pull_request, dev environment, production environment)
4. **Shared state** — Terraform state lives in Azure Storage, not anyone's laptop
5. **Governance built in** — required tags, security scanning (tfsec), fmt/validate checks
6. **Controlled promotion** — dev applies automatically, prod requires human approval

## CI/CD Pipeline

| Workflow | Trigger | What it does |
|---|---|---|
| `pr-checks.yml` | Pull request opened | Two jobs: `static-checks` (fmt/validate/tfsec, no Azure auth needed) then `plan` (Azure-authenticated, posts Terraform plan as a PR comment) |
| `apply.yml` | Merge to main | `apply-dev` runs automatically; `apply-prod` requires human approval before running — confirmed working via a real approval |

Authentication uses OIDC federation — no client secrets stored in GitHub. Required secrets:
- `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
- `TF_STATE_STORAGE_ACCOUNT`
- `TF_VAR_OWNER`, `TF_VAR_COST_CENTRE`

See `infra/PROMOTION_RUNBOOK.md` for the full 12-step promotion process.

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
   OUT → Streamlit UI → human reviews/edits → Approve & Send → Resend → real delivery
```

Built with **LangChain** (prompt templates, structured output parsing) and
**LangGraph** (multi-step state machine) rather than a single prompt — each
step is isolated, testable, and can fail safely into `needs_human_review`
without crashing the app.

### Three run modes

1. **Mock mode** (`TRIAGE_MOCK_MODE=true`) — rule-based keyword matching, no
   Azure call, works with zero setup. Used for local development and CI.
2. **Direct env var mode** — reads `AZURE_AI_ENDPOINT` / `AZURE_AI_KEY` straight
   from `.env`.
3. **Key Vault mode** (production pattern) — reads `AZURE_KEY_VAULT_URL`, pulls
   secrets at runtime using the caller's Azure identity. No secret ever touches
   a file. This is the mode used in the hosted deployment.

### Human-in-the-loop email sending

`email_sender.py` sends the agent-approved reply via **Resend**. It is **only
ever called from the "Approve & Send" button click** — nothing in the triage
pipeline can trigger it. If Resend isn't configured it runs in simulate mode,
logging what would be sent instead of failing, so the full flow can be demoed
without a real Resend account. Confirmed working with real email delivery to a
live inbox.

### Queue interactions

- **Hold** — pauses triage on an email; clicking Analyse again resumes it
- **Assign** — marks an email as assigned to an agent
- **Needs edit** — flags a draft reply for further editing before sending;
  clears automatically once approved
- All three use `st.session_state` so status persists across UI reruns

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
  -var="ai_model_name=gpt-5.1" -var="ai_model_version=2025-11-13" \
  -var="ai_model_capacity=3"
terraform apply   # add the same -var flags, then type yes
```

### AI Assistant — local
```bash
cd AI-Triage-Assistant
pip install -r requirements.txt
cp .env.example .env
```
Edit `.env`:
```
TRIAGE_MOCK_MODE=false
AZURE_KEY_VAULT_URL=https://kv-aqsh-dev.vault.azure.net/
AZURE_AI_MODEL_NAME=gpt-5.1
RESEND_API_KEY=re_your_key_here
```
Then:
```bash
streamlit run streamlit_app.py
```

### AI Assistant — hosted (Streamlit Community Cloud)

Already deployed at https://tasklogisticsassistant.streamlit.app. To redeploy
or reconfigure:

1. share.streamlit.io → sign in with GitHub
2. Repository: `aquashie14/Azure-AI-Foundry`, branch `main`, main file
   `AI-Triage-Assistant/streamlit_app.py`
3. Advanced settings → Secrets (TOML format):
```toml
AZURE_CLIENT_ID = "<streamlit-triage-app appId>"
AZURE_CLIENT_SECRET = "<service principal password>"
AZURE_TENANT_ID = "<tenant id>"
AZURE_KEY_VAULT_URL = "https://kv-aqsh-dev.vault.azure.net/"
AZURE_AI_MODEL_NAME = "gpt-5.1"
TRIAGE_MOCK_MODE = "false"
RESEND_API_KEY = "re_your_key_here"
RESEND_FROM_ADDRESS = "Task Logistics <onboarding@resend.dev>"
```

The hosted app authenticates using a dedicated Service Principal
(`streamlit-triage-app`) with `DefaultAzureCredential()`, which automatically
picks up `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` / `AZURE_TENANT_ID` from
the environment — no code changes needed, no `az login` required on the host.

## Key Lessons Learned

- **OIDC needs one federated credential per context** — pull requests, pushes
  to main, and each GitHub Environment (`dev`, `production`) each present a
  different `subject` claim to Azure AD and needed their own credential.
- **`terraform.tfvars` is gitignored**, so the pipeline reads all variables as
  `TF_VAR_*` environment variables instead — sensitive ones from GitHub
  Secrets, non-sensitive ones inline in the workflow.
- **Key Vault access policies must include every identity that touches it** —
  local developer, pipeline service principal, and the hosted app's service
  principal each needed their own policy block, or applying from one context
  would revoke another's access.
- **Azure AD (identity) and Azure RBAC (permissions) are separate systems** —
  a Service Principal needs both a federated credential/role in Azure AD *and*
  a role assignment in RBAC; having one without the other produces confusingly
  different error messages (`AuthorizationFailed` vs `No matching federated
  identity record found`).
- **Least-privilege access is achievable without admin approval** — rather
  than requesting broad Contributor rights for the hosted app (which needed
  Owner-level sign-off we didn't have), granting narrow Key Vault `Get`/`List`
  permissions directly achieved the same functional outcome with a much
  smaller blast radius.
- **`gpt-5-mini` and early `gpt-5.1` configs are reasoning-adjacent** — they
  spend tokens on invisible internal reasoning before writing visible output.
  A `max_tokens=500` budget silently produced empty replies; raising it (or
  switching model) fixed this. Reasoning-heavy models also sometimes reject
  custom `temperature` values entirely.
- **`api_version` and a model's release version are easy to confuse** — setting
  the Azure OpenAI REST `api_version` to a model's version string (e.g.
  `"2025-11-13"`, the model's release date) rather than a valid API version
  (`"2024-10-21"`) produces a 404 that looks like a missing deployment, when
  the deployment is actually fine.
- **`gpt-4o-mini` was deprecated mid-project** and could no longer accept new
  deployments — required switching models twice (`gpt-5-mini`, then `gpt-5.1`)
  and adjusting client configuration accordingly each time.
- **Git Bash mangles Unix-style resource paths on Windows** — commands
  containing `/subscriptions/...` get silently corrupted by MSYS path
  translation; running Azure CLI commands from PowerShell instead avoided
  this entirely.

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

*ZitiGroup AI Academy — AI Engineering Work Experience Programme, June–July 2026*