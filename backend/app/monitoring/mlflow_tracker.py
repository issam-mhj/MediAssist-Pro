"""MLflow tracking for RAG configuration, responses, and metrics."""

import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

import mlflow
from mlflow.models import infer_signature
from app.rag.config import RAGConfig


class MLflowTracker:
    """Track RAG experiments, configurations, and metrics with MLflow."""

    def __init__(self):
        # Set MLflow tracking URI
        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
        mlflow.set_tracking_uri(mlflow_uri)
        
        # Set experiment name
        experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "mediassist-rag")
        mlflow.set_experiment(experiment_name)
        
        self.current_run = None
        print(f"✅ MLflow tracker initialized (URI: {mlflow_uri})")

    def start_run(self, run_name: Optional[str] = None):
        """Start a new MLflow run."""
        if self.current_run:
            mlflow.end_run()
        
        run_name = run_name or f"rag_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_run = mlflow.start_run(run_name=run_name)
        return self.current_run

    def log_rag_config(self):
        """Log RAG configuration (chunking, embedding, retrieval)."""
        # Chunking config
        mlflow.log_param("chunk_size", RAGConfig.CHAR_CHUNK_SIZE)
        mlflow.log_param("chunk_overlap", RAGConfig.CHAR_CHUNK_OVERLAP)
        mlflow.log_param("chunk_strategy", "structure_aware_markdown")
        mlflow.log_param("chunk_separators", str(RAGConfig.CHUNK_SEPARATORS))

        # Embedding config
        mlflow.log_param("embedding_model", RAGConfig.EMBEDDING_MODEL_NAME)
        mlflow.log_param("embedding_dimension", RAGConfig.EMBEDDING_DIMENSION)
        mlflow.log_param("embedding_device", RAGConfig.EMBEDDING_DEVICE)
        mlflow.log_param("embedding_normalization", True)

        # Retrieval config
        mlflow.log_param("similarity_algorithm", RAGConfig.QDRANT_DISTANCE_METRIC)
        mlflow.log_param("top_k", RAGConfig.TOP_K_RETRIEVAL)
        mlflow.log_param("min_similarity_score", RAGConfig.MIN_SIMILARITY_SCORE)
        mlflow.log_param("vector_store", "Qdrant")
        mlflow.log_param("reranking", False)

        print("📝 RAG config logged to MLflow")

    def log_llm_config(
        self,
        model_name: str,
        temperature: float,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        prompt_template: Optional[str] = None,
    ):
        """Log LLM hyperparameters."""
        mlflow.log_param("llm_model", model_name)
        mlflow.log_param("llm_temperature", temperature)
        
        if max_tokens:
            mlflow.log_param("llm_max_tokens", max_tokens)
        if top_p:
            mlflow.log_param("llm_top_p", top_p)
        if top_k:
            mlflow.log_param("llm_top_k", top_k)
        if prompt_template:
            mlflow.log_text(prompt_template, "prompt_template.txt")

        print("📝 LLM config logged to MLflow")

    def log_query(
        self,
        question: str,
        answer: str,
        context: str,
        sources: List[str],
        latency: float,
        top_k: int,
    ):
        """Log a single RAG query with response and context."""
        timestamp = datetime.now().isoformat()
        
        # Log as metrics
        mlflow.log_metric("query_latency_seconds", latency, step=int(time.time()))
        mlflow.log_metric("context_length_chars", len(context), step=int(time.time()))
        mlflow.log_metric("answer_length_chars", len(answer), step=int(time.time()))
        mlflow.log_metric("sources_retrieved", len(sources), step=int(time.time()))

        # Log as artifacts
        query_data = f"""Timestamp: {timestamp}
Top-K: {top_k}
Latency: {latency:.3f}s

Question:
{question}

Answer:
{answer}

Sources:
{chr(10).join(f"  - {s}" for s in sources)}

Context:
{context}
"""
        mlflow.log_text(query_data, f"queries/query_{timestamp.replace(':', '-')}.txt")

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log RAG evaluation metrics (from DeepEval)."""
        step = step or int(time.time())
        for key, value in metrics.items():
            mlflow.log_metric(key, value, step=step)
        print(f"📊 Metrics logged: {metrics}")

    def log_model(self, model, artifact_path: str = "rag_model"):
        """Log the RAG pipeline as an MLflow model."""
        try:
            mlflow.pyfunc.log_model(
                artifact_path=artifact_path,
                python_model=model,
            )
            print(f"✅ Model logged to MLflow: {artifact_path}")
        except Exception as e:
            print(f"⚠️ Could not log model: {e}")

    def end_run(self):
        """End the current MLflow run."""
        if self.current_run:
            mlflow.end_run()
            self.current_run = None
            print("✅ MLflow run ended")


# Global tracker instance
_tracker: Optional[MLflowTracker] = None


def get_tracker() -> MLflowTracker:
    """Get or create the global MLflow tracker."""
    global _tracker
    if _tracker is None:
        _tracker = MLflowTracker()
    return _tracker
