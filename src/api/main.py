from fastapi import FastAPI, HTTPException
from typing import List
from src.logger import logger
from src.search.engine import LegalSemanticSearchEngine
from src.api.models import SearchRequest, SearchResponse, SearchResult
from src.loader import load_json
import os

app = FastAPI(title="Legal Semantic Search API")
logger.info("Запуск API приложения")

# Инициализация движка (пути можно вынести в переменные окружения)
TAGS_PATH = "data/raw/base.json"
CORPUS_PATH = "data/processed/laws.json"

# Загрузка корпуса
corpus = load_json(CORPUS_PATH) if os.path.exists(CORPUS_PATH) else []

engine = LegalSemanticSearchEngine(
    tags_filepath=TAGS_PATH,
    training_corpus=corpus
)

@app.post("/search", response_model=List[SearchResponse])
async def search(request: SearchRequest):
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
