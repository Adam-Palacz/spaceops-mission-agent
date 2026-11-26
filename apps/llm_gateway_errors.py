"""LLM gateway exception types (PS5.1, RD1.3)."""

from __future__ import annotations

from typing import Any


class LLMGatewayTimeoutError(Exception):
    """Raised when upstream LLM call times out."""


class LLMGatewayProviderError(Exception):
    """Raised when upstream LLM provider returns a non-timeout error."""


class LLMBudgetExceededError(Exception):
    """Raised when LLM budget guardrail refuses a call (PS5.6; no backend fallback)."""


class LLMEgressDeniedError(Exception):
    """Raised when mission-data model egress policy refuses a call (RD1.3; fail-closed, no fallback)."""

    def __init__(self, message: str, *, decision: Any = None) -> None:
        super().__init__(message)
        self.decision = decision
