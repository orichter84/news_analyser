import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import articles, analyse, stats, search, techniques

app = FastAPI(
    title="News Analyser API",
    version="1.0.0",
    description="REST API für den News Analyser — Framing- und Manipulationsanalyse.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router)
app.include_router(analyse.router)
app.include_router(stats.router)
app.include_router(search.router)
app.include_router(techniques.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/config")
def config() -> dict:
    return {
        "submit_enabled": os.environ.get("SUBMIT_ENABLED", "true").lower() != "false",
    }
