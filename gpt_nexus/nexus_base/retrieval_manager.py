import chromadb
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class RetrievalManager:
    def __init__(self):
        self.client = OpenAI()
        self.CHROMA_DB = "nexus_chroma_db"

    def get_embedding(self, text, model="text-embedding-3-small"):
        text = str(text)
        text = text.replace("\n", " ")
        return (
            self.client.embeddings.create(input=[text], model=model).data[0].embedding
        )

    def query_documents(self, knowledge_store, input_text, n_results=5):
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=knowledge_store)
        embedding = self.get_embedding(input_text)
        docs = collection.query(
            query_embeddings=[embedding], n_results=n_results, include=["documents"]
        )
        return docs["documents"]

    def apply_knowledge_RAG(self, knowledge_store, input_text, n_results=5):
        docs = self.query_documents(knowledge_store, input_text, n_results)

        prompt = input_text
        if docs:
            prompt += "\nUse the following documents to help answer the question:\n"
            for i, doc in enumerate(docs):
                prompt += f"Document {i+1}:\n{doc}\n"
        return prompt

    def get_documents(self, knowledge_store, include=["documents", "embeddings"]):
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=knowledge_store)
        documents = collection.get(include=include)
        return documents

    def load_document(self, knowledge_store, uploaded_file, splitter):
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
        if uploaded_file is not None:
            document = uploaded_file.read().decode("utf-8")
            docs = splitter.create_documents([document])

            embeddings = [self.get_embedding(doc) for doc in docs]
            ids = [f"id{i}" for i in range(len(docs))]

            # create chroma database client
            chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
            # get or create a collection
            collection = chroma_client.get_or_create_collection(name=knowledge_store)
            docs = [str(doc.page_content) for doc in docs]

            collection.add(embeddings=embeddings, documents=docs, ids=ids)
            return True
        return False

    def examine_documents(self, knowledge_store):
        """
        Displays all documents from ChromaDB.
        """
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=knowledge_store)
        documents = collection.get(include=["documents"])

        df = pd.DataFrame({"ID": documents["ids"], "Document": documents["documents"]})

        # Display the DataFrame in Streamlit
        return df

    def delete_knowledge_store(self, knowledge_store):
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        chroma_client.delete_collection(knowledge_store)
        return True
