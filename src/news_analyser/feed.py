"""
RSS-Feed-Collector.

Liest Feed-URLs aus feeds.txt, ruft neue Artikel ab und schleust sie
in die Analyse-Pipeline. Unterstützt manuellen Einzel-Lauf und
automatischen Intervall-Betrieb.
"""

import time
import datetime
from pathlib import Path
from typing import Generator

import feedparser

from .config import FeedConfig
from .repositories.db_storage import is_known_url
from .main import run
from .topic_filter import is_relevant


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
            print(f"[feed] Warnung: Feed nicht lesbar: {feed_url}")
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
                print(f"[feed] Thema '{topic or 'unbekannt'}' gefiltert: {title[:60]}")
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


def run_once(cfg: FeedConfig) -> None:
    feed_urls = _load_feed_urls(cfg.feeds_file)
    print(f"[feed] {len(feed_urls)} Feed(s) geladen, max. {cfg.max_articles} neue Artikel.")

    if cfg.allowed_topics:
        print(f"[feed] Themenfilter aktiv: {', '.join(sorted(cfg.allowed_topics))}")
    else:
        print("[feed] Themenfilter deaktiviert (FEED_TOPICS=all) — alle Artikel werden analysiert.")
    new_urls = list(_fetch_new_urls(feed_urls, cfg.max_articles, cfg.allowed_topics))
    if not new_urls:
        print("[feed] Keine neuen Artikel gefunden.")
        return

    print(f"[feed] {len(new_urls)} neue Artikel werden analysiert …")
    for url in new_urls:
        run(url)


def run_auto(cfg: FeedConfig) -> None:
    print(
        f"[feed] Auto-Modus gestartet – Intervall: {cfg.interval}s "
        f"({cfg.interval // 60} min). Abbrechen mit Ctrl+C."
    )
    while True:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[feed] Lauf um {now}")
        try:
            run_once(cfg)
        except Exception as exc:
            print(f"[feed] Fehler im Lauf: {exc}")
        print(f"[feed] Nächster Lauf in {cfg.interval}s …")
        time.sleep(cfg.interval)


def start(cfg: FeedConfig | None = None) -> None:
    cfg = cfg or FeedConfig.from_env()
    if cfg.mode == "auto":
        run_auto(cfg)
    else:
        run_once(cfg)
