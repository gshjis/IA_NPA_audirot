from src.core.comparator import Comparator

def test_comparator():
    comparator = Comparator()
    
    # Тест 1: Замена
    old = "это старый текст"
    new = "это новый текст"
    result = comparator.compare(old, new)
    print(f"Test 1: {result}")
    assert result == "это [старый/новый] текст"
    
    # Тест 2: Удаление
    old = "удалить это слово"
    new = "удалить слово"
    result = comparator.compare(old, new)
    print(f"Test 2: {result}")
    assert result == "удалить [это/] слово"
    
    # Тест 3: Вставка
    old = "добавить слово"
    new = "добавить новое слово"
    result = comparator.compare(old, new)
    print(f"Test 3: {result}")
    assert result == "добавить [/новое] слово"

    print("Все тесты пройдены успешно!")

if __name__ == "__main__":
    test_comparator()
