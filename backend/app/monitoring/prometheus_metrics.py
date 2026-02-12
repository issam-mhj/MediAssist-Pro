"""Prometheus metrics for RAG application monitoring."""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import time
from functools import wraps

# Create a registry for all metrics
REGISTRY = CollectorRegistry()

# Request metrics
rag_requests_total = Counter(
    "rag_requests_total",
    "Total number of RAG requests",
    ["endpoint", "status"],
    registry=REGISTRY,
)

rag_request_duration_seconds = Histogram(
    "rag_request_duration_seconds",
    "RAG request latency in seconds",
    ["endpoint"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
    registry=REGISTRY,
)

# RAG-specific metrics
rag_query_latency_seconds = Histogram(
    "rag_query_latency_seconds",
    "Time to generate RAG response",
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0),
    registry=REGISTRY,
)

rag_retrieval_chunks_count = Histogram(
    "rag_retrieval_chunks_count",
    "Number of chunks retrieved per query",
    buckets=(1, 3, 5, 10, 20, 50),
    registry=REGISTRY,
)

rag_answer_length_chars = Histogram(
    "rag_answer_length_chars",
    "Length of generated answer in characters",
    buckets=(50, 100, 200, 500, 1000, 2000, 5000),
    registry=REGISTRY,
)

rag_errors_total = Counter(
    "rag_errors_total",
    "Total number of RAG errors",
    ["error_type"],
    registry=REGISTRY,
)

# Quality metrics (updated via external evaluation)
rag_answer_relevance_score = Gauge(
    "rag_answer_relevance_score",
    "Latest answer relevance score",
    registry=REGISTRY,
)

rag_faithfulness_score = Gauge(
    "rag_faithfulness_score",
    "Latest faithfulness score",
    registry=REGISTRY,
)

# Vector store metrics
vector_store_documents_count = Gauge(
    "vector_store_documents_count",
    "Number of documents in vector store",
    registry=REGISTRY,
)

# System metrics
system_memory_usage_bytes = Gauge(
    "system_memory_usage_bytes",
    "Current memory usage in bytes",
    registry=REGISTRY,
)


def track_rag_query_time(func):
    """Decorator to track RAG query latency."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            rag_query_latency_seconds.observe(duration)
            return result
        except Exception as e:
            rag_errors_total.labels(error_type=type(e).__name__).inc()
            raise
    return wrapper


def get_metrics():
    """Get current Prometheus metrics in text format."""
    return generate_latest(REGISTRY)


def record_query_metrics(
    latency: float,
    chunks_count: int,
    answer_length: int,
    success: bool = True,
):
    """Record metrics for a single RAG query."""
    rag_query_latency_seconds.observe(latency)
    rag_retrieval_chunks_count.observe(chunks_count)
    rag_answer_length_chars.observe(answer_length)
    
    if success:
        rag_requests_total.labels(endpoint="query", status="success").inc()
    else:
        rag_requests_total.labels(endpoint="query", status="error").inc()


def update_quality_metrics(
    answer_relevance: float,
    faithfulness: float,
):
    """Update quality metrics from evaluation."""
    rag_answer_relevance_score.set(answer_relevance)
    rag_faithfulness_score.set(faithfulness)
