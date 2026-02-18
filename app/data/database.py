"""
Подключение к SQLite и базовые операции
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

DB_PATH = Path(__file__).parent.parent.parent / "familyquest.db"

def get_connection():
    """Получить соединение с БД"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Создать таблицы, если их нет"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица детей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            avatar TEXT,
            interests TEXT,
            points INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            streak_days INTEGER DEFAULT 0,
            last_active TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица заданий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            points INTEGER,
            difficulty TEXT,
            emoji TEXT,
            photo_required INTEGER DEFAULT 0,
            child_id INTEGER,
            due_date TEXT,
            completed INTEGER DEFAULT 0,
            completed_at TEXT,
            photo_url TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children (id)
        )
    ''')
    
    # Таблица истории наград
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewards_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            reward_name TEXT,
            points_spent INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            achievement_id TEXT,
            unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children (id)
        )
    ''')
    
    #таблица с описанием достижений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements_def (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            emoji TEXT,
            condition_type TEXT,  -- tasks_completed, streak_days, points_total
            condition_value INTEGER,
            reward_points INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"✅ База данных инициализирована: {DB_PATH}")

class ChildRepository:
    """Работа с детьми в БД"""
    
    @staticmethod
    def create(name: str, age: int, interests: List[str]) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        
        interests_json = json.dumps(interests, ensure_ascii=False)
        avatar = f"https://api.dicebear.com/7.x/adventurer/svg?seed={name}"
        last_active = datetime.now().date().isoformat()
        
        cursor.execute('''
            INSERT INTO children (name, age, avatar, interests, last_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, age, avatar, interests_json, last_active))
        
        child_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return child_id
    
    @staticmethod
    def get_all() -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM children ORDER BY points DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_by_id(child_id: int) -> Optional[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM children WHERE id = ?', (child_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def update_points(child_id: int, points: int):
        conn = get_connection()
        cursor = conn.cursor()
        
        # Получаем текущие баллы
        cursor.execute('SELECT points FROM children WHERE id = ?', (child_id,))
        row = cursor.fetchone()
        current_points = row['points'] if row else 0
        
        new_points = current_points + points
        new_level = new_points // 100 + 1
        
        cursor.execute('''
            UPDATE children 
            SET points = ?, level = ?, last_active = ?
            WHERE id = ?
        ''', (new_points, new_level, datetime.now().date().isoformat(), child_id))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def update_streak(child_id: int, streak_days: int):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE children SET streak_days = ? WHERE id = ?', (streak_days, child_id))
        conn.commit()
        conn.close()

class TaskRepository:
    """Работа с заданиями в БД"""
    
    @staticmethod
    def create(task_data: Dict) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (
                title, description, category, points, difficulty, 
                emoji, photo_required, child_id, due_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_data['title'],
            task_data['description'],
            task_data['category'],
            task_data['points'],
            task_data['difficulty'],
            task_data['emoji'],
            1 if task_data.get('photo_required') else 0,
            task_data['child_id'],
            task_data.get('due_date')
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    @staticmethod
    def get_daily_tasks(child_id: int, limit: int = 3) -> List[Dict]:
        """Получить активные задания на сегодня"""
        conn = get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        cursor.execute('''
            SELECT * FROM tasks 
            WHERE child_id = ? AND completed = 0 
            AND (due_date IS NULL OR due_date >= ?)
            ORDER BY created_at DESC
            LIMIT ?
        ''', (child_id, today, limit))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def complete_task(task_id: int, photo_url: str = None) -> int:
        """Отметить задание выполненным и вернуть баллы"""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Получаем баллы за задание
        cursor.execute('SELECT points, child_id FROM tasks WHERE id = ?', (task_id,))
        task = cursor.fetchone()
        
        if not task:
            conn.close()
            return 0
        
        points = task['points']
        child_id = task['child_id']
        
        # Обновляем задание
        cursor.execute('''
            UPDATE tasks 
            SET completed = 1, completed_at = ?, photo_url = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), photo_url, task_id))
        
        conn.commit()
        conn.close()
        
        # Начисляем баллы ребёнку
        ChildRepository.update_points(child_id, points)
        
        return points
