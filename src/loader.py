import json
import pathlib
from typing import Any, Union

def load_json(file_path: Union[str, pathlib.Path]) -> Any:
    """
    Загружает данные из JSON файла.

    Args:
        file_path (Union[str, pathlib.Path]): Путь к JSON файлу.

    Returns:
        Any: Содержимое JSON файла.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
