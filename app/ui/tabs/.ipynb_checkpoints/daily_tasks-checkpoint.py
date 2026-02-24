"""
Вкладка с ежедневными заданиями (исправленная версия)
"""
import streamlit as st
from ui.effects import play_success_effect
from utils.logger import logger, log_function_call

def render_daily_tasks(engine, child_id):
    """Отображение ежедневных заданий"""
    log_function_call("render_daily_tasks")
    
    child = engine.children.get(child_id)
    if not child:
        st.error("Выбери профиль")
        return
    
    # ПРОСТОЕ СОСТОЯНИЕ - только один флаг
    if 'completing_task_id' not in st.session_state:
        st.session_state.completing_task_id = None
    
    # ПОЛУЧАЕМ ЗАДАНИЯ
    tasks = engine.get_daily_tasks(child_id)
    incomplete_tasks = [t for t in tasks if not t.completed]
    
    if not incomplete_tasks:
        st.success("🎉 Все задания на сегодня выполнены! Молодец!")
        return
    
    # ЕСЛИ МЫ В РЕЖИМЕ ПОДТВЕРЖДЕНИЯ - ПОКАЗЫВАЕМ ТОЛЬКО ЭКРАН ПОДТВЕРЖДЕНИЯ
    if st.session_state.completing_task_id:
        task = next((t for t in incomplete_tasks if t.id == st.session_state.completing_task_id), None)
        
        if task:
            st.markdown("---")
            st.markdown(f"### ✅ Подтверждение: {task.title}")
            st.markdown(f"**{task.description}**")
            st.markdown(f"⭐ Награда: **{task.points} баллов**")
            
            if task.photo_required:
                photo = st.camera_input("Сделай фото результата", key="completion_camera_unique")
                
                if photo:
                    with st.spinner("Обрабатываем..."):
                        # Вызываем complete_task без параметра photo_url или с корректным
                        result = engine.complete_task(task.id, child_id)
                        points = result['points'] if isinstance(result, dict) else result
                        
                        play_success_effect()
                        st.success(f"✅ Молодец! +{points} баллов!")
                        
                        # Сбрасываем состояние
                        st.session_state.completing_task_id = None
                        st.rerun()
            
            else:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Да, я выполнил", key="confirm_completion_unique", use_container_width=True):
                        with st.spinner("Обрабатываем..."):
                            result = engine.complete_task(task.id, child_id)
                            points = result['points'] if isinstance(result, dict) else result
                            
                            play_success_effect()
                            st.success(f"✅ Отлично! +{points} баллов!")
                            
                            st.session_state.completing_task_id = None
                            st.rerun()
                
                with col2:
                    if st.button("❌ Отмена", key="cancel_completion_unique", use_container_width=True):
                        st.session_state.completing_task_id = None
                        st.rerun()
            
            # Добавляем кнопку возврата к списку
            if st.button("← Вернуться к списку заданий", key="back_to_list_unique"):
                st.session_state.completing_task_id = None
                st.rerun()
        
        else:
            # Задание не найдено - сбрасываем
            st.session_state.completing_task_id = None
            st.rerun()
        
        return  # ВАЖНО: выходим, не показывая список
    
    # ПОКАЗЫВАЕМ СПИСОК НЕВЫПОЛНЕННЫХ ЗАДАНИЙ
    st.subheader(f"📋 Задания для {child.name}")
    st.caption(f"Осталось выполнить: {len(incomplete_tasks)}")
    
    for task in incomplete_tasks:
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.markdown(f"<h1 style='font-size: 2.5rem;'>{task.emoji}</h1>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"**{task.title}**")
                if task.description:
                    st.caption(task.description[:100] + "..." if len(task.description) > 100 else task.description)
                st.markdown(f"⭐ {task.points} баллов")
            
            with col3:
                # УНИКАЛЬНЫЙ КЛЮЧ для каждой кнопки
                if st.button("✅", key=f"complete_{task.id}", help="Отметить выполненным"):
                    st.session_state.completing_task_id = task.id
                    st.rerun()
            
            st.divider()