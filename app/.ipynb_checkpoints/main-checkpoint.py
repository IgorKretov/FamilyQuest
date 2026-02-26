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

# ИМПОРТЫ МОДУЛЕЙ
from core.game_engine import GameEngine
from core.points_system import PointsCalculator
from ui.tabs.daily_tasks import render_daily_tasks
from ui.tabs.rewards import render_rewards
from ui.tabs.profile import render_profile
from ui.tabs.family import render_family
from ui.tabs.parent_dashboard import render_parent_dashboard
from ui.components import render_sidebar, load_css, render_add_child_form
from ui.tabs.create_task import render_create_task, render_task_library
from ui.tabs.achievements import render_achievements
from ui.tabs.ai_tasks import render_ai_tasks
from ui.tabs.child_connection import render_child_connection
from ui.effects import add_custom_css
from core.parent_mode import ParentMode, render_parent_login, render_parent_panel
from data.database import init_database, get_db_path, get_connection
from typing import Optional, Dict, List
from ui.auth.login_page import render_login_page
from core.auth_system import AuthSystem

# Инициализация базы данных
if 'db_initialized' not in st.session_state:
    init_database()
    st.session_state.db_initialized = True

# === СИСТЕМА АУТЕНТИФИКАЦИИ ===
# Проверяем, залогинен ли пользователь
if 'current_user' not in st.session_state:
    render_login_page()
    st.stop()  # Останавливаем выполнение дальше

# Получаем текущего пользователя
current_user = st.session_state.current_user

# Инициализация движка игры
if 'engine' not in st.session_state:
    st.session_state.engine = GameEngine()

# Загружаем данные в зависимости от типа пользователя
if current_user['user_type'] == 'child':
    # Для ребёнка загружаем его данные
    st.session_state.engine.load_child_data(current_user['id'])
    # Устанавливаем текущего ребёнка
    st.session_state.current_child = current_user['id']
else:
    # Для родителя загружаем всех его детей
    st.session_state.engine.load_family_data(current_user['id'])
    # Если есть дети, устанавливаем первого как текущего
    if st.session_state.engine.children:
        st.session_state.current_child = list(st.session_state.engine.children.keys())[0]

# Инициализация родительского режима
if 'parent_mode' not in st.session_state:
    st.session_state.parent_mode = ParentMode(get_db_path())
    st.session_state.parent_authenticated = False
    st.session_state.show_parent_login = False

# === ИНТЕРФЕЙС ===
# Шапка с информацией о пользователе
col1, col2, col3 = st.columns([6, 1, 1])
with col1:
    st.title(f"🎮 FamilyQuest - {current_user['name']}")
with col2:
    user_type_emoji = "👶" if current_user['user_type'] == 'child' else "👨‍👩‍👧"
    st.markdown(f"**{user_type_emoji} {current_user['user_type']}**")
with col3:
    if st.button("🚪 Выйти"):
        # Очищаем все данные сессии
        keys_to_delete = ['current_user', 'current_child', 'engine', 'parent_authenticated']
        for key in keys_to_delete:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Загрузка стилей
load_css()
add_custom_css()

# Родительский режим (только для родителей)
if current_user['user_type'] == 'parent':
    if st.session_state.get('show_parent_login', False) and not st.session_state.get('parent_authenticated', False):
        render_parent_login()
    elif st.session_state.get('parent_authenticated', False):
        render_parent_panel(st.session_state.engine, st.session_state.parent_mode)
        st.markdown("---")

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
        debug_vars = ['current_child', 'parent_authenticated', 'show_ai_task', 'show_quest']
        for key in debug_vars:
            if key in st.session_state:
                st.text(f"{key}: {st.session_state[key]}")
        
        # Показываем информацию о текущем пользователе
        if 'current_user' in st.session_state:
            st.text(f"current_user: {st.session_state.current_user['name']} ({st.session_state.current_user['user_type']})")
        
        # Показываем количество детей в движке
        if 'engine' in st.session_state:
            st.text(f"Детей в engine: {len(st.session_state.engine.children)}")

# Разный интерфейс для детей и родителей
if current_user['user_type'] == 'child':
    # === ИНТЕРФЕЙС ДЛЯ РЕБЁНКА ===
    
    # Проверяем, что текущий ребёнок загружен
    if st.session_state.current_child not in st.session_state.engine.children:
        st.error("Ошибка загрузки профиля. Пожалуйста, перезайдите.")
        if st.button("🔄 Перезайти"):
            del st.session_state.current_user
            st.rerun()
    else:
        # Боковая панель
        render_sidebar(st.session_state.engine, st.session_state.current_child)
        
        # Вкладки для ребёнка
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "📋 Задания",
            "✨ Создать",
            "🤖 ИИ-задания",
            "🏆 Достижения",
            "🎁 Награды",
            "👤 Профиль",
            "👨‍👩‍👧 Семья",
            "🔗 Подключить"
        ])
        
        with tab1:
            render_daily_tasks(st.session_state.engine, st.session_state.current_child)
        
        with tab2:
            subtab1, subtab2 = st.tabs(["✏️ Своё задание", "📚 Готовые шаблоны"])
            with subtab1:
                render_create_task(st.session_state.engine, st.session_state.current_child)
            with subtab2:
                render_task_library(st.session_state.engine, st.session_state.current_child)
        
        with tab3:
            render_ai_tasks(st.session_state.engine, st.session_state.current_child)
        
        with tab4:
            render_achievements(st.session_state.engine, st.session_state.current_child)
        
        with tab5:
            render_rewards(st.session_state.engine, st.session_state.current_child)
        
        with tab6:
            render_profile(st.session_state.engine, st.session_state.current_child)
        
        with tab7:
            render_family(st.session_state.engine, st.session_state.current_child)
        
        with tab8:
            render_child_connection(st.session_state.engine, st.session_state.current_child)

