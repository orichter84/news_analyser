"""
Vector database storage using ChromaDB (local, persistent).

Stores:
  - document:  the raw article text  (used for semantic search)
  - embedding: computed by ChromaDB's default embedding function
  - metadata:  flattened analysis JSON (for filtering + stats queries)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

from .chroma_client import get_client

_COLLECTION = "articles"

# Uses sentence-transformers/all-MiniLM-L6-v2 locally (no API key needed).
# Swap to OpenAIEmbeddingFunction if you prefer text-embedding-3-small.
_EMBED_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


def _get_collection() -> chromadb.Collection:
    return get_client().get_or_create_collection(
        name=_COLLECTION,
        embedding_function=_EMBED_FN,
        metadata={"hnsw:space": "cosine"},
    )


def _flatten_metadata(analysis: dict[str, Any]) -> dict[str, Any]:
    """ChromaDB metadata values must be str | int | float | bool."""
    ft = analysis.get("framing_target", {})
    techniques = analysis.get("detected_techniques", [])
    technique_names = json.dumps(
        [t["technique"] for t in techniques], ensure_ascii=False
    )

    return {
        "source_url":         analysis.get("source_url", ""),
        "domain":             analysis.get("domain", ""),
        "timestamp":          analysis.get("timestamp", ""),
        "title":              analysis.get("title", ""),
        "author":             analysis.get("author", ""),
        "published_at":       analysis.get("published_at", ""),
        "word_count":         int(analysis.get("word_count", 0)),
        "orwell_index":         float(ft.get("orwell_index", 0.0)),
        "dunning_kruger_index": float(ft.get("dunning_kruger_index", 0.0)),
        "main_narrative":       ft.get("main_narrative", ""),
        "target_direction":     ft.get("target_direction", ""),
        "intended_sentiment":   ft.get("intended_sentiment", ""),
        "technique_names":      technique_names,
        "bernays_score":        round(
            len(techniques) / analysis.get("word_count", 1) * 1000, 2
        ) if analysis.get("word_count", 0) > 0 else 0.0,
        "politische_stroemung": json.dumps(
            analysis.get("politische_stroemung", ["neutral"]), ensure_ascii=False
        ),
        "themenbereich":        analysis.get("themenbereich", "Sonstiges"),
        "manipulation_targets": json.dumps(
            analysis.get("manipulation_targets", []), ensure_ascii=False
        ),
        "analysis_json":        json.dumps(analysis, ensure_ascii=False),
        "llm_provider":         analysis.get("llm_provider", ""),
        "llm_model":            analysis.get("llm_model", ""),
    }


def store_result(article_text: str, analysis: dict[str, Any]) -> str:
    """Embed article_text, attach analysis as metadata. Returns the doc ID."""
    collection = _get_collection()
    doc_id = analysis.get("source_url", "unknown")

    # Upsert so re-running the same URL overwrites rather than duplicates.
    collection.upsert(
        ids=[doc_id],
        documents=[article_text],
        metadatas=[_flatten_metadata(analysis)],
    )
    return doc_id


def is_known_url(url: str) -> bool:
    """Prüft ob eine URL bereits in der DB gespeichert ist."""
    collection = _get_collection()
    result = collection.get(ids=[url], include=[])
    return len(result["ids"]) > 0


def query_similar(text: str, n_results: int = 5) -> list[dict[str, Any]]:
    """Return the n most semantically similar stored articles."""
    collection = _get_collection()
    results = collection.query(query_texts=[text], n_results=n_results)
    return results
