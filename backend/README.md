# Backend for NPA Analysis

FastAPI backend для анализа изменений нормативных правовых актов. Сервис:

- загружает PDF/DOCX документы
- сравнивает старую и новую версии
- вызывает существующий retrieval API по HTTP
- отправляет изменения и найденные нормы в Grok через OpenRouter
- сохраняет результаты в PostgreSQL

## Структура

```text
backend/
  main.py
  api/
    documents.py
    analysis.py
  services/
    parser_service.py
    diff_service.py
    semantic_service.py
    retrieval_service.py
    llm_service.py
    analysis_service.py
  models/
    schemas.py
  database/
    db.py
```

## Зависимости

- `fastapi`
- `uvicorn`
- `httpx`
- `python-multipart`
- `pdfplumber`
- `python-docx`
- `sentence-transformers`
- `psycopg`

## Переменные окружения

Скопируй пример и загрузи переменные в shell:

```bash
cp .env.example .env
set -a
source .env
set +a
```

Доступные переменные:

```bash
export BACKEND_DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/npa_analysis"
export BACKEND_CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
export COMETAPI_API_KEY="your-cometapi-key"
export COMETAPI_BASE_URL="https://openrouter.ai/api/v1"
export COMETAPI_MODEL="x-ai/grok-4.1-fast"
export RETRIEVAL_SERVICE_URL="http://127.0.0.1:8000"
export RETRIEVAL_TOP_K="3"
export RETRIEVAL_CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,http://localhost:8001,http://127.0.0.1:8001"
export SEMANTIC_MODEL_NAME="deepvk/USER2-base"
export SEMANTIC_MODEL_LOCAL_ONLY="false"
```

## Как запустить

1. Подними все сервисы одной командой:

```bash
docker compose up --build
```

2. Swagger/OpenAPI для фронтендера:

- Backend Swagger: `http://127.0.0.1:8001/docs`
- Backend OpenAPI JSON: `http://127.0.0.1:8001/openapi.json`
- Retrieval Swagger: `http://127.0.0.1:8000/docs`
- Retrieval OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## API

### 1. Upload

```bash
curl -X POST "http://127.0.0.1:8001/documents/upload" \
  -F "file=@/absolute/path/to/old_version.docx"
```

Ответ:

```json
{
  "document_id": "e4fd8b89-ef61-4e40-8c68-b877a6b2d26d",
  "filename": "old_version.docx",
  "uploaded_at": "2026-03-17T10:00:00+00:00"
}
```

### 2. Compare

```bash
curl -X POST "http://127.0.0.1:8001/analysis/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "old_document_id": "OLD_DOC_ID",
    "new_document_id": "NEW_DOC_ID"
  }'
```

Ответ:

```json
{
  "analysis_id": "e1820ff3-f071-45f9-b22d-300ca97d57d0",
  "status": "pending"
}
```

### 3. Result

```bash
curl "http://127.0.0.1:8001/analysis/e1820ff3-f071-45f9-b22d-300ca97d57d0"
```

Если анализ завершен:

```json
[
  {
    "article": "Статья 3",
    "change_type": "modified",
    "old": "Старая редакция...",
    "new": "Новая редакция...",
    "similarity": 0.71,
    "semantic_method": "sentence-transformers",
    "conflict": true,
    "risk": "red",
    "law": "Трудовой кодекс",
    "law_article": "Статья 21",
    "explanation": "Новое условие может противоречить действующим нормам.",
    "laws": [
      {
        "law_name": "Трудовой кодекс",
        "article": "Статья 21",
        "text": "Текст найденной статьи...",
        "score": 0.87
      }
    ]
  }
]
```

Если анализ еще не завершен, API вернет объект со статусом:

```json
{
  "analysis_id": "e1820ff3-f071-45f9-b22d-300ca97d57d0",
  "status": "running",
  "created_at": "2026-03-17T10:00:00+00:00",
  "updated_at": "2026-03-17T10:00:04+00:00",
  "error_message": null
}
```

## Примечания

- Retrieval сервис не изменяется и вызывается только по HTTP.
- Оба FastAPI сервиса поднимают Swagger UI на `/docs` и schema JSON на `/openapi.json`.
- Для браузерного фронтенда включен CORS через `BACKEND_CORS_ORIGINS` и `RETRIEVAL_CORS_ORIGINS`.
- Если данные retrieval (`data/raw/base.json`, `data/processed/laws.json`) отсутствуют, сервис всё равно стартует, но `/search` вернет `503` с описанием проблемы.
- Если CometAPI или модель sentence-transformers недоступны, backend использует fallback-оценку и продолжает анализ.
- Все результаты и метаданные хранятся в PostgreSQL, таблицы создаются автоматически при старте backend.
