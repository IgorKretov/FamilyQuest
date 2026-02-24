"""
Страница подтверждения выполнения задания
"""
import streamlit as st
from datetime import datetime
import sys
import os

# Добавляем путь к корневой папке проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.effects import play_success_effect
from utils.logger import logger

def main():
    st.set_page_config(page_title="Подтверждение задания", page_icon="✅")
    
    # Проверяем наличие выбранного задания
    if 'selected_task_id_for_completion' not in st.session_state or not st.session_state.selected_task_id_for_completion:
        st.error("Не выбрано задание для выполнения")
        if st.button("← Вернуться к заданиям"):
            st.switch_page("app/main.py")
        return
    
    # Получаем данные из главного приложения
    engine = st.session_state.get('engine')
    child_id = st.session_state.get('current_child')
    
    if not engine or not child_id:
        st.error("Ошибка: данные не найдены")
        if st.button("← Вернуться к заданиям"):
            st.switch_page("app/main.py")
        return
    
    # Получаем задание
    task_id = st.session_state.selected_task_id_for_completion
    tasks = engine.get_daily_tasks(child_id)
    task = next((t for t in tasks if t.id == task_id), None)
    
    if not task:
        st.error("Задание не найдено")
        if st.button("← Вернуться к заданиям"):
            st.switch_page("app/main.py")
        return
    
    st.title(f"✅ {task.title}")
    st.markdown(f"**{task.description}**")
    st.markdown(f"⭐ Награда: **{task.points} баллов**")
    
    # Если задание уже выполнено
    if task.completed:
        st.warning("Это задание уже выполнено!")
        if st.button("← Вернуться к заданиям"):
            st.switch_page("app/main.py")
        return
    
    # Фото требуется
    if task.photo_required:
        st.markdown("### 📸 Сделай фото результата")
        photo = st.camera_input("Нажми, чтобы сфотографировать")
        
        if photo:
            with st.spinner("Обрабатываем..."):
                # Здесь логика сохранения фото
                result = engine.complete_task(task.id, child_id, "photo_url")
                points = result['points'] if isinstance(result, dict) else result
                
                play_success_effect()
                st.success(f"✅ Молодец! +{points} баллов!")
                
                if isinstance(result, dict) and result.get('new_achievements'):
                    for ach in result['new_achievements']:
                        st.info(f"🏆 {ach['name']}! +{ach.get('reward_points', 0)} баллов")
                
                # Очищаем выбранное задание
                st.session_state.selected_task_id_for_completion = None
                
                if st.button("← Вернуться к заданиям"):
                    st.switch_page("app/main.py")
    
    # Фото не требуется
    else:
        st.markdown("### ✅ Подтверди выполнение")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Да, я выполнил задание", type="primary", use_container_width=True):
                with st.spinner("Обрабатываем..."):
                    result = engine.complete_task(task.id, child_id)
                    points = result['points'] if isinstance(result, dict) else result
                    
                    play_success_effect()
                    st.success(f"✅ Отлично! +{points} баллов!")
                    
                    if isinstance(result, dict) and result.get('new_achievements'):
                        for ach in result['new_achievements']:
                            st.info(f"🏆 {ach['name']}! +{ach.get('reward_points', 0)} баллов")
                    
                    st.session_state.selected_task_id_for_completion = None
                    
                    if st.button("← Вернуться к заданиям"):
                        st.switch_page("app/main.py")
        
        with col2:
            if st.button("❌ Отмена", use_container_width=True):
                st.session_state.selected_task_id_for_completion = None
                st.switch_page("app/main.py")

if __name__ == "__main__":
    main()