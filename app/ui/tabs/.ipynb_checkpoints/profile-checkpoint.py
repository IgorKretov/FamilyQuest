"""
Вкладка профиля ребёнка
"""
import streamlit as st

def render_profile(engine, child_id):
    st.subheader("👤 Мой профиль")
    
    child = engine.children.get(child_id)
    if not child:
        st.error("Ребёнок не найден")
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(f"https://api.dicebear.com/7.x/adventurer/svg?seed={child.name}", width=150)
    
    with col2:
        st.markdown(f"### {child.name}, {child.age} лет")
        st.markdown(f"**Уровень:** {child.level}")
        st.markdown(f"**Опыт:** {child.points} ⭐")
        st.markdown(f"**Дней подряд:** {child.streak_days} 🔥")
        st.markdown(f"**Интересы:** {', '.join(child.interests)}")
    
    st.markdown("---")
    st.subheader("📊 Статистика")
    
    # Здесь можно добавить графики
    st.info("Скоро здесь появится статистика твоих достижений!")
