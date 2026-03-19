from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlsplit, urlunsplit

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json

from backend.config import settings
from backend.logger import logger


def utc_now() -> datetime:
    return datetime.now(UTC)


def _ensure_storage_dirs() -> None:
    Path(settings.documents_dir).mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    _ensure_storage_dirs()
    connection = psycopg.connect(settings.database_url, row_factory=dict_row)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _redact_database_url(database_url: str) -> str:
    parsed = urlsplit(database_url)
    if not parsed.netloc or parsed.password is None:
        return database_url

    auth = f"{parsed.username}:***@" if parsed.username else ""
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"{auth}{host}{port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def _normalize_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    normalized: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, datetime):
            normalized[key] = value.astimezone(UTC).isoformat()
        else:
            normalized[key] = value
    return normalized


def _normalize_analysis_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    normalized = _normalize_row(row)
    if normalized is None:
        return None

    raw_result = normalized.pop("result_json", [])
    if isinstance(raw_result, str):
        normalized["result"] = json.loads(raw_result or "[]")
    elif raw_result is None:
        normalized["result"] = []
    else:
        normalized["result"] = raw_result
    return normalized


def init_db() -> None:
    logger.info("Initializing PostgreSQL database at %s", _redact_database_url(settings.database_url))
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                content_type TEXT,
                file_path TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
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
                result_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                error_message TEXT,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                FOREIGN KEY(old_document_id) REFERENCES documents(id) ON DELETE RESTRICT,
                FOREIGN KEY(new_document_id) REFERENCES documents(id) ON DELETE RESTRICT
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_analyses_status
            ON analyses (status)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_analyses_old_document_id
            ON analyses (old_document_id)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_analyses_new_document_id
            ON analyses (new_document_id)
            """
        )


def insert_document(
    *,
    document_id: str,
    filename: str,
    content_type: str | None,
    file_path: str,
) -> dict[str, Any]:
    created_at = utc_now()
    with get_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO documents (id, filename, content_type, file_path, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (document_id, filename, content_type, file_path, created_at),
        ).fetchone()
    document = _normalize_row(row)
    if document is None:
        raise RuntimeError(f"Failed to insert document {document_id}")
    return document


def get_document(document_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM documents WHERE id = %s",
            (document_id,),
        ).fetchone()
    return _normalize_row(row)


def create_analysis(*, analysis_id: str, old_document_id: str, new_document_id: str) -> dict[str, Any]:
    timestamp = utc_now()
    with get_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO analyses (
                id, old_document_id, new_document_id, status, result_json,
                error_message, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (analysis_id, old_document_id, new_document_id, "pending", Json([]), None, timestamp, timestamp),
        ).fetchone()
    analysis = _normalize_analysis_row(row)
    if analysis is None:
        raise RuntimeError(f"Failed to create analysis {analysis_id}")
    return analysis


def update_analysis(
    analysis_id: str,
    *,
    status: str,
    result: list[dict[str, Any]] | None = None,
    error_message: str | None = None,
) -> dict[str, Any] | None:
    updated_at = utc_now()
    result_json = None if result is None else Json(result)
    with get_connection() as connection:
        row = connection.execute(
            """
            UPDATE analyses
            SET status = %s,
                result_json = COALESCE(%s::jsonb, result_json),
                error_message = %s,
                updated_at = %s
            WHERE id = %s
            RETURNING *
            """,
            (status, result_json, error_message, updated_at, analysis_id),
        ).fetchone()
    return _normalize_analysis_row(row)


def get_analysis(analysis_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM analyses WHERE id = %s",
            (analysis_id,),
        ).fetchone()
    return _normalize_analysis_row(row)
