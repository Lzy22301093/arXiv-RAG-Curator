import logging
from typing import Optional

import lark_oapi as lark
from fastapi import FastAPI, Request
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody
from src.schemas.api.ask import AskRequest, AskResponse

logger = logging.getLogger(__name__)


class FeishuBot:
    """Feishu (Lark) bot for Q&A via webhook."""

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        verification_token: str,
        encrypt_key: str,
        opensearch_client,
        embeddings_client,
        llm_client,
        cache_client=None,
    ):
        """Initialize bot with required services."""
        self.app_id = app_id
        self.app_secret = app_secret
        self.verification_token = verification_token
        self.encrypt_key = encrypt_key
        self.opensearch = opensearch_client
        self.embeddings = embeddings_client
        self.llm = llm_client
        self.cache = cache_client
        self.client: Optional[lark.Client] = None

    def create_app(self) -> FastAPI:
        """Create a FastAPI sub-app with webhook routes."""
        app = FastAPI(title="Feishu Bot Webhook")

        # Build lark event handler
        event_handler = (
            lark.EventDispatcherHandler.builder(
                self.verification_token,
                self.encrypt_key,
            )
            .register_p2_im_message_receive_v1(self._on_message)
            .build()
        )

        # Mount lark webhook handler
        from lark_oapi.adapter.fastapi import get_lark_handler

        app.post("/")(get_lark_handler(event_handler))

        return app

    async def start(self) -> None:
        """Start the bot (initialize lark client)."""
        logger.info("Starting Feishu bot...")
        self.client = (
            lark.Client.builder().app_id(self.app_id).app_secret(self.app_secret).log_level(lark.LogLevel.WARNING).build()
        )
        logger.info("Feishu bot started successfully")

    async def stop(self) -> None:
        """Stop the bot."""
        self.client = None
        logger.info("Feishu bot stopped")

    def _on_message(self, data) -> None:
        """Handle incoming message events from Feishu."""
        try:
            message = data.event.message
            chat_type = message.chat_type

            # Only handle text messages
            if message.message_type != "text":
                return

            import json

            content = json.loads(message.content)
            text = content.get("text", "").strip()

            if not text:
                return

            # Extract chat_id for reply
            chat_id = message.chat_id

            # Handle commands
            if text.startswith("/"):
                self._handle_command(chat_id, text)
            else:
                # For direct messages or @mentions, handle as question
                if chat_type == "p2p":
                    self._handle_question(chat_id, text)
                elif chat_type == "group":
                    # In group chat, only respond when @mentioned
                    mentions = message.mentions or []
                    if mentions:
                        # Remove @mention prefix from text
                        for mention in mentions:
                            text = text.replace(mention.key, "").strip()
                        if text:
                            self._handle_question(chat_id, text)

        except Exception as e:
            logger.error(f"Failed to handle message: {e}", exc_info=True)

    def _handle_command(self, chat_id: str, text: str) -> None:
        """Handle bot commands."""
        parts = text.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "/start":
            self._send_text(
                chat_id,
                "欢迎使用 arXiv Paper Curator!\n\n"
                "我可以回答计算机科学论文相关的问题，并提供来源链接。\n\n"
                "命令:\n"
                "/help - 显示帮助信息\n"
                "/search <关键词> - 搜索论文",
            )
        elif command == "/help":
            self._send_text(
                chat_id,
                "发送任何关于计算机科学论文的问题。\n\n"
                "示例:\n"
                "- 什么是 Transformer 架构？\n"
                "- BERT 是如何工作的？\n"
                "- 解释注意力机制\n\n"
                "使用 /search 搜索特定论文。",
            )
        elif command == "/search":
            if not args:
                self._send_text(chat_id, "用法: /search <关键词>\n示例: /search neural networks")
                return
            self._handle_search(chat_id, args)
        else:
            self._send_text(chat_id, f"未知命令: {command}\n使用 /help 查看可用命令。")

    def _handle_search(self, chat_id: str, query: str) -> None:
        """Search papers and return results."""
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self._search_papers(query))
                    results = future.result(timeout=30)
            else:
                results = asyncio.run(self._search_papers(query))
            self._send_text(chat_id, results)
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            self._send_text(chat_id, f"搜索失败: {str(e)}")

    async def _search_papers(self, query: str) -> str:
        """Search papers via OpenSearch."""
        query_embedding = await self.embeddings.embed_query(query)
        results = self.opensearch.search_unified(
            query=query,
            query_embedding=query_embedding,
            size=10,
            use_hybrid=True,
        )

        hits = results.get("hits", [])
        if not hits:
            return "未找到相关论文，请尝试不同的关键词。"

        # Deduplicate by arxiv_id
        seen_ids = set()
        unique_papers = []
        for hit in hits:
            arxiv_id = hit.get("arxiv_id", "")
            if arxiv_id and arxiv_id not in seen_ids:
                seen_ids.add(arxiv_id)
                unique_papers.append(hit)
            if len(unique_papers) >= 5:
                break

        response = f"找到 {len(unique_papers)} 篇论文:\n\n"
        for idx, hit in enumerate(unique_papers, 1):
            title = hit.get("title", "Untitled")
            arxiv_id = hit.get("arxiv_id", "")
            url = f"https://arxiv.org/abs/{arxiv_id}"
            response += f"{idx}. {title}\n{url}\n\n"

        return response.strip()

    def _handle_question(self, chat_id: str, query: str) -> None:
        """Handle user questions via RAG pipeline."""
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self._get_rag_response(query))
                    answer = future.result(timeout=60)
            else:
                answer = asyncio.run(self._get_rag_response(query))
            self._send_text(chat_id, answer)
        except Exception as e:
            logger.error(f"Question handling failed: {e}", exc_info=True)
            self._send_text(chat_id, f"处理问题时出错: {str(e)}")

    async def _get_rag_response(self, query: str) -> str:
        """Run RAG pipeline and return formatted answer (DeepSeek API generation)."""

        # Check cache
        ask_request = AskRequest(query=query, top_k=3, use_hybrid=True)
        if self.cache:
            try:
                cached_response = await self.cache.find_cached_response(ask_request)
                if cached_response:
                    return self._format_answer(cached_response)
            except Exception as e:
                logger.warning(f"Cache lookup failed: {e}")

        # Generate embeddings
        query_embedding = None
        try:
            query_embedding = await self.embeddings.embed_query(query)
        except Exception as e:
            logger.warning(f"Failed to generate embeddings: {e}")

        # Search OpenSearch
        search_results = self.opensearch.search_unified(
            query=query,
            query_embedding=query_embedding,
            size=ask_request.top_k,
            use_hybrid=ask_request.use_hybrid and query_embedding is not None,
        )

        # Extract chunks and sources
        chunks = []
        sources_set = set()
        for hit in search_results.get("hits", []):
            arxiv_id = hit.get("arxiv_id", "")
            chunks.append(
                {
                    "arxiv_id": arxiv_id,
                    "chunk_text": hit.get("chunk_text", hit.get("abstract", "")),
                }
            )
            if arxiv_id:
                arxiv_id_clean = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
                sources_set.add(f"https://arxiv.org/pdf/{arxiv_id_clean}.pdf")

        sources = list(sources_set)

        if not chunks:
            return "未找到相关论文，请换个方式描述你的问题。"

        # Generate answer via DeepSeek API (LLMClient)
        result = await self.llm.generate_rag_answer(query=query, chunks=chunks)
        answer = result.get("answer", "") if isinstance(result, dict) else str(result)

        # Build response
        response = AskResponse(query=query, answer=answer, sources=sources, chunks_used=len(chunks), search_mode="hybrid")

        # Cache it
        if self.cache:
            try:
                await self.cache.store_response(ask_request, response)
            except Exception:
                pass

        return self._format_answer(response)

    def _format_answer(self, response: AskResponse) -> str:
        """Format answer for Feishu message."""
        message = f"Answer:\n{response.answer}\n"

        if response.sources:
            message += "\nSources:\n"
            for idx, source_url in enumerate(response.sources[:5], 1):
                arxiv_id = source_url.split("/")[-1].replace(".pdf", "")
                message += f"{idx}. https://arxiv.org/abs/{arxiv_id}\n"

        return message.strip()

    def _send_text(self, chat_id: str, text: str) -> None:
        """Send a text message to a Feishu chat."""
        if not self.client:
            logger.error("Feishu client not initialized")
            return

        import json

        body = CreateMessageRequestBody.builder()
        body.receive_id(chat_id)
        body.msg_type("text")
        body.content(json.dumps({"text": text}))

        request = CreateMessageRequest.builder().receive_id_type("chat_id").request_body(body.build()).build()

        response = self.client.im.v1.message.create(request)
        if not response.success():
            logger.error(f"Failed to send message: code={response.code}, msg={response.msg}")
