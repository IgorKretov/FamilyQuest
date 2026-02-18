"""
Модели данных для SQLite
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List
import sqlite3
import json

@dataclass
class Child:
    id: Optional[int]
    name: str
    age: int
    avatar: str
    interests: str  # храним как JSON строку
    points: int
    level: int
    streak_days: int
    last_active: str  # ISO формат даты
    created_at: str

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            name=data['name'],
            age=data['age'],
            avatar=data['avatar'],
            interests=data['interests'],
            points=data['points'],
            level=data['level'],
            streak_days=data['streak_days'],
            last_active=data['last_active'],
            created_at=data['created_at']
        )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'avatar': self.avatar,
            'interests': self.interests,
            'points': self.points,
            'level': self.level,
            'streak_days': self.streak_days,
            'last_active': self.last_active,
            'created_at': self.created_at
        }

@dataclass
class Task:
    id: Optional[int]
    title: str
    description: str
    category: str
    points: int
    difficulty: str
    emoji: str
    photo_required: bool
    child_id: int
    due_date: Optional[str]
    completed: bool
    completed_at: Optional[str]
    photo_url: Optional[str]
    created_at: str

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'points': self.points,
            'difficulty': self.difficulty,
            'emoji': self.emoji,
            'photo_required': self.photo_required,
            'child_id': self.child_id,
            'due_date': self.due_date,
            'completed': self.completed,
            'completed_at': self.completed_at,
            'photo_url': self.photo_url,
            'created_at': self.created_at
        }
