"""Factory function for creating LLM client instances."""

from src.config import get_settings
from src.services.llm.client import LLMClient


def make_llm_client() -> LLMClient:
    """Create and return an LLM client instance.

    Returns:
        Configured LLMClient instance
    """
    settings = get_settings()
    return LLMClient(settings)
