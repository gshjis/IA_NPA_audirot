from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import numpy as np
import json
from pathlib import Path

# Используем уже загруженную модель
model_name = 'DeepPavlov/rubert-base-cased-sentence'
cache_folder = "data/processed/cache/engine"  # Путь где лежит модель

print(f"Загрузка модели {model_name} из {cache_folder}...")
model = SentenceTransformer(model_name, cache_folder=cache_folder)

# Загрузка данных (пример пути)
data_path = Path("data/processed/laws.json")
if not data_path.exists():
    print(f"Файл {data_path} не найден.")
    exit()

with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Извлечение текстов
texts = [item["content"] if isinstance(item, dict) else item for item in data]
print(f"Всего текстов: {len(texts)}")

# Вычисление эмбеддингов с прогресс-баром
print("Вычисление эмбеддингов...")
embeddings = model.encode(
    texts, 
    normalize_embeddings=True, 
    show_progress_bar=True
)

# Сохранение
output_path = "article_embeddings.npy"
np.save(output_path, embeddings)
print(f"Эмбеддинги сохранены в {output_path}")
