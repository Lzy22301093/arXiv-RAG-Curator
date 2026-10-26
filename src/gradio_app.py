"""arXiv Paper Curator — Notion-style Gradio workspace.

Backend contracts unchanged:
  POST /api/v1/stream
  POST /api/v1/ingest   (YYYYMMDD via calendar form)
  GET  /api/v1/papers
  GET  /api/v1/papers/{arxiv_id}/pdf  (local cached PDF, open on click)
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
import re
import time
from datetime import datetime
from typing import Any, Iterator

import gradio as gr
import httpx

try:
    from src.gradio_styles import (
        CORE_CSS,
        HEAD_HTML,
        TAB_JS,
        answer_html,
        build_theme,
        footer_html,
        ingest_log_html,
        ingest_running_html,
        page_head,
        paper_list_html,
        placeholder_answer,
        sources_html,
        top_bar,
    )
except ImportError:
    from gradio_styles import (  # type: ignore
        CORE_CSS,
        HEAD_HTML,
        TAB_JS,
        answer_html,
        build_theme,
        footer_html,
        ingest_log_html,
        ingest_running_html,
        page_head,
        paper_list_html,
        placeholder_answer,
        sources_html,
        top_bar,
    )

logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_MODEL = "deepseek-flash"

# Ingest can legitimately run minutes (15 papers × embedding), so keep the HTTP
# timeout generous; the running-status card keeps the user informed meanwhile.
INGEST_TIMEOUT = httpx.Timeout(600.0, connect=10.0)
INGEST_TICK_SECONDS = 2.0


# ---------------------------------------------------------------------------
# Date helpers (calendar → API YYYYMMDD)
# ---------------------------------------------------------------------------


def _to_yyyymmdd(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d")
    s = str(value).strip()
    if not s:
        return ""
    if s.isdigit() and len(s) == 8:
        return s
    m = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        return f"{m.group(1)}{int(m.group(2)):02d}{int(m.group(3)):02d}"
    return s.replace("-", "").replace("/", "")[:8]


# ---------------------------------------------------------------------------
# Markdown → HTML
# ---------------------------------------------------------------------------


def _inline_md(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+?)`", r"<code>\1</code>", text)
    text = re.sub(
        r"\[([^\]]+?)\]\(([^)]+?)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        text,
    )
    return text


def markdown_to_html(md: str) -> str:
    if not md or not md.strip():
        return ""
    lines = md.split("\n")
    out: list[str] = []
    in_code = False
    in_list = False
    para: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if para:
            out.append("<p>" + _inline_md(" ".join(para)) + "</p>")
            para = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.rstrip("\n")
        if line.strip().startswith("```"):
            flush_para()
            close_list()
            if not in_code:
                out.append("<pre><code>")
                in_code = True
            else:
                out.append("</code></pre>")
                in_code = False
            continue
        if in_code:
            out.append(html.escape(line) + "\n")
            continue
        if not line.strip():
            flush_para()
            close_list()
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading:
            flush_para()
            close_list()
            level = min(3, max(1, len(heading.group(1))))
            out.append(f"<h{level}>{_inline_md(heading.group(2))}</h{level}>")
            continue
        if re.match(r"^\s*[-*+]\s+", line):
            flush_para()
            if not in_list:
                out.append("<ul>")
                in_list = True
            item = re.sub(r"^\s*[-*+]\s+", "", line)
            out.append(f"<li>{_inline_md(item)}</li>")
            continue
        if re.match(r"^\s*>\s?", line):
            flush_para()
            close_list()
            quote = re.sub(r"^\s*>\s?", "", line)
            out.append(f"<blockquote>{_inline_md(quote)}</blockquote>")
            continue
        close_list()
        para.append(line.strip())

    if in_code:
        out.append("</code></pre>")
    flush_para()
    close_list()
    return "".join(out)


# ---------------------------------------------------------------------------
# API handlers
# ---------------------------------------------------------------------------


async def stream_response(
    query: str, top_k: int = 3, use_hybrid: bool = True, model: str = DEFAULT_MODEL, categories: str = ""
) -> Iterator[str]:
    if not query or not query.strip():
        yield answer_html(
            '<div class="placeholder"><div class="title">请先输入问题 · Type a question first</div>'
            '<div class="desc">回答区正在等待输入 · Waiting for your query.</div></div>',
            error=True,
        )
        return

    category_list = [cat.strip() for cat in categories.split(",") if cat.strip()] if categories else None
    payload = {
        "query": query,
        "top_k": top_k,
        "use_hybrid": use_hybrid,
        "model": model,
        "categories": category_list,
    }

    yield answer_html(
        '<div class="placeholder"><div class="title">检索中 · Searching papers…</div>'
        '<div class="desc">正在检索片段并起草答案 · Retrieving chunks and drafting an answer.</div></div>',
        mode="hybrid" if use_hybrid else "vector",
        streaming=True,
    )

    try:
        url = f"{API_BASE_URL}/stream"
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload, headers={"Accept": "text/plain"}) as response:
                if response.status_code != 200:
                    yield answer_html(
                        f'<div class="placeholder"><div class="title">接口错误 · API error</div>'
                        f'<div class="desc">HTTP {response.status_code}</div></div>',
                        error=True,
                    )
                    return

                current_answer = ""
                sources: list[str] = []
                chunks_used: Any = ""
                search_mode = ""

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        data = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

                    if "error" in data:
                        yield answer_html(
                            f'<div class="placeholder"><div class="title">流式错误 · Stream error</div>'
                            f'<div class="desc">{html.escape(str(data["error"]))}</div></div>',
                            error=True,
                        )
                        return

                    if "sources" in data:
                        sources = data["sources"] or []
                        chunks_used = data.get("chunks_used", 0)
                        search_mode = data.get("search_mode", "unknown")

                    if "chunk" in data:
                        current_answer += data["chunk"]
                        yield answer_html(
                            markdown_to_html(current_answer),
                            mode=search_mode or ("hybrid" if use_hybrid else "vector"),
                            chunks=chunks_used if chunks_used != "" else "—",
                            source_count=len(sources) if sources else 0,
                            streaming=True,
                        ) + sources_html(sources)

                    if data.get("done", False):
                        final_answer = data.get("answer", current_answer)
                        if final_answer != current_answer:
                            current_answer = final_answer
                        body = markdown_to_html(current_answer) or "<p>未找到相关信息 · No relevant information found.</p>"
                        yield answer_html(
                            body,
                            mode=search_mode or ("hybrid" if use_hybrid else "vector"),
                            chunks=chunks_used if chunks_used != "" else "—",
                            source_count=len(sources) if sources else 0,
                            streaming=False,
                        ) + sources_html(sources)
                        return

                body = markdown_to_html(current_answer) or "<p>流意外结束 · Stream ended unexpectedly.</p>"
                yield answer_html(body, error=not bool(current_answer)) + sources_html(sources)

    except httpx.RequestError as e:
        yield answer_html(
            '<div class="placeholder"><div class="title">无法连接 API · Cannot reach API</div>'
            f'<div class="desc">期望地址 · Expected at {html.escape(API_BASE_URL)}. {html.escape(str(e))}</div></div>',
            error=True,
        )
    except Exception as e:  # noqa: BLE001
        yield answer_html(
            f'<div class="placeholder"><div class="title">未知错误 · Unexpected error</div>'
            f'<div class="desc">{html.escape(str(e))}</div></div>',
            error=True,
        )


async def run_ingest_ui(
    categories: str,
    from_date: Any,
    to_date: Any,
    max_results: int,
    process_pdfs: bool,
):
    """Generator: yields a live "ingesting" card (with elapsed seconds) while the
    API call runs, then the final summary — plus button state updates."""
    cats = [c.strip() for c in (categories or "cs.AI").split(",") if c.strip()]
    from_s = _to_yyyymmdd(from_date)
    to_s = _to_yyyymmdd(to_date)
    payload = {
        "categories": cats,
        "from_date": from_s or None,
        "to_date": to_s or None,
        "max_results": int(max_results),
        "process_pdfs": bool(process_pdfs),
        "index_to_opensearch": True,
    }

    btn_running = gr.update(value="抓取中 · Running…", variant="secondary", interactive=False)
    btn_idle = gr.update(value="开始抓取 · Run", variant="primary", interactive=True)
    started = time.monotonic()

    # Immediate feedback so the click is never silent
    yield ingest_running_html(cats, int(max_results), bool(process_pdfs), 0.0), btn_running

    client = httpx.AsyncClient(timeout=INGEST_TIMEOUT)
    try:
        request = asyncio.create_task(client.post(f"{API_BASE_URL}/ingest", json=payload))
        while not request.done():
            await asyncio.sleep(INGEST_TICK_SECONDS)
            if not request.done():
                yield ingest_running_html(cats, int(max_results), bool(process_pdfs), time.monotonic() - started), btn_running

        r = await request
        if r.status_code != 200:
            try:
                detail = r.json().get("detail") or r.text
            except Exception:
                detail = r.text
            yield ingest_log_html(f"## 抓取失败 · Ingest failed (HTTP {r.status_code})\n\n{detail}"), btn_idle
            return
        data = r.json()
        stats = f"""
