# MediAssist-Pro - Guide des Tâches

## 📋 PHASE 1 : CONFIGURATION INITIALE DU PROJET

### Tâche 1.1 : Structure des dossiers
**Objectif** : Créer l'architecture complète du projet

Créer la structure suivante :
```
MediAssist-Pro/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   │   └── query.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   │   └── query.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       └── rag.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   └── exceptions.py
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── document_processor.py
│   │   │   ├── chunking.py
│   │   │   ├── embeddings.py
│   │   │   ├── vector_store.py
│   │   │   ├── retriever.py
│   │   │   └── generator.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_auth.py
│   │       ├── test_rag.py
│   │       └── test_users.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── documents/
│   └── manuals/
├── docker-compose.yml
├── .gitignore
└── README.md
```

**📝 Documentation à produire** :
- Créer un fichier `docs/ARCHITECTURE.md` expliquant le rôle de chaque dossier
- Diagramme de l'architecture globale (dessin simple ou texte)

---

### Tâche 1.2 : Fichier .gitignore
**Objectif** : Éviter de committer des fichiers sensibles

Créer `.gitignore` avec :
```
__pycache__/
*.py[cod]
*$py.class
.env
*.db
*.sqlite
.venv/
venv/
env/
.idea/
.vscode/
*.log
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
chroma_db/
faiss_index/
```

**📝 Documentation à produire** :
- Aucune documentation spécifique

---

### Tâche 1.3 : Fichier requirements.txt
**Objectif** : Lister toutes les dépendances Python

Créer `backend/requirements.txt` :
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
langchain==0.1.0
langchain-community==0.0.13
langchain-openai==0.0.5
chromadb==0.4.22
sentence-transformers==2.3.1
pypdf==3.17.4
pytest==7.4.3
pytest-asyncio==0.23.3
httpx==0.26.0
python-dotenv==1.0.0
```

**📝 Documentation à produire** :
- Dans `docs/DEPENDENCIES.md` : expliquer le rôle de chaque bibliothèque principale

---

### Tâche 1.4 : Variables d'environnement
**Objectif** : Configurer les paramètres sensibles

Créer `backend/.env.example` :
```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/mediassist_db

# JWT
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI or LLM API
OPENAI_API_KEY=your-openai-api-key-here
# or for local models
OLLAMA_BASE_URL=http://localhost:11434

# Embeddings
EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Vector Store
VECTOR_STORE_TYPE=chromadb
CHROMA_PERSIST_DIRECTORY=./chroma_db

# App
APP_NAME=MediAssist-Pro
DEBUG=True
```

**📝 Documentation à produire** :
- Dans `docs/CONFIGURATION.md` : expliquer chaque variable et comment les obtenir

---

## 📋 PHASE 2 : BASE DE DONNÉES ET MODÈLES

### Tâche 2.1 : Configuration de la base de données
**Objectif** : Connecter l'application à PostgreSQL

Créer `backend/app/config.py` :
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OPENAI_API_KEY: Optional[str] = None
    EMBEDDINGS_MODEL: str
    VECTOR_STORE_TYPE: str = "chromadb"
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    APP_NAME: str = "MediAssist-Pro"
    DEBUG: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

Créer `backend/app/database.py` :
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**📝 Documentation à produire** :
- Dans `docs/DATABASE.md` : expliquer la connexion, les sessions, et comment utiliser `get_db()`

---

### Tâche 2.2 : Modèle User
**Objectif** : Créer la table users

Créer `backend/app/models/user.py` :
```python
from sqlalchemy import Column, Integer, String, Enum
from app.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TECHNICIAN = "technician"
    USER = "user"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
```

Créer `backend/app/models/__init__.py` :
```python
from app.models.user import User
from app.models.query import Query
```

**📝 Documentation à produire** :
- Dans `docs/DATABASE.md` : ajouter le schéma de la table users avec explication des champs

---

### Tâche 2.3 : Modèle Query
**Objectif** : Créer la table pour historique des requêtes

Créer `backend/app/models/query.py` :
```python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**📝 Documentation à produire** :
- Dans `docs/DATABASE.md` : ajouter le schéma de la table queries avec explication des champs

