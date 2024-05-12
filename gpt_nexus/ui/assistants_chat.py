import streamlit as st

from gpt_nexus.ui.assistants_panel import assistants_panel
from gpt_nexus.ui.cache import get_nexus


def assistants_page(username, win_height):
    nexus = get_nexus()
    user = nexus.get_participant(username)
    if user is None:
        st.error("Invalid user")
        st.stop()

    # Initialize session state for threads and current_thread_id if not already present
    if "asthreads" not in st.session_state:
        threads = nexus.get_threads_for_user(username, type="assistants")
        st.session_state["asthreads"] = threads
    if "ascurrent_thread_id" not in st.session_state:
        st.session_state["ascurrent_thread_id"] = None

    def select_thread(thread_id):
        st.session_state["ascurrent_thread_id"] = thread_id
        thread_history = nexus.read_messages(thread_id)
        # Here, we find the thread by ID and set its 'agent' attribute
        for thread in st.session_state["asthreads"]:
            if thread.thread_id == thread_id:
                thread.agent = None
                break

    def create_new_thread():
        new_thread_id = (
            len(st.session_state["asthreads"]) + 1
            if st.session_state["asthreads"]
            else 1
        )
        thread = nexus.create_thread(
            f"Thread: {new_thread_id}", username, type="assistants"
        )
        st.session_state["asthreads"].insert(0, thread)
        select_thread(thread.thread_id)

    st.sidebar.title("GPT Nexus -> Assistants")
    with st.sidebar.container(height=win_height - 300):
        st.button("+ New Thread", on_click=create_new_thread)
        # Sidebar UI for thread management

        st.header("Recent threads")
        for thread in st.session_state["asthreads"]:
            if st.button(thread.title, key=thread.thread_id):
                select_thread(thread.thread_id)

    # Main chat UI
    if st.session_state["ascurrent_thread_id"] is not None:
        current_thread = nexus.get_thread(st.session_state["ascurrent_thread_id"])
        if current_thread:
            # chat_agent = current_thread.agent

            with st.container():
                col_chat, col_agent = st.columns([4, 2])

                with col_chat:
                    st.title(current_thread.title)
                    with st.container(height=win_height - 300):
                        messages = nexus.read_messages(current_thread.thread_id)
                        for message in messages:
                            with st.chat_message(
                                message.author.username, avatar=message.author.avatar
                            ):
                                st.markdown(message.content)

                        placeholder = st.empty()

                    user_input = st.chat_input(
                        "Type your message here:", key="msg_input"
                    )

                with col_agent:
                    chat_agent = assistants_panel(nexus)
                chat_agent.chat_history = messages
                chat_avatar = chat_agent.profile.avatar

                if user_input:
                    with placeholder.container():
                        with st.chat_message(username, avatar=user.avatar):
                            st.markdown(user_input)
                            nexus.post_message(
                                current_thread.thread_id, username, "user", user_input
                            )

                        with st.chat_message(chat_agent.name, avatar=chat_avatar):
                            with st.spinner(text="The agent is thinking..."):
                                nexus.set_tracking_id(
                                    f"chat:thread{current_thread.thread_id}:{username}"
                                )
                                knowledge_rag = nexus.apply_knowledge_RAG(
                                    chat_agent.knowledge_store, user_input
                                )
                                memory_rag = nexus.apply_memory_RAG(
                                    chat_agent.memory_store, user_input, chat_agent
                                )
                                content = user_input + knowledge_rag + memory_rag
                                st.write_stream(
                                    chat_agent.get_response_stream(
                                        content, current_thread.id
                                    )
                                )
                            if chat_agent.memory_store != "None":
                                nexus.append_memory(
                                    chat_agent.memory_store,
                                    user_input,
                                    chat_agent.last_message,
                                    chat_agent,
                                )
                            nexus.set_tracking_id("Not set")
                            nexus.post_message(
                                current_thread.thread_id,
                                chat_agent.name,
                                "agent",
                                chat_agent.last_message,
                            )

                    st.rerun()
