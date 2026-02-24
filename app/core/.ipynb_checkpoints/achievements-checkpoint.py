"""
Система достижений (ачивок)
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import streamlit as st

# Словарь всех доступных достижений
ACHIEVEMENTS = {
    "first_task": {
        "name": "Первый шаг",
        "description": "Выполни первое задание",
        "emoji": "🌟",
        "condition_type": "tasks_completed",
        "condition_value": 1,
        "reward_points": 10
    },
    "helper_10": {
        "name": "Помощник",
        "description": "Выполни 10 заданий",
        "emoji": "🤝",
        "condition_type": "tasks_completed",
        "condition_value": 10,
        "reward_points": 50
    },
    "helper_50": {
        "name": "Супер-помощник",
        "description": "Выполни 50 заданий",
        "emoji": "🏆",
        "condition_type": "tasks_completed",
        "condition_value": 50,
        "reward_points": 200
    },
    "streak_7": {
        "name": "Неделя без остановки",
        "description": "Выполняй задания 7 дней подряд",
        "emoji": "🔥",
        "condition_type": "streak_days",
        "condition_value": 7,
        "reward_points": 100
    },
    "streak_30": {
        "name": "Железный человек",
        "description": "Выполняй задания 30 дней подряд",
        "emoji": "⚡",
        "condition_type": "streak_days",
        "condition_value": 30,
        "reward_points": 500
    },
    "points_500": {
        "name": "500 баллов",
        "description": "Накопи 500 баллов",
        "emoji": "💎",
        "condition_type": "points_total",
        "condition_value": 500,
        "reward_points": 100
    },
    "points_1000": {
        "name": "1000 баллов",
        "description": "Накопи 1000 баллов",
        "emoji": "👑",
        "condition_type": "points_total",
        "condition_value": 1000,
        "reward_points": 200
    },
    "creative_genius": {
        "name": "Творческий гений",
        "description": "Выполни 5 творческих заданий",
        "emoji": "🎨",
        "condition_type": "category_tasks",
        "condition_value": 5,
        "category": "creative",
        "reward_points": 100
    },
    "scientist": {
        "name": "Юный учёный",
        "description": "Выполни 5 научных заданий",
        "emoji": "🔬",
        "condition_type": "category_tasks",
        "condition_value": 5,
        "category": "science",
        "reward_points": 100
    },
    "sport_champion": {
        "name": "Спортивный чемпион",
        "description": "Выполни 5 спортивных заданий",
        "emoji": "🏃",
        "condition_type": "category_tasks",
        "condition_value": 5,
        "category": "sport",
        "reward_points": 100
    }
}

class AchievementSystem:
    """Система проверки и выдачи достижений"""
    
    def __init__(self, db_connection):
        self.conn = db_connection
        self._init_achievements_def()
    
    def _init_achievements_def(self):
        """Инициализация таблицы с определениями достижений"""
        cursor = self.conn.cursor()
        
        for ach_id, ach_data in ACHIEVEMENTS.items():
            cursor.execute('''
                INSERT OR IGNORE INTO achievements_def 
                (id, name, description, emoji, condition_type, condition_value, reward_points)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                ach_id,
                ach_data['name'],
                ach_data['description'],
                ach_data['emoji'],
                ach_data['condition_type'],
                ach_data['condition_value'],
                ach_data.get('reward_points', 0)
            ))
        
        self.conn.commit()
    
    def check_and_unlock(self, child_id: int, stats: Dict) -> List[Dict]:
        """Проверить, какие достижения можно разблокировать"""
        cursor = self.conn.cursor()
        
        # Получаем уже разблокированные
        cursor.execute('SELECT achievement_id FROM achievements WHERE child_id = ?', (child_id,))
        unlocked = {row[0] for row in cursor.fetchall()}
        
        new_achievements = []
        
        for ach_id, ach_data in ACHIEVEMENTS.items():
            if ach_id in unlocked:
                continue
            
            unlocked_now = False
            
            # Проверяем условие
            if ach_data['condition_type'] == 'tasks_completed':
                if stats.get('total_tasks', 0) >= ach_data['condition_value']:
                    unlocked_now = True
            
            elif ach_data['condition_type'] == 'streak_days':
                if stats.get('streak_days', 0) >= ach_data['condition_value']:
                    unlocked_now = True
            
            elif ach_data['condition_type'] == 'points_total':
                if stats.get('total_points', 0) >= ach_data['condition_value']:
                    unlocked_now = True
            
            elif ach_data['condition_type'] == 'category_tasks':
                category = ach_data.get('category')
                if category and stats.get(f'category_{category}', 0) >= ach_data['condition_value']:
                    unlocked_now = True
            
            if unlocked_now:
                # Сохраняем в БД
                cursor.execute('''
                    INSERT INTO achievements (child_id, achievement_id)
                    VALUES (?, ?)
                ''', (child_id, ach_id))
                
                # Начисляем бонусные баллы
                if ach_data.get('reward_points', 0) > 0:
                    self._add_reward_points(child_id, ach_data['reward_points'])
                
                new_achievements.append({
                    'id': ach_id,
                    **ach_data
                })
        
        self.conn.commit()
        return new_achievements
    
    def _add_reward_points(self, child_id: int, points: int):
        """Добавить бонусные баллы за достижение"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE children SET points = points + ? WHERE id = ?', (points, child_id))
    
    def get_unlocked_achievements(self, child_id: int) -> List[Dict]:
        """Получить все разблокированные достижения ребёнка"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT a.achievement_id, a.unlocked_at, d.name, d.description, d.emoji, d.reward_points
            FROM achievements a
            JOIN achievements_def d ON a.achievement_id = d.id
            WHERE a.child_id = ?
            ORDER BY a.unlocked_at DESC
        ''', (child_id,))
        
        return [dict(row) for row in cursor.fetchall()]
