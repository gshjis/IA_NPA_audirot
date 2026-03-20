from __future__ import annotations

import json
from typing import Any

import httpx

from backend.config import settings
from backend.logger import logger


class LLMService:
    _MAX_CONTEXT_LAWS = 3

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

        prompt = self._build_prompt(
            article=article,
            old_text=old_text,
            new_text=new_text,
            laws=laws,
            similarity=similarity,
            change_type=change_type,
        )

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
                        "temperature": 0,
                        "max_tokens": 600,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "Ты юридический AI-ассистент. Анализируй только предоставленные тексты "
                                    "изменения и переданные нормы. Не выдумывай факты, статьи и законы. "
                                    "Если данных недостаточно, выбирай relation='unclear'. "
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

        return self._normalize_response(parsed, laws)

    def _build_prompt(
        self,
        *,
        article: str,
        old_text: str,
        new_text: str,
        laws: list[dict[str, Any]],
        similarity: float,
        change_type: str,
    ) -> str:
        relevant_laws_json = json.dumps(
            self._flatten_law_matches(laws)[: self._MAX_CONTEXT_LAWS],
            ensure_ascii=False,
            indent=2,
        )
        return f"""
Проанализируй изменение нормативного правового акта.

Задача:
Определи, противоречит ли новая редакция переданным нормам, соответствует им или данных недостаточно.

Правила:
1. Анализируй в первую очередь new_text.
2. old_text используй только для понимания сути изменения.
3. Используй только нормы из блока relevant_laws.
4. relation:
   - "conflict" — новая редакция явно противоречит норме;
   - "consistent" — новая редакция соответствует норме или не противоречит ей по смыслу;
   - "unclear" — данных недостаточно, норма слишком общая или связь неочевидна.
5. conflict=true только при relation="conflict".
6. risk:
   - "red" — явное противоречие;
   - "yellow" — потенциальный риск или неоднозначность;
   - "green" — признаков противоречия не видно.
7. Заполняй law и law_article только если можешь опереться на конкретную норму.
8. evidence — короткая выдержка или суть той нормы, на которую ты опираешься.
9. confidence — число от 0 до 1.
10. Если relevant_laws пустой, не придумывай закон и верни пустые law/law_article/evidence.

Входные данные:
article: "{article}"
change_type: "{change_type}"
semantic_similarity: {similarity}

<old_text>
{old_text or "<пусто>"}
</old_text>

<new_text>
{new_text or "<пусто>"}
</new_text>

<relevant_laws>
{relevant_laws_json}
</relevant_laws>

Верни только JSON строго такого вида:
{{
  "relation": "conflict|consistent|unclear",
  "conflict": true,
  "risk": "green|yellow|red",
  "confidence": 0.0,
  "law": "название закона или пустая строка",
  "law_article": "статья закона или пустая строка",
  "evidence": "краткая суть нормы или пустая строка",
  "explanation": "1-2 коротких предложения без markdown"
}}
"""

    def _normalize_response(self, parsed: dict[str, Any], laws: list[dict[str, Any]]) -> dict[str, Any]:
        relation = self._normalize_relation(
            parsed.get("relation"),
            parsed.get("conflict"),
            parsed.get("risk"),
        )
        conflict = relation == "conflict"
        risk = self._normalize_risk(parsed.get("risk"), relation)
        confidence = self._normalize_confidence(parsed.get("confidence"), relation)
        law_fallback = "" if relation == "unclear" else self._first_law_name(laws)
        law_article_fallback = "" if relation == "unclear" else self._first_law_article(laws)
        evidence = str(parsed.get("evidence", "") or "").strip()
        explanation = str(parsed.get("explanation", "LLM did not provide explanation.") or "").strip()

        return {
            "relation": relation,
            "conflict": conflict,
            "risk": risk,
            "confidence": confidence,
            "law": str(parsed.get("law", law_fallback) or law_fallback),
            "law_article": str(parsed.get("law_article", law_article_fallback) or law_article_fallback),
            "evidence": evidence,
            "explanation": explanation or "LLM did not provide explanation.",
            "assessment_source": "llm",
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
        first_law_evidence = self._first_law_text(laws)
        law_context_exists = bool(first_law_name or first_law_article)

        if change_type in {"added", "removed"} or similarity < 0.65:
            risk = "red" if law_context_exists else "yellow"
        elif similarity < 0.85:
            risk = "yellow"
        else:
            risk = "green"

        relation = self._relation_from_risk(risk, law_context_exists)
        conflict = relation == "conflict"
        explanation = (
            f"Изменение в {article} оценено эвристически: тип изменения '{change_type}', "
            f"семантическая близость {similarity:.2f}. "
            f"{'Найдены потенциально релевантные нормы.' if law_context_exists else 'Релевантные нормы не найдены.'}"
        )

        return {
            "relation": relation,
            "conflict": conflict,
            "risk": risk,
            "confidence": self._heuristic_confidence(similarity, relation),
            "law": first_law_name,
            "law_article": first_law_article,
            "evidence": first_law_evidence,
            "explanation": explanation,
            "assessment_source": "heuristic",
        }

    def _normalize_relation(self, relation: Any, conflict: Any, risk: Any) -> str:
        relation_value = str(relation).strip().lower()
        if relation_value in {"conflict", "contradiction", "противоречие"}:
            return "conflict"
        if relation_value in {"consistent", "compliant", "match", "соответствие", "соответствует"}:
            return "consistent"
        if relation_value in {"unclear", "unknown", "insufficient", "неясно", "недостаточно"}:
            return "unclear"
        if self._as_bool(conflict):
            return "conflict"
        return self._relation_from_risk(self._normalize_risk(risk), law_context_exists=None)

    def _normalize_risk(self, risk: Any, relation: str | None = None) -> str:
        risk_value = str(risk).strip().lower()
        if risk_value in {"green", "yellow", "red"}:
            return risk_value
        if relation == "conflict":
            return "red"
        if relation == "consistent":
            return "green"
        return "yellow"

    def _normalize_confidence(self, confidence: Any, relation: str) -> float:
        try:
            value = float(confidence)
        except (TypeError, ValueError):
            if relation == "conflict":
                return 0.85
            if relation == "consistent":
                return 0.75
            return 0.5
        return min(max(value, 0.0), 1.0)

    def _relation_from_risk(self, risk: str, law_context_exists: bool | None) -> str:
        if risk == "red" and law_context_exists is not False:
            return "conflict"
        if risk == "green":
            return "consistent"
        return "unclear"

    def _heuristic_confidence(self, similarity: float, relation: str) -> float:
        base_confidence = min(max(similarity, 0.0), 1.0)
        if relation == "conflict":
            return max(0.55, base_confidence)
        if relation == "consistent":
            return max(0.5, base_confidence)
        return min(0.7, max(0.35, base_confidence))

    def _flatten_law_matches(self, laws: list[dict[str, Any]]) -> list[dict[str, Any]]:
        flattened_matches: list[dict[str, Any]] = []
        for group in laws:
            matches = group.get("law_matches", [])
            if isinstance(matches, list):
                flattened_matches.extend(match for match in matches if isinstance(match, dict))
        return flattened_matches

    def _first_law_text(self, laws: list[dict[str, Any]]) -> str:
        if not laws:
            return ""
        matches = laws[0].get("law_matches", [])
        if not matches:
            return ""
        return str(matches[0].get("text", ""))

    def _as_bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

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
