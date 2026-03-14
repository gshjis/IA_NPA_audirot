import json
from src.tagger import LegalSemanticTagger

def main():
    # Загрузка данных
    with open('data/processed/const.json', 'r', encoding='utf-8') as f:
        articles_data = json.load(f)
    
    articles_text = [a['content'] for a in articles_data]
    
    # Инициализация теггера
    tagger = LegalSemanticTagger(
        tags_filepath='data/raw/base.json',
        training_corpus=articles_text
    )
    
    # Пример поиска
    query = "Допустимо ли ограничение пассивного избирательного права для лиц, имеющих двойное гражданство?"
    results = tagger.find_articles_by_new_sentence(query, k=3)
    
    print(f"Результаты поиска для: '{query}'")
    for i, res in enumerate(results):
        print(f"{i+1}. Score: {res['score']:.4f} | Text: {res['text'][:100]}...")

if __name__ == "__main__":
    main()
