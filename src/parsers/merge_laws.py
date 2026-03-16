import json
import os
from src.logger import logger

def merge_laws(input_files: list, output_file: str):
    """
    Объединяет несколько JSON-файлов с законами в один файл.
    """
    merged_data = []
    
    for file_path in input_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        merged_data.extend(data)
                        logger.info(f"Добавлено {len(data)} статей из {file_path}")
                    else:
                        logger.warning(f"Предупреждение: {file_path} не содержит список статей.")
                except json.JSONDecodeError:
                    logger.error(f"Ошибка: Не удалось прочитать JSON из {file_path}")
        else:
            logger.warning(f"Предупреждение: Файл {file_path} не найден.")
            
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)
        
    logger.info(f"Успешно объединено {len(merged_data)} статей в {output_file}")

if __name__ == "__main__":
    files_to_merge = [
        "data/processed/const.json",
        "data/processed/labor_code.json"
    ]
    output = "data/processed/laws.json"
    merge_laws(files_to_merge, output)
