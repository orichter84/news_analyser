"""Unit tests for scraper.py — paywall detection, title fallback, HTTP-error
handling. Network calls (requests.get) and trafilatura extraction are mocked
so these tests are deterministic and don't hit the network."""

import requests

from news_analyser import scraper
from news_analyser.scraper import (
    Article,
    _bs4_fallback,
    _detect_paywall_markers,
    _extract_title,
    fetch_article,
)


class _FakeResponse:
    def __init__(self, text: str, status: int = 200):
        self.text = text
        self._status = status

    def raise_for_status(self):
        if self._status >= 400:
            raise requests.HTTPError(f"HTTP {self._status}")


class _FakeDoc:
    def __init__(self, text, title=None, author=None, date=None):
        self.text = text
        self.title = title
        self.author = author
        self.date = date


class TestDetectPaywallMarkers:
    def test_true_for_known_paywall_class(self):
        html = '<html><body><div class="tp-modal">Abo abschließen</div></body></html>'
        assert _detect_paywall_markers(html) is True

    def test_true_for_paywall_script_domain(self):
        html = '<html><head><script src="https://cdn.tinypass.com/api.js"></script></head></html>'
        assert _detect_paywall_markers(html) is True

    def test_false_for_plain_article(self):
        html = '<html><body><p>Ganz normaler Artikeltext ohne Paywall.</p></body></html>'
        assert _detect_paywall_markers(html) is False

    def test_piano_tracking_container_without_paywall_is_not_flagged(self):
        # "piano" alone (Piano Analytics tracking, not a Piano/TinyPass paywall)
        # must not trigger a false positive — see the comment in scraper.py.
        html = '<html><body><div class="js-at-internet-piano-container"></div></body></html>'
        assert _detect_paywall_markers(html) is False


class TestExtractTitle:
    def test_prefers_og_title(self):
        html = (
            '<html><head><meta property="og:title" content="OG Titel">'
            '<title>Tag Titel</title></head><body><h1>H1 Titel</h1></body></html>'
        )
        assert _extract_title(html) == "OG Titel"

    def test_falls_back_to_h1_without_og_title(self):
        html = "<html><body><h1>H1 Titel</h1></body></html>"
        assert _extract_title(html) == "H1 Titel"

    def test_falls_back_to_title_tag_without_h1(self):
        html = "<html><head><title>Tag Titel</title></head><body></body></html>"
        assert _extract_title(html) == "Tag Titel"

    def test_none_when_nothing_present(self):
        html = "<html><body><p>kein Titel hier</p></body></html>"
        assert _extract_title(html) is None


class TestBs4Fallback:
    def test_joins_paragraph_text(self):
        html = "<html><body><p>Erster Satz.</p><p>Zweiter Satz.</p></body></html>"
        assert _bs4_fallback(html) == "Erster Satz. Zweiter Satz."


class TestFetchArticle:
    def test_returns_none_on_http_error(self, monkeypatch):
        def fake_get(*args, **kwargs):
            raise requests.RequestException("boom")

        monkeypatch.setattr(scraper.requests, "get", fake_get)
        assert fetch_article("https://example.com/article") is None

    def test_returns_none_when_no_usable_text_found(self, monkeypatch):
        monkeypatch.setattr(
            scraper.requests, "get", lambda *a, **k: _FakeResponse("<html><body></body></html>")
        )
        monkeypatch.setattr(scraper.trafilatura, "bare_extraction", lambda *a, **k: None)
        assert fetch_article("https://example.com/article") is None

    def test_successful_extraction_returns_populated_article(self, monkeypatch):
        long_text = " ".join(["Wort"] * 200)  # > PAYWALL_MIN_WORDS, no paywall markers
        html = "<html><head><title>Fallback Titel</title></head><body></body></html>"

        monkeypatch.setattr(scraper.requests, "get", lambda *a, **k: _FakeResponse(html))
        monkeypatch.setattr(
            scraper.trafilatura,
            "bare_extraction",
            lambda *a, **k: _FakeDoc(
                text=long_text, title="Trafilatura Titel", author="Jane Doe", date="2026-08-20"
            ),
        )

        article = fetch_article("https://example.com/article")

        assert isinstance(article, Article)
        assert article.text == long_text
        assert article.title == "Trafilatura Titel"
        assert article.author == "Jane Doe"
        assert article.published_at == "2026-08-20"
        assert article.word_count == 200
        assert article.is_paywall is False

    def test_paywall_flagged_via_word_count_fallback(self, monkeypatch):
        # Long enough to pass the >=100-char extraction cutoff, but under the
        # 150-word PAYWALL_MIN_WORDS threshold.
        short_text = " ".join(["Wort"] * 120)
        html = "<html><body></body></html>"

        monkeypatch.setattr(scraper.requests, "get", lambda *a, **k: _FakeResponse(html))
        monkeypatch.setattr(
            scraper.trafilatura, "bare_extraction", lambda *a, **k: _FakeDoc(text=short_text)
        )

        article = fetch_article("https://example.com/article")

        assert article is not None
        assert article.is_paywall is True
