import json
import pathlib
from src.logger import logger
from typing import Any, Union

def load_json(file_path: Union[str, pathlib.Path]) -> Any:
    """
    Загружает данные из JSON файла.

    Args:
        file_path (Union[str, pathlib.Path]): Путь к JSON файлу.

    Returns:
        Any: Содержимое JSON файла.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Файл {file_path} успешно загружен")
            return data
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла {file_path}: {e}")
        raise
