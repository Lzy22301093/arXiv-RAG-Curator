#!/usr/bin/env python
"""Manual arXiv paper ingest CLI.

Examples:
  uv run python scripts/ingest.py --categories cs.AI --max 15
  uv run python scripts/ingest.py --categories cs.AI,cs.LG --from 20260701 --to 20260715 --max 30
  uv run python scripts/ingest.py --list --limit 20
  uv run python scripts/ingest.py --categories cs.CV --no-pdf --no-index
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Allow running from repo root without install
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.ingest_pipeline import list_papers_from_db, run_ingest  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest arXiv papers into PostgreSQL + OpenSearch")
    p.add_argument("--categories", default="cs.AI", help="Comma-separated arXiv categories (default: cs.AI)")
    p.add_argument("--from", dest="from_date", default=None, help="Start date YYYYMMDD")
    p.add_argument("--to", dest="to_date", default=None, help="End date YYYYMMDD")
    p.add_argument("--max", dest="max_results", type=int, default=15, help="Max papers (default: 15)")
    p.add_argument("--no-pdf", action="store_true", help="Skip PDF download/parse (faster)")
    p.add_argument("--no-index", action="store_true", help="Skip OpenSearch indexing")
    p.add_argument("--list", action="store_true", help="List stored papers instead of ingesting")
    p.add_argument("--limit", type=int, default=20, help="List limit")
    p.add_argument("--keyword", default=None, help="Filter keyword for --list")
    p.add_argument("--category-filter", default=None, help="Filter category for --list")
    return p.parse_args()


def print_papers(data: dict) -> None:
    print(f"Total (approx): {data.get('total')}")
    for i, item in enumerate(data.get("items") or [], 1):
        print(f"\n{i}. {item.get('title')}")
        print(f"   {item.get('arxiv_id')}  |  {item.get('published_date')}  |  {','.join(item.get('categories') or [])}")
        print(f"   {item.get('abs_url')}")
    print(f"\nStats: {data.get('stats')}")


async def main() -> int:
    args = parse_args()

    if args.list:
        data = list_papers_from_db(
            limit=args.limit,
            keyword=args.keyword,
            category=args.category_filter,
        )
        print_papers(data)
        return 0

    categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    print(
        f"Ingesting categories={categories} from={args.from_date} to={args.to_date} "
        f"max={args.max_results} pdf={not args.no_pdf} index={not args.no_index}"
    )

    result = await run_ingest(
        categories=categories,
        from_date=args.from_date,
        to_date=args.to_date,
        max_results=args.max_results,
        process_pdfs=not args.no_pdf,
        index_to_opensearch=not args.no_index,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if not result.get("errors") else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
