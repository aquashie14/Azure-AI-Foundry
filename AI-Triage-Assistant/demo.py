"""
Run the triage assistant against all sample emails and print results.

Updated to display all fields the Streamlit UI shows:
  - Category + label
  - Priority
  - Confidence
  - Suggested route
  - One-line summary
  - Suggested reply draft

Usage:
    python demo.py

Set TRIAGE_MOCK_MODE=false in .env to run against live Azure AI Foundry.
"""

from config import load_config
from sample_emails import SAMPLE_EMAILS
from triage import triage_email

DIVIDER = "=" * 65


def priority_tag(priority: str) -> str:
    return f"[{priority.upper()}]" if priority == "High" else f"[{priority}]"


def main():
    config = load_config()
    mode = (
        "MOCK MODE  (no Azure call — rule-based logic)"
        if config.mock_mode
        else "LIVE MODE  (calling Azure AI Foundry via LangGraph)"
    )

    print(f"\n{DIVIDER}")
    print(f"  Task Logistics — Email Triage Assistant")
    print(f"  {mode}")
    print(f"{DIVIDER}\n")

    approved = 0
    high_priority = 0

    for email in SAMPLE_EMAILS:
        result = triage_email(email, config)

        if result.priority == "High":
            high_priority += 1

        print(f"{'─' * 65}")
        print(f"  {result.email_id}  |  {email.get('time', '')}  |  {email.get('sender', '')}")
        print(f"  Subject:  {email.get('subject') or '(no subject)'}")
        print(f"{'─' * 65}")
        print(f"  Category:   {result.category_label}  ({result.category})")
        print(f"  Priority:   {priority_tag(result.priority)}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Route:      {result.suggested_route}")
        print(f"  Summary:    {result.summary}")
        print(f"\n  Suggested reply:")
        for line in result.suggested_reply.splitlines():
            print(f"    {line}")
        print()

    print(f"{DIVIDER}")
    print(f"  Processed : {len(SAMPLE_EMAILS)} emails")
    print(f"  High priority : {high_priority}")
    print(f"\n  Human-in-the-loop: no reply is ever sent automatically.")
    print(f"  All drafts require agent review in the Streamlit UI.")
    print(f"{DIVIDER}\n")


if __name__ == "__main__":
    main()
