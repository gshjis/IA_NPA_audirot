from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

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
    lifespan=lifespan,
)

app.include_router(documents_router)
app.include_router(analysis_router)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