---

### Tâche 2.4 : Schémas Pydantic pour User
**Objectif** : Validation des données entrantes/sortantes

Créer `backend/app/schemas/user.py` :
```python
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    role: UserRole

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
```

**📝 Documentation à produire** :
- Dans `docs/API_SCHEMAS.md` : expliquer chaque schéma et son usage (création, login, réponse)

---

### Tâche 2.5 : Schémas Pydantic pour Query
**Objectif** : Validation des requêtes RAG

Créer `backend/app/schemas/query.py` :
```python
from pydantic import BaseModel
from datetime import datetime

class QueryCreate(BaseModel):
    query: str

class QueryResponse(BaseModel):
    id: int
    query: str
    response: str
    created_at: datetime

    class Config:
        from_attributes = True

class RAGRequest(BaseModel):
    question: str
    top_k: int = 5

class RAGResponse(BaseModel):
    answer: str
    sources: list[str]
    query_id: int
```

**📝 Documentation à produire** :
- Dans `docs/API_SCHEMAS.md` : ajouter les schémas RAG avec exemples JSON

---

## 📋 PHASE 3 : AUTHENTIFICATION ET SÉCURITÉ

### Tâche 3.1 : Module de sécurité
**Objectif** : Implémenter JWT et hash de mots de passe

Créer `backend/app/core/security.py` :
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

**📝 Documentation à produire** :
- Dans `docs/SECURITY.md` : expliquer JWT, bcrypt, et le flux d'authentification

---

### Tâche 3.2 : Gestion des exceptions
**Objectif** : Centraliser les erreurs HTTP

Créer `backend/app/core/exceptions.py` :
```python
from fastapi import HTTPException, status

class CredentialsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

class UserNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

class UserAlreadyExistsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

class DocumentProcessingException(HTTPException):
    def __init__(self, detail: str = "Error processing document"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
```

**📝 Documentation à produire** :
- Dans `docs/ERROR_HANDLING.md` : lister toutes les exceptions et leurs codes HTTP

---

### Tâche 3.3 : Dépendances d'authentification
**Objectif** : Créer les dépendances pour protéger les routes

Créer `backend/app/api/deps.py` :
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.core.exceptions import CredentialsException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    payload = decode_token(token)
    if payload is None:
        raise CredentialsException()
    
    username: str = payload.get("sub")
    if username is None:
        raise CredentialsException()
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise CredentialsException()
    
    return user

def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
```

**📝 Documentation à produire** :
- Dans `docs/AUTHENTICATION.md` : expliquer le flux OAuth2, comment protéger une route

---

### Tâche 3.4 : Routes d'authentification
**Objectif** : Créer login et register

Créer `backend/app/api/routes/auth.py` :
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.exceptions import UserAlreadyExistsException
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise UserAlreadyExistsException()
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
```

**📝 Documentation à produire** :
- Dans `docs/API_ENDPOINTS.md` : documenter POST /auth/register et POST /auth/login avec exemples curl

---

## 📋 PHASE 4 : PIPELINE RAG - PRÉTRAITEMENT

### Tâche 4.1 : Processeur de documents
**Objectif** : Charger les PDF

