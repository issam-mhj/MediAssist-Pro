"""MLflow tracking for RAG configuration, responses, and metrics.

Uses **local file-based** tracking by default (``mlruns/`` directory inside
the working directory).  Set the ``MLFLOW_TRACKING_URI`` env-var to point to
a remote MLflow server when one is available – the tracker will fall back to
local storage automatically if the server is unreachable.

Every public method is wrapped so that a tracking failure **never** crashes
the application.
"""

import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

import mlflow
from app.rag.config import RAGConfig


class MLflowTracker:
    """Track RAG experiments, configurations, and metrics with MLflow."""

    def __init__(self):
        self.enabled = True
        self.current_run = None

        # Default to local file store – no server required
        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "file:///app/mlruns")
        try:
            mlflow.set_tracking_uri(mlflow_uri)
            experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "mediassist-rag")
            mlflow.set_experiment(experiment_name)
            print(f"✅ MLflow tracker initialized (URI: {mlflow_uri})")
        except Exception as exc:
            self.enabled = False
            print(f"⚠️ MLflow tracker disabled – init failed: {exc}")

    # ------------------------------------------------------------------
    # Internal safety wrapper
    # ------------------------------------------------------------------
    def _safe(self, fn, *args, **kwargs):
        """Run *fn* only when tracking is enabled; swallow errors."""
        if not self.enabled:
            return None
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            print(f"⚠️ MLflow call {fn.__name__} failed: {exc}")
            return None

    # ------------------------------------------------------------------
    def start_run(self, run_name: Optional[str] = None):
        """Start a new MLflow run."""
        if not self.enabled:
            return None
        try:
            if self.current_run:
                mlflow.end_run()
            run_name = run_name or f"rag_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.current_run = mlflow.start_run(run_name=run_name)
            return self.current_run
        except Exception as exc:
            print(f"⚠️ MLflow start_run failed: {exc}")
            self.current_run = None
            return None

    def log_rag_config(self):
        """Log RAG configuration (chunking, embedding, retrieval)."""
        def _log():
            mlflow.log_param("chunk_size", RAGConfig.CHAR_CHUNK_SIZE)
            mlflow.log_param("chunk_overlap", RAGConfig.CHAR_CHUNK_OVERLAP)
            mlflow.log_param("chunk_strategy", "structure_aware_markdown")
            mlflow.log_param("chunk_separators", str(RAGConfig.CHUNK_SEPARATORS))
            mlflow.log_param("embedding_model", RAGConfig.EMBEDDING_MODEL_NAME)
            mlflow.log_param("embedding_dimension", RAGConfig.EMBEDDING_DIMENSION)
            mlflow.log_param("embedding_device", RAGConfig.EMBEDDING_DEVICE)
            mlflow.log_param("embedding_normalization", True)
            mlflow.log_param("similarity_algorithm", RAGConfig.QDRANT_DISTANCE_METRIC)
            mlflow.log_param("top_k", RAGConfig.TOP_K_RETRIEVAL)
            mlflow.log_param("min_similarity_score", RAGConfig.MIN_SIMILARITY_SCORE)
            mlflow.log_param("vector_store", "Qdrant")
            mlflow.log_param("reranking", False)
            print("📝 RAG config logged to MLflow")
        self._safe(_log)

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
        def _log():
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
        self._safe(_log)

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
        def _log():
            timestamp = datetime.now().isoformat()
            step = int(time.time())
            mlflow.log_metric("query_latency_seconds", latency, step=step)
            mlflow.log_metric("context_length_chars", len(context), step=step)
            mlflow.log_metric("answer_length_chars", len(answer), step=step)
            mlflow.log_metric("sources_retrieved", len(sources), step=step)

            query_data = (
                f"Timestamp: {timestamp}\nTop-K: {top_k}\nLatency: {latency:.3f}s\n\n"
                f"Question:\n{question}\n\nAnswer:\n{answer}\n\n"
                f"Sources:\n{chr(10).join(f'  - {s}' for s in sources)}\n\n"
                f"Context:\n{context}\n"
            )
            mlflow.log_text(query_data, f"queries/query_{timestamp.replace(':', '-')}.txt")
            print("📝 Query logged to MLflow")
        self._safe(_log)

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log RAG evaluation metrics (from DeepEval)."""
        def _log():
            s = step or int(time.time())
            for key, value in metrics.items():
                mlflow.log_metric(key, value, step=s)
            print(f"📊 Metrics logged: {metrics}")
        self._safe(_log)

    def log_model(self, model, artifact_path: str = "rag_model"):
        """Log the RAG pipeline as an MLflow model."""
        def _log():
            mlflow.pyfunc.log_model(artifact_path=artifact_path, python_model=model)
            print(f"✅ Model logged to MLflow: {artifact_path}")
        self._safe(_log)

    def end_run(self):
        """End the current MLflow run."""
        if self.current_run:
            try:
                mlflow.end_run()
            except Exception:
                pass
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
