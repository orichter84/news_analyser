"""Central configuration – reads from environment variables."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    temperature: float
    max_tokens: int

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            provider=os.environ.get("LLM_PROVIDER", "openai"),
            model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.2")),
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "2048")),
        )


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
        root = Path(__file__).parent.parent.parent
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
            feeds_file=Path(os.environ.get("FEED_FILE", str(root / "feeds.txt"))),
            allowed_topics=topics,
        )
