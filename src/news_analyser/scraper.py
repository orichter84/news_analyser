"""
Article scraper – extracts clean plaintext and metadata from a URL.

Primary engine: trafilatura (best recall on news sites).
Fallback:       BeautifulSoup paragraph extraction.
"""

from dataclasses import dataclass, field
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
    fetched_at: str           # ISO-8601 Abrufzeitpunkt
    title: str | None = None
    author: str | None = None
    published_at: str | None = None  # ISO-8601 Publikationsdatum laut Artikel
    word_count: int = 0


def _bs4_fallback(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.find_all("p")
    return " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)


def _extract_title(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    og = soup.find("meta", property="og:title")
    if og:
        content = og.get("content")
        if content:
            return str(content).strip()
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    tag = soup.find("title")
    if tag:
        return tag.get_text(strip=True)
    return None


def fetch_article(url: str, timeout: int = 15) -> Article | None:
    domain = urlparse(url).netloc.removeprefix("www.")
    fetched_at = datetime.datetime.utcnow().isoformat() + "Z"

    try:
        response = requests.get(url, timeout=timeout, headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; NewsAnalyserBot/1.0; "
                "+https://github.com/orichter84/news_analyser)"
            )
        })
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"[scraper] HTTP error: {exc}")
        return None

    html = response.text

    # trafilatura bare_extraction liefert Text + Metadaten in einem Schritt
    doc = trafilatura.bare_extraction(
        html,
        include_comments=False,
        include_tables=False,
        favor_recall=True,
    )

    text       = getattr(doc, "text",   None) if doc else None
    title      = getattr(doc, "title",  None) if doc else None
    author     = getattr(doc, "author", None) if doc else None
    published_at = getattr(doc, "date", None) if doc else None

    # Titel-Fallback: og:title → h1 → <title>
    if not title:
        title = _extract_title(html)

    # BeautifulSoup als letzter Ausweg für den Text
    if not text or len(text) < 200:
        text = _bs4_fallback(html)

    if not text or len(text) < 100:
        return None

    text = text.strip()

    return Article(
        url=url,
        domain=domain,
        text=text,
        fetched_at=fetched_at,
        title=title,
        author=author,
        published_at=published_at,
        word_count=len(text.split()),
    )
