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

@dataclass
class Task:
    id: int
    title: str
    description: str
    category: str
    points: int
    difficulty: str
    emoji: str
    child_id: int
    created_at: datetime
    due_date: Optional[date] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    photo_required: bool = False
    photo_url: Optional[str] = None

@dataclass
class Child:
    id: int
    name: str
    age: int
    avatar: str
    interests: List[str]
    points: int = 0
    level: int = 1
    streak_days: int = 0
    last_active: date = date.today()

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
        
    def add_child(self, name: str, age: int, interests: List[str]) -> Child:
        child_id = len(self.children) + 1
        child = Child(
            id=child_id,
            name=name,
            age=age,
            avatar=f"https://api.dicebear.com/7.x/adventurer/svg?seed={name}",
            interests=interests
        )
        self.children[child_id] = child
        return child
    
    def create_task(self, **kwargs) -> Task:
        task_id = len(self.tasks) + 1
        task = Task(id=task_id, created_at=datetime.now(), **kwargs)
        self.tasks.append(task)
        return task
    
    def complete_task(self, task_id: int, child_id: int, photo_url: str = None) -> int:
        logger.info(f"✅ Task {task_id} completed by child {child_id}")
        task = next((t for t in self.tasks if t.id == task_id), None)
        if task and not task.completed:
            task.completed = True
            task.completed_at = datetime.now()
            task.photo_url = photo_url
            
            child = self.children[child_id]
            child.points += task.points
            child.level = self.calculate_level(child.points)
            
            # Проверка streak
            if child.last_active == date.today():
                child.streak_days += 1
            else:
                child.streak_days = 1
            child.last_active = date.today()
            
            return task.points
        return 0
    
    def calculate_level(self, points: int) -> int:
        """Расчёт уровня на основе баллов"""
        return points // 100 + 1
    
    def get_daily_tasks(self, child_id: int, count: int = 3) -> List[Task]:
        """Получить персонализированные задания на день"""
        # Загружаем из БД
        tasks = self.load_tasks_from_db(child_id)
        
        # Если заданий мало, создаём несколько стандартных
        if len(tasks) < count:
            # Здесь можно добавить логику генерации
            pass
        
        return tasks[:count]

    def load_children_from_db(self):
        """Загрузить всех детей из БД"""
        from data.database import ChildRepository
        
        children_data = ChildRepository.get_all()
        self.children = {}
        for child_data in children_data:
            # Преобразуем interests из JSON обратно в список
            if child_data['interests']:
                child_data['interests'] = json.loads(child_data['interests'])
            else:
                child_data['interests'] = []
            
            # Создаём объект Child
            child = Child(
                id=child_data['id'],
                name=child_data['name'],
                age=child_data['age'],
                avatar=child_data['avatar'],
                interests=child_data['interests'],
                points=child_data['points'],
                level=child_data['level'],
                streak_days=child_data['streak_days'],
                last_active=datetime.fromisoformat(child_data['last_active']).date()
            )
            self.children[child.id] = child

    
    def add_child_to_db(self, name: str, age: int, interests: List[str]) -> Child:
        """Добавить ребёнка в БД и в память"""
        from data.database import ChildRepository
        
        child_id = ChildRepository.create(name, age, interests)
        
        child = Child(
            id=child_id,
            name=name,
            age=age,
            avatar=f"https://api.dicebear.com/7.x/adventurer/svg?seed={name}",
            interests=interests,
            points=0,
            level=1,
            streak_days=0,
            last_active=date.today()
        )
        
        self.children[child_id] = child
        return child
    
    def save_task_to_db(self, task_data: Dict) -> Task:
        """Сохранить задание в БД"""
        from data.database import TaskRepository
        
        task_id = TaskRepository.create(task_data)
        
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
        
        return task
    
    def load_tasks_from_db(self, child_id: int) -> List[Task]:
        """Загрузить задания ребёнка из БД"""
        from data.database import TaskRepository
        
        tasks_data = TaskRepository.get_daily_tasks(child_id)
        tasks = []
        
        for task_data in tasks_data:
            task = Task(
                id=task_data['id'],
                title=task_data['title'],
                description=task_data['description'],
                category=task_data['category'],
                points=task_data['points'],
                difficulty=task_data['difficulty'],
                emoji=task_data['emoji'],
                photo_required=bool(task_data['photo_required']),
                child_id=task_data['child_id'],
                due_date=task_data.get('due_date'),
                completed=bool(task_data['completed']),
                completed_at=task_data.get('completed_at'),
                photo_url=task_data.get('photo_url'),
                created_at=datetime.fromisoformat(task_data['created_at']) if task_data['created_at'] else datetime.now()
            )
            tasks.append(task)
        
        return tasks
    
    def init_achievements(self, db_conn):
        """Инициализация системы достижений"""
        from data.database import get_connection
        self.achievement_system = AchievementSystem(get_connection())
        
    def complete_task(self, task_id: int, child_id: int, photo_url: str = None) -> Dict:
        """Расширенная версия с проверкой достижений"""
        from data.database import TaskRepository, ChildRepository
        
        # Получаем баллы за задание
        points = TaskRepository.complete_task(task_id, photo_url)
        
        if points > 0:
            # Собираем статистику для проверки достижений
            stats = self._collect_stats(child_id)
            
            # Проверяем новые достижения
            if self.achievement_system:
                new_achievements = self.achievement_system.check_and_unlock(child_id, stats)
                
                # Добавляем бонусные баллы за достижения
                total_reward = points
                for ach in new_achievements:
                    total_reward += ach.get('reward_points', 0)
                
                return {
                    'points': total_reward,
                    'new_achievements': new_achievements
                }
        
        return {'points': points, 'new_achievements': []}
    
    def _collect_stats(self, child_id: int) -> Dict:
        """Собрать статистику ребёнка для проверки достижений"""
        from data.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Общее количество выполненных заданий
        cursor.execute('''
            SELECT COUNT(*) FROM tasks 
            WHERE child_id = ? AND completed = 1
        ''', (child_id,))
        total_tasks = cursor.fetchone()[0]
        
        # Задания по категориям
        cursor.execute('''
            SELECT category, COUNT(*) FROM tasks 
            WHERE child_id = ? AND completed = 1
            GROUP BY category
        ''', (child_id,))
        category_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Текущие баллы и streak
        cursor.execute('''
            SELECT points, streak_days FROM children WHERE id = ?
        ''', (child_id,))
        child_data = cursor.fetchone()
        
        conn.close()
        
        stats = {
            'total_tasks': total_tasks,
            'total_points': child_data[0] if child_data else 0,
            'streak_days': child_data[1] if child_data else 0,
            **{f'category_{k}': v for k, v in category_stats.items()}
        }
        
        return stats
