#!/usr/bin/env python
"""Test Docling PDF parse only (no arXiv, no ingest).

Examples:
  uv run python scripts/test_pdf_parse.py --pdf path/to/file.pdf
  uv run python scripts/test_pdf_parse.py              # uses a generated sample PDF
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def make_sample_pdf(path: Path) -> Path:
    """Write a small multi-section PDF for smoke-testing Docling."""
    content = b"""BT /F1 16 Tf 50 750 Td (Introduction) Tj ET
BT /F1 12 Tf 50 720 Td (This paper studies attention mechanisms in transformers.) Tj ET
BT /F1 12 Tf 50 700 Td (We propose a hybrid retrieval method for scientific documents.) Tj ET
BT /F1 16 Tf 50 650 Td (Method) Tj ET
BT /F1 12 Tf 50 620 Td (The model encodes queries and passages into dense vectors.) Tj ET
BT /F1 16 Tf 50 570 Td (Conclusion) Tj ET
BT /F1 12 Tf 50 540 Td (Experiments show improved recall on arXiv papers.) Tj ET
"""
    stream = content
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        + f"4 0 obj<</Length {len(stream)}>>stream\n".encode()
        + stream
        + b"\nendstream\nendobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\ntrailer<</Size 6/Root 1 0 R>>\n%%EOF\n"
    )
    path.write_bytes(pdf)
    return path


async def parse_with_project_service(pdf_path: Path) -> None:
    from src.services.pdf_parser.factory import make_pdf_parser_service

    parser = make_pdf_parser_service()
    print(f"Parser limits: max_pages={parser.docling_parser.max_pages}, max_file_mb={parser.docling_parser.max_file_size_bytes / 1024 / 1024:.0f}")
    result = await parser.parse_pdf(pdf_path)
    if not result:
        print("FAIL: parser returned None")
        return
    print("OK: parsed")
    print(f"  sections: {len(result.sections)}")
    for s in result.sections[:5]:
        print(f"    - [{s.title[:60]}] {len(s.content)} chars")
    print(f"  raw_text: {len(result.raw_text or '')} chars")
    print(f"  parser_used: {result.parser_used}")
    print(f"  preview: {(result.raw_text or '')[:180]!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Test Docling PDF parsing locally")
    ap.add_argument("--pdf", help="Path to a PDF file")
    args = ap.parse_args()

    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"File not found: {pdf_path}")
            return 1
    else:
        pdf_path = Path(tempfile.gettempdir()) / "docling_parse_test.pdf"
        make_sample_pdf(pdf_path)
        print(f"Generated sample PDF: {pdf_path}")

    print(f"Testing parse: {pdf_path} ({pdf_path.stat().st_size} bytes)")
    asyncio.run(parse_with_project_service(pdf_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
