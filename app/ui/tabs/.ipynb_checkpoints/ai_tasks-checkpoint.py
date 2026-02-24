"""
Вкладка для генерации заданий с помощью ИИ
"""
import streamlit as st
import json
from core.ai_generator import AITaskGenerator
from ui.effects import play_success_effect
from datetime import datetime
from utils.logger import logger, log_function_call

def render_ai_tasks(engine, child_id):
    """Основная функция вкладки AI-заданий"""
    st.subheader("🤖 Умные задания от ИИ")
    
    child = engine.children.get(child_id)
    if not child:
        st.error("Выбери профиль")
        return
    
    # Инициализируем генератор (только один раз)
    if 'ai_generator' not in st.session_state:
        with st.spinner("🔄 Подключаюсь к GigaChat..."):
            try:
                st.session_state.ai_generator = AITaskGenerator()
                st.success("✅ GigaChat подключён!")
            except Exception as e:
                st.error(f"❌ Ошибка подключения к GigaChat: {e}")
                st.info("💡 Проверь, что ключ API добавлен в .env файл")
                return
    
    generator = st.session_state.ai_generator
    
    # Вкладки для разных типов генерации
    tab1, tab2, tab3 = st.tabs(["✨ Одно задание", "🎯 Квест на день", "📖 Задание-история"])
    
    with tab1:
        render_single_task(generator, child, engine)
    
    with tab2:
        render_daily_quest(generator, child, engine)
    
    with tab3:
        render_story_task(generator, child, engine)

def render_single_task(generator, child, engine):
    """Генерация одного задания (СТАБИЛЬНАЯ ВЕРСИЯ)"""
    log_function_call("render_single_task", child=child.name)
    
    # Инициализируем состояние, если нужно
    if 'ai_mode' not in st.session_state:
        st.session_state.ai_mode = 'input'  # 'input' или 'display'
    
    if st.session_state.ai_mode == 'input':
        # Режим ввода параметров
        render_input_mode(generator, child, engine)
    else:
        # Режим отображения задания
        render_display_mode(generator, child, engine)

def render_input_mode(generator, child, engine):
    """Режим ввода параметров (БЕЗ РЕКУРСИИ)"""
    st.markdown("### 🎲 Случайное задание")
    st.caption(f"Для {child.name}, {child.age} лет. Интересы: {', '.join(child.interests)}")
    
    col1, col2 = st.columns(2)
    
    with col1:
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
            format_func=lambda x: category_options[x],
            key="ai_category_input"
        )
    
    with col2:
        difficulty = st.select_slider(
            "Сложность",
            options=["easy", "medium", "hard"],
            value="medium",
            format_func=lambda x: {
                "easy": "🌟 Легко",
                "medium": "⭐⭐ Средне",
                "hard": "⭐⭐⭐ Сложно"
            }.get(x, x),
            key="ai_difficulty_input"
        )
    
    # Кнопка генерации - ТОЛЬКО ОНА МЕНЯЕТ СОСТОЯНИЕ
    if st.button("✨ Сгенерировать задание", key="generate_input", type="primary", use_container_width=True):
        logger.info(f"🎲 Генерация задания для {child.name}")
        with st.spinner("🤖 ИИ придумывает задание..."):
            task = generator.generate_task(
                child_name=child.name,
                age=child.age,
                interests=child.interests,
                category=selected_category,
                difficulty=difficulty
            )
            
            if task:
                logger.info(f"✅ Задание сгенерировано: {task.get('title')}")
                st.session_state.generated_task = task
                st.session_state.ai_mode = 'display'
                st.rerun()

