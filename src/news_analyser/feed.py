"""
RSS-Feed-Collector.

Liest Feed-URLs aus feeds.txt, ruft neue Artikel ab und schleust sie
in die Analyse-Pipeline. Unterstützt manuellen Einzel-Lauf und
automatischen Intervall-Betrieb.
"""

from __future__ import annotations

import json
import time
import datetime
import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Generator

import feedparser

from .config import FeedConfig
from .repositories.db_storage import is_known_url
from .main import run
from .topic_filter import is_relevant
from .agents.errors import GeminiQuotaExceededError

logger = logging.getLogger(__name__)

_GEMINI_QUOTA_COOLDOWN_SECONDS = 24 * 60 * 60
_QUOTA_COOLDOWN_FILE = Path(__file__).resolve().parents[2] / "data" / "gemini_quota_cooldown.json"


def _quota_cooldown_remaining() -> float:
    """Return remaining Gemini quota cooldown seconds, cleaning up expired state."""
    try:
        cooldown_until = float(json.loads(_QUOTA_COOLDOWN_FILE.read_text(encoding="utf-8"))["until"])
    except FileNotFoundError:
        return 0.0
    except (KeyError, TypeError, ValueError):
        logger.warning("Beschädigte Gemini-Cooldown-Datei; starte vorsorglich neue 24-Stunden-Pause.")
        start_quota_cooldown()
        return float(_GEMINI_QUOTA_COOLDOWN_SECONDS)

    remaining = cooldown_until - time.time()
    if remaining <= 0:
        _QUOTA_COOLDOWN_FILE.unlink(missing_ok=True)
        return 0.0
    return remaining


def start_quota_cooldown() -> None:
    """Persist a 24-hour Gemini cooldown atomically."""
    _QUOTA_COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=_QUOTA_COOLDOWN_FILE.parent,
        delete=False,
    ) as temp_file:
        json.dump({"until": time.time() + _GEMINI_QUOTA_COOLDOWN_SECONDS}, temp_file)
        temp_path = temp_file.name
    os.replace(temp_path, _QUOTA_COOLDOWN_FILE)


def _load_feed_urls(feeds_file: Path) -> list[str]:
    if not feeds_file.exists():
        raise FileNotFoundError(
            f"feeds.txt nicht gefunden: {feeds_file}\n"
            "Lege die Datei an und trage eine Feed-URL pro Zeile ein."
        )
    return [
        line.strip()
        for line in feeds_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def _fetch_new_urls(
    feed_urls: list[str],
    max_articles: int,
    allowed_topics: frozenset[str],
) -> Generator[str, None, None]:
    """Yield Artikel-URLs im Round-Robin über alle Feeds, bis max_articles erreicht."""
    # Kandidaten pro Feed sammeln
    candidates: list[list[str]] = []
    for feed_url in feed_urls:
        parsed = feedparser.parse(feed_url)
        if parsed.bozo:
            logger.warning("Feed nicht lesbar: %s", feed_url)
            candidates.append([])
            continue
        feed_candidates: list[str] = []
        for entry in parsed.entries:
            url = entry.get("link", "")
            if not url or is_known_url(url):
                continue
            title   = entry.get("title", "")
            summary = entry.get("summary", "")
            relevant, topic = is_relevant(title, summary, allowed_topics)
            if not relevant:
                logger.debug("Thema '%s' gefiltert: %s", topic or "unbekannt", title[:60])
                continue
            feed_candidates.append(url)
        candidates.append(feed_candidates)

    # Round-Robin: je ein Artikel pro Feed abwechselnd
    seen = 0
    round_idx = 0
    while seen < max_articles:
        any_left = False
        for feed_candidates in candidates:
            if round_idx < len(feed_candidates):
                any_left = True
                yield feed_candidates[round_idx]
                seen += 1
                if seen >= max_articles:
                    return
        if not any_left:
            return
        round_idx += 1


def run_once(cfg: FeedConfig) -> bool:
    """Run one feed cycle and return whether Gemini quota was exhausted."""
    cooldown_remaining = _quota_cooldown_remaining()
    if cooldown_remaining:
        resume_at = datetime.datetime.now() + datetime.timedelta(seconds=cooldown_remaining)
        logger.warning(
            "Feed pausiert wegen erschöpfter Gemini-Quota bis %s.",
            resume_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
        return True

    feed_urls = _load_feed_urls(cfg.feeds_file)
    logger.info("%d Feed(s) geladen, max. %d neue Artikel.", len(feed_urls), cfg.max_articles)

    if cfg.allowed_topics:
        logger.info("Themenfilter aktiv: %s", ", ".join(sorted(cfg.allowed_topics)))
    else:
        logger.info("Themenfilter deaktiviert (FEED_TOPICS=all) — alle Artikel werden analysiert.")
    new_urls = list(_fetch_new_urls(feed_urls, cfg.max_articles, cfg.allowed_topics))
    if not new_urls:
        logger.info("Keine neuen Artikel gefunden.")
        return False

    logger.info("%d neue Artikel werden analysiert …", len(new_urls))
    for url in new_urls:
        try:
            run(url)
        except GeminiQuotaExceededError as exc:
            logger.error("Gemini-Quota erschöpft: %s", exc)
            start_quota_cooldown()
            return True
    return False


def run_auto(cfg: FeedConfig) -> None:
    logger.info(
        "Auto-Modus gestartet – Intervall: %ds (%d min). Abbrechen mit Ctrl+C.",
        cfg.interval, cfg.interval // 60,
    )
    while True:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Lauf um %s", now)
        try:
            quota_exhausted = run_once(cfg)
        except Exception as exc:
            logger.error("Fehler im Lauf: %s", exc)
            quota_exhausted = False
        if quota_exhausted:
            cooldown_remaining = _quota_cooldown_remaining()
            time.sleep(cooldown_remaining)
            continue
        logger.info("Nächster Lauf in %ds …", cfg.interval)
        time.sleep(cfg.interval)


def start(cfg: FeedConfig | None = None) -> None:
    cfg = cfg or FeedConfig.from_env()
    if cfg.mode == "auto":
        run_auto(cfg)
    else:
        run_once(cfg)
