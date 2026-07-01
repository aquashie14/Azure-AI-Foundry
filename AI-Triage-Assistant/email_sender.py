"""
email_sender.py — sends the approved reply via SMTP.

IMPORTANT DESIGN RULE (per the project brief):
No reply is EVER sent automatically. This module is only ever called
from one place: the "Approve & Send" button click in streamlit_app.py,
after a human has read and (optionally edited) the AI's suggested reply.

Nothing in triage.py, config.py, or the LangGraph pipeline can call
this module. Sending is a deliberate, separate, human-triggered action.

SETUP (all optional — the app works fine without this configured):
Add to your .env:
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=your_email@gmail.com
    SMTP_PASSWORD=your_app_password        <- Gmail "App Password", not your real password
    SMTP_FROM_NAME=Task Logistics Customer Service

If SMTP_HOST is not set, send_email() runs in "simulate" mode:
it does not connect to anything, just returns a success result
so the demo flow still works end to end without real credentials.
"""

import os
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


@dataclass
class SendResult:
    sent: bool
    simulated: bool
    message: str


def is_smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"))


def send_email(to_address: str, subject: str, body: str) -> SendResult:
    """
    Sends the human-approved reply.

    If SMTP isn't configured, simulates a successful send instead of
    failing — this keeps demos and local dev working without needing
    real email credentials, while still exercising the full UI flow.
    """
    if not to_address or "@" not in to_address:
        return SendResult(sent=False, simulated=False, message="Invalid recipient email address.")

    if not is_smtp_configured():
        return SendResult(
            sent=True,
            simulated=True,
            message=f"[SIMULATED] Would send to {to_address} — SMTP not configured. "
                    f"Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env to send for real.",
        )

    host      = os.getenv("SMTP_HOST")
    port      = int(os.getenv("SMTP_PORT", "587"))
    user      = os.getenv("SMTP_USER")
    password  = os.getenv("SMTP_PASSWORD")
    from_name = os.getenv("SMTP_FROM_NAME", "Task Logistics Customer Service")

    try:
        msg = MIMEMultipart()
        msg["From"]    = f"{from_name} <{user}>"
        msg["To"]      = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)

        return SendResult(sent=True, simulated=False, message=f"Email sent to {to_address}.")

    except Exception as error:
        return SendResult(sent=False, simulated=False, message=f"Send failed: {error}")