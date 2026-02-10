"""Routes API pour le système RAG MediAssist-Pro."""

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
    current_user: User = Depends(get_current_user),
):
    """Indexe tous les documents PDF dans le vector store Qdrant."""
    try:
        # Charger les documents
        processor = DocumentProcessor()
        documents = processor.load_all_pdfs()

        if not documents:
            raise HTTPException(status_code=404, detail="No PDF documents found")

        # Chunker les documents
        chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
        chunks = chunker.create_character_chunks(documents)

        # Créer le vector store Qdrant
        vector_store_manager = VectorStoreManager()
        vector_store_manager.create_vector_store(chunks)

        return {
            "message": "Documents indexed successfully in Qdrant",
            "total_pages": len(documents),
            "total_chunks": len(chunks),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error indexing documents: {str(e)}"
        )


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload un nouveau document PDF."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Sauvegarder dans le dossier du module RAG (à côté du PDF existant)
        rag_dir = Path(__file__).resolve().parent.parent.parent / "rag"
        rag_dir.mkdir(parents=True, exist_ok=True)

        file_path = rag_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {"message": f"File {file.filename} uploaded successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error uploading file: {str(e)}"
        )


@router.post("/query", response_model=RAGResponse)
async def query_rag(
    request: RAGRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Interroge le système RAG."""
    try:
        generator = ResponseGenerator()
        result = generator.generate_answer(request.question, top_k=request.top_k)

        # Sauvegarder dans la base de données
        new_query = Query(
            user_id=current_user.id,
            query=request.question,
            response=result["answer"],
        )
        db.add(new_query)
        db.commit()
        db.refresh(new_query)

        return RAGResponse(
            answer=result["answer"],
            sources=result["sources"],
            query_id=new_query.id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing query: {str(e)}"
        )


@router.get("/history")
async def get_query_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 10,
):
    """Récupère l'historique des requêtes de l'utilisateur."""
    queries = (
        db.query(Query)
        .filter(Query.user_id == current_user.id)
        .order_by(Query.created_at.desc())
        .limit(limit)
        .all()
    )
    return queries


@router.get("/info")
async def get_vector_store_info(
    current_user: User = Depends(get_current_user),
):
    """Retourne les informations sur le vector store Qdrant."""
    try:
        manager = VectorStoreManager()
        info = manager.get_collection_info()
        return info
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting vector store info: {str(e)}"
        )


@router.get("/test-pdf")
async def test_pdf_extraction():
    """Test endpoint pour vérifier l'extraction PDF."""
    try:
        processor = DocumentProcessor()
        documents = processor.load_all_pdfs()

        if not documents:
            raise HTTPException(status_code=404, detail="No PDF documents found")

        return {
            "status": "success",
            "message": "PDF loaded successfully",
            "total_pages": len(documents),
            "first_500_chars": documents[0].page_content[:500],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing PDF: {str(e)}"
        )
