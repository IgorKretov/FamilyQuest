"""
Вкладка с достижениями
"""
import streamlit as st

def render_achievements(engine, child_id):
    st.subheader("🏆 Мои достижения")
    
    if not hasattr(engine, 'achievement_system') or not engine.achievement_system:
        st.info("Система достижений загружается...")
        return
    
    # Получаем разблокированные достижения
    unlocked = engine.achievement_system.get_unlocked_achievements(child_id)
    
    if not unlocked:
        st.info("🌟 Пока нет достижений. Выполняй задания, чтобы получить первые награды!")
    
    # Показываем достижения
    cols = st.columns(2)
    
    for idx, ach in enumerate(unlocked):
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 1.2rem;
                    border-radius: 15px;
                    margin: 0.5rem 0;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <h1 style="font-size: 2.5rem; text-align: center;">{ach['emoji']}</h1>
                    <h4 style="text-align: center; margin: 0;">{ach['name']}</h4>
                    <p style="text-align: center; font-size: 0.9rem; opacity: 0.9;">
                        {ach['description']}
                    </p>
                    <p style="text-align: center; font-size: 0.8rem;">
                        Получено: {ach['unlocked_at'][:10]}
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    # Показываем недоступные достижения (серые)
    st.markdown("---")
    st.subheader("🔒 Ещё можно получить")
    
    from app.core.achievements import ACHIEVEMENTS
    
    unlocked_ids = {a['achievement_id'] for a in unlocked}
    locked = [ach for aid, ach in ACHIEVEMENTS.items() if aid not in unlocked_ids]
    
    cols = st.columns(3)
    for idx, ach in enumerate(locked[:6]):  # Показываем только первые 6
        with cols[idx % 3]:
            st.markdown(f"""
            <div style="
                background: #f0f0f0;
                color: #999;
                padding: 1rem;
                border-radius: 10px;
                margin: 0.3rem 0;
                text-align: center;
                opacity: 0.7;
            ">
                <span style="font-size: 2rem;">{ach['emoji']}</span>
                <p style="margin: 0; font-weight: bold;">{ach['name']}</p>
                <p style="font-size: 0.8rem;">{ach['description']}</p>
            </div>
            """, unsafe_allow_html=True)