Créer `backend/app/rag/document_processor.py` :
```python
from pathlib import Path
from typing import List
from pypdf import PdfReader
from langchain.docstore.document import Document

class DocumentProcessor:
    """Charge et extrait le texte des documents PDF."""
    
    def __init__(self, documents_dir: str = "./documents/manuals"):
        self.documents_dir = Path(documents_dir)
    
    def load_pdf(self, file_path: str) -> List[Document]:
        """Charge un fichier PDF et retourne une liste de Documents."""
        reader = PdfReader(file_path)
        documents = []
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            metadata = {
                "source": str(file_path),
                "page": page_num + 1,
                "total_pages": len(reader.pages)
            }
            documents.append(Document(page_content=text, metadata=metadata))
        
        return documents
    
    def load_all_pdfs(self) -> List[Document]:
        """Charge tous les PDFs du répertoire."""
        all_documents = []
        pdf_files = list(self.documents_dir.glob("*.pdf"))
        
        for pdf_file in pdf_files:
            docs = self.load_pdf(str(pdf_file))
            all_documents.extend(docs)
        
        return all_documents
```

**📝 Documentation à produire** :
- Dans `docs/RAG_PIPELINE.md` : expliquer le chargement des PDF et la structure Document

---

### Tâche 4.2 : Chunking des documents
**Objectif** : Découper intelligemment les documents

Créer `backend/app/rag/chunking.py` :
```python
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

class DocumentChunker:
    """Découpe les documents en chunks avec overlap."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Découpe une liste de documents en chunks."""
        chunks = self.text_splitter.split_documents(documents)
        
        # Enrichir les métadonnées avec l'ID du chunk
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = i
            chunk.metadata["chunk_size"] = len(chunk.page_content)
        
        return chunks
```

**📝 Documentation à produire** :
- Dans `docs/RAG_PIPELINE.md` : expliquer la stratégie de chunking, chunk_size, overlap et pourquoi

---

### Tâche 4.3 : Génération des embeddings
**Objectif** : Transformer les chunks en vecteurs

Créer `backend/app/rag/embeddings.py` :
```python
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import settings

class EmbeddingsManager:
    """Gère la génération des embeddings."""
    
    def __init__(self):
        self.embeddings_model = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDINGS_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    
    def get_embeddings(self):
        """Retourne le modèle d'embeddings."""
        return self.embeddings_model
```

**📝 Documentation à produire** :
- Dans `docs/RAG_PIPELINE.md` : expliquer ce qu'est un embedding, le modèle choisi et pourquoi

---

## 📋 PHASE 5 : VECTOR STORE ET RETRIEVAL

### Tâche 5.1 : Vector Store (ChromaDB)
**Objectif** : Stocker et persister les embeddings

Créer `backend/app/rag/vector_store.py` :
```python
from typing import List
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from app.rag.embeddings import EmbeddingsManager
from app.config import settings

class VectorStoreManager:
    """Gère le vector store ChromaDB."""
    
    def __init__(self):
        self.embeddings_manager = EmbeddingsManager()
        self.embeddings = self.embeddings_manager.get_embeddings()
        self.persist_directory = settings.CHROMA_PERSIST_DIRECTORY
    
    def create_vector_store(self, documents: List[Document]) -> Chroma:
        """Crée un nouveau vector store à partir de documents."""
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        return vector_store
    
    def load_vector_store(self) -> Chroma:
        """Charge un vector store existant."""
        vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        return vector_store
    
    def add_documents(self, documents: List[Document]):
        """Ajoute des documents à un vector store existant."""
        vector_store = self.load_vector_store()
        vector_store.add_documents(documents)
```

**📝 Documentation à produire** :
- Dans `docs/VECTOR_STORE.md` : expliquer ChromaDB, la persistance, comment ajouter des docs

---

### Tâche 5.2 : Retriever avancé
**Objectif** : Rechercher les chunks pertinents

Créer `backend/app/rag/retriever.py` :
```python
from typing import List
from langchain.docstore.document import Document
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from app.rag.vector_store import VectorStoreManager

class RetrieverManager:
    """Gère la récupération des documents pertinents."""
    
    def __init__(self, top_k: int = 5):
        self.vector_store_manager = VectorStoreManager()
        self.vector_store = self.vector_store_manager.load_vector_store()
        self.top_k = top_k
    
    def search(self, query: str) -> List[Document]:
        """Recherche les documents les plus pertinents."""
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.top_k}
        )
        documents = retriever.get_relevant_documents(query)
        return documents
    
    def search_with_score(self, query: str) -> List[tuple]:
        """Recherche avec scores de similarité."""
        results = self.vector_store.similarity_search_with_score(query, k=self.top_k)
        return results
```

