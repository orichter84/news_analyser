"""
CLIConnector — ruft den Claude Code CLI als Subprocess auf.

Voraussetzung: `claude` muss im PATH verfügbar sein und authentifiziert sein.
Hinweis: temperature und max_tokens werden vom CLI nicht unterstützt und ignoriert.
"""

import json
import subprocess
from typing import Any, Dict

from .base import LLMConnector


class CLIConnector(LLMConnector):
    """Connector der den lokalen `claude`-CLI per Subprocess aufruft."""

    @property
    def name(self) -> str:
        return "cli"

    def generate(
        self,
        system_prompt: str,
        input_data: Dict[str, Any],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        user_content = json.dumps(input_data, ensure_ascii=False, indent=2)

        cmd = [
            "claude", "-p",
            "--no-session-persistence",  # keine History-Einträge
            "--system-prompt", system_prompt,
            "--model", model,
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
