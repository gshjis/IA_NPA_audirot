from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status

from backend.api.documents import build_document_upload_response, store_uploaded_document
from backend.database.db import create_analysis, get_analysis, get_analysis_statistics
from backend.logger import logger
from backend.models.schemas import (
    AnalysisResultItem,
    AnalysisStatisticsResponse,
    AnalysisStatusResponse,
    UploadAndCompareResponse,
)
from backend.services.analysis_service import AnalysisService


router = APIRouter(prefix="/analysis", tags=["analysis"])
analysis_service = AnalysisService()


def _queue_analysis(
    background_tasks: BackgroundTasks,
    *,
    old_document_id: str,
    new_document_id: str,
) -> str:
    analysis_id = str(uuid4())
    create_analysis(
        analysis_id=analysis_id,
        old_document_id=old_document_id,
        new_document_id=new_document_id,
    )
    logger.info(
        "Queued analysis %s for old_document=%s new_document=%s",
        analysis_id,
        old_document_id,
        new_document_id,
    )
    background_tasks.add_task(
        analysis_service.run_analysis,
        analysis_id,
        old_document_id,
        new_document_id,
    )
    return analysis_id


@router.post(
    "/upload-and-compare",
    response_model=UploadAndCompareResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_and_compare_documents(
    background_tasks: BackgroundTasks,
    old_file: UploadFile = File(...),
    new_file: UploadFile = File(...),
) -> UploadAndCompareResponse:
    old_document = await store_uploaded_document(old_file)
    new_document = await store_uploaded_document(new_file)
    analysis_id = _queue_analysis(
        background_tasks,
        old_document_id=str(old_document["id"]),
        new_document_id=str(new_document["id"]),
    )
    return UploadAndCompareResponse(
        analysis_id=analysis_id,
        status="pending",
        old_document=build_document_upload_response(old_document),
        new_document=build_document_upload_response(new_document),
    )


@router.get("/stats", response_model=AnalysisStatisticsResponse)
async def get_analysis_stats() -> AnalysisStatisticsResponse:
    stats = get_analysis_statistics()
    return AnalysisStatisticsResponse(**stats)


@router.get(
    "/{analysis_id}",
    response_model=list[AnalysisResultItem] | AnalysisStatusResponse,
)
async def get_analysis_result(analysis_id: str) -> list[AnalysisResultItem] | AnalysisStatusResponse:
    analysis = get_analysis(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if analysis["status"] != "completed":
        return AnalysisStatusResponse(
            analysis_id=analysis["id"],
            status=analysis["status"],
            created_at=datetime.fromisoformat(analysis["created_at"]).astimezone(UTC),
            updated_at=datetime.fromisoformat(analysis["updated_at"]).astimezone(UTC),
            error_message=analysis.get("error_message"),
        )

    return [AnalysisResultItem.model_validate(item) for item in analysis["result"]]