else:
    # === ИНТЕРФЕЙС ДЛЯ РОДИТЕЛЯ ===
    
    st.subheader("👨‍👩‍👧‍👦 Панель родителя")
    
    # Получаем детей родителя
    auth = AuthSystem(get_db_path())
    children = auth.get_children_for_parent(current_user['id'])
    
    if children:
        st.success(f"👋 У вас {len(children)} детей")
        
        # Выбор ребёнка для просмотра
        child_options = {f"{c['name']} ({c['age']} лет)": c['id'] for c in children}
        selected_child_name = st.selectbox("Выберите ребёнка", options=list(child_options.keys()))
        selected_child_id = child_options[selected_child_name]
        
        # Обновляем текущего ребёнка
        if st.session_state.current_child != selected_child_id:
            st.session_state.current_child = selected_child_id
            # Загружаем данные выбранного ребёнка в engine
            st.session_state.engine.load_child_data(selected_child_id)
            st.rerun()
        
        # Вкладки для родителя
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Прогресс",
            "📝 Задания",
            "🔗 Пригласить",
            "⚙️ Настройки"
        ])
        
        with tab1:
            st.subheader("📊 Прогресс ребёнка")
            
            # Получаем данные о ребёнке
            child = st.session_state.engine.children.get(selected_child_id)
            if child:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Баллы", child.points)
                with col2:
                    st.metric("Уровень", child.level)
                with col3:
                    st.metric("Дней подряд", child.streak_days)
                
                # Статистика по заданиям
                tasks = st.session_state.engine.get_daily_tasks(selected_child_id)
                total_tasks = len(tasks)
                completed_tasks = len([t for t in tasks if t.completed]) if tasks else 0
                
                if total_tasks > 0:
                    st.progress(completed_tasks / total_tasks, 
                               text=f"Выполнено {completed_tasks} из {total_tasks} заданий")
                else:
                    st.info("У ребёнка пока нет заданий")
        
        with tab2:
            st.subheader("📝 Управление заданиями")
            st.info("Здесь вы можете создавать задания для ребёнка")
            render_create_task(st.session_state.engine, selected_child_id)
            st.divider()
            render_task_library(st.session_state.engine, selected_child_id)
        
        with tab3:
            st.subheader("🔗 Пригласить ребёнка")
            
            if st.button("🎫 Сгенерировать код приглашения"):
                code = auth.generate_invite_code(current_user['id'])
                st.session_state.invite_code = code
                st.success("✅ Код сгенерирован!")
            
            if 'invite_code' in st.session_state:
                st.code(st.session_state.invite_code, language="text")
                st.caption("🔐 Код действителен 7 дней")
                
                st.info("""
                **Как подключить ребёнка:**
                1. Ребёнок открывает приложение и нажимает "У меня есть код"
                2. Вводит этот код и завершает регистрацию
                3. После подтверждения вы увидите его в списке детей
                """)
        
        with tab4:
            st.subheader("⚙️ Настройки")
            
            # Смена пароля
            with st.form("change_password"):
                st.markdown("#### Изменить пароль")
                current_password = st.text_input("Текущий пароль", type="password")
                new_password = st.text_input("Новый пароль", type="password")
                confirm_password = st.text_input("Подтвердите пароль", type="password")
                
                if st.form_submit_button("💾 Сохранить пароль", use_container_width=True):
                    # Проверяем текущий пароль
                    user = auth.login(current_user['username'], current_password)
                    if not user:
                        st.error("❌ Неверный текущий пароль")
                    elif new_password != confirm_password:
                        st.error("❌ Пароли не совпадают")
                    elif len(new_password) < 4:
                        st.error("❌ Пароль должен быть не менее 4 символов")
                    else:
                        # Здесь нужно добавить метод смены пароля в AuthSystem
                        st.info("Функция смены пароля будет добавлена")
            
            if st.button("🚪 Выйти из аккаунта", use_container_width=True):
                # Очищаем все данные сессии
                keys_to_delete = ['current_user', 'current_child', 'engine', 'parent_authenticated']
                for key in keys_to_delete:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    else:
        st.info("👋 У вас пока нет детей. Пригласите ребёнка!")
        
        if st.button("🎫 Сгенерировать код приглашения"):
            auth = AuthSystem(get_db_path())
            code = auth.generate_invite_code(current_user['id'])
            st.code(code, language="text")
            st.caption("🔐 Дайте этот код ребёнку, чтобы он подключился")

# Footer
st.markdown("---")
st.markdown("🌟 *Каждое задание делает тебя сильнее!*")