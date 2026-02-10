"""
Module de gestion du vector store avec Qdrant pour le système RAG MediAssist-Pro.
Gère la création, le chargement et la persistance des embeddings.
"""

from typing import List, Optional
from pathlib import Path
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.rag.embeddings import EmbeddingsManager


class VectorStoreManager:
    """Gère le vector store Qdrant avec persistance locale."""

    def __init__(
        self,
        collection_name: str = "mediassist_documents",
        persist_directory: str = "./qdrant_data",
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        embedding_dimension: int = 384,
    ):
        """
        Initialise le gestionnaire de vector store.

        Args:
            collection_name: Nom de la collection Qdrant.
            persist_directory: Répertoire pour la persistance locale.
            embedding_model_name: Modèle d'embeddings à utiliser.
            embedding_dimension: Dimension des vecteurs d'embedding.
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.embedding_dimension = embedding_dimension

        # Initialiser le gestionnaire d'embeddings
        self.embeddings_manager = EmbeddingsManager(model_name=embedding_model_name)
        self.embeddings = self.embeddings_manager.get_embeddings()

        # Initialiser le client Qdrant avec persistance locale
        self.client = QdrantClient(path=str(self.persist_directory))

        # S'assurer que la collection existe
        self._ensure_collection()

    def _ensure_collection(self):
        """Crée la collection si elle n'existe pas encore."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE,
                ),
            )
            print(f"✅ Collection '{self.collection_name}' créée dans Qdrant")
        else:
            info = self.client.get_collection(self.collection_name)
            print(
                f"📂 Collection '{self.collection_name}' chargée "
                f"({info.points_count} points)"
            )

    def create_vector_store(self, documents: List[Document]) -> QdrantVectorStore:
        """
        Crée un vector store à partir de documents et persiste les embeddings.

        Args:
            documents: Liste de Documents à indexer.

        Returns:
            Instance QdrantVectorStore.
        """
        if not documents:
            raise ValueError("Aucun document à indexer")

        print(f"📥 Indexation de {len(documents)} documents dans Qdrant...")

        # Supprimer l'ancienne collection et la recréer
        self.client.delete_collection(self.collection_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.embedding_dimension,
                distance=Distance.COSINE,
            ),
        )

        vector_store = QdrantVectorStore.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=self.collection_name,
            url=None,  # Local mode
            path=str(self.persist_directory),
            force_recreate=True,
        )

        count = self.client.get_collection(self.collection_name).points_count
        print(f"✅ {count} vecteurs indexés et persistés dans Qdrant")

        return vector_store

    def load_vector_store(self) -> QdrantVectorStore:
        """
        Charge un vector store Qdrant existant depuis le disque.

        Returns:
            Instance QdrantVectorStore.
        """
        vector_store = QdrantVectorStore.from_existing_collection(
            embedding=self.embeddings,
            collection_name=self.collection_name,
            path=str(self.persist_directory),
        )
        return vector_store

    def add_documents(self, documents: List[Document]):
        """
        Ajoute de nouveaux documents à la collection existante.

        Args:
            documents: Liste de Documents à ajouter.
        """
        if not documents:
            print("⚠️ Aucun document à ajouter")
            return

        vector_store = self.load_vector_store()
        vector_store.add_documents(documents)

        count = self.client.get_collection(self.collection_name).points_count
        print(f"✅ {len(documents)} documents ajoutés. Total: {count} vecteurs")

    def get_collection_info(self) -> dict:
        """
        Retourne les informations sur la collection.

        Returns:
            Dictionnaire avec les informations de la collection.
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status.value,
                "persist_directory": str(self.persist_directory),
            }
        except Exception as e:
            return {"error": str(e)}

    def delete_collection(self):
        """Supprime la collection."""
        self.client.delete_collection(self.collection_name)
        print(f"🗑️ Collection '{self.collection_name}' supprimée")

    def collection_exists_with_data(self) -> bool:
        """Vérifie si la collection existe et contient des données."""
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count > 0
        except Exception:
            return False