def render_display_mode(generator, child, engine):
    """Режим отображения задания (БЕЗ РЕКУРСИИ)"""
    task = st.session_state.generated_task
    
    # Карточка задания
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    ">
        <h1 style="text-align: center; font-size: 3rem;">{task.get('emoji', '🎯')}</h1>
        <h2 style="text-align: center; margin-top: 0;">{task.get('title', 'Задание')}</h2>
        <p style="text-align: center; font-size: 1.2rem;">{task.get('description', '')}</p>
        <p style="text-align: center; font-size: 2rem; font-weight: bold;">⭐ {task.get('points', 0)} баллов</p>
        <p style="text-align: center; opacity: 0.8;">⏱️ {task.get('estimated_time', 30)} минут</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Дополнительная информация
    col1, col2 = st.columns(2)
    
    with col1:
        if task.get('materials'):
            with st.expander("📦 Что понадобится", expanded=True):
                for material in task['materials']:
                    st.write(f"• {material}")
    
    with col2:
        if task.get('tips'):
            with st.expander("💡 Полезные советы", expanded=True):
                for tip in task['tips']:
                    st.write(f"• {tip}")
    
    # Кнопки действий
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        if st.button("✅ Добавить в задания", key="add_display", use_container_width=True):
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
            st.success("✅ Задание добавлено в список!")
            st.session_state.ai_mode = 'input'
            if 'generated_task' in st.session_state:
                del st.session_state.generated_task
            st.rerun()
    
    with col_b:
        if st.button("🔄 Ещё такое же", key="another_display", use_container_width=True):
            # Используем сохранённые параметры
            with st.spinner("🤖 ИИ придумывает ещё..."):
                new_task = generator.generate_task(
                    child_name=child.name,
                    age=child.age,
                    interests=child.interests,
                    category=st.session_state.get('ai_category_input', 'creative'),
                    difficulty=st.session_state.get('ai_difficulty_input', 'medium')
                )
                if new_task:
                    st.session_state.generated_task = new_task
                    st.rerun()
    
    with col_c:
        if st.button("❌ Закрыть", key="close_display", use_container_width=True):
            st.session_state.ai_mode = 'input'
            if 'generated_task' in st.session_state:
                del st.session_state.generated_task
            st.rerun()

