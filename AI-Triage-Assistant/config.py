"""
Configuration loader for the email triage assistant.

Design rule from the project brief: no hardcoded keys, anywhere.
This module supports two ways of getting the Azure AI Foundry
endpoint + key, in priority order:

1. Key Vault (production pattern). If AZURE_KEY_VAULT_URL is set,
   pull the endpoint and key from Key Vault using whatever Azure
   identity is currently logged in (az login locally, or the
   pipeline's OIDC identity in CI/CD). No secret ever touches a
   local .env file in this mode.

2. Environment variables (local dev shortcut). Reads
   AZURE_AI_ENDPOINT / AZURE_AI_KEY straight from the environment,
   which you set via a local .env file that is gitignored.

If neither is configured, the assistant runs in mock mode so you
can build and test the rest of the pipeline before Azure access
is confirmed.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class TriageConfig:
    mock_mode: bool
    endpoint: str | None
    key: str | None
    model_name: str | None


def _load_from_key_vault(vault_url: str) -> tuple[str, str]:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)

    endpoint = client.get_secret("ai-foundry-endpoint").value
    key = client.get_secret("ai-foundry-key").value
    return endpoint, key


def load_config() -> TriageConfig:
    mock_mode = os.getenv("TRIAGE_MOCK_MODE", "true").lower() == "true"
    model_name = os.getenv("AZURE_AI_MODEL_NAME")
    vault_url = os.getenv("AZURE_KEY_VAULT_URL")

    if mock_mode:
        return TriageConfig(mock_mode=True, endpoint=None, key=None, model_name=model_name)

    if vault_url:
        endpoint, key = _load_from_key_vault(vault_url)
    else:
        endpoint = os.getenv("AZURE_AI_ENDPOINT")
        key = os.getenv("AZURE_AI_KEY")

    if not endpoint or not key:
        raise RuntimeError(
            "Missing Azure AI endpoint/key. Set AZURE_KEY_VAULT_URL, or "
            "AZURE_AI_ENDPOINT + AZURE_AI_KEY in your .env, or set "
            "TRIAGE_MOCK_MODE=true to run without Azure."
        )

    return TriageConfig(mock_mode=False, endpoint=endpoint, key=key, model_name=model_name)
