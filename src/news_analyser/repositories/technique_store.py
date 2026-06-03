"""
ChromaDB-backed store for manipulation technique definitions.

Serves two purposes:
  1. Semantic normalization -- LLM free-text output mapped to canonical names
  2. Knowledge Base data source -- /api/techniques returns all entries

Technique definitions are loaded from src/news_analyser/data/techniques.json.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

from .chroma_client import get_client

_DATA_DIR = Path(__file__).parent.parent / "data"
_COLLECTION = "techniques"
_EMBED_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
)
# Cosine distance threshold: < 0.35 -> accept canonical mapping
_MATCH_THRESHOLD = 0.35


def _load_techniques() -> list[dict[str, Any]]:
    """Load technique definitions from the JSON data file."""
    path = _DATA_DIR / "techniques.json"
    return json.loads(path.read_text(encoding="utf-8"))


_TECHNIQUES: list[dict[str, Any]] = _load_techniques()


def _get_collection() -> chromadb.Collection:
    return get_client().get_or_create_collection(
        name=_COLLECTION,
        embedding_function=_EMBED_FN,
        metadata={"hnsw:space": "cosine"},
    )


def _ensure_seeded(col: chromadb.Collection) -> None:
    if col.count() > 0:
        return
    col.upsert(
        ids=[t["id"] for t in _TECHNIQUES],
        documents=[t["doc"] for t in _TECHNIQUES],
        metadatas=[
            {
                "id":            t["id"],
                "name":          t["name"],
                "name_de":       t["name_de"],
                "category":      t["category"],
                "description":   t["description"],
                "example":       t["example"],
                "reference_url": t["reference_url"],
            }
            for t in _TECHNIQUES
        ],
    )
    print(f"[techniques] {len(_TECHNIQUES)} Techniken in DB gespeichert.")


def normalize_technique(name: str) -> str:
    """Sucht den semantisch naechsten kanonischen Techniken-Namen.
    Gibt den Original-Namen zurueck wenn keine gute Uebereinstimmung gefunden wird."""
    col = _get_collection()
    _ensure_seeded(col)

    results = col.query(
        query_texts=[name],
        n_results=1,
        include=["metadatas", "distances"],
    )
    if not results["ids"] or not results["ids"][0]:
        return name

    distance = results["distances"][0][0]
    if distance > _MATCH_THRESHOLD:
        return name

    return results["metadatas"][0][0]["name"]


def get_all_techniques() -> list[dict[str, Any]]:
    """Gibt alle dokumentierten Techniken zurueck (fuer die Knowledge Base API)."""
    col = _get_collection()
    _ensure_seeded(col)
    result = col.get(include=["metadatas"])
    return sorted(
        [m for m in (result.get("metadatas") or []) if m],
        key=lambda m: (m.get("category", ""), m.get("name", "")),
    )


def get_technique(technique_id: str) -> dict[str, Any] | None:
    """Gibt eine einzelne Technik per ID zurueck."""
    col = _get_collection()
    _ensure_seeded(col)
    result = col.get(ids=[technique_id], include=["metadatas"])
    if not result["ids"]:
        return None
    return result["metadatas"][0]
