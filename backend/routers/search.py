import json
import sys
from pathlib import Path

from fastapi import APIRouter, Query

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from news_analyser.repositories.db_storage import query_similar

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def semantic_search(q: str = Query(..., min_length=2), n: int = Query(5, ge=1, le=20)) -> list[dict]:
    raw = query_similar(q, n_results=n)

    results = []
    for i, meta in enumerate(raw.get("metadatas", [[]])[0]):
        m = dict(meta)
        for field in ("technique_names", "politische_stroemung"):
            if isinstance(m.get(field), str):
                try:
                    m[field] = json.loads(m[field])
                except Exception:
                    m[field] = []
        results.append({
            "source_url":          m.get("source_url", ""),
            "domain":              m.get("domain", ""),
            "title":               m.get("title", ""),
            "published_at":        m.get("published_at", ""),
            "orwell_index":        float(m.get("orwell_index", 0.0)),
            "bernays_score":       float(m.get("bernays_score", 0.0)),
            "politische_stroemung": m.get("politische_stroemung", []),
            "technique_names":     m.get("technique_names", []),
            "similarity":          round(1 - raw["distances"][0][i], 3),
        })
    return results
