from __future__ import annotations

from typing import TypedDict


class AnonymizationResult(TypedDict):
    text: str
    mapping: dict[str, str]  # placeholder → original surface form
