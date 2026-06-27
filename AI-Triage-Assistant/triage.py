"""
Core email triage logic (D5) — LangChain + LangGraph.

Updated to match the Streamlit UI fields:
  - category + category_label (human-readable)
  - priority (High / Normal)
  - confidence (percentage string)
  - summary (one-line)
  - suggested_route (department)
  - suggested_reply (editable draft)

GRAPH FLOW:
  Email IN
     │
  [classify] ── figures out category + priority + confidence
     │
  [route] ────── needs_human_review? ──► [flag_for_human] ──► OUT
     │
     └─────────── clear category? ──► [summarise] ──► [reply] ──► OUT

No reply is ever sent automatically. This file only produces a
suggestion. A human reviews and approves it in the Streamlit UI.
"""

import json
from dataclasses import dataclass, field
from typing import TypedDict

from config import TriageConfig

# ── Categories ────────────────────────────────────────────────────────────────

CATEGORIES = [
    "delivery_status",
    "address_change",
    "claims",
    "complaint",
    "general_question",
    "needs_human_review",
]

# Human-readable labels shown in the UI pills
CATEGORY_LABELS = {
    "delivery_status":    "Tracking update",
    "address_change":     "Booking or collection",
    "claims":             "Damage or loss",
    "complaint":          "Complaint",
    "general_question":   "General query",
    "needs_human_review": "Needs review",
}

# Department routing shown in the UI
ROUTE_MAP = {
    "delivery_status":    "Customer Operations",
    "address_change":     "Bookings & Collections",
    "claims":             "Damage & Loss",
    "complaint":          "Customer Operations",
    "general_question":   "Customer Operations",
    "needs_human_review": "Manual Review Required",
}

# Default priority per category
PRIORITY_MAP = {
    "delivery_status":    "High",
    "claims":             "High",
    "complaint":          "High",
    "address_change":     "Normal",
    "general_question":   "Normal",
    "needs_human_review": "Normal",
}

# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class TriageResult:
    email_id: str
    category: str
    category_label: str
    summary: str
    suggested_reply: str
    suggested_route: str
    priority: str
    confidence: str
    raw_model_output: str | None = None


# ═════════════════════════════════════════════════════════════════════════════
# MOCK MODE
# Rule-based fallback — no model called, no Azure needed.
# Used when TRIAGE_MOCK_MODE=true in .env
# ═════════════════════════════════════════════════════════════════════════════

def _mock_triage(email: dict) -> TriageResult:
    """Rule-based stand-in for local testing without Azure access."""
    body    = (email.get("body") or "").lower()
    subject = (email.get("subject") or "").lower()
    text    = f"{subject} {body}"

    if len(body.strip()) < 15 or not any(c.isalpha() for c in body):
        category = "needs_human_review"
        summary  = "Email content is too short or unclear to classify."
        reply = (
            "Thanks for reaching out. Could you let us know a bit more "
            "about what you need help with, and your order or consignment "
            "reference if you have one? We want to make sure we help with "
            "the right thing."
        )

    elif "frustrat" in text or "third" in text or "furious" in text or "!!!" in body:
        category = "complaint"
        summary  = "Customer is frustrated about an unresolved or delayed order."
        reply = (
            "Thank you for contacting us and I'm very sorry to hear about "
            "your experience. I completely understand your frustration and "
            "want to assure you this is being treated as a priority. A senior "
            "member of our team will review your case and be in touch shortly "
            "with a full update."
        )

    elif "address" in text and (
        "previous order" in text or "still hasn't" in text
        or "10 days" in text or "missing" in text
    ):
        category = "needs_human_review"
        summary  = "Customer raises both an address change and a missing delivery."
        reply = (
            "Thank you for your email. I can see you have two separate "
            "requests — an address update and a delivery query. A member of "
            "our team will look into both and confirm the outcome of each "
            "to you shortly."
        )

    elif "address" in text or "change" in text and "deliver" in text:
        category = "address_change"
        summary  = "Customer wants to update the delivery address on an unshipped order."
        reply = (
            "Thank you for letting us know. We've noted your request to update "
            "the delivery address. A member of our team will confirm this has "
            "been applied to your order and advise if there are any cutoff "
            "constraints."
        )

    elif (
        "claim" in text or "broken" in text or "damaged" in text
        or "crush" in text or "refund" in text
    ):
        category = "claims"
        summary  = "Customer is reporting damaged goods and wants to file a claim."
        reply = (
            "We're very sorry to hear about the condition of your delivery. "
            "We've logged a claim against your consignment and our Damage & Loss "
            "team will be in touch shortly with next steps, including whether "
            "the items need to be retained for inspection."
        )

    elif (
        "where" in text or "tracking" in text or "not arrived" in text
        or "not moved" in text or "confirm when" in text
    ):
        category = "delivery_status"
        summary  = "Customer is requesting a status update on a consignment."
        reply = (
            "Thank you for getting in touch. We're checking the latest status "
            "of your consignment with our operations team and will follow up "
            "with a full update as soon as possible."
        )

    else:
        category = "general_question"
        summary  = "Customer has a general question about the service or process."
        reply = (
            "Thank you for your message. A member of our team will review "
            "your query and get back to you with the information you need "
            "as soon as possible."
        )

    # Override priority if email already has one set
    priority = email.get("priority") or PRIORITY_MAP.get(category, "Normal")

    return TriageResult(
        email_id        = email["id"],
        category        = category,
        category_label  = CATEGORY_LABELS[category],
        summary         = summary,
        suggested_reply = reply,
        suggested_route = ROUTE_MAP[category],
        priority        = priority,
        confidence      = "N/A (mock)",
        raw_model_output= "(mock mode - no model called)",
    )


