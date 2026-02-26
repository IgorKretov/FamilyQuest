"""
Регистрация нового ребёнка
"""
import streamlit as st
from core.auth import ParentManager

def render_child_registration(engine):
    st.subheader("👶 Регистрация нового героя")
    
    # Проверяем, есть ли активный родитель
    parent_id = st.session_state.get('parent_id')
    parent_manager = ParentManager()
    
    # Если есть код приглашения в сессии, запоминаем
    if 'pending_invite' not in st.session_state:
        st.session_state.pending_invite = None
    
    # Форма регистрации
    with st.form("child_registration_form"):
        st.markdown("### Давай познакомимся!")
        
        name = st.text_input("Как тебя зовут?", placeholder="Например: Саша")
        age = st.number_input("Сколько тебе лет?", min_value=3, max_value=17, value=8)
        
        st.markdown("### Что тебе нравится делать?")
        interests = st.multiselect(
            "Интересы",
            options=["creative", "science", "sport", "art", "music", "nature", "help", "learning"],
            format_func=lambda x: {
                "creative": "🎨 Рисовать, лепить, мастерить",
                "science": "🔬 Проводить опыты, изучать науку",
                "sport": "🏃 Бегать, прыгать, заниматься спортом",
                "art": "🖼️ Искусство, театр, танцы",
                "music": "🎵 Музыка, пение, игра на инструментах",
                "nature": "🌱 Природа, животные, растения",
                "help": "🤝 Помогать по дому, заботиться о других",
                "learning": "📚 Учиться, читать, решать задачи"
            }.get(x, x)
        )
        
        # Поле для кода приглашения (если есть)
        st.markdown("### 🔗 Есть код приглашения от родителей?")
        invite_code = st.text_input("Введи код (если есть)", 
                                    placeholder="FAM-XXXXXX",
                                    value=st.session_state.pending_invite if st.session_state.pending_invite else "")
        
        if st.form_submit_button("✨ Создать мой профиль", type="primary", use_container_width=True):
            if name and interests:
                # Проверяем код приглашения
                connected_parent = None
                if invite_code:
                    # Пытаемся найти родителя по коду
                    invite = parent_manager.get_invitation(invite_code)
                    if invite and invite['status'] == 'pending':
                        connected_parent = invite['parent_id']
                        st.success("✅ Код приглашения действителен!")
                    else:
                        st.warning("⚠️ Код недействителен. Ты сможешь подключить родителей позже.")
                
                # Создаём ребёнка (с привязкой к родителю, если есть код)
                child = engine.add_child_to_db(
                    name, 
                    age, 
                    interests, 
                    parent_id=connected_parent or parent_id
                )
                
                # Если есть код, активируем приглашение
                if connected_parent and invite_code:
                    parent_manager.accept_invitation(invite_code, child.id)
                
                # Устанавливаем текущим ребёнком
                st.session_state.current_child = child.id
                st.session_state.show_registration = False
                st.session_state.pending_invite = None
                
                st.success(f"🎉 Добро пожаловать, {name}!")
                st.balloons()
                st.rerun()
            else:
                if not name:
                    st.error("Пожалуйста, введи своё имя!")
                if not interests:
                    st.error("Выбери хотя бы один интерес!")