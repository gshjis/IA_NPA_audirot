from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from src.utils.logger import get_logger

logger = get_logger()

class SourceType(Enum):
    """Типы входных источников для парсера."""
    BYTES = "bytes"
    TEXT = "text"
    FILE_PATH = "file_path"
    STREAM = "stream"

@dataclass
class Chapter:
    """Глава документа."""
    id: str
    title: str
    level: int = 2  # Уровень вложенности (2 - глава)
    articles: List['Article'] = field(default_factory=list)

@dataclass
class Reference:
    """Ссылка на другой нормативно-правовой акт (НПА)."""
    document_id: str  # Уникальный идентификатор целевого НПА
    title: str        # Название документа
    context: str      # Контекст, в котором найдена ссылка
    start_pos: int    # Позиция начала в тексте
    end_pos: int      # Позиция конца в тексте
    article: Optional[str] = None  # Статья/пункт, на который ссылается


@dataclass
class DocumentMetadata:
    """Метаданные документа."""
    title: str
    document_type: str  # Закон, Постановление, Указ и т.д.
    number: str         # Номер документа
    date: str           # Дата принятия/публикации
    authority: Optional[str] = None  # Орган, издавший документ

@dataclass
class Section:
    """Раздел документа."""
    id: str
    title: str
    level: int  # Уровень вложенности (1 - высший)
    chapters: List['Chapter'] = field(default_factory=list) 
    articles: List['Article'] = field(default_factory=list)

@dataclass
class Article:
    """Статья документа."""
    id: str              # Уникальный ID в рамках документа (например, "article_5")
    number: str          # Номер статьи (например, "Статья 5")
    text: str            # Полный текст статьи
    title: Optional[str] = None  # Заголовок статьи (если есть)
    parts: List['Part'] = field(default_factory=list)  # Части/пункты внутри статьи
    references: List[Reference] = field(default_factory=list)

@dataclass
class Part:
    """Часть/пункт внутри статьи."""
    number: str  # Номер пункта (например, "1", "а)", "1.1")
    text: str
    references: List[Reference] = field(default_factory=list)

@dataclass
class Document:
    """Полная структура документа."""
    metadata: DocumentMetadata
    raw_text: str  # Полный текст документа без структуры (fallback)
    sections: List[Section] = field(default_factory=list)


class ParserError(Exception):
    """Базовое исключение для ошибок парсинга."""
    pass

class StructureMismatchError(ParserError):
    """Ошибка несоответствия ожидаемой структуры."""
    pass

class BaseParser(ABC):
    """
    Абстрактный базовый класс для парсеров страниц нормативно-правовых актов.
    
    Гарантирует:
    - Уникальные ID для статей в рамках документа
    - Сохранение порядка следования элементов
    - Полное сохранение текста (даже при сломанной структуре)
    """
    
    def __init__(self):
        self._article_counter = 0
    
    @abstractmethod
    def can_parse(self, source: Union[str, Path, bytes, Any]) -> bool:
        """
        Проверяет, может ли парсер обработать данный источник.
        
        Args:
            source: Входные данные (путь к файлу, байты, текст и т.д.)
        
        Returns:
            True если парсер подходит для этого источника.
        """
        pass
    
    @abstractmethod
    def parse_metadata(self, source: Union[str, Path, bytes, Any]) -> DocumentMetadata:
        """
        Извлекает метаданные документа.
        
        Args:
            source: Входные данные
            
        Returns:
            DocumentMetadata
            
        Raises:
            ParserError: Если метаданные не удалось извлечь
        """
        pass
    
    @abstractmethod
    def parse_structure(self, source: Union[str, Path, bytes, Any]) -> List[Section]:
        """
        Определяет иерархию документа (разделы, главы).
        
        Args:
            source: Входные данные
            
        Returns:
            Список разделов
            
        Raises:
            StructureMismatchError: Если структура не соответствует ожидаемой
        """
        pass
    
    @abstractmethod
    def parse_articles(self, source: Union[str, Path, bytes, Any]) -> List[Article]:
        """
        Извлекает все статьи документа с содержимым.
        
        Args:
            source: Входные данные
            
        Returns:
            Список статей
            
        Raises:
            ParserError
        """
        pass
    
    @abstractmethod
    def extract_references(self, text: str) -> List[Reference]:
        """
        Находит ссылки на другие НПА в тексте.
        
        Args:
            text: Текст для анализа
            
        Returns:
            Список найденных ссылок
        """
        pass
    
    def parse_parts(self, article_text: str) -> List[Part]:
        """
        Опциональный: разбивает текст статьи на части/пункты.
        
        Args:
            article_text: Текст статьи
            
        Returns:
            Список частей
        """
        logger.warning(f"parse_parts не реализован для {self.__class__.__name__}")
        return []
    
    def parse_tables(self, source: Union[str, Path, bytes, Any]) -> Dict[str, Any]:
        """
        Опциональный: извлекает таблицы из документа.
        
        Args:
            source: Входные данные
            
        Returns:
            Словарь таблиц {id: данные_таблицы}
        """
        logger.warning(f"parse_tables не реализован для {self.__class__.__name__}")
        return {}
    
    def parse(self, source: Union[str, Path, bytes, Any]) -> Document:
        """
        Основной метод парсинга: собирает все вместе.
        
        Args:
            source: Входные данные
            
        Returns:
            Полностью распарсенный Document
            
        Raises:
            ParserError: Любая ошибка парсинга
        """
        if not self.can_parse(source):
            raise ParserError(f"Парсер {self.__class__.__name__} не может обработать данный источник")
        
        try:
            metadata = self.parse_metadata(source)
            sections = self.parse_structure(source)
            articles = self.parse_articles(source)
            
            # Извлекаем ссылки из всех статей
            all_text = " ".join(article.text for article in articles)
            references = self.extract_references(all_text)
            
            # Распределяем ссылки по статьям и частям
            for article in articles:
                article_text = article.text
                article_refs = [r for r in references if r.start_pos >= article_text.find(article.text)]
                article.references = article_refs[:]
                
                # Парсим части если возможно
                article.parts = self.parse_parts(article.text)
            
            # Собираем Document
            doc = Document(
                metadata=metadata,
                sections=sections,
                raw_text=all_text
            )
            
            logger.info(f"Документ успешно распарсен: {metadata.title}")
            return doc
            
        except Exception as e:
            logger.error(f"Ошибка парсинга: {e}", exc_info=True)
            raise ParserError(f"Не удалось распарсить документ: {e}") from e
    
    def _generate_article_id(self, number: str) -> str:
        """Генерирует уникальный ID для статьи."""
        self._article_counter += 1
        return f"article_{self._article_counter:04d}_{number.replace(' ', '_')}"