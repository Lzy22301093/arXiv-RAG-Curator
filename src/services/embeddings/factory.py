from typing import Optional

from src.config import Settings, get_settings

from .jina_client import JinaEmbeddingsClient

# BGE is optional (requires sentence-transformers)
try:
    from .bge_client import BGEEmbeddingsClient
except ImportError:
    BGEEmbeddingsClient = None


def make_embeddings_service(settings: Optional[Settings] = None) -> JinaEmbeddingsClient:
    """Factory function to create embeddings service.

    Creates a new client instance each time to avoid closed client issues.

    :param settings: Optional settings instance
    :returns: JinaEmbeddingsClient instance
    """
    if settings is None:
        settings = get_settings()

    # Get API key from settings
    api_key = settings.jina_api_key

    return JinaEmbeddingsClient(api_key=api_key)


def make_embeddings_client(settings: Optional[Settings] = None) -> JinaEmbeddingsClient:
    """Factory function to create embeddings client.

    Creates a new client instance each time to avoid closed client issues.

    :param settings: Optional settings instance
    :returns: JinaEmbeddingsClient instance
    """
    if settings is None:
        settings = get_settings()

    # Get API key from settings
    api_key = settings.jina_api_key

    return JinaEmbeddingsClient(api_key=api_key)


def make_bge_embeddings_service(settings: Optional[Settings] = None):
    """Factory function to create BGE embeddings service (optional local model).

    :param settings: Optional settings instance
    :returns: BGEEmbeddingsClient instance, or None if sentence-transformers is not installed
    """
    if BGEEmbeddingsClient is None:
        return None

    if settings is None:
        settings = get_settings()

    return BGEEmbeddingsClient(
        model_name=settings.bge_model_name,
        device=settings.bge_device,
    )
