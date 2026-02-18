"""
Вкладка семейного соревнования
"""
import streamlit as st

def render_family(engine, child_id):
    st.subheader("👨‍👩‍👧 Семейный зачёт")
    
    if not engine.children:
        st.info("Добавьте членов семьи в настройках")
        return
    
    # Сортируем детей по баллам
    sorted_children = sorted(
        engine.children.values(), 
        key=lambda x: x.points, 
        reverse=True
    )
    
    st.markdown("### 🏆 Турнирная таблица")
    
    for idx, child in enumerate(sorted_children, 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "📱"
        highlight = child.id == child_id
        
        if highlight:
            st.markdown(f"""
            <div style="
                background: #e3f2fd;
                padding: 0.5rem;
                border-radius: 5px;
                margin: 0.2rem 0;
                border: 2px solid #4A90E2;
            ">
                {medal} <b>{child.name}</b> — {child.points} ⭐ (уровень {child.level})
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                background: #f5f5f5;
                padding: 0.5rem;
                border-radius: 5px;
                margin: 0.2rem 0;
            ">
                {medal} {child.name} — {child.points} ⭐ (уровень {child.level})
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("🔥 **Следующая цель:** Обогнать того, кто выше в таблице!")
