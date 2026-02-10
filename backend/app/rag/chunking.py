from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Optional
from langchain_core.documents import Document

try:
    from langchain_experimental.text_splitter import SemanticChunker
    from langchain_community.embeddings import HuggingFaceEmbeddings
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False

from app.rag.document_processor import load_documents


class DocumentChunker:
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def create_semantic_chunks(
        self,
        documents: List[Document],
        breakpoint_threshold_type: str = "percentile"
    ) -> List[Document]:
        print("\nCréation de chunks sémantiques...")

        if not SEMANTIC_AVAILABLE:
            return self.create_character_chunks(documents)

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        text_splitter = SemanticChunker(
            embeddings=embeddings,
            breakpoint_threshold_type=breakpoint_threshold_type
        )
        
        chunks = text_splitter.split_documents(documents)
        
        for i, chunk in enumerate(chunks, start=1):
            chunk.metadata["chunk_id"] = i
            chunk.metadata["chunk_type"] = "semantic"
            chunk.metadata["char_count"] = len(chunk.page_content)
        
        print(f"✅ {len(chunks)} chunks sémantiques créés")
        
        return chunks
    
    def create_character_chunks(
        self,
        documents: List[Document],
        separators: Optional[List[str]] = None
    ) -> List[Document]:
        print("\n📏 Création de chunks par caractères...")
        
        if separators is None:
            separators = [
                "\n\n", 
                "\n",    
                ". ",    
                ", ",    
                " ",     
                ""       
            ]
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False
        )
        
        chunks = text_splitter.split_documents(documents)
        
        for i, chunk in enumerate(chunks, start=1):
            chunk.metadata["chunk_id"] = i
            chunk.metadata["chunk_type"] = "character"
            chunk.metadata["char_count"] = len(chunk.page_content)
            chunk.metadata["chunk_size"] = self.chunk_size
            chunk.metadata["chunk_overlap"] = self.chunk_overlap
        
        print(f" {len(chunks)} chunks créés")
        print(f"   Taille moyenne: {sum(len(c.page_content) for c in chunks) / len(chunks):.0f} caractères")
        
        return chunks
    
    def create_hybrid_chunks(
        self,
        documents: List[Document],
        use_semantic: bool = True
    ) -> List[Document]:
        print("\n🔄 Création de chunks hybrides...")
        
        if use_semantic:
            chunks = self.create_semantic_chunks(documents)
            
            final_chunks = []
            for chunk in chunks:
                if len(chunk.page_content) > self.chunk_size * 1.5:
                    sub_chunks = self.create_character_chunks([chunk])
                    final_chunks.extend(sub_chunks)
                else:
                    final_chunks.append(chunk)
            
            print(f"✅ {len(final_chunks)} chunks hybrides créés")
            return final_chunks
        else:
            return self.create_character_chunks(documents)
    
    def get_chunk_stats(self, chunks: List[Document]) -> dict:
        if not chunks:
            return {}
        
        chunk_lengths = [len(chunk.page_content) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "min_length": min(chunk_lengths),
            "max_length": max(chunk_lengths),
            "avg_length": sum(chunk_lengths) / len(chunk_lengths),
            "total_chars": sum(chunk_lengths),
            "chunk_type": chunks[0].metadata.get("chunk_type", "unknown")
        }


if __name__ == "__main__":
    print("\n" + "="*50)
    print("TEST DU DOCUMENT CHUNKER")
    print("="*50 + "\n")
    
    print("📥 Chargement des documents...")
    documents = load_documents()
    
    if not documents:
        print(" Aucun document chargé")
        exit(1)
    
    print(f"✅ {len(documents)} documents chargés\n")
    
    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
    
    print("\n" + "="*50)
    print("TEST: Chunking par caractères")
    print("="*50)
    char_chunks = chunker.create_character_chunks(documents)
    char_stats = chunker.get_chunk_stats(char_chunks)
    
    print("\nStatistiques des chunks par caractères:")
    for key, value in char_stats.items():
        print(f"  {key}: {value}")
    
    if char_chunks:
        print("\n📄 Aperçu du premier chunk:")
        print(f"  ID: {char_chunks[0].metadata.get('chunk_id')}")
        print(f"  Page source: {char_chunks[0].metadata.get('page')}")
        print(f"  Longueur: {len(char_chunks[0].page_content)} caractères")
        print(f"\n  Contenu (150 premiers caractères):\n")
        print(f"  {char_chunks[0].page_content[:150]}...")
    
    print("\n" + "="*50)
    print("Tests terminés avec succès")
    print("="*50 + "\n")
