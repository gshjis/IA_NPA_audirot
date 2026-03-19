from __future__ import annotations

import json
from typing import Any

import httpx

from backend.config import settings
from backend.logger import logger


class RetrievalServiceClient:
    async def search_laws(self, text: str, top_k: int | None = None) -> list[dict[str, Any]]:
        effective_top_k = top_k or settings.retrieval_top_k
        payload = {
            "queries": {"change_1": text},
            "k": effective_top_k,
        }
        url = f"{settings.retrieval_service_url.rstrip('/')}/search"
        logger.info("Calling retrieval service at %s", url)

        async with httpx.AsyncClient(timeout=settings.retrieval_timeout_seconds) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            raw_response = response.json()

        return self._normalize_response(text, raw_response, effective_top_k)

    def _normalize_response(
        self,
        query_text: str,
        payload: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        normalized_matches: list[dict[str, Any]] = []

        for result_group in payload:
            law_matches: list[dict[str, Any]] = []
            for item in result_group.get("results", [])[:top_k]:
                article = item.get("article", {}) or {}
                law_matches.append(
                    {
                        "law_name": self._extract(article, "law_name", "document_name", "title", "name", default="Unknown law"),
                        "article": self._extract(article, "article", "article_number", "id", default="Unknown article"),
                        "text": self._extract(article, "content", "text", "body", default=json.dumps(article, ensure_ascii=False)),
                        "score": float(item.get("score", 0.0)),
                    }
                )
            normalized_matches.append(
                {
                    "npa_text": query_text,
                    "law_matches": law_matches,
                }
            )

        return normalized_matches

    def _extract(self, data: dict[str, Any], *keys: str, default: str) -> str:
        for key in keys:
            value = data.get(key)
            if value:
                return str(value)
        return default
