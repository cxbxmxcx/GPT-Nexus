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


class KnowledgeManager:
    def __init__(self):
        self.client = OpenAI()
        self.CHROMA_DB = "nexus_knowledge_chroma_db"

    def get_document_embedding(self, text, model="text-embedding-3-small"):
        if text is None:
            return None
        text = str(text)
        text = text.replace("\n", " ")
        return (
            self.client.embeddings.create(input=[text], model=model).data[0].embedding
        )

    def query_documents(self, knowledge_store, input_text, n_results=5):
        if knowledge_store is None or input_text is None:
            return None

        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=knowledge_store)
        embedding = self.get_document_embedding(input_text)
        docs = collection.query(
            query_embeddings=[embedding], n_results=n_results, include=["documents"]
        )
        return docs["documents"]

    def apply_knowledge_RAG(self, knowledge_store, input_text, n_results=5):
        if knowledge_store is None or input_text is None:
            return None

        docs = self.query_documents(knowledge_store, input_text, n_results)

        prompt = ""
        if docs:
            prompt += "\nUse the following documents to help answer the question:\n"
            for i, doc in enumerate(docs):
                prompt += f"Document {i+1}:\n{doc}\n"
        return prompt

    def get_documents(self, knowledge_store, include=["documents", "embeddings"]):
        if knowledge_store is None:
            return None

        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=knowledge_store)
        documents = collection.get(include=include)
        return documents

    def get_splitter(self, knowledge_store):
        chunking_option = knowledge_store.chunking_option
        chunk_size = knowledge_store.chunk_size
        overlap = knowledge_store.overlap

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

    def read_file(self, uploaded_file):
        document = None
        if uploaded_file is not None:
            # Check the file type
            if uploaded_file.type == "text/plain":
                document = uploaded_file.read().decode("utf-8")
            elif uploaded_file.type == "application/pdf":
                try:
                    import pdfplumber

                    with pdfplumber.open(uploaded_file) as pdf:
                        pages = [page.extract_text() for page in pdf.pages]
                    document = "\n".join(pages)  # Join the text of all pages
                except ImportError:
                    raise Exception("Please install pdfplumber to read PDF files.")
            elif (
                uploaded_file.type
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ):
                try:
                    import docx

                    doc = docx.Document(uploaded_file)
                    fullText = []
                    for para in doc.paragraphs:
                        fullText.append(para.text)
                    document = "\n".join(fullText)
                except ImportError:
                    raise Exception("Please install python-docx to read DOCX files.")
        return document

    def load_document(
        self,
        knowledge_store,
        uploaded_file,
    ):
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
        if knowledge_store is not None and uploaded_file is not None:
            document = self.read_file(uploaded_file)

            splitter = self.get_splitter(knowledge_store)
            docs = splitter.create_documents([document])

            embeddings = [self.get_document_embedding(doc) for doc in docs]

            # create chroma database client
            chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
            # get or create a collection
            collection = chroma_client.get_or_create_collection(
                name=knowledge_store.name
            )
            docs = [str(doc.page_content) for doc in docs]
            ids = [id_hash(m) for m in docs]

            collection.add(embeddings=embeddings, documents=docs, ids=ids)
            return True
        return False

    def examine_documents(self, knowledge_store):
        """
        Displays all documents from ChromaDB.
        """
        if knowledge_store is None:
            return None

        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        collection = chroma_client.get_or_create_collection(name=knowledge_store)
        documents = collection.get(include=["documents"])

        df = pd.DataFrame(
            {"ID Hash": documents["ids"], "Document": documents["documents"]}
        )

        # Display the DataFrame in Streamlit
        return df

    def delete_knowledge_store(self, knowledge_store):
        if knowledge_store is None:
            return False

        chroma_client = chromadb.PersistentClient(path=self.CHROMA_DB)
        chroma_client.delete_collection(knowledge_store)
        return True
