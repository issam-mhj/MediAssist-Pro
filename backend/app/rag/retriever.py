"""
Module de recherche (retrieval) pour le système RAG MediAssist-Pro.
Récupère les chunks les plus pertinents depuis Qdrant.
"""

from typing import List, Tuple
from langchain_core.documents import Document
from app.rag.vector_store import VectorStoreManager


class RetrieverManager:
    """Gère la récupération des documents pertinents depuis le vector store."""

    def __init__(self, top_k: int = 5):
        """
        Initialise le retriever.

        Args:
            top_k: Nombre de chunks à récupérer.
        """
        self.top_k = top_k
        self.vector_store_manager = VectorStoreManager()
        self._vector_store = None

    @property
    def vector_store(self):
        """Lazy-loading du vector store."""
        if self._vector_store is None:
            self._vector_store = self.vector_store_manager.load_vector_store()
        return self._vector_store

    def search(self, query: str) -> List[Document]:
        """
        Recherche les documents les plus pertinents par similarité.

        Args:
            query: Question de l'utilisateur.

        Returns:
            Liste des Documents les plus pertinents.
        """
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.top_k},
        )
        documents = retriever.invoke(query)
        return documents

    def search_with_score(self, query: str) -> List[Tuple[Document, float]]:
        """
        Recherche avec scores de similarité.

        Args:
            query: Question de l'utilisateur.

        Returns:
            Liste de tuples (Document, score).
        """
        results = self.vector_store.similarity_search_with_score(
            query, k=self.top_k
        )
        return results

    def search_filtered(
        self, query: str, min_score: float = 0.5
    ) -> List[Tuple[Document, float]]:
        """
        Recherche avec filtrage par score minimum.

        Args:
            query: Question de l'utilisateur.
            min_score: Score minimum de similarité.

        Returns:
            Liste filtrée de tuples (Document, score).
        """
        results = self.search_with_score(query)
        # Pour cosine similarity dans Qdrant, plus le score est élevé, plus c'est pertinent
        filtered = [(doc, score) for doc, score in results if score >= min_score]
        return filtered