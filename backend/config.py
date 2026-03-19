from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_list(value: str | None, default: list[str]) -> list[str]:
    if value is None:
        return default
    items = [item.strip() for item in value.split(",")]
    return [item for item in items if item]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("BACKEND_APP_NAME", "NPA Analysis Backend")
    app_version: str = os.getenv("BACKEND_APP_VERSION", "0.1.0")
    base_dir: Path = Path(os.getenv("BACKEND_BASE_DIR", "backend")).resolve()
    database_url: str = os.getenv(
        "BACKEND_DATABASE_URL",
        "postgresql://postgres:postgres@127.0.0.1:5432/npa_analysis",
    )
    documents_dir: Path = Path(os.getenv("BACKEND_DOCUMENTS_DIR", "backend/storage/documents")).resolve()
    log_dir: Path = Path(os.getenv("BACKEND_LOG_DIR", "backend/logs")).resolve()
    retrieval_service_url: str = os.getenv("RETRIEVAL_SERVICE_URL", "http://127.0.0.1:8000")
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "3"))
    retrieval_timeout_seconds: float = float(os.getenv("RETRIEVAL_TIMEOUT_SECONDS", "30"))
    cometapi_api_key: str = os.getenv("COMETAPI_API_KEY", "")
    cometapi_base_url: str = os.getenv("COMETAPI_BASE_URL", "https://openrouter.ai/api/v1")
    cometapi_model: str = os.getenv("COMETAPI_MODEL", "x-ai/grok-4.1-fast")
    cometapi_timeout_seconds: float = float(os.getenv("COMETAPI_TIMEOUT_SECONDS", "60"))
    semantic_model_name: str = os.getenv("SEMANTIC_MODEL_NAME", "deepvk/USER2-base")
    semantic_similarity_threshold: float = float(os.getenv("SEMANTIC_SIMILARITY_THRESHOLD", "0.82"))
    semantic_model_local_only: bool = _as_bool(os.getenv("SEMANTIC_MODEL_LOCAL_ONLY"), default=False)
    semantic_cache_dir: Path = Path(os.getenv("SEMANTIC_CACHE_DIR", "backend/storage/model_cache")).resolve()
    cors_origins: list[str] = field(
        default_factory=lambda: _as_list(
            os.getenv("BACKEND_CORS_ORIGINS"),
            ["http://localhost:3000", "http://127.0.0.1:3000"],
        )
    )


settings = Settings()
