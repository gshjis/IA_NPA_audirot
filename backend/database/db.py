from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from backend.config import settings
from backend.logger import logger


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _ensure_parent_dirs() -> None:
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.documents_dir).mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    _ensure_parent_dirs()
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    logger.info("Initializing SQLite database at %s", settings.database_path)
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                content_type TEXT,
                file_path TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                old_document_id TEXT NOT NULL,
                new_document_id TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(old_document_id) REFERENCES documents(id),
                FOREIGN KEY(new_document_id) REFERENCES documents(id)
            )
            """
        )


def insert_document(
    *,
    document_id: str,
    filename: str,
    content_type: str | None,
    file_path: str,
) -> dict[str, Any]:
    created_at = utc_now_iso()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (id, filename, content_type, file_path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (document_id, filename, content_type, file_path, created_at),
        )
    return get_document(document_id)


def get_document(document_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
    return dict(row) if row else None


def create_analysis(*, analysis_id: str, old_document_id: str, new_document_id: str) -> dict[str, Any]:
    timestamp = utc_now_iso()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO analyses (
                id, old_document_id, new_document_id, status, result_json,
                error_message, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (analysis_id, old_document_id, new_document_id, "pending", "[]", None, timestamp, timestamp),
        )
    return get_analysis(analysis_id)


def update_analysis(
    analysis_id: str,
    *,
    status: str,
    result: list[dict[str, Any]] | None = None,
    error_message: str | None = None,
) -> dict[str, Any] | None:
    updated_at = utc_now_iso()
    result_json = None if result is None else json.dumps(result, ensure_ascii=False)
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE analyses
            SET status = ?, result_json = COALESCE(?, result_json), error_message = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, result_json, error_message, updated_at, analysis_id),
        )
    return get_analysis(analysis_id)


def get_analysis(analysis_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM analyses WHERE id = ?",
            (analysis_id,),
        ).fetchone()
    if not row:
        return None
    analysis = dict(row)
    analysis["result"] = json.loads(analysis.pop("result_json") or "[]")
    return analysis
