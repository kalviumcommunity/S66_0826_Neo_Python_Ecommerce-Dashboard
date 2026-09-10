"""Query manager to load and cache SQL files from the backend queries directory."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from server.config import QUERIES_DIR


@lru_cache(maxsize=32)
def load_query(filename: str) -> str:
    """Load a SQL query from the queries directory and cache its text content."""
    query_path = QUERIES_DIR / filename
    if not query_path.exists():
        raise FileNotFoundError(f"SQL query file not found at: {query_path}")
    return query_path.read_text(encoding="utf-8").strip()
