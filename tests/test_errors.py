"""Unit tests for Gemini quota-error classification in agents/errors.py."""

import httpx
import openai
import pytest

from news_analyser.agents.errors import (
    GeminiQuotaExceededError,
    is_gemini_quota_error,
    raise_if_gemini_quota_error,
)


def _rate_limit_error(message: str = "rate limited") -> openai.RateLimitError:
    response = httpx.Response(status_code=429, request=httpx.Request("POST", "https://example.com"))
    return openai.RateLimitError(message, response=response, body=None)


@pytest.fixture(autouse=True)
def gemini_provider(monkeypatch):
    """Most tests assume LLM_PROVIDER=gemini; opt out explicitly where needed."""
    monkeypatch.setenv("LLM_PROVIDER", "gemini")


class TestIsGeminiQuotaError:
    def test_false_when_provider_is_not_gemini(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        exc = Exception("quota exceeded")
        assert is_gemini_quota_error(exc) is False

    def test_true_for_wrapped_rate_limit_error_via_cause_chain(self):
        cause = _rate_limit_error("You exceeded your current quota")
        wrapper = RuntimeError("OpenAI API-Fehler: " + str(cause))
        wrapper.__cause__ = cause
        assert is_gemini_quota_error(wrapper) is True

    def test_true_for_bare_rate_limit_error(self):
        assert is_gemini_quota_error(_rate_limit_error()) is True

    def test_true_for_generic_exception_with_status_code_429(self):
        exc = RuntimeError("something went wrong")
        exc.status_code = 429
        assert is_gemini_quota_error(exc) is True

    def test_true_for_resource_exhausted_text_marker(self):
        exc = RuntimeError("Error: RESOURCE_EXHAUSTED - please retry later")
        assert is_gemini_quota_error(exc) is True

    def test_true_for_daily_limit_text_marker(self):
        exc = RuntimeError("You have hit your daily limit")
        assert is_gemini_quota_error(exc) is True

    def test_false_for_unrelated_error(self):
        exc = RuntimeError("connection refused")
        assert is_gemini_quota_error(exc) is False

    def test_false_for_unrelated_error_with_unrelated_status_code(self):
        exc = RuntimeError("not found")
        exc.status_code = 404
        assert is_gemini_quota_error(exc) is False


class TestRaiseIfGeminiQuotaError:
    def test_raises_gemini_quota_exceeded_error_with_cause(self):
        cause = _rate_limit_error("quota exhausted")
        with pytest.raises(GeminiQuotaExceededError) as excinfo:
            raise_if_gemini_quota_error(cause)
        assert excinfo.value.__cause__ is cause

    def test_no_op_for_non_quota_exception(self):
        exc = RuntimeError("connection refused")
        assert raise_if_gemini_quota_error(exc) is None
