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

# Загрузка данных
data_path = Path("data/raw/base.json")
if not data_path.exists():
    print(f"Файл {data_path} не найден.")
    exit()

with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Извлечение всех тегов в плоский список
all_tags = []
tag_mapping = [] # Для отслеживания, какой тег какому ключу принадлежит

for category, tags in data.items():
    for tag in tags:
        all_tags.append(tag)
        tag_mapping.append({"category": category, "tag": tag})

print(f"Всего тегов: {len(all_tags)}")

# Вычисление эмбеддингов с прогресс-баром
print("Вычисление эмбеддингов...")
embeddings = model.encode(
    all_tags, 
    normalize_embeddings=True, 
    show_progress_bar=True
)

# Сохранение эмбеддингов и метаданных
output_embeddings_path = "tag_embeddings.npy"
output_mapping_path = "tag_mapping.json"

np.save(output_embeddings_path, embeddings)
with open(output_mapping_path, 'w', encoding='utf-8') as f:
    json.dump(tag_mapping, f, ensure_ascii=False, indent=4)

print(f"Эмбеддинги сохранены в {output_embeddings_path}")
print(f"Маппинг тегов сохранен в {output_mapping_path}")
