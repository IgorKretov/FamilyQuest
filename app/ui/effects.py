"""
Визуальные и звуковые эффекты
"""
import streamlit as st
import time
import random

def play_success_effect():
    """Эффект при успешном выполнении"""
    col1, col2, col3 = st.columns(3)
    with col2:
        st.balloons()
        st.markdown("""
        <div style="
            animation: bounce 0.5s;
            text-align: center;
            font-size: 3rem;
        ">
            🎉✨🌟
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.5)

def play_level_up_effect(level):
    """Эффект при повышении уровня"""
    st.snow()
    st.markdown(f"""
    <div style="
        animation: pulse 1s;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 1rem 0;
    ">
        <h1>🎊 УРОВЕНЬ {level} 🎊</h1>
        <p style="font-size: 2rem;">⭐"Ты становишься сильнее!"⭐</p>
    </div>
    """, unsafe_allow_html=True)

def play_achievement_effect(achievement_name):
    """Эффект при получении достижения"""
    st.balloons()
    st.snow()
    st.markdown(f"""
    <div style="
        animation: shake 0.5s;
        text-align: center;
        background: gold;
        color: black;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 3px solid orange;
    ">
        <h2>🏆 НОВОЕ ДОСТИЖЕНИЕ! 🏆</h2>
        <p style="font-size: 1.5rem;">{achievement_name}</p>
    </div>
    """, unsafe_allow_html=True)

def show_motivation_message():
    """Случайное мотивирующее сообщение"""
    messages = [
        "🔥 Так держать!",
        "⭐ Ты супер!",
        "💪 Ещё немного!",
        "🎯 Цель близко!",
        "🌟 Ты молодец!",
        "⚡ Не останавливайся!"
    ]
    
    st.info(random.choice(messages))

def add_custom_css():
    """Добавление CSS-анимаций"""
    st.markdown("""
    <style>
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-10px); }
            75% { transform: translateX(10px); }
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .sparkle {
            animation: spin 2s linear infinite;
        }
        
        .glow {
            animation: pulse 2s infinite;
        }
    </style>
    """, unsafe_allow_html=True)
