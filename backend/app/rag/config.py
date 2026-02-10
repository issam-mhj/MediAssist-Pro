"""
Configuration pour le prétraitement et le chunking de documents.
Permet de centraliser tous les paramètres configurables.
"""

import os
from pathlib import Path


class RAGConfig:
    RAG_DIR = Path(__file__).parent
    
    DEFAULT_PDF_PATH = RAG_DIR / "maintenance-des-appareils-de-laboratoire.pdf"
    
    DOCUMENTS_DIR = RAG_DIR / "documents"

    QDRANT_DB_DIR = RAG_DIR.parent.parent / "qdrant_data"
    
    CHAR_CHUNK_SIZE = 1000
    CHAR_CHUNK_OVERLAP = 200
    
    CHUNK_SEPARATORS = [
        "\n\n",     
        "\n",       
        ". ",       
        ", ",       
        " ",        
        ""          
    ]
    
    SEMANTIC_BREAKPOINT_TYPE = "percentile" 
    
    EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    
    EMBEDDING_DEVICE = "cpu"  
    EMBEDDING_DIMENSION = 384
    
    PREPROCESSING_CONFIG = {
        "normalize_whitespace": True,      
        "fix_hyphenation": True,           
        "normalize_quotes": True,          
        "remove_control_chars": True,
        "remove_empty_lines": True,        
        "strip_whitespace": True,         
    }
    
    MIN_PAGE_TEXT_LENGTH = 50
    

    TOP_K_RETRIEVAL = 5
    
    MIN_SIMILARITY_SCORE = 0.5

    QDRANT_COLLECTION_NAME = "mediassist_documents"
    
    QDRANT_DISTANCE_METRIC = "cosine"  
    
    VERBOSE = True
    
    SHOW_PROGRESS = True

    OPENAI_MODEL = "gpt-3.5-turbo"
    
    GENERATION_TEMPERATURE = 0.7
    
    MAX_RESPONSE_TOKENS = 500
    
    SYSTEM_PROMPT = """Tu es un assistant spécialisé en maintenance d'équipements 
    de laboratoire médical. Tu dois répondre de manière précise et professionnelle 
    en te basant uniquement sur les informations fournies dans le contexte."""

    @classmethod
    def get_chunk_config(cls) -> dict:
        """Retourne la configuration de chunking"""
        return {
            "chunk_size": cls.CHAR_CHUNK_SIZE,
            "chunk_overlap": cls.CHAR_CHUNK_OVERLAP,
            "separators": cls.CHUNK_SEPARATORS,
            "semantic_breakpoint_type": cls.SEMANTIC_BREAKPOINT_TYPE
        }
    
    @classmethod
    def get_embedding_config(cls) -> dict:
        """Retourne la configuration des embeddings"""
        return {
            "model_name": cls.EMBEDDING_MODEL_NAME,
            "device": cls.EMBEDDING_DEVICE,
            "dimension": cls.EMBEDDING_DIMENSION
        }
    
    @classmethod
    def get_retrieval_config(cls) -> dict:
        """Retourne la configuration de recherche"""
        return {
            "top_k": cls.TOP_K_RETRIEVAL,
            "min_similarity": cls.MIN_SIMILARITY_SCORE
        }
    
    @classmethod
    def ensure_directories(cls):
        """Crée les répertoires nécessaires s'ils n'existent pas"""
        cls.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.QDRANT_DB_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Valide la configuration"""
        errors = []
        
        if cls.CHAR_CHUNK_OVERLAP >= cls.CHAR_CHUNK_SIZE:
            errors.append("CHAR_CHUNK_OVERLAP doit être < CHAR_CHUNK_SIZE")
        
        if not cls.DEFAULT_PDF_PATH.exists():
            errors.append(f"PDF par défaut introuvable: {cls.DEFAULT_PDF_PATH}")
        
        if cls.TOP_K_RETRIEVAL < 1:
            errors.append("TOP_K_RETRIEVAL doit être >= 1")
        
        if not 0 <= cls.MIN_SIMILARITY_SCORE <= 1:
            errors.append("MIN_SIMILARITY_SCORE doit être entre 0 et 1")
        
        if errors:
            print("❌ Erreurs de configuration:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("✅ Configuration valide")
        return True
    
    @classmethod
    def print_config(cls):
        """Affiche la configuration actuelle"""
        print("\n" + "="*70)
        print("CONFIGURATION RAG")
        print("="*70)
        
        print("\n📁 Chemins:")
        print(f"  • Répertoire RAG: {cls.RAG_DIR}")
        print(f"  • PDF par défaut: {cls.DEFAULT_PDF_PATH.name}")
        print(f"  • Qdrant: {cls.QDRANT_DB_DIR}")
        
        print("\n📏 Chunking:")
        print(f"  • Taille: {cls.CHAR_CHUNK_SIZE} caractères")
        print(f"  • Overlap: {cls.CHAR_CHUNK_OVERLAP} caractères")
        print(f"  • Séparateurs: {len(cls.CHUNK_SEPARATORS)}")
        
        print("\n🧠 Embeddings:")
        print(f"  • Modèle: {cls.EMBEDDING_MODEL_NAME}")
        print(f"  • Device: {cls.EMBEDDING_DEVICE}")
        print(f"  • Dimension: {cls.EMBEDDING_DIMENSION}")
        
        print("\n🔍 Recherche:")
        print(f"  • Top K: {cls.TOP_K_RETRIEVAL}")
        print(f"  • Score min: {cls.MIN_SIMILARITY_SCORE}")
        
        print("\n💾 Qdrant:")
        print(f"  • Collection: {cls.QDRANT_COLLECTION_NAME}")
        print(f"  • Métrique: {cls.QDRANT_DISTANCE_METRIC}")
        
        print("\n" + "="*70 + "\n")

class QuickConfig(RAGConfig):
    """Configuration pour traitement rapide (chunks plus grands)"""
    CHAR_CHUNK_SIZE = 1500
    CHAR_CHUNK_OVERLAP = 250
    TOP_K_RETRIEVAL = 3


class PreciseConfig(RAGConfig):
    """Configuration pour recherche précise (chunks plus petits)"""
    CHAR_CHUNK_SIZE = 500
    CHAR_CHUNK_OVERLAP = 100
    TOP_K_RETRIEVAL = 10
    MIN_SIMILARITY_SCORE = 0.7


class ProductionConfig(RAGConfig):
    """Configuration pour environnement de production"""
    VERBOSE = False
    SHOW_PROGRESS = False
    TOP_K_RETRIEVAL = 5
    MIN_SIMILARITY_SCORE = 0.6


if __name__ == "__main__":
    print("\n🔧 Test de la configuration RAG\n")
    
    RAGConfig.validate_config()
    
    RAGConfig.print_config()
    
    RAGConfig.ensure_directories()
    print("Répertoires créés/vérifiés")
    
    print("\n📋 Configurations disponibles:")
    print("  • RAGConfig (défaut)")
    print("  • QuickConfig (rapide)")
    print("  • PreciseConfig (précis)")
    print("  • ProductionConfig (production)")
