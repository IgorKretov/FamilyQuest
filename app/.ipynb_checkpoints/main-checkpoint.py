"""
FamilyQuest - Главный файл приложения
"""
import streamlit as st
from datetime import datetime, timedelta
import traceback
import logging
import sys

# ДОЛЖНО БЫТЬ ПЕРВОЙ КОМАНДОЙ STREAMLIT
st.set_page_config(
    page_title="FamilyQuest",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Импортируем логгер первым делом
from utils.logger import logger, log_rerun, display_rerun_log

# Логируем запуск приложения
logger.info("=" * 50)
logger.info("🚀 FamilyQuest starting...")
logger.info(f"Streamlit version: {st.__version__}")
logger.info("=" * 50)

# Настройка логирования для консоли
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Навигация по страницам
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'main'

# Функция для отслеживания rerun
def debug_rerun():
    """Детальное логирование причин rerun"""
    
    # Считаем rerun
    if 'debug_rerun_count' not in st.session_state:
        st.session_state.debug_rerun_count = 0
        st.session_state.debug_last_time = datetime.now()
    else:
        st.session_state.debug_rerun_count += 1
        now = datetime.now()
        delta = (now - st.session_state.debug_last_time).total_seconds()
        st.session_state.debug_last_time = now
        
        logger.debug(f"🔄 Rerun #{st.session_state.debug_rerun_count} (прошло {delta:.2f}с)")
        
        # Логируем, какие виджеты могли вызвать rerun
        form_keys = [k for k in st.session_state.keys() if 'FormSubmitter' in k]
        if form_keys:
            logger.debug(f"📝 Формы в session_state: {form_keys}")
        
        # Проверяем изменения в критических переменных
        watch_vars = ['show_ai_task', 'show_quest', 'show_story', 'generated_task']
        for var in watch_vars:
            if var in st.session_state:
                logger.debug(f"   {var} = {st.session_state[var]}")
        
        # Если rerun слишком частые
        if st.session_state.debug_rerun_count > 10 and delta < 0.5:
            logger.error("🚨 Очень частые rerun! Возможная рекурсия!")
            traceback.print_stack()

# Вызываем отладку
debug_rerun()

# ОТЛАДКА: логируем каждый запуск скрипта
if 'script_run_counter' not in st.session_state:
    st.session_state.script_run_counter = 0
    logger.info("🆕 First script run")
else:
    st.session_state.script_run_counter += 1
    logger.info(f"🔄 Script run #{st.session_state.script_run_counter}")

# Логируем состояние сессии
logger.debug(f"Session state keys: {list(st.session_state.keys())}")

# Если мы на странице подтверждения задания
if st.session_state.get('selected_task_id_for_completion'):
    # Импортируем здесь, чтобы избежать циклических импортов
    from ui.tabs.complete_task import show as show_complete_task
    show_complete_task()
    st.stop()  # Останавливаем выполнение, чтобы не показывать остальной контент

# Импортируем остальные модули (после проверки навигации)
from core.game_engine import GameEngine
from core.points_system import PointsCalculator
from ui.tabs.daily_tasks import render_daily_tasks
from ui.tabs.rewards import render_rewards
from ui.tabs.profile import render_profile
from ui.tabs.family import render_family
from ui.components import render_sidebar, load_css, render_add_child_form
from ui.tabs.create_task import render_create_task, render_task_library
from ui.tabs.achievements import render_achievements
from ui.tabs.ai_tasks import render_ai_tasks
from ui.effects import add_custom_css
from core.parent_mode import ParentMode, render_parent_login, render_parent_panel
from data.database import init_database, get_db_path

# Инициализация базы данных
if 'db_initialized' not in st.session_state:
    init_database()
    st.session_state.db_initialized = True

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
    st.session_state.parent_mode = ParentMode(get_db_path())
    st.session_state.parent_authenticated = False
    st.session_state.show_parent_login = False

if 'current_child' not in st.session_state:
    # Берём первого ребёнка из списка
    if st.session_state.engine.children:
        st.session_state.current_child = list(st.session_state.engine.children.keys())[0]

# Проверка родительской сессии
if st.session_state.get('parent_authenticated', False):
    auth_time = st.session_state.get('parent_auth_time')
    if auth_time and (datetime.now() - auth_time > timedelta(minutes=5)):
        st.session_state.parent_authenticated = False

# Загрузка стилей
load_css()
add_custom_css()

# Родительский режим
if st.session_state.get('show_parent_login', False) and not st.session_state.get('parent_authenticated', False):
    render_parent_login()
elif st.session_state.get('parent_authenticated', False):
    render_parent_panel(st.session_state.engine, st.session_state.parent_mode)
    st.markdown("---")

# Отображение формы добавления ребёнка
if st.session_state.get('show_add_child', False):
    render_add_child_form(st.session_state.engine)

# Заголовок
st.title("🎮 FamilyQuest - Семейные приключения")

# ОТЛАДОЧНАЯ ПАНЕЛЬ (только для разработки)
if st.checkbox("🔧 Показать отладочную информацию", value=False):
    with st.expander("🐛 Отладка", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Запусков скрипта", st.session_state.get('script_run_counter', 0))
            st.metric("Rerun сегодня", len(st.session_state.get('rerun_log', [])))
        with col2:
            if st.button("🧹 Очистить лог rerun"):
                st.session_state.rerun_log = []
                st.rerun()
        
        display_rerun_log()
        
        # Показываем ключевые переменные сессии
        st.subheader("📊 Session State")
        for key in ['current_child', 'parent_authenticated', 'show_ai_task', 'show_quest']:
            if key in st.session_state:
                st.text(f"{key}: {st.session_state[key]}")

# Боковая панель с информацией о ребёнке
render_sidebar(st.session_state.engine, st.session_state.current_child)

# Создаём 7 вкладок
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📋 Задания",
    "✨ Создать",
    "🤖 ИИ-задания",
    "🏆 Достижения",
    "🎁 Награды",
    "👤 Профиль",
    "👨‍👩‍👧 Семья"
])

# Вкладка 1: Задания
with tab1:
    render_daily_tasks(st.session_state.engine, st.session_state.current_child)

# Вкладка 2: Создание заданий
with tab2:
    subtab1, subtab2 = st.tabs(["✏️ Своё задание", "📚 Готовые шаблоны"])
    with subtab1:
        render_create_task(st.session_state.engine, st.session_state.current_child)
    with subtab2:
        render_task_library(st.session_state.engine, st.session_state.current_child)

# Вкладка 3: ИИ-задания
with tab3:
    render_ai_tasks(st.session_state.engine, st.session_state.current_child)

# Вкладка 4: Достижения
with tab4:
    render_achievements(st.session_state.engine, st.session_state.current_child)

# Вкладка 5: Награды
with tab5:
    render_rewards(st.session_state.engine, st.session_state.current_child)

# Вкладка 6: Профиль
with tab6:
    render_profile(st.session_state.engine, st.session_state.current_child)

# Вкладка 7: Семья
with tab7:
    render_family(st.session_state.engine, st.session_state.current_child)

# Footer
st.markdown("---")
st.markdown("🌟 *Каждое задание делает тебя сильнее!*")