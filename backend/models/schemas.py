from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["green", "yellow", "red"]
AnalysisStatus = Literal["pending", "running", "completed", "failed"]


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    uploaded_at: datetime


class CompareRequest(BaseModel):
    old_document_id: str = Field(..., min_length=1)
    new_document_id: str = Field(..., min_length=1)


class CompareResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus


class LawMatch(BaseModel):
    law_name: str
    article: str
    text: str
    score: float


class AnalysisResultItem(BaseModel):
    article: str
    change_type: Literal["modified", "added", "removed"]
    old: str
    new: str
    similarity: float
    semantic_method: str
    conflict: bool
    risk: RiskLevel
    law: str
    law_article: str
    explanation: str
    laws: list[LawMatch] = Field(default_factory=list)


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None


class AnalysisRecord(BaseModel):
    analysis_id: str
    old_document_id: str
    new_document_id: str
    status: AnalysisStatus
    result: list[AnalysisResultItem] = Field(default_factory=list)
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
