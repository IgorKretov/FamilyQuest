"""
Родительский режим с PIN-кодом
"""
import streamlit as st
from datetime import datetime, timedelta
import hashlib

class ParentMode:
    def __init__(self, db_conn):
        self.conn = db_conn
        self._init_settings()
    
    def _init_settings(self):
        """Инициализация настроек"""
        cursor = self.conn.cursor()
        
        # Создаём таблицу если нет
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Добавляем PIN по умолчанию
        cursor.execute('''
            INSERT OR IGNORE INTO app_settings (key, value)
            VALUES ('parent_pin', '1234')
        ''')
        
        self.conn.commit()
    
    def check_pin(self, pin: str) -> bool:
        """Проверка PIN-кода"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM app_settings WHERE key = ?', ('parent_pin',))
        result = cursor.fetchone()
        return result and result[0] == pin
    
    def set_pin(self, new_pin: str) -> bool:
        """Установка нового PIN"""
        if len(new_pin) != 4 or not new_pin.isdigit():
            return False
        
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE app_settings 
            SET value = ?, updated_at = CURRENT_TIMESTAMP
            WHERE key = ?
        ''', (new_pin, 'parent_pin'))
        self.conn.commit()
        return True
    
    def get_settings(self) -> dict:
        """Получить все настройки"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT key, value FROM app_settings')
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def update_setting(self, key: str, value: str):
        """Обновить настройку"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO app_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        self.conn.commit()

def render_parent_login():
    """Рендеринг экрана входа для родителей"""
    with st.container():
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
            color: white;
            margin: 2rem 0;
        ">
            <h1>👨‍👩‍👧 Родительский режим</h1>
            <p>Введите PIN-код для доступа к настройкам</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("parent_login"):
            pin = st.text_input("PIN-код", type="password", max_chars=4)
            col1, col2, col3 = st.columns(3)
            with col2:
                submitted = st.form_submit_button("🔐 Войти")
            
            if submitted:
                if st.session_state.parent_mode.check_pin(pin):
                    st.session_state.parent_authenticated = True
                    st.session_state.parent_auth_time = datetime.now()
                    st.success("✅ Добро пожаловать, родитель!")
                    st.experimental_rerun()
                else:
                    st.error("❌ Неверный PIN-код")

def render_parent_panel(engine, parent_mode):
    """Рендеринг панели родителя"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin: 1rem 0;
    ">
        <h2>⚙️ Панель управления</h2>
    </div>
    """, unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Дети", "🔐 Настройки", "📊 Статистика", "📤 Экспорт"])
    
    with tab1:
        st.subheader("Управление детьми")
        
        # Список всех детей
        children = list(engine.children.values())
        
        for child in children:
            with st.expander(f"{child.name} ({child.age} лет)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Баллы", child.points)
                    st.metric("Уровень", child.level)
                with col2:
                    st.metric("Дней подряд", child.streak_days)
                    st.metric("Заданий выполнено", 
                             len([t for t in engine.tasks if t.child_id == child.id and t.completed]))
                
                if st.button(f"🔄 Сбросить прогресс {child.name}", key=f"reset_{child.id}"):
                    if st.session_state.get(f"confirm_reset_{child.id}", False):
                        # Здесь логика сброса
                        st.warning("Функция сброса будет добавлена")
                    else:
                        st.session_state[f"confirm_reset_{child.id}"] = True
                        st.warning("Нажмите ещё раз для подтверждения")
    
    with tab2:
        st.subheader("Настройки приложения")
        
        # Смена PIN
        with st.form("change_pin"):
            st.markdown("#### Изменить PIN-код")
            current_pin = st.text_input("Текущий PIN", type="password", max_chars=4)
            new_pin = st.text_input("Новый PIN (4 цифры)", type="password", max_chars=4)
            confirm_pin = st.text_input("Подтвердите PIN", type="password", max_chars=4)
            
            if st.form_submit_button("💾 Сохранить PIN"):
                if not parent_mode.check_pin(current_pin):
                    st.error("Неверный текущий PIN")
                elif new_pin != confirm_pin:
                    st.error("PIN-коды не совпадают")
                elif len(new_pin) != 4 or not new_pin.isdigit():
                    st.error("PIN должен состоять из 4 цифр")
                else:
                    parent_mode.set_pin(new_pin)
                    st.success("✅ PIN-код успешно изменён!")
        
        # Другие настройки
        st.markdown("---")
        st.markdown("#### Ограничения")
        
        daily_limit = st.number_input("Лимит экранного времени в день (минут)", 
                                      min_value=30, max_value=300, value=120, step=15)
        if st.button("💾 Сохранить лимит"):
            parent_mode.update_setting('daily_limit', str(daily_limit))
            st.success("✅ Лимит сохранён")
        
        weekend_bonus = st.checkbox("➕ Давать бонусные баллы в выходные", value=True)
        if st.button("💾 Сохранить"):
            parent_mode.update_setting('weekend_bonus', str(weekend_bonus))
            st.success("✅ Настройка сохранена")
    
    with tab3:
        st.subheader("Статистика использования")
        
        # График активности по дням
        st.markdown("#### Активность за последние 7 дней")
        
        # Здесь будет график
        st.info("📊 Скоро здесь появится график активности")
        
        # Общая статистика
        total_tasks = sum(1 for t in engine.tasks if t.completed)
        total_points = sum(c.points for c in engine.children.values())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Всего детей", len(engine.children))
        with col2:
            st.metric("Выполнено заданий", total_tasks)
        with col3:
            st.metric("Всего баллов", total_points)
        
        # Экспорт данных
        if st.button("📥 Экспортировать статистику (CSV)"):
            # Здесь будет экспорт
            st.success("Функция экспорта будет добавлена")

    with tab4:
        from utils.export import DataExporter, render_export_section
        from data.database import get_connection
        
        exporter = DataExporter(st.session_state.engine, get_connection())
        render_export_section(exporter)
