"""Unit tests for the shared negation/critical-prefix guard."""

from news_analyser.repositories.negation_guard import is_oppositional


class TestIsOppositional:
    def test_detects_anti_prefix(self):
        assert is_oppositional("antifeministisch")

    def test_detects_kritisch_suffix(self):
        assert is_oppositional("islamkritisch")

    def test_detects_gegner_suffix(self):
        assert is_oppositional("Kapitalismusgegner")

    def test_is_case_insensitive(self):
        assert is_oppositional("ANTI-Appeal to Fear")

    def test_plain_canonical_term_is_not_oppositional(self):
        assert not is_oppositional("feministisch")
        assert not is_oppositional("Appeal to Fear")

    def test_unrelated_term_is_not_oppositional(self):
        assert not is_oppositional("konservativ")
