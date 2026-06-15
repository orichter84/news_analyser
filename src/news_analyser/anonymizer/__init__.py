"""Anonymizer package — replaces group identifiers with neutral placeholders.

Usage (backwards-compatible):
    from news_analyser.anonymizer import anonymize, AnonymizationResult

Usage (explicit strategy):
    from news_analyser.anonymizer import get_strategy, SpacyStrategy
    strategy = SpacyStrategy()
    result = strategy.anonymize(text, group_terms=[...])
"""
from __future__ import annotations

import os
from functools import cache

from ._result import AnonymizationResult
from .spacy_strategy import SpacyStrategy
from .strategy import AnonymizationStrategy
from ._normalizations import IDEOLOGICAL_TERMS

__all__ = [
    "AnonymizationResult",
    "AnonymizationStrategy",
    "SpacyStrategy",
    "IDEOLOGICAL_TERMS",
    "get_strategy",
    "anonymize",
]

_REGISTRY: dict[str, type[AnonymizationStrategy]] = {
    "spacy": SpacyStrategy,  # type: ignore[type-abstract]
}


def get_strategy(name: str | None = None) -> AnonymizationStrategy:
    """Return an anonymization strategy by name.

    Falls back to the ``ANONYMIZER_STRATEGY`` environment variable, then
    ``"spacy"`` as the default.
    """
    key = (name or os.environ.get("ANONYMIZER_STRATEGY", "spacy")).lower()
    cls = _REGISTRY.get(key)
    if cls is None:
        raise ValueError(
            f"Unknown anonymization strategy: {key!r}. "
            f"Available: {sorted(_REGISTRY)}"
        )
    return cls()


@cache
def _default_strategy() -> AnonymizationStrategy:
    return get_strategy()


def anonymize(
    text: str,
    group_terms: list[dict[str, str]] | None = None,
) -> AnonymizationResult:
    """Convenience wrapper using the default strategy (backwards-compatible)."""
    return _default_strategy().anonymize(text, group_terms)
