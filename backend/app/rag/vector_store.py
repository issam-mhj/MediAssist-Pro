import os
import threading
from typing import List, Optional
from pathlib import Path
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.rag.embeddings import EmbeddingsManager
from app.rag.config import RAGConfig


class VectorStoreManager:
    """Singleton VectorStoreManager — one QdrantClient per process."""

    _instance: Optional["VectorStoreManager"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(
        self,
        collection_name: str = None,
        persist_directory: str = None,
        embedding_model_name: str = None,
        embedding_dimension: int = None,
    ):
        if self._initialized:
            return

        self.collection_name = collection_name or RAGConfig.QDRANT_COLLECTION_NAME
        self.persist_directory = Path(
            persist_directory
            or os.getenv("QDRANT_PERSIST_DIRECTORY")
            or str(RAGConfig.QDRANT_DB_DIR)
        )
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.embedding_dimension = embedding_dimension or RAGConfig.EMBEDDING_DIMENSION

        self.embeddings_manager = EmbeddingsManager(
            model_name=embedding_model_name or RAGConfig.EMBEDDING_MODEL_NAME
        )
        self.embeddings = self.embeddings_manager.get_embeddings()

        self.client = QdrantClient(path=str(self.persist_directory))
        self._ensure_collection()

        self._initialized = True
        print(f"✅ VectorStoreManager singleton initialised ({self.persist_directory})")


    def _ensure_collection(self):
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
        """Delete old vectors then embed + store new chunks."""
        if not documents:
            raise ValueError("Aucun document à indexer")

        print(f"📥 Indexation de {len(documents)} documents dans Qdrant...")

        # Delete then re-create the collection (clears old chunks)
        self.client.delete_collection(self.collection_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.embedding_dimension,
                distance=Distance.COSINE,
            ),
        )

        # Use the *same* client via QdrantVectorStore
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
        vector_store.add_documents(documents)

        count = self.client.get_collection(self.collection_name).points_count
        print(f"✅ {count} vecteurs indexés et persistés dans Qdrant")
        return vector_store

    def load_vector_store(self) -> QdrantVectorStore:
        """Return a QdrantVectorStore backed by the singleton client."""
        return QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )

    def add_documents(self, documents: List[Document]):
        if not documents:
            print("Aucun document à ajouter")
            return

        vector_store = self.load_vector_store()
        vector_store.add_documents(documents)

        count = self.client.get_collection(self.collection_name).points_count
        print(f"✅ {len(documents)} documents ajoutés. Total: {count} vecteurs")


    def get_collection_info(self) -> dict:
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "points_count": info.points_count,
                "status": info.status.value if hasattr(info.status, 'value') else str(info.status),
                "persist_directory": str(self.persist_directory),
            }
        except Exception as e:
            return {"error": str(e)}

    def delete_collection(self):
        self.client.delete_collection(self.collection_name)
        print(f"🗑️ Collection '{self.collection_name}' supprimée")

    def collection_exists_with_data(self) -> bool:
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count > 0
        except Exception:
            return False