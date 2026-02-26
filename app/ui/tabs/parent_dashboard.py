"""
Панель управления родителя
"""
import streamlit as st
from core.auth_system import AuthSystem
from data.database import get_connection

def render_parent_dashboard(engine):
    st.subheader("👨‍👩‍👧‍👦 Родительский кабинет")
    
    # Инициализация
    if 'auth_system' not in st.session_state:
        st.session_state.auth_system = AuthSystem(get_connection())
    
    auth = st.session_state.auth_system
    
    # Проверяем, залогинен ли родитель
    if 'current_user' not in st.session_state:
        st.warning("Сначала войдите в систему")
        return
    
    current_user = st.session_state.current_user
    if current_user['user_type'] != 'parent':
        st.error("Этот раздел только для родителей")
        return
    
    # Панель управления для родителя
    st.success(f"👋 Вы вошли как {current_user['name']}")
    
    tab1, tab2, tab3 = st.tabs(["👥 Мои дети", "🔗 Пригласить", "⚙️ Настройки"])
    
    with tab1:
        st.subheader("👥 Мои дети")
        children = auth.get_children_for_parent(current_user['id'])
        
        if children:
            for child in children:
                with st.container():
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        avatar = child.get('avatar', f"https://api.dicebear.com/7.x/adventurer/svg?seed={child['name']}")
                        st.image(avatar, width=50)
                    with col2:
                        st.markdown(f"**{child['name']}** ({child['age']} лет)")
                        st.caption(f"Баллов: {child.get('points', 0)} • Уровень: {child.get('level', 1)}")
                    with col3:
                        if st.button("👀", key=f"view_{child['id']}"):
                            st.session_state.current_child = child['id']
                            st.success(f"Выбран профиль {child['name']}")
                    st.divider()
        else:
            st.info("У вас пока нет детей. Пригласите ребёнка!")
    
    with tab2:
        st.subheader("🔗 Пригласить ребёнка")
        
        with st.form("generate_invite"):
            child_name = st.text_input("Имя ребёнка (необязательно)", placeholder="Например: Саша")
            
            if st.form_submit_button("Сгенерировать код", use_container_width=True):
                code = auth.generate_invite_code(
                    current_user['id'], 
                    child_name if child_name else None
                )
                st.session_state.last_invite_code = code
                st.success("✅ Код сгенерирован!")
        
        if 'last_invite_code' in st.session_state:
            st.markdown("### 🎫 Ваш пригласительный код:")
            st.code(st.session_state.last_invite_code, language="text")
            st.caption("🔐 Код действителен 7 дней")
            
            st.info("""
            **Как подключить ребёнка:**
            1. Ребёнок открывает приложение
            2. Выбирает вкладку "🔗 У меня есть код"
            3. Вводит этот код и завершает регистрацию
            4. Ребёнок автоматически появится в списке "Мои дети"
            """)
    
    with tab3:
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
            del st.session_state.current_user
            if 'current_child' in st.session_state:
                del st.session_state.current_child
            st.rerun()