**📝 Documentation à produire** :
- Dans `docs/RETRIEVAL.md` : expliquer la recherche par similarité, le paramètre top_k

---

## 📋 PHASE 6 : GÉNÉRATION DE RÉPONSE

### Tâche 6.1 : Générateur de réponses
**Objectif** : Utiliser un LLM pour générer des réponses

Créer `backend/app/rag/generator.py` :
```python
from typing import List
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from app.rag.retriever import RetrieverManager
from app.config import settings

class ResponseGenerator:
    """Génère des réponses en utilisant RAG."""
    
    def __init__(self):
        self.retriever_manager = RetrieverManager()
        
        # Prompt template
        self.prompt_template = """Tu es un assistant technique spécialisé dans les équipements biomédicaux de laboratoire.
        
Utilise UNIQUEMENT les informations du contexte suivant pour répondre à la question.
Si la réponse n'est pas dans le contexte, dis "Je ne trouve pas cette information dans les manuels techniques disponibles."

Contexte:
{context}

Question: {question}

Instructions:
- Réponds de manière précise et actionnable
- Cite la source (nom du fichier et page) si possible
- Utilise un langage technique mais compréhensible
- Structure ta réponse avec des points si nécessaire

Réponse:"""

        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )
    
    def generate_answer(self, question: str, top_k: int = 5) -> dict:
        """Génère une réponse à partir de la question."""
        # Récupérer les documents pertinents
        self.retriever_manager.top_k = top_k
        documents = self.retriever_manager.search(question)
        
        # Construire le contexte
        context = "\n\n".join([
            f"[Source: {doc.metadata.get('source', 'Unknown')} - Page {doc.metadata.get('page', 'N/A')}]\n{doc.page_content}"
            for doc in documents
        ])
        
        # Générer la réponse (vous pouvez utiliser OpenAI ou Ollama)
        # Pour l'exemple avec Ollama:
        llm = Ollama(model="llama2", base_url=settings.OLLAMA_BASE_URL)
        
        full_prompt = self.prompt.format(context=context, question=question)
        answer = llm(full_prompt)
        
        # Extraire les sources
        sources = [
            f"{doc.metadata.get('source', 'Unknown')} (Page {doc.metadata.get('page', 'N/A')})"
            for doc in documents
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": len(documents)
        }
```

**📝 Documentation à produire** :
- Dans `docs/GENERATION.md` : expliquer le prompt engineering, le choix du LLM, la structure de réponse

---

## 📋 PHASE 7 : ROUTES API RAG

### Tâche 7.1 : Route pour indexer des documents
**Objectif** : API pour charger et indexer des PDFs

