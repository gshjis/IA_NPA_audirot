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
CACHE_DIR = os.getenv("RETRIEVAL_CACHE_DIR", "/home/gshjis/Python_projects/IA_NPA_audirot/data/processed/cache/engine")

engine: LegalSemanticSearchEngine | None = None
engine_init_error: str | None = None


def _init_engine() -> None:
    global engine, engine_init_error

    try:
        corpus = load_json(CORPUS_PATH) if os.path.exists(CORPUS_PATH) else []
        # В текущем движке загрузка корпуса осуществляется из laws_filepath.
        engine = LegalSemanticSearchEngine(
            tags_filepath=TAGS_PATH,
            laws_filepath=CORPUS_PATH,
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

    # Пакетный поиск по списку запросов
    queries_in_order = list(request.queries.keys())
    query_texts = [request.queries[qid] for qid in queries_in_order]

    batch_results = engine.search_batch(
        query_texts,
        k=request.k,
        semantic_weight=request.similarity_weight,
    )

    results_list: List[SearchResponse] = []

    for req_id, per_query_results in zip(queries_in_order, batch_results):
        mapped_results: List[SearchResult] = []

        for res in per_query_results:
            q_tags = res.get("query_tags", [])[:5] or []
            a_tags = res.get("tags", []) or res.get("article_tags", [])[:5] or []
            common = sorted(list(set(q_tags) & set(a_tags)))

            mapped_results.append(
                SearchResult(
                    article=res.get("meta") or res.get("article") or {},
                    score=float(res.get("score", 0.0)),
                    query_tags={t: 1.0 for t in q_tags},
                    article_tags={t: 1.0 for t in a_tags[:5]},
                    common_tags=common,
                )
            )

        results_list.append(SearchResponse(request_id=req_id, results=mapped_results))

    return results_list
