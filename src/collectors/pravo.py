import json
from dataclasses import asdict
from src.collectors.urls import *
import requests
from .parsers.html import UniversalHtmlParser

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Скачиваем
page = requests.get(url=constitution_url, headers=headers)
html_code = page.content

# Парсим
parser = UniversalHtmlParser()
result = parser.parse(html_code)

# СОХРАНЯЕМ В JSON (ВОТ ТУТ)
parser.save_to_json(result.sections, 'constitution.json')

print("Готово! Файл constitution.json создан")