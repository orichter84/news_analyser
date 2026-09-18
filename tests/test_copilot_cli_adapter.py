"""Unit tests for CopilotCliAdapter that don't require the real `copilot` binary."""

from pathlib import Path

from news_analyser.copilot_cli_adapter import CopilotCliAdapter


def make_adapter(**config) -> CopilotCliAdapter:
    adapter = CopilotCliAdapter()
    # Bypass initialize()'s shutil.which() PATH check -- these tests exercise
    # command construction and cleanup, not the real subprocess call.
    adapter._model = config.get("model", "gpt-5.4")
    adapter._timeout = config.get("timeout", 180)
    adapter._cli_path = "copilot"
    return adapter


class TestBuildCmd:
    def test_locks_down_tools_and_sets_model(self):
        adapter = make_adapter(model="claude-sonnet-4.5")
        cmd = adapter._build_cmd("a prompt", "some-session-id")
        assert cmd[0] == "copilot"
        assert "-p" in cmd and cmd[cmd.index("-p") + 1] == "a prompt"
        assert "--available-tools" in cmd
        assert "--model" in cmd and cmd[cmd.index("--model") + 1] == "claude-sonnet-4.5"
        assert "--session-id" in cmd and cmd[cmd.index("--session-id") + 1] == "some-session-id"
        assert "-s" in cmd  # silent -- only the agent response, no stats

    def test_available_tools_has_no_argument(self):
        # A bare --available-tools disables all tools per the CLI's own docs;
        # passing a value would instead scope to that one tool.
        adapter = make_adapter()
        cmd = adapter._build_cmd("prompt", "sid")
        idx = cmd.index("--available-tools")
        assert cmd[idx + 1] == "--model"  # next token is the next flag, not a tool name


class TestCleanupSession:
    def test_removes_exactly_the_named_session_directory(self, tmp_path, monkeypatch):
        import news_analyser.copilot_cli_adapter as mod

        monkeypatch.setattr(mod, "_SESSION_STATE_DIR", tmp_path)
        target = tmp_path / "session-a"
        other = tmp_path / "session-b"
        target.mkdir()
        other.mkdir()
        (target / "events.jsonl").write_text("{}")

        adapter = make_adapter()
        adapter._cleanup_session("session-a")

        assert not target.exists()
        assert other.exists()  # untouched -- only the exact session id is deleted

    def test_missing_directory_does_not_raise(self, tmp_path, monkeypatch):
        import news_analyser.copilot_cli_adapter as mod

        monkeypatch.setattr(mod, "_SESSION_STATE_DIR", tmp_path)
        adapter = make_adapter()
        adapter._cleanup_session("never-existed")  # must not raise
