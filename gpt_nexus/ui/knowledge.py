import plotly.graph_objects as go
import streamlit as st
from sklearn.decomposition import PCA

from gpt_nexus.ui.cache import get_chat_system


def view_embeddings(chat, knowledge_store):
    """
    Displays all documents and their embeddings from ChromaDB.
    """
    if knowledge_store is None:
        st.error("Please create a knowledge store first.")
        st.stop()

    documents = chat.get_documents(knowledge_store, include=["documents", "embeddings"])

    embeddings = documents["embeddings"]
    documents = documents["documents"]

    if embeddings and documents and len(embeddings) > 3:
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
                    text=documents,  # Adding document texts for hover
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
        st.error("Not enough documents available to display.")


def add_document_to_store(chat, knowledge_store):
    if knowledge_store is None:
        st.error("Please create a knowledge store first.")
        st.stop()

    document_file = st.file_uploader(
        "Choose a file to upload as a new document:",
        type=["txt", "md", "html", "csv", "py", "json", "pdf", "docx"],
        key="upload_doc",
    )

    if document_file is not None:
        # Assuming text files for simplicity, but you may need to handle different file types differently
        document_name = document_file.name

        chat.load_document(knowledge_store, document_file)
        st.success("Document uploaded and processed successfully!")
        chat.add_document_to_store(knowledge_store, document_name)
        st.success(
            f"Document '{document_name}' added to Knowledge Store '{knowledge_store}'!"
        )


def knowledge_page(username):
    chat = get_chat_system()
    user = chat.get_participant(username)
    if user is None:
        st.error("Invalid user")
        st.stop()

    # Streamlit UI
    st.title("Knowledge Store Manager")

    with st.sidebar.expander("Manage Knowledge Stores"):
        store_name = st.text_input("Enter a new knowledge store name to create:")
        if st.button(
            "Create Knowledge Store",
            disabled=(
                store_name == ""
                or store_name in chat.get_knowledge_store_names()
                or store_name is None
                or len(store_name) < 3
            ),
        ):
            chat.add_knowledge_store(store_name)
            st.success(f"Knowledge Store '{store_name}' created!")

        selected_store_to_delete = st.selectbox(
            "Select a knowledge store to delete:",
            options=list(chat.get_knowledge_store_names()),
        )
        if st.button("Delete Knowledge Store"):
            chat.delete_knowledge_store(selected_store_to_delete)
            st.success(f"Knowledge Store '{selected_store_to_delete}' deleted!")

    # Document Management within a Knowledge Store
    st.header("Manage Knowledge Store")
    selected_store = st.selectbox(
        "Select a knowledge store to manage documents:",
        options=list(chat.get_knowledge_store_names()),
        key="manage_docs",
    )
    st.header(f"Managing {selected_store}")
    config_tabs = st.tabs(
        [
            "Add documents",
            "Examine documents",
            "View Embeddings",
            "Query Documents",
            "Configuration",
        ]
    )

    with config_tabs[0]:
        st.subheader("Add Documents to Knowledge Store")
        add_document_to_store(chat, selected_store)

    with config_tabs[1]:
        st.subheader("Examine Documents in Knowledge Store")
        df = chat.examine_documents(selected_store)
        st.table(df)

    with config_tabs[2]:
        st.subheader("View Embeddings in Knowledge Store")
        view_embeddings(chat, selected_store)

    with config_tabs[3]:
        st.subheader("Query Knowledge Store")
        query = st.text_area("Enter a query to search for similar documents:")
        if st.button("Search"):
            docs = chat.query_documents(selected_store, query)
            for doc in docs:
                st.write(doc)

    with config_tabs[4]:
        st.subheader("Knowledge Store Configuration")
        knowledge_store = chat.get_knowledge_store(selected_store)

        options = ["Character", "Recursive"]
        knowledge_store.chunking_option = st.selectbox(
            "Chunking Option",
            options,
            index=options.index(knowledge_store.chunking_option),
        )
        knowledge_store.chunk_size = st.number_input(
            "Chunk Size", min_value=1, value=knowledge_store.chunk_size
        )
        knowledge_store.overlap = st.number_input(
            "Overlap", min_value=0, value=knowledge_store.overlap
        )

        if st.button("Save Configuration"):
            chat.update_knowledge_store(knowledge_store)
