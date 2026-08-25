"""Unit tests for the JSON extraction and quote-grounding helpers in analyzer.py."""

from news_analyser.agents.analyzer import _extract_json, _validate_quote_grounding


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
