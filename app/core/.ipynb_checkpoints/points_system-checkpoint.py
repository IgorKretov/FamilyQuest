"""
Система подсчёта баллов и наград
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict

class RewardType(Enum):
    SCREEN_TIME = "screen_time"
    VIRTUAL_COIN = "virtual_coin"
    REAL_REWARD = "real_reward"

@dataclass
class Reward:
    id: int
    name: str
    type: RewardType
    cost: int
    description: str
    emoji: str
    quantity: int  # например, 30 минут, 50 монет

class PointsCalculator:
    def __init__(self):
        self.base_points = {
            "easy": 20,
            "medium": 35,
            "hard": 50
        }
        
        # Множители для разных факторов
        self.multipliers = {
            "streak": 0.1,      # +10% за каждый день streak
            "age_under_8": 1.3,  # +30% для малышей
            "age_over_12": 0.9,  # -10% для подростков
            "category_bonus": {
                "creative": 1.2,
                "help": 1.15,
                "learning": 1.1
            }
        }
    
    def calculate_task_points(self, difficulty: str, child_age: int, 
                            category: str, streak_days: int) -> int:
        """Расчёт баллов с учётом всех факторов"""
        points = self.base_points.get(difficulty, 30)
        
        # Множитель за категорию
        category_mult = self.multipliers["category_bonus"].get(category, 1.0)
        points *= category_mult
        
        # Множитель за возраст
        if child_age < 8:
            points *= self.multipliers["age_under_8"]
        elif child_age > 12:
            points *= self.multipliers["age_over_12"]
        
        # Бонус за streak
        streak_bonus = 1 + (streak_days * self.multipliers["streak"])
        points *= min(streak_bonus, 2.0)  # максимум x2
        
        return int(points)
    
    def get_next_level_requirements(self, current_points: int) -> Dict:
        """Получить требования для следующего уровня"""
        current_level = current_points // 100 + 1
        next_level = current_level + 1
        points_needed = next_level * 100 - current_points
        
        return {
            "current_level": current_level,
            "next_level": next_level,
            "points_needed": points_needed,
            "progress": (current_points % 100) / 100
        }
