import pymorphy3
import nltk
from typing import List
from nltk.corpus import stopwords

# Загрузка необходимых ресурсов NLTK
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
morph = pymorphy3.MorphAnalyzer()
stop_words = set(stopwords.words('russian'))

def get_keywords(text: str) -> List[str]:
    """
    Извлекает ключевые слова (существительные и прилагательные) из текста.
    """
    words = nltk.word_tokenize(text.lower())
    
    # Лемматизация и фильтрация
    keywords = []
    for word in words:
        if word.isalnum() and word not in stop_words:
            p = morph.parse(word)[0]
            if p.tag.POS in ['NOUN', 'ADJF', 'ADJS']:
                keywords.append(p.normal_form)
    
    return list(set(keywords))

print(get_keywords("Родители обязаны предоставлять юридическую помощь своим детям."))
