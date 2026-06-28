"""
CLIAdapter — ruft den Claude Code CLI als Subprocess auf.

Voraussetzung: `claude` muss im PATH verfügbar und authentifiziert sein.
Hinweis: temperature und max_tokens werden vom CLI nicht unterstützt und ignoriert.

Config keys (passed to initialize):
    model — Modellname, wird per --model an die CLI übergeben
            (default: "claude-opus-4-5")

ENV fallbacks (wenn nicht im config dict):
    LLM_MODEL    — provider-agnostischer Modellname (bevorzugt)
    OPENAI_MODEL — Legacy-Alias (backward compat)
"""

import json
import subprocess
from typing import Any, Dict

from .base import LLMAdapter


class CLIAdapter(LLMAdapter):
    """Adapter der den lokalen `claude`-CLI per Subprocess aufruft."""

    _DEFAULTS: dict = {
        "model": "claude-opus-4-5",
    }

    @property
    def name(self) -> str:
        return "cli"

    @property
    def model(self) -> str:
        return self._model

    def initialize(self, config: dict) -> None:
        # ---- Schritt 1: Nicht-sicherheitskritische Konfiguration ----
        import os
        model = config.get("model")
        if not model:
            model = os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_MODEL")
        self._model: str = model or self._DEFAULTS["model"]
        self._cli_path: str = os.environ.get("CLAUDE_CLI_PATH", "claude")

        # Kein Schritt 2: Der CLI authentifiziert sich eigenständig.

    def generate(
        self,
        system_prompt: str,
        input_data: Dict[str, Any],
    ) -> str:
        user_content = json.dumps(input_data, ensure_ascii=False, indent=2)

        cmd = [
            self._cli_path, "-p",
            "--no-session-persistence",  # keine History-Einträge
            "--system-prompt", system_prompt,
            "--model", self._model,
            "--tools", "",               # alle Tools deaktivieren – nur Text-Output
        ]

        try:
            result = subprocess.run(
                cmd,
                input=user_content,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=180,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "`claude` CLI nicht gefunden. Stelle sicher, dass Claude Code installiert "
                "und im PATH verfügbar ist."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Claude CLI hat nicht innerhalb von 180 Sekunden geantwortet.")

        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "(keine Ausgabe)"
            raise RuntimeError(f"Claude CLI Fehler (exit {result.returncode}):\n{detail}")

        return result.stdout.strip()
