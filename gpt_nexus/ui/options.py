import streamlit as st


def create_options_ui(custom_options):
    user_inputs = {}
    for attr_name, attr_details in custom_options.items():
        attr_type = attr_details["type"]
        default = attr_details.get("default")  # Get the default value if it exists
        if attr_type == "string":
            # Use selectbox for string options with a default option
            option = st.selectbox(
                f"Select {attr_name}",
                attr_details["options"],
                index=attr_details["options"].index(default)
                if default in attr_details["options"]
                else 0,
            )
        elif attr_type == "numeric":
            # Use slider for numeric options with a default value and specific step
            step = attr_details.get("step", 1)  # Use provided step value
            option = st.slider(
                f"Set {attr_name}",
                min_value=attr_details["min"],
                max_value=attr_details["max"],
                value=default,  # Set the default value here
                step=step,
            )
        elif attr_type == "bool":
            # Use checkbox for boolean options with a default enabled/disabled state
            option = st.checkbox(
                f"Enable {attr_name}", value=default
            )  # Use default value as the initial state

        user_inputs[attr_name] = option
    return user_inputs
