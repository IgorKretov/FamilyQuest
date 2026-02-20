"""
Вкладка для генерации заданий с помощью ИИ
"""
import streamlit as st
import json
from core.ai_generator import AITaskGenerator
from ui.effects import play_success_effect

def render_ai_tasks(engine, child_id):
    st.subheader("🤖 Умные задания от ИИ")
    
    child = engine.children.get(child_id)
    if not child:
        st.error("Выбери профиль")
        return
    
    # Инициализируем генератор
    if 'ai_generator' not in st.session_state:
        try:
            st.session_state.ai_generator = AITaskGenerator()
        except Exception as e:
            st.error(f"Ошибка подключения к GigaChat: {e}")
            st.info("💡 Проверь, что ключ API добавлен в secrets.toml")
            return
    
    generator = st.session_state.ai_generator
    
    # Вкладки для разных типов генерации [citation:9]
    tab1, tab2, tab3 = st.tabs(["✨ Одно задание", "🎯 Квест на день", "📖 Задание-история"])
    
    with tab1:
        render_single_task(generator, child, engine)
    
    with tab2:
        render_daily_quest(generator, child, engine)
    
    with tab3:
        render_story_task(generator, child, engine)

def render_single_task(generator, child, engine):
    """Генерация одного задания"""
    st.markdown("### 🎲 Случайное задание")
    st.markdown("Нажми кнопку, и ИИ придумает задание специально для тебя!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Выбор категории [citation:2]
        category_options = {
            "creative": "🎨 Творчество",
            "science": "🔬 Наука",
            "sport": "🏃 Спорт",
            "help": "🤝 Помощь",
            "learning": "📚 Учёба",
            "nature": "🌱 Природа"
        }
        selected_category = st.selectbox(
            "Категория",
            options=list(category_options.keys()),
            format_func=lambda x: category_options[x]
        )
    
    with col2:
        # Выбор сложности [citation:9]
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
    
    if st.button("✨ Сгенерировать задание"):
        with st.spinner("ИИ придумывает задание... 🤖"):
            task = generator.generate_task(
                child_name=child.name,
                age=child.age,
                interests=child.interests,
                category=selected_category,
                difficulty=difficulty
            )
            
            if task:
                st.session_state.generated_task = task
                st.session_state.show_ai_task = True
    
    # Отображение сгенерированного задания
    if st.session_state.get('show_ai_task', False):
        task = st.session_state.generated_task
        
        with st.container():
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2rem;
                border-radius: 20px;
                margin: 1rem 0;
            ">
                <h1 style="text-align: center;">{task.get('emoji', '🎯')}</h1>
                <h2 style="text-align: center;">{task.get('title', 'Задание')}</h2>
                <p style="text-align: center; font-size: 1.2rem;">{task.get('description', '')}</p>
                <p style="text-align: center; font-size: 1.5rem;">⭐ {task.get('points', 0)} баллов</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Показываем дополнительные детали [citation:9]
            if task.get('materials'):
                with st.expander("📦 Что понадобится"):
                    for material in task['materials']:
                        st.write(f"• {material}")
            
            if task.get('tips'):
                with st.expander("💡 Полезные советы"):
                    for tip in task['tips']:
                        st.write(f"• {tip}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Добавить в задания"):
                    # Сохраняем задание в БД
                    task_data = {
                        "title": task['title'],
                        "description": task['description'],
                        "category": task.get('category', 'creative'),
                        "points": task['points'],
                        "difficulty": task.get('difficulty', 'medium'),
                        "emoji": task.get('emoji', '🎯'),
                        "photo_required": task.get('photo_opportunity', True),
                        "child_id": child.id,
                        "due_date": None
                    }
                    engine.save_task_to_db(task_data)
                    play_success_effect()
                    st.success("✅ Задание добавлено!")
                    st.session_state.show_ai_task = False
                    st.experimental_rerun()
            
            with col2:
                if st.button("🔄 Ещё задание"):
                    st.session_state.show_ai_task = False
                    st.experimental_rerun()

def render_daily_quest(generator, child, engine):
    """Генерация квеста на день [citation:3]"""
    st.markdown("### 🎯 Квест на день")
    st.markdown("ИИ составит целый набор заданий, чтобы день был насыщенным!")
    
    count = st.slider("Сколько заданий?", min_value=2, max_value=5, value=3)
    
    if st.button("🚀 Создать квест"):
        with st.spinner("ИИ придумывает задания... 🤖"):
            tasks = generator.generate_daily_quest(
                child_name=child.name,
                age=child.age,
                interests=child.interests,
                count=count
            )
            
            if tasks:
                st.session_state.generated_quest = tasks
                st.session_state.show_quest = True
    
    # Отображение сгенерированного квеста
    if st.session_state.get('show_quest', False):
        tasks = st.session_state.generated_quest
        
        st.success(f"🎉 Квест готов! {len(tasks)} заданий ждут тебя!")
        
        for i, task in enumerate(tasks):
            with st.container():
                st.markdown(f"""
                <div style="
                    background: {'#f0f7ff' if i % 2 == 0 else '#f5f0ff'};
                    padding: 1rem;
                    border-radius: 10px;
                    margin: 0.5rem 0;
                ">
                    <h3>{task.get('emoji', '📌')} {task.get('title', f'Задание {i+1}')}</h3>
                    <p>{task.get('description', '')}</p>
                    <p>⭐ {task.get('points', 30)} баллов</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"✅ Добавить #{i+1}", key=f"add_quest_{i}"):
                    task_data = {
                        "title": task['title'],
                        "description": task['description'],
                        "category": task.get('category', 'creative'),
                        "points": task['points'],
                        "difficulty": task.get('difficulty', 'medium'),
                        "emoji": task.get('emoji', '🎯'),
                        "photo_required": True,
                        "child_id": child.id,
                        "due_date": None
                    }
                    engine.save_task_to_db(task_data)
                    st.success(f"✅ Задание '{task['title']}' добавлено!")
        
        if st.button("🔄 Новый квест"):
            st.session_state.show_quest = False
            st.experimental_rerun()

def render_story_task(generator, child, engine):
    """Генерация задания в формате истории [citation:8]"""
    st.markdown("### 📖 Задание-приключение")
    st.markdown("Представь, что ты герой сказки или космический путешественник!")
    
    if st.button("✨ Придумать историю"):
        with st.spinner("ИИ сочиняет историю... 📚"):
            task = generator.generate_story_task(
                child_name=child.name,
                age=child.age,
                interests=child.interests
            )
            
            if task:
                st.session_state.story_task = task
                st.session_state.show_story = True
    
    # Отображение истории
    if st.session_state.get('show_story', False):
        task = st.session_state.story_task
        
        with st.container():
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 100%);
                padding: 2rem;
                border-radius: 20px;
                margin: 1rem 0;
                color: #333;
            ">
                <h2 style="text-align: center;">📖 {task.get('title', 'Приключение')}</h2>
                <p style="font-style: italic; font-size: 1.2rem;">{task.get('story', '')}</p>
                <hr>
                <h3>🎯 Твоя миссия:</h3>
                <p style="font-size: 1.2rem;">{task.get('mission', '')}</p>
                <p style="font-size: 1.3rem; text-align: center;">🏆 {task.get('reward_description', 'Ты получишь награду!')}</p>
                <p style="text-align: center; font-size: 1.5rem;">⭐ {task.get('points', 45)} баллов</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Принять миссию"):
                    task_data = {
                        "title": task['title'],
                        "description": f"{task['story']} {task['mission']}",
                        "category": "creative",
                        "points": task.get('points', 45),
                        "difficulty": "medium",
                        "emoji": "📖",
                        "photo_required": True,
                        "child_id": child.id,
                        "due_date": None
                    }
                    engine.save_task_to_db(task_data)
                    play_success_effect()
                    st.success("✅ Миссия принята! Удачи, герой!")
                    st.session_state.show_story = False
                    st.experimental_rerun()
            
            with col2:
                if st.button("🔄 Другая история"):
                    st.session_state.show_story = False
                    st.experiment_rerun()
