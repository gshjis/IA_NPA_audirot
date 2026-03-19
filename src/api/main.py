import os
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.api.models import SearchRequest, SearchResponse, SearchResult
from src.loader import load_json
from src.logger import logger
from src.search.engine import LegalSemanticSearchEngine

app = FastAPI(
    title="Legal Semantic Search API",
    description="API семантического поиска по юридическому корпусу для backend и frontend-клиентов.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
logger.info("Запуск API приложения")

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "RETRIEVAL_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8001,http://127.0.0.1:8001",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TAGS_PATH = os.getenv("RETRIEVAL_TAGS_PATH", "data/raw/base.json")
CORPUS_PATH = os.getenv("RETRIEVAL_CORPUS_PATH", "data/processed/laws.json")
MODEL_NAME = os.getenv("RETRIEVAL_MODEL_NAME", "deepvk/USER2-base")
CACHE_DIR = os.getenv("RETRIEVAL_CACHE_DIR", "scripts/data/cache")

engine: LegalSemanticSearchEngine | None = None
engine_init_error: str | None = None


def _init_engine() -> None:
    global engine, engine_init_error

    try:
        corpus = load_json(CORPUS_PATH) if os.path.exists(CORPUS_PATH) else []
        engine = LegalSemanticSearchEngine(
            tags_filepath=TAGS_PATH,
            model_name=MODEL_NAME,
            training_corpus=corpus,
            cache_dir=CACHE_DIR,
        )
        engine_init_error = None
    except Exception as exc:
        engine = None
        engine_init_error = str(exc)
        logger.exception("Не удалось инициализировать движок retrieval API")


_init_engine()


@app.get("/health")
async def health() -> dict[str, str]:
    if engine is None:
        return {"status": "degraded", "reason": engine_init_error or "engine is not initialized"}
    return {"status": "ok"}


@app.post("/search", response_model=List[SearchResponse])
async def search(request: SearchRequest):
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Retrieval engine is unavailable. "
                f"Check RETRIEVAL_TAGS_PATH='{TAGS_PATH}' and RETRIEVAL_CORPUS_PATH='{CORPUS_PATH}'."
            ),
        )

    results_list = []
    
    for req_id, query_text in request.queries.items():
        try:
            # Поиск статей
            found_articles = engine.find_articles_by_new_sentence(
                query_text,
                k=request.k,
                similarity_weight=request.similarity_weight,
                coverage_weight=request.coverage_weight,
                penalty_factor=request.penalty_factor
            )
            
            # Формирование ответа
            results_list.append(SearchResponse(
                request_id=req_id,
                results=[
                    SearchResult(
                        article=res["article"],
                        score=res["score"],
                        query_tags=res["query_tags"],
                        article_tags=res["article_tags"],
                        common_tags=res["common_tags"]
                    ) for res in found_articles
                ]
            ))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при обработке запроса {req_id}: {str(e)}")
            
    return results_list
