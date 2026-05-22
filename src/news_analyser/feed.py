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
from .db_storage import is_known_url
from .main import run


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


def _fetch_new_urls(feed_urls: list[str], max_articles: int) -> Generator[str, None, None]:
    """Yield Artikel-URLs aus allen Feeds, die noch nicht in der DB sind."""
    seen = 0
    for feed_url in feed_urls:
        parsed = feedparser.parse(feed_url)
        if parsed.bozo:
            print(f"[feed] Warnung: Feed nicht lesbar: {feed_url}")
            continue
        for entry in parsed.entries:
            if seen >= max_articles:
                return
            url = entry.get("link", "")
            if not url:
                continue
            if is_known_url(url):
                continue
            seen += 1
            yield url


def run_once(cfg: FeedConfig) -> None:
    feed_urls = _load_feed_urls(cfg.feeds_file)
    print(f"[feed] {len(feed_urls)} Feed(s) geladen, max. {cfg.max_articles} neue Artikel.")

    new_urls = list(_fetch_new_urls(feed_urls, cfg.max_articles))
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
