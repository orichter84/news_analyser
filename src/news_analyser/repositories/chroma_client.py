"""
ChromaDB client factory.

Reads CHROMA_HOST and CHROMA_PORT from the environment and returns
an HttpClient. Defaults to localhost:8001 for local development.

Start local ChromaDB server:
    chroma run --host localhost --port 8001 --path data/chroma_db
"""
from __future__ import annotations

import os
import chromadb


def get_client() -> chromadb.HttpClient:
    host = os.environ.get("CHROMA_HOST", "localhost")
    port = int(os.environ.get("CHROMA_PORT", "8001"))
    return chromadb.HttpClient(host=host, port=port)
