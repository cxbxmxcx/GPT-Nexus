import streamlit as st
from ui.agent import agent_page
from ui.chat import chat_page
from ui.knowledge import knowledge_page
from ui.login import login_page
from ui.memory import memory_page


def main():
    st.set_page_config(layout="wide")
    if username := st.session_state.get("username"):
        selected_page = st.sidebar.selectbox(
            "GPT Nexus", ["Chat", "Agents", "Knowledge", "Memory"]
        )
        if selected_page == "Agents":
            agent_page(username)
            return
        elif selected_page == "Chat":
            chat_page(username)
            return
        elif selected_page == "Knowledge":
            knowledge_page(username)
            return
        elif selected_page == "Memory":
            memory_page(username)
            return

    else:
        login_page()


if __name__ == "__main__":
    main()