Créer `backend/app/api/routes/rag.py` :
```python
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.query import Query
from app.schemas.query import RAGRequest, RAGResponse
from app.rag.document_processor import DocumentProcessor
from app.rag.chunking import DocumentChunker
from app.rag.vector_store import VectorStoreManager
from app.rag.generator import ResponseGenerator
import shutil
from pathlib import Path

router = APIRouter(prefix="/rag", tags=["RAG"])

@router.post("/index")
async def index_documents(
    current_user: User = Depends(get_current_user)
):
    """Indexe tous les documents PDF du dossier documents/manuals."""
    try:
        # Charger les documents
        processor = DocumentProcessor()
        documents = processor.load_all_pdfs()
        
        if not documents:
            raise HTTPException(status_code=404, detail="No PDF documents found")
        
        # Chunker les documents
        chunker = DocumentChunker()
        chunks = chunker.chunk_documents(documents)
        
        # Créer le vector store
        vector_store_manager = VectorStoreManager()
        vector_store_manager.create_vector_store(chunks)
        
        return {
            "message": "Documents indexed successfully",
            "total_documents": len(documents),
            "total_chunks": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error indexing documents: {str(e)}")

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload un nouveau document PDF."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        documents_dir = Path("./documents/manuals")
        documents_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = documents_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"message": f"File {file.filename} uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.post("/query", response_model=RAGResponse)
async def query_rag(
    request: RAGRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Interroge le système RAG."""
    try:
        # Générer la réponse
        generator = ResponseGenerator()
        result = generator.generate_answer(request.question, top_k=request.top_k)
        
        # Sauvegarder dans la base de données
        new_query = Query(
            user_id=current_user.id,
            query=request.question,
            response=result["answer"]
        )
        db.add(new_query)
        db.commit()
        db.refresh(new_query)
        
        return RAGResponse(
            answer=result["answer"],
            sources=result["sources"],
            query_id=new_query.id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.get("/history")
async def get_query_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 10
):
    """Récupère l'historique des requêtes de l'utilisateur."""
    queries = db.query(Query).filter(
        Query.user_id == current_user.id
    ).order_by(Query.created_at.desc()).limit(limit).all()
    
    return queries
```

**📝 Documentation à produire** :
- Dans `docs/API_ENDPOINTS.md` : documenter POST /rag/index, POST /rag/upload, POST /rag/query avec exemples

---

## 📋 PHASE 8 : APPLICATION PRINCIPALE

### Tâche 8.1 : Fichier main.py
**Objectif** : Assembler toute l'application FastAPI

Créer `backend/app/main.py` :
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api.routes import auth, rag

# Créer les tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="RAG system for biomedical equipment technical manuals",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(rag.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Welcome to MediAssist-Pro API",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**📝 Documentation à produire** :
- Dans `docs/API_OVERVIEW.md` : vue d'ensemble de l'API, comment démarrer, routes disponibles

---

## 📋 PHASE 9 : DOCKER ET DÉPLOIEMENT

### Tâche 9.1 : Dockerfile pour le backend
**Objectif** : Conteneuriser l'application

Créer `backend/Dockerfile` :
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**📝 Documentation à produire** :
- Dans `docs/DOCKER.md` : expliquer le Dockerfile ligne par ligne

---

### Tâche 9.2 : Docker Compose
**Objectif** : Orchestrer backend + PostgreSQL

Créer `docker-compose.yml` :
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    container_name: mediassist_db
    environment:
      POSTGRES_USER: mediassist_user
      POSTGRES_PASSWORD: mediassist_password
      POSTGRES_DB: mediassist_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mediassist_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: mediassist_backend
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://mediassist_user:mediassist_password@db:5432/mediassist_db
      SECRET_KEY: your-secret-key-change-in-production
      ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 30
      EMBEDDINGS_MODEL: sentence-transformers/all-MiniLM-L6-v2
      VECTOR_STORE_TYPE: chromadb
      CHROMA_PERSIST_DIRECTORY: /app/chroma_db
      OLLAMA_BASE_URL: http://host.docker.internal:11434
    volumes:
      - ./backend:/app
      - ./documents:/app/documents
      - chroma_data:/app/chroma_db
    ports:
      - "8000:8000"

volumes:
  postgres_data:
  chroma_data:
```

**📝 Documentation à produire** :
- Dans `docs/DOCKER.md` : expliquer docker-compose, les volumes, comment démarrer

---

## 📋 PHASE 10 : TESTS

### Tâche 10.1 : Tests d'authentification
**Objectif** : Tester le système d'auth

Créer `backend/app/tests/test_auth.py` :
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user():
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

def test_login_user():
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials():
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
```

**📝 Documentation à produire** :
- Dans `docs/TESTING.md` : expliquer comment exécuter les tests, pytest, coverage

---

### Tâche 10.2 : Tests RAG
**Objectif** : Tester le pipeline RAG

