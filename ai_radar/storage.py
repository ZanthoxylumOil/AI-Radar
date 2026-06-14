from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import Analysis, NewsItem

SCHEMA = """
CREATE TABLE IF NOT EXISTS news_items (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    summary TEXT NOT NULL,
    published_at TEXT NOT NULL,
    region TEXT NOT NULL,
    category TEXT NOT NULL,
    collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS analyses (
    item_id TEXT PRIMARY KEY,
    relevance_score INTEGER NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(item_id) REFERENCES news_items(id)
);
"""


class Repository:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def save_items(self, items: list[NewsItem]) -> int:
        before = self.count_items()
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT OR IGNORE INTO news_items
                (id, source, title, url, summary, published_at, region, category)
                VALUES (:id, :source, :title, :url, :summary, :published_at, :region, :category)
                """,
                [item.to_dict() for item in items],
            )
        return self.count_items() - before

    def save_analysis(self, analysis: Analysis) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO analyses
                (item_id, relevance_score, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    analysis.item_id,
                    analysis.relevance_score,
                    json.dumps(analysis.to_dict(), ensure_ascii=False),
                    analysis.created_at,
                ),
            )

    def pending_items(self, limit: int = 100) -> list[NewsItem]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT n.* FROM news_items n
                LEFT JOIN analyses a ON a.item_id = n.id
                WHERE a.item_id IS NULL
                ORDER BY
                    CASE WHEN n.category IN ('policy', 'regulation') THEN 0 ELSE 1 END,
                    n.published_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [NewsItem(**{key: row[key] for key in NewsItem.__dataclass_fields__}) for row in rows]

    def latest_results(self, limit: int = 100) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT n.*, a.payload FROM news_items n
                JOIN analyses a ON a.item_id = n.id
                ORDER BY a.relevance_score DESC, n.published_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        results = []
        for row in rows:
            item = {key: row[key] for key in NewsItem.__dataclass_fields__}
            results.append({"item": item, "analysis": json.loads(row["payload"])})
        return results

    def count_items(self) -> int:
        with self.connect() as connection:
            return connection.execute("SELECT COUNT(*) FROM news_items").fetchone()[0]