"""
Система аутентификации и связи родитель-ребёнок
"""
import streamlit as st
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from data.database import get_connection

class ParentManager:
    """Управление родителями и связями с детьми"""
    
    def __init__(self):
        # НЕ СОХРАНЯЕМ connection в объекте!
        pass
    
    def _get_connection(self):
        """Получить новое соединение с БД для текущего потока"""
        return get_connection()

    def get_invitation(self, invite_code: str) -> Optional[Dict]:
        """Получить информацию о приглашении по коду"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM invitations 
            WHERE invite_code = ? AND status = 'pending' 
            AND expires_at > datetime('now')
        ''', (invite_code,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def register_parent(self, email: str, name: str, pin: str) -> Optional[int]:
        """Регистрация нового родителя"""
        conn = self._get_connection()  # Новое соединение для этой операции
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO parents (email, name, pin)
                VALUES (?, ?, ?)
            ''', (email, name, pin))
            conn.commit()
            parent_id = cursor.lastrowid
            conn.close()
            return parent_id
        except Exception as e:
            conn.close()
            st.error(f"Ошибка регистрации: {e}")
            return None
    
    def login_parent(self, email: str, pin: str) -> Optional[Dict]:
        """Вход родителя по email и PIN"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM parents WHERE email = ? AND pin = ?
        ''', (email, pin))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def generate_invite_code(self, parent_id: int, child_name: str = None) -> str:
        """Сгенерировать пригласительный код для ребёнка"""
        # Код формата FAM-XXXXXX (6 случайных символов)
        code = 'FAM-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO invitations (parent_id, invite_code, child_name, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (parent_id, code, child_name, expires_at))
        conn.commit()
        conn.close()
        
        return code
    
    def accept_invitation(self, invite_code: str, child_id: int) -> bool:
        """Принять приглашение и связать ребёнка с родителем"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Проверяем код
        cursor.execute('''
            SELECT * FROM invitations 
            WHERE invite_code = ? AND status = 'pending' 
            AND expires_at > datetime('now')
        ''', (invite_code,))
        row = cursor.fetchone()
        invite = dict(row) if row else None
        
        if not invite:
            conn.close()
            return False
        
        # Создаём связь
        cursor.execute('''
            INSERT INTO child_parent (child_id, parent_id)
            VALUES (?, ?)
        ''', (child_id, invite['parent_id']))
        
        # Обновляем статус приглашения
        cursor.execute('''
            UPDATE invitations SET status = 'used' WHERE id = ?
        ''', (invite['id'],))
        
        conn.commit()
        conn.close()
        return True
    
    def get_children_for_parent(self, parent_id: int) -> List[Dict]:
        """Получить всех детей родителя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.* FROM children c
            JOIN child_parent cp ON c.id = cp.child_id
            WHERE cp.parent_id = ? AND cp.status = 'active'
        ''', (parent_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_parents_for_child(self, child_id: int) -> List[Dict]:
        """Получить всех родителей ребёнка"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.* FROM parents p
            JOIN child_parent cp ON p.id = cp.parent_id
            WHERE cp.child_id = ? AND cp.status = 'active'
        ''', (child_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]