"""Jina AI rerank API client (cross-encoder second-stage ranking)."""

import logging
from typing import Any, Dict, List, Optional

import httpx
from src.schemas.rerank import JinaRerankRequest, JinaRerankResponse, RerankResultItem

logger = logging.getLogger(__name__)


class JinaRerankClient:
    """Client for Jina AI rerank API.

    Uses jina-reranker-v3 cross-encoder to rescore hybrid retrieval candidates.
    Documentation: https://jina.ai/models/jina-reranker-v3
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.jina.ai/v1",
        model: str = "jina-reranker-v3",
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=timeout)
        logger.info("Jina rerank client initialized (model=%s)", model)

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
    ) -> List[RerankResultItem]:
        """Rerank documents against a query.

        :param query: User query
        :param documents: Candidate texts (chunk texts)
        :param top_n: Optional max results to return; defaults to all
        :returns: Results sorted by relevance_score descending
        """
        if not documents:
            return []

        request_data = JinaRerankRequest(
            model=self.model,
            query=query,
            documents=documents,
            top_n=top_n if top_n is not None else len(documents),
            return_documents=False,
        )

        try:
            response = await self.client.post(
                f"{self.base_url}/rerank",
                headers=self.headers,
                json=request_data.model_dump(exclude_none=True),
            )
            response.raise_for_status()
            result = JinaRerankResponse(**response.json())
            ranked = sorted(result.results, key=lambda r: r.relevance_score, reverse=True)
            logger.debug("Reranked %d docs -> top_n=%s", len(documents), top_n)
            return ranked

        except httpx.HTTPError as e:
            logger.error("Error calling Jina rerank API: %s", e)
            raise
        except Exception as e:
            logger.error("Unexpected error in rerank: %s", e)
            raise

    async def rerank_items(
        self,
        query: str,
        items: List[Dict[str, Any]],
        top_n: Optional[int] = None,
        text_key: str = "chunk_text",
    ) -> List[Dict[str, Any]]:
        """Rerank dict items that carry text under ``text_key``.

        Falls back to original order truncated to ``top_n`` if texts are empty.
        Attaches ``rerank_score`` when scoring succeeds.
        """
        if not items:
            return []

        documents = [str(item.get(text_key) or item.get("abstract") or "") for item in items]
        if not any(documents):
            return items[:top_n] if top_n else items

        results = await self.rerank(query, documents, top_n=top_n)
        ranked: List[Dict[str, Any]] = []
        for r in results:
            if 0 <= r.index < len(items):
                new_item = dict(items[r.index])
                new_item["rerank_score"] = r.relevance_score
                ranked.append(new_item)

        if not ranked:
            return items[:top_n] if top_n else items
        return ranked

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
