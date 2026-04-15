"""
Input Guardrails for FinBot.

Four checks that run BEFORE retrieval in fail-fast order:
  1. Rate Limit
  2. PII Detection
  3. Prompt Injection Detection
  4. Off-Topic Detection
"""

import re
import logging
from typing import Optional

from app.guardrails.schemas import GuardrailCheckResult


logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# 1. RATE LIMITING
# ═══════════════════════════════════════════════════════════════════════════

# In-memory counter keyed by user_id
_session_counters: dict[str, int] = {}

MAX_QUERIES_PER_SESSION = 20
SOFT_WARNING_THRESHOLD = 18


def reset_rate_limit(user_id: str) -> None:
    """Reset the rate-limit counter for a user (e.g. on new session)."""
    _session_counters.pop(user_id, None)


def check_rate_limit(user_id: str) -> GuardrailCheckResult:
    """Check if the user has exceeded the session query limit."""
    count = _session_counters.get(user_id, 0) + 1
    _session_counters[user_id] = count

    if count > MAX_QUERIES_PER_SESSION:
        return GuardrailCheckResult(
            guardrail="rate_limit",
            status="blocked",
            reason="rate_limit_exceeded",
            message=(
                f"You have exceeded the maximum number of queries "
                f"({MAX_QUERIES_PER_SESSION}) for this session. "
                f"Please start a new session or contact support."
            ),
        )

    if count >= SOFT_WARNING_THRESHOLD:
        remaining = MAX_QUERIES_PER_SESSION - count
        return GuardrailCheckResult(
            guardrail="rate_limit",
            status="warning",
            reason="rate_limit_approaching",
            message=f"You have {remaining} queries remaining in this session.",
        )

    return GuardrailCheckResult(
        guardrail="rate_limit",
        status="allowed",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 2. PII DETECTION
# ═══════════════════════════════════════════════════════════════════════════

# Compiled regex patterns for Indian + common PII
_PII_PATTERNS: dict[str, re.Pattern] = {
    "aadhaar_number": re.compile(
        r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b"
    ),
    "pan_number": re.compile(
        r"\b[A-Z]{5}\d{4}[A-Z]\b"
    ),
    "email_address": re.compile(
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
    ),
    "bank_account_number": re.compile(
        r"\b\d{9,18}\b"
    ),
    "phone_number": re.compile(
        r"(?:\+91[\s\-]?)?[6-9]\d{9}\b"
    ),
    "credit_card_number": re.compile(
        r"\b(?:\d{4}[\s\-]?){3}\d{4}\b"
    ),
}


def check_pii(query: str) -> GuardrailCheckResult:
    """Detect PII patterns in the user query."""
    detected_types: list[str] = []

    for pii_type, pattern in _PII_PATTERNS.items():
        if pattern.search(query):
            detected_types.append(pii_type)

    if detected_types:
        pii_labels = ", ".join(t.replace("_", " ").title() for t in detected_types)
        return GuardrailCheckResult(
            guardrail="pii_detection",
            status="blocked",
            reason="pii_detected",
            message=(
                f"Your query appears to contain personal information ({pii_labels}). "
                f"For your security, please remove any personal data before "
                f"submitting your query."
            ),
        )

    return GuardrailCheckResult(
        guardrail="pii_detection",
        status="allowed",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 3. PROMPT INJECTION DETECTION
# ═══════════════════════════════════════════════════════════════════════════

_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(your|all|previous|prior)\s+(instructions|rules|guidelines)", re.IGNORECASE),
    re.compile(r"ignore\s+everything\s+(above|before|previously)", re.IGNORECASE),
    re.compile(r"disregard\s+(your|all|the)\s+(system\s+)?prompt", re.IGNORECASE),
    re.compile(r"act\s+as\s+(a\s+)?different\s+assistant", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(an?\s+)?unrestricted", re.IGNORECASE),
    re.compile(r"pretend\s+you\s+have\s+no\s+restrictions", re.IGNORECASE),
    re.compile(r"bypass\s+(security|access\s+control|rbac|restrictions)", re.IGNORECASE),
    re.compile(r"override\s+(access|security|permissions|controls)", re.IGNORECASE),
    re.compile(r"show\s+me\s+all\s+documents?\s+regardless", re.IGNORECASE),
    re.compile(r"forget\s+everything\s+you.ve\s+been\s+told", re.IGNORECASE),
    re.compile(r"output\s+(your|the)\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"reveal\s+(your|the)\s+(system\s+)?(prompt|instructions)", re.IGNORECASE),
    re.compile(r"do\s+not\s+follow\s+(your|any)\s+(rules|guidelines)", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"DAN\s+mode", re.IGNORECASE),
]


def check_prompt_injection(query: str) -> GuardrailCheckResult:
    """Detect prompt injection attempts using keyword pattern matching."""
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(query):
            logger.warning("Prompt injection detected: pattern=%s", pattern.pattern)
            return GuardrailCheckResult(
                guardrail="prompt_injection",
                status="blocked",
                reason="prompt_injection",
                message=(
                    "Your query has been flagged as a potential prompt injection "
                    "attempt. This action has been logged for security review."
                ),
            )

    return GuardrailCheckResult(
        guardrail="prompt_injection",
        status="allowed",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 4. OFF-TOPIC DETECTION (LLM-based via Groq)
# ═══════════════════════════════════════════════════════════════════════════

_OFF_TOPIC_SYSTEM_PROMPT = """You are a query classifier for FinSolve Technologies, a B2B fintech company.

Your task: Determine if the user's query is ON-TOPIC or OFF-TOPIC.

ON-TOPIC queries relate to:
- Finance: revenue, budgets, financial reports, investor relations, earnings
- Engineering: system architecture, APIs, deployments, incidents, technical docs
- Marketing: campaigns, brand, competitors, market research
- HR / General: company policies, leave, benefits, code of conduct, company FAQ
- Cross-department: company-wide updates, overall performance

OFF-TOPIC queries include:
- Sports scores, weather, cooking recipes, entertainment
- Personal advice, jokes, poems, stories
- Questions about other companies unrelated to FinSolve
- General knowledge unrelated to business operations

Respond with EXACTLY one word: ON_TOPIC or OFF_TOPIC"""


def check_off_topic(query: str) -> GuardrailCheckResult:
    """
    Use Groq LLM to classify whether the query is related to FinSolve business.
    Falls back to 'allowed' if the LLM call fails.
    """
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import SystemMessage, HumanMessage
        from app.config.settings import settings

        llm = ChatGroq(
            model=settings.GUARDRAILS_GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0,
            max_tokens=10,
        )

        response = llm.invoke([
            SystemMessage(content=_OFF_TOPIC_SYSTEM_PROMPT),
            HumanMessage(content=f"User query: {query}"),
        ])

        classification = response.content.strip().upper()

        if "OFF_TOPIC" in classification:
            return GuardrailCheckResult(
                guardrail="off_topic",
                status="blocked",
                reason="off_topic",
                message=(
                    "I'm sorry, but I can only answer questions related to "
                    "FinSolve Technologies' business operations, policies, "
                    "and documentation."
                ),
            )

        return GuardrailCheckResult(
            guardrail="off_topic",
            status="allowed",
        )

    except Exception as exc:
        logger.error("Off-topic detection failed, allowing query: %s", exc)
        return GuardrailCheckResult(
            guardrail="off_topic",
            status="allowed",
            reason="check_failed",
            message=None,
        )
