from __future__ import annotations

import asyncio
from typing import Any

from backend.database.db import get_document, update_analysis
from backend.logger import logger
from backend.services.diff_service import DiffService
from backend.services.llm_service import LLMService
from backend.services.parser_service import ParserService
from backend.services.retrieval_service import RetrievalServiceClient
from backend.services.semantic_service import SemanticService


class AnalysisService:
    def __init__(self) -> None:
        self.parser_service = ParserService()
        self.diff_service = DiffService()
        self.semantic_service = SemanticService()
        self.retrieval_service = RetrievalServiceClient()
        self.llm_service = LLMService()

    async def run_analysis(self, analysis_id: str, old_doc_id: str, new_doc_id: str) -> list[dict[str, Any]]:
        update_analysis(analysis_id, status="running")

        try:
            old_document = get_document(old_doc_id)
            new_document = get_document(new_doc_id)

            if old_document is None or new_document is None:
                raise ValueError("One or both documents are missing in the database")

            logger.info("Starting analysis %s for documents %s and %s", analysis_id, old_doc_id, new_doc_id)

            old_sections = await asyncio.to_thread(
                self.parser_service.parse_document,
                old_document["file_path"],
            )
            new_sections = await asyncio.to_thread(
                self.parser_service.parse_document,
                new_document["file_path"],
            )
            changes = await asyncio.to_thread(
                self.diff_service.compare_sections,
                old_sections,
                new_sections,
            )

            prepared_changes: list[tuple[str, dict[str, Any]]] = []
            retrieval_queries: dict[str, str] = {}
            for index, change in enumerate(changes, start=1):
                query_id = f"change_{index}"
                query_text = str(change.get("new") or change.get("old") or "")
                prepared_changes.append((query_id, change))
                if query_text.strip():
                    retrieval_queries[query_id] = query_text

            retrieval_results: dict[str, list[dict[str, Any]]]
            if retrieval_queries:
                try:
                    retrieval_results = await self.retrieval_service.search_laws_batch(retrieval_queries)
                except Exception as exc:
                    logger.warning(
                        "Retrieval service batch request failed for %s changes: %s",
                        len(retrieval_queries),
                        exc,
                    )
                    retrieval_results = {query_id: [] for query_id in retrieval_queries}
            else:
                retrieval_results = {}

            results: list[dict[str, Any]] = []
            for query_id, change in prepared_changes:
                semantic = await asyncio.to_thread(
                    self.semantic_service.compare,
                    str(change.get("old", "")),
                    str(change.get("new", "")),
                )
                laws = retrieval_results.get(query_id, [])

                llm_result = await self.llm_service.analyze_change(
                    article=str(change["article"]),
                    old_text=str(change.get("old", "")),
                    new_text=str(change.get("new", "")),
                    laws=laws,
                    similarity=semantic.similarity,
                    change_type=str(change["change_type"]),
                )

                flattened_laws = laws[0]["law_matches"] if laws else []
                results.append(
                    {
                        "article": change["article"],
                        "change_type": change["change_type"],
                        "old": change.get("old", ""),
                        "new": change.get("new", ""),
                        "similarity": semantic.similarity,
                        "semantic_method": semantic.method,
                        "relation": llm_result["relation"],
                        "conflict": llm_result["conflict"],
                        "risk": llm_result["risk"],
                        "confidence": llm_result["confidence"],
                        "law": llm_result["law"],
                        "law_article": llm_result["law_article"],
                        "evidence": llm_result["evidence"],
                        "explanation": llm_result["explanation"],
                        "assessment_source": llm_result["assessment_source"],
                        "laws": flattened_laws,
                    }
                )

            update_analysis(analysis_id, status="completed", result=results, error_message=None)
            logger.info("Analysis %s completed with %s changed sections", analysis_id, len(results))
            return results
        except Exception as exc:
            logger.exception("Analysis %s failed", analysis_id)
            update_analysis(analysis_id, status="failed", error_message=str(exc))
            raise
