"""
Страница входа и регистрации
"""
import streamlit as st
from core.auth_system import AuthSystem
from data.database import get_connection

def render_login_page():
    """Главная страница аутентификации"""
    
    # Инициализация
    if 'auth_system' not in st.session_state:
        st.session_state.auth_system = AuthSystem(get_connection())
    
    auth = st.session_state.auth_system
    
    # Проверяем, есть ли уже залогиненный пользователь
    if 'current_user' in st.session_state:
        return  # Пользователь уже залогинен
    
    st.title("🎮 FamilyQuest")
    st.markdown("### Добро пожаловать!")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔐 Вход", 
        "👶 Я ребёнок", 
        "👨‍👩‍👧 Я родитель",
        "🔗 У меня есть код"
    ])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Имя пользователя")
            password = st.text_input("Пароль", type="password")
            
            if st.form_submit_button("Войти", use_container_width=True):
                user = auth.login(username, password)
                if user:
                    st.session_state.current_user = user
                    st.success(f"Добро пожаловать, {user['name']}!")
                    st.rerun()
                else:
                    st.error("Неверное имя пользователя или пароль")
    
    with tab2:
        st.markdown("#### Регистрация для детей")
        with st.form("register_child_form"):
            child_username = st.text_input("Придумай имя пользователя", 
                                          help="Например: sasha2008")
            child_password = st.text_input("Придумай пароль", type="password")
            child_age = st.number_input("Сколько тебе лет?", min_value=3, max_value=17, value=8)
            
            interests = st.multiselect(
                "Твои интересы (помогут подбирать задания)",
                options=["creative", "science", "sport", "art", "music", "nature", "help", "learning"],
                format_func=lambda x: {
                    "creative": "🎨 Творчество",
                    "science": "🔬 Наука",
                    "sport": "🏃 Спорт",
                    "art": "🖼️ Искусство",
                    "music": "🎵 Музыка",
                    "nature": "🌱 Природа",
                    "help": "🤝 Помощь",
                    "learning": "📚 Учёба"
                }.get(x, x)
            )
            
            if st.form_submit_button("Зарегистрироваться", use_container_width=True):
                if child_username and child_password and interests:
                    # Имя берётся из username для детей
                    user_id = auth.register_child(
                        child_username, child_password, child_username, child_age, interests
                    )
                    if user_id:
                        st.success("✅ Регистрация успешна! Теперь можешь войти.")
                    else:
                        st.error("❌ Имя пользователя уже занято")
                else:
                    st.error("Заполни все поля!")
    
    with tab3:
        st.markdown("#### Регистрация для родителей")
        with st.form("register_parent_form"):
            parent_username = st.text_input("Придумайте имя пользователя")
            parent_password = st.text_input("Придумайте пароль", type="password")
            
            if st.form_submit_button("Зарегистрироваться", use_container_width=True):
                if parent_username and parent_password:
                    # Для родителей имя тоже берётся из username
                    user_id = auth.register_parent(parent_username, parent_password, parent_username)
                    if user_id:
                        st.success("✅ Регистрация успешна! Теперь можете войти.")
                    else:
                        st.error("❌ Имя пользователя уже занято")
                else:
                    st.error("Заполните все поля!")
    
    with tab4:
        st.markdown("#### У меня есть код приглашения")
        st.info("Если родители дали тебе код, введи его здесь")
        
        # Проверяем, залогинен ли уже ребёнок
        if 'current_user' in st.session_state:
            st.warning("Сначала выйди из текущего аккаунта")
        else:
            with st.form("invite_form"):
                invite_code = st.text_input("Введи код", placeholder="FAM-XXXXXX")
                
                if st.form_submit_button("Подключиться к родителям", use_container_width=True):
                    st.session_state.pending_invite_code = invite_code
                    st.session_state.show_invite_registration = True
                    st.rerun()
    
    # Отдельная страница для регистрации по инвайту
    if st.session_state.get('show_invite_registration', False):
        st.markdown("---")
        st.subheader("📝 Заверши регистрацию")
        
        with st.form("invite_registration_form"):
            username = st.text_input("Придумай имя пользователя")
            password = st.text_input("Придумай пароль", type="password")
            age = st.number_input("Сколько тебе лет?", min_value=3, max_value=17, value=8)
            
            interests = st.multiselect(
                "Твои интересы",
                options=["creative", "science", "sport", "art", "music", "nature", "help", "learning"],
                format_func=lambda x: {
                    "creative": "🎨 Творчество",
                    "science": "🔬 Наука",
                    "sport": "🏃 Спорт",
                    "art": "🖼️ Искусство",
                    "music": "🎵 Музыка",
                    "nature": "🌱 Природа",
                    "help": "🤝 Помощь",
                    "learning": "📚 Учёба"
                }.get(x, x)
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Зарегистрироваться и подключиться"):
                    if username and password and interests:
                        # Регистрируем ребёнка
                        user_id = auth.register_child(
                            username, password, username, age, interests
                        )
                        if user_id:
                            # Принимаем инвайт
                            if auth.accept_invitation(st.session_state.pending_invite_code, user_id):
                                # Автоматически логиним
                                user = auth.login(username, password)
                                st.session_state.current_user = user
                                st.session_state.show_invite_registration = False
                                del st.session_state.pending_invite_code
                                st.success("✅ Ты подключён к родителям!")
                                st.rerun()
                            else:
                                st.error("❌ Неверный или просроченный код")
                        else:
                            st.error("❌ Имя пользователя уже занято")
                    else:
                        st.error("Заполни все поля!")
            
            with col2:
                if st.form_submit_button("❌ Отмена"):
                    st.session_state.show_invite_registration = False
                    if 'pending_invite_code' in st.session_state:
                        del st.session_state.pending_invite_code
                    st.rerun()