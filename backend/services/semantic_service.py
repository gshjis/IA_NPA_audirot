from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from backend.config import settings
from backend.logger import logger

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional runtime dependency loading
    SentenceTransformer = None


@dataclass
class SemanticAnalysis:
    similarity: float
    meaning_changed: bool
    method: str


class SemanticService:
    def __init__(self) -> None:
        self._model = None
        self._load_error: Exception | None = None

    def compare(self, old_text: str, new_text: str) -> SemanticAnalysis:
        old_text = old_text.strip()
        new_text = new_text.strip()

        if not old_text and not new_text:
            return SemanticAnalysis(similarity=1.0, meaning_changed=False, method="empty")
        if not old_text or not new_text:
            return SemanticAnalysis(similarity=0.0, meaning_changed=True, method="empty-side")

        model = self._get_model()
        if model is None:
            similarity = SequenceMatcher(None, old_text, new_text).ratio()
            return SemanticAnalysis(
                similarity=round(float(similarity), 4),
                meaning_changed=similarity < settings.semantic_similarity_threshold,
                method="sequence-matcher-fallback",
            )

        embeddings = model.encode([old_text, new_text], normalize_embeddings=True)
        similarity = float(embeddings[0] @ embeddings[1])
        return SemanticAnalysis(
            similarity=round(similarity, 4),
            meaning_changed=similarity < settings.semantic_similarity_threshold,
            method="sentence-transformers",
        )

    def _get_model(self):
        if self._model is not None:
            return self._model
        if self._load_error is not None:
            return None
        if SentenceTransformer is None:
            self._load_error = RuntimeError("sentence-transformers is not installed")
            logger.warning("sentence-transformers is unavailable, using lexical fallback")
            return None
        try:
            self._model = SentenceTransformer(
                settings.semantic_model_name,
                cache_folder=str(settings.semantic_cache_dir),
                local_files_only=settings.semantic_model_local_only,
            )
            return self._model
        except Exception as exc:  # pragma: no cover - depends on local model availability
            self._load_error = exc
            logger.warning("Failed to load semantic model %s: %s", settings.semantic_model_name, exc)
            return None
