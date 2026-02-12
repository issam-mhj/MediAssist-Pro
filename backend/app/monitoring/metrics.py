"""RAG evaluation metrics using DeepEval."""

from typing import Dict, List
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
)
from deepeval.test_case import LLMTestCase


class RAGMetricsEvaluator:
    """Evaluate RAG responses with DeepEval metrics."""

    def __init__(self, model_name: str = "gpt-4"):
        """Initialize metrics.
        
        Note: DeepEval metrics require an LLM for evaluation.
        Set OPENAI_API_KEY if using GPT models.
        """
        self.answer_relevancy = AnswerRelevancyMetric(
            threshold=0.7,
            model=model_name,
        )
        self.faithfulness = FaithfulnessMetric(
            threshold=0.7,
            model=model_name,
        )
        self.contextual_precision = ContextualPrecisionMetric(
            threshold=0.7,
            model=model_name,
        )
        self.contextual_recall = ContextualRecallMetric(
            threshold=0.7,
            model=model_name,
        )

    def evaluate_response(
        self,
        question: str,
        answer: str,
        retrieved_contexts: List[str],
        expected_output: str = None,
    ) -> Dict[str, float]:
        """Evaluate a single RAG response.
        
        Returns:
            Dict with metrics: answer_relevance, faithfulness, precision, recall
        """
        test_case = LLMTestCase(
            input=question,
            actual_output=answer,
            expected_output=expected_output,
            retrieval_context=retrieved_contexts,
        )

        results = {}

        try:
            self.answer_relevancy.measure(test_case)
            results["answer_relevance"] = self.answer_relevancy.score
        except Exception as e:
            print(f"⚠️ Answer relevancy metric failed: {e}")
            results["answer_relevance"] = 0.0

        try:
            self.faithfulness.measure(test_case)
            results["faithfulness"] = self.faithfulness.score
        except Exception as e:
            print(f"⚠️ Faithfulness metric failed: {e}")
            results["faithfulness"] = 0.0

        try:
            self.contextual_precision.measure(test_case)
            results["precision"] = self.contextual_precision.score
        except Exception as e:
            print(f"⚠️ Precision metric failed: {e}")
            results["precision"] = 0.0

        try:
            self.contextual_recall.measure(test_case)
            results["recall"] = self.contextual_recall.score
        except Exception as e:
            print(f"⚠️ Recall metric failed: {e}")
            results["recall"] = 0.0

        return results


def evaluate_rag_response(
    question: str,
    answer: str,
    retrieved_contexts: List[str],
    expected_output: str = None,
) -> Dict[str, float]:
    """Convenience function to evaluate a RAG response.
    
    Returns metrics: answer_relevance, faithfulness, precision, recall
    """
    evaluator = RAGMetricsEvaluator()
    return evaluator.evaluate_response(
        question=question,
        answer=answer,
        retrieved_contexts=retrieved_contexts,
        expected_output=expected_output,
    )
