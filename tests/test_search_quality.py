import sys
import os
import numpy as np
import json
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Добавляем корень проекта в sys.path
sys.path.append(os.getcwd())
from src.search.engine import LegalSemanticSearchEngine
from src.logger import logger
import requests


class SearchQualityTester:
    """
    Класс для тестирования качества поиска.
    
    Методология:
    1. Генерируем синтетическую статью, которая ссылается на КОНКРЕТНЫЕ существующие статьи
    2. Ищем по тексту этой статьи
    3. Проверяем, нашлись ли те статьи, на которые мы ссылались
    """
    
    def __init__(
        self,
        tags_filepath: str = "data/raw/base.json",
        laws_filepath: str = "data/processed/laws.json",
        cache_dir: str = "data/test_results",
        openrouter_key: Optional[str] = None
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        print("🚀 Инициализация поискового движка...")
        self.searcher = LegalSemanticSearchEngine(
            tags_filepath=tags_filepath,
            laws_filepath=laws_filepath,
            tags_per_article=600,
            similarity_weight=0.9
        )
        
        # Загружаем все статьи для поиска ссылок
        self.all_articles = self.searcher.laws_data
        
        # Индексируем статьи по источнику для быстрого доступа
        self.articles_by_source = {}
        for article in self.all_articles:
            source = article.get("source")
            if source not in self.articles_by_source:
                self.articles_by_source[source] = []
            self.articles_by_source[source].append(article)
        
        # Выводим статистику
        stats = self.searcher.get_stats()
        print(f"📊 Статистика движка:")
        print(f"   - Статей в базе: {stats['num_articles']}")
        print(f"   - Тегов: {stats['num_tags']}")
        
        # Статистика по источникам
        print(f"   - Статей по источникам:")
        for source, articles in self.articles_by_source.items():
            print(f"     * {source}: {len(articles)}")
        
        self.openrouter_key = openrouter_key or os.getenv("OPENROUTER_API_KEY")
    
    def get_random_article_by_source(self, source: str) -> Dict[str, Any]:
        """Получить случайную существующую статью из указанного источника."""
        if source not in self.articles_by_source or not self.articles_by_source[source]:
            return None
        
        return random.choice(self.articles_by_source[source])
    
    def generate_test_article(
        self,
        topic: str,
        target_articles: List[Dict[str, Any]]
    ) -> str:
        """
        Генерирует статью, которая ссылается на КОНКРЕТНЫЕ существующие статьи.
        
        Args:
            topic: тема
            target_articles: список статей, на которые нужно сослаться
        """
        
        # Формируем описания ссылок
        references = []
        for i, article in enumerate(target_articles, 1):
            source = article.get("source", "unknown")
            number = article.get("number", "N/A")
            content_preview = article.get("content", "")[:100]
            
            references.append(f"""
Статья для ссылки {i}:
- Источник: {source}
- Номер: {number}
- Содержание: {content_preview}...
""")
        
        references_text = "\n".join(references)
        
        # Случайный тип НПА
        npa_types = [
            "УКАЗ ПРЕЗИДЕНТА РЕСПУБЛИКИ БЕЛАРУСЬ",
            "ПОСТАНОВЛЕНИЕ СОВЕТА МИНИСТРОВ РЕСПУБЛИКИ БЕЛАРУСЬ",
            "ЗАКОН РЕСПУБЛИКИ БЕЛАРУСЬ"
        ]
        npa_type = random.choice(npa_types)
        
        prompt = f"""
        Составь ОДНУ СТАТЬЮ нормативного правового акта Республики Беларусь на тему:
        "{topic}"

        Статья должна ВНОСИТЬ ИЗМЕНЕНИЯ в следующие существующие статьи:
        {references_text}

        ТРЕБОВАНИЯ К ФОРМУЛИРОВКАМ:
        1. ИСПОЛЬЗУЙ конкретные термины из содержания целевых статей (проценты, сроки, ответственность, порядок расчета и т.д.)
        2. НЕ ИСПОЛЬЗУЙ общие фразы: "применяются особые правила", "в соответствии с законодательством"
        3. КАЖДАЯ ссылка должна быть уникальной по смыслу
        4. Указывай КОНКРЕТНЫЕ числа, сроки, проценты

        Пример правильной формулировки (НЕ копировать, для примера):
        "Внести изменение в статью 179 Банковского кодекса, дополнив частью:
        'Процентная ставка по вкладам физических лиц не может превышать ставку рефинансирования более чем на 5 процентных пунктов'"

        Только текст статьи, без пояснений.
        """
        
        if self.openrouter_key:
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openrouter_key}"},
                    json={
                        "model": "google/gemini-2.0-flash-001",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 1000
                    },
                    timeout=30
                )
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"⚠️ Ошибка API: {e}")
                return self._mock_test_article(topic, target_articles)
        else:
            return self._mock_test_article(topic, target_articles)
    
    def _mock_test_article(self, topic: str, target_articles: List[Dict[str, Any]]) -> str:
        """Заглушка для генерации тестовой статьи."""
        article_text = f"Статья 1. О внесении изменений в законодательство о {topic}\n\n"
        
        for i, article in enumerate(target_articles, 1):
            source = article.get("source", "unknown")
            number = article.get("number", "N/A")
            
            article_text += f"{i}. Внести изменение в {source} Республики Беларусь, дополнив статью {number} частью следующего содержания:\n"
            article_text += f"   'В случаях, предусмотренных законодательством о {topic}, применяются особые правила.'\n\n"
        
        article_text += f"{len(target_articles)+1}. Настоящая статья вступает в силу после официального опубликования."
        
        return article_text
    
    def extract_article_references(self, article_text: str) -> List[Dict[str, Any]]:
        """
        Извлекает из текста статьи ссылки на другие статьи.
        Возвращает список словарей с source и number.
        """
        references = []
        
        # Простой парсинг для заглушки
        # В реальности здесь должен быть более сложный NLP
        import re
        
        # Ищем паттерны типа "статья 123 Гражданского кодекса" или "ст. 45 ТК"
        patterns = [
            r'стать[яеи]\s+(\d+)[^\d]*?(\w+\s+кодекс)',
            r'ст\.\s*(\d+)[^\d]*?(\w+\s+кодекс)',
            r'(\w+\s+кодекс)[^\d]*?стать[яеи]\s+(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, article_text, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    # Определяем, где номер, а где источник
                    if match[0].isdigit():
                        number, source = match
                    else:
                        source, number = match
                    
                    # Нормализуем название источника
                    source_map = {
                        'гражданского кодекса': 'Гражданский Кодекс',
                        'трудового кодекса': 'Трудовой кодекс',
                        'банковского кодекса': 'Банковский Кодекс',
                        'конституции': 'Конституция'
                    }
                    
                    for key, value in source_map.items():
                        if key in source.lower():
                            source = value
                            break
                    
                    references.append({
                        "source": source,
                        "number": number
                    })
        
        return references
    
    def find_articles_by_reference(
        self,
        references: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Находит в базе статьи по source и number.
        """
        found = []
        
        for ref in references:
            source = ref.get("source")
            number = ref.get("number")
            
            for article in self.all_articles:
                if (article.get("source") == source and 
                    str(article.get("number")) == str(number)):
                    found.append({
                        "id": article.get("id"),
                        "source": source,
                        "number": number,
                        "content": article.get("content", ""),
                        "reference": ref
                    })
                    break
        
        return found
    
    def run_test_suite(
        self,
        n_tests: int = 10,
        references_per_test: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Запуск тестирования с правильной методологией.
        
        Args:
            n_tests: количество тестов
            references_per_test: сколько ссылок должно быть в каждой тестовой статье
        """
        # Темы
        topics = [
            "пенсионное обеспечение",
            "защита персональных данных",
            "интеллектуальная собственность",
            "банковские гарантии",
            "дистанционная работа",
            "аренда недвижимости",
            "наследование имущества",
            "защита прав потребителей",
            "ипотечное кредитование",
            "трудовые споры"
        ]
        
        # Доступные источники для ссылок
        available_sources = ["Гражданский Кодекс", "Трудовой кодекс", "Банковский Кодекс", "Конституция"]
        
        print(f"\n{'='*80}")
        print(f"ТЕСТИРОВАНИЕ КАЧЕСТВА ПОИСКА (ПРАВИЛЬНАЯ МЕТОДОЛОГИЯ)")
        print(f"Количество тестов: {n_tests}")
        print(f"Ссылок на тест: {references_per_test}")
        print(f"{'='*80}\n")
        
        results = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for test_num in range(1, n_tests + 1):
            print(f"\n{'='*60}")
            print(f"ТЕСТ #{test_num} из {n_tests}")
            print(f"{'='*60}")
            
            # 1. Выбираем тему
            topic = random.choice(topics)
            
            # 2. Выбираем случайные СУЩЕСТВУЮЩИЕ статьи для ссылок
            target_articles = []
            used_sources = set()
            
            for _ in range(references_per_test):
                # Выбираем случайный источник, который ещё не использовали (для разнообразия)
                available = [s for s in available_sources if s not in used_sources]
                if not available:
                    available = available_sources
                
                source = random.choice(available)
                used_sources.add(source)
                
                # Получаем случайную статью из этого источника
                article = self.get_random_article_by_source(source)
                if article:
                    target_articles.append(article)
            
            if len(target_articles) < references_per_test:
                print(f"⚠️ Не удалось найти достаточно статей, пропускаем тест")
                continue
            
            print(f"\n📌 ТЕМА: {topic}")
            print(f"\n🎯 ЦЕЛЕВЫЕ СТАТЬИ (на них будем ссылаться):")
            for i, art in enumerate(target_articles, 1):
                print(f"   {i}. {art.get('source')} ст.{art.get('number')}")
                print(f"       {art.get('content', '')[:100]}...")
            
            # 3. Генерируем тестовую статью со ссылками на эти статьи
            print(f"\n🔄 Генерация тестовой статьи...")
            test_article = self.generate_test_article(topic, target_articles)
            print(f"\n📄 ТЕКСТ ТЕСТОВОЙ СТАТЬИ:\n{test_article}")
            
            # 4. Извлекаем ссылки (для проверки)
            extracted_refs = self.extract_article_references(test_article)
            print(f"\n🔍 Извлеченные ссылки: {extracted_refs}")
            
            # 5. Ищем по тексту тестовой статьи
            print(f"\n🔍 Поиск по тексту статьи...")
            search_results = self.searcher.search(test_article, k=50)
            
            # 6. Оцениваем, нашли ли мы целевые статьи
            target_ids = {art.get("id") for art in target_articles if art.get("id")}
            
            print(f"\n📊 РЕЗУЛЬТАТЫ ПОИСКА:")
            found_positions = []
            
            for i, res in enumerate(search_results, 1):
                res_id = res.get("meta", {}).get("original", {}).get("id")
                res_source = res.get("meta", {}).get("source", "unknown")
                res_number = res.get("article_number", "N/A")
                
                is_target = "✅" if res_id in target_ids else ""
                if is_target:
                    found_positions.append(i)
                
                print(f"   {i:2d}. [Score: {res['score']:.4f}] {is_target}")
                print(f"       {res_source} ст.{res_number}")
            
            # 7. Считаем метрики
            metrics = self.calculate_metrics(search_results[:10], target_ids)
            
            print(f"\n📊 МЕТРИКИ:")
            print(f"   Найдено целевых статей: {len(found_positions)} из {len(target_ids)}")
            print(f"   Позиции: {found_positions}")
            print(f"   Precision@1:  {metrics['precision_at_1']:.4f}")
            print(f"   Precision@5:  {metrics['precision_at_5']:.4f}")
            print(f"   Precision@10: {metrics['precision_at_10']:.4f}")
            print(f"   Recall@10:    {metrics['recall_at_10']:.4f}")
            print(f"   MRR:          {metrics['mrr']:.4f}")
            
            # Сохраняем результаты
            results.append({
                "test_number": test_num,
                "topic": topic,
                "target_articles": [
                    {
                        "id": a.get("id"),
                        "source": a.get("source"),
                        "number": a.get("number"),
                        "content_preview": a.get("content", "")[:200]
                    } for a in target_articles
                ],
                "test_article": test_article,
                "extracted_references": extracted_refs,
                "metrics": metrics,
                "found_positions": found_positions,
                "top_results": [
                    {
                        "source": r.get("meta", {}).get("source"),
                        "number": r.get("article_number"),
                        "score": r["score"],
                        "id": r.get("meta", {}).get("original", {}).get("id"),
                        "is_target": r.get("meta", {}).get("original", {}).get("id") in target_ids
                    } for r in search_results[:10]
                ]
            })
        
        # Сохранение
        filename = self.cache_dir / f"proper_test_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        self._print_final_stats(results, filename)
        
        return results
    
    def calculate_metrics(self, top_results: List[Dict], target_ids: set) -> Dict:
        """Расчет метрик качества."""
        metrics = {
            "precision_at_1": 0.0,
            "precision_at_5": 0.0,
            "precision_at_10": 0.0,
            "recall_at_10": 0.0,
            "mrr": 0.0,
            "found_count": 0
        }
        
        if not target_ids:
            return metrics
        
        found_at_ranks = []
        for rank, res in enumerate(top_results, 1):
            res_id = res.get("meta", {}).get("original", {}).get("id")
            if res_id in target_ids:
                found_at_ranks.append(rank)
        
        metrics["found_count"] = len(found_at_ranks)
        
        # Precision@k
        if len(top_results) >= 1:
            metrics["precision_at_1"] = 1.0 if 1 in found_at_ranks else 0.0
        
        if len(top_results) >= 5:
            found_in_top5 = sum(1 for r in found_at_ranks if r <= 5)
            metrics["precision_at_5"] = found_in_top5 / 5
        
        if len(top_results) >= 10:
            found_in_top10 = sum(1 for r in found_at_ranks if r <= 10)
            metrics["precision_at_10"] = found_in_top10 / 10
        
        # Recall@10
        metrics["recall_at_10"] = len(found_at_ranks) / len(target_ids)
        
        # MRR
        if found_at_ranks:
            metrics["mrr"] = np.mean([1.0 / r for r in found_at_ranks])
        
        return metrics
    
    def _print_final_stats(self,    results: List[Dict], filename: Path):
        """Печать финальной статистики."""
        print(f"\n{'='*80}")
        print("ФИНАЛЬНЫЙ ОТЧЕТ")
        print(f"{'='*80}")
        
        if not results:
            print("\n❌ Нет результатов")
            return
        
        # Общая статистика
        total_targets = sum(len(r["target_articles"]) for r in results)
        total_found = sum(len(r["found_positions"]) for r in results)
        
        print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Всего тестов: {len(results)}")
        print(f"   Всего целевых статей: {total_targets}")
        print(f"   Найдено в топ-10: {total_found}")
        print(f"   Общий recall: {total_found/total_targets:.2%}")
        
        # Средние метрики
        print(f"\n📈 СРЕДНИЕ МЕТРИКИ:")
        metrics_list = [r["metrics"] for r in results]
        
        print(f"   Precision@1:  {np.mean([m['precision_at_1'] for m in metrics_list]):.4f}")
        print(f"   Precision@5:  {np.mean([m['precision_at_5'] for m in metrics_list]):.4f}")
        print(f"   Precision@10: {np.mean([m['precision_at_10'] for m in metrics_list]):.4f}")
        print(f"   Recall@10:    {np.mean([m['recall_at_10'] for m in metrics_list]):.4f}")
        print(f"   MRR:          {np.mean([m['mrr'] for m in metrics_list]):.4f}")
        
        # Анализ по позициям
        all_positions = []
        for r in results:
            all_positions.extend(r["found_positions"])
        
        if all_positions:
            print(f"\n📊 РАСПРЕДЕЛЕНИЕ ПОЗИЦИЙ:")
            print(f"   Позиция 1: {sum(1 for p in all_positions if p == 1)} раз")
            print(f"   Позиция 2-3: {sum(1 for p in all_positions if 2 <= p <= 3)} раз")
            print(f"   Позиция 4-5: {sum(1 for p in all_positions if 4 <= p <= 5)} раз")
            print(f"   Позиция 6-10: {sum(1 for p in all_positions if 6 <= p <= 10)} раз")
        
        print(f"\n{'-'*80}")
        print(f"Отчет сохранен в: {filename}")
        print(f"{'='*80}\n")


def main():
    """Запуск тестирования."""
    tester = SearchQualityTester(
        tags_filepath="data/raw/base.json",
        laws_filepath="data/processed/laws.json",
        cache_dir="data/test_results",
        openrouter_key="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"
    )
    
    # Запускаем с правильной методологией
    results = tester.run_test_suite(
        n_tests=5,
        references_per_test=1  # По 2 ссылки на тест
    )


if __name__ == "__main__":
    main()