import pytest

from src.schemas.rerank import JinaRerankRequest, JinaRerankResponse, RerankResultItem


def test_jina_rerank_request_defaults():
    req = JinaRerankRequest(query="q", documents=["a", "b"])
    assert req.model == "jina-reranker-v3"
    assert req.return_documents is False
    assert req.top_n is None


def test_jina_rerank_response_parse():
    resp = JinaRerankResponse(
        model="jina-reranker-v3",
        usage={"total_tokens": 10},
        results=[
            RerankResultItem(index=1, relevance_score=0.9),
            RerankResultItem(index=0, relevance_score=0.2),
        ],
    )
    assert len(resp.results) == 2
    assert resp.results[0].index == 1


@pytest.mark.asyncio
async def test_rerank_items_orders_by_score():
    from src.services.rerank.jina_client import JinaRerankClient

    client = JinaRerankClient(api_key="test-key")

    async def fake_rerank(query, documents, top_n=None):
        return [
            RerankResultItem(index=1, relevance_score=0.95),
            RerankResultItem(index=0, relevance_score=0.4),
        ]

    client.rerank = fake_rerank  # type: ignore
    items = [
        {"chunk_text": "low relevance", "arxiv_id": "1"},
        {"chunk_text": "high relevance", "arxiv_id": "2"},
    ]
    ranked = await client.rerank_items("query", items, top_n=2)
    assert ranked[0]["arxiv_id"] == "2"
    assert ranked[0]["rerank_score"] == 0.95
    await client.close()
