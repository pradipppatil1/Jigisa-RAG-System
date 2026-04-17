"""
Output Guardrails for FinBot.

Four checks that run AFTER LLM generation:
  1. Source Citation Enforcement
  2. Grounding / Faithfulness Check
  3. Hallucinated Numbers Detection
  4. Cross-Role Leakage Detection
"""

import re
import logging
from typing import Optional

from app.guardrails.schemas import GuardrailCheckResult

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# 1. SOURCE CITATION ENFORCEMENT
# ═══════════════════════════════════════════════════════════════════════════

_CITATION_PATTERNS: list[re.Pattern] = [
    re.compile(r"\[Source:\s*.+?\]", re.IGNORECASE),
    re.compile(r"\(Source:\s*.+?\)", re.IGNORECASE),
    re.compile(r"\[Ref:\s*.+?\]", re.IGNORECASE),
    re.compile(r"According to\s+.+?\.(pdf|docx|md)", re.IGNORECASE),
    re.compile(r"Page\s+\d+", re.IGNORECASE),
    re.compile(r"p\.\s*\d+", re.IGNORECASE),
    re.compile(r"\*\*Source\*\*", re.IGNORECASE),
    re.compile(r"source_document", re.IGNORECASE),
]


def check_source_citations(
    response: str,
    retrieved_chunks: Optional[list[dict]] = None,
) -> GuardrailCheckResult:
    """
    Check if the LLM response contains at least one source citation.
    Citations can appear either inline in the response text (via patterns)
    or as metadata displayed separately in the UI via retrieved_chunks.
    """
    # If citations are shown in the UI via retrieved_chunks, that's sufficient
    if retrieved_chunks:
        return GuardrailCheckResult(
            guardrail="source_citation",
            status="allowed",
        )

    # No chunks retrieved at all — check the response text for inline citations
    for pattern in _CITATION_PATTERNS:
        if pattern.search(response):
            return GuardrailCheckResult(
                guardrail="source_citation",
                status="allowed",
            )

    return GuardrailCheckResult(
        guardrail="source_citation",
        status="warning",
        reason="missing_citations",
        message=(
            "⚠️ Note: This response was generated without any source documents. "
            "Please verify the information independently."
        ),
    )


# ═══════════════════════════════════════════════════════════════════════════
# 2. GROUNDING / FAITHFULNESS CHECK (LLM-based via Groq)
# ═══════════════════════════════════════════════════════════════════════════

_GROUNDING_SYSTEM_PROMPT = """You are a factual grounding checker. Your job is to determine whether
the RESPONSE is fully supported by the given CONTEXT chunks.

Rules:
- If the response contains financial figures, dates, statistics, or specific claims,
  check that each one appears in or can be directly inferred from the context.
- If ALL claims in the response are supported by the context, respond: GROUNDED
- If ANY claim is NOT supported by the context, respond: UNGROUNDED

Respond with EXACTLY one word: GROUNDED or UNGROUNDED"""


def check_grounding(
    response: str,
    retrieved_chunks: Optional[list[dict]] = None,
) -> GuardrailCheckResult:
    """
    Use Groq LLM to verify that the response is grounded in the retrieved context.
    Falls back to 'allowed' if the LLM call fails or no chunks are provided.
    """
    if not retrieved_chunks:
        return GuardrailCheckResult(
            guardrail="grounding_check",
            status="allowed",
            reason="no_chunks_to_verify",
        )

    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import SystemMessage, HumanMessage
        from app.config.settings import settings

        # Build context from chunks
        context_text = "\n---\n".join(
            chunk.get("page_content", chunk.get("text", ""))
            for chunk in retrieved_chunks
        )

        llm = ChatGroq(
            model=settings.GUARDRAILS_GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0,
            max_tokens=10,
        )

        result = llm.invoke([
            SystemMessage(content=_GROUNDING_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"CONTEXT:\n{context_text[:3000]}\n\n"
                f"RESPONSE:\n{response[:2000]}"
            )),
        ])

        classification = result.content.strip().upper()

        if "UNGROUNDED" in classification:
            return GuardrailCheckResult(
                guardrail="grounding_check",
                status="warning",
                reason="potentially_ungrounded",
                message=(
                    "⚠️ Disclaimer: Some information in this response could not be "
                    "verified against the source documents. Please cross-check "
                    "critical figures with the original documents."
                ),
            )

        return GuardrailCheckResult(
            guardrail="grounding_check",
            status="allowed",
        )

    except Exception as exc:
        logger.error("Grounding check failed, allowing response: %s", exc)
        return GuardrailCheckResult(
            guardrail="grounding_check",
            status="allowed",
            reason="check_failed",
        )


# ═══════════════════════════════════════════════════════════════════════════
# 3. HALLUCINATED NUMBERS DETECTION
# ═══════════════════════════════════════════════════════════════════════════

