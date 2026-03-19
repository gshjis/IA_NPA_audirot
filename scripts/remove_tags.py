import json
import sys

def remove_tags(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Предполагаем, что данные - это список словарей
    for item in data:
        keys_to_remove = ['tags', 'tag_scores', 'all_scores', 'relevance_scores', '_meta']
        for key in keys_to_remove:
            if key in item:
                del item[key]
            
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Теги удалены. Результат сохранен в {output_file}")

if __name__ == "__main__":
    input_path = 'data/processed/merged_tagged_filtered.json'
    output_path = 'data/processed/merged_no_tags.json'
    remove_tags(input_path, output_path)
