from src.services.embeddings.jina_client import JinaEmbeddingsClient
from src.services.llm.client import LLMClient
from src.services.opensearch.client import OpenSearchClient

from .agentic_rag import AgenticRAGService
from .config import GraphConfig


def make_agentic_rag_service(
    opensearch_client: OpenSearchClient,
    llm_client: LLMClient,
    embeddings_client: JinaEmbeddingsClient,
    top_k: int = 3,
    use_hybrid: bool = True,
    model: str = "deepseek-flash",
) -> AgenticRAGService:
    """
    Create AgenticRAGService with dependency injection.

    Args:
        opensearch_client: Client for document search
        llm_client: Client for LLM generation (DeepSeek API)
        embeddings_client: Client for embeddings
        top_k: Number of documents to retrieve (default: 3)
        use_hybrid: Use hybrid search (default: True)
        model: Model name to use (default: deepseek-flash)

    Returns:
        Configured AgenticRAGService instance
    """
    graph_config = GraphConfig(
        top_k=top_k,
        use_hybrid=use_hybrid,
        model=model,
    )

    return AgenticRAGService(
        opensearch_client=opensearch_client,
        llm_client=llm_client,
        embeddings_client=embeddings_client,
        graph_config=graph_config,
    )
