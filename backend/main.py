from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.analysis import router as analysis_router
from backend.api.documents import router as documents_router
from backend.config import settings
from backend.database.db import init_db
from backend.logger import logger


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    logger.info("Starting %s", settings.app_name)
    yield
    logger.info("Stopping %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API для загрузки документов, запуска анализа изменений и получения результатов.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins) or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(analysis_router)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
