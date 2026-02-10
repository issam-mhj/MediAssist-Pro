from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from app.rag.retriever import RetrieverManager


class ResponseGenerator:

    def __init__(self):
        """Initialise le générateur de réponses."""
        self.retriever_manager = RetrieverManager()

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
        """
        Construit le contexte à partir des documents récupérés.

        Args:
            documents: Liste de Documents pertinents.

        Returns:
            Contexte formaté sous forme de chaîne.
        """
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
        """
        Génère une réponse à une question en utilisant le pipeline RAG.
        Retourne le contexte et les sources sans appel LLM (mode retrieval-only).
        Pour une intégration LLM complète, un endpoint séparé peut être ajouté.

        Args:
            question: Question de l'utilisateur.
            top_k: Nombre de chunks à récupérer.

        Returns:
            Dictionnaire avec la réponse, les sources et les métadonnées.
        """
        # Mettre à jour le top_k du retriever
        self.retriever_manager.top_k = top_k

        # Récupérer les documents pertinents
        documents = self.retriever_manager.search(question)

        if not documents:
            return {
                "answer": "Je ne trouve pas d'information pertinente dans les manuels techniques disponibles.",
                "sources": [],
                "retrieved_chunks": 0,
                "context": "",
            }

        # Construire le contexte
        context = self._build_context(documents)

        # Extraire les sources
        sources = self._extract_sources(documents)

        # Construire le prompt complet (prêt pour un LLM)
        full_prompt = self.prompt.format(context=context, question=question)

        # Mode retrieval-only : retourner le contexte récupéré
        # L'intégration LLM (Ollama/OpenAI) peut être ajoutée ici
        answer = (
            f"📚 **Informations trouvées dans les manuels techniques:**\n\n"
            f"{context}\n\n"
            f"---\n"
            f"*{len(documents)} source(s) consultée(s)*"
        )

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": len(documents),
            "context": context,
            "prompt": full_prompt,
        }

    def generate_answer_with_llm(
        self, question: str, llm, top_k: int = 5
    ) -> dict:
        """
        Génère une réponse en utilisant un LLM externe.

        Args:
            question: Question de l'utilisateur.
            llm: Instance du LLM LangChain à utiliser.
            top_k: Nombre de chunks à récupérer.

        Returns:
            Dictionnaire avec la réponse LLM, les sources et les métadonnées.
        """
        self.retriever_manager.top_k = top_k
        documents = self.retriever_manager.search(question)

        if not documents:
            return {
                "answer": "Je ne trouve pas d'information pertinente dans les manuels techniques disponibles.",
                "sources": [],
                "retrieved_chunks": 0,
            }

        context = self._build_context(documents)
        sources = self._extract_sources(documents)

        full_prompt = self.prompt.format(context=context, question=question)
        answer = llm.invoke(full_prompt)

        return {
            "answer": answer if isinstance(answer, str) else answer.content,
            "sources": sources,
            "retrieved_chunks": len(documents),
        }