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
from ui.tabs.create_task import render_create_task, render_task_library
from ui.tabs.achievements import render_achievements
from ui.effects import add_custom_css, play_success_effect, play_achievement_effect
from core.parent_mode import ParentMode, render_parent_login, render_parent_panel
from datetime import datetime, timedelta

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
add_custom_css()
# Инициализация сессии
# Инициализация сессии
if 'engine' not in st.session_state:
    st.session_state.engine = GameEngine()
    
    # Загружаем существующих детей из БД
    st.session_state.engine.load_children_from_db()
    
    # Если детей нет, создаём тестового
    if not st.session_state.engine.children:
        child = st.session_state.engine.add_child_to_db("Саша", 8, ["creative", "science"])
        
        # Создаём тестовые задания
        st.session_state.engine.save_task_to_db({
            "title": "Космический корабль",
            "description": "Построй корабль из картонной коробки",
            "category": "creative",
            "points": 50,
            "difficulty": "medium",
            "emoji": "🚀",
            "photo_required": True,
            "child_id": child.id
        })
        st.session_state.engine.save_task_to_db({
            "title": "Невидимое письмо",
            "description": "Напиши письмо лимонным соком",
            "category": "science",
            "points": 30,
            "difficulty": "easy",
            "emoji": "📝",
            "photo_required": True,
            "child_id": child.id
        })
        st.session_state.engine.save_task_to_db({
            "title": "Помощь на кухне",
            "description": "Приготовь бутерброды для семьи",
            "category": "help",
            "points": 40,
            "difficulty": "easy",
            "emoji": "🍳",
            "photo_required": False,
            "child_id": child.id
        })

if 'parent_mode' not in st.session_state:
    from data.database import get_connection
    st.session_state.parent_mode = ParentMode(get_connection())
    st.session_state.parent_authenticated = False
    st.session_state.show_parent_login = False

if st.session_state.get('show_parent_login', False) and not st.session_state.get('parent_authenticated', False):
    render_parent_login()
elif st.session_state.get('parent_authenticated', False):
    render_parent_panel(st.session_state.engine, st.session_state.parent_mode)
    st.markdown("---")
    
if 'current_child' not in st.session_state:
    # Берём первого ребёнка из списка
    if st.session_state.engine.children:
        st.session_state.current_child = list(st.session_state.engine.children.keys())[0]

# Отображение формы добавления ребёнка (если нужно)
if st.session_state.get('show_add_child', False):
    render_add_child_form(st.session_state.engine)

# Проверка, не истекла ли родительская сессия (через 5 минут)
if st.session_state.get('parent_authenticated', False):
    auth_time = st.session_state.get('parent_auth_time', datetime.now() - timedelta(minutes=10))
    if datetime.now() - auth_time > timedelta(minutes=5):
        st.session_state.parent_authenticated = False
        st.warning("⏰ Сессия родителя истекла. Войдите снова.")
        
# Заголовок
st.title("🎮 FamilyQuest - Семейные приключения")

# Боковая панель с информацией о ребёнке
render_sidebar(st.session_state.engine, st.session_state.current_child)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Задания",
    "✨ Создать",
    "🏆 Достижения",  # Новая вкладка
    "🎁 Награды",
    "👤 Профиль",
    "👨‍👩‍👧 Семья"
])

with tab1:
    render_daily_tasks(st.session_state.engine, st.session_state.current_child)

with tab2:
    # Две подвкладки: создание и библиотека
    subtab1, subtab2 = st.tabs(["✏️ Своё задание", "📚 Готовые шаблоны"])
    with subtab1:
        render_create_task(st.session_state.engine, st.session_state.current_child)
    with subtab2:
        render_task_library(st.session_state.engine, st.session_state.current_child)

with tab3:
    render_achievements(st.session_state.engine, st.session_state.current_child)

with tab4:
    render_profile(st.session_state.engine, st.session_state.current_child)

with tab5:
    render_family(st.session_state.engine, st.session_state.current_child)

# Footer
st.markdown("---")
st.markdown("🌟 *Каждое задание делает тебя сильнее!*")