Créer `backend/app/tests/test_rag.py` :
```python
import pytest
from app.rag.document_processor import DocumentProcessor
from app.rag.chunking import DocumentChunker
from app.rag.embeddings import EmbeddingsManager

def test_document_processor():
    processor = DocumentProcessor()
    # Tester avec un PDF de test
    # documents = processor.load_pdf("test.pdf")
    # assert len(documents) > 0

def test_chunking():
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
    # Test chunking logic
    pass

def test_embeddings():
    embeddings_manager = EmbeddingsManager()
    embeddings = embeddings_manager.get_embeddings()
    assert embeddings is not None
```

**📝 Documentation à produire** :
- Dans `docs/TESTING.md` : ajouter les tests RAG et comment les exécuter

---

## 📋 PHASE 11 : README ET DOCUMENTATION FINALE

### Tâche 11.1 : README principal
**Objectif** : Guide complet du projet

Mettre à jour `README.md` :
```markdown
# MediAssist-Pro

Système RAG (Retrieval-Augmented Generation) pour l'assistance technique sur équipements biomédicaux.

## 🚀 Fonctionnalités

- 🔐 Authentification JWT
- 📄 Indexation de manuels techniques (PDF)
- 🤖 Réponses intelligentes via RAG
- 📊 Historique des requêtes
- 🔍 Recherche vectorielle avec ChromaDB
- 🐳 Déploiement avec Docker

## 🛠️ Technologies

- FastAPI
- PostgreSQL
- LangChain
- ChromaDB
- Sentence Transformers
- Docker

## 📦 Installation

### Avec Docker (Recommandé)

1. Cloner le repo
2. Copier `.env.example` vers `.env`
3. Lancer : `docker-compose up -d`
4. Accéder à : http://localhost:8000/docs

### Sans Docker

1. Installer PostgreSQL
2. Créer un environnement virtuel : `python -m venv venv`
3. Activer : `venv\Scripts\activate`
4. Installer : `pip install -r backend/requirements.txt`
5. Configurer `.env`
6. Lancer : `uvicorn app.main:app --reload`

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Endpoints](docs/API_ENDPOINTS.md)
- [RAG Pipeline](docs/RAG_PIPELINE.md)
- [Configuration](docs/CONFIGURATION.md)
- [Tests](docs/TESTING.md)

## 🧪 Tests

```bash
cd backend
pytest
```

## 📖 Utilisation

1. **S'inscrire** : POST `/api/auth/register`
2. **Se connecter** : POST `/api/auth/login`
3. **Uploader un PDF** : POST `/api/rag/upload`
4. **Indexer** : POST `/api/rag/index`
5. **Poser une question** : POST `/api/rag/query`

## 🤝 Contribution

Voir [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 Licence

MIT
```

**📝 Documentation à produire** :
- Le README lui-même est la documentation

---

### Tâche 11.2 : Documentation complète
**Objectif** : Finaliser tous les documents

S'assurer que tous ces fichiers existent dans `docs/` :

1. `ARCHITECTURE.md` - Architecture du système
2. `API_ENDPOINTS.md` - Toutes les routes API
3. `API_SCHEMAS.md` - Schémas Pydantic
4. `AUTHENTICATION.md` - Système d'auth
5. `CONFIGURATION.md` - Variables d'environnement
6. `DATABASE.md` - Schémas de tables
7. `DEPENDENCIES.md` - Bibliothèques utilisées
8. `DOCKER.md` - Docker et déploiement
9. `ERROR_HANDLING.md` - Gestion des erreurs
10. `GENERATION.md` - Génération de réponses
11. `RAG_PIPELINE.md` - Pipeline RAG complet
12. `RETRIEVAL.md` - Système de retrieval
13. `SECURITY.md` - Sécurité JWT/bcrypt
14. `TESTING.md` - Tests unitaires
15. `VECTOR_STORE.md` - ChromaDB