# ═════════════════════════════════════════════════════════════════════════════
# LANGGRAPH LIVE MODE
# ═════════════════════════════════════════════════════════════════════════════

class TriageState(TypedDict):
    email_id:        str
    email_subject:   str
    email_body:      str
    email_priority:  str
    category:        str
    category_label:  str
    confidence:      str
    summary:         str
    suggested_reply: str
    suggested_route: str
    priority:        str
    raw_output:      str


def _build_model(config: TriageConfig):
    from langchain_openai import AzureChatOpenAI
    return AzureChatOpenAI(
        azure_endpoint   = config.endpoint,
        api_key          = config.key,
        azure_deployment = config.model_name,
        api_version      = "2024-02-01",
        temperature      = 0.2,
        max_tokens       = 500,
    )


# ── Node 1: Classify ──────────────────────────────────────────────────────────

def make_classify_node(model):
    """
    Classifies the email into a category, assigns a priority,
    and estimates confidence. Uses PydanticOutputParser so the
    model's response is validated automatically.
    """
    from langchain_core.output_parsers import PydanticOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from pydantic import BaseModel, field_validator

    class ClassifyOutput(BaseModel):
        category:   str
        priority:   str
        confidence: str   # e.g. "92%"

        @field_validator("category")
        @classmethod
        def valid_category(cls, v):
            return v if v in CATEGORIES else "needs_human_review"

        @field_validator("priority")
        @classmethod
        def valid_priority(cls, v):
            return v if v in ("High", "Normal") else "Normal"

    parser = PydanticOutputParser(pydantic_object=ClassifyOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an email classifier for a logistics company customer "
            "service desk. Classify the email into exactly one category:\n"
            "{categories}\n\n"
            "Also assign a priority (High or Normal) and a confidence "
            "percentage (e.g. '94%').\n\n"
            "Use needs_human_review if the email is: unclear, empty, "
            "spam-like, or contains multiple unrelated requests.\n\n"
            "High priority applies to: delivery_status, claims, complaint.\n\n"
            "{format_instructions}"
        )),
        ("human", "Subject: {subject}\n\n{body}"),
    ])

    chain = prompt | model | parser

    def classify_node(state: TriageState) -> dict:
        try:
            result = chain.invoke({
                "categories":          ", ".join(CATEGORIES),
                "format_instructions": parser.get_format_instructions(),
                "subject":             state["email_subject"],
                "body":                state["email_body"],
            })
            return {
                "category":       result.category,
                "category_label": CATEGORY_LABELS.get(result.category, result.category),
                "priority":       result.priority,
                "confidence":     result.confidence,
                "raw_output":     f"classify: {result.model_dump_json()}",
            }
        except Exception as e:
            return {
                "category":       "needs_human_review",
                "category_label": CATEGORY_LABELS["needs_human_review"],
                "priority":       "Normal",
                "confidence":     "0%",
                "raw_output":     f"classify error: {e}",
            }

    return classify_node


# ── Routing ───────────────────────────────────────────────────────────────────

def route_after_classify(state: TriageState) -> str:
    return "flag" if state["category"] == "needs_human_review" else "summarise"


# ── Node 2a: Flag for human ───────────────────────────────────────────────────

def flag_node(state: TriageState) -> dict:
    return {
        "summary": (
            "Email is unclear or contains multiple requests — "
            "flagged for human review."
        ),
        "suggested_reply": (
            "Thank you for your email. Your message has been flagged for "
            "review by one of our team members who will be in touch shortly. "
            "If you have a consignment or order reference, please include it "
            "in any follow-up as it will help us assist you faster."
        ),
        "suggested_route": ROUTE_MAP["needs_human_review"],
    }


# ── Node 2b: Summarise ────────────────────────────────────────────────────────

