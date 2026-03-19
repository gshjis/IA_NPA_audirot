from search.engine import LegalSemanticSearchEngine
import numpy as np

# Инициализация
searcher = LegalSemanticSearchEngine(
    tags_filepath="data/raw/base.json",
    laws_filepath="data/processed/laws.json",
    tags_per_article=400,
    similarity_weight=0.7, 
)

# Диагностика
query = "ипотека в беларуси документы"
print(f"\n🔍 Запрос: '{query}'")

# 1. Посмотрим, какие теги рекомендуются для запроса
query_tags = searcher.get_tag_recommendations(query, k=100)
print(f"Рекомендуемые теги для запроса: {query_tags}")

# 2. Посмотрим результаты поиска
results = searcher.search(query, k=50)
print(f"\nНайдено статей: {len(results)}")

for i, res in enumerate(results):
    print(f"\n{i+1}. [Score: {res['score']:.4f}] [Sem: {res['semantic_score']:.4f}] [BM25: {res['bm25_score']:.4f}]")
    print(f"   Источник: {res['meta'].get('source', 'unknown')}")
    print(f"   Теги: {', '.join(res['tags'][:5])}")
    print(f"   Текст: {res['text'][:100]}...")
