"""Unit tests for StrictOpenAIAdapter._parse_response — no network, no client init."""

from types import SimpleNamespace

import pytest
from llm_adapter import LLMGenerationError

from news_analyser.strict_openai_adapter import StrictOpenAIAdapter


def _adapter():
    adapter = StrictOpenAIAdapter.__new__(StrictOpenAIAdapter)
    adapter._max_tokens = 8192
    return adapter


def _response(content, finish_reason="stop"):
    choice = SimpleNamespace(finish_reason=finish_reason, message=SimpleNamespace(content=content))
    return SimpleNamespace(choices=[choice])


def test_returns_stripped_content_on_stop():
    assert _adapter()._parse_response(_response('  {"a": 1}\n')) == '{"a": 1}'


def test_accepts_missing_finish_reason():
    assert _adapter()._parse_response(_response('{"a": 1}', finish_reason=None)) == '{"a": 1}'


@pytest.mark.parametrize("reason", ["length", "content_filter", "model_length", "error"])
def test_raises_on_incomplete_finish_reason(reason):
    with pytest.raises(LLMGenerationError, match=reason):
        _adapter()._parse_response(_response('{"a": 1, "b": [', finish_reason=reason))


@pytest.mark.parametrize("content", [None, "", "   "])
def test_raises_on_empty_content(content):
    with pytest.raises(LLMGenerationError):
        _adapter()._parse_response(_response(content))


def test_raises_on_no_choices():
    with pytest.raises(LLMGenerationError):
        _adapter()._parse_response(SimpleNamespace(choices=[]))
