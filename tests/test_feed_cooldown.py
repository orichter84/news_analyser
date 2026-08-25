"""Unit tests for the Gemini quota cooldown persistence and run_once() control
flow in feed.py. Filesystem access is redirected to a tmp_path; network/DB/LLM
calls are stubbed out so these tests are fully isolated."""

import json
import time

import pytest

from news_analyser import feed
from news_analyser.agents.errors import GeminiQuotaExceededError
from news_analyser.config import FeedConfig


@pytest.fixture(autouse=True)
def isolated_cooldown_file(tmp_path, monkeypatch):
    cooldown_file = tmp_path / "gemini_quota_cooldown.json"
    monkeypatch.setattr(feed, "_QUOTA_COOLDOWN_FILE", cooldown_file)
    return cooldown_file


class TestQuotaCooldownPersistence:
    def test_no_cooldown_when_file_absent(self):
        assert feed._quota_cooldown_remaining() == 0.0

    def test_remaining_positive_right_after_starting_cooldown(self):
        feed.start_quota_cooldown()
        remaining = feed._quota_cooldown_remaining()
        assert 0 < remaining <= feed._GEMINI_QUOTA_COOLDOWN_SECONDS

    def test_write_is_atomic_no_leftover_temp_files(self, isolated_cooldown_file):
        feed.start_quota_cooldown()
        siblings = list(isolated_cooldown_file.parent.iterdir())
        assert siblings == [isolated_cooldown_file]

    def test_expired_cooldown_is_cleaned_up(self, isolated_cooldown_file):
        isolated_cooldown_file.write_text(json.dumps({"until": time.time() - 10}), encoding="utf-8")
        assert feed._quota_cooldown_remaining() == 0.0
        assert not isolated_cooldown_file.exists()

    def test_corrupted_file_fails_closed_with_fresh_cooldown(self, isolated_cooldown_file):
        isolated_cooldown_file.write_text("not valid json{{{", encoding="utf-8")

        remaining = feed._quota_cooldown_remaining()

        assert remaining == pytest.approx(feed._GEMINI_QUOTA_COOLDOWN_SECONDS, abs=5)
        # a corrupted read must self-heal into a fresh, well-formed cooldown file
        assert json.loads(isolated_cooldown_file.read_text(encoding="utf-8"))["until"] > time.time()


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


class TestRunOnce:
    def test_skips_fetch_entirely_when_cooldown_active(self, monkeypatch):
        feed.start_quota_cooldown()

        def fail_if_called(*args, **kwargs):
            raise AssertionError("_load_feed_urls should not be called during an active cooldown")

        monkeypatch.setattr(feed, "_load_feed_urls", fail_if_called)

        assert feed.run_once(_cfg()) is True

    def test_quota_error_mid_run_starts_cooldown_and_stops(self, monkeypatch):
        monkeypatch.setattr(feed, "_load_feed_urls", lambda *a, **k: ["http://feed.example/rss"])
        monkeypatch.setattr(
            feed, "_fetch_new_urls", lambda *a, **k: iter(["http://a", "http://b", "http://c"])
        )

        seen = []

        def fake_run(url):
            seen.append(url)
            if url == "http://b":
                raise GeminiQuotaExceededError("quota exhausted")

        monkeypatch.setattr(feed, "run", fake_run)

        result = feed.run_once(_cfg())

        assert result is True
        assert seen == ["http://a", "http://b"]  # stops after the quota error, never reaches c
        assert feed._quota_cooldown_remaining() > 0

    def test_successful_run_returns_false_without_starting_cooldown(self, monkeypatch):
        monkeypatch.setattr(feed, "_load_feed_urls", lambda *a, **k: ["http://feed.example/rss"])
        monkeypatch.setattr(feed, "_fetch_new_urls", lambda *a, **k: iter(["http://a", "http://b"]))

        seen = []
        monkeypatch.setattr(feed, "run", lambda url: seen.append(url))

        result = feed.run_once(_cfg())

        assert result is False
        assert seen == ["http://a", "http://b"]
        assert feed._quota_cooldown_remaining() == 0.0

    def test_no_new_articles_returns_false(self, monkeypatch):
        monkeypatch.setattr(feed, "_load_feed_urls", lambda *a, **k: ["http://feed.example/rss"])
        monkeypatch.setattr(feed, "_fetch_new_urls", lambda *a, **k: iter([]))

        assert feed.run_once(_cfg()) is False
