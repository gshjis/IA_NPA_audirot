from bs4 import BeautifulSoup
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import re
import json
from src.collectors.parsers.base import BaseParser, DocumentMetadata, Article, Document, Section, Chapter, Part, Reference
from src.utils.logger import get_logger

logger = get_logger(__name__)

class UniversalHtmlParser(BaseParser):
    """Универсальный парсер HTML документов НПА с автоматическим определением структуры."""

    def can_parse(self, source: str | Path | bytes) -> bool:
        """Проверяет, является ли источник HTML."""
        logger.info(f"Проверка возможности парсинга источника: {type(source)}")
            # Если это строка
        if isinstance(source, str):
            # Проверяем, похоже ли это на HTML-код, а не на путь к файлу
            if source.strip().startswith('<') and ('<html' in source.lower() or '<!doctype' in source.lower()):
                return True
            # Иначе пробуем как путь к файлу
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    content = f.read()
                return '<html' in content.lower() or '<!doctype html' in content.lower()
            except:
                return False
                
        elif isinstance(source, (str, Path)):
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                return False
            return '<html' in content.lower() or '<!doctype html' in content.lower()
        elif isinstance(source, bytes):
            content = source.decode('utf-8', errors='ignore')
            return '<html' in content.lower() or '<!doctype html' in content.lower()
        return False

    def _load_html(self, source: str | Path | bytes) -> BeautifulSoup:
        """Загружает HTML из источника."""
        logger.info(f"Загрузка HTML из источника: {type(source)}")
        if isinstance(source, (str, Path)):
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()
        elif isinstance(source, bytes):
            content = source.decode('utf-8', errors='ignore')
        else:
            content = str(source)

        soup = BeautifulSoup(content, 'html.parser')
        return soup

    def parse_metadata(self, source: str | Path | bytes) -> DocumentMetadata:
        """Извлекает метаданные документа."""
        logger.info("Извлечение метаданных документа")
        soup = self._load_html(source)
        
        # Ищем заголовок
        title_tag = soup.find('title') or soup.find('h1')
        title = title_tag.get_text().strip() if title_tag else "Неизвестный документ"
        
        # Пытаемся определить тип документа
        doc_type = "НПА"
        if any(word in title.lower() for word in ['конституция', 'konst']):
            doc_type = "Конституция"
        elif any(word in title.lower() for word in ['кодекс', 'codex']):
            doc_type = "Кодекс"
        elif any(word in title.lower() for word in ['закон', 'law']):
            doc_type = "Закон"
        elif any(word in title.lower() for word in ['указ', 'decree']):
            doc_type = "Указ"
        elif any(word in title.lower() for word in ['постановление', 'resolution']):
            doc_type = "Постановление"
        
        # Эвристика для номера и даты
        number = ""
        date = ""
        lines = title.split()
        
        for i, line in enumerate(lines):
            if '№' in line:
                number = line
            if 'от' in line.lower() and i + 1 < len(lines):
                date = lines[i + 1] if 'от' in line.lower() else line
        
        return DocumentMetadata(
            title=title,
            document_type=doc_type,
            number=number,
            date=date
        )
    
    def _collect_article_text(self, start_element) -> str:
        text_parts = [start_element.get_text().strip()]
        
        current = start_element.next_sibling
        while current:
            if not hasattr(current, 'name'):
                current = current.next_sibling
                continue
            
            # Стоп-условия:
            # 1. Заголовок раздела/главы
            if current.name == 'h2':
                break
                
            # 2. Новая статья (параграф с <b> и словом "Статья")
            if current.name == 'p':
                b_tag = current.find('b')
                if b_tag and 'Статья' in b_tag.get_text():
                    break  # ← ВАЖНО: остановиться, не добавляя этот параграф
                else:
                    text_parts.append(current.get_text().strip())
            
            current = current.next_sibling
        
        return ' '.join(text_parts)
    
    def _extract_article_number_from_element(self, element) -> str:
        """
        Извлекает номер статьи, анализируя ВСЕ элементы в начале параграфа.
        """
        # Собираем все части номера из первых элементов
        number_parts = []
        
        # Перебираем непосредственных детей параграфа
        for child in element.children:
            if not hasattr(child, 'name'):
                continue
                
            if child.name == 'b':
                # Извлекаем текст из <b>
                b_text = child.get_text()
                # Ищем цифры
                digits = re.search(r'(\d+)', b_text)
                if digits:
                    number_parts.append(digits.group(1))
            
            elif child.name == 'sup':
                # Извлекаем цифру из <sup>
                sup_text = child.get_text()
                sup_digits = re.search(r'(\d+)', sup_text)
                if sup_digits:
                    number_parts.append(sup_digits.group(1))
            
            # Останавливаемся, если накопили достаточно или встретили точку
            if len(number_parts) >= 2 or (child.name == 'b' and '.' in child.get_text()):
                break
        
        # Формируем номер
        if len(number_parts) == 2:
            return f"{number_parts[0]}-{number_parts[1]}"
        elif len(number_parts) == 1:
            return number_parts[0]
        
        return ""

    def parse_structure(self, source: str | Path | bytes) -> List[Section]:
        """Основной метод - парсинг структуры документа с class='usercontent'."""
        logger.info("Парсинг структуры документа (новый метод)")
        soup = self._load_html(source)
        
        # Ищем контейнер
        container = soup.find(class_='usercontent')
        if not container:
            logger.warning("Контейнер 'usercontent' не найден, используем старый метод")
            return self._parse_structure_old(soup)
            
        sections: List[Section] = []
        current_section: Optional[Section] = None
        current_chapter: Optional[Chapter] = None
        current_article: Optional[Article] = None
        
        for element in container.find_all(['h2', 'p']):
            if element.name == 'h2':
                text = element.get_text().strip()
                if 'РАЗДЕЛ' in text.upper():
                    current_section = Section(
                        id=f"sec_{len(sections) + 1}",
                        title=text,
                        level=1
                    )
                    sections.append(current_section)
                    current_chapter = None
                elif 'ГЛАВА' in text.upper():
                    if not current_section:
                        current_section = Section(id="sec_default", title="Документ", level=1)
                        sections.append(current_section)
                    current_chapter = Chapter(
                        id=f"ch_{len(current_section.chapters) + 1}",
                        title=text,
                        level=2
                    )
                    current_section.chapters.append(current_chapter)
            elif element.name == 'p':
                # Получаем текст для предварительной проверки (только для скорости)
                text_preview = element.get_text().strip()
                if not text_preview:
                    continue
                
                # Проверяем, есть ли в параграфе <b> со словом "Статья" (признак начала новой статьи)
                b_tag = element.find('b')
                is_new_article = b_tag and 'Статья' in b_tag.get_text()
                
                if is_new_article:
                    # Это новая статья
                    if not current_section:
                        current_section = Section(id="sec_default", title="Документ", level=1)
                        sections.append(current_section)
                    
                    target = current_chapter if current_chapter else current_section
                    
                    # ИЗМЕНЕНИЕ 1: Используем новый метод для извлечения номера из HTML-структуры
                    article_number = self._extract_article_number_from_element(element)
                    
                    # ИЗМЕНЕНИЕ 2: Используем новый метод для сбора полного текста статьи
                    article_text = self._collect_article_text(element)
                    
                    article_id = f"art_{len(target.articles) + 1}"
                    current_article = Article(
                        id=article_id,
                        number=article_number,
                        text=article_text,
                        title=f"Статья {article_number}"
                    )
                    target.articles.append(current_article)
                    
                elif current_article:
                    # Это продолжение текста текущей статьи (без признака новой статьи)
                    current_article.text += " " + text_preview
                    
        return sections

    def _parse_structure_old(self, soup: BeautifulSoup) -> List[Section]:
        """Старый метод парсинга структуры."""
        soup = self._clean_html(soup)
        candidates = self._extract_heading_candidates(soup)
        filtered = self._filter_candidates(candidates)
        
        if not filtered:
            return self._create_flat_structure(soup)
        
        typed = []
        for cand in filtered:
            elem_type, level = self._detect_element_type(cand['text'])
            if elem_type:
                cand['type'] = elem_type
                cand['level'] = level
                typed.append(cand)
        
        if not typed:
            return self._create_flat_structure(soup)
        
        tree = self._build_hierarchy(typed)
        self._collect_text_for_nodes(tree, soup)
        return self._convert_tree_to_sections(tree)

    def _clean_html(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Удаляет мусор из HTML."""
        logger.debug("Очистка HTML от мусора")
        # Удаляем ненужные теги
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'meta', 'link']):
            tag.decompose()
        
        # Удаляем элементы с мусорными классами
        for tag in soup.find_all(class_=lambda x: x and any(
            kw in x.lower() for kw in ['nav', 'menu', 'footer', 'sidebar', 'comment', 'advert']
        )):
            tag.decompose()
        
        return soup

    def _extract_heading_candidates(self, soup: BeautifulSoup) -> List[Dict]:
        """Находит кандидатов в заголовки по весам."""
        logger.debug("Извлечение кандидатов в заголовки")
        candidates = []
        
        # H1-H6 (самые сильные кандидаты)
        for level in range(1, 7):
            for tag in soup.find_all(f'h{level}'):
                text = tag.get_text().strip()
                if text and len(text) < 300:
                    weight = 12 - level  # h1=11, h2=10, ...
                    candidates.append({
                        'element': tag,
                        'text': text,
                        'weight': weight,
                        'tag': f'h{level}',
                        'position': self._get_element_position(soup, tag)
                    })
        
        # Жирный текст в параграфах
        for tag in soup.find_all(['b', 'strong']):
            text = tag.get_text().strip()
            parent = tag.find_parent('p')
            if parent and 10 < len(text) < 200:
                weight = 7
                candidates.append({
                    'element': tag,
                    'text': text,
                    'weight': weight,
                    'tag': 'strong',
                    'position': self._get_element_position(soup, tag)
                })
        
        # Параграфы с заголовочными классами
        for tag in soup.find_all(class_=lambda x: x and any(
            kw in x.lower() for kw in ['title', 'header', 'heading', 'caption']
        )):
            text = tag.get_text().strip()
            if text and len(text) < 300:
                weight = 8
                candidates.append({
                    'element': tag,
                    'text': text,
                    'weight': weight,
                    'tag': tag.name,
                    'position': self._get_element_position(soup, tag)
                })
        
        # Параграфы, начинающиеся с цифры или ключевых слов
        for tag in soup.find_all('p'):
            text = tag.get_text().strip()
            if not text or len(text) > 300:
                continue
            
            first_word = text.split()[0] if text else ""
            if first_word and (first_word[0].isdigit() or any(
                kw in text.lower()[:20] for kw in ['раздел', 'глава', 'статья', 'пункт']
            )):
                weight = 6
                candidates.append({
                    'element': tag,
                    'text': text,
                    'weight': weight,
                    'tag': 'p',
                    'position': self._get_element_position(soup, tag)
                })
        
        # Сортируем по позиции
        return sorted(candidates, key=lambda x: x['position'])

    def _get_element_position(self, soup: BeautifulSoup, element) -> int:
        """Возвращает порядковый номер элемента в документе."""
        all_elements = soup.find_all(True)
        try:
            return all_elements.index(element)
        except ValueError:
            logger.warning(f"Элемент не найден в документе: {element.name}")
            return 0

    def _filter_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Фильтрует кандидатов, оставляя только лучших."""
        logger.debug(f"Фильтрация {len(candidates)} кандидатов в заголовки")
        if not candidates:
            return []
        
        # Берем кандидатов с весом > 6
        filtered = [c for c in candidates if c['weight'] > 6]
        
        # Если осталось мало, берем топ-20 по весу
        if len(filtered) < 3:
            filtered = sorted(candidates, key=lambda x: x['weight'], reverse=True)[:20]
        
        return sorted(filtered, key=lambda x: x['position'])

    def _detect_element_type(self, text: str) -> Tuple[Optional[str], int]:
        """Определяет тип и уровень по тексту."""
        logger.debug(f"Определение типа элемента: {text[:50]}...")
        text_upper = text.upper()
        
        # Разделы
        if re.search(r'РАЗДЕЛ\s+[IVXLCDM]+', text_upper):
            return 'section', 1
        if re.search(r'SECTION\s+\d+', text_upper):
            return 'section', 1
        
        # Главы
        if re.search(r'ГЛАВА\s+\d+', text_upper):
            return 'chapter', 2
        if re.search(r'CHAPTER\s+\d+', text_upper):
            return 'chapter', 2
        
        # Статьи
        if re.search(r'СТАТЬЯ\s+\d+', text_upper):
            return 'article', 3
        if re.search(r'ARTICLE\s+\d+', text_upper):
            return 'article', 3
        
        # Пункты (нумерованные)
        if re.match(r'^\d+\.', text.strip()):
            return 'clause', 4
        
        # Подпункты
        if re.match(r'^\d+\.\d+\.', text.strip()):
            return 'subclause', 5
        
        # Части
        if re.match(r'^[а-я]\)', text.lower()) or re.match(r'^[a-z]\)', text.lower()):
            return 'part', 6
        
        return None, 0

    def _build_hierarchy(self, elements: List[Dict]) -> List[Dict]:
        """Строит дерево иерархии."""
        logger.debug(f"Построение иерархии из {len(elements)} элементов")
        if not elements:
            return []
        
        root = []
        stack: list[Dict] = []
        
        for elem in elements:
            level = elem['level']
            elem['children'] = []
            elem['content_elements'] = []  # для сбора текста
            
            # Поднимаемся по стеку, пока не найдем родителя с меньшим уровнем
            while stack and stack[-1]['level'] >= level:
                stack.pop()
            
            if stack:
                # Добавляем как ребенка к последнему в стеке
                stack[-1]['children'].append(elem)
            else:
                # Добавляем в корень
                root.append(elem)
            
            stack.append(elem)
        
        return root

    def _collect_text_for_nodes(self, tree: List[Dict], soup: BeautifulSoup):
        """Собирает текст для каждого узла на основе позиций в HTML."""
        logger.debug("Сбор текста для узлов")
        all_elements = soup.find_all(True)
        
        def collect_for_node(node):
            # Находим позицию элемента узла
            try:
                start_pos = all_elements.index(node['element'])
            except ValueError:
                node['text_content'] = ""
                for child in node.get('children', []):
                    collect_for_node(child)
                return
            
            # Находим следующий элемент того же или более высокого уровня
            end_pos = len(all_elements)
            node_level = node['level']
            
            for i in range(start_pos + 1, len(all_elements)):
                current = all_elements[i]
                
                # Проверяем, не является ли текущий элемент заголовком
                is_heading = False
                for candidate in self._extract_heading_candidates_from_element(current):
                    if candidate.get('level', 10) <= node_level:
                        end_pos = i
                        is_heading = True
                        break
                
                if is_heading:
                    break
            
            # Собираем текст из элементов между start_pos и end_pos
            text_parts = []
            for i in range(start_pos + 1, end_pos):
                elem = all_elements[i]
                # Игнорируем сами заголовки
                is_heading = False
                for candidate in self._extract_heading_candidates_from_element(elem):
                    if 'element' in candidate and candidate['element'] == elem:
                        is_heading = True
                        break
                if is_heading:
                    continue
                text_parts.append(elem.get_text().strip())
            
            node['text_content'] = ' '.join(text_parts)
            
            # Рекурсивно для детей
            for child in node.get('children', []):
                collect_for_node(child)
        
        for node in tree:
            collect_for_node(node)

    def _extract_heading_candidates_from_element(self, element) -> List[Dict]:
        """Быстрая проверка, является ли элемент заголовком."""
        text = element.get_text().strip()
        if not text or len(text) > 300:
            return []
        
        candidates = []
        
        # Проверка по тегу
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = 11 - int(element.name[1])
            elem_type, _ = self._detect_element_type(text)
            if elem_type:
                candidates.append({
                    'element': element,
                    'level': level,
                    'type': elem_type
                })
        
        # Проверка по тексту
        elem_type, level = self._detect_element_type(text)
        if elem_type:
            candidates.append({
                'element': element,
                'level': level,
                'type': elem_type
            })
        
        return candidates

    def _convert_tree_to_sections(self, tree: List[Dict]) -> List[Section]:
        """Конвертирует дерево в объекты Section/Chapter/Article."""
        logger.info(f"Конвертация дерева ({len(tree)} узлов) в секции")
        sections: List[Section] = []
        
        def process_node(node, parent_section=None, parent_chapter=None):
            node_type = node.get('type')
            title = node['text']
            text = node.get('text_content', '')
            
            if node_type == 'section':
                section = Section(
                    id=f"sec_{len(sections) + 1}",
                    title=title,
                    level=1
                )
                sections.append(section)
                
                # Обрабатываем детей
                for child in node.get('children', []):
                    process_node(child, parent_section=section)
                    
            elif node_type == 'chapter':
                if parent_section:
                    # Создаем Chapter и добавляем в секцию
                    chapter = Chapter(
                        id=f"ch_{len(parent_section.chapters) + 1}",
                        title=title,
                        level=2
                    )
                    parent_section.chapters.append(chapter)
                    
                    # Обрабатываем детей (статьи)
                    for child in node.get('children', []):
                        process_node(child, parent_section=parent_section, parent_chapter=chapter)
                        
            elif node_type in ['article', 'clause', 'subclause', 'part']:
                # Определяем родителя (глава или секция)
                if parent_chapter:
                    target = parent_chapter
                elif parent_section:
                    target = parent_section
                else:
                    # Если нет родителя, создаем корневую секцию
                    if not sections:
                        sections.append(Section(
                            id="sec_root",
                            title="Документ",
                            level=1
                        ))
                    target = sections[-1]
                
                # Извлекаем номер статьи из текста
                number = self._extract_article_number(title)
                
                article = Article(
                    id=f"art_{len(target.articles) + 1}",
                    number=number,
                    text=text,
                    title=title
                )
                target.articles.append(article)
                
                # Извлекаем ссылки
                article.references = self.extract_references(text)
        
        for node in tree:
            process_node(node)
        
        return sections

    def _extract_article_number(self, title: str) -> str:
        """Извлекает номер статьи из заголовка."""
        logger.debug(f"Извлечение номера статьи из: {title[:50]}...")
        
        # Преобразуем HTML <sup>...N...</sup> в -N, игнорируя вложенные теги
        title = re.sub(r'<sup[^>]*>.*?(\d+).*?</sup>', r'-\1', title, flags=re.DOTALL)
        
        # Преобразуем Юникод-индексы
        unicode_map = {'¹': '-1', '²': '-2', '³': '-3', '⁴': '-4', '⁵': '-5', '⁶': '-6'}
        for char, replacement in unicode_map.items():
            title = title.replace(char, replacement)
        
        # Статья 45 или Статья 89-4
        match = re.search(r'(?:Статья|СТАТЬЯ|статья)\s+(\d+(?:-\d+)?)', title, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Если ничего не нашли — возвращаем пустую строку, не обрезаем
        return ""

    def _create_flat_structure(self, soup: BeautifulSoup) -> List[Section]:
        """Создает плоскую структуру, если не удалось определить иерархию."""
        logger.warning("Создание плоской структуры документа")
        section = Section(
            id="sec_flat",
            title="Документ",
            level=1
        )
        
        # Берем все параграфы как статьи
        for i, p in enumerate(soup.find_all('p')):
            text = p.get_text().strip()
            if text and len(text) > 20:  # игнорируем слишком короткие
                article = Article(
                    id=f"art_{i+1}",
                    number=f"{i+1}",
                    text=text,
                    title=""
                )
                section.articles.append(article)
        
        return [section]

    def parse_articles(self, source: str | Path | bytes) -> List[Article]:
        """Извлекает все статьи из документа."""
        logger.info("Извлечение всех статей")
        sections = self.parse_structure(source)
        articles = []
        for section in sections:
            articles.extend(section.articles)
        logger.info(f"Извлечено {len(articles)} статей")
        return articles

    def extract_references(self, text: str) -> List[Reference]:
        """Находит ссылки на другие НПА в тексте."""
        logger.debug(f"Поиск ссылок в тексте длиной {len(text)} символов")
        references: List[Reference] = []
        
        if not text:
            return references
        
        # Паттерны для белорусских НПА (без коротких аббревиатур)
        patterns = [
            # Закон № 130-З
            (r'(Закон|ЗАКОН)\s+(?:Республики\s+Беларусь\s+)?(?:от\s+\d{1,2}\s+\w+\s+\d{4}\s+г?\.?)?\s*№\s*([\d-]+[А-Я]?)', 'law'),
            
            # Указ № 100
            (r'(Указ|УКАЗ)\s+(?:Президента\s+(?:Республики\s+Беларусь\s+)?)?(?:от\s+\d{1,2}\s+\w+\s+\d{4}\s+г?\.?)?\s*№\s*([\d-]+)', 'decree'),
            
            # Постановление № 123
            (r'(Постановление|ПОСТАНОВЛЕНИЕ)\s+(?:Совета\s+Министров\s+)?(?:Республики\s+Беларусь\s+)?(?:от\s+\d{1,2}\s+\w+\s+\d{4}\s+г?\.?)?\s*№\s*([\d-]+)', 'resolution'),
            
            # Полные названия кодексов
            (r'(Трудовой\s+кодекс|Гражданский\s+кодекс|Уголовный\s+кодекс)', 'codex'),
            
            # Конституция
            (r'(Конституция|КОНСТИТУЦИЯ)', 'constitution')
        ]
        
        for pattern, ref_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start, end = match.span()
                
                # Формируем ID документа (упрощенно)
                doc_id = match.group(0).replace(' ', '_')[:50]
                
                ref = Reference(
                    document_id=doc_id,
                    title=match.group(0),
                    context=text[max(0, start-50):min(len(text), end+50)].strip(),
                    start_pos=start,
                    end_pos=end
                )
                references.append(ref)
        
        # Добавляем внутренние ссылки
        references.extend(self.extract_internal_references(text))
        
        # Удаляем дубликаты (по позиции)
        unique_refs: List[Reference] = []
        seen_positions = set()
        for ref in references:
            pos_key = (ref.start_pos, ref.end_pos)
            if pos_key not in seen_positions:
                seen_positions.add(pos_key)
                unique_refs.append(ref)
        
        return unique_refs

    def extract_internal_references(self, text: str) -> List[Reference]:
        # 1. Заменяем юникод-индексы
        unicode_map = {'¹': '-1', '²': '-2', '³': '-3', '⁴': '-4', '⁵': '-5', '⁶': '-6'}
        for char, replacement in unicode_map.items():
            text = text.replace(char, replacement)
        
        # 2. Заменяем HTML-индексы
        text = re.sub(r'<sup[^>]*>.*?(\d+).*?</sup>', r'-\1', text, flags=re.DOTALL)
        
        # 3. Ищем паттерны
        pattern = r'(?:стать[яею]|ст\.)\s+(\d+(?:-\d+)?)'
        
        references = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            article_num = match.group(1)
            references.append(Reference(
                document_id="self",
                title=match.group(0),
                context=text[max(0, match.start()-20):min(len(text), match.end()+20)],
                start_pos=match.start(),
                end_pos=match.end()
            ))
        return references

    def parse_parts(self, article_text: str) -> List[Part]:
        """Разбивает статью на части/пункты."""
        logger.debug(f"Разбор статьи на части, длина текста: {len(article_text)}")
        parts: List[Part] = []
        
        if not article_text:
            return parts
        
        # Ищем нумерованные пункты (1., 2., 1.1., а), б))
        patterns = [
            r'(\d+\.)\s+([^\.]+\.?)',  # 1. текст
            r'(\d+\.\d+\.)\s+([^\.]+\.?)',  # 1.1. текст
            r'([а-я]\))\s+([^\.]+\.?)',  # а) текст
            r'([a-z]\))\s+([^\.]+\.?)'  # a) текст
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, article_text, re.IGNORECASE):
                part = Part(
                    number=match.group(1),
                    text=match.group(2).strip()
                )
                parts.append(part)
        
        return parts

    def save_to_json(self, sections: List[Section], output_path: str | Path):
        """Сохраняет структуру документа в JSON файл."""
        logger.info(f"Сохранение структуры документа в {output_path}")
        
        def section_to_dict(section: Section) -> Dict[str, Any]:
            return {
                "id": section.id,
                "title": section.title,
                "level": section.level,
                "chapters": [chapter_to_dict(ch) for ch in section.chapters],
                "articles": [article_to_dict(art) for art in section.articles]
            }
            
        def chapter_to_dict(chapter: Chapter) -> Dict[str, Any]:
            return {
                "id": chapter.id,
                "title": chapter.title,
                "level": chapter.level,
                "articles": [article_to_dict(art) for art in chapter.articles]
            }
            
        def article_to_dict(article: Article) -> Dict[str, Any]:
            return {
                "id": article.id,
                "number": article.number,
                "title": article.title,
                "text": article.text,
                "references": [ref_to_dict(ref) for ref in article.references]
            }
            
        def ref_to_dict(ref: Reference) -> Dict[str, Any]:
            return {
                "document_id": ref.document_id,
                "title": ref.title,
                "context": ref.context,
                "start_pos": ref.start_pos,
                "end_pos": ref.end_pos
            }
            
        data = [section_to_dict(s) for s in sections]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info("Документ успешно сохранен в JSON")