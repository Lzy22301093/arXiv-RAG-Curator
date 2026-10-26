"""Inspect PDF parse + chunk results for interview/QA.

Usage:
  uv run python scripts/inspect_pdf_parse.py <path-to.pdf>
  uv run python scripts/inspect_pdf_parse.py <path-to.pdf> --out data/parse_preview

What you see:
  1. PdfContent: sections titles/lengths, raw_text stats
  2. TextChunker: each chunk's section_title / word_count / first 200 chars
  3. Optional dump: markdown-ish text files for manual reading
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Ensure project root is importable when run as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.pdf_parser.factory import make_pdf_parser_service  # noqa: E402
from src.services.indexing.text_chunker import TextChunker  # noqa: E402


def _hr(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


async def inspect(pdf_path: Path, out_dir: Path | None) -> None:
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    parser = make_pdf_parser_service()
    chunker = TextChunker(chunk_size=600, overlap_size=100, min_chunk_size=100)

    _hr("1. RAW PARSE (DoclingParser → PdfContent)")
    content = await parser.parse_pdf(pdf_path)
    if content is None:
        print("parse_pdf returned None (likely size/page limit skip)")
        return

    print(f"parser_used   : {content.parser_used}")
    print(f"raw_text chars: {len(content.raw_text):,}")
    print(f"raw_text words: {len(content.raw_text.split()):,}")
    print(f"sections      : {len(content.sections)}")
    print(f"figures       : {len(content.figures)}  (code currently drops these)")
    print(f"tables        : {len(content.tables)}   (code currently drops these)")
    print(f"references    : {len(content.references)}")

    _hr("2. SECTIONS (after parse, before chunk filter)")
    for i, sec in enumerate(content.sections):
        words = len(sec.content.split())
        title = sec.title.replace("\n", " ")[:60]
        print(f"[{i:02d}] {words:5d}w  {title}")
        # show first line of content for leftover header/footer check
        first_line = sec.content.strip().splitlines()[0][:80] if sec.content.strip() else ""
        if first_line:
            print(f"      ↳ {first_line}")

    _hr("3. CHUNKS (TextChunker.chunk_paper)")
    # Use arXiv-like metadata for realistic header (title+abstract)
    title = content.sections[0].title if content.sections else pdf_path.stem
    abstract = ""
    # Prefer abstract-like early section if present
    for sec in content.sections:
        t = sec.title.lower()
        if "abstract" in t or t == "content":
            abstract = sec.content[:800]
            break
    if not abstract and content.raw_text:
        abstract = " ".join(content.raw_text.split()[:120])

    chunks = chunker.chunk_paper(
        title=title,
        abstract=abstract,
        arxiv_id="INSPECT",
        paper_id="inspect-1",
        full_text=content.raw_text,
        sections=[{"title": s.title, "content": s.content} for s in content.sections],
    )
    print(f"total chunks  : {len(chunks)}")
    for i, ch in enumerate(chunks):
        meta = ch.metadata
        st = (meta.section_title or "-")[:40]
        preview = ch.text[:200].replace("\n", " / ")
        print(f"\n--- chunk[{i}] words={meta.word_count} section={st} ---")
        print(preview + ("..." if len(ch.text) > 200 else ""))

    _hr("4. HEURISTIC CHECKS (what interviewers care about)")
    sample = content.raw_text[:20000]
    leaks = []
    for kw in ("arXiv:", "preprint", "University", "gmail.com", "@", "http"):
        if kw.lower() in sample.lower():
            leaks.append(kw)
    print(f"possible leftover markers in raw_text head: {leaks or 'none in first 20k chars'}")
    tableish = sum(1 for line in content.raw_text.splitlines() if line.count("|") >= 3 or line.count("\t") >= 3)
    print(f"lines that look like tables (| or tabs): {tableish}")
    print("note: project drops structured tables (tables=[]); table cells may appear only in raw_text.")

    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "raw_text.txt").write_text(content.raw_text, encoding="utf-8")
        sections_md = "\n\n".join(f"## {s.title}\n\n{s.content}" for s in content.sections)
        (out_dir / "sections.md").write_text(sections_md, encoding="utf-8")
        chunks_md = "\n\n".join(
            f"## chunk[{i}] ({c.metadata.word_count}w, {c.metadata.section_title or '-'})\n\n{c.text}"
            for i, c in enumerate(chunks)
        )
        (out_dir / "chunks.md").write_text(chunks_md, encoding="utf-8")
        _hr(f"5. DUMPED to {out_dir}")
        for p in sorted(out_dir.iterdir()):
            print(f"  {p.name:20s} {p.stat().st_size:,} bytes")


def main() -> None:
    ap = argparse.ArgumentParser(description="Inspect PDF parse + chunk output")
    ap.add_argument("pdf", type=Path, help="Path to a PDF file")
    ap.add_argument("--out", type=Path, default=None, help="Optional directory to dump text previews")
    args = ap.parse_args()
    asyncio.run(inspect(args.pdf, args.out))


if __name__ == "__main__":
    main()
