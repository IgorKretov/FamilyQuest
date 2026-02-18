"""
FamilyQuest - Главный файл приложения
"""
import streamlit as st
from datetime import datetime
from core.game_engine import GameEngine
from core.points_system import PointsCalculator
from ui.tabs.daily_tasks import render_daily_tasks
from ui.tabs.rewards import render_rewards
from ui.tabs.profile import render_profile
from ui.tabs.family import render_family
from ui.components import render_sidebar, load_css

# Инициализация базы данных при первом запуске
from data.database import init_database, ChildRepository, TaskRepository

# Создаём таблицы, если их нет
init_database()

# Настройка страницы
st.set_page_config(
    page_title="FamilyQuest",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Загрузка стилей
load_css()

# Инициализация сессии
if 'engine' not in st.session_state:
    st.session_state.engine = GameEngine()
    # Создаём тестового ребёнка
    st.session_state.engine.add_child("Саша", 8, ["creative", "science"])
    st.session_state.engine.create_task(
        title="Космический корабль",
        description="Построй корабль из картонной коробки",
        category="creative",
        points=50,
        difficulty="medium",
        emoji="🚀",
        photo_required=True
    )
    st.session_state.engine.create_task(
        title="Невидимое письмо",
        description="Напиши письмо лимонным соком",
        category="science",
        points=30,
        difficulty="easy",
        emoji="📝",
        photo_required=True
    )
    st.session_state.engine.create_task(
        title="Помощь на кухне",
        description="Приготовь бутерброды для семьи",
        category="help",
        points=40,
        difficulty="easy",
        emoji="🍳",
        photo_required=False
    )

if 'current_child' not in st.session_state:
    st.session_state.current_child = 1  # ID первого ребёнка

# Заголовок
st.title("🎮 FamilyQuest - Семейные приключения")

# Боковая панель с информацией о ребёнке
render_sidebar(st.session_state.engine, st.session_state.current_child)

# Основные вкладки
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Задания",
    "🎁 Награды",
    "👤 Профиль",
    "👨‍👩‍👧 Семья"
])

with tab1:
    render_daily_tasks(st.session_state.engine, st.session_state.current_child)

with tab2:
    render_rewards(st.session_state.engine, st.session_state.current_child)

with tab3:
    render_profile(st.session_state.engine, st.session_state.current_child)

with tab4:
    render_family(st.session_state.engine, st.session_state.current_child)

# Footer
st.markdown("---")
st.markdown("🌟 *Каждое задание делает тебя сильнее!*")
