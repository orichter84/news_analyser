"""
M365CopilotConnector — calls Microsoft 365 Copilot via Microsoft Graph Copilot Chat API (beta).

- Uses delegated OAuth access token (Bearer) from env var: M365_COPILOT_ACCESS_TOKEN
- Creates a copilotConversation once and reuses it for subsequent calls (multi-turn).
- Ignores model/temperature/max_tokens as requested.
"""

import json
import os
from typing import Any, Dict, Optional

import requests

from .base import LLMConnector


class M365CopilotConnector(LLMConnector):
    @property
    def name(self) -> str:
        return "m365_copilot"

    def __init__(self) -> None:
        token = os.environ.get("M365_COPILOT_ACCESS_TOKEN")
        if not token:
            raise EnvironmentError(
                "M365_COPILOT_ACCESS_TOKEN not set. Provide a delegated Graph access token."
            )

        self._token = token
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            }
        )

        self._conversation_id: Optional[str] = None

        self._location_hint = {
            "countryOrRegion": os.environ.get("M365_COPILOT_COUNTRY", "DE"),
            "state": os.environ.get("M365_COPILOT_STATE", ""),
            "city": os.environ.get("M365_COPILOT_CITY", ""),
        }

        self._web_grounding = os.environ.get("M365_COPILOT_WEB_GROUNDING", "false").lower() == "true"

    def generate(
        self,
        system_prompt: str,
        input_data: Dict[str, Any],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        user_json = json.dumps(input_data, ensure_ascii=False, indent=2)
        prompt = f"{system_prompt}\n\nInput:\n{user_json}"

        convo_id = self._ensure_conversation()

        url = f"https://graph.microsoft.com/beta/copilot/conversations/{convo_id}/chat"

        body: Dict[str, Any] = {
            "message": {"content": prompt},
            "locationHint": self._location_hint,
        }

        if self._web_grounding:
            body["contextualResources"] = {"useWeb": True}

        resp = self._session.post(url, data=json.dumps(body), timeout=120)
        if resp.status_code >= 400:
            raise RuntimeError(f"M365 Copilot Chat API error {resp.status_code}: {resp.text}")

        return self._extract_text(resp.json())

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
