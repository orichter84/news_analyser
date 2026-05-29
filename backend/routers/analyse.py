import sys
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from news_analyser.scraper import fetch_article
from news_analyser.agents import analyze_article
from news_analyser.repositories.db_storage import store_result, is_known_url

router = APIRouter(prefix="/analyse", tags=["analyse"])

_jobs: dict[str, dict] = {}


class AnalyseRequest(BaseModel):
    url: str
    force: bool = False


def _run_analysis(job_id: str, url: str) -> None:
    try:
        article = fetch_article(url)
        if article is None:
            _jobs[job_id] = {"status": "error", "message": "Scraping fehlgeschlagen"}
            return
        if article.is_paywall:
            _jobs[job_id] = {"status": "paywall", "message": "Artikel befindet sich hinter einer Paywall."}
            return
        result = analyze_article(article)
        if result is None:
            _jobs[job_id] = {"status": "error", "message": "Analyse fehlgeschlagen"}
            return
        store_result(article.text, result)
        _jobs[job_id] = {"status": "done", "result": result}
    except Exception as exc:
        _jobs[job_id] = {"status": "error", "message": str(exc)}


@router.post("")
def submit_analyse(req: AnalyseRequest, background_tasks: BackgroundTasks) -> dict:
    if not req.force and is_known_url(req.url):
        return {"status": "skipped", "message": "URL bereits in der Datenbank", "job_id": None}

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending"}
    background_tasks.add_task(_run_analysis, job_id, req.url)
    return {"status": "accepted", "message": "Analyse gestartet", "job_id": job_id}


@router.get("/job/{job_id}")
def job_status(job_id: str) -> dict:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")
    return job