<div class="stat-grid">
  <div class="stat-box"><div class="k">抓取 · Fetched</div><div class="v">{data.get("papers_fetched", 0)}</div></div>
  <div class="stat-box"><div class="k">入库 · Stored</div><div class="v">{data.get("papers_stored", 0)}</div></div>
  <div class="stat-box"><div class="k">索引 · Indexed</div><div class="v">{data.get("papers_indexed", 0)}</div></div>
  <div class="stat-box"><div class="k">片段 · Chunks</div><div class="v">{data.get("chunks_indexed", 0)}</div></div>
  <div class="stat-box"><div class="k">PDF</div><div class="v">{data.get("pdfs_parsed", 0)}</div></div>
  <div class="stat-box"><div class="k">耗时 · Time</div><div class="v">{data.get("processing_time", 0):.1f}s</div></div>
</div>
"""
        lines = [
            "## 抓取完成 · Ingest complete",
            f"- 分类 · categories: {', '.join(data.get('categories') or cats)}",
            f"- 范围 · range: {data.get('from_date') or '不限/any'} → {data.get('to_date') or '不限/any'}",
            f"- 抓取 · fetched: {data.get('papers_fetched', 0)}",
            f"- 入库 · stored: {data.get('papers_stored', 0)}",
            f"- PDF 解析 · parsed: {data.get('pdfs_parsed', 0)}（下载/downloaded {data.get('pdfs_downloaded', 0)}）",
            f"- 索引 · indexed: {data.get('papers_indexed', 0)} papers / {data.get('chunks_indexed', 0)} chunks",
            f"- 耗时 · duration: {data.get('processing_time', 0):.1f}s",
        ]
        errs = data.get("errors") or []
        if errs:
            lines.append("### 错误 · Errors (first 5)")
            for e in errs[:5]:
                lines.append(f"- {e}")
        yield stats + ingest_log_html("\n".join(lines)), btn_idle
    except httpx.RequestError as e:
        yield ingest_log_html(f"## 连接失败 · Connection failed\n\n请确认 API 已启动 · Is the API running?\n\n{e}"), btn_idle
    except Exception as e:  # noqa: BLE001 — always restore the button and show an end state
        logger.exception("Ingest UI handler failed")
        yield ingest_log_html(f"## 未知错误 · Unexpected error\n\n{html.escape(str(e))}"), btn_idle
    finally:
        await client.aclose()


def load_papers_ui(keyword: str, category: str) -> str:
    """GET /api/v1/papers. Sync so page-load always finishes (no hanging Loading)."""
    params = {"limit": 50, "offset": 0}
    if keyword and keyword.strip():
        params["keyword"] = keyword.strip()
    if category and category.strip():
        params["category"] = category.strip()
    try:
        with httpx.Client(timeout=8.0) as client:
            r = client.get(f"{API_BASE_URL}/papers", params=params)
            if r.status_code != 200:
                return f'<div class="empty-state">HTTP {r.status_code}: {html.escape(r.text[:200])}</div>'
            data = r.json()
    except Exception as e:  # noqa: BLE001 — always render an end state
        return f'<div class="empty-state">无法连接 API · Cannot reach API. 请确认服务已启动。<br />{html.escape(str(e))}</div>'

    items = []
    for item in data.get("items") or []:
        arxiv_id = item.get("arxiv_id", "")
        local_pdf_path = item.get("local_pdf_url") or f"/api/v1/papers/{arxiv_id}/pdf"
        local_pdf_http = f"http://localhost:8000{local_pdf_path}"
        items.append(
            {
                "title": item.get("title") or "",
                "arxiv_id": arxiv_id,
                "published_date": (item.get("published_date") or "")[:10],
                "categories": item.get("categories") or [],
                "abs_url": item.get("abs_url") or f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": item.get("pdf_url") or f"https://arxiv.org/pdf/{arxiv_id}",
                "local_pdf_http": local_pdf_http,
                "pdf_processed": bool(item.get("pdf_processed")),
                "local_pdf_path": local_pdf_path,
            }
        )
    return paper_list_html(items)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------


def create_gradio_interface():
    theme = build_theme()

    with gr.Blocks(
        title="arXiv Paper Curator",
        theme=theme,
        css=CORE_CSS,
        head=HEAD_HTML,
        js=TAB_JS,
        fill_height=False,
    ) as interface:
        with gr.Column(elem_id="main-shell"):
            gr.HTML(top_bar())
            gr.HTML(page_head())

            with gr.Tabs():
                # ----- Ask -----
                with gr.Tab("问答 · Ask", elem_classes=["custom-tab"]):
                    with gr.Column(elem_classes=["section-block"]):
                        gr.HTML(
                            '<h2 class="section-title">向语料提问 · Ask the corpus</h2>'
                            '<p class="section-desc">混合检索已入库论文，答案流式输出并附可打开来源。 '
                            "Hybrid retrieval over ingested papers; answer streams with openable sources.</p>"
                        )
                        gr.HTML('<div class="field-label">你的问题 · Your question</div>')
                        query_input = gr.Textbox(
                            label="Question · 问题",
                            placeholder="什么是机器学习中的 Transformer？ / What are transformers in ML?",
                            lines=3,
                            max_lines=8,
                            show_label=False,
                            container=False,
                            elem_classes=["composer"],
                        )
                        gr.HTML('<p class="field-hint">按 Enter 发送 · Press Enter to send.</p>')

                        with gr.Row():
                            with gr.Column(scale=4):
                                gr.HTML('<p class="field-hint">可选设置见「高级」 · Optional settings under Advanced.</p>')
                            with gr.Column(scale=1, min_width=120):
                                submit_btn = gr.Button("提问 · Ask", variant="primary", elem_id="submit-btn")

                        with gr.Accordion("高级 · Advanced", open=False):
                            top_k = gr.Slider(1, 10, value=3, step=1, label="检索片段数 · Chunks")
                            use_hybrid = gr.Checkbox(value=True, label="混合检索 Hybrid（BM25 + 向量）")
                            model_choice = gr.Dropdown(
                                choices=["deepseek-flash", "deepseek-reasoner", "llama3.2:1b", "llama3.2:3b"],
                                value=DEFAULT_MODEL,
                                label="模型 · Model",
                            )
                            categories = gr.Textbox(
                                label="arXiv 分类 · Categories",
                                placeholder="cs.AI, cs.LG",
                                info="英文逗号分隔，留空为全部 · Comma-separated; empty = all.",
                            )

                    with gr.Column(elem_classes=["section-block"]):
                        gr.HTML(
                            '<h2 class="section-title">回答 · Answer</h2>'
                            '<p class="section-desc">带来源的答复 · Grounded reply with numbered sources.</p>'
                        )
                        response_output = gr.HTML(
                            value=answer_html(placeholder_answer()),
                            elem_id="answer-output",
                        )

                    with gr.Column(elem_classes=["section-block"]):
                        gr.HTML(
                            '<h2 class="section-title">示例 · Examples</h2>'
                            '<p class="section-desc">点击一行填入表单 · Click a row to fill the form.</p>'
                        )
                        gr.Examples(
                            examples=[
                                ["What are transformers in machine learning?", 3, True, "deepseek-flash", "cs.AI, cs.LG"],
                                ["How do convolutional neural networks work?", 5, True, "deepseek-flash", "cs.CV, cs.LG"],
                                ["What is attention mechanism in deep learning?", 4, False, "deepseek-flash", "cs.AI"],
                            ],
                            inputs=[query_input, top_k, use_hybrid, model_choice, categories],
                            label="示例 · Examples",
                        )

                    submit_btn.click(
                        fn=stream_response,
                        inputs=[query_input, top_k, use_hybrid, model_choice, categories],
                        outputs=[response_output],
                        show_progress="minimal",
                    )
                    query_input.submit(
                        fn=stream_response,
                        inputs=[query_input, top_k, use_hybrid, model_choice, categories],
                        outputs=[response_output],
                        show_progress="minimal",
                    )

                # ----- Ingest -----
                with gr.Tab("抓取 · Ingest", elem_classes=["custom-tab"]):
                    with gr.Column(elem_classes=["section-block"]):
                        gr.HTML(
                            '<h2 class="section-title">抓取论文 · Ingest papers</h2>'
                            '<p class="section-desc">从 arXiv 抓入本地库。日期用日历选择，无需手填。 '
                            "Fetch from arXiv into the local library. Pick dates on the calendar.</p>"
                        )

                        gr.HTML('<div class="field-label">分类 · Categories</div>')
                        ingest_cats = gr.Textbox(
                            label="Categories · 分类",
                            value="cs.AI, cs.LG",
                            placeholder="cs.AI, cs.LG, cs.CL",
                            show_label=False,
                            container=False,
                        )

                        gr.HTML('<div class="field-label">日期范围 · Date range</div>')
                        with gr.Row():
                            with gr.Column():
                                gr.HTML(
                                    """
