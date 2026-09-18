"""
CopilotCliAdapter — ruft die GitHub Copilot CLI (`@github/copilot`) als Subprocess auf.

Voraussetzung: `copilot` muss im PATH verfuegbar und authentifiziert sein —
entweder interaktiv (`copilot` starten, dann `/login`) oder headless ueber
eines der Env-Vars `COPILOT_GITHUB_TOKEN`/`GH_TOKEN`/`GITHUB_TOKEN` (Fine-Grained
Personal Access Token; fuer Serverbetrieb der passende Weg, da `/login` einen
Browser-OAuth-Flow braucht).

**Kein Drop-in fuer CLIAdapter** — andere Flags als die Claude-CLI:
- Kein `--system-prompt`-Flag. System-Prompt und Input werden zu einem
  einzigen `-p`-Argument zusammengefuegt (getestet: Copilot CLI liest den
  Prompt nicht von stdin, anders als `claude -p`).
- Tool-Zugriff wird ueber `--available-tools` ganz ohne Argument gesperrt
  (deaktiviert laut CLI-Doku alle Tools) statt ueber `--tools ""` wie bei
  Claude. Notwendig, weil die Pipeline ungeprueften, gescrapten Artikeltext
  als Modell-Input schickt — Copilot CLI ist ein vollwertiger Coding-Agent
  mit Shell-/Datei-/URL-Zugriff, kein reines Completion-Modell wie Claude im
  `-p`-Modus mit `--tools ""`.

**Session-Cleanup:** jeder Call schreibt ohne erkennbares Abschalt-Flag
persistenten State nach `~/.copilot/session-state/<uuid>/` (~64 KB/Call —
geprueft) plus Zeilen in `~/.copilot/session-store.db`. Der Adapter erzeugt
daher selbst eine UUID, uebergibt sie explizit per `--session-id`, und loescht
nach dem Call genau dieses Verzeichnis wieder (`shutil.rmtree`) — nie andere
Sessions, da die ID vorher bekannt und eindeutig ist. Die SQLite-Zeilen selbst
bleiben (kein Cleanup-Kommando in der CLI gefunden), sind aber klein im
Vergleich zum Verzeichnisinhalt (Events, Workspace-Snapshot, Checkpoints).

stdout wird — wie bei `cli_adapter.py` — in eine Temp-Datei geschrieben statt
per Pipe gelesen, als Vorsichtsmassnahme gegen dasselbe fd-Inheritance-Problem
(github.com/anthropics/claude-code/issues/28407), falls dieser Adapter selbst
innerhalb eines laufenden Claude-Code-Prozesses aufgerufen wird.

Config keys (passed to initialize):
    model   — Modellname, wird per --model an die CLI uebergeben (default: "gemini-3.8-flash";
              verfuegbare IDs haengen vom Copilot-Abo ab, siehe `copilot --model <bogus>`
              fuer eine Fehlermeldung oder frag das Modell selbst danach)
    timeout — Sekunden, bevor der Subprocess-Aufruf abgebrochen wird (default: 180)

ENV fallbacks (wenn nicht im config dict):
    LLM_MODEL          — provider-agnostischer Modellname (bevorzugt)
    OPENAI_MODEL        — Legacy-Alias (backward compat)
    COPILOT_CLI_PATH    — Pfad/Name der CLI-Binary (default: "copilot", via PATH aufgeloest)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict

from llm_adapter.base import LLMAdapter, LLMGenerationError, LLMInitializationError

logger = logging.getLogger(__name__)

_SESSION_STATE_DIR = Path.home() / ".copilot" / "session-state"


class CopilotCliAdapter(LLMAdapter):
    """Adapter der die lokale `copilot`-CLI (GitHub Copilot CLI) per Subprocess aufruft."""

    _DEFAULTS: dict = {
        "model": "gemini-3.8-flash",
        "timeout": 180,
    }

    @property
    def name(self) -> str:
        return "copilot_cli"

    @property
    def model(self) -> str:
        return self._model

    def initialize(self, config: dict) -> None:
        model = config.get("model")
        if not model:
            model = os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_MODEL")
        self._model: str = model or self._DEFAULTS["model"]
        self._timeout: int = int(config.get("timeout", self._DEFAULTS["timeout"]))

        cli_name = os.environ.get("COPILOT_CLI_PATH", "copilot")
        resolved_path = shutil.which(cli_name)
        if resolved_path is None:
            raise LLMInitializationError(
                f"`{cli_name}` CLI nicht gefunden. Installieren via "
                "`npm install -g @github/copilot` und authentifizieren "
                "(`copilot` starten, dann `/login`, oder COPILOT_GITHUB_TOKEN/"
                "GH_TOKEN/GITHUB_TOKEN env var fuer headless-Betrieb)."
            )
        self._cli_path = resolved_path

    def _build_cmd(self, prompt: str, session_id: str) -> list[str]:
        return [
            self._cli_path, "-p", prompt,
            "-s",                    # nur die Agent-Antwort, keine Statuszeilen
            "--available-tools",     # ohne Argument -> alle Tools gesperrt, reines LLM
            "--model", self._model,
            "--session-id", session_id,
        ]

    def _cleanup_session(self, session_id: str) -> None:
        try:
            shutil.rmtree(_SESSION_STATE_DIR / session_id, ignore_errors=True)
        except Exception as exc:
            logger.warning("Konnte Copilot-Session-State nicht bereinigen (%s): %s", session_id, exc)

    def _finish(self, returncode: int, stdout_text: str, stderr_text: str) -> str:
        if returncode != 0:
            detail = stderr_text.strip() or stdout_text.strip() or "(keine Ausgabe)"
            raise LLMGenerationError(f"Copilot CLI Fehler (exit {returncode}):\n{detail}")

        stderr_output = stderr_text.strip()
        if stderr_output:
            logger.warning("Copilot CLI stderr (exit 0): %s", stderr_output)

        return stdout_text.strip()

    def generate(
        self,
        system_prompt: str,
        input_data: Dict[str, Any],
    ) -> str:
        user_content = json.dumps(input_data, ensure_ascii=False, indent=2)
        prompt = f"{system_prompt}\n\n{user_content}"
        session_id = str(uuid.uuid4())
        cmd = self._build_cmd(prompt, session_id)

        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        tmp_path = tmp.name
        tmp.close()

        try:
            with open(tmp_path, "w", encoding="utf-8") as out_file:
                try:
                    result = subprocess.run(
                        cmd,
                        stdout=out_file,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding="utf-8",
                        timeout=self._timeout,
                    )
                except FileNotFoundError:
                    raise LLMGenerationError(
                        "`copilot` CLI nicht gefunden. Stelle sicher, dass die GitHub "
                        "Copilot CLI installiert und im PATH verfuegbar ist."
                    )
                except subprocess.TimeoutExpired:
                    raise LLMGenerationError(
                        f"Copilot CLI hat nicht innerhalb von {self._timeout} Sekunden geantwortet."
                    )

            with open(tmp_path, "r", encoding="utf-8") as f:
                stdout_text = f.read()
        finally:
            os.unlink(tmp_path)
            self._cleanup_session(session_id)

        return self._finish(result.returncode, stdout_text, result.stderr)
