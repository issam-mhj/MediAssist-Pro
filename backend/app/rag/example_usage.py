"""
Script d'exemple pour le prétraitement et le chunking de documents PDF.
Démontre l'utilisation du DocumentProcessor et DocumentChunker.
"""

from document_processor import DocumentProcessor, load_documents
from chunking import DocumentChunker
import json


def main():
    print("\n" + "="*70)
    print("DÉMONSTRATION COMPLÈTE : PRÉTRAITEMENT ET CHUNKING")
    print("="*70 + "\n")
    
    # ========================================================================
    # ÉTAPE 1: Chargement et extraction du PDF
    # ========================================================================
    print("📚 ÉTAPE 1: Chargement du document PDF")
    print("-" * 70)
    
    processor = DocumentProcessor()
    
    # Afficher les métadonnées du document
    print("\n📋 Métadonnées du document:")
    metadata = processor.extract_metadata()
    for key, value in metadata.items():
        print(f"  • {key}: {value}")
    
    # Charger tous les documents
    print("\n📥 Extraction du contenu...")
    documents = processor.load_pdf()
    
    print(f"\n✅ {len(documents)} pages extraites")
    print(f"   Total de caractères: {sum(len(doc.page_content) for doc in documents):,}")
    
    # Exemple d'extraction d'une page spécifique
    print("\n📄 Exemple: Extraction de la page 1")
    page_1_text = processor.get_page_text(1)
    print(f"   Longueur: {len(page_1_text)} caractères")
    print(f"   Aperçu: {page_1_text[:150]}...")
    
    # ========================================================================
    # ÉTAPE 2: Chunking par caractères (méthode fixe)
    # ========================================================================
    print("\n\n📏 ÉTAPE 2: Chunking par caractères")
    print("-" * 70)
    
    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
    char_chunks = chunker.create_character_chunks(documents)
    
    # Statistiques
    stats = chunker.get_chunk_stats(char_chunks)
    print("\n📊 Statistiques:")
    print(f"   • Nombre de chunks: {stats['total_chunks']}")
    print(f"   • Taille minimale: {stats['min_length']} caractères")
    print(f"   • Taille maximale: {stats['max_length']} caractères")
    print(f"   • Taille moyenne: {stats['avg_length']:.0f} caractères")
    print(f"   • Total: {stats['total_chars']:,} caractères")
    
    # Aperçu d'un chunk
    print("\n📄 Aperçu du chunk #10:")
    if len(char_chunks) >= 10:
        chunk = char_chunks[9]
        print(f"   • Page source: {chunk.metadata['page']}")
        print(f"   • Longueur: {len(chunk.page_content)} caractères")
        print(f"   • Contenu: {chunk.page_content[:200]}...")
    
    # ========================================================================
    # ÉTAPE 3: Chunking sémantique
    # ========================================================================
    print("\n\n🧠 ÉTAPE 3: Chunking sémantique")
    print("-" * 70)
    print("⚠️  Note: Le chunking sémantique nécessite le téléchargement")
    print("   d'un modèle d'embeddings (peut prendre quelques minutes)")
    print("   au premier lancement.\n")
    
    # Utilisation d'un sous-ensemble pour la démo
    sample_docs = documents[:5]  # Premières 5 pages seulement
    print(f"📌 Utilisation de {len(sample_docs)} pages pour la démo")
    
    try:
        semantic_chunks = chunker.create_semantic_chunks(sample_docs)
        
        # Statistiques
        sem_stats = chunker.get_chunk_stats(semantic_chunks)
        print(f"\n📊 Statistiques sémantiques:")
        print(f"   • Nombre de chunks: {sem_stats['total_chunks']}")
        print(f"   • Taille moyenne: {sem_stats['avg_length']:.0f} caractères")
        print(f"   • Min/Max: {sem_stats['min_length']} / {sem_stats['max_length']}")
        
        # Aperçu
        print("\n📄 Aperçu du premier chunk sémantique:")
        if semantic_chunks:
            chunk = semantic_chunks[0]
            print(f"   • Page source: {chunk.metadata['page']}")
            print(f"   • Longueur: {len(chunk.page_content)} caractères")
            print(f"   • Contenu: {chunk.page_content[:200]}...")
    
    except Exception as e:
        print(f"\n⚠️  Chunking sémantique ignoré: {str(e)}")
        print("   (Vous pouvez installer les dépendances si nécessaire)")
    
    # ========================================================================
    # ÉTAPE 4: Sauvegarde des chunks (optionnel)
    # ========================================================================
    print("\n\n💾 ÉTAPE 4: Exemple de sauvegarde")
    print("-" * 70)
    
    # Préparer les données pour la sauvegarde
    chunks_data = []
    for i, chunk in enumerate(char_chunks[:5], 1):  # Premiers 5 chunks
        chunks_data.append({
            "chunk_id": chunk.metadata.get("chunk_id"),
            "page": chunk.metadata.get("page"),
            "content": chunk.page_content[:100] + "...",  # Tronqué pour la démo
            "char_count": len(chunk.page_content)
        })
    
    print("\n📦 Exemple de structure des chunks (5 premiers):")
    print(json.dumps(chunks_data, indent=2, ensure_ascii=False)[:500] + "...")
    
    # ========================================================================
    # RÉSUMÉ FINAL
    # ========================================================================
    print("\n\n" + "="*70)
    print("✅ RÉSUMÉ")
    print("="*70)
    print(f"📄 Document traité: {metadata.get('file_name', 'N/A')}")
    print(f"📊 Pages extraites: {len(documents)}")
    print(f"📏 Chunks créés (caractères): {len(char_chunks)}")
    print(f"💾 Taille totale: {sum(len(c.page_content) for c in char_chunks):,} caractères")
    print("\n🎉 Prétraitement et chunking terminés avec succès!")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Opération interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