<div class="date-field">
  <label for="from-date-native">开始 · From</label>
  <input type="date" id="from-date-native" />
</div>
"""
                                )
                                from_date_box = gr.Textbox(
                                    value="",
                                    elem_id="from-date-box",
                                    show_label=False,
                                    container=False,
                                    visible=True,
                                    elem_classes=["date-sync-box"],
                                )
                            with gr.Column():
                                gr.HTML(
                                    """
<div class="date-field">
  <label for="to-date-native">结束 · To</label>
  <input type="date" id="to-date-native" />
</div>
"""
                                )
                                to_date_box = gr.Textbox(
                                    value="",
                                    elem_id="to-date-box",
                                    show_label=False,
                                    container=False,
                                    visible=True,
                                    elem_classes=["date-sync-box"],
                                )
                        gr.HTML(
                            '<p class="field-hint">用日历选择，无需手填 · Pick on the calendar, no typing. 提交格式 YYYYMMDD.</p>'
                        )

                        ingest_max = gr.Slider(1, 100, value=15, step=1, label="最多篇数 · Max papers")
                        ingest_pdf = gr.Checkbox(
                            value=False,
                            label="下载并解析 PDF · Download & parse PDFs",
                            info="开启后才能「打开本地 PDF」 · Required for Open local PDF.",
                        )

                        with gr.Row():
                            with gr.Column(scale=3):
                                gr.HTML('<p class="field-hint">需要本地 PDF 时请勾选解析 · Enable PDF parse for local files.</p>')
                            with gr.Column(scale=1, min_width=120):
                                ingest_btn = gr.Button("开始抓取 · Run", variant="primary")

                    with gr.Column(elem_classes=["section-block"]):
                        gr.HTML(
                            '<h2 class="section-title">结果 · Output</h2>'
                            '<p class="section-desc">抓取结果摘要 · Ingest result summary.</p>'
                        )
                        ingest_log = gr.HTML(
                            value=ingest_log_html("就绪 · Ready."),
                            elem_id="ingest-log",
                        )

                    ingest_btn.click(
                        fn=run_ingest_ui,
                        inputs=[ingest_cats, from_date_box, to_date_box, ingest_max, ingest_pdf],
                        outputs=[ingest_log, ingest_btn],
                        show_progress="minimal",
                    )

                # ----- Library -----
                with gr.Tab("论文库 · Library", elem_classes=["custom-tab"]):
                    with gr.Column(elem_classes=["section-block"]):
                        gr.HTML(
                            '<h2 class="section-title">论文库 · Paper library</h2>'
                            '<p class="section-desc">打开摘要、arXiv PDF，或一键打开<strong>本地缓存 PDF</strong>。 '
                            "Open abstract, arXiv PDF, or the local cached PDF in one click.</p>"
                        )
                        with gr.Row():
                            with gr.Column(scale=2):
                                gr.HTML('<div class="field-label">搜索 · Search</div>')
                                lib_keyword = gr.Textbox(
                                    label="Keyword · 关键词",
                                    placeholder="transformer",
                                    show_label=False,
                                    container=False,
                                )
                            with gr.Column(scale=1):
                                gr.HTML('<div class="field-label">分类 · Category</div>')
                                lib_category = gr.Textbox(
                                    label="Category · 分类",
                                    placeholder="cs.AI",
                                    show_label=False,
                                    container=False,
                                )
                            with gr.Column(scale=0, min_width=110):
                                gr.HTML('<div class="field-label">&nbsp;</div>')
                                refresh_btn = gr.Button("刷新 · Refresh", variant="primary")

                    with gr.Column(elem_classes=["section-block"]):
                        gr.HTML(
                            '<h2 class="section-title">论文 · Papers</h2>'
                            '<p class="section-desc">悬停可见拖拽手柄 · Hover a row for the drag handle.</p>'
                        )
                        # Render initial list synchronously so the page never sticks on Loading.
                        papers_table = gr.HTML(
                            value=load_papers_ui("", ""),
                            elem_id="papers-list",
                        )

                    refresh_btn.click(
                        fn=load_papers_ui,
                        inputs=[lib_keyword, lib_category],
                        outputs=[papers_table],
                        show_progress="minimal",
                    )
                    interface.load(
                        fn=load_papers_ui,
                        inputs=[lib_keyword, lib_category],
                        outputs=[papers_table],
                    )

            gr.HTML(footer_html())

    return interface


def main():
    print("启动 arXiv Paper Curator（Notion 双语界面）...")
    print("Starting arXiv Paper Curator (Notion bilingual UI)...")
    print(f"API Base URL: {API_BASE_URL}")
    interface = create_gradio_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        show_error=True,
        quiet=False,
    )


if __name__ == "__main__":
    main()
