from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    categories: List[str] = Field(default_factory=lambda: ["cs.AI"], description="arXiv categories, e.g. cs.AI")
    from_date: Optional[str] = Field(None, description="YYYYMMDD, optional")
    to_date: Optional[str] = Field(None, description="YYYYMMDD, optional")
    max_results: int = Field(15, ge=1, le=200)
    process_pdfs: bool = Field(False, description="Download/parse PDFs (slower)")
    index_to_opensearch: bool = Field(True)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "categories": ["cs.AI", "cs.LG"],
                    "from_date": "20260701",
                    "to_date": "20260715",
                    "max_results": 20,
                    "process_pdfs": False,
                }
            ]
        }
    }


class IngestResponse(BaseModel):
    papers_fetched: int = 0
    pdfs_downloaded: int = 0
    pdfs_parsed: int = 0
    papers_stored: int = 0
    papers_indexed: int = 0
    chunks_indexed: int = 0
    categories: List[str] = Field(default_factory=list)
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    processing_time: float = 0


class PaperListItem(BaseModel):
    arxiv_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    published_date: str = ""
    abstract: str = ""
    pdf_url: str = ""
    abs_url: str = ""
    local_pdf_url: str = ""
    pdf_processed: bool = False


class PaperListResponse(BaseModel):
    total: int = 0
    limit: int = 50
    offset: int = 0
    items: List[PaperListItem] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)
