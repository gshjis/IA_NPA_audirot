import logging
import sys
from pathlib import Path

def setup_logger(name="IA_NPA_auditor", log_file="logs/app.log"):
    # Создаем директорию для логов, если её нет
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Добавляем эмодзи в зависимости от уровня
    class EmojiFormatter(logging.Formatter):
        def format(self, record):
            if record.levelno == logging.INFO:
                record.msg = f"ℹ️ {record.msg}"
            elif record.levelno == logging.WARNING:
                record.msg = f"⚠️ {record.msg}"
            elif record.levelno == logging.ERROR:
                record.msg = f"❌ {record.msg}"
            elif record.levelno == logging.DEBUG:
                record.msg = f"🔍 {record.msg}"
            return super().format(record)

    formatter = EmojiFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Логирование в файл
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Логирование в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    # Используем стандартный форматтер для файла, а для консоли можно оставить тот же
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Создаем глобальный экземпляр
logger = setup_logger()
