from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path


class LLMCache:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def get(self, prompt: str) -> str | None:
        key = self._key(prompt)
        with sqlite3.connect(self.path) as connection:
            row = connection.execute("SELECT response FROM llm_cache WHERE cache_key = ?", (key,)).fetchone()
        return row[0] if row else None

    def set(self, prompt: str, response: str) -> None:
        key = self._key(prompt)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO llm_cache (cache_key, response, created_at)
                VALUES (?, ?, datetime('now'))
                """,
                (key, response),
            )

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_cache (
                    cache_key TEXT PRIMARY KEY,
                    response TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _key(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

