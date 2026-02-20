import streamlit as st
st.set_page_config(page_title="Тест AI-вкладки")

st.title("🧪 Тест AI-вкладки")

from app.ui.tabs.ai_tasks import render_ai_tasks

# Создаём тестовый движок
from app.core.game_engine import GameEngine
engine = GameEngine()
child_id = 1

# Вызываем функцию
render_ai_tasks(engine, child_id)
