"""
Guardrail Service — orchestrates all input and output guardrail checks.

Responsibilities:
  1. Run input guardrails in fail-fast order before retrieval.
  2. Run output guardrails independently after LLM generation.
  3. Log every guardrail trigger to the MySQL guardrail_logs table.
  4. Return structured InputValidationResult / OutputValidationResult.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.guardrails.schemas import (
    GuardrailCheckResult,
    InputValidationResult,
    OutputValidationResult,
)
from app.guardrails.input_guardrails import (
    check_rate_limit,
    check_pii,
    check_prompt_injection,
    check_off_topic,
)
from app.guardrails.output_guardrails import (
    check_source_citations,
    check_grounding,
    check_hallucinated_numbers,
    check_cross_role_leakage,
)
from app.core.database import SessionLocal
from app.models.guardrail_log import GuardrailLog

logger = logging.getLogger(__name__)


class GuardrailService:
    """Orchestrates input and output guardrail checks with MySQL logging."""

    # ── INPUT VALIDATION ─────────────────────────────────────────────────

    def validate_input(
        self,
        query: str,
        user_id: str,
        user_role: Optional[str] = None,
    ) -> InputValidationResult:
        """
        Run all input guardrails in fail-fast order.
        Returns immediately on the first 'blocked' check.
        """
        checks: list[GuardrailCheckResult] = []

        # Ordered fail-fast pipeline
        input_checks = [
            lambda: check_rate_limit(user_id),
            lambda: check_pii(query),
            lambda: check_prompt_injection(query),
            lambda: check_off_topic(query),
        ]

        overall_status = "allowed"

        for check_fn in input_checks:
            result = check_fn()
            checks.append(result)

            # Log non-allowed results to MySQL
            if result.status != "allowed":
                self._log(
                    user_id=user_id,
                    user_role=user_role,
                    query=query if result.guardrail != "pii_detection" else "[REDACTED]",
                    guardrail_name=result.guardrail,
                    guardrail_type="input",
                    status=result.status,
                    reason=result.reason,
                )

            # Fail-fast: stop on blocked
            if result.status == "blocked":
                overall_status = "blocked"
                break

            # Track warnings
            if result.status == "warning":
                overall_status = "warning"

        return InputValidationResult(
            status=overall_status,
            checks=checks,
        )

    # ── OUTPUT VALIDATION ────────────────────────────────────────────────

    def validate_output(
        self,
        response: str,
        retrieved_chunks: Optional[list[dict]] = None,
        user_role: str = "employee",
        user_id: Optional[str] = None,
        query: Optional[str] = None,
    ) -> OutputValidationResult:
        """
        Run all output guardrails independently (no fail-fast).
        Returns aggregated results with warnings.
        """
        checks: list[GuardrailCheckResult] = []
        warnings: list[str] = []

        # All output checks run independently
        output_checks = [
            lambda: check_source_citations(response, retrieved_chunks),
            lambda: check_grounding(response, retrieved_chunks),
            lambda: check_hallucinated_numbers(response, retrieved_chunks),
            lambda: check_cross_role_leakage(response, user_role),
        ]

        overall_status = "allowed"

        for check_fn in output_checks:
            result = check_fn()
            checks.append(result)

            if result.status == "warning":
                overall_status = "warning"
                if result.message:
                    warnings.append(result.message)

                # Log warnings to MySQL
                self._log(
                    user_id=user_id,
                    user_role=user_role,
                    query=query,
                    guardrail_name=result.guardrail,
                    guardrail_type="output",
                    status=result.status,
                    reason=result.reason,
                )

            elif result.status == "blocked":
                overall_status = "blocked"
                self._log(
                    user_id=user_id,
                    user_role=user_role,
                    query=query,
                    guardrail_name=result.guardrail,
                    guardrail_type="output",
                    status=result.status,
                    reason=result.reason,
                )

        return OutputValidationResult(
            status=overall_status,
            checks=checks,
            warnings=warnings,
        )

    # ── LOGGING ──────────────────────────────────────────────────────────

    @staticmethod
    def _log(
        user_id: Optional[str],
        user_role: Optional[str],
        query: Optional[str],
        guardrail_name: str,
        guardrail_type: str,
        status: str,
        reason: Optional[str],
    ) -> None:
        """Persist a guardrail event to the MySQL guardrail_logs table."""
        try:
            db = SessionLocal()
            log_entry = GuardrailLog(
                timestamp=datetime.now(timezone.utc),
                user_id=user_id,
                user_role=user_role,
                query=query,
                guardrail_name=guardrail_name,
                guardrail_type=guardrail_type,
                status=status,
                reason=reason,
            )
            db.add(log_entry)
            db.commit()
            logger.info(
                "Guardrail log | %s | %s | %s | %s",
                guardrail_type,
                guardrail_name,
                status,
                reason,
            )
        except Exception as exc:
            logger.error("Failed to persist guardrail log: %s", exc)
            db.rollback()
        finally:
            db.close()


# Module-level singleton
guardrail_service = GuardrailService()
