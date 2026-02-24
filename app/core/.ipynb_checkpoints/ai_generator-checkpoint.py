"""
Модуль для генерации заданий с помощью GigaChat (API v1)
Использует прямой REST API без асинхронных проблем
"""
import os
import json
import requests
import streamlit as st
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
import urllib3
import logging

# Настройка логгера
logger = logging.getLogger("FamilyQuest.AI")
logger.setLevel(logging.DEBUG)

# Отключаем предупреждения о SSL (для разработки)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AITaskGenerator:
    """Генератор заданий на базе GigaChat через прямой REST API"""
    
    def __init__(self):
        """Инициализация генератора"""
        logger.info("=" * 50)
        logger.info("🤖 ИНИЦИАЛИЗАЦИЯ AITaskGenerator")
        logger.info("=" * 50)
        
        # Загружаем credentials
        load_dotenv()
        self.auth_key = (
            os.getenv("GIGACHAT_AUTH_KEY") or 
            st.secrets.get("GIGACHAT_AUTH_KEY")
        )
        
        if not self.auth_key:
            logger.error("❌ Не найден ключ авторизации GigaChat!")
            st.error("""
            ❌ Не найден ключ авторизации GigaChat!
            
            Добавьте в файл .env:
            GIGACHAT_AUTH_KEY=ваш_ключ_авторизации
            """)
            return
        else:
            logger.info("✅ Ключ авторизации загружен")
            logger.debug(f"Ключ (первые 10 символов): {self.auth_key[:10]}...")
        
        # URL для получения токена
        self.token_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        logger.info(f"📡 Token URL: {self.token_url}")
        
        # URL для генерации текста
        self.api_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        logger.info(f"📡 API URL: {self.api_url}")
        
        # Кэш для токена
        self.token = None
        self.token_expires = None
        logger.info("🔄 Кэш токена инициализирован")
        
        # Категории заданий
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
        logger.info(f"📚 Загружено {len(self.categories)} категорий заданий")
        
        # Словарь сложности
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
        logger.info(f"📊 Загружено {len(self.difficulty_levels)} уровней сложности")
        logger.info("=" * 50)
        
        # Добавляем кэш для предотвращения повторов
        self.last_titles = []
        
        # Добавляем возрастные группы
        self.age_groups = {
            "3-6": {
                "name": "Дошкольник",
                "description": "Для дошкольников: простые, игровые задания с минимальным текстом, много наглядности",
                "materials": ["карандаши", "бумага", "пластилин", "кубики", "игрушки"]
            },
            "7-10": {
                "name": "Младший школьник",
                "description": "Для младших школьников: творческие задания, простые опыты, помощь по дому",
                "materials": ["краски", "клей", "ножницы", "книги", "конструктор"]
            },
            "11-13": {
                "name": "Подросток",
                "description": "Для подростков: более сложные творческие проекты, кулинария, уход за животными",
                "materials": ["акриловые краски", "продукты", "инструменты", "книги"]
            },
            "14-17": {
                "name": "Старший подросток",
                "description": "Для старших подростков: серьезные проекты, программирование, сложные опыты, волонтерство",
                "materials": ["ноутбук", "специальные ингредиенты", "инструменты", "спортивный инвентарь"]
            }
        }
        logger.info(f"📚 Загружено {len(self.age_groups)} возрастных групп")
    
    def _get_age_group(self, age: int) -> str:
        """Определить возрастную группу"""
        if age <= 6:
            return "3-6"
        elif age <= 10:
            return "7-10"
        elif age <= 13:
            return "11-13"
        else:
            return "14-17"
    
    def _get_token(self) -> Optional[str]:
        """Получение токена доступа"""
        logger.info("🔄 _get_token() вызван")
        
        # Проверяем, не истёк ли текущий токен
        if self.token and self.token_expires:
            time_left = (self.token_expires - datetime.now()).total_seconds()
            logger.debug(f"Текущий токен истекает через {time_left:.1f} сек")
            
            if datetime.now() < self.token_expires:
                logger.info("✅ Используем существующий токен")
                return self.token
            else:
                logger.info("⏰ Токен истёк, получаем новый")
        
        # Генерируем уникальный RqUID для каждого запроса
        rquid = str(uuid.uuid4())
        logger.debug(f"Сгенерирован RqUID: {rquid}")
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': rquid,
            'Authorization': f'Basic {self.auth_key}'
        }
        logger.debug("Headers подготовлены")
        
        payload = {
            'scope': 'GIGACHAT_API_PERS'
        }
        
        try:
            logger.info("📡 Отправка запроса на получение токена...")
            response = requests.post(
                self.token_url, 
                headers=headers, 
                data=payload, 
                verify=False,
                timeout=30
            )
            logger.info(f"📡 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires = datetime.now() + timedelta(seconds=expires_in - 60)
                logger.info(f"✅ Токен получен, истекает через {expires_in} сек")
                logger.debug(f"Токен (первые 20 символов): {self.token[:20]}...")
                return self.token
            else:
                logger.error(f"❌ Ошибка получения токена: {response.status_code}")
                logger.error(f"Текст ответа: {response.text}")
                st.error(f"Ошибка получения токена: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("⏰ Таймаут при получении токена")
            st.error("Таймаут при подключении к GigaChat")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"🔌 Ошибка подключения: {e}")
            st.error(f"Ошибка подключения к GigaChat: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка: {e}")
            st.error(f"Ошибка подключения к GigaChat: {e}")
            return None
    
    def _call_gigachat(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """Отправка запроса к GigaChat API"""
        logger.info("📡 _call_gigachat() вызван")
        logger.debug(f"Температура: {temperature}")
        logger.debug(f"Длина промпта: {len(prompt)} символов")
        
        # Логируем первые 200 символов промпта
        logger.debug(f"Промпт (начало): {prompt[:200]}...")
        
        token = self._get_token()
        if not token:
            logger.error("❌ Не удалось получить токен")
            return None
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        payload = {
            "model": "GigaChat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": 1000
        }
        logger.debug(f"Payload подготовлен, модель: {payload['model']}")
        
        try:
            logger.info("📡 Отправка запроса к API...")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=30
            )
            logger.info(f"📡 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                logger.info(f"✅ Ответ получен, длина: {len(content)} символов")
                logger.debug(f"Ответ (первые 200 символов): {content[:200]}...")
                return content
            else:
                logger.error(f"❌ Ошибка API: {response.status_code}")
                logger.error(f"Текст ответа: {response.text}")
                st.error(f"Ошибка API: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("⏰ Таймаут при вызове API")
            st.error("Таймаут при вызове GigaChat API")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при вызове GigaChat: {e}")
            st.error(f"Ошибка при вызове GigaChat: {e}")
            return None
    
    def generate_task(self, child_name: str, age: int, interests: List[str], 
                      category: str = None, difficulty: str = "medium") -> Dict:
        """Сгенерировать персонализированное задание"""
        logger.info("=" * 40)
        logger.info(f"🎯 GENERATE_TASK для {child_name}")
        logger.info("=" * 40)
        logger.info(f"👤 Ребёнок: {child_name}, возраст: {age}")
        logger.info(f"📋 Интересы: {interests}")
        logger.info(f"📌 Категория: {category}")
        logger.info(f"⚖️ Сложность: {difficulty}")
        
        start_time = datetime.now()
        
        # Определяем возрастную группу
        age_group = self._get_age_group(age)
        age_info = self.age_groups.get(age_group, self.age_groups["7-10"])
        logger.info(f"👥 Возрастная группа: {age_info['name']} ({age_group})")
        
        # Определяем категорию
        if not category and interests:
            import random
            valid_interests = [i for i in interests if i in self.categories]
            logger.debug(f"Валидные интересы из категорий: {valid_interests}")
            category = random.choice(valid_interests) if valid_interests else "creative"
            logger.info(f"🎲 Выбрана случайная категория: {category}")
        elif not category:
            category = "creative"
            logger.info(f"📌 Категория не указана, используем: {category}")
        
        category_info = self.categories.get(category, self.categories["creative"])
        difficulty_info = self.difficulty_levels.get(difficulty, self.difficulty_levels["medium"])
        
        logger.debug(f"Инфо категории: {category_info['name']}")
        logger.debug(f"Инфо сложности: {difficulty_info['name']} ({difficulty_info['base_points']} баллов)")
        
        # Список уже сгенерированных названий для предотвращения повторов
        avoid_titles = ", ".join([f'"{t}"' for t in self.last_titles[-3:]])
        logger.debug(f"Избегаем названия: {avoid_titles if avoid_titles else 'нет'}")
        
        # Формируем промпт с учетом возраста
        prompt = f"""Ты — помощник для создания увлекательных заданий для детей и подростков. 
Придумай задание для ребёнка со следующими характеристиками:

- Имя: {child_name}
- Возраст: {age} лет (возрастная группа: {age_group})
- Интересы: {', '.join(interests) if interests else 'разные'}
- Категория: {category_info['name']} ({category_info['prompt']})
- Сложность: {difficulty_info['name']} ({difficulty_info['prompt']})

ВАЖНЫЕ ТРЕБОВАНИЯ ДЛЯ ЭТОГО ВОЗРАСТА:
{age_info['description']}
Подходящие материалы: {', '.join(age_info['materials'][:3])}

Задание должно быть:
1. Соответствовать возрасту {age} лет (НЕ детское, если ребёнок старше 12 лет)
2. Учитывать интересы: {', '.join(interests) if interests else 'разные'}
3. Безопасным и выполнимым дома или на улице
4. ИНТЕРЕСНЫМ для ребёнка этого возраста
5. С чёткими критериями выполнения
6. С возможностью фотоотчёта

ИЗБЕГАЙ этих названий (они уже использовались): {avoid_titles if avoid_titles else "нет"}

Оформи ответ ТОЛЬКО в виде JSON (без пояснений):
{{
    "title": "Название задания (короткое, с эмодзи)",
    "description": "Подробное описание (3-4 предложения)",
    "materials": ["список", "необходимых", "материалов"],
    "estimated_time": число (минут),
    "tips": ["совет 1", "совет 2"],
    "photo_opportunity": true
}}"""
        
        logger.info("📝 Промпт сформирован")
        
        try:
            logger.info("🔄 Отправка запроса к GigaChat...")
            response_text = self._call_gigachat(prompt)
            
            if not response_text:
                logger.warning("⚠️ Не получен ответ от GigaChat, используем fallback")
                return self._get_fallback_task(category, difficulty, age)
            
            logger.info("✅ Ответ получен, начинаем парсинг")
            
            # Извлекаем JSON из ответа
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                logger.debug(f"Извлечён JSON (первые 100 символов): {json_str[:100]}...")
                task_data = json.loads(json_str)
                logger.info(f"✅ JSON успешно распарсен, поля: {list(task_data.keys())}")
            else:
                logger.warning("⚠️ JSON не найден в ответе, парсим как текст")
                task_data = self._parse_text_response(response_text)
            
            # Добавляем метаданные
            points = difficulty_info["base_points"] + (age // 2)
            task_data.update({
                "category": category,
                "difficulty": difficulty,
                "points": points,
                "emoji": self._get_category_emoji(category),
                "generated_by": "ai",
                "generated_at": datetime.now().isoformat()
            })
            
            # Сохраняем название в историю
            self.last_titles.append(task_data.get("title", ""))
            if len(self.last_titles) > 10:
                self.last_titles.pop(0)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Задание сгенерировано за {elapsed:.2f} сек")
            logger.info(f"📌 Название: {task_data.get('title')}")
            logger.info(f"⭐ Баллы: {task_data.get('points')}")
            
            return task_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            logger.error(f"Проблемный текст: {response_text if 'response_text' in locals() else 'нет'}")
            return self._get_fallback_task(category, difficulty, age)
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при генерации: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self._get_fallback_task(category, difficulty, age)
    
    def generate_daily_quest(self, child_name: str, age: int, interests: List[str], 
                             count: int = 3) -> List[Dict]:
        """Сгенерировать несколько заданий на день"""
        logger.info("=" * 40)
        logger.info(f"🎯 GENERATE_DAILY_QUEST для {child_name}")
        logger.info("=" * 40)
        logger.info(f"👤 Ребёнок: {child_name}, возраст: {age}")
        logger.info(f"📋 Количество заданий: {count}")
        logger.info(f"📋 Интересы: {interests}")
        
        tasks = []
        start_time = datetime.now()
        
        # Определяем возрастную группу
        age_group = self._get_age_group(age)
        age_info = self.age_groups.get(age_group, self.age_groups["7-10"])
        
        prompt = f"""Составь набор из {count} разных заданий для ребёнка {child_name} ({age} лет).
Интересы: {', '.join(interests) if interests else 'разносторонние'}.

Возрастная группа: {age_info['name']}
Рекомендации: {age_info['description']}

Задания должны быть разных категорий и сложности.
Каждое задание должно соответствовать возрасту.

Оформи ответ ТОЛЬКО в виде JSON-массива:
[
    {{
        "title": "Название 1",
        "description": "Описание 1",
        "category": "creative/sport/help/learning",
        "difficulty": "easy/medium/hard",
        "estimated_time": 30
    }},
    ...
]"""
        
        logger.info("📝 Промпт для квеста сформирован")
        
        try:
            logger.info("🔄 Отправка запроса к GigaChat...")
            response_text = self._call_gigachat(prompt, temperature=0.8)
            
            if response_text:
                logger.info("✅ Ответ получен, начинаем парсинг")
                json_start = response_text.find('[')
                json_end = response_text.rfind(']') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    logger.debug(f"Извлечён JSON (первые 100 символов): {json_str[:100]}...")
                    tasks_data = json.loads(json_str)
                    logger.info(f"✅ JSON успешно распарсен, получено {len(tasks_data)} заданий")
                    
                    for i, task in enumerate(tasks_data[:count]):
                        difficulty = task.get("difficulty", "medium")
                        category = task.get("category", "creative")
                        task["points"] = self.difficulty_levels[difficulty]["base_points"] + (age // 2)
                        task["emoji"] = self._get_category_emoji(category)
                        task["generated_by"] = "ai"
                        tasks.append(task)
                        logger.debug(f"  Задание {i+1}: {task.get('title')} ({difficulty}, {task['points']} баллов)")
            
            # Если не получилось, генерируем по одному
            if not tasks:
                logger.warning("⚠️ Не удалось получить квест, генерируем по одному")
                for i in range(count):
                    logger.info(f"Генерация задания {i+1}/{count}...")
                    tasks.append(self.generate_task(child_name, age, interests))
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Квест сгенерирован за {elapsed:.2f} сек, всего {len(tasks)} заданий")
            
            return tasks
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON квеста: {e}")
            logger.info("Генерируем по одному как запасной вариант")
            return [self.generate_task(child_name, age, interests) for _ in range(count)]
        except Exception as e:
            logger.error(f"❌ Ошибка генерации квеста: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return [self.generate_task(child_name, age, interests) for _ in range(count)]
    
    def generate_story_task(self, child_name: str, age: int, interests: List[str]) -> Dict:
        """Сгенерировать задание в формате истории"""
        logger.info("=" * 40)
        logger.info(f"📖 GENERATE_STORY_TASK для {child_name}")
        logger.info("=" * 40)
        logger.info(f"👤 Ребёнок: {child_name}, возраст: {age}")
        logger.info(f"📋 Интересы: {interests}")
        
        start_time = datetime.now()
        
        # Определяем возрастную группу
        age_group = self._get_age_group(age)
        age_info = self.age_groups.get(age_group, self.age_groups["7-10"])
        
        prompt = f"""Придумай увлекательное задание для ребёнка {child_name} ({age} лет) в формате истории.
Интересы: {', '.join(interests) if interests else 'приключения'}.

Возрастная группа: {age_info['name']}
История должна соответствовать возрасту: {age_info['description']}

Оформи ответ ТОЛЬКО в виде JSON:
{{
    "title": "Название истории",
    "story": "Вступление (2-3 предложения)",
    "mission": "Что нужно сделать (конкретное задание)",
    "reward_description": "Как будет выглядеть награда в истории",
    "estimated_time": число (минут)
}}"""
        
        logger.info("📝 Промпт для истории сформирован")
        
        try:
            logger.info("🔄 Отправка запроса к GigaChat...")
            response_text = self._call_gigachat(prompt, temperature=0.9)
            
            if response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    logger.debug(f"Извлечён JSON: {json_str[:100]}...")
                    task_data = json.loads(json_str)
                    task_data["points"] = 45 + (age // 2)
                    task_data["generated_by"] = "ai_story"
                    task_data["emoji"] = "📖"
                    
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"✅ История сгенерирована за {elapsed:.2f} сек")
                    logger.info(f"📌 Название: {task_data.get('title')}")
                    
                    return task_data
                    
        except Exception as e:
            logger.error(f"❌ Ошибка генерации истории: {e}")
        
        # Запасной вариант
        logger.warning("⚠️ Используем запасную историю")
        return {
            "title": "🌟 Волшебное приключение",
            "story": f"Однажды {child_name} нашёл волшебный портал, ведущий в удивительный мир...",
            "mission": "Нарисуй или опиши, что ты увидел в волшебной стране",
            "reward_description": "Ты получишь звание Хранителя портала и 50 баллов!",
            "estimated_time": 40,
            "points": 45,
            "emoji": "📖",
            "generated_by": "fallback"
        }
    
    def _parse_text_response(self, text: str) -> Dict:
        """Парсинг текстового ответа"""
        logger.debug("📝 Парсинг текстового ответа")
        logger.debug(f"Текст для парсинга (первые 200 символов): {text[:200]}...")
        
        return {
            "title": "🎯 Интересное задание",
            "description": text[:200],
            "materials": ["то, что есть дома"],
            "estimated_time": 30,
            "tips": ["Будь внимателен", "Попроси помощи, если нужно"],
            "photo_opportunity": True
        }
    
    def _get_fallback_task(self, category: str, difficulty: str, age: int) -> Dict:
        """Запасное задание"""
        logger.info(f"📋 Используем fallback задание (категория: {category}, сложность: {difficulty})")
        
        # Определяем возрастную группу для fallback
        age_group = self._get_age_group(age)
        
        fallbacks = {
            "creative": {
                "3-6": {
                    "title": "🎨 Рисунок для мамы",
                    "description": "Нарисуй красивый рисунок для мамы. Используй яркие цвета!"
                },
                "7-10": {
                    "title": "🎨 Открытка своими руками",
                    "description": "Сделай поздравительную открытку для кого-то из семьи. Используй аппликацию, рисунки и красивые надписи."
                },
                "11-13": {
                    "title": "🎨 Фотоистория",
                    "description": "Сделай серию фотографий на тему 'Мой день'. Обработай их и создай коллаж."
                },
                "14-17": {
                    "title": "🎨 Дизайн-проект",
                    "description": "Придумай дизайн своей комнаты или рабочего места. Нарисуй план или создай 3D-модель."
                }
            },
            "sport": {
                "3-6": {
                    "title": "🏃 Весёлая зарядка",
                    "description": "Сделай весёлую зарядку под музыку. Попрыгай, похлопай, потянись!"
                },
                "14-17": {
                    "title": "🏋️ Персональная тренировка",
                    "description": "Составь для себя комплекс упражнений на 20 минут и выполни его. Можно использовать приложение для фитнеса."
                }
            },
            "science": {
                "3-6": {
                    "title": "🔬 Радуга в стакане",
                    "description": "Сделай радугу из воды и сахара с помощью родителей!"
                },
                "14-17": {
                    "title": "🔬 Химический эксперимент",
                    "description": "Проведи безопасный химический опыт. Например, сделай вулкан из соды и уксуса."
                }
            }
        }
        
        # Выбираем подходящее запасное задание
        category_fallbacks = fallbacks.get(category, fallbacks["creative"])
        if age_group in category_fallbacks:
            task_info = category_fallbacks[age_group]
        else:
            # Если для этой возрастной группы нет, берем среднюю
            task_info = category_fallbacks.get("7-10", fallbacks["creative"]["7-10"])
        
        points = self.difficulty_levels[difficulty]["base_points"] + (age // 2)
        
        logger.debug(f"Fallback задание: {task_info['title']}, {points} баллов")
        
        return {
            "title": task_info["title"],
            "description": task_info["description"],
            "materials": ["материалы из дома"],
            "estimated_time": 30,
            "tips": ["Будь внимателен", "Попроси помощи, если нужно"],
            "photo_opportunity": True,
            "points": points,
            "category": category,
            "difficulty": difficulty,
            "emoji": self._get_category_emoji(category),
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


# Функция для быстрой проверки
def test_generation():
    """Тестовая функция"""
    print("\n" + "="*60)
    print("🧪 ТЕСТИРОВАНИЕ AITaskGenerator")
    print("="*60 + "\n")
    
    generator = AITaskGenerator()
    
    # Получаем токен отдельно для проверки
    print("\n📡 Получение токена...")
    token = generator._get_token()
    if token:
        print("✅ Токен получен успешно!")
        
        # Тестовая генерация для ребёнка 8 лет
        print("\n🎯 Тестовая генерация задания (8 лет)...")
        task = generator.generate_task(
            child_name="Саша",
            age=8,
            interests=["creative", "science"],
            difficulty="medium"
        )
        print("\n📋 Результат:")
        print(json.dumps(task, indent=2, ensure_ascii=False))
        
        # Тестовая генерация для подростка 16 лет
        print("\n🎯 Тестовая генерация задания (16 лет)...")
        task_teen = generator.generate_task(
            child_name="Петя",
            age=16,
            interests=["music", "sport"],
            difficulty="hard"
        )
        print("\n📋 Результат для подростка:")
        print(json.dumps(task_teen, indent=2, ensure_ascii=False))
        
        # Тест квеста
        print("\n🎯 Тестовая генерация квеста...")
        quest = generator.generate_daily_quest(
            child_name="Саша",
            age=8,
            interests=["creative", "science"],
            count=2
        )
        print(f"\n📋 Получено {len(quest)} заданий")
        for i, t in enumerate(quest):
            print(f"  {i+1}. {t.get('title')} - {t.get('points')} баллов")
        
    else:
        print("❌ Не удалось получить токен")

if __name__ == "__main__":
    test_generation()