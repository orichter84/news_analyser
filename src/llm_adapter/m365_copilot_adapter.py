"""
M365CopilotAdapter — calls Microsoft 365 Copilot via Microsoft Graph Copilot Chat API (beta).

Config keys (passed to initialize):
    api_key_env    — ENV var name for the delegated OAuth token
                     (default: "M365_COPILOT_ACCESS_TOKEN")
    country        — country hint for Copilot, e.g. "DE" (default: "DE")
    state          — state/region hint (default: "")
    city           — city hint (default: "")
    web_grounding  — enable Bing web grounding (default: False)

Note: model, temperature, max_tokens are not supported by this adapter.
"""

import json
import os
from typing import Any, Dict, Optional

import requests

from .base import LLMAdapter


class M365CopilotAdapter(LLMAdapter):

    _DEFAULTS: dict = {
        "api_key_env":   "M365_COPILOT_ACCESS_TOKEN",
        "country":       "DE",
        "state":         "",
        "city":          "",
        "web_grounding": False,
    }

    @property
    def name(self) -> str:
        return "m365_copilot"

    @property
    def model(self) -> str:
        return "m365-copilot"

    def initialize(self, config: dict) -> None:
        # ---- Schritt 1: Nicht-sicherheitskritische Konfiguration ----
        api_key_env: str = config.get("api_key_env", self._DEFAULTS["api_key_env"])

        self._location_hint = {
            "countryOrRegion": config.get("country", os.environ.get("M365_COPILOT_COUNTRY", self._DEFAULTS["country"])),
            "state":           config.get("state",   os.environ.get("M365_COPILOT_STATE",   self._DEFAULTS["state"])),
            "city":            config.get("city",    os.environ.get("M365_COPILOT_CITY",    self._DEFAULTS["city"])),
        }

        web_grounding_raw = config.get("web_grounding")
        if web_grounding_raw is None:
            web_grounding_raw = os.environ.get("M365_COPILOT_WEB_GROUNDING", "false")
        self._web_grounding: bool = (
            str(web_grounding_raw).lower() == "true"
            if isinstance(web_grounding_raw, str)
            else bool(web_grounding_raw)
        )

        # ---- Schritt 2: Sicherheitskritische Werte aus ENV ----
        token = os.environ.get(api_key_env)
        if not token:
            raise EnvironmentError(
                f"Umgebungsvariable '{api_key_env}' ist nicht gesetzt. "
                "Bitte einen delegierten Graph-Zugangstoken bereitstellen."
            )

        self._token = token
        self._conversation_id: Optional[str] = None
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._token}",
                "Content-Type":  "application/json",
            }
        )

    def generate(
        self,
        system_prompt: str,
        input_data: Dict[str, Any],
    ) -> str:
        user_json = json.dumps(input_data, ensure_ascii=False, indent=2)
        prompt = f"{system_prompt}\n\nInput:\n{user_json}"

        convo_id = self._ensure_conversation()

        url = f"https://graph.microsoft.com/beta/copilot/conversations/{convo_id}/chat"

        body: Dict[str, Any] = {
            "message":      {"content": prompt},
            "locationHint": self._location_hint,
        }

        if self._web_grounding:
            body["contextualResources"] = {"useWeb": True}

        resp = self._session.post(url, data=json.dumps(body), timeout=120)
        if resp.status_code >= 400:
            raise RuntimeError(f"M365 Copilot Chat API error {resp.status_code}: {resp.text}")

        return self._extract_text(resp.json())

    # ------------------------------------------------------------------

    def _ensure_conversation(self) -> str:
        if self._conversation_id:
            return self._conversation_id

        resp = self._session.post(
            "https://graph.microsoft.com/beta/copilot/conversations",
            data="{}",
            timeout=30,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Create conversation failed {resp.status_code}: {resp.text}")

        convo = resp.json()
        convo_id = convo.get("id")
        if not convo_id:
            raise RuntimeError(f"Create conversation did not return an id: {convo}")

        self._conversation_id = convo_id
        return convo_id

    def _extract_text(self, payload: Dict[str, Any]) -> str:
        msgs = payload.get("messages")
        if isinstance(msgs, list) and msgs:
            for m in reversed(msgs):
                content = m.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
                if isinstance(content, list):
                    texts = [str(b["text"]) for b in content if isinstance(b, dict) and b.get("text")]
                    if texts:
                        return "\n".join(texts).strip()

        for key in ("lastMessage", "response", "result"):
            v = payload.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()

        return json.dumps(payload, ensure_ascii=False)
