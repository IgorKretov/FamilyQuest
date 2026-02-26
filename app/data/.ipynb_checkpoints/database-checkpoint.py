"""
Подключение к SQLite и базовые операции
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import streamlit as st

DB_PATH = Path(__file__).parent.parent.parent / "familyquest.db"
_INITIALIZED = False  # Флаг для отслеживания инициализации

def get_connection():
    """Получить НОВОЕ соединение с БД для текущего потока"""
    DB_PATH = Path(__file__).parent.parent.parent / "familyquest.db"
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    # ВАЖНО: не кэшируем соединения!
    return conn
    
def get_db_path():
    """Вернуть путь к файлу БД"""
    return str(DB_PATH)

def init_database():
    """Создать таблицы, если их нет (безопасная версия)"""
    global _INITIALIZED
    
    # Если уже инициализировали в этой сессии — пропускаем
    if _INITIALIZED:
        return
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Таблица users (родители и дети) с ВСЕМИ необходимыми полями
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                user_type TEXT NOT NULL,  -- 'child' или 'parent'
                age INTEGER,              -- для детей
                interests TEXT,            -- для детей (JSON)
                avatar TEXT,
                points INTEGER DEFAULT 0,   -- баллы (для детей)
                level INTEGER DEFAULT 1,    -- уровень (для детей)
                streak_days INTEGER DEFAULT 0,  -- дней подряд (для детей)
                last_active TEXT,            -- последняя активность (для детей)
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица для связи родителей и детей (через user_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_relations (
                parent_id INTEGER,
                child_id INTEGER,
                status TEXT DEFAULT 'active',
                connected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES users (id),
                FOREIGN KEY (child_id) REFERENCES users (id),
                PRIMARY KEY (parent_id, child_id)
            )
        ''')
        
        # Таблица для заданий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,  -- Кому назначено (child)
                created_by INTEGER,         -- Кто создал (parent, может быть NULL)
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                points INTEGER,
                difficulty TEXT,
                emoji TEXT,
                photo_required INTEGER DEFAULT 0,
                due_date TEXT,
                completed INTEGER DEFAULT 0,
                completed_at TEXT,
                photo_url TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Таблица для приглашений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invitations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NOT NULL,
                invite_code TEXT UNIQUE NOT NULL,
                child_name TEXT,
                status TEXT DEFAULT 'pending',
                expires_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES users (id)
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
                FOREIGN KEY (child_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица достижений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER,
                achievement_id TEXT,
                unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (child_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица определений достижений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements_def (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                emoji TEXT,
                condition_type TEXT,
                condition_value INTEGER,
                reward_points INTEGER
            )
        ''')
        
        # Таблица child_parent (для обратной совместимости)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS child_parent (
                child_id INTEGER,
                parent_id INTEGER,
                status TEXT DEFAULT 'active',
                connected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (child_id) REFERENCES users (id),
                FOREIGN KEY (parent_id) REFERENCES users (id),
                PRIMARY KEY (child_id, parent_id)
            )
        ''')
        
        # Таблица children (для обратной совместимости со старым кодом)
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
                parent_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица родителей (для обратной совместимости)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                pin TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица app_settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Добавляем PIN по умолчанию, если нет
        cursor.execute('''
            INSERT OR IGNORE INTO app_settings (key, value)
            VALUES ('parent_pin', '1234')
        ''')
        
        conn.commit()
        conn.close()
        
        _INITIALIZED = True
        print(f"✅ База данных инициализирована: {DB_PATH}")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        _INITIALIZED = False

class ChildRepository:
    """Работа с детьми в БД"""
    
    @staticmethod
    def create(name: str, age: int, interests: List[str], parent_id: int = None) -> int:
        """Создать ребёнка (опционально с привязкой к родителю)"""
        conn = get_connection()
        cursor = conn.cursor()
        
        interests_json = json.dumps(interests, ensure_ascii=False)
        avatar = f"https://api.dicebear.com/7.x/adventurer/svg?seed={name}"
        last_active = datetime.now().date().isoformat()
        
        if parent_id:
            cursor.execute('''
                INSERT INTO children (name, age, avatar, interests, last_active, parent_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, age, avatar, interests_json, last_active, parent_id))
        else:
            cursor.execute('''
                INSERT INTO children (name, age, avatar, interests, last_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, age, avatar, interests_json, last_active))
        
        child_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return child_id
    
    @staticmethod
    def get_by_parent(parent_id: int) -> List[Dict]:
        """Получить детей конкретного родителя"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Пробуем выполнить запрос с parent_id
            cursor.execute('''
                SELECT * FROM children 
                WHERE parent_id = ? OR parent_id IS NULL
                ORDER BY points DESC
            ''', (parent_id,))
        except sqlite3.OperationalError as e:
            # Если колонки нет - используем старый метод
            if "no such column: parent_id" in str(e):
                cursor.execute('SELECT * FROM children ORDER BY points DESC')
            else:
                raise e
                
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
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
                user_id, title, description, category, points, difficulty, 
                emoji, photo_required, due_date, created_by
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
        conn.close()
        return task_id
    
    @staticmethod
    def get_daily_tasks(child_id: int, limit: int = 10) -> List[Dict]:
        """Получить активные задания на сегодня"""
        conn = get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        cursor.execute('''
            SELECT * FROM tasks 
            WHERE user_id = ? AND completed = 0 
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
        cursor.execute('SELECT points, user_id FROM tasks WHERE id = ?', (task_id,))
        task = cursor.fetchone()
        
        if not task:
            conn.close()
            return 0
        
        points = task['points']
        user_id = task['user_id']
        
        # Обновляем задание
        cursor.execute('''
            UPDATE tasks 
            SET completed = 1, completed_at = ?, photo_url = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), photo_url, task_id))
        
        conn.commit()
        conn.close()
        
        # Начисляем баллы ребёнку через users
        conn2 = get_connection()
        cursor2 = conn2.cursor()
        cursor2.execute('''
            UPDATE users 
            SET points = points + ?, 
                level = (points + ?) / 100 + 1,
                last_active = ?
            WHERE id = ?
        ''', (points, points, datetime.now().date().isoformat(), user_id))
        conn2.commit()
        conn2.close()
        
        return points