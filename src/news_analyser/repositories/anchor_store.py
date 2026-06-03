"""
RAG Anchor Store — selbst-bootstrappende Kalibrierungsreferenzen.

Verwaltet eine separate ChromaDB-Collection 'orwell_anchors' mit manuell
oder automatisch validierten Referenzartikeln.

Lazy-Loading-Prinzip:
  - Unter MIN_ANCHORS: nur statische Few-Shot-Anker im Prompt (kein RAG)
  - Ab MIN_ANCHORS: k ähnlichste Anker dynamisch in den Prompt eingebettet
  - Nach jeder Analyse: Artikel automatisch als neuer Anker gespeichert
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

from .chroma_client import get_client

_COLLECTION = "orwell_anchors"
_EMBED_FN   = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
)

MIN_ANCHORS = 5   # Mindestanzahl bevor RAG aktiv wird
K_RESULTS   = 3   # Anzahl ähnlicher Anker pro Anfrage


def _get_collection() -> chromadb.Collection:
    return get_client().get_or_create_collection(
        name=_COLLECTION,
        embedding_function=_EMBED_FN,
        metadata={"hnsw:space": "cosine"},
    )


def anchor_count() -> int:
    return _get_collection().count()


def get_similar_anchors(text: str, k: int = K_RESULTS) -> list[dict[str, Any]]:
    """Gibt die k ähnlichsten Anker zurück — leere Liste wenn zu wenig vorhanden."""
    col = _get_collection()
    if col.count() < MIN_ANCHORS:
        return []

    results = col.query(
        query_texts=[text],
        n_results=min(k, col.count()),
        include=["metadatas", "documents", "distances"],
    )

    anchors = []
    for i, meta in enumerate(results["metadatas"][0]):
        anchors.append({
            "orwell_index":         meta.get("orwell_index", 0.0),
            "politische_stroemung": meta.get("politische_stroemung", "neutral"),
            "domain":               meta.get("domain", ""),
            "excerpt":              results["documents"][0][i][:300],
            "similarity":           round(1 - results["distances"][0][i], 3),
        })
    return anchors


def add_anchor(
    text: str,
    orwell_index: float,
    politische_stroemung: list[str],
    domain: str,
    source_url: str,
) -> None:
    """Speichert einen analysierten Artikel als Anker-Referenz."""
    col = _get_collection()
    col.upsert(
        ids=[source_url],
        documents=[text],
        metadatas=[{
            "orwell_index":         orwell_index,
            "politische_stroemung": json.dumps(politische_stroemung, ensure_ascii=False),
            "domain":               domain,
            "source_url":           source_url,
        }],
    )


def format_anchors_for_prompt(anchors: list[dict[str, Any]]) -> str:
    """Formatiert Anker als lesbaren Prompt-Abschnitt."""
    if not anchors:
        return ""

    lines = ["## Dynamische Kalibrierungsreferenzen (ähnliche Artikel aus dem Korpus)\n"]
    for i, a in enumerate(anchors, 1):
        lines.append(
            f"**Referenz {i}** (Ähnlichkeit: {a['similarity']:.2f} | "
            f"Orwell-Index: {a['orwell_index']:.2f} | "
            f"Stroemung: {a['politische_stroemung']} | "
            f"Quelle: {a['domain']})"
        )
        lines.append(f"> {a['excerpt'].strip()}")
        lines.append("")

    lines.append(
        "Nutze diese Referenzen zur Kalibrierung deines orwell_index — "
        "ähnliche Texte sollten ähnliche Scores erhalten."
    )
    return "\n".join(lines)
