from pydantic import BaseModel, Field
from typing import Dict, List, Any
from src.logger import logger

class SearchRequest(BaseModel):
    # Запрос представляет собой словарь, где ключи - ID (строки), значения - тексты запросов
    queries: Dict[str, str] = Field(..., description="Словарь запросов: {id: текст_запроса}")
    k: int = Field(5, description="Количество возвращаемых статей", ge=1)
    similarity_weight: float = Field(0.4, description="Вес косинусного сходства", ge=0.0, le=1.0)
    coverage_weight: float = Field(0.6, description="Вес покрытия тегов", ge=0.0, le=1.0)
    penalty_factor: float = Field(0.5, description="Коэффициент штрафа", ge=0.0, le=1.0)

class SearchResult(BaseModel):
    article: Dict[str, Any]
    score: float
    query_tags: Dict[str, float]
    article_tags: Dict[str, float]
    common_tags: List[str]

class SearchResponse(BaseModel):
    request_id: str
    results: List[SearchResult]
