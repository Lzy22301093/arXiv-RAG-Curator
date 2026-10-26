"""Shared fixtures for agent tests."""

import pytest
from unittest.mock import Mock, AsyncMock
from langchain_core.messages import HumanMessage

from src.services.agents.context import Context


@pytest.fixture
def mock_opensearch_client():
    """Create a mock OpenSearch client."""
    client = Mock()
    client.search_unified = AsyncMock(return_value=[])
    client.health_check = Mock(return_value=True)
    return client


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client (DeepSeek API)."""
    client = Mock()
    client.get_langchain_model = Mock()
    client.generate = AsyncMock(return_value={"response": "test"})
    return client


@pytest.fixture
def mock_jina_embeddings_client():
    """Create a mock Jina embeddings client."""
    client = Mock()
    client.embed_query = AsyncMock(return_value=[0.1] * 1024)
    client.embed_passages = AsyncMock(return_value=[[0.1] * 1024])
    return client


@pytest.fixture
def test_context(mock_opensearch_client, mock_llm_client, mock_jina_embeddings_client):
    """Create a test Context with mocked dependencies."""
    return Context(
        llm_client=mock_llm_client,
        opensearch_client=mock_opensearch_client,
        embeddings_client=mock_jina_embeddings_client,
        model_name="deepseek-flash",
        temperature=0.0,
        top_k=3,
        max_retrieval_attempts=2,
        guardrail_threshold=60,
    )


@pytest.fixture
def sample_human_message():
    """Create a sample HumanMessage for testing."""
    return HumanMessage(content="What is the transformer architecture?")


@pytest.fixture
def sample_tool_message():
    """Create a sample ToolMessage for testing."""
    from langchain_core.messages import ToolMessage
    return ToolMessage(
        content='[{"title": "Attention Is All You Need", "abstract": "We propose a new simple network architecture, the Transformer.", "arxiv_id": "1706.03762"}]',
        tool_call_id="test_tool_call_id",
        name="retrieve_papers",
    )


@pytest.fixture
def sample_ai_message():
    """Create a sample AIMessage for testing."""
    from langchain_core.messages import AIMessage
    return AIMessage(content="The Transformer is a neural network architecture.")
