from __future__ import annotations

from abc import ABC, abstractmethod

from ._result import AnonymizationResult


class AnonymizationStrategy(ABC):
    """Pipeline for anonymizing text in four ordered steps.

    Subclasses implement the individual steps; this base class owns the
    orchestration and guarantees the execution order.
    """

    def anonymize(
        self,
        text: str,
        group_terms: list[dict[str, str]] | None = None,
    ) -> AnonymizationResult:
        text, norm_mapping    = self.normalize(text)
        text, ner_mapping     = self.ner(text)
        text, group_mapping   = self.replace_groups(text, group_terms)
        text                  = self.correct(text)
        return AnonymizationResult(
            text=text,
            mapping={**norm_mapping, **ner_mapping, **group_mapping},
        )

    @abstractmethod
    def normalize(self, text: str) -> tuple[str, dict[str, str]]:
        """Replace ideologically loaded terms with neutral equivalents.

        No placeholders — plain text in, plain text out.
        """

    @abstractmethod
    def ner(self, text: str) -> tuple[str, dict[str, str]]:
        """Detect named entities and replace with typed placeholders.

        Person-X, Org-X, Geo-X — no group handling.
        """

    @abstractmethod
    def replace_groups(
        self,
        text: str,
        group_terms: list[dict[str, str]] | None = None,
    ) -> tuple[str, dict[str, str]]:
        """Replace group identifiers with Gruppe-X placeholders.

        No NER, no grammar — groups only.
        """

    def correct(self, text: str) -> str:
        """Fix grammatical errors introduced by earlier replacements.

        Default: no-op. Override to add article/pronoun corrections.
        """
        return text
