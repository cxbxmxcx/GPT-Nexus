import plotly.graph_objects as go
import streamlit as st
from sklearn.decomposition import PCA

from gpt_nexus.nexus_base.chat_models import MemoryType
from gpt_nexus.ui.cache import get_chat_system
from gpt_nexus.ui.options import create_options_ui


def view_embeddings(chat, memory_store):
    """
    Displays all memories and their embeddings from ChromaDB.
    """
    if memory_store is None:
        st.error("Please create a memory store first.")
        st.stop()

    memories = chat.get_memories(memory_store, include=["documents", "embeddings"])

    embeddings = memories["embeddings"]
    memories = memories["documents"]

    if embeddings and memories and len(embeddings) > 3:
        # Applying PCA to reduce dimensions to 3
        pca = PCA(n_components=3)
        reduced_embeddings = pca.fit_transform(embeddings)

        # Creating a 3D plot using Plotly
        fig = go.Figure(
            data=[
                go.Scatter3d(
                    x=reduced_embeddings[:, 0],
                    y=reduced_embeddings[:, 1],
                    z=reduced_embeddings[:, 2],
                    mode="markers",
                    text=memories,  # Adding document texts for hover
                    hoverinfo="text",  # Showing only the text on hover
                    marker=dict(
                        size=12,
                        color=[
                            f"rgb({int((x+1)*128)}, {int((y+1)*128)}, {int((z+1)*128)})"
                            for x, y, z in zip(
                                reduced_embeddings[:, 0],
                                reduced_embeddings[:, 1],
                                reduced_embeddings[:, 2],
                            )
                        ],
                        opacity=0.8,
                    ),
                )
            ],
            layout=dict(
                title="Document Embeddings",
                scene=dict(
                    xaxis_title="PCA 1",
                    yaxis_title="PCA 2",
                    zaxis_title="PCA 3",
                ),
                height=800,
            ),
        )
        st.plotly_chart(fig)
    else:
        st.error("Not enough memories to display.")


def add_memory_to_store(chat, memory_store):
    if memory_store is None:
        st.error("Please create a memory store first.")
        st.stop()

    st.title("Agent Settings")
    agents = chat.get_agent_names()

    agents = [agent for agent in agents if chat.get_agent(agent).supports_memory]

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

    memory = st.text_area("Enter a memory to add to the store:")

    if st.button("Add Memory") and memory != "" and memory is not None:
        chat.load_memory(memory_store, memory, chat_agent)
        st.success("Memory added successfully!")


def memory_page(username):
    chat = get_chat_system()
    user = chat.get_participant(username)
    if user is None:
        st.error("Invalid user")
        st.stop()

    # Streamlit UI
    st.title("Memory Store Manager")

    with st.sidebar.expander("Manage Memory Stores"):
        store_name = st.text_input("Enter a new memory store name to create:")
        store_name = store_name.strip().replace(" ", "_")
        if st.button(
            "Create Memory Store",
            disabled=(
                store_name == ""
                or store_name in chat.get_memory_store_names()
                or store_name is None
                or len(store_name) < 3
            ),
        ):
            chat.add_memory_store(store_name)
            st.success(f"Memory Store '{store_name}' created!")

        selected_store_to_delete = st.selectbox(
            "Select a memory store to delete:",
            options=list(chat.get_memory_store_names()),
        )
        if st.button("Delete Memory Store"):
            chat.delete_memory_store(selected_store_to_delete)
            st.success(f"Memory Store '{selected_store_to_delete}' deleted!")

    # Memory Management within a Memory Store
    st.header("Manage Memory Store")
    selected_store = st.selectbox(
        "Select a memory store to manage memories:",
        options=list(chat.get_memory_store_names()),
        key="manage_docs",
    )
    st.header(f"Managing {selected_store}")
    config_tabs = st.tabs(
        [
            "Add memories",
            "Examine memories",
            "View Memory Embeddings",
            "Query Memories",
            "Configuration",
        ]
    )

    with config_tabs[0]:
        st.subheader("Add Memory to Memory Store")
        add_memory_to_store(chat, selected_store)

    with config_tabs[1]:
        st.subheader("Examine Memories in Memory Store")
        df = chat.examine_memories(selected_store)
        st.table(df)

    with config_tabs[2]:
        st.subheader("View Embeddings in Memory Store")
        view_embeddings(chat, selected_store)

    with config_tabs[3]:
        st.subheader("Query Memory Store")
        query = st.text_area("Enter a query to search for similar memories:")
        if st.button("Search"):
            docs = chat.query_memories(selected_store, query)
            for doc in docs:
                st.write(doc)

    with config_tabs[4]:
        st.subheader("Memory Store Configuration")
        memory_store = chat.get_memory_store(selected_store)

        memory_types = [
            MemoryType.CONVERSATIONAL.value,
            MemoryType.SEMANTIC.value,
            MemoryType.PROCEDURAL.value,
            MemoryType.EPISODIC.value,
        ]
        memory_store.memory_type = st.selectbox(
            "Memory Type",
            memory_types,
            index=memory_types.index(memory_store.memory_type),
        )

        memory_function = chat.get_memory_function(memory_store.memory_type)
        st.write(f"Memory Function: {memory_function}")

        if st.button("Save Configuration"):
            chat.update_memory_store(memory_store)
