import sys
import os
import numpy as np
import hashlib
import json
from pathlib import Path

# Добавляем корень проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
from tqdm import tqdm
from typing import List, Dict, Any, Optional, Tuple
from src.logger import logger
from src.loader import load_json

class LegalSemanticSearchEngine:
    """
    Оптимизированный движок для юридического семантического поиска.
    
    Особенности:
    - Кэширование эмбеддингов тегов и статей
    - Гибридный поиск (семантика + BM25 + IDF)
    - Настраиваемое количество тегов
    - Поддержка категорий тегов
    """
    
    def __init__(
        self,
        tags_filepath: str = "data/raw/base.json",
        laws_filepath: str = "data/processed/laws.json",
        model_name: str = 'DeepPavlov/rubert-base-cased-sentence',
        cache_dir: str = "data/processed/cache/engine",
        tags_per_article: int = 400,
        similarity_weight: float = 0.7,
        use_bm25: bool = True,
        force_recompute: bool = False
    ):
        """
        Инициализация поискового движка.
        
        Args:
            tags_filepath: путь к JSON с тегами (категория -> список тегов)
            laws_filepath: путь к JSON с законами/статьями
            model_name: название sentence-transformer модели
            cache_dir: директория для кэширования
            tags_per_article: сколько тегов присваивать статье
            similarity_weight: вес семантики (1 - вес BM25)
            use_bm25: использовать ли BM25
            force_recompute: пересчитать всё заново
        """
        self.tags_per_article = tags_per_article
        self.similarity_weight = similarity_weight
        self.use_bm25 = use_bm25
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Загружаем теги
        self._load_tags(tags_filepath)
        
        # 2. Загружаем модель
        self._load_model(model_name, force_recompute)
        
        # 3. Загружаем или вычисляем эмбеддинги тегов
        self._load_or_compute_tag_embeddings(force_recompute)
        
        # 4. Загружаем законы
        self._load_laws(laws_filepath)
        
        # 5. Загружаем или вычисляем эмбеддинги статей и теги
        self._load_or_compute_article_data(force_recompute)
        
        # 6. Инициализируем BM25
        if self.use_bm25 and self.articles_texts:
            self._init_bm25()
        
        # 7. Вычисляем IDF веса
        self._compute_idf()
        
        logger.info("✅ LegalSemanticSearchEngine инициализирован")
    
    def _load_tags(self, tags_filepath: str):
        """Загрузка тегов из JSON."""
        try:
            self.raw_tags = load_json(tags_filepath)
            logger.info(f"📚 Загружено {len(self.raw_tags)} категорий тегов")
            
            # Преобразуем в плоский список для эмбеддингов
            self.tag_names = []
            self.tag_to_category = {}
            
            for category, tags in self.raw_tags.items():
                for tag in tags:
                    self.tag_names.append(tag)
                    self.tag_to_category[tag] = category
            
            logger.info(f"🏷️ Всего тегов: {len(self.tag_names)}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки тегов: {e}")
            raise
    
    def _load_model(self, model_name: str, force_recompute: bool):
        """Загрузка sentence-transformer модели."""
        model_path = self.cache_dir / "model_loaded.flag"
        
        if model_path.exists() and not force_recompute:
            logger.info(f"🔄 Модель {model_name} уже загружена, используем кэш")
        else:
            logger.info(f"📥 Загрузка модели {model_name}...")
        
        self.model = SentenceTransformer(
            model_name,
            cache_folder=str(self.cache_dir)
        )
        
        # Создаём флаг, что модель загружена
        model_path.touch()
        logger.info("✅ Модель загружена")
    
    def _load_or_compute_tag_embeddings(self, force_recompute: bool):
        """Загрузка или вычисление эмбеддингов тегов."""
        tag_emb_path = self.cache_dir / "tag_embeddings.npy"
        tag_names_path = self.cache_dir / "tag_names.json"
        
        if tag_emb_path.exists() and tag_names_path.exists() and not force_recompute:
            logger.info(f"📂 Загрузка эмбеддингов тегов из кэша...")
            self.tag_embeddings = np.load(tag_emb_path)
            with open(tag_names_path, 'r', encoding='utf-8') as f:
                cached_names = json.load(f)
            
            # Проверяем, что теги не изменились
            if cached_names == self.tag_names:
                logger.info(f"✅ Эмбеддинги тегов загружены ({len(self.tag_embeddings)} шт.)")
                return
            else:
                logger.warning("⚠️ Теги изменились, пересчитываем эмбеддинги...")
        
        # Вычисляем эмбеддинги
        logger.info(f"🧮 Вычисление эмбеддингов для {len(self.tag_names)} тегов...")
        self.tag_embeddings = self.model.encode(
            self.tag_names,
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=64
        )
        
        # Сохраняем
        np.save(tag_emb_path, self.tag_embeddings)
        with open(tag_names_path, 'w', encoding='utf-8') as f:
            json.dump(self.tag_names, f, ensure_ascii=False)
        
        logger.info(f"✅ Эмбеддинги тегов сохранены в {tag_emb_path}")
    
    def _load_laws(self, laws_filepath: str):
        """Загрузка законов."""
        self.laws_path = Path(laws_filepath)
        if not self.laws_path.exists():
            logger.error(f"❌ Файл законов не найден: {laws_filepath}")
            raise FileNotFoundError(f"Laws file not found: {laws_filepath}")
        
        with open(self.laws_path, 'r', encoding='utf-8') as f:
            self.laws_data = json.load(f)
        
        logger.info(f"📜 Загружено {len(self.laws_data)} статей/законов")
        
        # Извлекаем тексты
        self.articles_texts = []
        self.articles_meta = []
        
        for item in self.laws_data:
            if isinstance(item, dict):
                text = item.get("content") or item.get("text", "")
                self.articles_texts.append(text)
                self.articles_meta.append({
                    "source": item.get("source", "unknown"),
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "original": item
                })
            else:
                self.articles_texts.append(str(item))
                self.articles_meta.append({"source": "unknown", "original": item})
    
    def _load_or_compute_article_data(self, force_recompute: bool):
        """Загрузка или вычисление эмбеддингов статей и тегов."""
        articles_emb_path = self.cache_dir / "article_embeddings.npy"
        tagged_path = self.cache_dir / "tagged_articles.json"
        
        # Проверяем, всё ли есть в кэше
        cache_valid = (
            articles_emb_path.exists() and 
            tagged_path.exists() and 
            not force_recompute
        )
        
        if cache_valid:
            logger.info(f"📂 Загрузка данных статей из кэша...")
            
            # Загружаем эмбеддинги
            self.article_embeddings = np.load(articles_emb_path)
            
            # Загружаем тегированные статьи
            with open(tagged_path, 'r', encoding='utf-8') as f:
                self.tagged_articles = json.load(f)
            
            logger.info(f"✅ Загружено {len(self.tagged_articles)} тегированных статей")
            logger.info(f"✅ Эмбеддинги статей: {self.article_embeddings.shape}")
            
        else:
            # Вычисляем с нуля
            self._compute_article_data()
            
            # Сохраняем
            np.save(articles_emb_path, self.article_embeddings)
            with open(tagged_path, 'w', encoding='utf-8') as f:
                # Без indent для скорости
                json.dump(self.tagged_articles, f, ensure_ascii=False)
            
            logger.info(f"✅ Данные статей сохранены в кэш")
    
    def _compute_article_data(self):
        """Вычисление эмбеддингов статей и присвоение тегов."""
        logger.info(f"🧮 Вычисление эмбеддингов для {len(self.articles_texts)} статей...")
        
        # Вычисляем эмбеддинги статей
        self.article_embeddings = self.model.encode(
            self.articles_texts,
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=32
        )
        
        logger.info(f"✅ Эмбеддинги статей вычислены: {self.article_embeddings.shape}")
        
        # Вычисляем схожесть с тегами
        logger.info(f"🔄 Вычисление схожести статей с тегами...")
        similarities = cosine_similarity(self.article_embeddings, self.tag_embeddings)
        
        # Для каждой статьи выбираем топ тегов
        self.tagged_articles = []
        
        for i, text in enumerate(tqdm(self.articles_texts, desc="Присвоение тегов")):
            sim_scores = similarities[i]
            top_indices = np.argsort(sim_scores)[::-1][:self.tags_per_article]
            tags = []
            tag_scores = {}
            tag_positions = {}
            
            for position, idx in enumerate(top_indices):
                tag = self.tag_names[idx]
                score = float(sim_scores[idx])
                tags.append(tag)
                tag_scores[tag] = score
                tag_positions[tag] = position
            
            self.tagged_articles.append({
                "text": text[:500] + "..." if len(text) > 500 else text,  # укорачиваем для хранения
                "full_text_length": len(text),
                "tags": tags,
                "tag_scores": tag_scores,
                "tag_positions": tag_positions,
                "meta": self.articles_meta[i]
            })
        
        logger.info(f"✅ Теги присвоены всем статьям")
    
    def _init_bm25(self):
        """Инициализация BM25."""
        logger.info(f"🔧 Инициализация BM25...")
        tokenized_corpus = [text.split() for text in self.articles_texts]
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info(f"✅ BM25 готов")
    
    def _compute_idf(self):
        """Вычисление IDF весов для тегов."""
        if not self.tagged_articles:
            self.idf_weights = {tag: 1.0 for tag in self.tag_names}
            return
        
        n_docs = len(self.tagged_articles)
        df_counts = {tag: 0 for tag in self.tag_names}
        
        for article in self.tagged_articles:
            for tag in article.get("tags", []):
                if tag in df_counts:
                    df_counts[tag] += 1
        
        # IDF = log(N / (df + 1)) + 1 (сглаживание)
        self.idf_weights = {
            tag: np.log(n_docs / (df + 1)) + 1 
            for tag, df in df_counts.items()
        }
        
        logger.info(f"📊 IDF веса вычислены (редкие теги: {sum(df == 0 for df in df_counts.values())} шт.)")
    
    def get_tag_recommendations(self, text: str, k: Optional[int] = None) -> List[Tuple[str, float]]:
        """
        Получает рекомендации тегов для текста.
        
        Args:
            text: входной текст
            k: количество тегов (если None, используется self.tags_per_article)
        
        Returns:
            список кортежей (тег, оценка)
        """
        if not text or not text.strip():
            return []
            
        k = k or self.tags_per_article
        
        text_embedding = self.model.encode([text], normalize_embeddings=True)
        similarities = cosine_similarity(text_embedding, self.tag_embeddings)[0]
        
        top_indices = np.argsort(similarities)[::-1][:k]
        
        return [(self.tag_names[i], float(similarities[i])) for i in top_indices]
    
    def search(
        self,
        query: str,
        k: int = 10,
        semantic_weight: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск релевантных статей по запросу.
        
        Args:
            query: поисковый запрос
            k: количество результатов
            semantic_weight: вес семантики (если None, используется self.similarity_weight)
        
        Returns:
            список статей с оценками
        """
        if not self.tagged_articles:
            return []
        
        if not query or not query.strip():
            return []
        
        weight = semantic_weight if semantic_weight is not None else self.similarity_weight
        
        # 1. Получаем теги запроса с весами
        query_tags = self.get_tag_recommendations(query, k=self.tags_per_article * 2)
        
        # Применяем IDF веса и позиционный вес к оценкам тегов запроса
        # Вариант В: (1/sqrt(pos_query+1)) * (score * idf)
        query_tag_dict = {
            tag: (score * self.idf_weights.get(tag, 1.0)) / np.sqrt(pos + 1)
            for pos, (tag, score) in enumerate(query_tags)
        }
        
        # 2. BM25 scores
        if self.use_bm25:
            tokenized_query = query.split()
            bm25_scores = self.bm25.get_scores(tokenized_query)
            if np.max(bm25_scores) > 0:
                # Min-Max нормализация для стабильности
                bm25_scores = (bm25_scores - np.min(bm25_scores)) / (np.max(bm25_scores) - np.min(bm25_scores) + 1e-9)
        else:
            bm25_scores = np.zeros(len(self.tagged_articles))
        
        # 3. Комбинируем
        results = []
        for i, article in enumerate(self.tagged_articles):
            article_tags = article.get("tag_scores", {})
            article_tag_positions = article.get("tag_positions", {})
            
            # Семантическая оценка через теги (косинусное сходство + штраф)
            common_tags = set(query_tag_dict.keys()) & set(article_tags.keys())
            if common_tags:
                vec_q = np.array([query_tag_dict[t] for t in common_tags])
                vec_a = np.array([article_tags[t] for t in common_tags])
                
                # Косинусное сходство
                norm_q = np.linalg.norm(vec_q)
                norm_a = np.linalg.norm(vec_a)
                if norm_q > 0 and norm_a > 0:
                    cosine_sim = np.dot(vec_q, vec_a) / (norm_q * norm_a)
                else:
                    cosine_sim = 0.0
                
                # Штраф за размер пересечения
                fullness_coeff = len(common_tags) / self.tags_per_article
                semantic_score = cosine_sim * fullness_coeff
            else:
                semantic_score = 0.0
            
            # Комбинированная оценка
            combined_score = weight * semantic_score + (1 - weight) * bm25_scores[i]
            
            results.append({
                "text": article.get("text", ""),
                "full_text_length": article.get("full_text_length", 0),
                "tags": article.get("tags", []),
                "tag_scores": article.get("tag_scores", {}),
                "meta": article.get("meta", {}),
                "score": float(combined_score),
                "semantic_score": float(semantic_score),
                "bm25_score": float(bm25_scores[i]) if self.use_bm25 else 0.0
            })
        
        # Сортируем и берем кандидатов для переранжирования
        results.sort(key=lambda x: x["score"], reverse=True)
        candidates = results[:k * 5]
        
        # Переранжирование
        reranked = []
        tokenized_query = query.split()
        for res in candidates:
            # 1. BM25 (уже есть)
            # 2. Точное совпадение (премия)
            exact_match = 1.0 if query.lower() in res["text"].lower() else 0.0
            
            # 3. Позиция тегов (штраф, если теги глубоко)
            # Средняя позиция тегов в статье
            avg_pos = np.mean(list(res.get("tag_positions", {}).values())) if res.get("tag_positions") else 100
            position_bonus = 1.0 / (1.0 + np.log1p(avg_pos))
            
            # 4. Длина текста (премия)
            length_bonus = np.log1p(res.get("full_text_length", 0)) / 10.0
            
            # Формула переранживания
            rerank_score = (0.4 * res["score"] +
                            0.3 * res["bm25_score"] +
                            0.2 * exact_match +
                            0.1 * position_bonus +
                            0.05 * length_bonus)
            
            res["score"] = float(rerank_score)
            reranked.append(res)
            
        reranked.sort(key=lambda x: x["score"], reverse=True)
        return reranked[:k]
    
    def search_by_tags(self, query_tags: List[str], k: int = 10) -> List[Dict[str, Any]]:
        """
        Поиск статей по списку тегов (булев поиск).
        
        Args:
            query_tags: список тегов
            k: количество результатов
        
        Returns:
            список статей, отсортированных по количеству совпадений
        """
        if not self.tagged_articles:
            return []
        
        results = []
        for article in self.tagged_articles:
            article_tags = set(article.get("tags", []))
            matches = len(set(query_tags) & article_tags)
            
            if matches > 0:
                score = matches / len(query_tags) if query_tags else 0.0
                results.append({
                    "text": article.get("text", ""),
                    "tags": article.get("tags", []),
                    "meta": article.get("meta", {}),
                    "matches": matches,
                    "score": score
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика по движку."""
        return {
            "num_tags": len(self.tag_names),
            "num_categories": len(self.raw_tags),
            "num_articles": len(self.tagged_articles),
            "tags_per_article": self.tags_per_article,
            "use_bm25": self.use_bm25,
            "similarity_weight": self.similarity_weight,
            "cache_dir": str(self.cache_dir)
        }


# ================== Пример использования ==================
if __name__ == "__main__":
    # Инициализация
    searcher = LegalSemanticSearchEngine(
        tags_filepath="data/raw/base.json",
        laws_filepath="data/processed/laws.json",
        tags_per_article=400,
        similarity_weight=0.9
    )
    
    # Поиск
    query = """
"Банк обязан осуществлять операции по текущему (расчетному) банковскому счету в течение одного банковского дня. При нарушении указанного срока банк уплачивает клиенту пеню в размере 0,1 процента от суммы операции за каждый день просрочки."
это что-то нарушает?"""
    results = searcher.search(query, k=50)
    
    print(f"\n🔍 Запрос: '{query}'")
    print(f"Найдено статей: {len(results)}")
    
    for i, res in enumerate(results):
        print(f"\n{i+1}. [Score: {res['score']:.4f}]")
        print(f"   Источник: {res['meta'].get('source', 'unknown')}")
        print(f"   Теги: {', '.join(res['tags'][:5])}")
        print(f"   Текст: {res['text'][:200]}...")
    

    