import collections
import matplotlib.pyplot as plt
import pymorphy3
import Stemmer
from typing import List, Tuple

# Инициализация
morph = pymorphy3.MorphAnalyzer()
stemmer = Stemmer.Stemmer("russian")

# Минимальный список стоп-слов (можно расширить)
RUSSIAN_STOPWORDS = {
    'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то', 'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'ее', 'мне', 'было', 'вот', 'от', 'еще', 'нет', 'о', 'из', 'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг', 'ли', 'если', 'уже', 'или', 'ни', 'быть', 'был', 'него', 'до', 'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь', 'там', 'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут', 'где', 'есть', 'надо', 'ней', 'для', 'мы', 'тебя', 'их', 'чем', 'была', 'сам', 'чтоб', 'без', 'будто', 'чего', 'раз', 'тоже', 'себе', 'под', 'будет', 'ж', 'тогда', 'кто', 'этот', 'того', 'потому', 'этого', 'какой', 'совсем', 'ним', 'здесь', 'этом', 'один', 'почти', 'мой', 'тем', 'чтобы', 'нее', 'сейчас', 'были', 'куда', 'зачем', 'всех', 'никогда', 'можно', 'при', 'наконец', 'два', 'об', 'другой', 'хоть', 'после', 'над', 'больше', 'тот', 'через', 'эти', 'нас', 'про', 'всего', 'них', 'какая', 'много', 'разве', 'три', 'эту', 'моя', 'впрочем', 'хорошо', 'свою', 'этой', 'перед', 'иногда', 'лучше', 'чуть', 'том', 'нельзя', 'такой', 'им', 'более', 'всегда', 'конечно', 'всю', 'между'
}

def analyze_documents(documents: List[str]) -> None:
    """Анализ с точки зрения BM25 (только стемминг)"""
    all_words = []
    
    for doc in documents:
        words = doc.lower().split()
        for word in words:
            word = word.strip('.,!?:;"()[]{}')
            if word and word not in RUSSIAN_STOPWORDS:
                # Только стемминг (как в BM25)
                stem = stemmer.stemWord(word)
                all_words.append(stem)
    
    # Частотный словарь
    word_counts = collections.Counter(all_words)
    
    # Вывод словаря
    print("Словарь частоты:")
    for word, count in word_counts.most_common():
        print(f"{word}: {count}")
        
    # Построение бар-плота
    most_common: List[Tuple[str, int]] = word_counts.most_common()
    if not most_common:
        print("Нет данных для построения графика.")
        return
        
    words_list, counts_list = zip(*most_common)
    
    plt.figure(figsize=(12, 6))
    plt.bar(words_list, counts_list)
    plt.xticks(rotation=45, ha='right')
    plt.title('Топ-20 наиболее частых слов (стеммы)')
    plt.xlabel('Слова')
    plt.ylabel('Частота')
    plt.tight_layout()
    plt.show()
