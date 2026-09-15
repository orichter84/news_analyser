"""Unit tests for the JSON extraction and quote-grounding helpers in analyzer.py."""

from news_analyser.agents.analyzer import (
    _dedupe_techniques,
    _extract_json,
    _validate_quote_grounding,
    _validate_stroemung_grounding,
)


class TestExtractJson:
    def test_plain_json_object(self):
        assert _extract_json('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}

    def test_strips_markdown_code_fence(self):
        raw = '```json\n{"a": 1}\n```'
        assert _extract_json(raw) == {"a": 1}

    def test_strips_thinking_tokens(self):
        raw = '<think>hmm let me consider</think>{"a": 1}'
        assert _extract_json(raw) == {"a": 1}

    def test_array_wrapped_result_takes_first_element(self):
        assert _extract_json('[{"a": 1}, {"a": 2}]') == {"a": 1}

    def test_empty_array_returns_none(self):
        assert _extract_json("[]") is None

    def test_malformed_json_is_repaired(self):
        # trailing comma — invalid JSON, but json_repair should fix it
        raw = '{"a": 1, "b": 2,}'
        assert _extract_json(raw) == {"a": 1, "b": 2}

    def test_unparseable_garbage_returns_none(self):
        assert _extract_json("this is not json at all, just prose.") is None

    def test_non_dict_non_list_result_returns_none(self):
        assert _extract_json("42") is None


class TestValidateQuoteGrounding:
    def test_keeps_quote_present_in_source(self):
        techniques = [{"technique": "x", "quote": "hello world"}]
        result = _validate_quote_grounding(techniques, "say hello world to everyone")
        assert result == techniques

    def test_drops_quote_not_in_source(self):
        techniques = [{"technique": "x", "quote": "never said this"}]
        result = _validate_quote_grounding(techniques, "completely different text")
        assert result == []

    def test_drops_empty_quote(self):
        techniques = [{"technique": "x", "quote": "  "}]
        result = _validate_quote_grounding(techniques, "some source text")
        assert result == []

    def test_drops_inflated_occurrence_count(self):
        # "hi" only occurs once in the source, but is claimed twice
        techniques = [
            {"technique": "x", "quote": "hi"},
            {"technique": "x", "quote": "hi"},
        ]
        result = _validate_quote_grounding(techniques, "hi there")
        assert len(result) == 1

    def test_keeps_quote_matching_actual_occurrence_count(self):
        techniques = [
            {"technique": "x", "quote": "hi"},
            {"technique": "x", "quote": "hi"},
        ]
        result = _validate_quote_grounding(techniques, "hi there, hi again")
        assert len(result) == 2


class TestDedupeTechniques:
    def test_removes_exact_duplicate_after_normalization(self):
        # two different raw labels that both normalized to the same canonical
        # technique, over the same quote
        techniques = [
            {"technique": "Emotional Manipulation", "quote": "katastrophale Folgen"},
            {"technique": "Emotional Manipulation", "quote": "katastrophale Folgen"},
        ]
        result = _dedupe_techniques(techniques)
        assert len(result) == 1

    def test_keeps_same_technique_different_quotes(self):
        techniques = [
            {"technique": "Emotional Manipulation", "quote": "erste Stelle"},
            {"technique": "Emotional Manipulation", "quote": "zweite Stelle"},
        ]
        result = _dedupe_techniques(techniques)
        assert result == techniques

    def test_keeps_different_technique_same_quote(self):
        # same passage, genuinely reported once per distinct technique — not a duplicate
        techniques = [
            {"technique": "Scapegoating", "quote": "gemeinsame Stelle"},
            {"technique": "Loaded Language", "quote": "gemeinsame Stelle"},
        ]
        result = _dedupe_techniques(techniques)
        assert result == techniques


class TestValidateStroemungGrounding:
    def test_keeps_quote_present_in_source(self):
        stroemung = [{"label": "konservativ", "quote": "Wir müssen jetzt handeln."}]
        result = _validate_stroemung_grounding(stroemung, "Der Autor schreibt: Wir müssen jetzt handeln.")
        assert result == stroemung
        assert result[0]["label"] == "konservativ"

    def test_nulls_unverifiable_quote_but_keeps_label(self):
        stroemung = [{"label": "grün", "quote": "Dieser Satz steht nirgends im Text."}]
        result = _validate_stroemung_grounding(stroemung, "Ein völlig anderer Artikeltext.")
        assert result == [{"label": "grün", "quote": None}]

    def test_passes_through_plain_string_entries(self):
        result = _validate_stroemung_grounding(["neutral"], "irgendein Text")
        assert result == ["neutral"]

    def test_passes_through_neutral_with_null_quote(self):
        stroemung = [{"label": "neutral", "quote": None}]
        result = _validate_stroemung_grounding(stroemung, "irgendein Text")
        assert result == stroemung
