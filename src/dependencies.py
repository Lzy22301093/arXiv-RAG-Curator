from functools import lru_cache
from typing import TYPE_CHECKING, Annotated, Generator, Optional

if TYPE_CHECKING:
    from fastapi import Depends, Request
    from sqlalchemy.orm import Session
else:
    try:
        from fastapi import Depends, Request
        from sqlalchemy.orm import Session
    except ImportError:
        pass

from src.config import Settings
from src.db.interfaces.base import BaseDatabase
from src.services.agents.agentic_rag import AgenticRAGService
from src.services.agents.factory import make_agentic_rag_service
from src.services.arxiv.client import ArxivClient
from src.services.cache.client import CacheClient
from src.services.embeddings.factory import make_embeddings_service
from src.services.embeddings.jina_client import JinaEmbeddingsClient
from src.services.feishu.bot import FeishuBot
from src.services.llm.client import LLMClient
from src.services.opensearch.client import OpenSearchClient
from src.services.pdf_parser.parser import PDFParserService
from src.services.rerank.jina_client import JinaRerankClient


@lru_cache
def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


def get_request_settings(request: Request) -> Settings:
    """Get settings from the request state."""
    return request.app.state.settings


def get_database(request: Request) -> BaseDatabase:
    """Get database from the request state."""
    return request.app.state.database


def get_db_session(database: Annotated[BaseDatabase, Depends(get_database)]) -> Generator[Session, None, None]:
    """Get database session dependency."""
    with database.get_session() as session:
        yield session


def get_opensearch_client(request: Request) -> OpenSearchClient:
    """Get OpenSearch client from the request state."""
    return request.app.state.opensearch_client


def get_arxiv_client(request: Request) -> ArxivClient:
    """Get arXiv client from the request state."""
    return request.app.state.arxiv_client


def get_pdf_parser(request: Request) -> PDFParserService:
    """Get PDF parser service from the request state."""
    return request.app.state.pdf_parser


def get_embeddings_service(request: Request) -> JinaEmbeddingsClient:
    """Get embeddings service from the request state."""
    return request.app.state.embeddings_service


def get_rerank_service(request: Request) -> Optional[JinaRerankClient]:
    """Get optional Jina rerank service from the request state."""
    return getattr(request.app.state, "rerank_service", None)


def get_bge_embeddings_service(request: Request):
    """Get optional BGE embeddings service from the request state (None if not installed)."""
    return getattr(request.app.state, "bge_embeddings_service", None)


def get_llm_client(request: Request) -> LLMClient:
    """Get LLM client (DeepSeek API) from the request state."""
    return request.app.state.llm_client


def get_cache_client(request: Request) -> CacheClient | None:
    """Get cache client from the request state."""
    return getattr(request.app.state, "cache_client", None)


def get_feishu_service(request: Request) -> Optional[FeishuBot]:
    """Get Feishu service from the request state."""
    return getattr(request.app.state, "feishu_service", None)


# Dependency annotations
SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[BaseDatabase, Depends(get_database)]
SessionDep = Annotated[Session, Depends(get_db_session)]
OpenSearchDep = Annotated[OpenSearchClient, Depends(get_opensearch_client)]
ArxivDep = Annotated[ArxivClient, Depends(get_arxiv_client)]
PDFParserDep = Annotated[PDFParserService, Depends(get_pdf_parser)]
EmbeddingsDep = Annotated[JinaEmbeddingsClient, Depends(get_embeddings_service)]
BGEEmbeddingsDep = Annotated[Optional[object], Depends(get_bge_embeddings_service)]
RerankDep = Annotated[Optional[JinaRerankClient], Depends(get_rerank_service)]
LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]
CacheDep = Annotated[CacheClient | None, Depends(get_cache_client)]
FeishuDep = Annotated[Optional[FeishuBot], Depends(get_feishu_service)]


def get_agentic_rag_service(
    opensearch: OpenSearchDep,
    embeddings: EmbeddingsDep,
    llm_client: LLMClientDep,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AgenticRAGService:
    """Get agentic RAG service."""
    return make_agentic_rag_service(
        opensearch_client=opensearch,
        llm_client=llm_client,
        embeddings_client=embeddings,
        model=settings.deepseek_model,
    )


AgenticRAGDep = Annotated[AgenticRAGService, Depends(get_agentic_rag_service)]
