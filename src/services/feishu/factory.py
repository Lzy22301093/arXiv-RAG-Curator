import logging
from typing import Optional

from src.config import get_settings
from src.services.feishu.bot import FeishuBot

logger = logging.getLogger(__name__)


def make_feishu_service(
    opensearch_client,
    embeddings_client,
    llm_client,
    cache_client=None,
) -> Optional[FeishuBot]:
    """
    Create Feishu bot if enabled.

    Args:
        opensearch_client: OpenSearch client
        embeddings_client: Embeddings service client
        llm_client: LLM client (DeepSeek API)
        cache_client: Optional cache client

    Returns:
        FeishuBot instance or None if disabled
    """
    settings = get_settings()

    if not settings.feishu.enabled:
        logger.info("Feishu bot is disabled")
        return None

    if not settings.feishu.app_id or not settings.feishu.app_secret:
        logger.warning("Feishu app_id or app_secret not configured")
        return None

    bot = FeishuBot(
        app_id=settings.feishu.app_id,
        app_secret=settings.feishu.app_secret,
        verification_token=settings.feishu.verification_token,
        encrypt_key=settings.feishu.encrypt_key,
        opensearch_client=opensearch_client,
        embeddings_client=embeddings_client,
        llm_client=llm_client,
        cache_client=cache_client,
    )

    logger.info("Feishu bot created successfully")
    return bot
