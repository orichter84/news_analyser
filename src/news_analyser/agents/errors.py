"""Errors and error classification shared by analysis passes."""

from __future__ import annotations

import os

try:
    import openai
except ImportError:
    openai = None


class GeminiQuotaExceededError(RuntimeError):
    """Raised when Gemini rejects a request because its quota is exhausted."""


class AnalysisAbortedError(RuntimeError):
    """Raised when an analysis pass fails and the article must not be stored.

    Covers adapter errors, timeouts, truncated or unparseable output — anything
    except an exhausted Gemini quota, which keeps its own error type because it
    triggers the feed cooldown.
    """

    def __init__(self, stage: str, reason: str) -> None:
        super().__init__(f"{stage}: {reason}")
        self.stage = stage
        self.reason = reason


def is_gemini_quota_error(exc: Exception) -> bool:
    """Return whether an adapter error indicates Gemini's exhausted quota."""
    if os.environ.get("LLM_PROVIDER", "openai").lower() != "gemini":
        return False

    current: BaseException | None = exc
    while current is not None:
        if openai is not None and isinstance(current, openai.RateLimitError):
            return True
        if getattr(current, "status_code", None) == 429:
            return True
        current = current.__cause__

    message = str(exc).lower()
    return any(marker in message for marker in (
        "resource_exhausted",
        "resource exhausted",
        "daily limit",
    ))


def raise_if_gemini_quota_error(exc: Exception) -> None:
    """Raise a domain-specific error when an adapter reports exhausted Gemini quota."""
    if is_gemini_quota_error(exc):
        raise GeminiQuotaExceededError(str(exc)) from exc