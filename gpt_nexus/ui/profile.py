import streamlit as st

from gpt_nexus.ui.cache import get_chat_system


def display_profile(profile):
    # Use columns to organize the layout
    col1, col2 = st.columns(2)

    with col1:
        profile.name = st.text_input("Name", value=profile.name)
        profile.avatar = st.text_input("Avatar", value=profile.avatar)
        profile.persona = st.text_area("Persona", value=profile.persona)

    with col2:
        # Safely handle actions, knowledge, memory which could be None
        actions = ", ".join(profile.actions) if profile.actions else ""
        profile.actions = [
            action.strip()
            for action in st.text_input("Actions (comma-separated)", actions).split(",")
            if action
        ]

        knowledge = ", ".join(profile.knowledge) if profile.knowledge else ""
        profile.knowledge = [
            item.strip()
            for item in st.text_input("Knowledge (comma-separated)", knowledge).split(
                ","
            )
            if item
        ]

        memory = ", ".join(profile.memory) if profile.memory else ""
        profile.memory = [
            item.strip()
            for item in st.text_input("Memory (comma-separated)", memory).split(",")
            if item
        ]

    # Placeholders for complex structures. Implement appropriate JSON/string editors if necessary.
    profile.evaluators = st.text_area("Evaluators (JSON structure)", "Not implemented")
    profile.reasoners = st.text_area("Reasoners (JSON structure)", "Not implemented")
    profile.planners = st.text_area("Planners (JSON structure)", "Not implemented")
    profile.feedback = st.text_area("Feedback (JSON structure)", "Not implemented")


def profile_page(username):
    chat = get_chat_system()
    user = chat.get_participant(username)
    if user is None:
        st.error("Invalid user")
        st.stop()

    profiles = chat.get_profile_names()

    if profile := st.selectbox("Select a profile", options=profiles):
        selected_profile = chat.get_profile(profile)
        display_profile(selected_profile)
