import logging
from typing import Optional

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Создает или возвращает логгер с предустановленной конфигурацией.
    
    Args:
        name: Имя логгера (по умолчанию __name__ вызывающего модуля)
        
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Базовая конфигурация если не настроено
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger