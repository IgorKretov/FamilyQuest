"""
Вкладка создания новых заданий
"""
import streamlit as st
from datetime import datetime, timedelta

def render_create_task(engine, child_id):
    st.subheader("✨ Создать своё задание")
    
    with st.form("create_task_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Название задания", placeholder="Например: Помыть посуду")
            emoji = st.text_input("Эмодзи", value="🎯", placeholder="🎨 🔬 📚")
            
            category = st.selectbox(
                "Категория",
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
            
            difficulty = st.select_slider(
                "Сложность",
                options=["easy", "medium", "hard"],
                value="medium",
                format_func=lambda x: {
                    "easy": "🌟 Легко",
                    "medium": "⭐⭐ Средне",
                    "hard": "⭐⭐⭐ Сложно"
                }.get(x, x)
            )
        
        with col2:
            description = st.text_area("Описание", placeholder="Что нужно сделать?")
            
            points = st.number_input("Баллы", min_value=10, max_value=200, value=30, step=5)
            
            photo_required = st.checkbox("📸 Нужно фото для подтверждения", value=False)
            
            has_due_date = st.checkbox("📅 Установить срок выполнения")
            if has_due_date:
                due_date = st.date_input("Срок", value=datetime.now().date() + timedelta(days=1))
            else:
                due_date = None
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col2:
            submitted = st.form_submit_button("✅ Создать задание")
        
        if submitted:
            if title and description:
                task_data = {
                    "title": title,
                    "description": description,
                    "category": category,
                    "points": points,
                    "difficulty": difficulty,
                    "emoji": emoji,
                    "photo_required": photo_required,
                    "child_id": child_id,
                    "due_date": due_date.isoformat() if due_date else None
                }
                
                task = engine.save_task_to_db(task_data)
                st.success(f"✅ Задание '{title}' создано! +{points} баллов")
                st.balloons()
                st.info("👆 Теперь оно появится в списке заданий")
            else:
                st.error("Заполни название и описание!")

def render_task_library(engine, child_id):
    """Библиотека готовых заданий"""
    st.subheader("📚 Библиотека заданий")
    
    # Готовые шаблоны заданий
    templates = [
        {"title": "Убрать в комнате", "desc": "Пылесос, протереть пыль, сложить вещи", 
         "category": "help", "points": 50, "difficulty": "medium", "emoji": "🧹"},
        {"title": "Почитать книгу", "desc": "20 минут чтения", 
         "category": "learning", "points": 30, "difficulty": "easy", "emoji": "📚"},
        {"title": "Помочь с ужином", "desc": "Помочь приготовить или накрыть на стол", 
         "category": "help", "points": 40, "difficulty": "easy", "emoji": "🍳"},
        {"title": "Нарисовать рисунок", "desc": "Нарисовать что-то и подарить", 
         "category": "art", "points": 45, "difficulty": "medium", "emoji": "🎨"},
        {"title": "Зарядка", "desc": "15 минут активных упражнений", 
         "category": "sport", "points": 35, "difficulty": "easy", "emoji": "🏃"},
    ]
    
    cols = st.columns(2)
    for idx, template in enumerate(templates):
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
                    <h2 style="text-align: center;">{template['emoji']}</h2>
                    <h4 style="text-align: center;">{template['title']}</h4>
                    <p style="text-align: center;">{template['desc']}</p>
                    <p style="text-align: center; color: #4A90E2;">+{template['points']} ⭐</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"➕ Добавить", key=f"add_template_{idx}"):
                    task_data = {
                        "title": template['title'],
                        "description": template['desc'],
                        "category": template['category'],
                        "points": template['points'],
                        "difficulty": template['difficulty'],
                        "emoji": template['emoji'],
                        "photo_required": False,
                        "child_id": child_id,
                        "due_date": None
                    }
                    engine.save_task_to_db(task_data)
                    st.success(f"✅ Задание добавлено!")
                    st.experimental_rerun()
