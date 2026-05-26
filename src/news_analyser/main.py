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
from pathlib import Path

from .scraper import Article, fetch_article
from .analyzer import analyze_article
from .db_storage import store_result
from .stats import print_report


def run(url: str) -> None:
    print(f"[*] Fetching: {url}")
    article = fetch_article(url)
    if not article:
        print(f"[!] Could not extract text from {url}")
        return

    if article.is_paywall:
        print(f"[~] Paywall erkannt ({article.word_count} Wörter) – übersprungen: {url}")
        return

    print(f"[*] Analyzing ({len(article.text)} chars) …")
    result = analyze_article(article)
    if not result:
        print("[!] Analysis failed – no JSON returned.")
        return

    store_result(article.text, result)
    ft = result["framing_target"]
    techniques = result["detected_techniques"]
    word_count = result.get("word_count", 0)
    bernays = round(len(techniques) / word_count * 1000, 2) if word_count > 0 else 0.0
    dk = ft.get("dunning_kruger_index", 0.0)
    stroemung = result.get("politische_stroemung", ["neutral"])
    print(f"[+] Stored. Orwell-Index: {ft['orwell_index']:.2f}  |  Bernays Score: {bernays:.2f}/1000w  |  DK-Index: {dk:.2f}")
    print(f"    Stroemung: {stroemung}")
    print(f"    Techniken: {[t['technique'] for t in techniques]}")


def run_text_file(path: str, domain: str, source_url: str) -> None:
    text = Path(path).read_text(encoding="utf-8").strip()
    if len(text) < 100:
        print(f"[!] Text zu kurz für eine Analyse ({len(text)} Zeichen).")
        return

    fetched_at = datetime.datetime.utcnow().isoformat() + "Z"
    article = Article(
        url=source_url,
        domain=domain,
        text=text,
        fetched_at=fetched_at,
        word_count=len(text.split()),
    )

    print(f"[*] Analyzing text file '{path}' ({len(text)} chars, {article.word_count} Wörter) …")
    result = analyze_article(article)
    if not result:
        print("[!] Analysis failed – no JSON returned.")
        return

    store_result(article.text, result)
    ft = result["framing_target"]
    techniques = result["detected_techniques"]
    word_count = result.get("word_count", 0)
    bernays = round(len(techniques) / word_count * 1000, 2) if word_count > 0 else 0.0
    dk = ft.get("dunning_kruger_index", 0.0)
    stroemung = result.get("politische_stroemung", ["neutral"])
    print(f"[+] Stored. Orwell-Index: {ft['orwell_index']:.2f}  |  Bernays Score: {bernays:.2f}/1000w  |  DK-Index: {dk:.2f}")
    print(f"    Stroemung: {stroemung}")
    print(f"    Techniken: {[t['technique'] for t in techniques]}")


def main() -> None:
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
        run(args.url)

    elif args.file:
        with open(args.file, encoding="utf-8") as fh:
            urls = [line.strip() for line in fh if line.strip()]
        for url in urls:
            run(url)

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
