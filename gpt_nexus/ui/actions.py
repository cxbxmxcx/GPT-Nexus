import streamlit as st

from gpt_nexus.ui.cache import get_chat_system


def actions_page(username):
    chat = get_chat_system()
    user = chat.get_participant(username)
    if user is None:
        st.error("Invalid user")
        st.stop()

    actions = chat.get_actions()

    action_names = [action["name"] for action in actions]
    selected_action_name = st.selectbox("Select an action", options=action_names)

    # Find the selected action in the data
    selected_action = next(
        (action for action in actions if action["name"] == selected_action_name), None
    )

    if selected_action:
        st.write(
            f"**Description:** {selected_action['agent_action']['function']['description']}"
        )

        # Parameters
        st.write("**Parameters:**")
        parameters = selected_action["agent_action"]["function"]["parameters"][
            "properties"
        ]
        for param_name, param_info in parameters.items():
            st.write(
                f"- {param_name}: {param_info['description']} (Type: {param_info['type']})"
            )

        # Required Parameters
        required_params = selected_action["agent_action"]["function"]["parameters"][
            "required"
        ]
        st.write("**Required Parameters:**")
        for param in required_params:
            st.write(f"- {param}")

        # Check if it's a semantic action
        if selected_action["prompt_template"]:
            st.write("**Action Type:** Semantic Action")
        else:
            st.write("**Action Type:** Native Action")

    st.write(actions)
