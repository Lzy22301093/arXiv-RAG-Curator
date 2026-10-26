import json
import logging
import time
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from src.dependencies import CacheDep, EmbeddingsDep, LLMClientDep, OpenSearchDep, RerankDep
from src.schemas.api.ask import AskRequest, AskResponse
from src.services.llm.prompts import RAGPromptBuilder

logger = logging.getLogger(__name__)

# Two separate routers - one for regular ask, one for streaming
ask_router = APIRouter(tags=["ask"])
stream_router = APIRouter(tags=["stream"])


async def _prepare_chunks_and_sources(
    request: AskRequest,
    opensearch_client,
    embeddings_service,
    rerank_service=None,
    rerank_candidates: int = 15,
) -> tuple[List[Dict], List[str], List[str]]:
    """Retrieve and prepare chunks for RAG with optional Jina rerank."""

    # Handle embeddings for hybrid search
    query_embedding = None
    if request.use_hybrid:
        try:
            query_embedding = await embeddings_service.embed_query(request.query)
            logger.info("Generated query embedding for hybrid search")
        except Exception as e:
            logger.warning(f"Failed to generate embeddings, falling back to BM25: {e}")

    use_rerank = bool(rerank_service) and getattr(request, "use_rerank", True)
    retrieve_size = request.top_k
    if use_rerank:
        retrieve_size = max(request.top_k, min(rerank_candidates, max(request.top_k * 5, request.top_k)))

    search_results = opensearch_client.search_unified(
        query=request.query,
        query_embedding=query_embedding,
        size=retrieve_size,
        from_=0,
        categories=request.categories,
        use_hybrid=request.use_hybrid and query_embedding is not None,
        min_score=0.0,
    )

    hits = list(search_results.get("hits", []))

    if use_rerank and len(hits) > 1:
        try:
            hits = await rerank_service.rerank_items(
                query=request.query,
                items=hits,
                top_n=request.top_k,
                text_key="chunk_text",
            )
            logger.info(f"Reranked {len(search_results.get('hits', []))} candidates -> {len(hits)} chunks")
        except Exception as e:
            logger.warning(f"Rerank failed, falling back to hybrid order: {e}")
            hits = hits[: request.top_k]
    else:
        hits = hits[: request.top_k]

    # Extract essential data for LLM
    chunks = []
    arxiv_ids = []
    sources_set = set()

    for hit in hits:
        arxiv_id = hit.get("arxiv_id", "")

        # Minimal chunk data for LLM
        chunks.append(
            {
                "arxiv_id": arxiv_id,
                "chunk_text": hit.get("chunk_text", hit.get("abstract", "")),
            }
        )

        if arxiv_id:
            arxiv_ids.append(arxiv_id)
            arxiv_id_clean = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
            sources_set.add(f"https://arxiv.org/pdf/{arxiv_id_clean}.pdf")

    return chunks, list(sources_set), arxiv_ids


