"""Unit tests for backend/routers/status.py — the /status endpoint's chroma
health check, feed-status file parsing, and the PID+start-time liveness check
that guards against PID reuse. Imported the same way the real app does
(backend/ on sys.path, flat `routers` package), so no FastAPI app needs to
be spun up as a separate process."""

import datetime
import json
import os
import sys
from pathlib import Path

import psutil
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from routers import status as status_router  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_status_file(tmp_path, monkeypatch):
    status_file = tmp_path / "feed_status.json"
    monkeypatch.setattr(status_router, "_FEED_STATUS_FILE", status_file)
    return status_file


def _own_start_iso() -> str:
    return datetime.datetime.fromtimestamp(
        psutil.Process(os.getpid()).create_time(), tz=datetime.timezone.utc
    ).isoformat()


def _unused_pid() -> int:
    """A PID that (almost certainly) doesn't correspond to a running process."""
    candidate = 2**30
    while psutil.pid_exists(candidate):
        candidate -= 1
    return candidate


class TestProcessAlive:
    def test_false_for_no_pid(self):
        assert status_router._process_alive(None, None) is False

    def test_false_for_nonexistent_pid(self):
        assert status_router._process_alive(_unused_pid(), None) is False

    def test_true_for_live_pid_without_started_at(self):
        assert status_router._process_alive(os.getpid(), None) is True

    def test_true_for_live_pid_with_matching_started_at(self):
        assert status_router._process_alive(os.getpid(), _own_start_iso()) is True

    def test_false_for_live_pid_with_mismatched_started_at_guards_against_pid_reuse(self):
        # Same (real, running) PID as this test process, but a start time that's
        # nowhere near its actual creation time — simulates the PID having been
        # reused by an unrelated process after the original one (e.g. the feed
        # daemon) died.
        stale_started_at = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc).isoformat()
        assert status_router._process_alive(os.getpid(), stale_started_at) is False

    def test_true_for_unparseable_started_at_fails_open_to_pid_existence(self):
        assert status_router._process_alive(os.getpid(), "not-a-timestamp") is True


class TestChromaStatus:
    def test_ok_when_heartbeat_succeeds(self, monkeypatch):
        class _FakeClient:
            def heartbeat(self):
                return 12345

        monkeypatch.setattr(status_router, "get_client", lambda: _FakeClient())
        assert status_router._chroma_status() == {"status": "ok"}

    def test_error_when_heartbeat_raises(self, monkeypatch):
        class _FakeClient:
            def heartbeat(self):
                raise ConnectionError("refused")

        monkeypatch.setattr(status_router, "get_client", lambda: _FakeClient())
        result = status_router._chroma_status()
        assert result["status"] == "error"
        assert "refused" in result["detail"]


class TestFeedStatus:
    def test_defaults_when_file_missing(self):
        feed = status_router._feed_status()
        assert feed["pid"] is None
        assert feed["running"] is False

    def test_defaults_when_file_corrupted(self, isolated_status_file):
        isolated_status_file.write_text("not valid json{{{", encoding="utf-8")
        feed = status_router._feed_status()
        assert feed["pid"] is None
        assert feed["running"] is False

    def test_running_true_for_live_matching_process(self, isolated_status_file):
        isolated_status_file.write_text(
            json.dumps({"pid": os.getpid(), "started_at": _own_start_iso(), "mode": "auto"}),
            encoding="utf-8",
        )
        feed = status_router._feed_status()
        assert feed["running"] is True
        assert feed["mode"] == "auto"

    def test_running_false_for_dead_pid_from_stored_file(self, isolated_status_file):
        isolated_status_file.write_text(
            json.dumps({"pid": _unused_pid(), "started_at": None}), encoding="utf-8"
        )
        assert status_router._feed_status()["running"] is False


class TestStatusEndpoint:
    def test_returns_backend_chroma_and_feed_sections(self, monkeypatch):
        def _raise():
            raise ConnectionError("no chroma")

        monkeypatch.setattr(status_router, "get_client", _raise)
        app = FastAPI()
        app.include_router(status_router.router)
        client = TestClient(app)
        response = client.get("/status")
        assert response.status_code == 200
        body = response.json()
        assert body["backend"] == {"status": "ok"}
        assert body["chroma"]["status"] == "error"
        assert "running" in body["feed"]


class TestTailLines:
    def test_missing_file_returns_empty_list(self, tmp_path):
        assert status_router._tail_lines(tmp_path / "missing.log", 10) == []

    def test_returns_all_lines_when_under_the_limit(self, tmp_path):
        log_file = tmp_path / "small.log"
        log_file.write_text("a\nb\nc\n", encoding="utf-8")
        assert status_router._tail_lines(log_file, 10) == ["a", "b", "c"]

    def test_truncates_to_max_lines(self, tmp_path):
        log_file = tmp_path / "many.log"
        log_file.write_text("\n".join(f"line{i}" for i in range(10)), encoding="utf-8")
        assert status_router._tail_lines(log_file, 3) == ["line7", "line8", "line9"]

    def test_strips_ansi_color_codes(self, tmp_path):
        # ChromaDB's startup banner (and uvicorn's colored log levels) contain
        # ANSI escape sequences that must not leak into the plain-text UI.
        log_file = tmp_path / "colored.log"
        log_file.write_text("\x1b[38;5;069mhello\x1b[0m\nplain\n", encoding="utf-8")
        assert status_router._tail_lines(log_file, 10) == ["hello", "plain"]

    def test_bounded_byte_window_still_yields_correct_tail(self, tmp_path, monkeypatch):
        # Each "entry-NNN" line is 10 bytes incl. newline; a 80-byte window covers
        # the last ~8 lines but not the full 550-byte file, exercising the
        # seek-from-end path while still comfortably holding the 5 requested lines.
        monkeypatch.setattr(status_router, "_LOG_TAIL_BYTES", 80)
        log_file = tmp_path / "big.log"
        log_file.write_text("\n".join(f"entry-{i:03d}" for i in range(50)), encoding="utf-8")

        result = status_router._tail_lines(log_file, 5)

        assert result == ["entry-045", "entry-046", "entry-047", "entry-048", "entry-049"]


class TestLogEndpoint:
    def test_returns_lines_for_known_log(self, tmp_path, monkeypatch):
        log_file = tmp_path / "app.log"
        log_file.write_text("hello\nworld\n", encoding="utf-8")
        monkeypatch.setitem(status_router._LOG_FILES, "app", log_file)

        app = FastAPI()
        app.include_router(status_router.router)
        response = TestClient(app).get("/status/logs/app")

        assert response.status_code == 200
        assert response.json() == {"lines": ["hello", "world"]}

    def test_unknown_log_name_returns_404(self):
        app = FastAPI()
        app.include_router(status_router.router)
        response = TestClient(app).get("/status/logs/does-not-exist")
        assert response.status_code == 404
