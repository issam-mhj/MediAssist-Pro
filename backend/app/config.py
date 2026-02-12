from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

# Resolve the .env file path relative to this config file (backend/.env)
_env_file = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OPENAI_API_KEY: Optional[str] = None
    LLAMA_CLOUD_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2"
    EMBEDDINGS_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_STORE_TYPE: str = "qdrant"
    QDRANT_PERSIST_DIRECTORY: str = "./qdrant_data"
    QDRANT_COLLECTION_NAME: str = "mediassist_documents"
    # Legacy ChromaDB setting (kept for backward compat)
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    APP_NAME: str = "MediAssist-Pro"
    DEBUG: bool = False

    class Config:
        env_file = str(_env_file)
        extra = "ignore"

settings = Settings()
