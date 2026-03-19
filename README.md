# IA_NPA_auditor

Система семантического анализа и тегирования нормативно-правовых актов (НПА).

## Запуск

### 1. Подготовка `.env`

Скопируй шаблон:

```bash
cp .env.example .env
```

Минимально проверь эти значения:

```bash
BACKEND_DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5433/npa_analysis"
COMETAPI_BASE_URL="https://openrouter.ai/api/v1"
COMETAPI_MODEL="x-ai/grok-4.1-fast"
COMETAPI_API_KEY="your-openrouter-key"
RETRIEVAL_SERVICE_URL="http://127.0.0.1:8000"
```

Если фронтендер будет ходить из браузера, добавь его origin в `BACKEND_CORS_ORIGINS`.

### 2. Режим разработки: Postgres в Docker, backend и retrieval локально

Этот сценарий удобен для второго backend-разработчика: база данных крутится в Docker, а Python-сервисы запускаются обычными командами и быстро подхватывают изменения кода.

1. Подними только PostgreSQL:

```bash
docker compose up -d postgres
```

2. Установи зависимости локально.

Если в проекте используете Poetry:

```bash
poetry install
```

Если работаешь без Poetry, используй локальное виртуальное окружение проекта и поставь зависимости тем способом, который принят у команды.

3. В одном терминале запусти retrieval:

```bash
cd /mnt/data/IA_NPA_audirot
set -a
source .env
set +a
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

4. Во втором терминале запусти backend:

```bash
cd /mnt/data/IA_NPA_audirot
set -a
source .env
set +a
poetry run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

5. Проверь, что сервисы поднялись:

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8000/health
```

Swagger:

- backend: `http://127.0.0.1:8001/docs`
- retrieval: `http://127.0.0.1:8000/docs`

### 3. Полный запуск через Docker Compose

Одна команда поднимает:

- `postgres` на `127.0.0.1:5433`
- `retrieval` на `127.0.0.1:8000`
- `backend` на `127.0.0.1:8001`

Запуск:

```bash
docker compose up --build
```

Если нужно в фоне:

```bash
docker compose up --build -d
```

Остановить:

```bash
docker compose down
```

Посмотреть логи:

```bash
docker compose logs -f
```

### 4. Проверка, что всё поднялось

Swagger и OpenAPI:

- backend Swagger: `http://127.0.0.1:8001/docs`
- backend OpenAPI: `http://127.0.0.1:8001/openapi.json`
- retrieval Swagger: `http://127.0.0.1:8000/docs`
- retrieval OpenAPI: `http://127.0.0.1:8000/openapi.json`

Healthcheck:

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8000/health
```

### 5. Основной сценарий для фронта: `upload-and-compare`

Для фронта основной endpoint такой:

```text
POST /analysis/upload-and-compare
```

Он принимает сразу два файла:

- `old_file`
- `new_file`

И сразу ставит анализ в очередь, возвращая `analysis_id`.

Пример запроса:

```bash
curl -X POST "http://127.0.0.1:8001/analysis/upload-and-compare" \
  -F "old_file=@/absolute/path/to/old_version.docx" \
  -F "new_file=@/absolute/path/to/new_version.docx"
```

Пример ответа:

```json
{
  "analysis_id": "ANALYSIS_ID",
  "status": "pending",
  "old_document": {
    "document_id": "OLD_DOC_ID",
    "filename": "old_version.docx",
    "uploaded_at": "2026-03-19T10:00:00+00:00"
  },
  "new_document": {
    "document_id": "NEW_DOC_ID",
    "filename": "new_version.docx",
    "uploaded_at": "2026-03-19T10:00:01+00:00"
  }
}
```

### 6. Проверка результата анализа

После получения `analysis_id` фронт или `curl` опрашивает:

```text
GET /analysis/{analysis_id}
```

Пример:

```bash
curl "http://127.0.0.1:8001/analysis/ANALYSIS_ID"
```

Если анализ ещё идёт:

```json
{
  "analysis_id": "ANALYSIS_ID",
  "status": "running",
  "created_at": "2026-03-19T10:00:00+00:00",
  "updated_at": "2026-03-19T10:00:03+00:00",
  "error_message": null
}
```

Если анализ завершён:

```json
[
  {
    "article": "2.1",
    "change_type": "modified",
    "old": "Старая редакция...",
    "new": "Новая редакция...",
    "similarity": 0.97,
    "semantic_method": "sentence-transformers",
    "relation": "conflict",
    "conflict": true,
    "risk": "red",
    "confidence": 0.91,
    "law": "Название закона",
    "law_article": "Статья 12",
    "evidence": "Краткая опора на норму",
    "explanation": "Почему система считает это конфликтом или соответствием.",
    "assessment_source": "llm",
    "laws": [
      {
        "law_name": "Название закона",
        "article": "Статья 12",
        "text": "Текст найденной нормы",
        "score": 0.87
      }
    ]
  }
]
```

### 7. Готовый smoke test на example-файлах

В репозитории есть тестовые файлы:

- `/mnt/data/IA_NPA_audirot/backend/examples/documents/old_regulation.docx`
- `/mnt/data/IA_NPA_audirot/backend/examples/documents/new_regulation.docx`

Запуск анализа одной командой:

```bash
curl -X POST "http://127.0.0.1:8001/analysis/upload-and-compare" \
  -F "old_file=@/mnt/data/IA_NPA_audirot/backend/examples/documents/old_regulation.docx" \
  -F "new_file=@/mnt/data/IA_NPA_audirot/backend/examples/documents/new_regulation.docx"
