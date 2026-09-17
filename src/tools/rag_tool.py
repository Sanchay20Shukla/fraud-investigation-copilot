from src.retrieval.retriever import Retriever


class RAGTool(Retriever):
    """Search only the indexed policy corpus; return text and verifiable source IDs."""
