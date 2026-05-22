"""
Article scraper – extracts clean plaintext from a URL.

Primary engine: trafilatura (best recall on news sites).
Fallback:       BeautifulSoup paragraph extraction.
"""

from dataclasses import dataclass
from urllib.parse import urlparse
import datetime

import trafilatura
import requests
from bs4 import BeautifulSoup


@dataclass
class Article:
    url: str
    domain: str
    text: str
    fetched_at: str  # ISO-8601


def _bs4_fallback(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.find_all("p")
    return " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)


def fetch_article(url: str, timeout: int = 15) -> Article | None:
    domain = urlparse(url).netloc.removeprefix("www.")
    fetched_at = datetime.datetime.utcnow().isoformat() + "Z"

    try:
        response = requests.get(url, timeout=timeout, headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; NewsAnalyserBot/1.0; "
                "+https://github.com/local/news_analyser)"
            )
        })
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"[scraper] HTTP error: {exc}")
        return None

    html = response.text

    # trafilatura is the primary extractor
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        no_fallback=False,
    )

    # BeautifulSoup as last resort
    if not text or len(text) < 200:
        text = _bs4_fallback(html)

    if not text or len(text) < 100:
        return None

    return Article(url=url, domain=domain, text=text.strip(), fetched_at=fetched_at)