```

Если установлен `jq`, можно сразу получить `analysis_id` и прочитать результат:

```bash
ANALYSIS_ID=$(curl -s -X POST "http://127.0.0.1:8001/analysis/upload-and-compare" \
  -F "old_file=@/mnt/data/IA_NPA_audirot/backend/examples/documents/old_regulation.docx" \
  -F "new_file=@/mnt/data/IA_NPA_audirot/backend/examples/documents/new_regulation.docx" | jq -r '.analysis_id')

curl -s "http://127.0.0.1:8001/analysis/$ANALYSIS_ID" | jq
```

### 8. Если что-то не работает

Если backend не стартует:

- проверь `BACKEND_DATABASE_URL`
- проверь, что `postgres` контейнер поднялся
- посмотри `docker compose logs backend`

Если retrieval отвечает `503`:

- проверь, что у тебя есть данные для retrieval
- посмотри `docker compose logs retrieval`

Если LLM уходит в fallback:

- проверь `COMETAPI_API_KEY`
- проверь `COMETAPI_BASE_URL`
- посмотри `docker compose logs backend`

Подробная документация по backend находится в `backend/README.md`.

## Суть проекта
Проект предназначен для автоматического анализа текстов НПА (на примере Конституции Республики Беларусь), их тегирования на основе семантической близости к заданным тематикам и интеллектуального поиска статей по запросу пользователя.

## Формальная постановка модели

Пусть $Q$ — вектор релевантностей тегов для запроса, $A_i$ — вектор тегов $i$-й статьи, $W_i$ — вес $i$-й статьи, $N_i$ — индикатор "шумности" статьи ($N_i = 0$ если статья шумная, иначе $1$).

Релевантность статьи $S_i$ вычисляется как:
$$S_i = \left( \frac{Q \cdot A_i}{\|Q\| \|A_i\|} + \text{bonus}(Q, A_i) \right) \cdot W_i \cdot N_i$$

где:
- $\frac{Q \cdot A_i}{\|Q\| \|A_i\|}$ — косинусное сходство векторов тегов.
- $\text{bonus}(Q, A_i)$ — градиентный бонус: $+0.05$ за каждый совпадающий тег из топ-3 тегов запроса.
- $W_i$ — весовой коэффициент статьи.
- $N_i$ — фильтр шума (обнуляет оценку для шумных статей).

## Алгоритм работы

### 1. Парсинг данных
Исходный текст НПА (`const.txt`) преобразуется в структурированный JSON-формат. Парсер использует регулярные выражения для выделения разделов, глав и статей, сохраняя иерархическую структуру документа.

### 2. Логика присвоения тегов (`assign_tags`)
- **Подготовка**: Теги загружаются из JSON-файла, где каждому тегу соответствует список ключевых слов. Эти слова объединяются в текстовое описание.
- **Эмбеддинги**: Модель `SentenceTransformer` преобразует описания тегов в векторы (эмбеддинги).
- **Сравнение**: Для каждой статьи вычисляется эмбеддинг. С помощью косинусного сходства (`cosine_similarity`) определяется близость статьи к каждому тегу.
- **Результат**: Статье присваиваются топ-K наиболее близких тегов.

### 3. Логика поиска статей (`find_articles_by_new_sentence`)
Поиск реализован как гибридный процесс:
1. **Семантический вектор**: Запрос преобразуется в вектор релевантностей тегов (порог $0.25$ для включения тега в вектор).
2. **Косинусное сходство**: Вычисляется сходство между вектором запроса и векторами тегов статей.
3. **Применение фильтров и весов**:
   - **Веса статей**: Применяются коэффициенты значимости.
   - **Фильтрация шума**: Статьи из списка "шумных" получают оценку $0.0$.
   - **Гибридный бонус**: Градиентный бонус $+0.05$ за каждый совпадающий тег из топ-3 тегов запроса.
4. **Ранжирование**: Статьи сортируются по итоговой оценке (score), и возвращается топ-K результатов.

## Структура проекта
- `data/`: Хранилище данных.
  - `raw/`: Исходные текстовые файлы.
  - `processed/`: Обработанные JSON-файлы.
- `src/`: Исходный код приложения.
  - `parser.py`: Логика парсинга документов.
  - `search/`: Модуль семантического поиска.
    - `engine.py`: Основной класс `LegalSemanticSearchEngine`.
    - `utils.py`: Вспомогательные функции обработки текста.
- `scripts/`: Вспомогательные скрипты и исследовательские ноутбуки.
- `main.py`: Точка входа для запуска системы.
