
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
import json
import os

def load_tags_from_json(filepath="base.json"):
    """
    Загружает словарь тегов из JSON-файла.
    
    Parameters:
    -----------
    filepath : str
        Путь к JSON-файлу с тегами
        
    Returns:
    --------
    dict
        Словарь тегов с ключевыми словами
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tag_data = json.load(f)
        print(f"✓ Загружено {len(tag_data)} тегов из {filepath}")
        return tag_data
    except FileNotFoundError:
        print(f"✗ Файл {filepath} не найден")
        return {}
    except json.JSONDecodeError:
        print(f"✗ Ошибка парсинга JSON в {filepath}")
        return {}


class LegalSemanticTagger:
    """
    Класс для присвоения научно обоснованных тегов статьям Конституции.
    Теги загружаются из внешнего JSON-файла.
    """
    
    def __init__(self, tags_filepath="data/raw/base.json", model_name='paraphrase-multilingual-MiniLM-L12-v2', training_corpus=None, article_weights=None, noisy_articles=None):
        """
        Инициализация с загрузкой тегов из JSON и обучающим корпусом.
        """
        # Загружаем теги из JSON
        self.tag_keywords = load_tags_from_json(tags_filepath)
        self.training_corpus = training_corpus or []
        self.article_weights = np.ones(len(self.training_corpus))
        if article_weights:
            for idx, weight in article_weights.items():
                if 0 <= idx < len(self.article_weights):
                    self.article_weights[idx] = weight
        
        self.noisy_articles = set(noisy_articles or [])
        
        if not self.tag_keywords:
            raise ValueError(f"Не удалось загрузить теги из {tags_filepath}")
        
        # Загружаем модель
        print(f"Загрузка модели {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("Модель загружена")
        
        # Преобразуем теги в описания для эмбеддингов
        self.tag_names = list(self.tag_keywords.keys())
        self.tag_descriptions = [". ".join(self.tag_keywords[tag]) for tag in self.tag_names]
        
        print(f"Создано {len(self.tag_descriptions)} описаний тегов")
        
        # Вычисляем эмбеддинги для тегов (один раз)
        print("Вычисление эмбеддингов для тегов...")
        self.tag_embeddings = self.model.encode(self.tag_descriptions, normalize_embeddings=True)
        
        # Предварительно вычисляем эмбеддинги корпуса для быстрого поиска
        self.tagged_corpus = []
        if self.training_corpus:
            print("Тегирование обучающего корпуса...")
            self.tagged_corpus = self.assign_tags(self.training_corpus)
            
        print("Готово")
    
    def assign_tags(self, articles_list: List[str], tags_per_article: int = 15) -> List[Dict[str, Any]]:
        """
        Присваивает теги статьям на основе семантической близости.
        """
        print(f"Вычисление эмбеддингов для {len(articles_list)} статей...")
        article_embeddings = self.model.encode(articles_list, normalize_embeddings=True)
        
        print("Вычисление схожести с тегами...")
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
                    self.tag_names[j]: float(sim_scores[j]) 
                    for j in range(len(self.tag_names)) 
                    if sim_scores[j] > 0.2
                }
            })
        
        return tagged_articles
    
    def get_tag_recommendations(self, text: str, threshold: float = 0.2) -> Dict[str, float]:
        """
        Получить рекомендации тегов для одного текста.
        """
        text_embedding = self.model.encode([text], normalize_embeddings=True)
        similarities = cosine_similarity(text_embedding, self.tag_embeddings)[0]
        
        recommendations = {}
        for i, score in enumerate(similarities):
            if score >= threshold:
                recommendations[self.tag_names[i]] = float(score)
        
        return dict(sorted(recommendations.items(), key=lambda x: x[1], reverse=True))

    def find_articles_by_new_sentence(self, new_sentence: str, k: int = 5, expand_query: bool = False) -> List[Dict[str, Any]]:
        """
        Находит топ-k статей, вычисляя косинусное сходство между вектором тегов
        нового предложения и вектором тегов каждой статьи.
        """
        if not self.tagged_corpus:
            return []
            
        # 1. Получаем теги и их релевантность для нового предложения
        query = new_sentence
        if expand_query:
            tags_rec = self.get_tag_recommendations(new_sentence, threshold=0.5)
            synonyms = []
            for tag in tags_rec:
                synonyms.extend(self.tag_keywords.get(tag, []))
            if synonyms:
                query = f"{new_sentence}. {' '.join(set(synonyms))}"
        
        query_tags_rec = self.get_tag_recommendations(query, threshold=0.15)
        
        # Преобразуем в вектор (numpy)
        query_vector = np.array([query_tags_rec.get(tag, 0.0) for tag in self.tag_names])
        query_norm = np.linalg.norm(query_vector)
        
        if query_norm == 0:
            return []
        
        # 2. Вычисляем косинусное сходство для каждой статьи
        results = []
        for i, article in enumerate(self.tagged_corpus):
            article_tags_rec = article.get("all_scores", {})
            
            # Вектор статьи
            article_vector = np.array([article_tags_rec.get(tag, 0.0) for tag in self.tag_names])
            article_norm = np.linalg.norm(article_vector)
            
            if article_norm == 0:
                score = 0.0
            else:
                # Косинусное сходство: (A · B) / (||A|| * ||B||)
                score = np.dot(query_vector, article_vector) / (query_norm * article_norm)
            
            # Гибридный бонус: бонус за совпадение топ-3 тегов
            target_tags = sorted(query_tags_rec, key=lambda k: query_tags_rec[k], reverse=True)[:3]
            article_tag_set = set(article_tags_rec.keys())
            bonus = 0.0
            for tag in target_tags:
                if tag in article_tag_set:
                    bonus += 0.1
            score += bonus
            
            # Применяем фильтр шума и веса статей
            if i in self.noisy_articles:
                score = 0.0
            else:
                score *= self.article_weights.get(i, 1.0)
            
            results.append({
                "text": article["text"],
                "score": float(score)
            })
            
        # 3. Сортируем по убыванию релевантности и берем топ-k
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:k]
