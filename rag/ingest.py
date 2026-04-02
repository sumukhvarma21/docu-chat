import os
import chromadb
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

os.environ["ANONYMIZED_TELEMETRY"] = "false"

CHROMA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "chroma_store")
)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Single shared client — prevents file lock conflicts
_chroma_client = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _chroma_client

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

def ingest_file(file_path: str) -> int:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.lower().endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError("Only .txt files are supported.")

    documents = loader.load()

    if not documents:
        raise ValueError("Document loaded but contained no text.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(documents)

    embeddings = get_embeddings()
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        client=get_chroma_client(),
        collection_name="default",
    )

    return len(chunks)

def clear_store():
    client = get_chroma_client()
    for collection in client.list_collections():
        client.delete_collection(collection.name)