import time

import streamlit as st


def assistants_panel(nexus):
    st.header("Assistants Manager")

    # Fetching all assistants
    assistants = nexus.list_assistants()
    assistant_options = {a.name: a.id for a in assistants.data}
    assistant_options["Create New Assistant"] = "new"

    # Dropdown for selecting assistants
    selected_option = st.selectbox(
        "Select an Assistant", options=list(assistant_options.keys())
    )

    if selected_option == "Create New Assistant":
        name = st.text_input("Name for new Assistant")
        instructions = st.text_area("Instructions for new Assistant")

        # Dropdown for model selection
        models = ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o"]
        selected_model = st.selectbox("Select Model", models)

        # Checkboxes for tools
        code_interpreter = st.checkbox("Code Interpreter")

        # Compile tools list based on selections
        tools = []
        if code_interpreter:
            tools.append({"type": "code_interpreter"})

        if st.button("Create Assistant"):
            assistant = nexus.create_assistant(
                name, instructions, selected_model, tools
            )

            st.success(f"Assistant created with ID: {assistant.id}")
            return assistant
        return None
    else:
        assistant_id = assistant_options[selected_option]
        assistant = nexus.retrieve_assistant(assistant_id)

        new_name = st.text_input("New Name", value=assistant.name)
        new_instructions = st.text_area(
            "New Instructions", value=assistant.instructions, height=300
        )

        # Populate model dropdown from assistant
        models = [
            "gpt-3.5-turbo",
            "gpt-4-turbo",
        ]
        current_model = assistant.model if "model" in assistant else "gpt-4-turbo"
        selected_model = st.selectbox(
            "Select Model", models, index=models.index(current_model)
        )

        tools_list = [tool.type for tool in assistant.tools]
        code_interpreter = st.checkbox(
            "Code Interpreter", value="code_interpreter" in tools_list
        )

        # Compile updated tools list based on selections
        tools = []
        if code_interpreter:
            tools.append({"type": "code_interpreter"})

        if st.button("Update Assistant"):
            nexus.update_assistant(
                assistant_id, new_name, new_instructions, selected_model, tools
            )
            st.success("Assistant updated!")

        if st.button("Delete Assistant"):
            nexus.delete_assistant(assistant_id)
            st.success("Assistant deleted!")
            time.sleep(1)
            st.rerun()

        return assistant
