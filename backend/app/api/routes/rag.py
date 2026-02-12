"""Routes API pour le système RAG MediAssist-Pro."""

import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.query import Query
from app.schemas.query import RAGRequest, RAGResponse
from app.rag.document_processor import DocumentProcessor
from app.rag.chunking import DocumentChunker
from app.rag.vector_store import VectorStoreManager
from app.rag.generator import ResponseGenerator
from app.rag.config import RAGConfig
from app.monitoring.mlflow_tracker import get_tracker
from app.monitoring.prometheus_metrics import (
    record_query_metrics,
    update_quality_metrics,
    rag_requests_total,
)
from app.monitoring.metrics import evaluate_rag_response

router = APIRouter(prefix="/rag", tags=["RAG"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_pdf_files():
    """Return list of PDF paths found in the rag module folder."""
    pdf_files = list(RAGConfig.RAG_DIR.glob("*.pdf"))
    if not pdf_files:
        raise HTTPException(
            status_code=404,
            detail=f"No PDF files found in {RAGConfig.RAG_DIR}. "
                   f"Place your PDF in backend/app/rag/."
        )
    return pdf_files


# ---------------------------------------------------------------------------
# Step 1 — List available PDFs
# ---------------------------------------------------------------------------
@router.get("/pdfs")
async def list_pdfs():
    """Liste les PDFs disponibles dans le dossier rag (aucun traitement)."""
    rag_dir = RAGConfig.RAG_DIR
    pdf_files = list(rag_dir.glob("*.pdf"))
    return {
        "directory": str(rag_dir),
        "pdf_files": [
            {"name": f.name, "size_kb": round(f.stat().st_size / 1024, 2)}
            for f in pdf_files
        ],
        "count": len(pdf_files),
    }


# ---------------------------------------------------------------------------
# Step 2 — Extract text from PDF(s)  →  returns extracted pages
# ---------------------------------------------------------------------------
@router.post("/extract")
async def extract_documents():
    """Extracts text from the PDF(s) in the rag/ folder via LlamaParse.

    Returns the raw extracted pages so you can inspect the result.
    """
    try:
        pdf_files = _get_pdf_files()

        processor = DocumentProcessor(documents_dir=str(RAGConfig.RAG_DIR))
        documents = processor.load_all_pdfs()

        if not documents:
            raise HTTPException(status_code=404, detail="No content extracted from PDFs")

        return {
            "message": "PDF extraction complete",
            "pdf_files": [f.name for f in pdf_files],
            "total_pages": len(documents),
            "pages": [
                {
                    "page": doc.metadata.get("page"),
                    "source": doc.metadata.get("source"),
                    "char_count": len(doc.page_content),
                    "preview": doc.page_content[:300],
                }
                for doc in documents
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error extracting PDF: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Step 3 — Chunk extracted text  →  returns chunk details
# ---------------------------------------------------------------------------
@router.post("/chunk")
async def chunk_documents():
    """Extracts PDF text then splits into chunks.

    Returns chunk statistics and a preview of each chunk.
    """
    try:
        pdf_files = _get_pdf_files()

        processor = DocumentProcessor(documents_dir=str(RAGConfig.RAG_DIR))
        documents = processor.load_all_pdfs()

        if not documents:
            raise HTTPException(status_code=404, detail="No content extracted from PDFs")

        chunker = DocumentChunker(
            chunk_size=RAGConfig.CHAR_CHUNK_SIZE,
            chunk_overlap=RAGConfig.CHAR_CHUNK_OVERLAP,
        )
        chunks = chunker.create_character_chunks(documents)
        stats = chunker.get_chunk_stats(chunks)

        return {
            "message": "Chunking complete",
            "pdf_files": [f.name for f in pdf_files],
            "total_pages": len(documents),
            "total_chunks": len(chunks),
            "stats": stats,
            "chunks": [
                {
                    "chunk_id": c.metadata.get("chunk_id"),
                    "page": c.metadata.get("page"),
                    "source": c.metadata.get("source"),
                    "char_count": len(c.page_content),
                    "preview": c.page_content[:200],
                }
                for c in chunks
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error chunking documents: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Step 4 — Full pipeline: extract → chunk → embed → store in Qdrant
# ---------------------------------------------------------------------------
@router.post("/index")
async def index_documents():
    """Full pipeline: extract PDF → chunk → delete old vectors → embed & store.

    Auto-detects PDFs from the rag/ folder (no upload needed).
    Old chunks are deleted before storing new ones.
    """
    try:
        pdf_files = _get_pdf_files()

        # Extract
        processor = DocumentProcessor(documents_dir=str(RAGConfig.RAG_DIR))
        documents = processor.load_all_pdfs()

        if not documents:
            raise HTTPException(status_code=404, detail="No content extracted from PDFs")

        # Chunk
        chunker = DocumentChunker(
            chunk_size=RAGConfig.CHAR_CHUNK_SIZE,
            chunk_overlap=RAGConfig.CHAR_CHUNK_OVERLAP,
        )
        chunks = chunker.create_character_chunks(documents)

        # Embed + store (deletes old vectors first)
        manager = VectorStoreManager()
        manager.create_vector_store(chunks)

        return {
            "message": "Documents indexed successfully in Qdrant",
            "pdf_files": [f.name for f in pdf_files],
            "total_pages": len(documents),
            "total_chunks": len(chunks),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error indexing documents: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Query the RAG system
# ---------------------------------------------------------------------------
@router.post("/query", response_model=RAGResponse)
async def query_rag(
    request: RAGRequest,
    db: Session = Depends(get_db),
):
    """Interroge le système RAG with MLflow tracking and Prometheus metrics."""
    start_time = time.time()
    
    try:
        # Track with Prometheus
        rag_requests_total.labels(endpoint="query", status="in_progress").inc()
        
        # Generate answer
        generator = ResponseGenerator()
        result = generator.generate_answer(request.question, top_k=request.top_k)
        
        latency = time.time() - start_time
        
        # Extract context for logging/metrics
        retrieved_contexts = [doc.page_content for doc in result.get("documents", [])]
        
        # Log to MLflow
        tracker = get_tracker()
        try:
            if not tracker.current_run:
                tracker.start_run()
                tracker.log_rag_config()
                tracker.log_llm_config(
                    model_name=generator.llm.model if hasattr(generator.llm, 'model') else "unknown",
                    temperature=generator.llm.temperature if hasattr(generator.llm, 'temperature') else 0.3,
                )
            
            tracker.log_query(
                question=request.question,
                answer=result["answer"],
                context="\n\n".join(retrieved_contexts) if retrieved_contexts else "No context",
                sources=result["sources"],
                latency=latency,
                top_k=request.top_k,
            )
            
            # Evaluate with DeepEval (optional - requires OpenAI key)
            try:
                metrics = evaluate_rag_response(
                    question=request.question,
                    answer=result["answer"],
                    retrieved_contexts=retrieved_contexts,
                )
                tracker.log_metrics(metrics)
                update_quality_metrics(
                    answer_relevance=metrics.get("answer_relevance", 0.0),
                    faithfulness=metrics.get("faithfulness", 0.0),
                )
            except Exception as eval_error:
                print(f"⚠️ Evaluation skipped: {eval_error}")
        
        except Exception as mlflow_error:
            print(f"⚠️ MLflow logging failed: {mlflow_error}")
        
        # Record Prometheus metrics
        record_query_metrics(
            latency=latency,
            chunks_count=len(retrieved_contexts),
            answer_length=len(result["answer"]),
            success=True,
        )
        
        # Save to database
        new_query = Query(
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
        record_query_metrics(
            latency=time.time() - start_time,
            chunks_count=0,
            answer_length=0,
            success=False,
        )
        raise HTTPException(
            status_code=500, detail=f"Error processing query: {str(e)}"
        )


# ---------------------------------------------------------------------------
# History & info
# ---------------------------------------------------------------------------
@router.get("/history")
async def get_query_history(
    db: Session = Depends(get_db),
    limit: int = 10,
):
    """Récupère l'historique des requêtes."""
    queries = (
        db.query(Query)
        .order_by(Query.created_at.desc())
        .limit(limit)
        .all()
    )
    return queries


@router.get("/info")
async def get_vector_store_info():
    """Retourne les informations sur le vector store Qdrant."""
    try:
        manager = VectorStoreManager()
        info = manager.get_collection_info()
        return info
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting vector store info: {str(e)}"
        )
