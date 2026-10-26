from typing import Optional

from src.config import Settings, get_settings

from .jina_client import JinaRerankClient


def make_rerank_service(settings: Optional[Settings] = None) -> Optional[JinaRerankClient]:
    """Create Jina rerank service when enabled and API key is present.

    :returns: JinaRerankClient, or None if disabled / missing key
    """
    if settings is None:
        settings = get_settings()

    if not settings.rerank.enabled:
        return None

    if not settings.jina_api_key:
        return None

    return JinaRerankClient(
        api_key=settings.jina_api_key,
        base_url=settings.rerank.base_url,
        model=settings.rerank.model,
        timeout=settings.rerank.timeout_seconds,
    )
