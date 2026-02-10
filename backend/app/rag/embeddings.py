from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import List


class EmbeddingsManager:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
    ):
        self.model_name = model_name
        self.device = device
        self._embeddings_model = None

    @property
    def embeddings_model(self) -> HuggingFaceEmbeddings:
        if self._embeddings_model is None:
            print(f"🧠 Chargement du modèle d'embeddings: {self.model_name}...")
            self._embeddings_model = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={"device": self.device},
                encode_kwargs={"normalize_embeddings": True},
            )
            print("✅ Modèle d'embeddings chargé")
        return self._embeddings_model

    def get_embeddings(self) -> HuggingFaceEmbeddings:
        return self.embeddings_model

    def embed_text(self, text: str) -> List[float]:
        return self.embeddings_model.embed_query(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings_model.embed_documents(texts)

    def get_dimension(self) -> int:
        sample = self.embed_text("test")
        return len(sample)