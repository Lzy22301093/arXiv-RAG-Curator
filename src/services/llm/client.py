"""LLM Client for DeepSeek API integration using LangChain OpenAI."""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.config import Settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with DeepSeek API via OpenAI-compatible interface."""

    def __init__(self, settings: Settings):
        """Initialize LLM client with settings.

        Args:
            settings: Application settings containing DeepSeek API configuration
        """
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
        self.default_model = settings.deepseek_model

        # Validate configuration
        if not self.api_key:
            logger.warning("DeepSeek API key not configured - LLM features will be limited")

        logger.info(f"LLM Client initialized with model: {self.default_model}")

    async def generate_rag_answer(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        model: str = "deepseek-flash",
    ) -> Dict[str, Any]:
        """Generate a RAG answer using retrieved chunks.

        Args:
            query: User's question
            chunks: Retrieved document chunks with metadata
            model: Model to use for generation

        Returns:
            Dictionary with answer, sources, confidence, and citations
        """
        try:
            # Build context from chunks
            if chunks:
                context_parts = []
                for i, chunk in enumerate(chunks[:5], 1):
                    chunk_text = chunk.get("chunk_text", "")
                    arxiv_id = chunk.get("arxiv_id", "")
                    context_parts.append(f"[{i}] (arXiv:{arxiv_id}) {chunk_text}")
                context = "\n\n".join(context_parts)

                system_prompt = """You are a helpful research assistant. Answer the user's question based on the provided research paper excerpts.
Always cite the sources using [arXiv:ID] format. If the information is not in the provided context, say so clearly.
Be concise and accurate."""

                user_prompt = f"""Based on the following research paper excerpts, answer this question: {query}

Research Paper Excerpts:
{context}

Answer:"""
            else:
                system_prompt = """You are a helpful research assistant. Answer the user's question based on your general knowledge.
Be concise and accurate. If you're unsure about something, say so clearly."""

                user_prompt = query

            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            # Get model and invoke
            llm = self.get_langchain_model(model=model, temperature=0.7)
            response = await llm.ainvoke(messages)
            answer_text = response.content

            # Build sources from chunks
            sources = []
            seen_urls = set()
            for chunk in chunks:
                arxiv_id = chunk.get("arxiv_id")
                if arxiv_id:
                    arxiv_id_clean = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id_clean}.pdf"
                    if pdf_url not in seen_urls:
                        sources.append(pdf_url)
                        seen_urls.add(pdf_url)

            citations = list(set(chunk.get("arxiv_id") for chunk in chunks if chunk.get("arxiv_id")))

            return {
                "answer": answer_text,
                "sources": sources,
                "confidence": "medium" if chunks else "low",
                "citations": citations[:5],
            }

        except Exception as e:
            logger.error(f"Error generating RAG answer: {e}")
            raise Exception(f"Failed to generate RAG answer: {e}")

    async def generate_rag_answer_stream(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        model: str = "deepseek-flash",
    ):
        """Generate a streaming RAG answer using retrieved chunks.

        Args:
            query: User's question
            chunks: Retrieved document chunks with metadata
            model: Model to use for generation

        Yields:
            Streaming response chunks with partial answers
        """
        try:
            # Build context from chunks
            if chunks:
                context_parts = []
                for i, chunk in enumerate(chunks[:5], 1):
                    chunk_text = chunk.get("chunk_text", "")
                    arxiv_id = chunk.get("arxiv_id", "")
                    context_parts.append(f"[{i}] (arXiv:{arxiv_id}) {chunk_text}")
                context = "\n\n".join(context_parts)

                system_prompt = """You are a helpful research assistant. Answer the user's question based on the provided research paper excerpts.
Always cite the sources using [arXiv:ID] format. If the information is not in the provided context, say so clearly.
Be concise and accurate."""

                user_prompt = f"""Based on the following research paper excerpts, answer this question: {query}

Research Paper Excerpts:
{context}

Answer:"""
            else:
                system_prompt = """You are a helpful research assistant. Answer the user's question based on your general knowledge.
Be concise and accurate. If you're unsure about something, say so clearly."""

                user_prompt = query

            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            # Get model and stream
            llm = self.get_langchain_model(model=model, temperature=0.7)

            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield {"response": chunk.content}

            yield {"done": True}

        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            raise Exception(f"Error in streaming generation: {e}")

    def get_langchain_model(
        self,
        model: Optional[str] = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> ChatOpenAI:
        """Get a LangChain-compatible ChatOpenAI model instance.

        This method creates a ChatOpenAI instance configured for DeepSeek API.
        It's compatible with the existing agent nodes that call get_langchain_model().

        Args:
            model: Model name to use (defaults to settings.deepseek_model)
            temperature: Temperature for generation (0.0 to 1.0)
            **kwargs: Additional parameters to pass to ChatOpenAI

        Returns:
            ChatOpenAI instance configured for DeepSeek API
        """
        model_name = model or self.default_model

        logger.debug(f"Creating ChatOpenAI model: {model_name}, temperature: {temperature}")

        return ChatOpenAI(
            model=model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=temperature,
            **kwargs,
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check if DeepSeek API is accessible.

        Returns:
            Dictionary with health status information
        """
        try:
            # Create a minimal model instance to test connectivity
            llm = self.get_langchain_model(temperature=0.0)

            # Try a simple invocation to verify API access
            from langchain_core.messages import HumanMessage

            response = await llm.ainvoke([HumanMessage(content="Hello")])

            return {
                "status": "healthy",
                "message": "DeepSeek API is accessible",
                "model": self.default_model,
            }
        except Exception as e:
            logger.error(f"DeepSeek API health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"DeepSeek API check failed: {str(e)}",
                "model": self.default_model,
            }
