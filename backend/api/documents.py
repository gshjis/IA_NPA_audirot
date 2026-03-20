from __future__ import annotations

from typing import Any
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile

from backend.config import settings
from backend.database.db import insert_document
from backend.logger import logger
from backend.models.schemas import DocumentUploadResponse


router = APIRouter(prefix="/documents", tags=["documents"])
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
CONTENT_TYPE_TO_EXTENSION = {
    "application/pdf": ".pdf",
    "application/x-pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


def _normalize_filename(filename: str | None) -> str:
    raw_name = (filename or "").strip().strip("'\"")
    if not raw_name:
        return ""
    return raw_name.replace("\\", "/").split("/")[-1]


def _detect_extension(filename: str, content_type: str | None) -> str:
    extension = Path(filename).suffix.lower()
    if extension in ALLOWED_EXTENSIONS:
        return extension
    normalized_content_type = (content_type or "").split(";")[0].strip().lower()
    return CONTENT_TYPE_TO_EXTENSION.get(normalized_content_type, "")


async def store_uploaded_document(file: UploadFile) -> dict[str, Any]:
    filename = _normalize_filename(file.filename)
    extension = _detect_extension(filename, file.content_type)
    if extension not in ALLOWED_EXTENSIONS:
        await file.close()
        raise HTTPException(
            status_code=400,
            detail=(
                "Only .pdf and .docx files are supported. "
                f"Received filename='{file.filename}' content_type='{file.content_type}'."
            ),
        )

    document_id = str(uuid4())
    target_path = Path(settings.documents_dir) / f"{document_id}{extension}"
    target_path.parent.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    await file.close()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    target_path.write_bytes(content)

    stored_filename = filename or f"{document_id}{extension}"

    document = insert_document(
        document_id=document_id,
        filename=stored_filename,
        content_type=file.content_type,
        file_path=str(target_path),
    )
    logger.info("Document %s uploaded as %s", document["id"], document["file_path"])
    return document


def build_document_upload_response(document: dict[str, Any]) -> DocumentUploadResponse:
    return DocumentUploadResponse(
        document_id=document["id"],
        filename=document["filename"],
        uploaded_at=datetime.fromisoformat(document["created_at"]).astimezone(UTC),
    )
