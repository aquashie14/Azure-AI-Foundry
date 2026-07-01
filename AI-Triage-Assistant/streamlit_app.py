"""
Task Logistics Customer Service Desk
UI fixes: radio labels, secondary buttons, text area background
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── TriageResult dataclass ────────────────────────────────────────────────────

@dataclass(frozen=True)
class TriageResult:
    category:        str
    summary:         str
    suggested_reply: str
    priority:        str
    confidence:      int
    route:           str


def _parse_confidence(raw: str) -> int:
    try:
        return int(raw.replace("%", "").strip())
    except (ValueError, AttributeError):
        return 72


def triage_email(email_text: str, email_id: str = "ET-0000") -> TriageResult:
    try:
        from config import load_config
        from triage import triage_email as backend_triage

        config = load_config()
        email  = {"id": email_id, "subject": "", "body": email_text}
        result = backend_triage(email, config)

        return TriageResult(
            category        = result.category_label,
            summary         = result.summary,
            suggested_reply = result.suggested_reply,
            priority        = result.priority,
            confidence      = _parse_confidence(result.confidence),
            route           = result.suggested_route,
        )

    except Exception as error:
        st.warning(f"Backend unavailable, using demo mode. Error: {error}")
        return local_demo_triage(email_text)


# ── Local demo triage ─────────────────────────────────────────────────────────

CATEGORY_RULES = [
    ("Delivery delay",       ["late", "delay", "not arrived", "overdue", "missed", "due yesterday", "stuck"], "Customer Operations"),
    ("Tracking update",      ["tracking", "track", "where is", "status", "eta", "consignment"], "Customer Operations"),
    ("Damage or loss",       ["damage", "damaged", "crushed", "broken", "lost", "missing", "claim", "pod"], "Claims"),
    ("Address change",       ["address", "postcode", "change delivery", "update delivery", "wrong address"], "Planning"),
    ("Booking or collection",["book", "booking", "collection", "collect", "slot", "warehouse"], "Planning"),
    ("Billing query",        ["invoice", "charged", "fee", "credit", "billing", "payment", "cost"], "Accounts"),
    ("Customs documents",    ["customs", "export", "import", "commercial invoice", "eori", "documents"], "Customs"),
    ("Complaint",            ["complaint", "unacceptable", "angry", "escalate", "manager", "poor service"], "Customer Care Lead"),
]


def first_reference(text: str) -> str:
    match = re.search(r"\b(?:TSK|INV|POD|BK)-?\d{4,}\b", text, re.IGNORECASE)
    return match.group(0).upper() if match else "the customer's query"


def local_demo_triage(email_text: str) -> TriageResult:
    text   = email_text.lower()
    scored = []

    for category, keywords, route in CATEGORY_RULES:
        score = sum(1 for kw in keywords if kw in text)
        if score:
            scored.append((score, category, route))

    if scored:
        scored.sort(reverse=True)
        score, category, route = scored[0]
        confidence = min(95, 64 + score * 10)
    else:
        category, route, confidence = "General enquiry", "Customer Operations", 58

    reference = first_reference(email_text)
    priority  = "High" if any(w in text for w in ["urgent", "today", "complaint", "not arrived"]) else "Normal"
    clean     = re.sub(r"\s+", " ", email_text.strip())
    sentence  = re.split(r"(?<=[.!?])\s+", clean)[0]
    if len(sentence) > 116:
        sentence = f"{sentence[:113].rstrip()}..."

    summary = f"{category}: {reference} - {sentence}"
    reply   = (
        f"Hello,\n\nThanks for getting in touch about {reference}. "
        f"I will review this with the {route.lower()} team and confirm the next update for you.\n\n"
        "This draft is prepared for human review and will not be sent automatically.\n\n"
        "Kind regards,\nTask Logistics Customer Service"
    )
    return TriageResult(category, summary, reply, priority, confidence, route)


def azure_is_configured() -> bool:
    key_vault = os.getenv("AZURE_KEY_VAULT_URL")
    direct    = all([os.getenv("AZURE_OPENAI_API_KEY"), os.getenv("AZURE_OPENAI_ENDPOINT"), os.getenv("AZURE_OPENAI_DEPLOYMENT")])
    mock      = os.getenv("TRIAGE_MOCK_MODE", "true").lower() == "true"
    return (key_vault or direct) and not mock


def _load_sample_emails() -> list[dict]:
    """
    Loads the real sample email set from sample_emails.py (9 emails,
    including edge cases: garbled spam, multi-intent, empty body).

    That file uses fields: id, sender, time, subject, priority, body
    The UI below expects: id, from, received, subject, body
    This adapter bridges the two without changing either file.
    """
    try:
        from sample_emails import SAMPLE_EMAILS as _raw_emails

        adapted = []
        for e in _raw_emails:
            adapted.append({
                "id":       e["id"],
                "from":     e.get("sender", "Unknown"),
                "received": e.get("time", ""),
                "subject":  e.get("subject") or "(no subject)",
                "body":     e.get("body", ""),
            })
        return adapted

    except Exception as error:
        st.warning(f"Could not load sample_emails.py, using fallback set. Error: {error}")
        return [
            {"id": "ET-1042", "from": "Priya Shah", "subject": "Pallet delivery still not arrived",
             "received": "09:14",
             "body": "Hello, our pallet consignment TSK447812 was due at our Birmingham depot yesterday. "
                     "The tracking has not moved since Hinckley and we need this stock for today's outbound run. "
                     "Can someone confirm when it will arrive?"},
        ]


SAMPLE_EMAILS = _load_sample_emails()


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Task Logistics Email Triage",
    page_icon="TL",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS — fixes radio labels, secondary buttons, text area ───────────────────

st.markdown("""
<style>
    /* ── Base ── */
    .stApp { background: #f4f6f9 !important; color: #172033 !important; }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding: 1.2rem 1.6rem 2rem; max-width: 1500px; }

    /* ── FIX: Radio button labels invisible ── */
    div[data-testid="stRadio"] label p {
        color: #172033 !important;
        font-size: 0.88rem !important;
    }
    div[data-testid="stRadio"] > label {
        color: #172033 !important;
    }

    /* ── FIX: Secondary buttons (Hold, Assign, Needs edit) black ── */
    div[data-testid="stButton"] > button {
        border-radius: 7px;
        min-height: 2.45rem;
        font-weight: 700;
        background-color: #ffffff !important;
        color: #172033 !important;
        border: 1.5px solid #d8dee8 !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #f0f4f8 !important;
        border-color: #203354 !important;
        color: #172033 !important;
    }
    /* Primary buttons stay red */
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #c0392b !important;
        color: white !important;
        border: none !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #a93226 !important;
    }

    /* ── FIX: Text area dark background ── */
    div[data-testid="stTextArea"] textarea {
        background-color: #ffffff !important;
        color: #172033 !important;
        border-radius: 8px !important;
        border-color: #d8dee8 !important;
        font-size: .94rem !important;
        line-height: 1.5 !important;
    }

    /* ── FIX: Checkbox labels invisible ── */
    div[data-testid="stCheckbox"] label p {
        color: #172033 !important;
    }

    /* ── FIX: Warning/info text ── */
    div[data-testid="stAlert"] {
        color: #172033 !important;
    }

    /* ── Header bar ── */
    .desk-top {
        background: #203354; color: white; border-radius: 8px;
        padding: 18px 22px; margin-bottom: 14px;
        border-bottom: 5px solid #f3b23c;
    }
    .desk-title { font-size: 1.45rem; font-weight: 780; margin: 0; }
    .desk-subtitle { color: #d8e4f3; margin-top: 5px; font-size: .94rem; }

    /* ── Metric strip ── */
    .metric-strip {
        display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px; margin-bottom: 14px;
    }
    .desk-metric {
        background: #ffffff; border: 1px solid #d8dee8;
        border-radius: 8px; padding: 12px 14px;
    }
    .desk-metric span { color: #5a6578; display: block; font-size: .78rem; margin-bottom: 4px; }
    .desk-metric strong { font-size: 1.25rem; color: #172033; }

    /* ── Queue cards ── */
    .queue-card {
        background: #ffffff; border: 1px solid #d8dee8;
        border-radius: 8px; padding: 12px;
        margin-bottom: 10px;
    }
    .queue-meta { color: #5a6578; font-size: .78rem; }
    .queue-subject { font-weight: 720; margin: 4px 0 6px; color: #172033; }

    /* ── Pills ── */
    .tag {
        display: inline-flex; align-items: center; border-radius: 999px;
        padding: 4px 9px; font-size: .76rem; font-weight: 700;
        border: 1px solid transparent; margin-right: 5px; margin-bottom: 4px;
    }
    .tag-blue  { background: #e6eefb; color: #254b83; border-color: #c9d9f4; }
    .tag-green { background: #e7f5ee; color: #18794e; border-color: #bbe2ce; }
    .tag-amber { background: #fff3d7; color: #b76e00; border-color: #f3d391; }
    .tag-red   { background: #fde8e7; color: #b42318; border-color: #f8c2bd; }
    .tag-teal  { background: #dff5f2; color: #0f766e; border-color: #b7e3de; }

    /* ── Result panels ── */
    .result-panel {
        background: #ffffff; border: 1px solid #d8dee8;
        border-radius: 8px; padding: 16px 18px; margin-bottom: 12px;
    }
    .panel-title {
        color: #5a6578; font-size: .78rem; font-weight: 760;
        text-transform: uppercase; letter-spacing: .04em; margin-bottom: 6px;
    }
    .summary-line { font-size: 1rem; line-height: 1.45; color: #172033; }

    /* ── Human in the loop banner ── */
    .human-loop {
        background: #fff7e6; border: 1px solid #f3d391;
        border-left: 5px solid #f3b23c; border-radius: 8px;
        padding: 12px 14px; color: #5f3900;
        margin-bottom: 12px; font-weight: 650;
    }

    /* ── Subheaders ── */
    h3 { color: #172033 !important; }

    @media (max-width: 900px) {
        .metric-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────

ai_mode = "Azure AI Foundry" if azure_is_configured() else "Demo mode"

st.markdown(f"""
    <div class="desk-top">
        <div class="desk-title">Task Logistics Customer Service Desk</div>
        <div class="desk-subtitle">AI-assisted inbound email triage. Drafts are prepared for agent review only.</div>
    </div>
    <div class="metric-strip">
        <div class="desk-metric"><span>Inbox waiting</span><strong>18</strong></div>
        <div class="desk-metric"><span>High priority</span><strong>4</strong></div>
        <div class="desk-metric"><span>Ready for review</span><strong>7</strong></div>
        <div class="desk-metric"><span>AI mode</span><strong>{ai_mode}</strong></div>
    </div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.subheader("AI connection")
    if azure_is_configured():
        st.success("Azure AI Foundry connected")
        st.caption("LangChain + LangGraph backend active.")
    else:
        st.warning("Demo mode — local rule-based triage")
        st.caption("Set the following in your .env to go live:")
    st.code("""
TRIAGE_MOCK_MODE=false
AZURE_KEY_VAULT_URL=https://kv-aqsh-dev.vault.azure.net/
AZURE_AI_MODEL_NAME=gpt-4o-mini
    """.strip())

    st.subheader("Email sending")
    from email_sender import is_smtp_configured
    if is_smtp_configured():
        st.success("SMTP connected — Approve & Send sends real emails")
    else:
        st.warning("Simulate mode — approvals log but don't send")
        st.caption("Set the following in your .env to send for real:")
    st.code("""
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_NAME=Task Logistics Customer Service
    """.strip())
    st.caption(
        "Gmail: use an App Password, not your real password. "
        "Generate one at myaccount.google.com/apppasswords"
    )

# ── Three column layout ───────────────────────────────────────────────────────

queue_col, work_col, review_col = st.columns([1.1, 1.45, 1.25], gap="medium")

# ── LEFT: Inbox queue ─────────────────────────────────────────────────────────

with queue_col:
    st.subheader("Inbox queue")

    options = [f"{e['id']} — {e['subject']}" for e in SAMPLE_EMAILS] + ["✏️ New pasted email"]

    selected_label = st.radio(
        "Select an email to triage",
        options,
        label_visibility="visible",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    for item in SAMPLE_EMAILS:
        preview        = local_demo_triage(item["body"])
        priority_class = "tag-red" if preview.priority == "High" else "tag-green"
        is_selected    = selected_label.startswith(item["id"])
        border         = "border: 2px solid #203354;" if is_selected else ""

        st.markdown(f"""
            <div class="queue-card" style="{border}">
                <div class="queue-meta">{item["received"]} · {item["from"]} · {item["id"]}</div>
                <div class="queue-subject">{item["subject"]}</div>
                <span class="tag tag-blue">{preview.category}</span>
                <span class="tag {priority_class}">{preview.priority}</span>
            </div>
        """, unsafe_allow_html=True)

# ── MIDDLE: Email body + actions ──────────────────────────────────────────────

with work_col:
    st.subheader("Incoming email")

    selected_index = next(
        (i for i, e in enumerate(SAMPLE_EMAILS) if selected_label.startswith(e["id"])),
        None,
    )

    selected_id    = SAMPLE_EMAILS[selected_index]["id"]   if selected_index is not None else "ET-0000"
    selected_body  = SAMPLE_EMAILS[selected_index]["body"] if selected_index is not None else ""

    if selected_index is not None:
        item = SAMPLE_EMAILS[selected_index]
        st.markdown(
            f"<div style='font-size:.85rem;color:#5a6578;margin-bottom:6px;'>"
            f"{item['received']} · <strong>{item['from']}</strong> · {item['id']}</div>",
            unsafe_allow_html=True,
        )

    email_text = st.text_area(
        "Email body",
        value=selected_body,
        height=220,
        placeholder="Paste a customer email here for triage...",
        label_visibility="collapsed",
    )

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        analyse = st.button("🔍 Analyse", type="primary", use_container_width=True)
    with col_b:
        hold    = st.button("⏸ Hold",    use_container_width=True)
    with col_c:
        assign  = st.button("👤 Assign",  use_container_width=True)

    if hold:
        st.info("Email placed on hold.")
    if assign:
        st.info("Assign functionality — coming soon.")

    # Run triage when email is present
    result = triage_email(email_text, selected_id) if email_text.strip() else None

# ── RIGHT: Triage result ──────────────────────────────────────────────────────

with review_col:
    st.subheader("Triage result")

    if result is None:
        st.info("Select or paste an email, then click Analyse.")
    else:
        priority_class   = "tag-red"   if result.priority   == "High" else "tag-green"
        confidence_class = "tag-green" if result.confidence >= 80      else "tag-amber"

        st.markdown(f"""
            <div class="result-panel">
                <div class="panel-title">Category</div>
                <span class="tag tag-teal">{result.category}</span>
                <span class="tag {priority_class}">{result.priority} priority</span>
                <span class="tag {confidence_class}">{result.confidence}% confidence</span>
            </div>
            <div class="result-panel">
                <div class="panel-title">One-line summary</div>
                <div class="summary-line">{result.summary}</div>
            </div>
            <div class="result-panel">
                <div class="panel-title">Suggested route</div>
                <div class="summary-line">{result.route}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="human-loop">
                Human-in-the-loop: the AI prepares a draft only.
                Nothing is sent until an agent reviews and approves it.
            </div>
        """, unsafe_allow_html=True)

        final_reply = st.text_area(
            "Suggested reply for agent review",
            value=result.suggested_reply,
            height=220,
        )

        recipient_email = st.text_input(
            "Send reply to (customer email)",
            value=f"{item['from'].lower().replace(' ', '.')}@example.com" if selected_index is not None else "",
            help="This is where the approved reply will be sent. Edit if needed.",
        )

        col_approve, col_edit = st.columns(2)
        with col_approve:
            approved = st.button("✅ Approve & Send", type="primary", use_container_width=True)
        with col_edit:
            st.button("✏️ Needs edit", use_container_width=True)

        if approved:
            from email_sender import is_smtp_configured, send_email

            send_result = send_email(
                to_address=recipient_email,
                subject=f"Re: {item['subject']}" if selected_index is not None else "Re: your enquiry",
                body=final_reply,
            )

            if send_result.sent and send_result.simulated:
                st.success(f"Draft approved. {send_result.message}")
                st.caption(
                    "Running in simulate mode — no email credentials configured. "
                    "See sidebar for setup instructions."
                )
            elif send_result.sent:
                st.success(f"✅ {send_result.message}")
            else:
                st.error(f"Could not send: {send_result.message}")

        with st.expander("Agent checklist", expanded=True):
            st.checkbox("Reference number checked",
                        value=first_reference(email_text) != "the customer's query")
            st.checkbox("Customer account reviewed")
            st.checkbox("Reply tone reviewed")
            st.checkbox("Approval recorded before sending")