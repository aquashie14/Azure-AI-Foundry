"""
Run the triage assistant against the sample emails and print results.

This is the script you run live in the demo (D5 acceptance criteria:
"Run live in the demo against the deployed endpoint").

Usage:
    python demo.py
"""

from config import load_config
from sample_emails import SAMPLE_EMAILS
from triage import triage_email


def main():
    config = load_config()
    mode = "MOCK MODE (no Azure call)" if config.mock_mode else "LIVE MODE (calling Azure AI Foundry)"
    print(f"\n{'=' * 60}")
    print(f"Email Triage Assistant - {mode}")
    print(f"{'=' * 60}\n")

    for email in SAMPLE_EMAILS:
        result = triage_email(email, config)

        print(f"--- {result.email_id} ---")
        print(f"Subject:  {email.get('subject') or '(no subject)'}")
        print(f"Category: {result.category}")
        print(f"Summary:  {result.summary}")
        print(f"Reply:    {result.suggested_reply}")
        print()


if __name__ == "__main__":
    main()
