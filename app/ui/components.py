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
        
        # Прогресс-бар уровня (БЕЗ ПАРАМЕТРА TEXT)
        points_in_level = child.points % 100
        st.progress(points_in_level / 100)
        # Текст выводим отдельно
        st.caption(f"Уровень {child.level} • {points_in_level}%")
        
        # Метрики
        col1, col2 = st.columns(2)
        with col1:
            st.metric("⭐ Баллы", child.points)
        with col2:
            st.metric("🔥 Дней", child.streak_days)
        
        st.markdown("---")
        st.caption(f"🎯 Интересы: {', '.join(child.interests)}")

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
