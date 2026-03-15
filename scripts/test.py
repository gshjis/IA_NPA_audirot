# %%
import sys
sys.path.insert(0, '..')

from src.search.engine import LegalSemanticSearchEngine
from src.loader import load_json
# %%ё
# Загружаем статьи
raw_D = load_json("/home/gshjis/Python_projects/IA_NPA_auditor/data/processed/const.json")
articles = [r["content"] for r in raw_D]

# СОЗДАЕМ engine - здесь уже происходит тегирование корпуса!
tagger = LegalSemanticSearchEngine(
    tags_filepath="/home/gshjis/Python_projects/IA_NPA_auditor/data/raw/base.json", 
    training_corpus=articles
)

# НЕ НУЖНО вызывать assign_tags снова - корпус уже протегирован
# tagged = tagger.assign_tags(articles)  # ← эту строку можно удалить

# Сразу переходим к тестированию
test_queries = [
    "Как наследуется квартира?",
    "Вправе ли административно-территориальная единица в одностороннем порядке сецессировать из состава унитарного государства на основании результатов локального плебисцита?",
    # ... остальные запросы
]

# %%
# ============================================================================
# СЕМАНТИЧЕСКИЙ ТЕСТ КОНСТИТУЦИИ
# ============================================================================

print("=" * 80)
print("🔍 ТЕСТИРОВАНИЕ СЕМАНТИЧЕСКОГО ПОИСКА".center(80))
print("=" * 80)

for idx, query in enumerate(test_queries, 1):
    
    print(f"\n{'-' * 80}")
    print(f"📌 ЗАПРОС №{idx}: {query}")
    print(f"{'-' * 80}")
    
    # Поиск топ-3 статей
    results = tagger.find_articles_by_new_sentence(query, k=5)
    
    if not results:
        print("❌ НИЧЕГО НЕ НАЙДЕНО")
        continue
    
    for rank, res in enumerate(results, 1):
        if res['score'] >= 0.8:
            icon = "🟢🔝"
        elif res['score'] >= 0.6:
            icon = "🟡"
        else:
            icon = "⚪"
        
        print(f"\n{icon} [{rank}] РЕЛЕВАНТНОСТЬ: {res['score']:.3f}")
        print(f"   {res['text'][:300]}...")
    
    print(f"\n{'-' * 80}")

print("\n" + "=" * 80)
print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО".center(80))
print("=" * 80)