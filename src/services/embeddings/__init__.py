from .factory import make_embeddings_client, make_embeddings_service
from .jina_client import JinaEmbeddingsClient

# BGE imports are optional (requires sentence-transformers)
try:
    from .bge_client import BGEEmbeddingsClient
    from .factory import make_bge_embeddings_service
except ImportError:
    BGEEmbeddingsClient = None
    make_bge_embeddings_service = None

__all__ = [
    "BGEEmbeddingsClient",
    "JinaEmbeddingsClient",
    "make_bge_embeddings_service",
    "make_embeddings_client",
    "make_embeddings_service",
]
