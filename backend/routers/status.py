import datetime
import json
import sys
from pathlib import Path

import psutil
from fastapi import APIRouter

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from news_analyser.repositories.chroma_client import get_client

_PID_IDENTITY_TOLERANCE_SECONDS = 5

router = APIRouter(prefix="/status", tags=["status"])

_FEED_STATUS_FILE = Path(__file__).parent.parent.parent / "data" / "feed_status.json"

_FEED_STATUS_DEFAULTS = {
    "pid": None,
    "mode": None,
    "started_at": None,
    "last_run_at": None,
    "last_run_status": None,
    "last_run_articles": None,
    "next_run_at": None,
}


def _process_alive(pid: int | None, started_at: str | None) -> bool:
    """Liveness check that also guards against PID reuse.

    A dead feed process's PID can be handed to an unrelated process by the OS,
    which would make a plain os.kill(pid, 0) probe report a false "running".
    Cross-checking the process's actual creation time against the started_at
    we recorded when the feed wrote the PID rules that out.
    """
    if not pid or not psutil.pid_exists(pid):
        return False
    if not started_at:
        return True  # no recorded start time to cross-check against
    try:
        recorded = datetime.datetime.fromisoformat(started_at)
        actual = datetime.datetime.fromtimestamp(
            psutil.Process(pid).create_time(), tz=datetime.timezone.utc
        )
    except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
        return True
    return abs((actual - recorded).total_seconds()) < _PID_IDENTITY_TOLERANCE_SECONDS


def _chroma_status() -> dict:
    try:
        get_client().heartbeat()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def _feed_status() -> dict:
    feed = dict(_FEED_STATUS_DEFAULTS)
    if _FEED_STATUS_FILE.exists():
        try:
            stored = json.loads(_FEED_STATUS_FILE.read_text(encoding="utf-8"))
            feed.update(stored)
        except (OSError, ValueError):
            pass
    feed["running"] = _process_alive(feed.get("pid"), feed.get("started_at"))
    return feed


@router.get("")
def get_status() -> dict:
    return {
        "backend": {"status": "ok"},
        "chroma": _chroma_status(),
        "feed": _feed_status(),
    }
