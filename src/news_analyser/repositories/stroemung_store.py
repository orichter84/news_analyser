"""
ChromaDB-backed store for the canonical politische_stroemung taxonomy.

Mirrors technique_store.py: the LLM is free to coin new labels (per pass2.md,
"not exhaustive"), so free-text synonyms ("wirtschaftsliberal", "neoliberal",
"marktwirtschaftlich") are mapped onto the fixed taxonomy in
src/news_analyser/data/stroemungen.json via semantic nearest-match, instead of
splintering publisher-profile and stats aggregations across near-duplicate
labels.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

from .chroma_client import get_client
from .negation_guard import is_oppositional

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"
_COLLECTION = "stroemungen"
_EMBED_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
)
# Cosine distance threshold: < 0.35 -> accept canonical mapping
_MATCH_THRESHOLD = 0.35


def _load_stroemungen() -> list[dict[str, Any]]:
    path = _DATA_DIR / "stroemungen.json"
    return json.loads(path.read_text(encoding="utf-8"))


_STROEMUNGEN: list[dict[str, Any]] = _load_stroemungen()
_CANONICAL_NAMES: set[str] = {s["name"] for s in _STROEMUNGEN}


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
        ids=[s["id"] for s in _STROEMUNGEN],
        documents=[s["doc"] for s in _STROEMUNGEN],
        metadatas=[{"id": s["id"], "name": s["name"]} for s in _STROEMUNGEN],
    )
    logger.info("%d Strömungen in DB gespeichert.", len(_STROEMUNGEN))


def normalize_stroemung(label: str) -> str:
    """Maps LLM free-text to the closest canonical politische_stroemung label.

    Returns the original label unchanged if it's already canonical or if no
    sufficiently close match is found (coined labels the taxonomy doesn't
    cover yet are kept as-is rather than forced onto an unrelated neighbour).
    """
    if not label:
        return label
    if label in _CANONICAL_NAMES:
        return label
    if is_oppositional(label):
        return label

    col = _get_collection()
    _ensure_seeded(col)

    results = col.query(
        query_texts=[label],
        n_results=1,
        include=["metadatas", "distances"],
    )
    if not results["ids"] or not results["ids"][0]:
        return label

    distance = results["distances"][0][0]
    if distance > _MATCH_THRESHOLD:
        return label

    return results["metadatas"][0][0]["name"]
