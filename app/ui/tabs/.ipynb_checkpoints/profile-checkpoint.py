"""
Вкладка профиля ребёнка
"""
import streamlit as st
from datetime import datetime

def render_profile(engine, child_id):
    st.subheader("👤 Мой профиль")
    
    child = engine.children.get(child_id)
    if not child:
        st.error("👶 Ребёнок не найден. Возможно, нужно перезайти.")
        if st.button("🔄 Перезайти"):
            if 'current_user' in st.session_state:
                del st.session_state.current_user
            st.rerun()
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        avatar_url = child.avatar if hasattr(child, 'avatar') else f"https://api.dicebear.com/7.x/adventurer/svg?seed={child.name}"
        st.image(avatar_url, width=150)
    
    with col2:
        st.markdown(f"### {child.name}, {child.age} лет")
        st.markdown(f"**Уровень:** {child.level}")
        st.markdown(f"**Опыт:** {child.points} ⭐")
        st.markdown(f"**Дней подряд:** {child.streak_days} 🔥")
        if child.interests:
            interest_emojis = {
                "creative": "🎨 Творчество",
                "science": "🔬 Наука",
                "sport": "🏃 Спорт",
                "help": "🤝 Помощь",
                "learning": "📚 Учёба",
                "nature": "🌱 Природа",
                "art": "🎨 Искусство",
                "music": "🎵 Музыка"
            }
            interests_display = [interest_emojis.get(i, i) for i in child.interests]
            st.markdown(f"**Интересы:** {', '.join(interests_display)}")
    
    st.markdown("---")
    st.subheader("📊 Статистика")
    
    # Получаем задания для статистики
    tasks = engine.get_daily_tasks(child_id)
    total_tasks = len([t for t in engine.tasks if t.child_id == child_id])
    completed_tasks = len([t for t in engine.tasks if t.child_id == child_id and t.completed])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Всего заданий", total_tasks)
    with col2:
        st.metric("Выполнено", completed_tasks)
    with col3:
        if total_tasks > 0:
            percent = int(completed_tasks / total_tasks * 100)
            st.metric("Процент", f"{percent}%")
        else:
            st.metric("Процент", "0%")
    
    # График прогресса по категориям (упрощённо)
    if completed_tasks > 0:
        st.subheader("🏆 Достижения")
        st.info("🎉 Ты молодец! Продолжай в том же духе!")

def render_child_connection(engine, child_id):
    """Интерфейс для подключения к родителю"""
    from core.auth import ParentManager
    
    pm = ParentManager()  # Без параметров!
    
    st.subheader("🔗 Связать с родителем")
    
    # Проверяем, есть ли уже родители
    parents = pm.get_parents_for_child(child_id)
    
    if parents:
        st.success("✅ Вы уже связаны с родителями:")
        for p in parents:
            st.write(f"• {p['name']} ({p['email']})")
        
        if st.button("➕ Подключить ещё одного родителя"):
            st.session_state.show_invite_form = True
    
    if st.session_state.get('show_invite_form', False) or not parents:
        with st.form("connect_parent"):
            invite_code = st.text_input("Введите пригласительный код", 
                                        placeholder="FAM-XXXXXX",
                                        help="Код можно получить у родителей")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Подключиться", use_container_width=True):
                    if pm.accept_invitation(invite_code, child_id):
                        st.success("✅ Родитель подключён!")
                        st.session_state.show_invite_form = False
                        st.rerun()
                    else:
                        st.error("❌ Неверный или просроченный код")
            with col2:
                if st.form_submit_button("Отмена", use_container_width=True):
                    st.session_state.show_invite_form = False
                    st.rerun()