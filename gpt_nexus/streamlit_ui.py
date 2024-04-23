import streamlit as st
from ui.actions import actions_page
from ui.agent import agent_page
from ui.chat import chat_page
from ui.knowledge import knowledge_page
from ui.login import login_page
from ui.memory import memory_page
from ui.profile import profile_page
from ui.prompts import prompts_page
from ui.usage import usage_page
from ui.workflow import workflow_page


def main():
    st.set_page_config(page_title="GPT Nexus", page_icon="icon.png", layout="wide")
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = ""

    if "last_log_message" not in st.session_state:
        st.session_state.last_log_message = None
    if username := st.session_state.get("username"):
        selected_page = st.sidebar.selectbox(
            "GPT Nexus",
            [
                "Chat Playground",
                "Actions",
                "Knowledge",
                "Memory",
                "Profile",
                "Prompts",
                "Usage",
                "Behaviors",
            ],
        )
        if selected_page == "Agents":
            agent_page(username)
            return
        elif selected_page == "Chat Playground":
            chat_page(username)
            return
        elif selected_page == "Knowledge":
            knowledge_page(username)
            return
        elif selected_page == "Memory":
            memory_page(username)
            return
        elif selected_page == "Workflow":
            workflow_page(username)
            return
        elif selected_page == "Profile":
            profile_page(username)
            return
        elif selected_page == "Prompts":
            prompts_page(username)
            return
        elif selected_page == "Usage":
            usage_page(username)
            return
        elif selected_page == "Actions":
            actions_page(username)
            return

    else:
        login_page()


if __name__ == "__main__":
    main()
