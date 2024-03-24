import chromadb
import pandas as pd
from dotenv import load_dotenv
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)
from openai import OpenAI

from gpt_nexus.nexus_base.utils import id_hash

load_dotenv()


class MemoryManager:
    def __init__(self):
        self.client = OpenAI()
        self.CHROMA_DB = "nexus_memory_chroma_db"

    def get_memory_embedding(self, text, model="text-embedding-3-small"):
        if text is None:
            return None

        text = str(text)
        text = text.replace("\n", " ")
        return (
            self.client.embeddings.create(input=[text], model=model).data[0].embedding
        )

    def query_memories(self, memory_store, input_text, n_results=5):
        if memory_store is None or input_text is None:
            return None

        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=memory_store)
        embedding = self.get_memory_embedding(input_text)
        docs = collection.query(
            query_embeddings=[embedding], n_results=n_results, include=["documents"]
        )
        return docs["documents"]

    def apply_memory_RAG(self, memory_store, input_text, n_results=5):
        if memory_store is None or input_text is None:
            return None

        docs = self.query_memories(memory_store, input_text, n_results)

        prompt = ""
        if docs:
            prompt += "\nUse the following memories to help answer the question:\n"
            for i, doc in enumerate(docs):
                prompt += f"Memory {i+1}:\n{doc}\n"
        return prompt

    def get_memories(self, memory_store, include=["documents", "embeddings"]):
        if memory_store is None:
            return None
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=memory_store)
        memories = collection.get(include=include)
        return memories

    def get_splitter(self, memory_store):
        chunking_option = memory_store.chunking_option
        chunk_size = memory_store.chunk_size
        overlap = memory_store.overlap

        if chunking_option == "Character":
            return CharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=overlap, separator="\n"
            )
        elif chunking_option == "Recursive":
            return RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                length_function=len,
                is_separator_regex=False,
            )

    def load_memory(self, memory_store, memory):
        """
        Loads a document from upload, splits it based on chunking option and saves embeddings.

        Args:
            uploaded_file: A Streamlit file uploader object.
            chunker: A Langchain TextSplitter object (CharacterTextSplitter or WordTextSplitter).
            chunk_size: The size of each chunk.
            overlap: The size of the overlap between chunks.

        Returns:
            None
        """
        if memory_store is not None and memory is not None and len(memory) > 0:
            splitter = self.get_splitter(memory_store)
            docs = splitter.create_documents([memory])

            embeddings = [self.get_memory_embedding(doc) for doc in docs]

            # create chroma database client
            chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
            # get or create a collection
            collection = chroma_client.get_or_create_collection(name=memory_store.name)
            docs = [str(doc.page_content) for doc in docs]
            ids = [id_hash(m) for m in docs]

            collection.add(embeddings=embeddings, documents=docs, ids=ids)
            return True
        return False

    def examine_memories(self, memory_store):
        """
        Displays all documents from ChromaDB.
        """
        if memory_store is None:
            return None
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=memory_store)
        memories = collection.get(include=["documents"])

        df = pd.DataFrame({"ID Hash": memories["ids"], "Memory": memories["documents"]})

        # Display the DataFrame in Streamlit
        return df

    def delete_memory_store(self, memory_store):
        if memory_store is None:
            return False
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        chroma_client.delete_collection(memory_store)
        return True

    def append_memory(
        self, memory_store, user_input, llm_response, memory_function=None, agent=None
    ):
        if memory_store is None or user_input is None or llm_response is None:
            return False

        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=memory_store.name)

        memory = f"""
        user:
        {user_input}
        assistant:
        {llm_response}
        """

        if memory_function is not None and agent is not None:
            memories = agent.get_semantic_response(memory_function, memory).split(",")
        else:
            memories = [memory]

        embeddings = [self.get_memory_embedding(m) for m in memories]
        ids = [id_hash(m) for m in memory]

        collection.add(embeddings=embeddings, documents=memories, ids=ids)
        return True