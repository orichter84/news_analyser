"""Unit tests for detect_groups() — exercises the adapter interface contract
(a `.generate(system_prompt, input_data)` call) with fake adapters, without any
real LLM or network calls."""

import pytest

from news_analyser.agents.errors import GeminiQuotaExceededError
from news_analyser.agents.group_detector import detect_groups


class _FakeAdapter:
    """Minimal double satisfying the adapter interface used by detect_groups()."""

    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error
        self.calls = []

    def generate(self, system_prompt, input_data):
        self.calls.append({"system_prompt": system_prompt, "input_data": input_data})
        if self._error is not None:
            raise self._error
        return self._response


def test_returns_parsed_group_list_on_valid_response():
    adapter = _FakeAdapter(response='[{"term": "Ausländer", "type": "ethnic_origin"}]')
    result = detect_groups("irgendein Text", adapter)
    assert result == [{"term": "ausländer", "type": "ethnic_origin"}]


def test_calls_adapter_with_text_as_input_data():
    adapter = _FakeAdapter(response="[]")
    detect_groups("mein artikeltext", adapter)
    assert adapter.calls[0]["input_data"] == {"text": "mein artikeltext"}


def test_ignores_non_dict_items_in_response():
    adapter = _FakeAdapter(response='[{"term": "a", "type": "b"}, "not-a-dict", {"term": "c"}]')
    result = detect_groups("text", adapter)
    assert result == [{"term": "a", "type": "b"}]


def test_non_list_response_returns_empty_list():
    adapter = _FakeAdapter(response='{"not": "a list"}')
    assert detect_groups("text", adapter) == []


def test_unparseable_response_returns_empty_list():
    adapter = _FakeAdapter(response="not json at all")
    assert detect_groups("text", adapter) == []


def test_adapter_error_returns_empty_list_when_not_quota_related(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    adapter = _FakeAdapter(error=RuntimeError("network hiccup"))
    assert detect_groups("text", adapter) == []


def test_adapter_gemini_quota_error_propagates_as_domain_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    adapter = _FakeAdapter(error=RuntimeError("RESOURCE_EXHAUSTED: quota exceeded"))
    with pytest.raises(GeminiQuotaExceededError):
        detect_groups("text", adapter)
