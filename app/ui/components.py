"""
Переиспользуемые компоненты интерфейса
"""
import streamlit as st

def render_sidebar(engine, child_id):
    """Отображение боковой панели с информацией о ребёнке"""
    child = engine.children.get(child_id)
    if not child:
        return
    
    with st.sidebar:
        st.image(f"https://api.dicebear.com/7.x/adventurer/svg?seed={child.name}", width=100)
        st.markdown(f"### {child.name}")
        
        # Прогресс-бар уровня
        points_in_level = child.points % 100
        st.progress(points_in_level / 100)
        st.caption(f"Уровень {child.level} • {points_in_level}%")
        
        # Метрики
        col1, col2 = st.columns(2)
        with col1:
            st.metric("⭐ Баллы", child.points)
        with col2:
            st.metric("🔥 Дней", child.streak_days)
        
        # Селектор детей
        render_child_selector(engine)
        
        st.markdown("---")
        st.caption(f"🎯 Интересы: {', '.join(child.interests)}")

    with st.sidebar:
        # ... существующие элементы ...
        
        st.markdown("---")
        
        # Кнопка родительского режима
        if not st.session_state.get('parent_authenticated', False):
            if st.button("👨‍👩‍👧 Родителям", use_container_width=True):
                st.session_state.show_parent_login = True
        else:
            # Показываем, что родительский режим активен
            st.success("👑 Режим родителя")
            if st.button("🚪 Выйти", use_container_width=True):
                st.session_state.parent_authenticated = False
                st.session_state.show_parent_login = False
                st.experimental_rerun()


def render_child_selector(engine):
    """Компонент для выбора и добавления детей"""
    st.markdown("### 👥 Дети")
    
    # Получаем список всех детей
    children = list(engine.children.values())
    
    if children:
        # Создаём словарь для выбора
        child_options = {f"{c.name} ({c.age} лет) ⭐{c.points}": c.id for c in children}
        
        # Определяем текущего ребёнка
        current_child_id = st.session_state.get('current_child')
        
        # Находим текущее значение в списке
        current_display = None
        for name, cid in child_options.items():
            if cid == current_child_id:
                current_display = name
                break
        
        if not current_display and child_options:
            current_display = list(child_options.keys())[0]
        
        # Выбор ребёнка
        selected = st.selectbox(
            "Выбери профиль",
            options=list(child_options.keys()),
            index=list(child_options.keys()).index(current_display) if current_display in list(child_options.keys()) else 0,
            key="child_selector_main"
        )
        
        # Обновляем только если изменилось
        if selected and child_options[selected] != current_child_id:
            st.session_state.current_child = child_options[selected]
            # Используем экспериментальный rerun только при реальном изменении
            st.experimental_rerun()
    
    # Кнопка добавления нового ребёнка
    if st.button("➕ Добавить ребёнка", use_container_width=True, key="add_child_btn"):
        st.session_state.show_add_child = True
        st.experimental_rerun()


def render_add_child_form(engine):
    """Форма добавления нового ребёнка"""
    with st.form("add_child_form"):
        st.subheader("👶 Новый герой")
        
        name = st.text_input("Имя ребёнка")
        age = st.number_input("Возраст", min_value=3, max_value=17, value=8)
        
        interests = st.multiselect(
            "Интересы (помогут подбирать задания)",
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
            if st.form_submit_button("✅ Добавить"):
                if name and interests:
                    child = engine.add_child_to_db(name, age, interests)
                    st.session_state.current_child = child.id
                    st.session_state.show_add_child = False
                    st.success(f"🎉 Добро пожаловать, {name}!")
                    st.experimental_rerun()
                else:
                    st.error("Заполни имя и выбери интересы!")
        
        with col2:
            if st.form_submit_button("❌ Отмена"):
                st.session_state.show_add_child = False
                st.experimental_rerun()

def load_css():
    """Загрузка кастомных CSS стилей"""
    st.markdown("""
    <style>
        /* Основные стили */
        .stButton > button {
            width: 100%;
            border-radius: 10px;
            height: 3em;
            font-size: 1.1em;
        }
        
        /* Карточки заданий */
        .task-card {
            background: white;
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 1rem 0;
            transition: transform 0.2s;
        }
        .task-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        
        /* Анимации */
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
        }
        .emoji-bounce {
            animation: bounce 1s infinite;
        }
        
        /* Мобильная адаптация */
        @media (max-width: 768px) {
            .stButton > button {
                font-size: 0.9em;
            }
        }
    </style>
    """, unsafe_allow_html=True)
