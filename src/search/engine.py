import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
from src.logger import logger
from src.loader import load_json
from typing import Optional

class LegalSemanticSearchEngine:
    """
    Класс для присвоения научно обоснованных тегов статьям Конституции.
    Теги загружаются из внешнего JSON-файла.
    """

    def _compute_idf(self) -> Dict[str, float]:
        """
        Вычисляет IDF для каждого тега на основе размеченного корпуса.
        """
        if not self.tagged_corpus:
            return {tag: 1.0 for tag in self.tag_names}
        
        n_docs = len(self.tagged_corpus)
        idf = {}
        for tag in self.tag_names:
            # Считаем, в скольких статьях встречается тег
            df = sum(1 for article in self.tagged_corpus if tag in article.get("tags", []))
            # Формула IDF: log(N / (df + 1)) + 1
            idf[tag] = np.log(n_docs / (df + 1)) + 1
        return idf

    def __init__(
        self, 
        tags_filepath="data/raw/base.json", 
        model_name='deepvk/USER2-base', 
        training_corpus=None, 
        cache_dir="data/cache", 
        tags_per_article:int = 50
    ):
        """
        Инициализация движка поиска.

        Args:
            tags_filepath (str): Путь к JSON-файлу с тегами.
            model_name (str): Название модели SentenceTransformer.
            training_corpus (List[str], optional): Список статей для обучения.
            article_weights (Dict[int, float], optional): Веса статей для ранжирования.
            noisy_articles (List[int], optional): Список индексов статей, которые нужно игнорировать.
            cache_dir (str): Директория для кэширования моделей и эмбеддингов.
            threshold (float): Порог отсечения для тегов.
        """
        self.tags_per_article = tags_per_article
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем теги из JSON
        try:
            self.tag_keywords = load_json(tags_filepath)
            logger.info(f"Загружено {len(self.tag_keywords)} тегов из {tags_filepath}")
        except Exception as e:
            logger.error(f"Ошибка загрузки тегов из {tags_filepath}: {e}")
            self.tag_keywords = {}
        self.training_corpus = training_corpus or []
        
        if not self.tag_keywords:
            logger.error(f"Не удалось загрузить теги из {tags_filepath}")
            raise ValueError(f"Не удалось загрузить теги из {tags_filepath}")
        
        # Загружаем модель (локально)
        logger.info(f"Загрузка модели {model_name}...")
        # Попытка загрузки из локального кэша, если не удается - из интернета
        try:
            logger.info(f"Попытка загрузки модели из локального кэша: {model_name}...")
            self.model = SentenceTransformer(model_name, cache_folder=str(self.cache_dir / "models"), local_files_only=True)
        except Exception:
            logger.info(f"Модель не найдена локально, загрузка из интернета...")
            self.model = SentenceTransformer(model_name, cache_folder=str(self.cache_dir / "models"), local_files_only=False)
        logger.info("Модель загружена")
        
        # Преобразуем теги в описания для эмбеддингов
        self.tag_names = list(self.tag_keywords.keys())
        self.tag_descriptions = [". ".join(self.tag_keywords[tag]) for tag in self.tag_names]
        
        logger.info(f"Создано {len(self.tag_descriptions)} описаний тегов")
        
        # Вычисляем или загружаем эмбеддинги для тегов
        self.tag_embeddings = self._load_or_compute_embeddings("tag_embeddings.npy", self.tag_descriptions)
        
        # Предварительно вычисляем эмбеддинги корпуса для быстрого поиска
        self.tagged_corpus = []
        if self.training_corpus:
            logger.info("Тегирование обучающего корпуса...")
            # Извлекаем тексты для эмбеддингов
            texts = [article["content"] if isinstance(article, dict) else article for article in self.training_corpus]
            self.tagged_corpus = self.assign_tags(texts, tags_per_article=self.tags_per_article)
            
            # Сохраняем оригинальные объекты статей
            for i, article in enumerate(self.training_corpus):
                self.tagged_corpus[i]["original_data"] = article
            
            # Вычисляем или загружаем эмбеддинги статей
            self.article_embeddings = self._load_or_compute_embeddings("article_embeddings.npy", texts)
            
        # Вычисляем IDF веса
        self.idf_weights = self._compute_idf()
        logger.info("IDF веса вычислены")
        
        logger.info("Инициализация завершена")

    def _load_or_compute_embeddings(self, filename: str, texts: List[str]) -> np.ndarray:
        """
        Загружает эмбеддинги из кэша или вычисляет их, если кэш отсутствует.

        Args:
            filename (str): Имя файла кэша.
            texts (List[str]): Список текстов для эмбеддинга.

        Returns:
            np.ndarray: Массив эмбеддингов.
        """
        path = self.cache_dir / filename
        if path.exists():
            logger.info(f"Загрузка эмбеддингов из {path}...")
            return np.load(path)
        else:
            logger.info(f"Вычисление эмбеддингов и сохранение в {path}...")
            embeddings = self.model.encode(texts, normalize_embeddings=True)
            np.save(path, embeddings)
            return embeddings
    
    def assign_tags(self, articles_list: List[str], tags_per_article: int) -> List[Dict[str, Any]]:
        """
        Присваивает теги статьям на основе семантической близости.

        Args:
            articles_list (List[str]): Список текстов статей.
            tags_per_article (int): Максимальное количество тегов на статью.

        Returns:
            List[Dict[str, Any]]: Список словарей с информацией о тегах для каждой статьи.
        """
        logger.info(f"Вычисление эмбеддингов для {len(articles_list)} статей...")
        article_embeddings = self.model.encode(articles_list, normalize_embeddings=True)
        
        logger.info("Вычисление схожести с тегами...")
        similarities = cosine_similarity(article_embeddings, self.tag_embeddings)
        
        tagged_articles = []
        
        for i, article_text in enumerate(articles_list):
            sim_scores = similarities[i]
            top_indices = np.argsort(sim_scores)[::-1][:tags_per_article]
            
            article_tags = []
            tag_scores = {}
            
            for idx in top_indices:
                tag_name = self.tag_names[idx]
                score = float(sim_scores[idx])
                article_tags.append(tag_name)
                tag_scores[tag_name] = score
            
            tagged_articles.append({
                "text": article_text,
                "tags": article_tags,
                "tag_scores": tag_scores,
                "all_scores": {
                    self.tag_names[idx]: float(sim_scores[idx])
                    for idx in top_indices
                }
            })
        
        return tagged_articles
    
    def get_tag_recommendations(self, text: str) -> Dict[str, float]:
        """
        Получает рекомендации тегов для одного текста.

        Args:
            text (str): Входной текст.

        Returns:
            Dict[str, float]: Словарь {тег: оценка_релевантности}, ограниченный self.tags_per_article.
        """
        logger.info(f"Получение рекомендаций тегов для текста длиной {len(text)}...")
        text_embedding = self.model.encode([text], normalize_embeddings=True)
        similarities = cosine_similarity(text_embedding, self.tag_embeddings)[0]
        
        # Получаем индексы топ-N тегов
        top_indices = np.argsort(similarities)[::-1][:self.tags_per_article]
        
        recommendations = {}
        for i in top_indices:
            recommendations[self.tag_names[i]] = float(similarities[i])
        
        logger.info(f"Найдено {len(recommendations)} тегов")
        return dict(sorted(recommendations.items(), key=lambda x: x[1], reverse=True))

    def get_tag_recommendations_formatted(self, text: str) -> str:
        """
        Получает рекомендации тегов и возвращает их в виде отформатированной строки.

        Args:
            text (str): Входной текст.

        Returns:
            str: Отформатированная строка с тегами.
        """
        tags = self.get_tag_recommendations(text)
        if not tags:
            return "Теги не найдены."
            
        output = [f"\n🔍 ТЕГИ ДЛЯ ЗАПРОСА: '{text}'", "-" * 40]
        for tag, score in sorted(tags.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            output.append(f"   {tag:30} [{bar}] {score:.3f}")
        output.append("-" * 40)
        return "\n".join(output)


    def find_articles_by_new_sentence(self, new_sentence: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Находит топ-k статей, вычисляя косинусное сходство между вектором тегов
        нового предложения и вектором тегов каждой статьи, учитывая только теги запроса.

        Args:
            new_sentence (str): Запрос пользователя.
            k (int): Количество возвращаемых статей.

        Returns:
            List[Dict[str, Any]]: Список найденных статей с их оценками.
        """
        logger.info(f"Поиск статей для запроса: '{new_sentence[:50]}...'")
        if not self.tagged_corpus:
            logger.warning("Обучающий корпус пуст, поиск невозможен")
            return []
            
        # 1. Получаем теги и их релевантность для нового предложения
        query_tags_rec = self.get_tag_recommendations(new_sentence)
        
        # Преобразуем в вектор (numpy), учитывая только теги из запроса и IDF веса
        query_tags = list(query_tags_rec.keys())
        query_vector = np.array([query_tags_rec[tag] * self.idf_weights.get(tag, 1.0) for tag in query_tags])
        query_norm = np.linalg.norm(query_vector)
        
        if query_norm == 0:
            logger.warning("Вектор запроса пуст")
            return []
        
        # 2. Вычисляем косинусное сходство для каждой статьи
        results = []
        for i, article in enumerate(self.tagged_corpus):
            article_tags_rec = article.get("all_scores", {})
            
            # Векторы только по общим тегам (пересечение)
            common_tags = [tag for tag in query_tags if tag in article_tags_rec]
            
            if not common_tags:
                score = 0.0
            else:
                q_vec = np.array([query_tags_rec[tag] * self.idf_weights.get(tag, 1.0) for tag in common_tags])
                a_vec = np.array([article_tags_rec[tag] * self.idf_weights.get(tag, 1.0) for tag in common_tags])
                
                q_norm = np.linalg.norm(q_vec)
                a_norm = np.linalg.norm(a_vec)
                
                similarity = np.dot(q_vec, a_vec) / (q_norm * a_norm) if (q_norm > 0 and a_norm > 0) else 0.0
                
                # Покрытие запроса (доля веса запроса, покрытая статьей)
                coverage = np.sum(a_vec) / np.sum([query_tags_rec[tag] * self.idf_weights.get(tag, 1.0) for tag in query_tags])
                
                # Штраф за непокрытые теги запроса
                missing_tags_ratio = 1.0 - (len(common_tags) / len(query_tags))
                penalty = 0.5 * missing_tags_ratio
                
                # Итоговый score
                score = (0.4 * similarity + 0.6 * coverage) - penalty
                    
            results.append({
                "article": article.get("original_data", {"content": article["text"]}),
                "score": float(score),
                "query_tags": query_tags_rec,
                "article_tags": article.get("tag_scores", {}),
                "common_tags": common_tags
            })
            
        # 3. Сортируем и применяем базовый diversity
        results.sort(key=lambda x: x["score"], reverse=True)
        
        final_results = []
        seen_texts = set()
        for res in results:
            # Используем контент статьи для дедупликации
            article = res["article"]
            article_content = article.get("content", str(article)) if isinstance(article, dict) else str(article)
            if article_content not in seen_texts:
                final_results.append(res)
                seen_texts.add(article_content)
            if len(final_results) >= k:
                break
        
        logger.info(f"Найдено {len(final_results)} статей")
        return final_results