@ask_router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    opensearch_client: OpenSearchDep,
    embeddings_service: EmbeddingsDep,
    llm_client: LLMClientDep,
    cache_client: CacheDep,
    rerank_service: RerankDep,
) -> AskResponse:
    """Clean RAG endpoint with exact match caching."""

    start_time = time.time()

    try:
        # Check exact cache first
        cached_response = None
        if cache_client:
            try:
                cached_response = await cache_client.find_cached_response(request)
                if cached_response:
                    logger.info("Returning cached response for exact query match")
                    return cached_response
            except Exception as e:
                logger.warning(f"Cache check failed, proceeding with normal flow: {e}")

        # Retrieve chunks
        chunks, sources, _ = await _prepare_chunks_and_sources(
            request,
            opensearch_client,
            embeddings_service,
            rerank_service=rerank_service,
        )

        if not chunks:
            # No documents found - use LLM directly without RAG context
            logger.info("No chunks found, using LLM directly without RAG context")
            rag_response = await llm_client.generate_rag_answer(
                query=request.query,
                chunks=[],  # Empty chunks - LLM will answer from general knowledge
                model=request.model,
            )
            answer = rag_response.get("answer", "Unable to generate answer")

            response = AskResponse(
                query=request.query,
                answer=answer,
                sources=[],
                chunks_used=0,
                search_mode="no-context",
            )
            return response

        # Build prompt
        prompt_builder = RAGPromptBuilder()
        try:
            prompt_data = prompt_builder.create_structured_prompt(request.query, chunks)
            final_prompt = prompt_data["prompt"]
        except Exception:
            final_prompt = prompt_builder.create_rag_prompt(request.query, chunks)

        # Generate answer
        rag_response = await llm_client.generate_rag_answer(query=request.query, chunks=chunks, model=request.model)
        answer = rag_response.get("answer", "Unable to generate answer")

        # Prepare response
        response = AskResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            chunks_used=len(chunks),
            search_mode="bm25" if not request.use_hybrid else "hybrid",
        )

        # Store response in exact match cache
        if cache_client:
            try:
                await cache_client.store_response(request, response)
            except Exception as e:
                logger.warning(f"Failed to store response in cache: {e}")

        return response

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@stream_router.post("/stream")
async def ask_question_stream(
    request: AskRequest,
    opensearch_client: OpenSearchDep,
    embeddings_service: EmbeddingsDep,
    llm_client: LLMClientDep,
    cache_client: CacheDep,
    rerank_service: RerankDep,
) -> StreamingResponse:
    """Clean streaming RAG endpoint."""

    async def generate_stream():
        start_time = time.time()

        try:
            # Check exact cache first
            if cache_client:
                try:
                    cached_response = await cache_client.find_cached_response(request)
                    if cached_response:
                        logger.info("Returning cached response for exact streaming query match")

                        # Send metadata first (same format as non-cached)
                        metadata_response = {
                            "sources": cached_response.sources,
                            "chunks_used": cached_response.chunks_used,
                            "search_mode": cached_response.search_mode,
                        }
                        yield f"data: {json.dumps(metadata_response)}\n\n"

                        # Stream the cached response in chunks
                        for chunk in cached_response.answer.split():
                            yield f"data: {json.dumps({'chunk': chunk + ' '})}\n\n"

                        # Send completion signal with just the final answer
                        yield f"data: {json.dumps({'answer': cached_response.answer, 'done': True})}\n\n"
                        return
                except Exception as e:
                    logger.warning(f"Cache check failed, proceeding with normal flow: {e}")

            # Retrieve chunks
            chunks, sources, _ = await _prepare_chunks_and_sources(
                request,
                opensearch_client,
                embeddings_service,
                rerank_service=rerank_service,
            )

            if not chunks:
                yield f"data: {json.dumps({'answer': 'No relevant information found.', 'sources': [], 'done': True})}\n\n"
                return

            # Send metadata first
            search_mode = "bm25" if not request.use_hybrid else "hybrid"
            metadata_response = {"sources": sources, "chunks_used": len(chunks), "search_mode": search_mode}
            yield f"data: {json.dumps(metadata_response)}\n\n"

            # Build prompt
            prompt_builder = RAGPromptBuilder()
            final_prompt = prompt_builder.create_rag_prompt(request.query, chunks)

            # Stream generation
            full_response = ""
            async for chunk in llm_client.generate_rag_answer_stream(
                query=request.query, chunks=chunks, model=request.model
            ):
                if chunk.get("response"):
                    text_chunk = chunk["response"]
                    full_response += text_chunk
                    yield f"data: {json.dumps({'chunk': text_chunk})}\n\n"

                if chunk.get("done", False):
                    yield f"data: {json.dumps({'answer': full_response, 'done': True})}\n\n"
                    break

            # Store response in exact match cache
            if cache_client and full_response:
                try:
                    search_mode = "bm25" if not request.use_hybrid else "hybrid"
                    response_to_cache = AskResponse(
                        query=request.query,
                        answer=full_response,
                        sources=sources,
                        chunks_used=len(chunks),
                        search_mode=search_mode,
                    )
                    await cache_client.store_response(request, response_to_cache)
                except Exception as e:
                    logger.warning(f"Failed to store streaming response in cache: {e}")

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(), media_type="text/plain", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
