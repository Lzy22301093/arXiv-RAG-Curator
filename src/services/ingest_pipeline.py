"""Manual / UI paper ingestion pipeline."""

import logging
import time
from typing import Any, Dict, List, Optional

from src.db.factory import make_database
from src.services.arxiv.factory import make_arxiv_client
from src.services.indexing.factory import make_hybrid_indexing_service
from src.services.metadata_fetcher import make_metadata_fetcher
from src.services.pdf_parser.factory import make_pdf_parser_service

logger = logging.getLogger(__name__)


async def run_ingest(
    categories: Optional[List[str]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    max_results: int = 15,
    process_pdfs: bool = False,
    index_to_opensearch: bool = True,
) -> Dict[str, Any]:
    """Fetch arXiv papers, store metadata, optionally parse PDFs and index.

    :param categories: arXiv categories, e.g. ["cs.AI", "cs.LG"]
    :param from_date: YYYYMMDD
    :param to_date: YYYYMMDD
    :param max_results: max papers to fetch
    :param process_pdfs: download/parse PDFs (slower; needs docling/HF)
    :param index_to_opensearch: chunk + embed + write OpenSearch
    :returns: ingest statistics
    """
    categories = [c.strip() for c in (categories or []) if c.strip()]

    started_at = time.monotonic()

    arxiv_client = make_arxiv_client()
    pdf_parser = make_pdf_parser_service()
    database = make_database()
    metadata_fetcher = make_metadata_fetcher(arxiv_client, pdf_parser)

    result: Dict[str, Any] = {
        "papers_fetched": 0,
        "pdfs_downloaded": 0,
        "pdfs_parsed": 0,
        "papers_stored": 0,
        "papers_indexed": 0,
        "chunks_indexed": 0,
        "categories": categories or [arxiv_client.search_category],
        "from_date": from_date,
        "to_date": to_date,
        "errors": [],
        "processing_time": 0,
    }

    with database.get_session() as session:
        fetch_stats = await metadata_fetcher.fetch_and_process_papers(
            max_results=max_results,
            from_date=from_date,
            to_date=to_date,
            process_pdfs=process_pdfs,
            store_to_db=True,
            db_session=session,
            categories=categories or None,
        )
        result.update({k: fetch_stats.get(k, result.get(k)) for k in fetch_stats if k != "errors"})
        result["errors"].extend(fetch_stats.get("errors") or [])

        if index_to_opensearch and result.get("papers_stored", 0) > 0:
            from sqlalchemy import desc
            from src.models.paper import Paper

            papers = session.query(Paper).order_by(desc(Paper.created_at)).limit(result["papers_stored"]).all()
            papers_data = [
                {
                    "id": str(p.id),
                    "arxiv_id": p.arxiv_id,
                    "title": p.title,
                    "authors": p.authors,
                    "abstract": p.abstract,
                    "categories": p.categories,
                    "published_date": p.published_date,
                    "raw_text": p.raw_text,
                    "sections": p.sections,
                }
                for p in papers
            ]
            try:
                indexer = make_hybrid_indexing_service()
                stats = await indexer.index_papers_batch(papers=papers_data, replace_existing=True)
                result["papers_indexed"] = stats.get("papers_processed", 0)
                result["chunks_indexed"] = stats.get("total_chunks_indexed", 0)
                index_errors = stats.get("errors") or []
                if index_errors:
                    result["errors"].extend(str(e) for e in index_errors[:10])
                    if result["chunks_indexed"] == 0:
                        result["errors"].append(
                            "所有片段索引失败 · 0 chunks indexed — 嵌入服务 api.jina.ai 很可能不可达。"
                            "Embedding API likely unreachable: check network/proxy or configure local BGE (BGE_*)."
                        )
            except Exception as e:
                logger.error(f"Indexing failed: {e}")
                result["errors"].append(f"Indexing failed: {e}")

    # Cover the whole pipeline (fetch + store + index), not just the fetch step
    result["processing_time"] = round(time.monotonic() - started_at, 3)

    return result


def list_papers_from_db(
    limit: int = 50,
    offset: int = 0,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """List ingested papers for UI/CLI.

    :param limit: page size
    :param offset: page offset
    :param keyword: filter by title/abstract substring
    :param category: filter by category substring
    """
    from sqlalchemy import or_
    from src.models.paper import Paper
    from src.repositories.paper import PaperRepository

    database = make_database()
    with database.get_session() as session:
        repo = PaperRepository(session)
        q = session.query(Paper)
        if keyword:
            like = f"%{keyword}%"
            q = q.filter(or_(Paper.title.ilike(like), Paper.abstract.ilike(like), Paper.arxiv_id.ilike(like)))

        total = q.count()
        # Fetch a larger window when filtering by category in Python
        fetch_limit = limit + offset + 50 if category else limit
        fetch_offset = 0 if category else offset
        rows = q.order_by(Paper.published_date.desc()).limit(fetch_limit).offset(fetch_offset).all()

        items = []
        for p in rows:
            cats = p.categories or []
            if category and category.lower() not in ",".join(str(c) for c in cats).lower():
                continue
            items.append(
                {
                    "arxiv_id": p.arxiv_id,
                    "title": p.title,
                    "authors": p.authors,
                    "categories": cats,
                    "published_date": p.published_date.isoformat() if p.published_date else "",
                    "abstract": (p.abstract or "")[:300],
                    "pdf_url": p.pdf_url or f"https://arxiv.org/pdf/{p.arxiv_id}.pdf",
                    "abs_url": f"https://arxiv.org/abs/{p.arxiv_id}",
                    "local_pdf_url": f"/api/v1/papers/{p.arxiv_id}/pdf",
                    "pdf_processed": bool(p.pdf_processed),
                }
            )

        if category:
            items = items[offset : offset + limit]

        return {
            "total": total if not category else len(items),
            "limit": limit,
            "offset": offset,
            "items": items,
            "stats": repo.get_processing_stats(),
        }
