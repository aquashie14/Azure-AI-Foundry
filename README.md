# Azure AI Foundry — Governed AI Platform & Email Triage Assistant

ZitiGroup AI Academy capstone project (11–27 June 2026).

## Project Overview

A governed Azure AI platform built with Terraform and GitHub Actions, topped with a
proof-of-concept AI assistant that triages customer service emails for the (anonymised)
customer service desk of a UK logistics operator.

For each incoming email, the assistant returns:
- A **category** (e.g. delivery status, address change, claims)
- A **one-line summary**
- A **suggested reply**

A human always reviews the suggested reply before anything is sent — no email is sent
automatically.

## Status

🚧 **Project setup in progress.** This repo will be built out from the
`terraform-foundry-demo` scaffold once access is confirmed.

- [ ] Azure sandbox access confirmed
- [ ] Scaffold imported
- [ ] Terraform remote state backend configured
- [ ] OIDC federation set up (GitHub Actions ↔ Azure)
- [ ] Dev environment applied (D1)
- [ ] CI/CD pipeline live (D2)
- [ ] Governance pack in place (D3)
- [ ] Production environment + promotion gate (D4)
- [ ] Triage assistant built and tested (D5)
- [ ] Documentation and demo ready (D6)

## Platform Rules

1. **No portal clicking.** All infrastructure is provisioned through Terraform.
2. **No cowboy deploys.** Every change goes through a pull request with a visible
   Terraform plan before merge.
3. **No long-lived secrets.** The pipeline authenticates to Azure with OIDC federation.
4. **Shared state.** Terraform state lives in Azure Storage, not on anyone's laptop.
5. **Governance built in.** Security scanning, required tags, approved regions, and
   cost controls are enforced in the delivery path.
6. **Controlled promotion.** Dev is automatic; production requires a human approval gate.

## Team

| Role | Owner |
|---|---|
| Platform engineer | TBD |
| Pipeline engineer | TBD |
| Governance engineer | TBD |
| AI application engineer | TBD |
| Delivery lead (rotating weekly) | TBD |

## Tooling Checklist

- [ ] Git + GitHub account
- [ ] Terraform 1.6+
- [ ] Azure CLI
- [ ] GitHub CLI
- [ ] VS Code + HashiCorp Terraform extension
- [ ] Python 3.11+

## Mentor & Contacts

- **Mentor:** Ayodele Ajayi
- **Weekday build support:** Ukachi
- **Programme contact:** Ebelechukwu Anaoji (ZitiGroup)

## Timeline

| Date | Milestone |
|---|---|
| Thu 11 Jun | Kickoff |
| Sat 13 Jun | Check-in 1 — foundations ready |
| Sat 20 Jun | Check-in 2 — platform live |
| Sat 27 Jun | Check-in 3 — final demo |

---

*Confidential case study material from ZitiGroup AI Academy. Client context is
anonymised and representative.*
