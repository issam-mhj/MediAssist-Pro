# Module RAG - Prétraitement et Chunking de Documents

Ce module fournit des outils complets pour le prétraitement et le chunking de documents PDF dans le cadre du système RAG (Retrieval-Augmented Generation) de MediAssist-Pro.

## 📋 Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Modules](#modules)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Exemples](#exemples)
- [Configuration](#configuration)

## 🎯 Vue d'ensemble

Le système de prétraitement et chunking permet de :

1. **Extraire** le texte de documents PDF techniques (manuels de maintenance)
2. **Nettoyer** et normaliser le texte extrait
3. **Découper** le contenu en chunks optimisés pour la recherche sémantique
4. **Enrichir** avec des métadonnées pour un meilleur tracking

## 🏗️ Architecture

```
backend/app/rag/
├── document_processor.py   # Extraction et prétraitement PDF
├── chunking.py             # Stratégies de chunking
├── embeddings.py           # Génération d'embeddings
├── vector_store.py         # Stockage vectoriel (ChromaDB)
├── retriever.py            # Recherche et récupération
├── generator.py            # Génération de réponses
└── example_usage.py        # Exemples d'utilisation
```

## 📦 Modules

### 1. `document_processor.py`

**Responsabilité** : Extraction et prétraitement du contenu PDF

#### Classe `DocumentProcessor`

```python
class DocumentProcessor:
    def __init__(self, pdf_path: Optional[str] = None)
    def load_pdf(self) -> List[Document]
    def preprocess_text(self, text: str) -> str
    def extract_metadata(self) -> Dict[str, any]
    def get_page_text(self, page_number: int) -> str
```

**Fonctionnalités** :
- ✅ Extraction de texte page par page
- ✅ Nettoyage des artefacts PDF (sauts de ligne, espaces)
- ✅ Normalisation des caractères spéciaux
- ✅ Extraction de métadonnées (auteur, pages, taille)
- ✅ Support des documents multi-pages

**Exemple** :
```python
processor = DocumentProcessor()
documents = processor.load_pdf()
# Retourne: List[Document] avec texte et métadonnées
```

### 2. `chunking.py`

**Responsabilité** : Découpage intelligent du contenu

#### Classe `DocumentChunker`

```python
class DocumentChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200)
    def create_semantic_chunks(documents: List[Document]) -> List[Document]
    def create_character_chunks(documents: List[Document]) -> List[Document]
    def create_hybrid_chunks(documents: List[Document]) -> List[Document]
    def get_chunk_stats(chunks: List[Document]) -> dict
```

#### Stratégies de chunking

##### 🔤 Chunking par caractères (Character-based)
- Découpe fixe basée sur la taille
- Préserve les séparateurs naturels (paragraphes, phrases)
- Chevauchement configurable entre chunks
- **Avantages** : Rapide, prévisible, contrôlable
- **Cas d'usage** : Documents bien structurés

##### 🧠 Chunking sémantique (Semantic)
- Découpe basée sur la similarité sémantique
- Utilise des embeddings pour détecter les ruptures de contexte
- Chunks de taille variable mais cohérents sémantiquement
- **Avantages** : Meilleure cohérence contextuelle
- **Cas d'usage** : Documents complexes, texte narratif

##### 🔄 Chunking hybride
- Combine les deux approches
- Chunking sémantique initial + subdivision si nécessaire
- Équilibre entre cohérence et taille

## 🚀 Installation

### Dépendances requises

```bash
pip install pypdf langchain langchain-core langchain-community \
            langchain-experimental langchain-text-splitters \
            sentence-transformers
```

Ou via requirements.txt :
```bash
cd backend
pip install -r requirements.txt
```

## 💻 Utilisation

### Utilisation de base

```python
from document_processor import DocumentProcessor
from chunking import DocumentChunker

# 1. Charger et prétraiter le PDF
processor = DocumentProcessor()
documents = processor.load_pdf()

# 2. Créer des chunks
chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
chunks = chunker.create_character_chunks(documents)

print(f"✅ {len(chunks)} chunks créés")
```

### Extraction d'une page spécifique

```python
processor = DocumentProcessor()

# Extraire la page 5
page_text = processor.get_page_text(5)
print(page_text)
```

### Chunking sémantique

```python
chunker = DocumentChunker()

# Chunking sémantique avec seuil percentile
semantic_chunks = chunker.create_semantic_chunks(
    documents,
    breakpoint_threshold_type="percentile"
)
```

### Statistiques sur les chunks

```python
stats = chunker.get_chunk_stats(chunks)
print(f"Nombre de chunks: {stats['total_chunks']}")
print(f"Taille moyenne: {stats['avg_length']}")
print(f"Min/Max: {stats['min_length']}/{stats['max_length']}")
```

## 📊 Exemples

### Script de démonstration complet

```bash
cd backend/app/rag
python example_usage.py
```

Ce script démontre :
1. Chargement et extraction du PDF
2. Affichage des métadonnées
3. Chunking par caractères avec statistiques
4. Chunking sémantique (sur échantillon)
5. Sauvegarde des résultats

### Test unitaires

```bash
# Test du document processor
python document_processor.py

# Test du chunker
python chunking.py
```

## ⚙️ Configuration

### Paramètres de chunking

```python
chunker = DocumentChunker(
    chunk_size=1000,      # Taille maximale d'un chunk (caractères)
    chunk_overlap=200     # Chevauchement entre chunks (caractères)
)
```

**Recommandations** :
- **chunk_size** : 500-1500 caractères (selon le contexte)
- **chunk_overlap** : 15-20% de chunk_size
- Plus le chunk_size est petit, plus la recherche est précise mais fragmentée
- Plus l'overlap est grand, meilleure est la continuité mais redondance accrue

### Séparateurs personnalisés

```python
custom_separators = [
    "\n\n",     # Paragraphes
    "\n",       # Lignes
    ". ",       # Phrases
    ", ",       # Clauses
    " "         # Mots
]

chunks = chunker.create_character_chunks(
    documents,
    separators=custom_separators
)
```

## 📈 Performances

### Document de test
- **Fichier** : `maintenance-des-appareils-de-laboratoire.pdf`
- **Pages** : 57 (55 pages extraites avec contenu)
- **Taille** : ~1.1 MB
- **Caractères totaux** : ~185,000

### Résultats

#### Chunking par caractères
- **Chunks créés** : 241
- **Taille moyenne** : 868 caractères
- **Temps** : < 1 seconde

#### Chunking sémantique
- **Chunks créés** : Variable selon le contenu
- **Taille moyenne** : ~1000 caractères
- **Temps** : 2-5 secondes (après téléchargement du modèle)

## 🔍 Structure des données

### Document LangChain

```python
Document(
    page_content="Texte du chunk...",
    metadata={
        "source": "maintenance-des-appareils-de-laboratoire.pdf",
        "page": 15,
        "total_pages": 57,
        "file_path": "/path/to/file.pdf",
        "chunk_id": 42,
        "chunk_type": "character",
        "char_count": 950,
        "chunk_size": 1000,
        "chunk_overlap": 200
    }
)
```

## 🛠️ Fonctions utilitaires

### `load_documents(pdf_path)`
Fonction standalone pour charger rapidement un PDF

```python
from document_processor import load_documents

docs = load_documents("path/to/file.pdf")
```

## 📝 Notes importantes

### Prétraitement du texte

Le prétraitement effectue :
- ✅ Suppression des espaces multiples
- ✅ Correction des mots coupés (hyphenation)
- ✅ Normalisation des apostrophes et guillemets
- ✅ Suppression des lignes vides multiples
- ✅ Nettoyage des caractères de contrôle

### Métadonnées enrichies

Chaque chunk contient :
- Source du document
- Numéro de page d'origine
- ID unique du chunk
- Type de chunking utilisé
- Taille en caractères
- Paramètres de chunking

## 🚧 Améliorations futures

- [ ] Support d'autres formats (DOCX, TXT, HTML)
- [ ] Détection automatique de la structure (titres, sections)
- [ ] Chunking contextuel (par section/chapitre)
- [ ] Filtrage de contenu (tables des matières, index)
- [ ] Cache des embeddings pour performance
- [ ] Support multi-langue amélioré

## 🐛 Dépannage

### Erreur : Module 'pypdf' not found
```bash
pip install pypdf
```

### Erreur : Module 'langchain' not found
```bash
pip install langchain langchain-core langchain-community
```

### Chunking sémantique lent
- Le premier lancement télécharge le modèle d'embeddings (~100MB)
- Les exécutions suivantes utilisent le cache local
- Utiliser `chunk_size` plus grand pour réduire le nombre de chunks

### PDF corrompu ou non lisible
- Vérifier que le fichier PDF n'est pas chiffré
- Essayer de le réexporter avec un autre outil PDF
- Vérifier les permissions de lecture du fichier

## 📚 Ressources

- [LangChain Documentation](https://python.langchain.com/)
- [pypdf Documentation](https://pypdf.readthedocs.io/)
- [Sentence Transformers](https://www.sbert.net/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

## ✅ Tests validés

- ✅ Extraction de 57 pages PDF
- ✅ Prétraitement de 185k caractères
- ✅ Génération de 241 chunks (caractères)
- ✅ Génération de 20 chunks (sémantique sur échantillon)
- ✅ Métadonnées complètes et cohérentes
- ✅ Statistiques précises

---

**Auteur** : MediAssist-Pro Team  
**Date** : Février 2026  
**Version** : 1.0
