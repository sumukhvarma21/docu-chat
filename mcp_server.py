from fastmcp import FastMCP
from rag.ingest import clear_store, ingest_file
from rag.retriever import ask_question

mcp = FastMCP(
    name="DocuChat",
    description=(
        "Chat with your documents. "
        "Ingest a .txt file then ask natural language questions about it. "
        "Answers are grounded in the document."
    ),
)


@mcp.tool()
def ingest_document(file_path: str) -> str:
    """
    Ingest a .txt file into the vector store so it can be queried.
    After calling this, use query_document to ask questions.

    Args:
        file_path: Absolute path to the .txt file.
                   Example: "/Users/yourname/documents/report.txt"
    """
    try:
        chunks = ingest_file(file_path)
        return (
            f"Successfully ingested '{file_path}' into {chunks} chunks. "
            f"You can now use query_document to ask questions about it."
        )
    except FileNotFoundError as e:
        return f"File not found: {e}"
    except ValueError as e:
        return f"Unsupported file or empty document: {e}"
    except Exception as e:
        return f"Unexpected error during ingestion: {e}"


@mcp.tool()
def query_document(question: str) -> str:
    """
    Ask a natural language question about the ingested document.
    Searches for the most relevant sections and uses Gemini to answer.

    Args:
        question: The question to ask about the document content.
    """
    try:
        return ask_question(question)
    except RuntimeError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Unexpected error while answering: {e}"


@mcp.tool()
def reset_store() -> str:
    """
    Clear all ingested documents from the vector store.
    Use this before ingesting a new document to start fresh.
    """
    try:
        clear_store()
        return "Vector store cleared. Ready to ingest a new document."
    except Exception as e:
        return f"Error clearing store: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")