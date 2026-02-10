"""RAG (Retrieval-Augmented Generation) package for MediAssist-Pro."""

__all__ = [
    "DocumentProcessor",
    "load_documents",
    "DocumentChunker",
    "EmbeddingsManager",
    "VectorStoreManager",
    "RetrieverManager",
    "ResponseGenerator",
]


def __getattr__(name):
    if name == "DocumentProcessor":
        from app.rag.document_processor import DocumentProcessor
        return DocumentProcessor
    elif name == "load_documents":
        from app.rag.document_processor import load_documents
        return load_documents
    elif name == "DocumentChunker":
        from app.rag.chunking import DocumentChunker
        return DocumentChunker
    elif name == "EmbeddingsManager":
        from app.rag.embeddings import EmbeddingsManager
        return EmbeddingsManager
    elif name == "VectorStoreManager":
        from app.rag.vector_store import VectorStoreManager
        return VectorStoreManager
    elif name == "RetrieverManager":
        from app.rag.retriever import RetrieverManager
        return RetrieverManager
    elif name == "ResponseGenerator":
        from app.rag.generator import ResponseGenerator
        return ResponseGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
