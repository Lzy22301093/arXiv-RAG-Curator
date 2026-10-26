"""Paper ingest + library browsing API (used by Gradio and scripts)."""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from src.config import get_settings
from src.exceptions import ArxivAPIException, PipelineException
from src.schemas.api.library import IngestRequest, IngestResponse, PaperListResponse
from src.services.ingest_pipeline import list_papers_from_db, run_ingest

logger = logging.getLogger(__name__)

library_router = APIRouter(prefix="/api/v1", tags=["library"])


def _local_pdf_path(arxiv_id: str) -> Path:
    """Resolve cached PDF path used by ArxivClient.download_pdf."""
    settings = get_settings()
    cache_dir = Path(settings.arxiv.pdf_cache_dir)
    # Same filename convention as ArxivClient._get_pdf_path
    safe = arxiv_id.replace("/", "_")
    if not safe.lower().endswith(".pdf"):
        safe = f"{safe}.pdf"
    return cache_dir / safe


@library_router.post("/ingest", response_model=IngestResponse)
async def ingest_papers(request: IngestRequest) -> IngestResponse:
    """Fetch papers from arXiv, store, optionally parse PDFs and index."""
    try:
        result = await run_ingest(
            categories=request.categories,
            from_date=request.from_date,
            to_date=request.to_date,
            max_results=request.max_results,
            process_pdfs=request.process_pdfs,
            index_to_opensearch=request.index_to_opensearch,
        )
        return IngestResponse(**result)
    except (ArxivAPIException, PipelineException) as e:
        msg = str(e)
        logger.error(f"Ingest failed: {msg}")
        if "429" in msg or "Too Many Requests" in msg:
            raise HTTPException(
                status_code=429,
                detail="arXiv 接口限流（429）。请等 1–3 分钟再试；不要连续猛点抓取。",
            ) from e
        raise HTTPException(status_code=502, detail=f"抓取失败: {msg}") from e
    except Exception as e:
        logger.exception("Ingest unexpected error")
        raise HTTPException(status_code=500, detail=f"服务内部错误: {e}") from e


@library_router.get("/papers", response_model=PaperListResponse)
async def list_papers(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    keyword: str | None = Query(None, description="Filter title/abstract/id"),
    category: str | None = Query(None, description="Filter category substring"),
) -> PaperListResponse:
    """List ingested papers with arXiv links."""
    data = list_papers_from_db(limit=limit, offset=offset, keyword=keyword, category=category)
    return PaperListResponse(**data)


@library_router.get("/papers/{arxiv_id}/pdf")
async def download_paper_pdf(arxiv_id: str) -> FileResponse:
    """Serve the locally cached PDF (source file) for a paper."""
    # Strip version-only confusion: allow both 2610.2863v1 and 2610.2863
    candidates = [_local_pdf_path(arxiv_id), _local_pdf_path(arxiv_id.split("v")[0])]
    path = next((p for p in candidates if p.is_file()), None)
    if not path:
        # Fallback: glob cache dir
        settings = get_settings()
        cache_dir = Path(settings.arxiv.pdf_cache_dir)
        base = arxiv_id.split("v")[0]
        matches = list(cache_dir.glob(f"{base}*.pdf")) if cache_dir.is_dir() else []
        if matches:
            path = matches[0]
    if not path or not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"本地未找到 PDF（可能未勾选解析 PDF 下载）。缓存目录: {settings.arxiv.pdf_cache_dir}",
        )
    # Inline disposition so the browser opens the local PDF on click (same GET route)
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=path.name,
        content_disposition_type="inline",
    )
