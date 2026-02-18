"""
Вкладка с ежедневными заданиями
"""
import streamlit as st
from datetime import datetime
from app.core.game_engine import GameEngine

def render_daily_tasks(engine: GameEngine, child_id: int):
    st.subheader("📋 Задания на сегодня")
    
    # Получаем задания для ребёнка
    tasks = engine.get_daily_tasks(child_id)
    
    if not tasks:
        st.info("🎉 На сегодня заданий нет! Отдыхай!")
        return
    
    # Создаём колонки для заданий
    cols = st.columns(len(tasks))
    
    for idx, (col, task) in enumerate(zip(cols, tasks)):
        with col:
            # Карточка задания
            with st.container():
                st.markdown(f"""
                <div style="
                    background: white;
                    padding: 1rem;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                ">
                    <h1 style="font-size: 3rem;">{task.emoji}</h1>
                    <h3>{task.title}</h3>
                    <p>{task.description}</p>
                    <p style="font-size: 1.5rem; color: #4A90E2;">+{task.points} ⭐</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Кнопка выполнения
                if st.button(f"✅ Выполнил", key=f"task_{task.id}"):
                    st.session_state.current_task = task
                    st.session_state.show_completion = True
    
    # Модальное окно для подтверждения выполнения
    if st.session_state.get("show_completion", False):
        with st.expander("📸 Подтверди выполнение", expanded=True):
            task = st.session_state.current_task
            
            if task.photo_required:
                photo = st.camera_input("Сделай фото")
                if photo:
                    # Здесь будет сохранение фото
                    points = engine.complete_task(task.id, child_id, "photo_url")
                    st.success(f"✅ Молодец! +{points} баллов!")
                    st.balloons()
                    st.session_state.show_completion = False
                    st.rerun()
            else:
                if st.button("Да, я выполнил задание"):
                    points = engine.complete_task(task.id, child_id)
                    st.success(f"✅ Отлично! +{points} баллов!")
                    st.balloons()
                    st.session_state.show_completion = False
                    st.experimental_rerun()
