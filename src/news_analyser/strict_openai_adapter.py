"""OpenAI-kompatibler Adapter, der unvollständige Antworten als Fehler behandelt.

`llm_adapter.OpenAIAdapter` loggt bei `finish_reason != "stop"` (z.B. `"length"`,
wenn `max_tokens` erreicht wurde, oder `"content_filter"`) nur eine Warnung und gibt
den abgeschnittenen Text trotzdem zurück. `_extract_json` würde ihn danach per
`json_repair` zu gültigem, aber unvollständigem JSON "reparieren" — fehlende Felder
fielen dann still auf Defaults zurück (orwell_index 0.0, politische_stroemung
["neutral"] …) und das verfälschte Ergebnis würde gespeichert. Siehe
docs/concepts/decisions/0013-reject-incomplete-analyses.md.
"""

from __future__ import annotations

from typing import Any

from llm_adapter import LLMGenerationError, OpenAIAdapter


class StrictOpenAIAdapter(OpenAIAdapter):
    """Wie `OpenAIAdapter`, aber jede nicht regulär beendete Antwort wirft einen Fehler."""

    def _parse_response(self, response: Any) -> str:
        if not response.choices:
            raise LLMGenerationError("OpenAI response enthielt keine choices.")

        choice = response.choices[0]
        if choice.finish_reason not in ("stop", None):
            raise LLMGenerationError(
                f"Antwort unvollständig (finish_reason={choice.finish_reason!r}, "
                f"max_tokens={self._max_tokens})."
            )

        content = choice.message.content
        if not content or not content.strip():
            raise LLMGenerationError("OpenAI response enthielt keinen Text.")

        return content.strip()
