"""
Вспомогательные функции
"""
import streamlit as st
from utils.logger import logger, log_rerun

def safe_rerun(source, reason=""):
    """Безопасный rerun с логированием"""
    log_rerun(source, reason)
    
    # Проверяем, не слишком ли часто вызываем rerun
    if 'last_rerun_time' in st.session_state:
        time_since_last = (datetime.now() - st.session_state.last_rerun_time).total_seconds()
        if time_since_last < 0.5:  # Меньше 500ms
            logger.warning(f"⚠️ Частый rerun! {time_since_last:.2f}s since last")
    
    st.session_state.last_rerun_time = datetime.now()
    
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except AttributeError:
            logger.error("❌ Нет метода rerun!")
            st.stop()