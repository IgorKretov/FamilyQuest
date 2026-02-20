"""
Модуль для генерации заданий с помощью GigaChat
"""
import os
import json
import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from dotenv import load_dotenv

class AITaskGenerator:
    """Генератор заданий на базе GigaChat"""
    
    def __init__(self):
        # Загружаем credentials из переменных окружения или st.secrets
        load_dotenv()
        self.credentials = (
            os.getenv("GIGACHAT_CREDENTIALS") or  # Из .env
            st.secrets.get("GIGACHAT_CREDENTIALS")  # Из Streamlit secrets
        )
        
        if not self.credentials:
            st.error("""
            ❌ Не найден ключ GigaChat!
            
            Локально: создай файл .env с GIGACHAT_CREDENTIALS=твой_ключ
            На Streamlit Cloud: добавь секрет в настройках
            """)
            return
        # Параметры подключения к GigaChat [citation:1]
        self.client = GigaChat(
            credentials=self.credentials,
            verify_ssl_certs=False,  # Для разработки, в продакшн лучше настроить сертификаты
            model="GigaChat",  # Можно также использовать "GigaChat-Pro" или "GigaChat-Plus"
            timeout=30,
            max_retries=3
        )
        
        # Категории заданий с эмодзи [citation:9]
        self.categories = {
            "creative": {
                "name": "🎨 Творчество",
                "prompt": "творческое задание, связанное с рисованием, лепкой, конструированием"
            },
            "science": {
                "name": "🔬 Наука",
                "prompt": "научное или экспериментальное задание, простой опыт или наблюдение"
            },
            "sport": {
                "name": "🏃 Спорт",
                "prompt": "спортивное или физическое задание, упражнение, активная игра"
            },
            "help": {
                "name": "🤝 Помощь",
                "prompt": "задание по дому, помощь родителям, забота о других"
            },
            "learning": {
                "name": "📚 Учёба",
                "prompt": "развивающее или учебное задание, связанное со школьными предметами"
            },
            "nature": {
                "name": "🌱 Природа",
                "prompt": "задание на свежем воздухе, наблюдение за природой, уход за растениями"
            }
        }
        
        # Словарь сложности [citation:9]
        self.difficulty_levels = {
            "easy": {
                "name": "🌟 Легко",
                "prompt": "простое задание, которое займёт 10-15 минут",
                "base_points": 20
            },
            "medium": {
                "name": "⭐⭐ Средне",
                "prompt": "задание средней сложности, 20-30 минут",
                "base_points": 35
            },
            "hard": {
                "name": "⭐⭐⭐ Сложно",
                "prompt": "сложное задание, 40-60 минут",
                "base_points": 50
            }
        }
    
    def generate_task(self, child_name: str, age: int, interests: List[str], 
                      category: str = None, difficulty: str = "medium") -> Dict:
        """
        Сгенерировать персонализированное задание для ребёнка [citation:2][citation:9]
        """
        
        # Определяем категорию (если не указана, выбираем из интересов)
        if not category and interests:
            # Берём случайную категорию из интересов
            import random
            category = random.choice(interests) if interests in self.categories else "creative"
        elif not category:
            category = "creative"
        
        category_info = self.categories.get(category, self.categories["creative"])
        difficulty_info = self.difficulty_levels.get(difficulty, self.difficulty_levels["medium"])
        
        # Формируем промпт для GigaChat [citation:9]
        prompt = f"""
        Ты — помощник для создания увлекательных заданий для детей. 
        Придумай задание для ребёнка со следующими характеристиками:
        
        - Имя: {child_name}
        - Возраст: {age} лет
        - Интересы: {', '.join(interests) if interests else 'разные'}
        - Категория: {category_info['name']} ({category_info['prompt']})
        - Сложность: {difficulty_info['name']} ({difficulty_info['prompt']})
        
        Задание должно быть:
        1. Безопасным и выполнимым дома или на улице
        2. Интересным для ребёнка этого возраста
        3. Развивающим полезные навыки
        4. С чёткими критериями выполнения
        5. С возможностью фотоотчёта (если уместно)
        
        Оформи ответ в формате JSON:
        {{
            "title": "Название задания (короткое и яркое, можно с эмодзи)",
            "description": "Подробное описание того, что нужно сделать (3-4 предложения)",
            "materials": ["список", "необходимых", "материалов"],
            "estimated_time": число (в минутах),
            "tips": ["полезный совет 1", "совет 2"],
            "photo_opportunity": true/false (можно ли подтвердить фото)
        }}
        
        Ответ должен быть только в виде JSON, без лишнего текста.
        """
        
        try:
            # Отправляем запрос к GigaChat [citation:1]
            response = self.client.chat(prompt)
            
            # Извлекаем JSON из ответа
            content = response.choices[0].message.content
            
            # Ищем JSON в ответе (иногда модель добавляет пояснения)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                task_data = json.loads(json_str)
            else:
                # Если не нашли JSON, парсим текст
                task_data = self._parse_text_response(content)
            
            # Добавляем метаданные
            task_data.update({
                "category": category,
                "difficulty": difficulty,
                "points": difficulty_info["base_points"] + (age // 2),  # Бонус за возраст
                "emoji": self._get_category_emoji(category),
                "generated_by": "ai",
                "generated_at": datetime.now().isoformat()
            })
            
            return task_data
            
        except Exception as e:
            st.error(f"Ошибка при генерации задания: {e}")
            # Возвращаем запасное задание
            return self._get_fallback_task(category, difficulty)
    
    def generate_daily_quest(self, child_name: str, age: int, interests: List[str], 
                             count: int = 3) -> List[Dict]:
        """
        Сгенерировать несколько заданий на день (квест) [citation:3]
        """
        tasks = []
        
        # Создаём промпт для генерации нескольких заданий
        prompt = f"""
        Составь набор из {count} разных заданий для ребёнка {child_name} ({age} лет).
        Интересы: {', '.join(interests) if interests else 'разносторонние'}.
        
        Задания должны быть:
        - Разных категорий (творчество, спорт, учёба, помощь по дому)
        - Разной сложности
        - Интересными и выполнимыми
        
        Оформи ответ как JSON-массив с заданиями.
        Каждое задание должно содержать поля: title, description, category, difficulty, estimated_time.
        
        Ответ должен быть только в виде JSON-массива.
        """
        
        try:
            response = self.client.chat(prompt)
            content = response.choices[0].message.content
            
            # Ищем JSON в ответе
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                tasks_data = json.loads(json_str)
                
                # Добавляем баллы и эмодзи
                for i, task in enumerate(tasks_data[:count]):
                    difficulty = task.get("difficulty", "medium")
                    category = task.get("category", "creative")
                    task["points"] = self.difficulty_levels[difficulty]["base_points"]
                    task["emoji"] = self._get_category_emoji(category)
                    task["generated_by"] = "ai"
                    tasks.append(task)
            
            return tasks
            
        except Exception as e:
            st.warning(f"Не удалось сгенерировать набор: {e}")
            # Генерируем по одному
            for _ in range(count):
                tasks.append(self.generate_task(child_name, age, interests))
            return tasks
    
    def generate_story_task(self, child_name: str, age: int, interests: List[str]) -> Dict:
        """
        Сгенерировать задание в формате истории/сказки [citation:8]
        """
        prompt = f"""
        Придумай увлекательное задание для ребёнка {child_name} ({age} лет) в формате истории.
        Интересы: {', '.join(interests) if interests else 'приключения'}.
        
        Задание должно выглядеть как маленький квест или приключение.
        Например: "Ты — космический исследователь, которому нужно... "
        
        Оформи ответ в формате JSON:
        {{
            "title": "Название истории",
            "story": "Краткое вступление (2-3 предложения)",
            "mission": "Что нужно сделать",
            "reward_description": "Как будет выглядеть награда в истории",
            "estimated_time": число
        }}
        """
        
        try:
            response = self.client.chat(prompt)
            content = response.choices[0].message.content
            
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                task_data = json.loads(content[json_start:json_end])
                task_data["generated_by"] = "ai_story"
                task_data["points"] = 45  # Бонус за креативность
                return task_data
                
        except Exception:
            pass
        
        return self._get_fallback_task("creative", "medium")
    
    def _parse_text_response(self, text: str) -> Dict:
        """Парсинг текстового ответа (если модель не вернула JSON)"""
        lines = text.strip().split('\n')
        task = {
            "title": "Интересное задание",
            "description": text[:200],
            "materials": ["то, что есть дома"],
            "estimated_time": 30,
            "tips": ["Будь внимателен", "Попроси помощи, если нужно"],
            "photo_opportunity": True
        }
        
        # Простой парсинг (можно улучшить)
        for line in lines:
            if "назв" in line.lower() or "title" in line.lower():
                task["title"] = line.split(':')[-1].strip()
            elif "опис" in line.lower() or "desc" in line.lower():
                task["description"] = line.split(':')[-1].strip()
        
        return task
    
    def _get_fallback_task(self, category: str, difficulty: str) -> Dict:
        """Запасное задание на случай ошибок API"""
        fallbacks = {
            "creative": {
                "title": "🎨 Волшебный рисунок",
                "description": "Нарисуй своё настроение сегодня. Используй яркие цвета и не бойся экспериментировать!"
            },
            "science": {
                "title": "🔬 Радуга в стакане",
                "description": "Попробуй сделать радугу из воды и сахара. Найди рецепт в интернете с родителями!"
            },
            "sport": {
                "title": "🏃 Полоса препятствий",
                "description": "Придумай и построй полосу препятствий из подушек, стульев и коробок. Пройди её 3 раза!"
            },
            "help": {
                "title": "🤝 Сюрприз для мамы",
                "description": "Сделай что-то приятное для мамы без просьбы: уберись, полей цветы или приготовь чай."
            }
        }
        
        base = fallbacks.get(category, fallbacks["creative"])
        points = self.difficulty_levels[difficulty]["base_points"]
        
        return {
            **base,
            "points": points,
            "category": category,
            "difficulty": difficulty,
            "emoji": self._get_category_emoji(category),
            "estimated_time": 30,
            "materials": ["материалы из дома"],
            "photo_opportunity": True,
            "generated_by": "fallback"
        }
    
    def _get_category_emoji(self, category: str) -> str:
        """Получить эмодзи для категории"""
        emojis = {
            "creative": "🎨",
            "science": "🔬",
            "sport": "🏃",
            "help": "🤝",
            "learning": "📚",
            "nature": "🌱"
        }
        return emojis.get(category, "🎯")

# Функция для быстрой проверки генерации
def test_generation():
    """Тестовая функция"""
    generator = AITaskGenerator()
    task = generator.generate_task(
        child_name="Саша",
        age=8,
        interests=["creative", "science"],
        difficulty="medium"
    )
    print(json.dumps(task, indent=2, ensure_ascii=False))
