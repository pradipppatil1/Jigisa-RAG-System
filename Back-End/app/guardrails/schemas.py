"""
Pydantic schemas for the Guardrails module.

Every guardrail check returns a uniform structured result.
"""

from pydantic import BaseModel
from typing import Optional, Literal


class GuardrailCheckResult(BaseModel):
    """Result of a single guardrail check."""
    guardrail: str
    status: Literal["blocked", "allowed", "warning"]
    reason: Optional[str] = None
    message: Optional[str] = None


class InputValidationResult(BaseModel):
    """Aggregated result of all input guardrail checks."""
    status: Literal["blocked", "allowed", "warning"]
    checks: list[GuardrailCheckResult] = []

    @property
    def is_blocked(self) -> bool:
        return self.status == "blocked"


class OutputValidationResult(BaseModel):
    """Aggregated result of all output guardrail checks."""
    status: Literal["blocked", "allowed", "warning"]
    checks: list[GuardrailCheckResult] = []
    warnings: list[str] = []
