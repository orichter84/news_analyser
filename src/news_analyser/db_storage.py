"""
Vector database storage using ChromaDB (local, persistent).

Stores:
  - document:  the raw article text  (used for semantic search)
  - embedding: computed by ChromaDB's default embedding function
  - metadata:  flattened analysis JSON (for filtering + stats queries)
"""

import json
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions


_DB_PATH = Path(__file__).parent.parent.parent / "data" / "chroma_db"
_COLLECTION = "articles"

# Uses sentence-transformers/all-MiniLM-L6-v2 locally (no API key needed).
# Swap to OpenAIEmbeddingFunction if you prefer text-embedding-3-small.
_EMBED_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


def _get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(_DB_PATH))
    return client.get_or_create_collection(
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
        "source_url":       analysis.get("source_url", ""),
        "domain":           analysis.get("domain", ""),
        "timestamp":        analysis.get("timestamp", ""),
        "bias_score":       float(ft.get("bias_score", 0.0)),
        "main_narrative":   ft.get("main_narrative", ""),
        "target_direction": ft.get("target_direction", ""),
        "intended_sentiment": ft.get("intended_sentiment", ""),
        "technique_names":  technique_names,           # JSON-encoded list
        "technique_count":  len(techniques),
        # Full analysis JSON for later retrieval
        "analysis_json":    json.dumps(analysis, ensure_ascii=False),
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
