"""
Система аутентификации пользователей
"""
import streamlit as st
import hashlib
import random
import string
import json
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List
import sqlite3
from data.database import get_connection

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

class AuthSystem:
    """Система аутентификации"""
    
    def __init__(self, db_path=None):
        """Инициализация - сохраняем путь к БД, но НЕ создаём соединение"""
        self.db_path = db_path
    
    def _get_connection(self):
        """Создаём НОВОЕ соединение для каждого запроса"""
        from data.database import get_connection
        return get_connection()
    
    def register_child(self, username: str, password: str, name: str, age: int, interests: List[str]) -> Optional[int]:
        """Регистрация нового ребёнка"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            password_hash = hash_password(password)
            interests_json = json.dumps(interests, ensure_ascii=False)
            avatar = f"https://api.dicebear.com/7.x/adventurer/svg?seed={username}"
            last_active = date.today().isoformat()
            
            cursor.execute('''
                INSERT INTO users (
                    username, password_hash, name, user_type, age, interests, avatar,
                    points, level, streak_days, last_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                username, password_hash, name, 'child', age, interests_json, avatar,
                0, 1, 0, last_active
            ))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
            
        except sqlite3.IntegrityError as e:
            print(f"IntegrityError: {e}")
            conn.close()
            return None
        except Exception as e:
            print(f"Exception: {e}")
            conn.close()
            raise e
        
    def register_parent(self, username: str, password: str, name: str) -> Optional[int]:
        """Регистрация нового родителя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            password_hash = hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, name, user_type)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, name, 'parent'))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
            
        except sqlite3.IntegrityError:
            conn.close()
            return None
        except Exception as e:
            conn.close()
            raise e
    
    def login(self, username: str, password: str) -> Optional[Dict]:
        """Вход пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        password_hash = hash_password(password)
        
        cursor.execute('''
            SELECT * FROM users WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        row = cursor.fetchone()
        
        if row:
            user = dict(row)
            # Преобразуем interests обратно в список для детей
            if user['user_type'] == 'child' and user.get('interests'):
                try:
                    user['interests'] = json.loads(user['interests'])
                except (json.JSONDecodeError, TypeError):
                    user['interests'] = []
            
            # Убедимся, что числовые поля существуют
            if 'points' not in user or user['points'] is None:
                user['points'] = 0
            if 'level' not in user or user['level'] is None:
                user['level'] = 1
            if 'streak_days' not in user or user['streak_days'] is None:
                user['streak_days'] = 0
            
            conn.close()
            return user
        
        conn.close()
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Получить пользователя по ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            user = dict(row)
            if user['user_type'] == 'child' and user.get('interests'):
                try:
                    user['interests'] = json.loads(user['interests'])
                except (json.JSONDecodeError, TypeError):
                    user['interests'] = []
            
            # Убедимся, что числовые поля существуют
            if 'points' not in user or user['points'] is None:
                user['points'] = 0
            if 'level' not in user or user['level'] is None:
                user['level'] = 1
            if 'streak_days' not in user or user['streak_days'] is None:
                user['streak_days'] = 0
            
            conn.close()
            return user
        
        conn.close()
        return None
    
    def generate_invite_code(self, parent_id: int, child_name: str = None) -> str:
        """Сгенерировать код приглашения для ребёнка"""
        code = 'FAM-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO invitations (parent_id, invite_code, child_name, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (parent_id, code, child_name, expires_at))
            
            conn.commit()
            conn.close()
            return code
            
        except Exception as e:
            conn.close()
            raise e
    
    def accept_invitation(self, invite_code: str, child_id: int) -> bool:
        """Принять приглашение и связать с родителем"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверяем код
            cursor.execute('''
                SELECT * FROM invitations 
                WHERE invite_code = ? AND status = 'pending' 
                AND expires_at > datetime('now')
            ''', (invite_code,))
            invite = cursor.fetchone()
            
            if not invite:
                conn.close()
                return False
            
            # Создаём связь
            cursor.execute('''
                INSERT INTO family_relations (parent_id, child_id, status)
                VALUES (?, ?, 'active')
            ''', (invite['parent_id'], child_id))
            
            # Обновляем статус приглашения
            cursor.execute('''
                UPDATE invitations SET status = 'used' WHERE id = ?
            ''', (invite['id'],))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            conn.rollback()
            conn.close()
            raise e
    
    def get_children_for_parent(self, parent_id: int) -> List[Dict]:
        """Получить всех детей родителя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT u.* FROM users u
                JOIN family_relations fr ON u.id = fr.child_id
                WHERE fr.parent_id = ? AND fr.status = 'active' AND u.user_type = 'child'
            ''', (parent_id,))
            
            children = []
            for row in cursor.fetchall():
                child = dict(row)
                if child.get('interests'):
                    try:
                        child['interests'] = json.loads(child['interests'])
                    except (json.JSONDecodeError, TypeError):
                        child['interests'] = []
                
                # Убедимся, что числовые поля существуют
                if 'points' not in child or child['points'] is None:
                    child['points'] = 0
                if 'level' not in child or child['level'] is None:
                    child['level'] = 1
                if 'streak_days' not in child or child['streak_days'] is None:
                    child['streak_days'] = 0
                
                children.append(child)
            
            conn.close()
            return children
            
        except Exception as e:
            conn.close()
            raise e
    
    def get_parents_for_child(self, child_id: int) -> List[Dict]:
        """Получить всех родителей ребёнка"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT u.* FROM users u
                JOIN family_relations fr ON u.id = fr.parent_id
                WHERE fr.child_id = ? AND fr.status = 'active' AND u.user_type = 'parent'
            ''', (child_id,))
            
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
            
        except Exception as e:
            conn.close()
            raise e
    
    def update_child_points(self, child_id: int, points_to_add: int) -> bool:
        """Обновить баллы ребёнка"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Получаем текущие баллы
            cursor.execute('SELECT points FROM users WHERE id = ?', (child_id,))
            row = cursor.fetchone()
            current_points = row['points'] if row else 0
            
            new_points = current_points + points_to_add
            new_level = new_points // 100 + 1
            
            cursor.execute('''
                UPDATE users 
                SET points = ?, level = ?, last_active = ?
                WHERE id = ?
            ''', (new_points, new_level, date.today().isoformat(), child_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            conn.close()
            return False