def render_daily_quest(generator, child, engine):
    """Генерация квеста на день"""
    st.markdown("### 🎯 Квест на день")
    st.caption(f"Для {child.name}, {child.age} лет. Набор заданий на целый день!")
    
    # Инициализируем состояние квеста
    if 'quest_mode' not in st.session_state:
        st.session_state.quest_mode = 'input'
    
    if st.session_state.quest_mode == 'input':
        count = st.slider("Сколько заданий в квесте?", min_value=2, max_value=5, value=3, key="quest_count_input")
        
        if st.button("🚀 Создать квест", key="create_quest_input", type="primary", use_container_width=True):
            with st.spinner("🤖 ИИ придумывает задания..."):
                tasks = generator.generate_daily_quest(
                    child_name=child.name,
                    age=child.age,
                    interests=child.interests,
                    count=count
                )
                
                if tasks:
                    st.session_state.generated_quest = tasks
                    st.session_state.quest_mode = 'display'
                    st.rerun()
    else:
        tasks = st.session_state.generated_quest
        st.success(f"🎉 Квест готов! {len(tasks)} заданий ждут тебя!")
        
        for i, task in enumerate(tasks):
            with st.container():
                st.markdown(f"""
                <div style="
                    background: {'#f0f7ff' if i % 2 == 0 else '#f5f0ff'};
                    padding: 1.2rem;
                    border-radius: 15px;
                    margin: 0.8rem 0;
                    border-left: 5px solid #667eea;
                ">
                    <h3>{task.get('emoji', '📌')} {task.get('title', f'Задание {i+1}')}</h3>
                    <p>{task.get('description', '')}</p>
                    <p><strong>⭐ {task.get('points', 30)} баллов</strong> • ⏱️ {task.get('estimated_time', 30)} мин</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"✅ Добавить задание {i+1}", key=f"add_quest_{i}"):
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
                    st.rerun()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Новый квест", key="new_quest_display", use_container_width=True):
                st.session_state.quest_mode = 'input'
                if 'generated_quest' in st.session_state:
                    del st.session_state.generated_quest
                st.rerun()
        with col2:
            if st.button("➕ Добавить все задания", key="add_all_quest_display", use_container_width=True):
                for task in tasks:
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
                play_success_effect()
                st.success(f"✅ Все {len(tasks)} заданий добавлены!")
                st.session_state.quest_mode = 'input'
                if 'generated_quest' in st.session_state:
                    del st.session_state.generated_quest
                st.rerun()

def render_story_task(generator, child, engine):
    """Генерация задания в формате истории"""
    st.markdown("### 📖 Задание-приключение")
    st.caption("Представь, что ты герой сказки или космический путешественник!")
    
    # Инициализируем состояние истории
    if 'story_mode' not in st.session_state:
        st.session_state.story_mode = 'input'
    
    if st.session_state.story_mode == 'input':
        if st.button("✨ Придумать историю", key="create_story_input", type="primary", use_container_width=True):
            with st.spinner("🤖 ИИ сочиняет историю..."):
                task = generator.generate_story_task(
                    child_name=child.name,
                    age=child.age,
                    interests=child.interests
                )
                
                if task:
                    st.session_state.story_task = task
                    st.session_state.story_mode = 'display'
                    st.rerun()
    else:
        task = st.session_state.story_task
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 100%);
            padding: 2rem;
            border-radius: 20px;
            margin: 1.5rem 0;
            color: #333;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        ">
            <h2 style="text-align: center;">📖 {task.get('title', 'Приключение')}</h2>
            <p style="font-style: italic; font-size: 1.2rem;">{task.get('story', '')}</p>
            <hr>
            <h3>🎯 Твоя миссия:</h3>
            <p style="font-size: 1.1rem;">{task.get('mission', '')}</p>
            <p style="font-size: 1.2rem; text-align: center;">🏆 {task.get('reward_description', 'Ты получишь награду!')}</p>
            <p style="text-align: center; font-size: 2rem; font-weight: bold;">⭐ {task.get('points', 45)} баллов</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Принять миссию", key="accept_story_display", use_container_width=True):
                task_data = {
                    "title": task['title'],
                    "description": f"{task.get('story', '')} {task.get('mission', '')}",
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
                st.session_state.story_mode = 'input'
                if 'story_task' in st.session_state:
                    del st.session_state.story_task
                st.rerun()
        
        with col2:
            if st.button("🔄 Другая история", key="another_story_display", use_container_width=True):
                with st.spinner("🤖 ИИ сочиняет новую историю..."):
                    new_task = generator.generate_story_task(
                        child_name=child.name,
                        age=child.age,
                        interests=child.interests
                    )
                    if new_task:
                        st.session_state.story_task = new_task
                        st.rerun()
# """
# Вкладка для генерации заданий с помощью ИИ
# """
# import streamlit as st
# import json
# from core.ai_generator import AITaskGenerator
# from ui.effects import play_success_effect
# from datetime import datetime
# from utils.logger import logger, log_function_call

# def render_ai_tasks(engine, child_id):
#     """Основная функция вкладки AI-заданий"""
#     st.subheader("🤖 Умные задания от ИИ")
    
#     child = engine.children.get(child_id)
#     if not child:
#         st.error("Выбери профиль")
#         return
    
#     # Инициализируем генератор (только один раз)
#     if 'ai_generator' not in st.session_state:
#         with st.spinner("🔄 Подключаюсь к GigaChat..."):
#             try:
#                 st.session_state.ai_generator = AITaskGenerator()
#                 st.success("✅ GigaChat подключён!")
#             except Exception as e:
#                 st.error(f"❌ Ошибка подключения к GigaChat: {e}")
#                 st.info("💡 Проверь, что ключ API добавлен в .env файл")
#                 return
    
#     generator = st.session_state.ai_generator
    
#     # Вкладки для разных типов генерации
#     tab1, tab2, tab3 = st.tabs(["✨ Одно задание", "🎯 Квест на день", "📖 Задание-история"])
    
#     with tab1:
#         render_single_task(generator, child, engine)
    
#     with tab2:
#         render_daily_quest(generator, child, engine)
    
#     with tab3:
#         render_story_task(generator, child, engine)

# def render_single_task(generator, child, engine):
#     """Генерация одного задания (ИСПРАВЛЕННАЯ ВЕРСИЯ)"""
#     log_function_call("render_single_task", child=child.name)
    
#     # Проверяем, показываем ли мы сгенерированное задание
#     showing_task = st.session_state.get('show_ai_task', False) and 'generated_task' in st.session_state
    
#     if not showing_task:
#         # Режим ввода параметров (виджеты ТОЛЬКО здесь)
#         st.markdown("### 🎲 Случайное задание")
#         st.caption(f"Для {child.name}, {child.age} лет. Интересы: {', '.join(child.interests)}")
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             category_options = {
#                 "creative": "🎨 Творчество",
#                 "science": "🔬 Наука",
#                 "sport": "🏃 Спорт",
#                 "help": "🤝 Помощь",
#                 "learning": "📚 Учёба",
#                 "nature": "🌱 Природа"
#             }
#             selected_category = st.selectbox(
#                 "Категория",
#                 options=list(category_options.keys()),
#                 format_func=lambda x: category_options[x],
#                 key="ai_category_main"
#             )
        
#         with col2:
#             difficulty = st.select_slider(
#                 "Сложность",
#                 options=["easy", "medium", "hard"],
#                 value="medium",
#                 format_func=lambda x: {
#                     "easy": "🌟 Легко",
#                     "medium": "⭐⭐ Средне",
#                     "hard": "⭐⭐⭐ Сложно"
#                 }.get(x, x),
#                 key="ai_difficulty_main"
#             )
        
#         # Кнопка генерации
#         if st.button("✨ Сгенерировать задание", key="generate_main", type="primary", use_container_width=True):
#             logger.info(f"🎲 Генерация задания для {child.name}")
#             with st.spinner("🤖 ИИ придумывает задание..."):
#                 task = generator.generate_task(
#                     child_name=child.name,
#                     age=child.age,
#                     interests=child.interests,
#                     category=selected_category,
#                     difficulty=difficulty
#                 )
                
#                 if task:
#                     logger.info(f"✅ Задание сгенерировано: {task.get('title')}")
#                     st.session_state.generated_task = task
#                     st.session_state.show_ai_task = True
#                     st.rerun()
    
#     else:
#         # Режим отображения задания (НЕТ виджетов ввода!)
#         task = st.session_state.generated_task
        
#         # Карточка задания
#         st.markdown(f"""
#         <div style="
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             color: white;
#             padding: 2rem;
#             border-radius: 20px;
#             margin: 1.5rem 0;
#             box-shadow: 0 10px 20px rgba(0,0,0,0.2);
#         ">
#             <h1 style="text-align: center; font-size: 3rem;">{task.get('emoji', '🎯')}</h1>
#             <h2 style="text-align: center; margin-top: 0;">{task.get('title', 'Задание')}</h2>
#             <p style="text-align: center; font-size: 1.2rem;">{task.get('description', '')}</p>
#             <p style="text-align: center; font-size: 2rem; font-weight: bold;">⭐ {task.get('points', 0)} баллов</p>
#             <p style="text-align: center; opacity: 0.8;">⏱️ {task.get('estimated_time', 30)} минут</p>
#         </div>
#         """, unsafe_allow_html=True)
        
#         # Дополнительная информация
#         col1, col2 = st.columns(2)
        
#         with col1:
#             if task.get('materials'):
#                 with st.expander("📦 Что понадобится", expanded=True):
#                     for material in task['materials']:
#                         st.write(f"• {material}")
        
#         with col2:
#             if task.get('tips'):
#                 with st.expander("💡 Полезные советы", expanded=True):
#                     for tip in task['tips']:
#                         st.write(f"• {tip}")
        
#         # Кнопки действий
#         col_a, col_b, col_c = st.columns(3)
        
#         with col_a:
#             if st.button("✅ Добавить в задания", key="add_task_main", use_container_width=True):
#                 task_data = {
#                     "title": task['title'],
#                     "description": task['description'],
#                     "category": task.get('category', 'creative'),
#                     "points": task['points'],
#                     "difficulty": task.get('difficulty', 'medium'),
#                     "emoji": task.get('emoji', '🎯'),
#                     "photo_required": task.get('photo_opportunity', True),
#                     "child_id": child.id,
#                     "due_date": None
#                 }
#                 engine.save_task_to_db(task_data)
#                 play_success_effect()
#                 st.success("✅ Задание добавлено в список!")
#                 # Очищаем состояние и возвращаемся к вводу
#                 st.session_state.show_ai_task = False
#                 if 'generated_task' in st.session_state:
#                     del st.session_state.generated_task
#                 st.rerun()
        
#         with col_b:
#             if st.button("🔄 Ещё такое же", key="another_same_main", use_container_width=True):
#                 # Нужно запомнить параметры для новой генерации
#                 with st.spinner("🤖 ИИ придумывает ещё..."):
#                     new_task = generator.generate_task(
#                         child_name=child.name,
#                         age=child.age,
#                         interests=child.interests,
#                         category=st.session_state.get('ai_category_main', 'creative'),
#                         difficulty=st.session_state.get('ai_difficulty_main', 'medium')
#                     )
#                     if new_task:
#                         st.session_state.generated_task = new_task
#                         st.rerun()
        
#         with col_c:
#             if st.button("❌ Закрыть", key="close_task_main", use_container_width=True):
#                 st.session_state.show_ai_task = False
#                 if 'generated_task' in st.session_state:
#                     del st.session_state.generated_task
#                 st.rerun()

# def render_daily_quest(generator, child, engine):
#     """Генерация квеста на день"""
#     st.markdown("### 🎯 Квест на день")
#     st.caption(f"Для {child.name}, {child.age} лет. Набор заданий на целый день!")
    
#     # Проверяем, показываем ли мы сгенерированный квест
#     showing_quest = st.session_state.get('show_quest', False) and 'generated_quest' in st.session_state
    
#     if not showing_quest:
#         count = st.slider("Сколько заданий в квесте?", min_value=2, max_value=5, value=3, key="quest_count")
        
#         if st.button("🚀 Создать квест", key="create_quest", type="primary", use_container_width=True):
#             with st.spinner("🤖 ИИ придумывает задания..."):
#                 tasks = generator.generate_daily_quest(
#                     child_name=child.name,
#                     age=child.age,
#                     interests=child.interests,
#                     count=count
#                 )
                
#                 if tasks:
#                     st.session_state.generated_quest = tasks
#                     st.session_state.show_quest = True
#                     st.rerun()
    
#     else:
#         tasks = st.session_state.generated_quest
#         st.success(f"🎉 Квест готов! {len(tasks)} заданий ждут тебя!")
        
#         for i, task in enumerate(tasks):
#             with st.container():
#                 st.markdown(f"""
#                 <div style="
#                     background: {'#f0f7ff' if i % 2 == 0 else '#f5f0ff'};
#                     padding: 1.2rem;
#                     border-radius: 15px;
#                     margin: 0.8rem 0;
#                     border-left: 5px solid #667eea;
#                 ">
#                     <h3>{task.get('emoji', '📌')} {task.get('title', f'Задание {i+1}')}</h3>
#                     <p>{task.get('description', '')}</p>
#                     <p><strong>⭐ {task.get('points', 30)} баллов</strong> • ⏱️ {task.get('estimated_time', 30)} мин</p>
#                 </div>
#                 """, unsafe_allow_html=True)
                
#                 if st.button(f"✅ Добавить задание {i+1}", key=f"add_quest_{i}"):
#                     task_data = {
#                         "title": task['title'],
#                         "description": task['description'],
#                         "category": task.get('category', 'creative'),
#                         "points": task['points'],
#                         "difficulty": task.get('difficulty', 'medium'),
#                         "emoji": task.get('emoji', '🎯'),
#                         "photo_required": True,
#                         "child_id": child.id,
#                         "due_date": None
#                     }
#                     engine.save_task_to_db(task_data)
#                     st.success(f"✅ Задание '{task['title']}' добавлено!")
#                     st.rerun()
        
#         col1, col2 = st.columns(2)
#         with col1:
#             if st.button("🔄 Новый квест", key="new_quest", use_container_width=True):
#                 st.session_state.show_quest = False
#                 if 'generated_quest' in st.session_state:
#                     del st.session_state.generated_quest
#                 st.rerun()
#         with col2:
#             if st.button("➕ Добавить все задания", key="add_all_quest", use_container_width=True):
#                 for task in tasks:
#                     task_data = {
#                         "title": task['title'],
#                         "description": task['description'],
#                         "category": task.get('category', 'creative'),
#                         "points": task['points'],
#                         "difficulty": task.get('difficulty', 'medium'),
#                         "emoji": task.get('emoji', '🎯'),
#                         "photo_required": True,
#                         "child_id": child.id,
#                         "due_date": None
#                     }
#                     engine.save_task_to_db(task_data)
#                 play_success_effect()
#                 st.success(f"✅ Все {len(tasks)} заданий добавлены!")
#                 st.session_state.show_quest = False
#                 if 'generated_quest' in st.session_state:
#                     del st.session_state.generated_quest
#                 st.rerun()

# def render_story_task(generator, child, engine):
#     """Генерация задания в формате истории"""
#     st.markdown("### 📖 Задание-приключение")
#     st.caption("Представь, что ты герой сказки или космический путешественник!")
    
#     # Проверяем, показываем ли мы сгенерированную историю
#     showing_story = st.session_state.get('show_story', False) and 'story_task' in st.session_state
    
#     if not showing_story:
#         if st.button("✨ Придумать историю", key="create_story", type="primary", use_container_width=True):
#             with st.spinner("🤖 ИИ сочиняет историю..."):
#                 task = generator.generate_story_task(
#                     child_name=child.name,
#                     age=child.age,
#                     interests=child.interests
#                 )
                
#                 if task:
#                     st.session_state.story_task = task
#                     st.session_state.show_story = True
#                     st.rerun()
    
#     else:
#         task = st.session_state.story_task
        
#         st.markdown(f"""
#         <div style="
#             background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 100%);
#             padding: 2rem;
#             border-radius: 20px;
#             margin: 1.5rem 0;
#             color: #333;
#             box-shadow: 0 10px 20px rgba(0,0,0,0.1);
#         ">
#             <h2 style="text-align: center;">📖 {task.get('title', 'Приключение')}</h2>
#             <p style="font-style: italic; font-size: 1.2rem;">{task.get('story', '')}</p>
#             <hr>
#             <h3>🎯 Твоя миссия:</h3>
#             <p style="font-size: 1.1rem;">{task.get('mission', '')}</p>
#             <p style="font-size: 1.2rem; text-align: center;">🏆 {task.get('reward_description', 'Ты получишь награду!')}</p>
#             <p style="text-align: center; font-size: 2rem; font-weight: bold;">⭐ {task.get('points', 45)} баллов</p>
#         </div>
#         """, unsafe_allow_html=True)
        
#         col1, col2 = st.columns(2)
#         with col1:
#             if st.button("✅ Принять миссию", key="accept_story", use_container_width=True):
#                 task_data = {
#                     "title": task['title'],
#                     "description": f"{task.get('story', '')} {task.get('mission', '')}",
#                     "category": "creative",
#                     "points": task.get('points', 45),
#                     "difficulty": "medium",
#                     "emoji": "📖",
#                     "photo_required": True,
#                     "child_id": child.id,
#                     "due_date": None
#                 }
#                 engine.save_task_to_db(task_data)
#                 play_success_effect()
#                 st.success("✅ Миссия принята! Удачи, герой!")
#                 st.session_state.show_story = False
#                 if 'story_task' in st.session_state:
#                     del st.session_state.story_task
#                 st.rerun()
        
#         with col2:
#             if st.button("🔄 Другая история", key="another_story", use_container_width=True):
#                 with st.spinner("🤖 ИИ сочиняет новую историю..."):
#                     new_task = generator.generate_story_task(
#                         child_name=child.name,
#                         age=child.age,
#                         interests=child.interests
#                     )
#                     if new_task:
#                         st.session_state.story_task = new_task
#                         st.rerun()