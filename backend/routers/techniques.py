import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from news_analyser.repositories.technique_store import get_all_techniques, get_technique

router = APIRouter(prefix="/techniques", tags=["techniques"])


@router.get("")
def list_techniques() -> list[dict]:
    return get_all_techniques()


@router.get("/{technique_id}")
def get_technique_by_id(technique_id: str) -> dict:
    t = get_technique(technique_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Technique not found")
    return t
