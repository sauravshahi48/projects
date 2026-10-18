"""SQLite stores original files and extracted pages; indexes are rebuilt, never unpickled."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .models import Document, Page


class Store:
    def __init__(self, data_dir: Path):
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "documents.sqlite3"
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, sha256 TEXT UNIQUE NOT NULL,
                    mime_type TEXT NOT NULL, created_at TEXT NOT NULL,
                    pages_json TEXT NOT NULL, content BLOB NOT NULL
                )
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def load(self) -> list[Document]:
        with self.connection() as db:
            rows = db.execute("SELECT * FROM documents ORDER BY created_at, id").fetchall()
        return [
            Document(
                id=row["id"],
                name=row["name"],
                sha256=row["sha256"],
                mime_type=row["mime_type"],
                created_at=row["created_at"],
                pages=tuple(Page(**p) for p in json.loads(row["pages_json"])),
                data=bytes(row["content"]),
            )
            for row in rows
        ]

    def insert(self, document: Document):
        with self.connection() as db:
            db.execute(
                "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    document.id,
                    document.name,
                    document.sha256,
                    document.mime_type,
                    document.created_at,
                    json.dumps([{"number": p.number, "text": p.text} for p in document.pages]),
                    document.data,
                ),
            )

    def delete(self, document_id: str):
        with self.connection() as db:
            db.execute("DELETE FROM documents WHERE id = ?", (document_id,))
