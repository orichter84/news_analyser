"""Unit tests for _rotate_feed_urls() in feed.py.

Ensures every configured feed eventually leads the round-robin so a tight
LLM quota (only a few articles get through before GeminiQuotaExceededError
aborts the cycle) doesn't permanently starve feeds further down feeds.txt.
"""

import json

from news_analyser import feed


def _read_offset(rotation_file) -> int:
    return json.loads(rotation_file.read_text(encoding="utf-8"))["offset"]


class TestRotateFeedUrls:
    def test_empty_list_returns_empty_and_writes_nothing(self, _isolate_feed_state_files):
        assert feed._rotate_feed_urls([]) == []
        assert not feed._ROTATION_FILE.exists()

    def test_first_call_starts_at_offset_zero(self):
        urls = ["a", "b", "c"]
        assert feed._rotate_feed_urls(urls) == ["a", "b", "c"]
        assert _read_offset(feed._ROTATION_FILE) == 1

    def test_second_call_rotates_by_one(self):
        urls = ["a", "b", "c"]
        feed._rotate_feed_urls(urls)  # offset 0 -> 1
        assert feed._rotate_feed_urls(urls) == ["b", "c", "a"]
        assert _read_offset(feed._ROTATION_FILE) == 2

    def test_every_feed_leads_once_over_a_full_cycle(self):
        urls = ["a", "b", "c", "d"]
        leaders = [feed._rotate_feed_urls(urls)[0] for _ in range(len(urls))]
        assert sorted(leaders) == sorted(urls)  # each fed led exactly once

    def test_wraps_around_after_a_full_cycle(self):
        urls = ["a", "b", "c"]
        for _ in range(len(urls)):
            feed._rotate_feed_urls(urls)
        assert feed._rotate_feed_urls(urls) == ["a", "b", "c"]  # back to the start

    def test_corrupted_rotation_file_fails_open_to_offset_zero(self):
        feed._ROTATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        feed._ROTATION_FILE.write_text("not valid json{{{", encoding="utf-8")
        assert feed._rotate_feed_urls(["a", "b"]) == ["a", "b"]

    def test_shrunk_feed_list_does_not_crash_on_stale_offset(self):
        feed._atomic_write_json(feed._ROTATION_FILE, {"offset": 5})
        # only 2 feeds now, but the stored offset assumes at least 6
        assert feed._rotate_feed_urls(["a", "b"]) == ["b", "a"]

    def test_write_is_atomic_no_leftover_temp_files(self):
        feed._rotate_feed_urls(["a", "b"])
        siblings = list(feed._ROTATION_FILE.parent.iterdir())
        assert siblings == [feed._ROTATION_FILE]
