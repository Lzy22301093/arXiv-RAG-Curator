from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class JinaRerankRequest(BaseModel):
    """Request model for Jina rerank API."""

    model: str = "jina-reranker-v3"
    query: str
    documents: List[str]
    top_n: Optional[int] = None
    return_documents: bool = False


class RerankResultItem(BaseModel):
    """Single rerank result from Jina API."""

    index: int
    relevance_score: float
    document: Optional[Dict] = None


class JinaRerankResponse(BaseModel):
    """Response model from Jina rerank API."""

    model: str
    usage: Dict[str, int] = Field(default_factory=dict)
    results: List[RerankResultItem]
