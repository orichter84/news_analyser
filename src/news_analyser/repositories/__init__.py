"""
Repository layer — alle ChromaDB-Operationen an einem Ort.

    article_repository  — Artikel speichern, suchen, Duplikat-Check
    anchor_repository   — RAG-Kalibrierungsanker (orwell_anchors Collection)
    technique_repository — Manipulationstechniken-KB (techniques Collection)
"""

from .db_storage import store_result, is_known_url, query_similar
from .anchor_store import get_similar_anchors, add_anchor, format_anchors_for_prompt, anchor_count
from .technique_store import normalize_technique, get_all_techniques, get_technique

__all__ = [
    "store_result", "is_known_url", "query_similar",
    "get_similar_anchors", "add_anchor", "format_anchors_for_prompt", "anchor_count",
    "normalize_technique", "get_all_techniques", "get_technique",
]
