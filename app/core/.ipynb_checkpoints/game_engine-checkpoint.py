"""
Ядро игровой логики FamilyQuest
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Dict, Optional
from core.achievements import AchievementSystem
from utils.logger import logger
import random
import json
import sqlite3

@dataclass
class Task:
    def __init__(self, id, title, description, category, points, difficulty, emoji, 
                 photo_required, child_id, due_date=None, completed=False, 
                 completed_at=None, photo_url=None, created_at=None):
        self.id = id
        self.title = title
        self.description = description
        self.category = category
        self.points = points
        self.difficulty = difficulty
        self.emoji = emoji
        self.photo_required = photo_required
        self.child_id = child_id
        self.due_date = due_date
        self.completed = completed
        self.completed_at = completed_at
        self.photo_url = photo_url
        self.created_at = created_at


@dataclass
class Child:
    def __init__(self, id, name, age, avatar, interests, points, level, streak_days, last_active, parent_id=None):
        self.id = id
        self.name = name
        self.age = age
        self.avatar = avatar
        self.interests = interests if isinstance(interests, list) else []
        self.points = points
        self.level = level
        self.streak_days = streak_days
        self.last_active = last_active
        self.parent_id = parent_id  # Добавлено поле для родителя
        
class GameEngine:
    def __init__(self):
        self.tasks: List[Task] = []
        self.children: Dict[int, Child] = {}
        self.categories = {
            "creative": {"name": "Творчество", "emoji": "🎨"},
            "science": {"name": "Наука", "emoji": "🔬"},
            "help": {"name": "Помощь", "emoji": "🤝"},
            "sport": {"name": "Спорт", "emoji": "🏃"},
            "learning": {"name": "Учёба", "emoji": "📚"},
            "nature": {"name": "Природа", "emoji": "🌱"},
        }
        self.achievement_system = None
        
    def add_child(self, name: str, age: int, interests: List[str], parent_id: int = None) -> Child:
        """Добавить ребёнка (только в память)"""
        child_id = len(self.children) + 1
        child = Child(
            id=child_id,
            name=name,
            age=age,
            avatar=f"https://api.dicebear.com/7.x/adventurer/svg?seed={name}",
            interests=interests,
            points=0,
            level=1,
            streak_days=0,
            last_active=date.today(),
            parent_id=parent_id
        )
        self.children[child_id] = child
        return child
    
    def create_task(self, **kwargs) -> Task:
        """Создать задание (только в память)"""
        task_id = len(self.tasks) + 1
        task = Task(id=task_id, created_at=datetime.now(), **kwargs)
        self.tasks.append(task)
        return task
    
    def complete_task(self, task_id: int, child_id: int, photo_url: str = None) -> Dict:
        """Отметить задание выполненным (базовая версия)"""
        logger.info(f"✅ Task {task_id} completed by child {child_id}")
        
        # Находим задание в памяти
        task = next((t for t in self.tasks if t.id == task_id), None)
        if not task:
            logger.warning(f"Task {task_id} not found in memory")
            return {'points': 0, 'new_achievements': []}
        
        if task.completed:
            logger.warning(f"Task {task_id} already completed")
            return {'points': 0, 'new_achievements': []}
        
        # Обновляем в БД
        from data.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Обновляем задание
            cursor.execute('''
                UPDATE tasks 
                SET completed = 1, completed_at = ?, photo_url = ?
                WHERE id = ? AND user_id = ?
            ''', (datetime.now().isoformat(), photo_url, task_id, child_id))
            
            # Обновляем баллы ребёнка в таблице users
            cursor.execute('''
                UPDATE users 
                SET points = points + ?, 
                    level = ((points + ?) / 100) + 1,
                    last_active = ?
                WHERE id = ?
            ''', (task.points, task.points, date.today().isoformat(), child_id))
            
            conn.commit()
            
            # Обновляем данные в памяти
            task.completed = True
            task.completed_at = datetime.now()
            task.photo_url = photo_url
            
            child = self.children.get(child_id)
            if child:
                child.points += task.points
                child.level = self.calculate_level(child.points)
                child.last_active = date.today()
            
            conn.close()
            return {'points': task.points, 'new_achievements': []}
            
        except sqlite3.Error as e:
            logger.error(f"Database error in complete_task: {e}")
            conn.rollback()
            conn.close()
            return {'points': 0, 'new_achievements': []}
    
    def calculate_level(self, points: int) -> int:
        """Расчёт уровня на основе баллов"""
        return points // 100 + 1
    
    def get_daily_tasks(self, child_id: int, count: int = 3) -> List[Task]:
        """Получить персонализированные задания на день"""
        # Загружаем из БД актуальные задания
        tasks = self.load_tasks_from_db(child_id)
        
        # Обновляем список в памяти
        self.tasks = tasks
        
        # Возвращаем невыполненные задания
        incomplete_tasks = [t for t in tasks if not t.completed]
        
        # Если заданий мало, создаём несколько стандартных (можно добавить логику)
        if len(incomplete_tasks) < count:
            # Здесь можно добавить автоматическую генерацию заданий
            pass
        
        return incomplete_tasks
    
    def _safe_json_loads(self, json_str):
        """Безопасная загрузка JSON с обработкой ошибок"""
        if not json_str:
            return []
        if isinstance(json_str, list):
            return json_str
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            # Если не удалось распарсить, возвращаем пустой список
            return []
    
    def load_children_from_db(self, parent_id: int = None):
        """Загрузить детей из БД (фильтр по родителю)"""
        from data.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            if parent_id:
                # Загружаем детей, привязанных к родителю
                cursor.execute('''
                    SELECT u.* FROM users u
                    JOIN family_relations fr ON u.id = fr.child_id
                    WHERE fr.parent_id = ? AND u.user_type = 'child'
                ''', (parent_id,))
            else:
                # Загружаем всех детей (для обратной совместимости)
                cursor.execute('SELECT * FROM users WHERE user_type = "child"')
            
            self.children = {}
            for row in cursor.fetchall():
                child_data = dict(row)
                # Безопасно преобразуем interests из JSON
                child_data['interests'] = self._safe_json_loads(child_data.get('interests'))
                
                # Создаём объект Child
                child = Child(
                    id=child_data['id'],
                    name=child_data['name'],
                    age=child_data['age'],
                    avatar=child_data.get('avatar', f"https://api.dicebear.com/7.x/adventurer/svg?seed={child_data['name']}"),
                    interests=child_data['interests'],
                    points=child_data.get('points', 0),
                    level=child_data.get('level', 1),
                    streak_days=child_data.get('streak_days', 0),
                    last_active=datetime.fromisoformat(child_data['last_active']).date() if child_data.get('last_active') else date.today(),
                    parent_id=parent_id
                )
                self.children[child.id] = child
            
        except sqlite3.Error as e:
            logger.error(f"Database error in load_children_from_db: {e}")
        finally:
            conn.close()
    
    def add_child_to_db(self, name: str, age: int, interests: List[str], parent_id: int = None) -> Child:
        """Добавить ребёнка в БД и в память (с опциональной привязкой к родителю)"""
        from data.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            interests_json = json.dumps(interests, ensure_ascii=False)
            avatar = f"https://api.dicebear.com/7.x/adventurer/svg?seed={name}"
            last_active = date.today().isoformat()
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, name, user_type, age, interests, avatar, last_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, 'temporary_hash', name, 'child', age, interests_json, avatar, last_active))
            
            child_id = cursor.lastrowid
            
            # Если есть родитель, создаём связь
            if parent_id:
                cursor.execute('''
                    INSERT INTO family_relations (parent_id, child_id)
                    VALUES (?, ?)
                ''', (parent_id, child_id))
            
            conn.commit()
            
            # Создаём объект в памяти
            child = Child(
                id=child_id,
                name=name,
                age=age,
                avatar=avatar,
                interests=interests,
                points=0,
                level=1,
                streak_days=0,
                last_active=date.today(),
                parent_id=parent_id
            )
            
            self.children[child_id] = child
            return child
            
        except sqlite3.Error as e:
            logger.error(f"Database error in add_child_to_db: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def save_task_to_db(self, task_data: Dict) -> int:
        """Сохранить задание в БД"""
        from data.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO tasks (
                    user_id, title, description, category, points, 
                    difficulty, emoji, photo_required, due_date, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_data['child_id'],
                task_data['title'],
                task_data['description'],
                task_data['category'],
                task_data['points'],
                task_data['difficulty'],
                task_data['emoji'],
                1 if task_data.get('photo_required') else 0,
                task_data.get('due_date'),
                task_data.get('created_by')
            ))
            
            task_id = cursor.lastrowid
            conn.commit()
            
            # Обновляем список в памяти
            task = Task(
                id=task_id,
                title=task_data['title'],
                description=task_data['description'],
                category=task_data['category'],
                points=task_data['points'],
                difficulty=task_data['difficulty'],
                emoji=task_data['emoji'],
                photo_required=task_data.get('photo_required', False),
                child_id=task_data['child_id'],
                due_date=task_data.get('due_date'),
                completed=False,
                completed_at=None,
                photo_url=None,
                created_at=datetime.now()
            )
            self.tasks.append(task)
            
            return task_id
            
        except sqlite3.Error as e:
            logger.error(f"Database error in save_task_to_db: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    def load_tasks_from_db(self, child_id: int) -> List[Task]:
        """Загрузить задания ребёнка из БД"""
        from data.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        tasks = []
        try:
            cursor.execute('''
                SELECT * FROM tasks 
                WHERE user_id = ? AND completed = 0
                ORDER BY created_at DESC
            ''', (child_id,))
            
            for row in cursor.fetchall():
                task_data = dict(row)
                task = Task(
                    id=task_data['id'],
                    title=task_data['title'],
                    description=task_data['description'],
                    category=task_data['category'],
                    points=task_data['points'],
                    difficulty=task_data['difficulty'],
                    emoji=task_data['emoji'],
                    photo_required=bool(task_data['photo_required']),
                    child_id=task_data['user_id'],
                    due_date=task_data.get('due_date'),
                    completed=bool(task_data['completed']),
                    completed_at=task_data.get('completed_at'),
                    photo_url=task_data.get('photo_url'),
                    created_at=datetime.fromisoformat(task_data['created_at']) if task_data['created_at'] else datetime.now()
                )
                tasks.append(task)
            
        except sqlite3.Error as e:
            logger.error(f"Database error in load_tasks_from_db: {e}")
        finally:
            conn.close()
        
        return tasks
    
    def init_achievements(self, db_conn):
        """Инициализация системы достижений"""
        from data.database import get_connection
        self.achievement_system = AchievementSystem(get_connection())
    
    def complete_task_with_achievements(self, task_id: int, child_id: int, photo_url: str = None) -> Dict:
        """Расширенная версия с проверкой достижений"""
        from data.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Получаем баллы за задание
            cursor.execute('SELECT points FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            if not row:
                return {'points': 0, 'new_achievements': []}
            
            points = row['points']
            
            if points > 0:
                # Обновляем задание
                cursor.execute('''
                    UPDATE tasks 
                    SET completed = 1, completed_at = ?, photo_url = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), photo_url, task_id))
                
                # Обновляем баллы ребёнка
                cursor.execute('''
                    UPDATE users 
                    SET points = points + ?, 
                        level = ((points + ?) / 100) + 1,
                        last_active = ?
                    WHERE id = ?
                ''', (points, points, date.today().isoformat(), child_id))
                
                conn.commit()
                
                # Собираем статистику для проверки достижений
                stats = self._collect_stats(child_id, conn)
                
                # Проверяем новые достижения
                new_achievements = []
                if self.achievement_system:
                    new_achievements = self.achievement_system.check_and_unlock(child_id, stats)
                    
                    # Добавляем бонусные баллы за достижения
                    for ach in new_achievements:
                        cursor.execute('''
                            UPDATE users 
                            SET points = points + ? 
                            WHERE id = ?
                        ''', (ach.get('reward_points', 0), child_id))
                        conn.commit()
                
                # Обновляем данные в памяти
                task = next((t for t in self.tasks if t.id == task_id), None)
                if task:
                    task.completed = True
                    task.completed_at = datetime.now()
                    task.photo_url = photo_url
                
                child = self.children.get(child_id)
                if child:
                    child.points += points
                    child.level = self.calculate_level(child.points)
                    child.last_active = date.today()
                
                return {
                    'points': points,
                    'new_achievements': new_achievements
                }
            
            return {'points': 0, 'new_achievements': []}
            
        except sqlite3.Error as e:
            logger.error(f"Database error in complete_task_with_achievements: {e}")
            conn.rollback()
            return {'points': 0, 'new_achievements': []}
        finally:
            conn.close()
    
    def _collect_stats(self, child_id: int, conn=None) -> Dict:
        """Собрать статистику ребёнка для проверки достижений"""
        close_conn = False
        if not conn:
            from data.database import get_connection
            conn = get_connection()
            close_conn = True
        
        cursor = conn.cursor()
        
        try:
            # Общее количество выполненных заданий
            cursor.execute('''
                SELECT COUNT(*) FROM tasks 
                WHERE user_id = ? AND completed = 1
            ''', (child_id,))
            total_tasks = cursor.fetchone()[0] or 0
            
            # Задания по категориям
            cursor.execute('''
                SELECT category, COUNT(*) FROM tasks 
                WHERE user_id = ? AND completed = 1
                GROUP BY category
            ''', (child_id,))
            category_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Текущие баллы и streak
            cursor.execute('''
                SELECT points, streak_days FROM users WHERE id = ?
            ''', (child_id,))
            row = cursor.fetchone()
            points = row['points'] if row else 0
            streak_days = row['streak_days'] if row else 0
            
            stats = {
                'total_tasks': total_tasks,
                'total_points': points,
                'streak_days': streak_days,
                **{f'category_{k}': v for k, v in category_stats.items()}
            }
            
            return stats
            
        except sqlite3.Error as e:
            logger.error(f"Database error in _collect_stats: {e}")
            return {
                'total_tasks': 0,
                'total_points': 0,
                'streak_days': 0
            }
        finally:
            if close_conn:
                conn.close()
    
    def load_child_data(self, child_id: int):
        """Загрузить данные конкретного ребёнка"""
        from data.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Загружаем данные ребёнка
            cursor.execute('''
                SELECT id, name, age, avatar, interests, points, level, streak_days, last_active 
                FROM users WHERE id = ? AND user_type = 'child'
            ''', (child_id,))
            row = cursor.fetchone()
            
            if row:
                child_data = dict(row)
                # Безопасно преобразуем interests из JSON
                child_data['interests'] = self._safe_json_loads(child_data.get('interests'))
                
                child = Child(
                    id=child_data['id'],
                    name=child_data['name'],
                    age=child_data['age'],
                    avatar=child_data.get('avatar', f"https://api.dicebear.com/7.x/adventurer/svg?seed={child_data['name']}"),
                    interests=child_data['interests'],
                    points=child_data.get('points', 0),
                    level=child_data.get('level', 1),
                    streak_days=child_data.get('streak_days', 0),
                    last_active=datetime.fromisoformat(child_data['last_active']).date() if child_data.get('last_active') else date.today()
                )
                self.children = {child.id: child}
                
                # Загружаем задания ребёнка
                self.tasks = self.load_tasks_from_db(child_id)
            
        except sqlite3.Error as e:
            logger.error(f"Database error in load_child_data: {e}")
        finally:
            conn.close()

    def load_family_data(self, parent_id: int):
        """Загрузить данные всей семьи для родителя"""
        from data.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Получаем всех детей родителя через запрос
            cursor.execute('''
                SELECT u.* FROM users u
                JOIN family_relations fr ON u.id = fr.child_id
                WHERE fr.parent_id = ? AND u.user_type = 'child'
            ''', (parent_id,))
            
            self.children = {}
            for row in cursor.fetchall():
                child_data = dict(row)
                # Безопасно преобразуем interests из JSON
                child_data['interests'] = self._safe_json_loads(child_data.get('interests'))
                
                child = Child(
                    id=child_data['id'],
                    name=child_data['name'],
                    age=child_data['age'],
                    avatar=child_data.get('avatar', f"https://api.dicebear.com/7.x/adventurer/svg?seed={child_data['name']}"),
                    interests=child_data['interests'],
                    points=child_data.get('points', 0),
                    level=child_data.get('level', 1),
                    streak_days=child_data.get('streak_days', 0),
                    last_active=datetime.fromisoformat(child_data['last_active']).date() if child_data.get('last_active') else date.today(),
                    parent_id=parent_id
                )
                self.children[child.id] = child
            
        except sqlite3.Error as e:
            logger.error(f"Database error in load_family_data: {e}")
        finally:
            conn.close()
    
    def update_child_points(self, child_id: int, points_to_add: int):
        """Обновить баллы ребёнка (используется из других модулей)"""
        child = self.children.get(child_id)
        if child:
            child.points += points_to_add
            child.level = self.calculate_level(child.points)
            
            # Обновляем в БД
            from data.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE users 
                    SET points = points + ?, level = ?
                    WHERE id = ?
                ''', (points_to_add, child.level, child_id))
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Database error in update_child_points: {e}")
                conn.rollback()
            finally:
                conn.close()