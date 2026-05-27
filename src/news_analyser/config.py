"""Central configuration – reads from environment variables.

Note: .env is loaded by the news_analyser package __init__.py — no load_dotenv here.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class LLMConfig:
    provider: str

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(provider=os.environ.get("LLM_PROVIDER", "openai"))


@dataclass(frozen=True)
class FeedConfig:
    mode: str           # "manual" | "auto"
    interval: int       # Sekunden zwischen Runs (nur im auto-Modus)
    max_articles: int   # max. neue Artikel pro Lauf
    feeds_file: Path    # Pfad zur feeds.txt
    allowed_topics: frozenset[str]  # leere Menge = alle Themen analysieren

    @classmethod
    def from_env(cls) -> "FeedConfig":
        from .topic_filter import DEFAULT_ALLOWED_TOPICS
        config_dir = Path(__file__).parent.parent.parent.parent / "config"
        raw = os.environ.get("FEED_TOPICS", "")
        if raw.strip().lower() == "all":
            topics: frozenset[str] = frozenset()
        elif raw.strip():
            topics = frozenset(t.strip().capitalize() for t in raw.split(",") if t.strip())
        else:
            topics = frozenset(DEFAULT_ALLOWED_TOPICS)
        return cls(
            mode=os.environ.get("FEED_MODE", "manual"),
            interval=int(os.environ.get("FEED_INTERVAL", "3600")),
            max_articles=int(os.environ.get("FEED_MAX_ARTICLES", "20")),
            feeds_file=Path(os.environ.get("FEED_FILE", str(config_dir / "feeds.txt"))),
            allowed_topics=topics,
        )
