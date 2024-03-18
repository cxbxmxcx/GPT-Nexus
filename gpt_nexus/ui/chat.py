import time

import streamlit as st
from streamlit_js_eval import set_cookie

from gpt_nexus.ui.cache import get_chat_system
from gpt_nexus.ui.options import create_options_ui


def chat_page(username):
    st.set_page_config(layout="wide")

    chat = get_chat_system()
    user = chat.get_participant(username)
    if user is None:
        st.error("Invalid user")
        st.stop()

    # Initialize session state for threads and current_thread_id if not already present
    if "threads" not in st.session_state:
        threads = chat.get_threads_for_user(username)
        st.session_state["threads"] = threads
    if "current_thread_id" not in st.session_state:
        st.session_state["current_thread_id"] = None

    def select_thread(thread_id):
        st.session_state["current_thread_id"] = thread_id
        thread_history = chat.read_messages(thread_id)
        # Here, we find the thread by ID and set its 'agent' attribute
        for thread in st.session_state["threads"]:
            if thread.thread_id == thread_id:
                thread.agent = None
                break

    def create_new_thread():
        new_thread_id = (
            max(int(thread.thread_id) for thread in st.session_state["threads"]) + 1
            if st.session_state["threads"]
            else 1
        )
        thread = chat.create_thread(f"Chat: {new_thread_id + 1}", username)
        st.session_state["threads"].insert(0, thread)
        select_thread(new_thread_id)

    st.sidebar.title("GPT Nexus -> Chat")
    with st.sidebar.container(height=1000):
        st.button("+ New Chat", on_click=create_new_thread)
        # Sidebar UI for thread management

        st.header("Recent chats")
        for thread in st.session_state["threads"]:
            if st.button(thread.title, key=thread.thread_id):
                select_thread(thread.thread_id)

    if st.sidebar.button("Logout"):
        st.session_state["username"] = None
        set_cookie("username", "", 0)
        time.sleep(5)
        st.rerun()

    if st.sidebar.button("Agents"):
        st.session_state["current_page"] = "agents"
        st.rerun()

    # Main chat UI
    if st.session_state["current_thread_id"] is not None:
        current_thread = chat.get_thread(st.session_state["current_thread_id"])
        if current_thread:
            # chat_agent = current_thread.agent

            with st.container():
                col_chat, col_agent = st.columns([4, 2])

                with col_chat:
                    st.title(current_thread.title)
                    with st.container(height=500):
                        messages = chat.read_messages(current_thread.thread_id)
                        for message in messages:
                            with st.chat_message(
                                message.author.username, avatar=message.author.avatar
                            ):
                                st.markdown(message.content)

                        placeholder = st.empty()

                    user_input = st.chat_input(
                        "Type your message here:", key="msg_input"
                    )

                def format_agent_profile(agent_name):
                    profile = chat.get_profile(agent_name)
                    return f"{profile.avatar} : {profile.name}"

                with col_agent:
                    st.title("Agent Settings")
                    agents = chat.get_agent_names()
                    selected_agent = st.selectbox(
                        "Choose an agent engine:",
                        agents,
                        key="agents",
                        # label_visibility="collapsed",
                        help="Choose an agent to chat with.",
                    )
                    chat_agent = chat.get_agent(selected_agent)
                    with st.expander("Agent Options:", expanded=False):
                        options = chat_agent.get_attribute_options()
                        if options:
                            selected_options = create_options_ui(options)
                            for key, value in selected_options.items():
                                setattr(chat_agent, key, value)

                    profiles = chat.get_profile_names()
                    selected_profile = st.selectbox(
                        "Choose an agent profile:",
                        profiles,
                        key="profiles",
                        # label_visibility="collapsed",
                        help="Choose a profile for your agent.",
                        format_func=format_agent_profile,
                    )

                    if chat_agent.supports_actions:
                        action_names = chat.get_action_names()
                        selected_action_names = st.multiselect(
                            "Select actions:",
                            action_names,
                            key="actions",
                            # label_visibility="collapsed",
                            help="Choose the actions the agent can use.",
                        )
                        selected_actions = chat.get_actions(selected_action_names)
                        chat_agent.actions = selected_actions

                chat_agent.profile = chat.get_profile(selected_profile)
                chat_agent.chat_history = messages
                chat_avatar = chat_agent.profile.avatar

                if user_input:
                    with placeholder.container():
                        with st.chat_message(username, avatar=user.avatar):
                            st.markdown(user_input)
                            chat.post_message(
                                current_thread.thread_id, username, "user", user_input
                            )

                        with st.chat_message(chat_agent.name, avatar=chat_avatar):
                            with st.spinner(text="The agent is thinking..."):
                                st.write_stream(
                                    chat_agent.get_response_stream(
                                        user_input, current_thread.id
                                    )
                                )
                            chat.post_message(
                                current_thread.thread_id,
                                chat_agent.name,
                                "agent",
                                chat_agent.last_message,
                            )

                    st.rerun()
                    st.rerun()
