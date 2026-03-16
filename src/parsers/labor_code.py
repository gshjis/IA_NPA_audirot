import re
import json
import os

def parse_labor_code(file_path, output_json_path):
    """
    Парсит текстовый файл с Трудовым кодексом и сохраняет статьи в JSON.

    Args:
        file_path (str): Путь к исходному текстовому файлу.
        output_json_path (str): Путь для сохранения результирующего JSON-файла.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {file_path}")
        return
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return

    # Регулярное выражение для поиска статей.
    # Ищет: "Статья X. Текст..." и захватывает номер и весь контент до следующей статьи или конца строки/файла.
    # Флаг re.DOTALL позволяет точке (.) захватывать символы новой строки.
    # Используем re.MULTILINE для корректной работы ^ и $, если потребуется.
    article_pattern = re.compile(
        r'^Статья\s+(\d+(?:-\d+)?)\.\s+(.+?)(?=^Статья\s+\d+|\Z)',
        re.DOTALL | re.MULTILINE
    )

    # Регулярное выражение для поиска разделов. Ищет: "РАЗДЕЛ X ...".
    section_pattern = re.compile(r'^РАЗДЕЛ\s+([A-Z]+)\s+(.+?)$', re.MULTILINE)

    # Регулярное выражение для поиска глав. Ищет: "Глава X ...".
    chapter_pattern = re.compile(r'^Глава\s+(\d+)\s+(.+?)$', re.MULTILINE)

    # Находим все разделы, главы и статьи
    sections = list(section_pattern.finditer(text))
    chapters = list(chapter_pattern.finditer(text))
    articles = list(article_pattern.finditer(text))

    # Если не удалось найти статьи по основному шаблону, пробуем запасной вариант
    # (для случаев, когда после номера статьи нет точки)
    if not articles:
        print("Основной шаблон не сработал, пробую запасной...")
        article_pattern_alt = re.compile(
            r'^Статья\s+(\d+(?:-\d+)?)\s+(.+?)(?=^Статья\s+\d+|\Z)',
            re.DOTALL | re.MULTILINE
        )
        articles = list(article_pattern_alt.finditer(text))

    if not articles:
        print("Не найдено ни одной статьи. Проверьте структуру файла.")
        # Для отладки можно вывести первые 500 символов
        # print(text[:500])
        return

    print(f"Найдено разделов: {len(sections)}")
    print(f"Найдено глав: {len(chapters)}")
    print(f"Найдено статей: {len(articles)}")

    parsed_data = []
    current_section_num = 0
    current_section_title = ""
    section_index = 0
    chapter_index = 0

    # Проходим по всем найденным статьям
    for i, article_match in enumerate(articles):
        article_num_str = article_match.group(1).strip() # Номер статьи (как строка, например, "1" или "2611")
        article_content_full = article_match.group(2).strip() # Полный текст статьи

        # Извлекаем только первый абзац или заголовок статьи для чистоты (до первого переноса строки)
        # Но по заданию нужно сохранять весь контент статьи, поэтому оставляем как есть.
        # Однако часто после номера идет заголовок. Можно отделить заголовок от текста, если нужно.
        # В данном случае оставляем весь content как есть.
        article_content = article_content_full

        # Определяем, к какому разделу относится статья.
        # Ищем ближайший раздел, который начинается до текущей статьи.
        # Используем article_match.start() для получения позиции начала статьи в тексте.
        article_start_pos = article_match.start()
        current_section_num = 0
        current_section_title = ""
        for s in sections:
            if s.start() < article_start_pos:
                section_title_parts = s.group(2).strip().split('\n')
                current_section_title = section_title_parts[0] if section_title_parts else s.group(2).strip()
                # Преобразуем римскую цифру в арабскую (I, II, III, IV, V, VI)
                roman_num = s.group(1).strip()
                roman_to_arabic = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6}
                current_section_num = roman_to_arabic.get(roman_num, 0)
            else:
                break

        # Определяем, к какой главе относится статья.
        # Ищем ближайшую главу, которая начинается до текущей статьи.
        current_chapter_num = 0
        for ch in chapters:
            if ch.start() < article_start_pos:
                # Извлекаем номер главы (арабская цифра)
                chapter_num_str = ch.group(1).strip()
                try:
                    current_chapter_num = int(chapter_num_str)
                except ValueError:
                    current_chapter_num = 0 # На случай, если номер не число
            else:
                break

        # Пытаемся преобразовать номер статьи в целое число для сортировки,
        # но оставляем как строку в итоговом словаре.
        try:
            # Убираем возможные суффиксы типа "1", "11", "2611" и т.д. - они останутся частью строки
            article_num_display = article_num_str
        except ValueError:
            article_num_display = article_num_str

        # Создаем запись
        entry = {
            "source": "Трудовой кодекс",
            "section": current_section_num,
            "chapter": current_chapter_num,
            "number": article_num_display,
            "content": article_content
        }
        parsed_data.append(entry)

    # Проверка на случай, если статьи не сгруппированы по разделам/главам (все section=0, chapter=0)
    all_sections_zero = all(item['section'] == 0 for item in parsed_data)
    all_chapters_zero = all(item['chapter'] == 0 for item in parsed_data)

    if all_sections_zero:
        print("Предупреждение: Не удалось определить разделы для статей. Поле 'section' заполнено нулями.")
    if all_chapters_zero:
        print("Предупреждение: Не удалось определить главы для статей. Поле 'chapter' заполнено нулями.")

    # Запись в JSON файл
    try:
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(parsed_data, json_file, ensure_ascii=False, indent=4)
        print(f"Успешно сохранено {len(parsed_data)} статей в файл: {output_json_path}")
    except Exception as e:
        print(f"Ошибка при записи JSON файла: {e}")

# Пример использования
if __name__ == "__main__":
    # Предположим, что файл с кодексом находится в той же папке и называется 'tk.txt'
    input_filename = '/home/gshjis/Python_projects/IA_NPA_auditor/data/raw/labor_code.txt' # Замените на имя вашего файла
    output_filename = '/home/gshjis/Python_projects/IA_NPA_auditor/data/processed/labor_code.json'

    # Проверяем, существует ли входной файл
    if os.path.exists(input_filename):
        parse_labor_code(input_filename, output_filename)
    else:
        print(f"Входной файл '{input_filename}' не найден в текущей директории.")
        print("Создайте файл или укажите правильный путь.")