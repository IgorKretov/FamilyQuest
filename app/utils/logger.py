"""
Модуль логирования для FamilyQuest
"""
import logging
import os
from datetime import datetime
from pathlib import Path
import streamlit as st
from ui.components import safe_rerun

# Создаём папку для логов, если её нет
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Имя файла лога с датой
LOG_FILE = LOG_DIR / f"familyquest_{datetime.now().strftime('%Y%m%d')}.log"

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()  # Вывод в консоль
    ]
)

# Создаём логгер для приложения
logger = logging.getLogger("FamilyQuest")

def log_function_call(func_name, **kwargs):
    """Логирование вызова функции с параметрами"""
    params = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.debug(f"CALL {func_name}({params})")

def log_function_return(func_name, result):
    """Логирование возврата из функции"""
    logger.debug(f"RETURN {func_name} -> {result}")

def log_error(func_name, error):
    """Логирование ошибки"""
    logger.error(f"ERROR in {func_name}: {error}", exc_info=True)

def log_rerun(source, reason=""):
    """Специальное логирование для rerun"""
    logger.warning(f"RERUN from {source}: {reason}")
    
    # Сохраняем в st.session_state для отображения
    if 'rerun_log' not in st.session_state:
        st.session_state.rerun_log = []
    
    st.session_state.rerun_log.append({
        'time': datetime.now().strftime('%H:%M:%S.%f')[:-3],
        'source': source,
        'reason': reason
    })
    
    # Если слишком много rerun за короткое время
    recent = [r for r in st.session_state.rerun_log 
              if (datetime.now() - datetime.strptime(r['time'], '%H:%M:%S.%f')).seconds < 5]
    
    if len(recent) > 5:
        logger.critical(f"🔥 ПОТЕНЦИАЛЬНАЯ РЕКУРСИЯ! {len(recent)} rerun за 5 секунд")
        st.error(f"⚠️ Обнаружено {len(recent)} перезагрузок за 5 секунд!")

def display_rerun_log():
    """Отображение лога rerun в интерфейсе (для отладки)"""
    if st.session_state.get('rerun_log'):
        with st.expander("📋 Лог перезагрузок (отладка)"):
            for entry in st.session_state.rerun_log[-10:]:  # Последние 10
                st.text(f"[{entry['time']}] {entry['source']}: {entry['reason']}")
            
            if st.button("Очистить лог"):
                st.session_state.rerun_log = []
                safe_rerun()