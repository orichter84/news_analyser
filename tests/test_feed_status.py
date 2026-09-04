"""Unit tests for the feed status file (data/feed_status.json) written by
feed.py and read by the backend's /status endpoint. Filesystem access is
redirected to a tmp_path; network/DB/LLM calls are stubbed out."""

import json

import pytest

from news_analyser import feed
from news_analyser.agents.errors import GeminiQuotaExceededError
from news_analyser.config import FeedConfig


@pytest.fixture
def isolated_files(_isolate_feed_state_files):
    # All of feed.py's state files are already redirected into tmp_path by the
    # autouse fixture in conftest.py; this just hands back the specific path.
    return feed._STATUS_FILE


def _cfg(**overrides) -> FeedConfig:
    defaults = dict(
        mode="manual",
        interval=3600,
        max_articles=5,
        feeds_file="unused.txt",
        allowed_topics=frozenset(),
    )
    defaults.update(overrides)
    return FeedConfig(**defaults)


def _read_status(status_file) -> dict:
    return json.loads(status_file.read_text(encoding="utf-8"))


class TestWriteStatus:
    def test_writes_pid_and_started_at(self, isolated_files):
        feed._write_status(mode="manual")
        data = _read_status(isolated_files)
        assert data["pid"] == feed.os.getpid()
        assert data["mode"] == "manual"
        assert data["started_at"] == feed._PROCESS_STARTED_AT

    def test_merges_with_existing_fields_instead_of_overwriting(self, isolated_files):
        feed._write_status(mode="auto")
        feed._write_status(last_run_status="ok", last_run_articles=3)

        data = _read_status(isolated_files)
        assert data["mode"] == "auto"  # preserved from the earlier write
        assert data["last_run_status"] == "ok"
        assert data["last_run_articles"] == 3

    def test_write_is_atomic_no_leftover_temp_files(self, isolated_files):
        feed._write_status(mode="manual")
        siblings = list(isolated_files.parent.iterdir())
        assert siblings == [isolated_files]


class TestRunOnceStatusReporting:
    def test_cooldown_active_reports_quota_cooldown(self, monkeypatch, isolated_files):
        feed.start_quota_cooldown()

        def fail_if_called(*args, **kwargs):
            raise AssertionError("should not fetch during an active cooldown")

        monkeypatch.setattr(feed, "_load_feed_urls", fail_if_called)

        feed.run_once(_cfg())

        assert _read_status(isolated_files)["last_run_status"] == "quota_cooldown"

    def test_no_new_articles_reports_status_and_zero_count(self, monkeypatch, isolated_files):
        monkeypatch.setattr(feed, "_load_feed_urls", lambda *a, **k: ["http://feed.example/rss"])
        monkeypatch.setattr(feed, "_fetch_new_urls", lambda *a, **k: iter([]))

        feed.run_once(_cfg())

        data = _read_status(isolated_files)
        assert data["last_run_status"] == "no_new_articles"
        assert data["last_run_articles"] == 0
        assert data["last_run_at"] is not None

    def test_successful_run_reports_ok_with_article_count(self, monkeypatch, isolated_files):
        monkeypatch.setattr(feed, "_load_feed_urls", lambda *a, **k: ["http://feed.example/rss"])
        monkeypatch.setattr(feed, "_fetch_new_urls", lambda *a, **k: iter(["http://a", "http://b"]))
        monkeypatch.setattr(feed, "run", lambda url: None)

        feed.run_once(_cfg())

        data = _read_status(isolated_files)
        assert data["last_run_status"] == "ok"
        assert data["last_run_articles"] == 2

    def test_quota_error_mid_run_reports_partial_count(self, monkeypatch, isolated_files):
        monkeypatch.setattr(feed, "_load_feed_urls", lambda *a, **k: ["http://feed.example/rss"])
        monkeypatch.setattr(
            feed, "_fetch_new_urls", lambda *a, **k: iter(["http://a", "http://b", "http://c"])
        )

        def fake_run(url):
            if url == "http://b":
                raise GeminiQuotaExceededError("quota exhausted")

        monkeypatch.setattr(feed, "run", fake_run)

        feed.run_once(_cfg())

        data = _read_status(isolated_files)
        assert data["last_run_status"] == "quota_exceeded"
        assert data["last_run_articles"] == 1  # only "a" completed before "b" raised
