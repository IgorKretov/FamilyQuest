"""
Вкладка с наградами и магазином
"""
import streamlit as st

def render_rewards(engine, child_id):
    st.subheader("🎁 Магазин наград")
    
    # Получаем данные о ребёнке
    child = engine.children.get(child_id)
    if not child:
        st.error("Ребёнок не найден")
        return
    
    st.metric("Твои баллы", f"{child.points} ⭐", delta=None)
    
    # Пример списка наград
    rewards = [
        {"name": "30 мин в YouTube", "cost": 50, "emoji": "📱"},
        {"name": "Мороженое", "cost": 30, "emoji": "🍦"},
        {"name": "Поход в кино", "cost": 200, "emoji": "🎬"},
        {"name": "Новая игра", "cost": 500, "emoji": "🎮"},
    ]
    
    cols = st.columns(2)
    for idx, reward in enumerate(rewards):
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"""
                <div style="
                    background: white;
                    padding: 1rem;
                    border-radius: 10px;
                    margin: 0.5rem 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <h2 style="text-align: center;">{reward['emoji']}</h2>
                    <h4 style="text-align: center;">{reward['name']}</h4>
                    <p style="text-align: center; color: #4A90E2; font-weight: bold;">
                        {reward['cost']} ⭐
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Купить", key=f"buy_{idx}"):
                    if child.points >= reward['cost']:
                        st.success(f"✅ Ты купил {reward['name']}!")
                        # Здесь будет логика списания баллов
                    else:
                        st.error("❌ Не хватает баллов!")
