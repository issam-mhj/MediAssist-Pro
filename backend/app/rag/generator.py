import os
from typing import List

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from app.rag.retriever import RetrieverManager


def _get_llm():
    """Return the best available LLM.

    Priority:
    1. OpenAI (if OPENAI_API_KEY is set)
    2. Ollama  (default — runs inside Docker)
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        from langchain_openai import ChatOpenAI
        print(" Using OpenAI LLM")
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=0.3,
            api_key=openai_key,
        )

    from langchain_ollama import ChatOllama
    base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    print(f" Using Ollama LLM ({model}) at {base_url}")
    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=0.3,
    )


class ResponseGenerator:

    def __init__(self):
        self.retriever_manager = RetrieverManager()
        self.llm = _get_llm()

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
            input_variables=["context", "question"],
        )

    def _build_context(self, documents: List[Document]) -> str:
        context_parts = []
        for doc in documents:
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "N/A")
            context_parts.append(
                f"[Source: {source} - Page {page}]\n{doc.page_content}"
            )
        return "\n\n".join(context_parts)

    def _extract_sources(self, documents: List[Document]) -> List[str]:
        sources = []
        seen = set()
        for doc in documents:
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "N/A")
            key = f"{source} (Page {page})"
            if key not in seen:
                sources.append(key)
                seen.add(key)
        return sources

    def generate_answer(self, question: str, top_k: int = 5) -> dict:
        self.retriever_manager.top_k = top_k

        documents = self.retriever_manager.search(question)

        if not documents:
            return {
                "answer": "Je ne trouve pas cette information dans les manuels techniques disponibles.",
                "sources": [],
            }

        context = self._build_context(documents)
        sources = self._extract_sources(documents)

        formatted_prompt = self.prompt.format(
            context=context, question=question
        )

        try:
            response = self.llm.invoke(formatted_prompt)
            answer = response.content
        except Exception as e:
            answer = (
                f"Erreur lors de la génération: {str(e)}\n\n"
                f"Contexte trouvé:\n{context}"
            )

        return {
            "answer": answer,
            "sources": sources,
            "documents": documents, 
        }