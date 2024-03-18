import streamlit as st
from nexus_base.chat_system import ChatSystem


@st.cache_resource
def get_chat_system():
    return ChatSystem()
