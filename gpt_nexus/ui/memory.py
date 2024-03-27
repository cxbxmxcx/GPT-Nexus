from collections import defaultdict

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from gpt_nexus.nexus_base.chat_models import MemoryType
from gpt_nexus.ui.cache import get_chat_system
from gpt_nexus.ui.options import create_options_ui


def group_memories_by_labels(memories, labels):
    """
    Groups memories by labels.

    Parameters:
    - memories: A list of memory items.
    - labels: A list of labels corresponding to each memory item.

    Returns:
    A defaultdict with labels as keys and lists of corresponding memories as values.
    """
    grouped_memories = defaultdict(list)
    for emb, label in zip(memories, labels):
        grouped_memories[label].append(emb)
    return grouped_memories


def display_memories_per_label(grouped_memories):
    """
    Displays the number of memories per label in a Streamlit table.

    Parameters:
    - grouped_memories: A defaultdict with labels as keys and lists of memories as values.
    """
    # Calculating the number of memories per label
    label_counts = {
        label: len(memories) for label, memories in grouped_memories.items()
    }

    # Converting to a DataFrame for nicer display in Streamlit
    import pandas as pd

    label_counts_df = pd.DataFrame(
        list(label_counts.items()), columns=["Label", "Number of Memories"]
    )

    # Displaying the DataFrame as a table in Streamlit
    st.table(label_counts_df.sort_values(by="Number of Memories", ascending=False))


def view_embeddings(chat, memory_store):
    """
    Displays all memories and their embeddings from ChromaDB, colored by KMeans clusters.
    Finds the optimum number of clusters based on silhouette scores for 2 to 20 clusters,
    with a preference for smaller, more numerous clusters.
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

        # Find the optimum number of clusters using silhouette scores
        silhouette_scores = []
        for n_clusters in range(2, 21):  # Test from 2 to 20 clusters
            if n_clusters >= len(reduced_embeddings):
                break
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(reduced_embeddings)
            score = silhouette_score(reduced_embeddings, labels)
            silhouette_scores.append(score)

        # You might prefer more clusters, so instead of directly choosing the highest score,
        # consider a point where adding more clusters doesn't significantly improve the score
        # This is a simplified approach to prioritize more, smaller clusters
        n_clusters_optimal = (
            np.argmax(silhouette_scores) + 2
        )  # Adding 2 because range starts at 2

        # Now that we have our optimal number of clusters, run KMeans with it
        kmeans_optimal = KMeans(n_clusters=n_clusters_optimal, random_state=42)
        kmeans_optimal.fit(reduced_embeddings)
        labels_optimal = kmeans_optimal.labels_

        # Creating a 3D plot using Plotly with data colored by optimal cluster assignment
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
                        color=labels_optimal,  # Color by cluster labels
                        colorscale="Viridis",  # You can choose any colorscale
                        opacity=0.8,
                    ),
                )
            ],
            layout=dict(
                title=f"Document Embeddings Colored by KMeans Clusters (Optimal Clusters: {n_clusters_optimal})",
                scene=dict(
                    xaxis_title="PCA 1",
                    yaxis_title="PCA 2",
                    zaxis_title="PCA 3",
                ),
                height=800,
            ),
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            st.plotly_chart(fig)

        with col2:
            # Group embeddings by labels using the provided function
            grouped_memories = group_memories_by_labels(memories, labels_optimal)
            chat_agent = get_agent(chat, "embed")
            display_memories_per_label(grouped_memories)
            st.write(
                "Consider using the agent to compress memories if you have more than 10 memories in a cluster."
            )
            if st.button("Compress Memories"):
                with st.spinner(text="The agent is compressing the memories..."):
                    chat.compress_memories(memory_store, grouped_memories, chat_agent)
                    st.success("Memories compressed successfully!")
                    st.rerun()

    else:
        st.error("Not enough memories to display.")


def get_agent(chat, agent_key):
    st.title("Memory Compression Settings")
    agents = chat.get_agent_names()
    agents = [agent for agent in agents if chat.get_agent(agent).supports_memory]
    selected_agent = st.selectbox(
        "Choose an agent engine:",
        agents,
        key=agent_key + "agent",
        # label_visibility="collapsed",
        help="Choose an agent to chat with.",
    )
    chat_agent = chat.get_agent(selected_agent)
    with st.expander("Agent Options:", expanded=False):
        options = chat_agent.get_attribute_options()
        if options:
            selected_options = create_options_ui(options, agent_key)
            for key, value in selected_options.items():
                setattr(chat_agent, key, value)
    return chat_agent


def add_memory_to_store(chat, memory_store):
    if memory_store is None:
        st.error("Please create a memory store first.")
        st.stop()

    chat_agent = get_agent(chat, "add")

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
            "Memory Embeddings & Compression",
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
        st.subheader("Memory Embeddings and Compression")
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
        st.text_area("Memory Function:", memory_function.function_prompt, disabled=True)

        if st.button("Save Configuration"):
            chat.update_memory_store(memory_store)
            st.success("Configuration saved successfully!")
