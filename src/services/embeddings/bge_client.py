import asyncio
import logging
from typing import List

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class BGEEmbeddingsClient:
    """Client for BGE (BAAI General Embedding) models.

    Uses sentence-transformers to load BGE model locally.
    Model: BAAI/bge-large-zh-v1.5 (1024 dimensions)
    """

    def __init__(self, model_name: str = "BAAI/bge-large-zh-v1.5", device: str = "cpu"):
        """Initialize BGE embeddings client.

        :param model_name: HuggingFace model name or local path
        :param device: Device to run model on ('cpu' or 'cuda')
        """
        self.model_name = model_name
        self.device = device
        self._model: SentenceTransformer | None = None
        logger.info(f"BGE embeddings client initialized (model={model_name}, device={device})")

    def _get_model(self) -> SentenceTransformer:
        """Lazy load the model on first use."""
        if self._model is None:
            logger.info(f"Loading BGE model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("BGE model loaded successfully")
        return self._model

    async def embed_passages(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Embed text passages for indexing.

        BGE model prefix: Represent this passage for retrieval:

        :param texts: List of text passages to embed
        :param batch_size: Number of texts to process in each batch
        :returns: List of embedding vectors
        """
        model = self._get_model()

        # BGE retrieval passages don't need prefix for indexing
        # But we add the retrieval prefix for better search quality
        texts_with_prefix = [f"Represent this passage for retrieval: {t}" for t in texts]

        # Run in executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: model.encode(texts_with_prefix, batch_size=batch_size, show_progress_bar=False, normalize_embeddings=True),
        )

        # Convert numpy arrays to lists
        result = [emb.tolist() for emb in embeddings]
        logger.info(f"Successfully embedded {len(texts)} passages")
        return result

    async def embed_query(self, query: str) -> List[float]:
        """Embed a search query.

        BGE model prefix: Represent this query for retrieval:

        :param query: Query text to embed
        :returns: Embedding vector for the query
        """
        model = self._get_model()

        # BGE query prefix for retrieval
        query_with_prefix = f"Represent this query for retrieval: {query}"

        # Run in executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: model.encode([query_with_prefix], normalize_embeddings=True),
        )

        result = embedding[0].tolist()
        logger.debug(f"Embedded query: '{query[:50]}...'")
        return result

    async def close(self):
        """Close the client (release model from memory)."""
        if self._model is not None:
            del self._model
            self._model = None
            logger.info("BGE model released from memory")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
