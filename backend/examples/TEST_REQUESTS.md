# Test Requests

Локальные тестовые документы лежат в игнорируемой папке:

- `/mnt/data/IA_NPA_audirot/backend/examples/documents/old_regulation.docx`
- `/mnt/data/IA_NPA_audirot/backend/examples/documents/new_regulation.docx`

## 1. Запуск сервисов

В первом терминале:

```bash
source .venv/bin/activate
set -a
source .env
set +a
uvicorn src.api.main:app --reload --port 8000
```

Во втором терминале:

```bash
source .venv/bin/activate
set -a
source .env
set +a
uvicorn backend.main:app --reload --port 8001
```

## 2. Проверка healthcheck

```bash
curl http://127.0.0.1:8001/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

## 3. Запуск анализа одним запросом

Не добавляй вручную заголовок `Content-Type: multipart/form-data` для `curl` с `-F`, пусть `curl` выставит его сам.

```bash
curl -X POST "http://127.0.0.1:8001/analysis/upload-and-compare" \
  -F "old_file=@/mnt/data/IA_NPA_audirot/backend/examples/documents/old_regulation.docx" \
  -F "new_file=@/mnt/data/IA_NPA_audirot/backend/examples/documents/new_regulation.docx"
```

Пример ответа:

```json
{
  "analysis_id": "ANALYSIS_ID",
  "status": "pending",
  "old_document": {
    "document_id": "OLD_DOC_ID",
    "filename": "old_regulation.docx",
    "uploaded_at": "2026-03-18T00:00:00+00:00"
  },
  "new_document": {
    "document_id": "NEW_DOC_ID",
    "filename": "new_regulation.docx",
    "uploaded_at": "2026-03-18T00:00:00+00:00"
  }
}
```

## 4. Статистика

```bash
curl "http://127.0.0.1:8001/analysis/stats"
```

Пример ответа:

```json
{
  "total_documents_scanned": 12,
  "total_changes_found": 37
}
```

## 5. Получение результата

```bash
curl "http://127.0.0.1:8001/analysis/ANALYSIS_ID"
```

Если анализ еще выполняется, ответ будет примерно таким:

```json
{
  "analysis_id": "ANALYSIS_ID",
  "status": "running",
  "created_at": "2026-03-18T00:00:00+00:00",
  "updated_at": "2026-03-18T00:00:02+00:00",
  "error_message": null
}
```

Если анализ завершен, ответ будет списком изменений:

```json
[
  {
    "article": "Статья 3",
    "change_type": "modified",
    "old": "Старая редакция...",
    "new": "Новая редакция...",
    "similarity": 0.71,
    "semantic_method": "sentence-transformers",
    "relation": "conflict",
    "conflict": true,
    "risk": "red",
    "confidence": 0.91,
    "law": "Трудовой кодекс",
    "law_article": "Статья 21",
    "evidence": "Работник имеет право на условия труда, соответствующие требованиям законодательства.",
    "explanation": "Новое условие может противоречить действующим нормам.",
    "assessment_source": "llm",
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

## 6. Быстрый сценарий через переменные shell

```bash
ANALYSIS_ID=$(curl -s -X POST "http://127.0.0.1:8001/analysis/upload-and-compare" \
  -F "old_file=@/mnt/data/IA_NPA_audirot/backend/examples/documents/old_regulation.docx" \
  -F "new_file=@/mnt/data/IA_NPA_audirot/backend/examples/documents/new_regulation.docx" | jq -r '.analysis_id')

curl "http://127.0.0.1:8001/analysis/$ANALYSIS_ID"
```
