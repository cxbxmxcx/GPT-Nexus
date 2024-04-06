import json
import os

import streamlit as st
from code_editor import code_editor
from pybars import Compiler

from gpt_nexus.ui.agent_panel import agent_panel
from gpt_nexus.ui.cache import get_chat_system


def prompts_page(username):
    chat = get_chat_system()
    user = chat.get_participant(username)
    if user is None:
        st.error("Invalid user")
        st.stop()

    # UI for the app
    st.title("Prompt Template Manager")
    prompt_names = chat.get_prompt_template_names()
    template_names = ["Create New Template"] + sorted(prompt_names)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    editor_commands_path = os.path.join(current_dir, "editor_commands.json")

    with open(editor_commands_path) as json_info_file:
        btns = json.load(json_info_file)
    height = [12, 15]
    language = "handlebars"
    theme = "default"
    shortcuts = "vscode"
    focus = True
    wrap = True

    with st.sidebar.container(height=600):
        chat_agent = agent_panel(chat)

    left_column, right_column = st.columns([4, 4])

    with left_column:
        selected_template_name = st.selectbox("Select a template", template_names)
        if selected_template_name == "Create New Template":
            new_name = st.text_input("Template Name").strip()
            new_inputs = st.text_input("Inputs (comma-separated)")
            response_dict = code_editor(
                "",
                height=height,
                lang=language,
                theme=theme,
                shortcuts=shortcuts,
                focus=focus,
                buttons=btns,
            )
            new_content = response_dict["text"]

            if new_name and new_content:
                if st.button("Add Prompt Template") or response_dict["type"] == "saved":
                    try:
                        # Save the new template
                        chat.add_prompt_template(
                            new_name,
                            new_content,
                            [input.strip() for input in new_inputs.split(",")],
                        )
                        st.success(f"Prompt Template '{new_name}' added!")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                        st.stop()

        elif selected_template_name:
            # Load and display the selected template for editing
            selected_template = chat.get_prompt_template(selected_template_name)
            edited_name = st.text_input("Template Name", value=selected_template_name)
            edited_inputs = st.text_input(
                "Inputs (comma-separated)",
                value=", ".join(selected_template.inputs.split(",")),
            )
            response_dict = code_editor(
                selected_template.content,
                height=height,
                lang=language,
                theme=theme,
                shortcuts=shortcuts,
                focus=focus,
                buttons=btns,
            )
            edited_content = response_dict["text"]

            col1, col2 = st.columns([1, 1])
            with col1:
                if (
                    edited_content
                    and st.button("Update Template")
                    or response_dict["type"] == "saved"
                ):
                    # Update the template with new values
                    chat.update_prompt_template(
                        edited_name,
                        edited_content,
                        [input.strip() for input in edited_inputs.split(",")],
                    )
                    if edited_name != selected_template_name:
                        # If the name was edited, delete the old entry after saving the new one
                        chat.delete_prompt_template(selected_template_name)
                    st.success(f"Template '{edited_name}' updated!")
            with col2:
                if st.button("Delete Template") or response_dict["type"] == "delete":
                    chat.delete_prompt_template(selected_template_name)
                    st.success(f"Template '{selected_template_name}' deleted!")
                    st.rerun()

    with right_column:
        # Use the current content and inputs from the left column for testing
        current_content = (
            new_content
            if selected_template_name == "Create New Template"
            else edited_content
        )
        current_inputs = (
            new_inputs
            if selected_template_name == "Create New Template"
            else edited_inputs
        )
        if current_content:
            inputs = {}
            for field in current_inputs.split(", "):
                field = field.strip()  # Clean up whitespace
                if field:  # Ensure the field is not empty
                    inputs[field] = st.text_input(f"Value for {field}", key=field)

            if st.button("Run Test", key="test"):
                compiler = Compiler()
                template = compiler.compile(current_content)
                result = template(inputs)
                st.subheader("Rendered Template:")
                st.write(result)

            if result:
                with st.spinner(text="Sending prompt to agent LLM..."):
                    knowledge_rag = chat.apply_knowledge_RAG(
                        chat_agent.knowledge_store, result
                    )
                    memory_rag = chat.apply_memory_RAG(
                        chat_agent.memory_store, result, chat_agent
                    )
                    cola, colb = st.columns(2)
                    with cola.container(height=400):
                        st.write("Augmented prompt")
                        content = result + knowledge_rag + memory_rag
                        st.write(content)
                    with colb.container(height=400):
                        st.write("LLM Response")
                        st.write_stream(chat_agent.get_response_stream(content, None))
                if chat_agent.memory_store != "None":
                    chat.append_memory(
                        chat_agent.memory_store,
                        result,
                        chat_agent.last_message,
                        chat_agent,
                    )