**📝 Documentation à produire** :
- Chaque fichier doit être complet et bien structuré

---

## 📋 PHASE 12 : OPTIMISATIONS ET AMÉLIORATIONS

### Tâche 12.1 : Query Expansion
**Objectif** : Améliorer la recherche en reformulant la requête

Ajouter dans `backend/app/rag/retriever.py` :
```python
def expand_query(self, query: str) -> List[str]:
    """Génère des variantes de la requête."""
    # Implémentation simple : synonymes, reformulations
    expanded_queries = [query]
    # Ajouter logique d'expansion ici
    return expanded_queries
```

**📝 Documentation à produire** :
- Dans `docs/ADVANCED_RAG.md` : expliquer query expansion et son impact

---

### Tâche 12.2 : Reranking
**Objectif** : Réordonner les résultats pour plus de pertinence

Ajouter dans `backend/app/rag/retriever.py` :
```python
from langchain.retrievers.document_compressors import CohereRerank

def rerank_results(self, query: str, documents: List[Document]) -> List[Document]:
    """Réordonne les documents par pertinence."""
    # Implémentation de reranking
    pass
```

**📝 Documentation à produire** :
- Dans `docs/ADVANCED_RAG.md` : expliquer le reranking

---

### Tâche 12.3 : Cache des réponses
**Objectif** : Éviter de recalculer les réponses identiques

Ajouter un système de cache simple :
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_generate_answer(question: str):
    # Logique de génération
    pass
```

**📝 Documentation à produire** :
- Dans `docs/PERFORMANCE.md` : expliquer le cache et ses bénéfices

---

### Tâche 12.4 : Logging
**Objectif** : Tracer toutes les opérations

Créer `backend/app/core/logging.py` :
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("mediassist")
```

**📝 Documentation à produire** :
- Dans `docs/MONITORING.md` : expliquer le système de logging

---

## 📋 CHECKLIST FINALE

### Avant de considérer le projet terminé :

- [ ] Toutes les tables de la base de données sont créées
- [ ] L'authentification JWT fonctionne
- [ ] Les PDFs sont chargés et indexés correctement
- [ ] Le chunking préserve le contexte
- [ ] Le vector store persiste les données
- [ ] La recherche retourne des résultats pertinents
- [ ] Le LLM génère des réponses cohérentes
- [ ] Les sources sont citées dans les réponses
- [ ] L'historique des requêtes est sauvegardé
- [ ] Docker Compose lance tout correctement
- [ ] Les tests passent avec succès
- [ ] Tous les fichiers de documentation sont complets
- [ ] Le README est clair et informatif
- [ ] Les variables d'environnement sont bien configurées
- [ ] La gestion des erreurs est centralisée

---

## 🎯 RÉSUMÉ DES LIVRABLES

### Code
1. Backend FastAPI complet
2. Modèles SQLAlchemy (User, Query)
3. Schémas Pydantic
4. Routes API (Auth, RAG)
5. Pipeline RAG (chunking, embeddings, retrieval, generation)
6. Tests unitaires
7. Dockerfile + Docker Compose

### Documentation
1. README.md principal
2. 15+ fichiers de documentation technique
3. Exemples d'utilisation API
4. Guide de déploiement

### Infrastructure
1. PostgreSQL configuré
2. ChromaDB persisté
3. Docker containerization
4. Variables d'environnement

---

## 💡 CONSEILS POUR LA RÉALISATION

1. **Travailler étape par étape** : Ne passez pas à la phase suivante avant d'avoir terminé la précédente
2. **Tester régulièrement** : Après chaque tâche majeure, testez que tout fonctionne
3. **Commiter souvent** : Faites des commits Git après chaque tâche complétée
4. **Documenter au fur et à mesure** : Ne laissez pas la documentation pour la fin
5. **Demander de l'aide** : Si vous êtes bloqué, cherchez de l'aide sur la documentation officielle

**Bon courage ! 🚀**
