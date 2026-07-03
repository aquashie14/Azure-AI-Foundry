"""
email_sender.py — sends the approved reply via Resend's API directly.

IMPORTANT DESIGN RULE (per the project brief):
No reply is EVER sent automatically. This module is only ever called
from one place: the "Approve & Send" button click in streamlit_app.py,
after a human has read and (optionally edited) the AI's suggested reply.

Nothing in triage.py, config.py, or the LangGraph pipeline can call
this module. Sending is a deliberate, separate, human-triggered action.

SETUP (all optional — the app works fine without this configured):
1. Sign up at resend.com (free tier: 100 emails/day)
2. Create an API key in the dashboard
3. Add to your .env:
     RESEND_API_KEY=re_your_key_here

If RESEND_API_KEY is not set, send_email() runs in "simulate" mode:
it does not make any network call, just returns a success result so
the demo flow still works end to end without a real Resend account.

NOTE: until you verify your own sending domain with Resend, the default
sender "onboarding@resend.dev" can only deliver to the email address
you signed up to Resend with. Verify a domain in the Resend dashboard
to send to arbitrary recipient addresses.
"""

import os
from dataclasses import dataclass

import requests

RESEND_API_URL = "https://api.resend.com/emails"


@dataclass
class SendResult:
    sent: bool
    simulated: bool
    message: str


def is_resend_configured() -> bool:
    return bool(os.getenv("RESEND_API_KEY"))


def send_email(to_address: str, subject: str, body: str) -> SendResult:
    """
    Sends the human-approved reply via Resend's API.

    If Resend isn't configured, simulates a successful send instead of
    failing — this keeps demos and local dev working without needing a
    real Resend account.
    """
    if not to_address or "@" not in to_address:
        return SendResult(sent=False, simulated=False, message="Invalid recipient email address.")

    if not is_resend_configured():
        return SendResult(
            sent=True,
            simulated=True,
            message=f"[SIMULATED] Would send to {to_address} via Resend — "
                    f"not configured. Set RESEND_API_KEY in .env to send for real.",
        )

    api_key      = os.getenv("RESEND_API_KEY")
    from_address = os.getenv("RESEND_FROM_ADDRESS", "Task Logistics <onboarding@resend.dev>")

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": from_address,
                "to": [to_address],
                "subject": subject,
                "text": body,
            },
            timeout=10,
        )

        if response.status_code in (200, 201):
            data = response.json()
            return SendResult(
                sent=True,
                simulated=False,
                message=f"Email sent to {to_address} (id: {data.get('id', 'unknown')}).",
            )

        try:
            error_detail = response.json().get("message", response.text)
        except Exception:
            error_detail = response.text

        return SendResult(
            sent=False,
            simulated=False,
            message=f"Send failed ({response.status_code}): {error_detail}",
        )

    except requests.exceptions.Timeout:
        return SendResult(sent=False, simulated=False, message="Send failed: request timed out.")
    except requests.exceptions.ConnectionError:
        return SendResult(sent=False, simulated=False, message="Send failed: could not reach Resend.")
    except Exception as error:
        return SendResult(sent=False, simulated=False, message=f"Send failed: {error}")