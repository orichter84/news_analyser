"""
Article scraper – extracts clean plaintext and metadata from a URL.

Primary engine: trafilatura (best recall on news sites).
Fallback:       BeautifulSoup paragraph extraction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse
import datetime

import trafilatura
import requests
from bs4 import BeautifulSoup


PAYWALL_MIN_WORDS = 150  # Fallback: Wortanzahl-Schwelle

# HTML-Marker die auf eine Paywall hinweisen (CSS-Klassen, IDs, Script-Domains)
_PAYWALL_CLASS_FRAGMENTS = [
    "paywall", "piano", "paid-content", "premium-content",
    "subscriber-only", "subscription-wall", "content-wall",
    "tp-modal", "tp-container",        # Piano/TinyPass
    "spplus", "sp-paywall",            # Spiegel+
    "z-paywall", "zp-paywall",         # Zeit+
    "faz-paywall", "faz-premium",      # FAZ+
    "hb-paywall",                      # Handelsblatt
    "c-paywall", "c-piano",            # Focus / Burda
]

# Script-URLs: wenn diese geladen werden, ist Piano aktiv
_PAYWALL_SCRIPT_DOMAINS = [
    "cdn.tinypass.com",
    "experience.tinypass.com",
    "sandbox.tinypass.com",
    "a.piano.io",
    "buy.piano.io",
]

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
    is_paywall: bool = False


def _detect_paywall_markers(html: str) -> bool:
    """True wenn bekannte Paywall-Marker im HTML gefunden werden."""
    soup = BeautifulSoup(html, "html.parser")

    # Klassen / IDs aller Elemente prüfen
    for tag in soup.find_all(True):
        for attr in ("class", "id"):
            values = tag.get(attr, [])
            if isinstance(values, str):
                values = [values]
            combined = " ".join(values).lower()
            if any(marker in combined for marker in _PAYWALL_CLASS_FRAGMENTS):
                return True

    # Piano-Script-Tags prüfen
    for script in soup.find_all("script", src=True):
        src = script.get("src", "").lower()
        if any(domain in src for domain in _PAYWALL_SCRIPT_DOMAINS):
            return True

    # <tp:contentwall> — Piano custom element
    if soup.find("tp:contentwall"):
        return True

    return False


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
    words = len(text.split())
    is_paywall = _detect_paywall_markers(html) or words < PAYWALL_MIN_WORDS

    return Article(
        url=url,
        domain=domain,
        text=text,
        fetched_at=fetched_at,
        title=title,
        author=author,
        published_at=published_at,
        word_count=words,
        is_paywall=is_paywall,
    )
