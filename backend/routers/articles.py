import json
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query, HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from news_analyser.repositories.db_storage import _get_collection

router = APIRouter(prefix="/articles", tags=["articles"])


def _parse_meta(meta: dict[str, Any]) -> dict[str, Any]:
    for field in ("technique_names", "politische_stroemung"):
        if isinstance(meta.get(field), str):
            try:
                meta[field] = json.loads(meta[field])
            except Exception:
                meta[field] = []
    return meta


@router.get("")
def list_articles(
    domain: str | None = Query(None),
    orwell_min: float = Query(0.0, ge=0.0, le=1.0),
    orwell_max: float = Query(1.0, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict]:
    col = _get_collection()
    result = col.get(include=["metadatas"])
    metas = result.get("metadatas") or []

    rows = []
    for m in metas:
        m = _parse_meta(dict(m))
        oi = float(m.get("orwell_index", 0.0))
        if oi < orwell_min or oi > orwell_max:
            continue
        if domain and m.get("domain") != domain:
            continue
        rows.append({
            "source_url":          m.get("source_url", ""),
            "domain":              m.get("domain", ""),
            "title":               m.get("title", ""),
            "published_at":        m.get("published_at", ""),
            "orwell_index":        oi,
            "bernays_score":       float(m.get("bernays_score", 0.0)),
            "dunning_kruger_index": float(m.get("dunning_kruger_index", 0.0)) or None,
            "politische_stroemung": m.get("politische_stroemung", []),
            "technique_names":     m.get("technique_names", []),
            "intended_sentiment":  m.get("intended_sentiment", ""),
        })

    rows.sort(key=lambda r: r["published_at"] or "", reverse=True)
    return rows[:limit]


@router.get("/{article_id:path}")
def get_article(article_id: str) -> dict:
    col = _get_collection()
    result = col.get(ids=[article_id], include=["metadatas"])
    if not result["ids"]:
        raise HTTPException(status_code=404, detail="Article not found")

    m = _parse_meta(dict(result["metadatas"][0]))
    raw = m.get("analysis_json", "{}")
    try:
        full = json.loads(raw)
    except Exception:
        full = m
    full = _parse_meta(full)

    # Felder aus den Metadaten auf die oberste Ebene heben (für das Frontend)
    full.setdefault("orwell_index",         float(m.get("orwell_index", 0.0)))
    full.setdefault("bernays_score",        float(m.get("bernays_score", 0.0)))
    full.setdefault("dunning_kruger_index", float(m.get("dunning_kruger_index", 0.0)) or None)
    full.setdefault("technique_names",      m.get("technique_names", []))
    full.setdefault("intended_sentiment",   m.get("intended_sentiment", ""))
    full.setdefault("themenbereich",        m.get("themenbereich", ""))
    if "manipulation_targets" not in full:
        raw = m.get("manipulation_targets", "[]")
        try:
            full["manipulation_targets"] = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            full["manipulation_targets"] = []

    return full
