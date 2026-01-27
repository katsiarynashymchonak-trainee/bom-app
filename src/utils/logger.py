# src/ui/utils/logger.py

import streamlit as st

def log(message: str):
    if "logs" not in st.session_state:
        st.session_state.logs = []
    st.session_state.logs.append(message)
    st.write(message)
