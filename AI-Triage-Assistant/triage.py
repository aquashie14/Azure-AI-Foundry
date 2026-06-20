"""
Core email triage logic (D5).

For each incoming customer email, returns:
  - category: one of a fixed set of labels
  - summary: a one-line summary
  - suggested_reply: a draft reply for a human agent to review

No reply is ever sent automatically - this only ever produces a
suggestion. A human always reviews it (see README).
"""

import json
from dataclasses import dataclass

from config import TriageConfig

CATEGORIES = [
    "delivery_status",
    "address_change",
    "claims",
    "complaint",
    "general_question",
    "needs_human_review",  # used when the email is too ambiguous to classify safely
]

SYSTEM_PROMPT = f"""You are a customer service email triage assistant for a \
logistics company. Read the customer email and respond with ONLY a JSON \
object (no other text) with exactly these fields:

- "category": one of {CATEGORIES}
- "summary": a single-sentence summary of what the customer wants
- "suggested_reply": a short, polite draft reply a human agent can review \
and send. Do not promise specific dates or refunds - keep it general and \
reassuring, and note that a team member will follow up with specifics.

If the email is unclear, spam-like, empty, or doesn't fit any category, \
use "needs_human_review" and write a suggested_reply asking the customer \
to clarify their request.

Respond with raw JSON only. No markdown, no code fences, no commentary."""


@dataclass
class TriageResult:
    email_id: str
    category: str
    summary: str
    suggested_reply: str
    raw_model_output: str | None = None


def _mock_triage(email: dict) -> TriageResult:
    """Rough rule-based stand-in so the pipeline can be built and tested
    before Azure access is confirmed. Not a substitute for the real model."""
    body = (email.get("body") or "").lower()
    subject = (email.get("subject") or "").lower()
    text = f"{subject} {body}"

    if len(body.strip()) < 15 or not any(c.isalpha() for c in body):
        category = "needs_human_review"
        summary = "Email content is too short or unclear to classify."
        reply = (
            "Thanks for reaching out. Could you let us know a bit more "
            "about what you need help with, and your order number if "
            "you have one? We want to make sure we help with the right thing."
        )
    elif "frustrat" in text or "third email" in text or "!!!" in body:
        category = "complaint"
        summary = "Customer is frustrated about a delayed or unresolved order."
        reply = (
            "We're sorry for the delay and the frustration this has "
            "caused. We've flagged this for priority follow-up and "
            "someone from our team will be in touch shortly."
        )
    elif "address" in text and (
        "track" in text or "where" in text or "arrived" in text or "previous order" in text
    ):
        category = "needs_human_review"
        summary = "Customer raises both an address change and a delivery query."
        reply = (
            "Thanks for your email - I can see you have two separate "
            "requests here. A member of our team will look into both "
            "your address update and your delivery question shortly."
        )
    elif "address" in text or "move" in text:
        category = "address_change"
        summary = "Customer wants to update their delivery address."
        reply = (
            "Thanks for letting us know! We've noted your request to "
            "update the delivery address. A team member will confirm "
            "this has been applied to your order shortly."
        )
    elif "claim" in text or "broken" in text or "damaged" in text or "refund" in text:
        category = "claims"
        summary = "Customer wants to file a claim for a damaged or unwanted item."
        reply = (
            "We're sorry to hear about this. We've logged your claim "
            "and a member of our team will follow up with the next "
            "steps shortly."
        )
    elif "where" in text or "track" in text or "delivery" in text:
        category = "delivery_status"
        summary = "Customer is asking for an update on their delivery."
        reply = (
            "Thanks for getting in touch! We're checking the latest "
            "status on your order and a team member will follow up "
            "with an update shortly."
        )
    else:
        category = "general_question"
        summary = "Customer has a general question about the service or process."
        reply = (
            "Thanks for your question! A member of our team will get "
            "back to you shortly with the details you need."
        )

    return TriageResult(
        email_id=email["id"],
        category=category,
        summary=summary,
        suggested_reply=reply,
        raw_model_output="(mock mode - no model called)",
    )


def _live_triage(email: dict, config: TriageConfig) -> TriageResult:
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
    from azure.core.credentials import AzureKeyCredential

    client = ChatCompletionsClient(
        endpoint=config.endpoint,
        credential=AzureKeyCredential(config.key),
    )

    user_text = f"Subject: {email.get('subject', '')}\n\n{email.get('body', '')}"

    response = client.complete(
        model=config.model_name,
        messages=[
            SystemMessage(content=SYSTEM_PROMPT),
            UserMessage(content=user_text),
        ],
        temperature=0.2,
    )

    raw_output = response.choices[0].message.content

    try:
        parsed = json.loads(raw_output)
        category = parsed.get("category", "needs_human_review")
        if category not in CATEGORIES:
            category = "needs_human_review"
        summary = parsed.get("summary", "")
        reply = parsed.get("suggested_reply", "")
    except (json.JSONDecodeError, AttributeError):
        # Model didn't return valid JSON - fail safe rather than guessing.
        category = "needs_human_review"
        summary = "Model response could not be parsed - needs manual review."
        reply = "Thanks for your email - a member of our team will review this shortly."

    return TriageResult(
        email_id=email["id"],
        category=category,
        summary=summary,
        suggested_reply=reply,
        raw_model_output=raw_output,
    )


def triage_email(email: dict, config: TriageConfig) -> TriageResult:
    if config.mock_mode:
        return _mock_triage(email)
    return _live_triage(email, config)
