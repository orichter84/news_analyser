import pytest

from news_analyser import feed


@pytest.fixture(autouse=True)
def _isolate_feed_state_files(tmp_path, monkeypatch):
    """Redirect every persistent state file feed.py writes into tmp_path.

    Autouse so a newly added state file doesn't silently leak into the real
    data/ directory the way _STATUS_FILE and _ROTATION_FILE each did before
    this fixture existed — they were added after the original per-test-file
    fixture and neither test file remembered to isolate them.
    """
    monkeypatch.setattr(feed, "_QUOTA_COOLDOWN_FILE", tmp_path / "gemini_quota_cooldown.json")
    monkeypatch.setattr(feed, "_STATUS_FILE", tmp_path / "feed_status.json")
    monkeypatch.setattr(feed, "_ROTATION_FILE", tmp_path / "feed_rotation.json")
