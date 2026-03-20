FROM python:3.12-slim AS python-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app


FROM python-base AS backend-builder

COPY docker/requirements/backend.txt /tmp/requirements.txt

RUN python -m pip install --prefix=/install -r /tmp/requirements.txt


FROM python-base AS retrieval-builder

COPY docker/requirements/retrieval.txt /tmp/requirements.txt

RUN python -m pip install --prefix=/install -r /tmp/requirements.txt


FROM python-base AS backend

COPY --from=backend-builder /install /usr/local
COPY backend ./backend

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]


FROM python-base AS retrieval

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/data/raw /app/data/processed /app/scripts/data/cache

COPY --from=retrieval-builder /install /usr/local
COPY retrieval_app.py ./
COPY src ./src

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "retrieval_app:app", "--host", "0.0.0.0", "--port", "8000"]
