# Backend for NPA Analysis

FastAPI backend для анализа изменений нормативных правовых актов. Сервис:

- загружает PDF/DOCX документы
- сравнивает старую и новую версии
- вызывает существующий retrieval API по HTTP
- отправляет изменения и найденные нормы в Claude через CometAPI
- сохраняет результаты в SQLite

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
export COMETAPI_API_KEY="your-cometapi-key"
export COMETAPI_BASE_URL="https://api.cometapi.com/v1"
export COMETAPI_MODEL="claude-3-5-haiku-latest"
export RETRIEVAL_SERVICE_URL="http://127.0.0.1:8000"
export RETRIEVAL_TOP_K="3"
export SEMANTIC_MODEL_NAME="deepvk/USER2-base"
export SEMANTIC_MODEL_LOCAL_ONLY="false"
```

## Как запустить

1. Подними retrieval API из существующего проекта:

```bash
uvicorn src.api.main:app --reload --port 8000
```

2. Подними новый backend:

```bash
uvicorn backend.main:app --reload --port 8001
```

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
- Если CometAPI или модель sentence-transformers недоступны, backend использует fallback-оценку и продолжает анализ.
- Все результаты и метаданные хранятся в SQLite: `backend/database/app.db`.
