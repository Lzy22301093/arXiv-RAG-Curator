from dataclasses import dataclass
import logging
from typing import Optional

from src.services.embeddings.jina_client import JinaEmbeddingsClient
from src.services.llm.client import LLMClient
from src.services.opensearch.client import OpenSearchClient

logger = logging.getLogger(__name__)


@dataclass
class Context:
    """Runtime context for agent dependencies.

    This contains immutable dependencies that nodes need but don't modify.

    :param llm_client: Client for LLM generation via DeepSeek API
    :param opensearch_client: Client for document search
    :param embeddings_client: Client for embeddings
    :param model_name: Model to use for LLM calls
    :param temperature: Temperature for generation
    :param top_k: Number of documents to retrieve
    :param max_retrieval_attempts: Maximum retrieval attempts
    :param guardrail_threshold: Threshold for guardrail validation (0-100)
    """

    llm_client: LLMClient
    opensearch_client: OpenSearchClient = None
    embeddings_client: JinaEmbeddingsClient = None
    model_name: str = "deepseek-flash"
    temperature: float = 0.0
    top_k: int = 3
    max_retrieval_attempts: int = 2
    guardrail_threshold: int = 60

    def get_llm(self, model: Optional[str] = None, temperature: Optional[float] = None):
        """Get LLM instance from the DeepSeek API client.

        Args:
            model: Model name to use (defaults to self.model_name)
            temperature: Temperature for generation (defaults to self.temperature)

        Returns:
            LangChain-compatible LLM instance

        Raises:
            ValueError: If no LLM client is available
        """
        if not self.llm_client:
            raise ValueError("No LLM client available")

        model_name = model or self.model_name
        temp = temperature if temperature is not None else self.temperature

        logger.debug(f"Using LLM client for model: {model_name}")
        return self.llm_client.get_langchain_model(
            model=model_name,
            temperature=temp,
        )