def make_summarise_node(model):
    """One-line summary shown in the UI summary box."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are summarising a customer service email for a logistics "
            "company. Write a single sentence (max 20 words) describing "
            "what the customer wants. Include the reference number if "
            "mentioned. Return the sentence only, no punctuation at the end."
        )),
        ("human", "Category: {category}\nSubject: {subject}\n\n{body}"),
    ])

    chain = prompt | model | StrOutputParser()

    def summarise_node(state: TriageState) -> dict:
        try:
            summary = chain.invoke({
                "category": state["category"],
                "subject":  state["email_subject"],
                "body":     state["email_body"],
            })
            return {
                "summary":         summary.strip(),
                "suggested_route": ROUTE_MAP.get(state["category"], "Customer Operations"),
            }
        except Exception:
            return {
                "summary":         f"Customer email regarding {state['category'].replace('_', ' ')}.",
                "suggested_route": ROUTE_MAP.get(state["category"], "Customer Operations"),
            }

    return summarise_node


# ── Node 3: Reply ─────────────────────────────────────────────────────────────

def make_reply_node(model):
    """
    Generates the suggested reply shown in the editable text area.
    Knows the category, priority, and summary from previous nodes
    so it can write a more targeted reply.
    """
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are drafting a reply for a human customer service agent at "
            "a logistics company. The agent will review and send this — you "
            "are not sending it automatically.\n\n"
            "Guidelines:\n"
            "- Polite, professional, concise (3-5 sentences max)\n"
            "- Do NOT promise specific delivery dates or refund amounts\n"
            "- Do NOT make up tracking or reference information\n"
            "- Match tone to category: complaints need empathy, queries need clarity\n"
            "- High priority emails need a more urgent, reassuring tone\n"
            "- End by saying a team member will follow up with specifics\n"
            "- Return the reply text only, no subject line"
        )),
        ("human", (
            "Category: {category}\n"
            "Priority: {priority}\n"
            "Summary: {summary}\n"
            "Original email:\nSubject: {subject}\n\n{body}"
        )),
    ])

    chain = prompt | model | StrOutputParser()

    def reply_node(state: TriageState) -> dict:
        try:
            reply = chain.invoke({
                "category": state["category"],
                "priority": state["priority"],
                "summary":  state["summary"],
                "subject":  state["email_subject"],
                "body":     state["email_body"],
            })
            return {"suggested_reply": reply.strip()}
        except Exception:
            return {
                "suggested_reply": (
                    "Thank you for your email. A member of our team will "
                    "review your request and be in touch shortly."
                )
            }

    return reply_node


# ── Build the graph ───────────────────────────────────────────────────────────

def _build_graph(config: TriageConfig):
    from langgraph.graph import END, START, StateGraph

    model = _build_model(config)

    classify_node  = make_classify_node(model)
    summarise_node = make_summarise_node(model)
    reply_node     = make_reply_node(model)

    graph = StateGraph(TriageState)

    graph.add_node("classify",  classify_node)
    graph.add_node("flag",      flag_node)
    graph.add_node("summarise", summarise_node)
    graph.add_node("reply",     reply_node)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        route_after_classify,
        {"flag": "flag", "summarise": "summarise"},
    )
    graph.add_edge("flag",      END)
    graph.add_edge("summarise", "reply")
    graph.add_edge("reply",     END)

    return graph.compile()


_graph_cache = None

def _get_graph(config: TriageConfig):
    global _graph_cache
    if _graph_cache is None:
        _graph_cache = _build_graph(config)
    return _graph_cache


def _live_triage(email: dict, config: TriageConfig) -> TriageResult:
    graph = _get_graph(config)

    initial_state: TriageState = {
        "email_id":        email["id"],
        "email_subject":   email.get("subject") or "",
        "email_body":      email.get("body") or "",
        "email_priority":  email.get("priority") or "Normal",
        "category":        "",
        "category_label":  "",
        "confidence":      "",
        "summary":         "",
        "suggested_reply": "",
        "suggested_route": "",
        "priority":        "",
        "raw_output":      "",
    }

    final = graph.invoke(initial_state)

    return TriageResult(
        email_id        = email["id"],
        category        = final["category"],
        category_label  = final["category_label"],
        summary         = final["summary"],
        suggested_reply = final["suggested_reply"],
        suggested_route = final["suggested_route"],
        priority        = final["priority"],
        confidence      = final.get("confidence", "N/A"),
        raw_model_output= final.get("raw_output"),
    )


# ── Public interface ──────────────────────────────────────────────────────────

def triage_email(email: dict, config: TriageConfig) -> TriageResult:
    """
    Main entry point — called by demo.py, streamlit_app.py, and app.py.
    Picks mock or live mode based on config.
    """
    if config.mock_mode:
        return _mock_triage(email)
    return _live_triage(email, config)
