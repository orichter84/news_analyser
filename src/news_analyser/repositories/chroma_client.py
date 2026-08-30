"""
ChromaDB client factory.

Reads CHROMA_HOST and CHROMA_PORT from the environment and returns
an HttpClient. Defaults to localhost:8001 for local development.

Start local ChromaDB server:
    chroma run --host localhost --port 8001 --path data/chroma_db
"""
from __future__ import annotations

import os
from functools import lru_cache

import chromadb


@lru_cache(maxsize=1)
def get_client() -> chromadb.HttpClient:
    """Return a process-wide shared HttpClient.

    Each HttpClient() opens a connection on construction, so creating one per
    call (the previous behaviour) leaked a connection/file descriptor on the
    Chroma server for every article, technique lookup and status poll —
    enough over a few days of continuous feed operation to exhaust the
    server's open-file limit ("Too many open files"). A single cached client
    is also chromadb's documented usage pattern.
    """
    host = os.environ.get("CHROMA_HOST", "localhost")
    port = int(os.environ.get("CHROMA_PORT", "8001"))
    return chromadb.HttpClient(host=host, port=port)
