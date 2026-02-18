"""
Ядро игровой логики FamilyQuest
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Dict, Optional
import random

@dataclass
class Task:
    id: int
    title: str
    description: str
    category: str
    points: int
    difficulty: str  # easy, medium, hard
    emoji: str
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
        child = self.children.get(child_id)
        if not child:
            return []
        
        # Фильтруем по интересам и возрасту
        suitable_tasks = []
        for task in self.tasks:
            if not task.completed:
                # Здесь можно добавить сложную логику подбора
                suitable_tasks.append(task)
        
        # Перемешиваем и берём нужное количество
        random.shuffle(suitable_tasks)
        return suitable_tasks[:count]
