"""
Вкладка для подключения ребёнка к родителям
"""
import streamlit as st
from core.auth_system import AuthSystem
from data.database import get_connection

def render_child_connection(engine, child_id):
    st.subheader("🔗 Подключиться к родителям")
    
    auth = AuthSystem(get_connection())
    
    # Проверяем, есть ли уже родители
    parents = auth.get_parents_for_child(child_id)
    
    if parents:
        st.success("✅ Вы уже связаны с родителями:")
        for p in parents:
            st.write(f"• {p['name']}")
        
        if st.button("➕ Подключить ещё одного родителя"):
            st.session_state.show_invite_form = True
    
    if st.session_state.get('show_invite_form', False) or not parents:
        with st.form("connect_parent"):
            invite_code = st.text_input("Введите код приглашения от родителей", 
                                       placeholder="FAM-XXXXXX",
                                       help="Код можно получить у родителей")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Подключиться", use_container_width=True):
                    if auth.accept_invitation(invite_code, child_id):
                        st.success("🎉 Родитель подключён!")
                        st.session_state.show_invite_form = False
                        st.rerun()
                    else:
                        st.error("❌ Неверный или просроченный код")
            with col2:
                if st.form_submit_button("❌ Отмена", use_container_width=True):
                    st.session_state.show_invite_form = False
                    st.rerun()