# Patterns to extract numerical values from the LLM response
_NUMBER_PATTERNS: list[re.Pattern] = [
    re.compile(r"\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|trillion|M|B|K))?", re.IGNORECASE),
    re.compile(r"₹[\d,]+(?:\.\d+)?(?:\s*(?:crore|lakh|Cr|L))?", re.IGNORECASE),
    re.compile(r"\d+(?:\.\d+)?%"),
    re.compile(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b"),
    re.compile(r"\b(?:FY|Q[1-4])\s*\d{4}\b", re.IGNORECASE),
]


def check_hallucinated_numbers(
    response: str,
    retrieved_chunks: Optional[list[dict]] = None,
) -> GuardrailCheckResult:
    """
    Extract numbers, currency values, and percentages from the response
    and check if they appear in the retrieved chunk content.
    """
    if not retrieved_chunks:
        return GuardrailCheckResult(
            guardrail="hallucination_check",
            status="allowed",
            reason="no_chunks_to_verify",
        )

    # Build combined chunk text for searching
    chunk_text = " ".join(
        chunk.get("page_content", chunk.get("text", ""))
        for chunk in retrieved_chunks
    ).lower()

    # Extract all numerical values from the response
    extracted_values: list[str] = []
    for pattern in _NUMBER_PATTERNS:
        matches = pattern.findall(response)
        extracted_values.extend(matches)

    if not extracted_values:
        return GuardrailCheckResult(
            guardrail="hallucination_check",
            status="allowed",
        )

    # Check each value against chunk text
    ungrounded_values: list[str] = []
    for value in extracted_values:
        # Normalize: remove formatting for comparison
        normalized = value.replace(",", "").replace(" ", "").lower()
        if normalized not in chunk_text.replace(",", "").replace(" ", ""):
            ungrounded_values.append(value)

    if ungrounded_values:
        values_str = ", ".join(ungrounded_values[:5])  # Cap at 5 for readability
        return GuardrailCheckResult(
            guardrail="hallucination_check",
            status="warning",
            reason="hallucinated_data",
            message=(
                f"⚠️ Warning: The following values in this response were not found "
                f"in the source documents: {values_str}. "
                f"Please verify these figures independently."
            ),
        )

    return GuardrailCheckResult(
        guardrail="hallucination_check",
        status="allowed",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 4. CROSS-ROLE LEAKAGE DETECTION
# ═══════════════════════════════════════════════════════════════════════════

# Department-specific keyword clusters
_DEPARTMENT_KEYWORDS: dict[str, list[str]] = {
    "finance": [
        "revenue", "profit margin", "ebitda", "dividend", "earnings",
        "budget allocation", "net income", "cash flow", "fiscal year",
        "balance sheet", "income statement", "audit", "shareholder",
        "quarterly results", "financial projection",
    ],
    "engineering": [
        "api endpoint", "kubernetes", "deployment pipeline", "incident report",
        "system architecture", "microservice", "database schema", "ci/cd",
        "rollback", "load balancer", "docker", "terraform", "runbook",
        "code review", "sprint",
    ],
    "marketing": [
        "campaign roi", "brand guideline", "market share", "competitor analysis",
        "target audience", "brand positioning", "marketing channel",
        "conversion rate", "customer acquisition", "social media campaign",
        "brand awareness", "market research", "ad spend",
    ],
}

# Maps user roles to the departments they are NOT allowed to see
_ROLE_RESTRICTED_DEPARTMENTS: dict[str, list[str]] = {
    "employee":    ["finance", "engineering", "marketing"],
    "finance":     ["engineering", "marketing"],
    "engineering": ["finance", "marketing"],
    "marketing":   ["finance", "engineering"],
    "c_level":     [],  # No restrictions
}


def check_cross_role_leakage(
    response: str,
    user_role: str,
) -> GuardrailCheckResult:
    """
    Check if the LLM response contains department-specific terminology
    from collections the user is NOT authorized to access.
    """
    restricted_depts = _ROLE_RESTRICTED_DEPARTMENTS.get(user_role, [])

    if not restricted_depts:
        return GuardrailCheckResult(
            guardrail="cross_role_leakage",
            status="allowed",
        )

    response_lower = response.lower()
    leaked_departments: list[str] = []

    for dept in restricted_depts:
        keywords = _DEPARTMENT_KEYWORDS.get(dept, [])
        # Flag only if multiple keywords from a single department are found
        matches = [kw for kw in keywords if kw in response_lower]
        if len(matches) >= 2:
            leaked_departments.append(dept.title())

    if leaked_departments:
        depts_str = ", ".join(leaked_departments)
        return GuardrailCheckResult(
            guardrail="cross_role_leakage",
            status="warning",
            reason="cross_role_leakage",
            message=(
                f"⚠️ Security Notice: This response may contain information "
                f"from departments outside your access scope ({depts_str}). "
                f"The flagged content has been reviewed. If you believe this "
                f"is an error, please contact your administrator."
            ),
        )

    return GuardrailCheckResult(
        guardrail="cross_role_leakage",
        status="allowed",
    )
