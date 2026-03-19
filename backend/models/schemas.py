from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["green", "yellow", "red"]
RelationType = Literal["conflict", "consistent", "unclear"]
AssessmentSource = Literal["llm", "heuristic"]
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


class UploadAndCompareResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    old_document: DocumentUploadResponse
    new_document: DocumentUploadResponse


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
    relation: RelationType = "unclear"
    conflict: bool
    risk: RiskLevel
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    law: str
    law_article: str
    evidence: str = ""
    explanation: str
    assessment_source: AssessmentSource = "heuristic"
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
