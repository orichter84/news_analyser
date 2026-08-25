"""
news_analyser – Entry point.

Usage:
    python run.py --url https://example.com/article
    python run.py --file urls.txt              # eine URL pro Zeile
    python run.py --stats                      # Statistik-Report
    python run.py --stats --top 10
    python run.py --feed                       # einmaliger Feed-Lauf (manuell)
    python run.py --feed --auto                # Dauerbetrieb (FEED_INTERVAL Sekunden)
    python run.py --feed --interval 1800       # Dauerbetrieb, alle 30 Min
"""

import argparse
import datetime
import logging
from pathlib import Path

from .logging_config import setup_logging
from .scraper import Article, fetch_article
from .agents import analyze_article
from .agents.errors import GeminiQuotaExceededError
from .repositories.db_storage import store_result
from .stats import print_report

logger = logging.getLogger(__name__)


def run(url: str) -> None:
    logger.info("Fetching: %s", url)
    article = fetch_article(url)
    if not article:
        logger.warning("Could not extract text from %s", url)
        return

    if article.is_paywall:
        logger.info("Paywall erkannt (%d Wörter) – übersprungen: %s", article.word_count, url)
        return

    logger.info("Analyzing (%d chars) …", len(article.text))
    result = analyze_article(article)
    if not result:
        logger.warning("Analysis failed – no JSON returned.")
        return

    store_result(article.text, result, url=article.url)
    ft = result["framing_target"]
    techniques = result["detected_techniques"]
    word_count = result.get("word_count", 0)
    bernays = round(len(techniques) / word_count * 1000, 2) if word_count > 0 else 0.0
    dk = ft.get("dunning_kruger_index", 0.0)
    stroemung = result.get("politische_stroemung", ["neutral"])
    logger.info(
        "Stored. Orwell-Index: %.2f  |  Bernays Score: %.2f/1000w  |  DK-Index: %.2f",
        ft["orwell_index"], bernays, dk,
    )
    logger.info("Stroemung: %s", stroemung)
    logger.info("Techniken: %s", [t["technique"] for t in techniques])


def run_text_file(path: str, domain: str, source_url: str) -> None:
    text = Path(path).read_text(encoding="utf-8").strip()
    if len(text) < 100:
        logger.warning("Text zu kurz für eine Analyse (%d Zeichen).", len(text))
        return

    fetched_at = datetime.datetime.utcnow().isoformat() + "Z"
    article = Article(
        url=source_url,
        domain=domain,
        text=text,
        fetched_at=fetched_at,
        word_count=len(text.split()),
    )

    logger.info(
        "Analyzing text file '%s' (%d chars, %d Wörter) …",
        path, len(text), article.word_count,
    )
    result = analyze_article(article)
    if not result:
        logger.warning("Analysis failed – no JSON returned.")
        return

    store_result(article.text, result, url=article.url)
    ft = result["framing_target"]
    techniques = result["detected_techniques"]
    word_count = result.get("word_count", 0)
    bernays = round(len(techniques) / word_count * 1000, 2) if word_count > 0 else 0.0
    dk = ft.get("dunning_kruger_index", 0.0)
    stroemung = result.get("politische_stroemung", ["neutral"])
    logger.info(
        "Stored. Orwell-Index: %.2f  |  Bernays Score: %.2f/1000w  |  DK-Index: %.2f",
        ft["orwell_index"], bernays, dk,
    )
    logger.info("Stroemung: %s", stroemung)
    logger.info("Techniken: %s", [t["technique"] for t in techniques])


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description="Media manipulation analyser")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Einzelne Artikel-URL analysieren")
    group.add_argument("--file", help="Textdatei mit einer URL pro Zeile")
    group.add_argument("--text-file", dest="text_file", metavar="PATH",
                       help="Rohtextdatei direkt analysieren (ohne Scraper)")
    group.add_argument("--stats", action="store_true", help="Statistik-Report ausgeben")
    group.add_argument("--feed", action="store_true", help="RSS-Feeds abrufen und analysieren")

    parser.add_argument("--top", type=int, default=5, help="Top-N für Statistiken (default: 5)")
    parser.add_argument("--auto", action="store_true", help="Feed im Dauerbetrieb (auto-Modus)")
    parser.add_argument("--interval", type=int, help="Intervall in Sekunden für --auto (überschreibt FEED_INTERVAL)")
    parser.add_argument("--domain", default="local",
                        help="Domain-Label für --text-file (default: local)")
    parser.add_argument("--source-url", dest="source_url", default=None,
                        help="URL-Label für --text-file (default: local://<dateiname>)")

    args = parser.parse_args()

    if args.stats:
        print_report(n=args.top)

    elif args.text_file:
        source_url = args.source_url or f"local://{Path(args.text_file).name}"
        run_text_file(args.text_file, domain=args.domain, source_url=source_url)

    elif args.url:
        try:
            run(args.url)
        except GeminiQuotaExceededError as exc:
            from .feed import start_quota_cooldown
            start_quota_cooldown()
            logger.error("Gemini-Quota erschöpft: %s", exc)

    elif args.file:
        with open(args.file, encoding="utf-8") as fh:
            urls = [line.strip() for line in fh if line.strip()]
        for url in urls:
            try:
                run(url)
            except GeminiQuotaExceededError as exc:
                from .feed import start_quota_cooldown
                start_quota_cooldown()
                logger.error("Gemini-Quota erschöpft: %s", exc)
                break

    elif args.feed:
        from .config import FeedConfig
        from .feed import start
        cfg = FeedConfig.from_env()
        if args.interval:
            cfg = FeedConfig(
                mode="auto" if (args.auto or args.interval) else cfg.mode,
                interval=args.interval,
                max_articles=cfg.max_articles,
                feeds_file=cfg.feeds_file,
                allowed_topics=cfg.allowed_topics,
            )
        elif args.auto:
            cfg = FeedConfig(
                mode="auto",
                interval=cfg.interval,
                max_articles=cfg.max_articles,
                feeds_file=cfg.feeds_file,
                allowed_topics=cfg.allowed_topics,
            )
        start(cfg)


if __name__ == "__main__":
    main()
