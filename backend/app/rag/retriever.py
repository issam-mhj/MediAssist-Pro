from typing import List, Tuple
from langchain_core.documents import Document
from app.rag.vector_store import VectorStoreManager


class RetrieverManager:

    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self._manager = VectorStoreManager()

    @property
    def vector_store(self):
        return self._manager.load_vector_store()

    def search(self, query: str) -> List[Document]:
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.top_k},
        )
        documents = retriever.invoke(query)
        return documents

    def search_with_score(self, query: str) -> List[Tuple[Document, float]]:
        results = self.vector_store.similarity_search_with_score(
            query, k=self.top_k
        )
        return results

    def search_filtered(
        self, query: str, min_score: float = 0.5
    ) -> List[Tuple[Document, float]]:
        results = self.search_with_score(query)
        filtered = [(doc, score) for doc, score in results if score >= min_score]
        return filtered