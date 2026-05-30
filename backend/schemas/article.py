from __future__ import annotations

from pydantic import BaseModel
from typing import Any


class DetectedTechnique(BaseModel):
    technique: str
    quote: str
    explanation: str


class FramingTarget(BaseModel):
    main_narrative: str
    intended_sentiment: str
    orwell_index: float
    dunning_kruger_index: float | None = None
    target_direction: str | None = None


class ArticleResponse(BaseModel):
    source_url: str
    domain: str
    title: str
    author: str
    published_at: str
    word_count: int
    timestamp: str
    detected_techniques: list[DetectedTechnique]
    framing_target: FramingTarget
    politische_stroemung: list[str]
    orwell_index: float
    bernays_score: float
    dunning_kruger_index: float | None = None
    intended_sentiment: str | None = None


class ArticleListItem(BaseModel):
    source_url: str
    domain: str
    title: str
    published_at: str
    orwell_index: float
    bernays_score: float
    dunning_kruger_index: float | None = None
    politische_stroemung: list[str]
    technique_names: list[str]
    intended_sentiment: str | None = None


class AnalyseRequest(BaseModel):
    url: str


class AnalyseResponse(BaseModel):
    status: str
    message: str
    job_id: str | None = None
    result: dict[str, Any] | None = None
