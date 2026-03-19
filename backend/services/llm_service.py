from __future__ import annotations

import json
from typing import Any

import httpx

from backend.config import settings
from backend.logger import logger


class LLMService:
    def __init__(self) -> None:
        self._base_url = settings.cometapi_base_url.rstrip("/")
        self._api_key = settings.cometapi_api_key
        self._model = settings.cometapi_model

    async def analyze_change(
        self,
        *,
        article: str,
        old_text: str,
        new_text: str,
        laws: list[dict[str, Any]],
        similarity: float,
        change_type: str,
    ) -> dict[str, Any]:
        if not self._api_key:
            logger.warning("LLM provider key is not configured, using heuristic analysis")
            return self._heuristic_response(
                article=article,
                old_text=old_text,
                new_text=new_text,
                laws=laws,
                similarity=similarity,
                change_type=change_type,
            )

        laws_json = json.dumps(laws, ensure_ascii=False, indent=2)
        prompt = f"""
Проанализируй изменение нормативного правового акта.

Статья/пункт: {article}
Тип изменения: {change_type}
Semantic similarity: {similarity}

Было:
{old_text or "<пусто>"}

Стало:
{new_text or "<пусто>"}

Релевантные нормы закона:
{laws_json}

Верни только валидный JSON со структурой:
{{
  "conflict": true,
  "risk": "green|yellow|red",
  "law": "название закона",
  "law_article": "статья закона",
  "explanation": "краткое объяснение"
}}
"""

        try:
            async with httpx.AsyncClient(timeout=settings.cometapi_timeout_seconds) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._model,
                        "temperature": 0.2,
                        "max_tokens": 600,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "Ты юридический AI-ассистент. Анализируй только предоставленные тексты "
                                    "и нормы закона. Не выдумывай факты. "
                                    "Отвечай только валидным JSON без markdown."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                    },
                )
                response.raise_for_status()
                payload = response.json()
            content = self._extract_message_content(payload)
        except Exception as exc:
            logger.warning("LLM request failed: %s. Using heuristic response.", exc)
            return self._heuristic_response(
                article=article,
                old_text=old_text,
                new_text=new_text,
                laws=laws,
                similarity=similarity,
                change_type=change_type,
            )

        parsed = self._parse_json_content(content)
        if parsed is None:
            logger.warning("Failed to parse LLM response as JSON, using heuristic fallback")
            return self._heuristic_response(
                article=article,
                old_text=old_text,
                new_text=new_text,
                laws=laws,
                similarity=similarity,
                change_type=change_type,
            )

        return {
            "conflict": bool(parsed.get("conflict", False)),
            "risk": self._normalize_risk(parsed.get("risk", "yellow")),
            "law": str(parsed.get("law", self._first_law_name(laws))),
            "law_article": str(parsed.get("law_article", self._first_law_article(laws))),
            "explanation": str(parsed.get("explanation", "LLM did not provide explanation.")),
        }

    def _extract_message_content(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices", [])
        if not choices:
            raise ValueError("LLM response does not contain choices")
        message = choices[0].get("message", {}) or {}
        content = message.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_chunks = []
            for item in content:
                if isinstance(item, dict) and item.get("type") in {"text", "output_text"}:
                    text_chunks.append(str(item.get("text", "")))
            return "\n".join(chunk for chunk in text_chunks if chunk).strip()
        return str(content)

    def _parse_json_content(self, content: str) -> dict[str, Any] | None:
        raw = content.strip()
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            fenced = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            try:
                return json.loads(fenced)
            except json.JSONDecodeError:
                return None

    def _heuristic_response(
        self,
        *,
        article: str,
        old_text: str,
        new_text: str,
        laws: list[dict[str, Any]],
        similarity: float,
        change_type: str,
    ) -> dict[str, Any]:
        first_law_name = self._first_law_name(laws)
        first_law_article = self._first_law_article(laws)
        law_context_exists = bool(first_law_name or first_law_article)

        if change_type in {"added", "removed"} or similarity < 0.65:
            risk = "red" if law_context_exists else "yellow"
        elif similarity < 0.85:
            risk = "yellow"
        else:
            risk = "green"

        conflict = risk == "red" and law_context_exists
        explanation = (
            f"Изменение в {article} оценено эвристически: тип изменения '{change_type}', "
            f"семантическая близость {similarity:.2f}. "
            f"{'Найдены потенциально релевантные нормы.' if law_context_exists else 'Релевантные нормы не найдены.'}"
        )

        return {
            "conflict": conflict,
            "risk": risk,
            "law": first_law_name,
            "law_article": first_law_article,
            "explanation": explanation,
        }

    def _normalize_risk(self, risk: Any) -> str:
        risk_value = str(risk).strip().lower()
        if risk_value in {"green", "yellow", "red"}:
            return risk_value
        return "yellow"

    def _first_law_name(self, laws: list[dict[str, Any]]) -> str:
        if not laws:
            return ""
        matches = laws[0].get("law_matches", [])
        if not matches:
            return ""
        return str(matches[0].get("law_name", ""))

    def _first_law_article(self, laws: list[dict[str, Any]]) -> str:
        if not laws:
            return ""
        matches = laws[0].get("law_matches", [])
        if not matches:
            return ""
        return str(matches[0].get("article", ""))
