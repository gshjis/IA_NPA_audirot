import re
import json
from typing import List, Dict, Any

def parse_constitution_to_json(text: str) -> List[Dict[str, Any]]:
    """
    Парсит текст конституции в список словарей (статей),
    группируя их по разделам и главам.
    """
    # Регулярные выражения
    section_pattern = re.compile(r'РАЗДЕЛ\s+([IVXLCDM]+)', re.IGNORECASE)
    chapter_pattern = re.compile(r'ГЛАВА\s+(\d+)', re.IGNORECASE)
    article_pattern = re.compile(r'Статья\s+(\d+\.?\d*)\.', re.IGNORECASE)
    
    data: List[Dict[str, Any]] = []
    current_section: str = ""
    current_chapter: str = ""
    current_article: Dict[str, Any] = {}
    has_article: bool = False
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Проверка на раздел
        section_match = section_pattern.match(line)
        if section_match:
            current_section = section_match.group(1)
            current_chapter = ""
            has_article = False
            continue
            
        # Проверка на главу
        chapter_match = chapter_pattern.match(line)
        if chapter_match:
            current_chapter = chapter_match.group(1)
            has_article = False
            continue
            
        # Проверка на статью
        article_match = article_pattern.match(line)
        if article_match:
            article_number = article_match.group(1)
            
            current_article = {
                "section": current_section,
                "chapter": current_chapter,
                "number": article_number,
                "content": []
            }
            # Если после "Статья X." есть текст, добавляем его в контент
            remaining_text = line[article_match.end():].strip()
            if remaining_text:
                current_article["content"].append(remaining_text)
                
            data.append(current_article)
            has_article = True
        elif has_article:
            # Добавляем строку к содержимому текущей статьи
            current_article["content"].append(line)
            
    # Преобразуем список строк контента в одну строку
    for article in data:
        article["content"] = " ".join(article["content"])
            
    return data


def main():
    # Чтение из файла
    with open('data/raw/const.txt', 'r', encoding='utf-8') as f:
        text = f.read()
        
    # Парсинг
    articles = parse_constitution_to_json(text)
    
    # Запись в JSON
    with open('data/processed/const.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
        
    print("Конституция успешно преобразована в data/processed/const.json")

if __name__ == "__main__":
    main()
