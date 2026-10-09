"""Abort handling in analyzer.py: every pass failure becomes AnalysisAbortedError
(with stage + reason) and is logged once, with the article URL."""

import logging

import pytest

from news_analyser.agents import analyzer
from news_analyser.agents.errors import AnalysisAbortedError, GeminiQuotaExceededError
from news_analyser.scraper import Article


class _FakeAdapter:
    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error

    def generate(self, system_prompt, input_data):
        if self._error is not None:
            raise self._error
        return self._response


@pytest.fixture(autouse=True)
def _no_debug_files(monkeypatch):
    monkeypatch.setattr(analyzer, "_write_debug", lambda *a, **k: None)


def _run(adapter):
    return analyzer._run_pass(adapter, "Pass 2", "prompt", {"text": "x"}, "f.txt", "run")


def test_run_pass_returns_parsed_result():
    assert _run(_FakeAdapter(response='{"a": 1}')) == {"a": 1}


def test_run_pass_adapter_error_aborts_with_stage(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mistral")
    adapter = _FakeAdapter(error=RuntimeError("Antwort unvollständig (finish_reason='length')"))
    with pytest.raises(AnalysisAbortedError, match="Pass 2: Antwort unvollständig") as info:
        _run(adapter)
    assert info.value.stage == "Pass 2"


def test_run_pass_truncated_output_aborts_with_stage():
    with pytest.raises(AnalysisAbortedError, match="Pass 2: Antwort abgeschnitten"):
        _run(_FakeAdapter(response='{"a": [1, 2'))


def test_run_pass_gemini_quota_keeps_its_own_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    with pytest.raises(GeminiQuotaExceededError):
        _run(_FakeAdapter(error=RuntimeError("RESOURCE_EXHAUSTED")))


def test_analyze_article_logs_abort_with_url(monkeypatch, caplog):
    def _abort(article, skip_anonymize):
        raise AnalysisAbortedError("Pass 1", "Antwort abgeschnitten")

    monkeypatch.setattr(analyzer, "_analyze_article", _abort)
    article = Article(url="https://example.org/a", domain="example.org", text="t",
                      fetched_at="2026-10-09T00:00:00Z", word_count=1)

    with caplog.at_level(logging.ERROR, logger=analyzer.logger.name):
        with pytest.raises(AnalysisAbortedError):
            analyzer.analyze_article(article)

    assert "https://example.org/a" in caplog.text
    assert "Pass 1: Antwort abgeschnitten" in caplog.text
    assert "nichts gespeichert" in caplog.text
