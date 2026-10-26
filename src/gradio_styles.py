"""Notion-style design system for the arXiv Paper Curator Gradio UI.

Palette: canvas #f7f6f3 · card #ffffff · ink #37352f · border #e5e5e5 (gray-200)
Hover #efedea · active #e3e1db · accent #2eaadc
No gradients, no large radii, no heavy shadows, no translate/scale motion.
"""

from __future__ import annotations

import html
from typing import Any, Iterable, Sequence

# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

CANVAS = "#f7f6f3"
CARD = "#ffffff"
INK = "#37352f"
MUTED = "#787774"
FAINT = "#9b9a97"
BORDER = "#e5e5e5"  # gray-200-ish
HOVER = "#efedea"
ACTIVE = "#e3e1db"
ACCENT = "#2eaadc"
ACCENT_SOFT = "#e7f5fb"
RED = "#eb5757"
GREEN = "#0f7b6c"
YELLOW = "#dfab01"

FONT = (
    "ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', "
    "'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', Helvetica, Arial, sans-serif"
)
MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

HEAD_HTML = """
<meta name="color-scheme" content="light" />
<meta name="theme-color" content="#f7f6f3" />
"""

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CORE_CSS = r"""
:root {
  --canvas: #f7f6f3;
  --card: #ffffff;
  --ink: #37352f;
  --muted: #787774;
  --faint: #9b9a97;
  --border: #e5e5e5;
  --hover: #efedea;
  --active: #e3e1db;
  --accent: #2eaadc;
  --accent-soft: #e7f5fb;
  --red: #eb5757;
  --green: #0f7b6c;
  --yellow: #dfab01;
  --font: __FONT__;
  --mono: __MONO__;
  --radius: 6px;
  --radius-lg: 8px;
}

* { box-sizing: border-box; }

html, body {
  background: var(--canvas) !important;
  color: var(--ink) !important;
  font-family: var(--font) !important;
  font-size: 14.5px !important;
  line-height: 1.55 !important;
  -webkit-font-smoothing: antialiased;
}

.gradio-container {
  max-width: none !important;
  padding: 0 !important;
  margin: 0 !important;
  background: transparent !important;
  font-family: var(--font) !important;
  color: var(--ink) !important;
}

#main-shell {
  width: min(880px, calc(100% - 32px));
  margin: 0 auto;
  padding: 20px 0 48px;
}

/* Top bar */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
  padding: 8px 2px;
  color: var(--muted);
  font-size: 13px;
}

.top-bar .brand {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--ink);
  font-weight: 600;
  font-size: 13.5px;
}

.top-bar .brand .mark {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  background: var(--ink);
  color: var(--card);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
}

.top-bar .pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 8px;
  border-radius: 4px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--muted);
  font-size: 12px;
  transition: background-color 150ms ease;
}

.pill:hover { background: var(--hover); }
.pill .dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--green);
}

/* Page title (Notion doc) */
.page-title {
  margin: 8px 0 6px;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--ink);
  line-height: 1.2;
}

.page-desc {
  margin: 0 0 18px;
  color: var(--muted);
  font-size: 14.5px;
  max-width: 62ch;
  line-height: 1.55;
}

/* Tabs */
.tab-shell {
  background: transparent;
  border: none;
  margin-bottom: 4px;
}

.tab-shell .tab-container,
.tab-shell [role="tablist"] {
  display: flex !important;
  gap: 2px !important;
  padding: 0 !important;
  border: none !important;
  background: transparent !important;
  overflow-x: auto;
}

.tab-shell [role="tab"],
.tab-shell .tab-container button {
  appearance: none !important;
  background: transparent !important;
  color: var(--muted) !important;
  border: none !important;
  border-radius: var(--radius) !important;
  font-family: var(--font) !important;
  font-size: 13.5px !important;
  font-weight: 500 !important;
  padding: 7px 12px !important;
  cursor: pointer !important;
  box-shadow: none !important;
  transition: background-color 150ms ease, color 150ms ease !important;
  min-height: 0 !important;
  white-space: nowrap;
}

.tab-shell [role="tab"]:hover {
  background: var(--hover) !important;
  color: var(--ink) !important;
}

.tab-shell [role="tab"][aria-selected="true"],
.tab-shell button[role="tab"].selected,
.tab-shell .tab-container button[aria-selected="true"] {
  background: var(--active) !important;
  color: var(--ink) !important;
  font-weight: 600 !important;
  box-shadow: none !important;
}

.tab-shell [role="tabpanel"],
.tab-shell .tabitem {
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
  padding: 16px 0 0 !important;
}

/* Section blocks */
.section-block {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px 18px;
  margin-bottom: 14px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
}

.section-desc {
  margin: 0 0 12px;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.55;
  max-width: 62ch;
}

.field-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  margin: 12px 0 6px;
}

.field-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--faint);
}

/* Inputs */
.gradio-container textarea,
.gradio-container input[type="text"],
.gradio-container input[type="number"],
.gradio-container input[type="email"],
.gradio-container input[type="date"],
.gradio-container input[type="datetime-local"] {
  width: 100% !important;
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: var(--ink) !important;
  font-family: var(--font) !important;
  font-size: 14px !important;
  line-height: 1.5 !important;
  padding: 9px 11px !important;
  outline: none !important;
  box-shadow: none !important;
  transition: border-color 150ms ease, box-shadow 150ms ease, background-color 150ms ease !important;
  min-height: 38px !important;
}

.gradio-container textarea:focus,
.gradio-container input[type="text"]:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(46, 170, 220, 0.25) !important;
  background: var(--card) !important;
}

.gradio-container textarea::placeholder,
.gradio-container input::placeholder {
  color: var(--faint) !important;
  opacity: 1 !important;
}

.composer textarea {
  min-height: 96px;
  resize: vertical;
}

/* Buttons — Ultimate Restraint */
.gradio-container button {
  font-family: var(--font) !important;
  font-weight: 500 !important;
  border-radius: var(--radius) !important;
  box-shadow: none !important;
  transition: background-color 150ms ease, color 150ms ease, border-color 150ms ease !important;
  transform: none !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
}

.gradio-container button.primary {
  background: var(--accent) !important;
  color: #ffffff !important;
  border: 1px solid var(--accent) !important;
  padding: 8px 14px !important;
  font-size: 13px !important;
  border-radius: var(--radius) !important;
}

.gradio-container button.primary:hover {
  background: #2498c4 !important;
  border-color: #2498c4 !important;
  filter: none !important;
  transform: none !important;
  box-shadow: none !important;
}

.gradio-container button.primary:active {
  background: #1e86ad !important;
}

.gradio-container button.secondary,
.gradio-container button:not(.primary):not(.stop):not([role="tab"]) {
  background: transparent !important;
  color: var(--ink) !important;
  border: 1px solid var(--border) !important;
  padding: 8px 14px !important;
  font-size: 13px !important;
}

.gradio-container button.secondary:hover,
.gradio-container button:not(.primary):not(.stop):not([role="tab"]):hover {
  background: var(--hover) !important;
  transform: none !important;
  box-shadow: none !important;
  border-color: var(--border) !important;
}

.gradio-container button.secondary:active,
.gradio-container button:not(.primary):not(.stop):not([role="tab"]):active {
  background: var(--active) !important;
}

.gradio-container button.stop {
  background: transparent !important;
  border: 1px solid var(--border) !important;
  color: var(--ink) !important;
}

/* Accordion */
button.label-wrap {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  width: 100% !important;
  background: transparent !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: var(--ink) !important;
  font-family: var(--font) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  padding: 9px 12px !important;
  margin: 4px 0 10px !important;
  cursor: pointer !important;
  box-shadow: none !important;
  transition: background-color 150ms ease !important;
}

button.label-wrap:hover {
  background: var(--hover) !important;
}

button.label-wrap:active {
  background: var(--active) !important;
}

button.label-wrap span {
  display: inline !important;
  opacity: 1 !important;
  visibility: visible !important;
  color: inherit !important;
}

button.label-wrap + div,
button.label-wrap ~ div {
  padding: 4px 2px 10px !important;
}

button.label-wrap ~ div label,
button.label-wrap ~ div .label {
  display: flex !important;
  color: var(--muted) !important;
  font-family: var(--font) !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  margin: 10px 0 6px !important;
  opacity: 1 !important;
  visibility: visible !important;
  background: transparent !important;
  border: none !important;
}

button.label-wrap ~ div .info {
  display: block !important;
  color: var(--faint) !important;
  font-size: 12px !important;
  opacity: 1 !important;
}

/* Hide default gradio labels */
.gradio-container .block > .label-wrap:not(button),
.gradio-container .block > .label {
  display: none !important;
}

/* Cards / answer — flatten nested card (answer sits in section-block) */
.answer-shell {
  background: transparent;
  border: none;
  border-top: 1px solid var(--border);
  border-radius: 0;
  padding: 12px 0 0;
  margin-top: 4px;
}

.answer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  font-size: 12px;
  color: var(--faint);
}

.answer-toolbar .title {
  color: var(--ink);
  font-weight: 600;
  font-size: 13px;
}

.answer-body {
  min-height: 120px;
  color: var(--ink);
  font-size: 14.5px;
  line-height: 1.65;
}

.answer-body .placeholder .title {
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 6px;
  color: var(--ink);
}

.answer-body .placeholder .desc {
  color: var(--muted);
  font-size: 13.5px;
  line-height: 1.55;
  max-width: 56ch;
}

.answer-prose p { margin: 0 0 0.75em; }
.answer-prose p:last-child { margin-bottom: 0; }
.answer-prose h1, .answer-prose h2, .answer-prose h3 {
  font-family: var(--font);
  letter-spacing: -0.01em;
  margin: 0.9em 0 0.4em;
  font-weight: 600;
  color: var(--ink);
}
.answer-prose ul, .answer-prose ol {
  margin: 0 0 0.8em;
  padding-left: 1.3em;
}
.answer-prose li { margin: 0.2em 0; }
.answer-prose code {
  font-family: var(--mono);
  font-size: 0.9em;
  background: var(--canvas);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.08em 0.28em;
}
.answer-prose pre {
  background: var(--canvas);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px;
  overflow: auto;
  margin: 0 0 0.8em;
  font-family: var(--mono);
  font-size: 12.5px;
}
.answer-prose a { color: var(--accent); text-decoration: none; }
.answer-prose a:hover { text-decoration: underline; text-underline-offset: 2px; }
.answer-prose strong { font-weight: 600; }
.answer-prose blockquote {
  margin: 0 0 0.8em;
  padding: 6px 12px;
  border-left: 3px solid var(--border);
  color: var(--muted);
}

.stream-cursor {
  display: inline-block;
  width: 6px;
  height: 1em;
  margin-left: 2px;
  vertical-align: text-bottom;
  background: var(--accent);
  animation: blink 1s step-end infinite;
}

@keyframes blink { 50% { opacity: 0; } }

.meta-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 8px;
  border-radius: 4px;
  background: var(--canvas);
  color: var(--muted);
  font-size: 12px;
  border: none !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  font-family: var(--font) !important;
}

.meta-chip b {
  color: var(--ink);
  font-weight: 600;
  font-family: var(--font);
  font-size: 12px;
}

/* Sources / refs */
.sources {
  margin-top: 12px;
}

.sources-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  margin-bottom: 8px;
}

.ref-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 6px;
}

.ref-item {
  display: grid;
  grid-template-columns: 2rem 1fr;
  gap: 8px;
  align-items: start;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card);
  transition: background-color 150ms ease;
}

.ref-item:hover {
  background: var(--hover);
}

.ref-item .n {
  color: var(--faint);
  font-size: 12px;
  font-family: var(--mono);
  padding-top: 1px;
}

.ref-item a {
  color: var(--accent);
  text-decoration: none;
  font-size: 13px;
  word-break: break-all;
}

.ref-item a:hover { text-decoration: underline; text-underline-offset: 2px; }

.ref-item .rid {
  display: block;
  color: var(--faint);
  font-family: var(--mono);
  font-size: 11px;
  margin-top: 2px;
  word-break: break-all;
}

/* Log — sit flat inside section */
.log-shell {
  background: transparent;
  border: none;
  border-top: 1px solid var(--border);
  border-radius: 0;
  padding: 12px 0 0;
  min-height: 120px;
  margin-top: 4px;
}

.log-head {
  font-size: 12px;
  color: var(--faint);
  margin-bottom: 8px;
}

.log-body {
  font-size: 13.5px;
  line-height: 1.65;
  color: var(--ink);
}

.log-body .hl { font-weight: 600; margin-top: 0.55em; }
.log-body .dim { color: var(--muted); }
.log-body .err { color: var(--red); }

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 8px;
  margin: 10px 0 14px;
}

.stat-box {
  background: var(--canvas);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 12px;
}

.stat-box .k {
  font-size: 11px;
  color: var(--muted);
  margin-bottom: 4px;
}

.stat-box .v {
  font-size: 18px;
  font-weight: 650;
  color: var(--ink);
  letter-spacing: -0.01em;
}

/* Ingest running status card */
.ingest-running {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  background: var(--accent-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 14px 16px;
}

.ingest-spinner {
  flex: none;
  width: 16px;
  height: 16px;
  margin-top: 3px;
  border: 2px solid var(--accent);
  border-top-color: transparent;
  border-radius: 50%;
  animation: ingest-spin 0.8s linear infinite;
}

@keyframes ingest-spin { to { transform: rotate(360deg); } }

.ingest-running .title {
  font-size: 14px;
  font-weight: 650;
  color: var(--ink);
}

.ingest-running .title .elapsed {
  font-family: var(--mono);
  color: var(--accent);
  font-weight: 600;
  margin-left: 6px;
}

.ingest-running .desc {
  font-size: 12.5px;
  color: var(--muted);
  margin-top: 4px;
  line-height: 1.7;
}

.ingest-running .desc b { color: var(--ink); font-weight: 600; }

/* Library list with drag-handle illusion */
.paper-list {
  display: grid;
  gap: 6px;
}

.paper-row {
  position: relative;
  display: grid;
  grid-template-columns: 16px 1fr;
  gap: 8px;
  align-items: start;
  padding: 10px 12px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  transition: background-color 150ms ease;
}

.paper-row:hover {
  background: var(--hover);
}

.paper-row .drag {
  opacity: 0;
  color: var(--faint);
  font-size: 11px;
  letter-spacing: -1px;
  line-height: 1.2;
  padding-top: 3px;
  transition: opacity 150ms ease;
  user-select: none;
}

.paper-row:hover .drag {
  opacity: 1;
}

.paper-row .title {
  display: block;
  color: var(--ink);
  font-weight: 600;
  font-size: 14px;
  text-decoration: none;
  line-height: 1.4;
}

.paper-row .title:hover {
  color: var(--ink);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.paper-row .meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 1px 7px;
  border-radius: 4px;
  background: var(--canvas);
  color: var(--muted);
  font-size: 11.5px;
  border: none !important;
}

.tag.accent {
  background: var(--accent-soft);
  color: #1a7fa6;
}

.paper-row .links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
}

.paper-row .links a {
  color: var(--accent);
  font-size: 12.5px;
  text-decoration: none;
  padding: 2px 0;
  transition: background-color 150ms ease;
}

.paper-row .links a:hover {
  text-decoration: underline;
  text-underline-offset: 2px;
}

.paper-row .links a.open-local {
  color: var(--ink);
  background: var(--canvas);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 2px 8px;
}

.paper-row .links a.open-local:hover {
  background: var(--active);
  text-decoration: none;
}

.paper-row .local-file {
  margin-top: 4px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--faint);
  word-break: break-all;
}

.empty-state {
  padding: 18px 14px;
  border: 1px dashed var(--border);
  border-radius: var(--radius-lg);
  color: var(--muted);
  font-size: 13.5px;
  background: var(--card);
}

/* Examples table */
.block:has(.table-wrap) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}

.block:has(.table-wrap) > .label {
  display: none !important;
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card);
}

table[role="grid"],
.table-wrap table {
  width: 100% !important;
  border-collapse: collapse !important;
  border-spacing: 0 !important;
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  font-family: var(--font) !important;
}

table[role="grid"] th,
.table-wrap table th {
  text-align: left !important;
  font-size: 11.5px !important;
  font-weight: 600 !important;
  color: var(--muted) !important;
  padding: 8px 10px !important;
  border: none !important;
  border-bottom: 1px solid var(--border) !important;
  background: var(--canvas) !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}

table[role="grid"] td,
.table-wrap table td {
  padding: 9px 10px !important;
  border: none !important;
  border-bottom: 1px solid var(--border) !important;
  background: transparent !important;
  color: var(--ink) !important;
  font-size: 12.5px !important;
  vertical-align: top !important;
  text-align: left !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}

table[role="grid"] tbody tr:last-child td,
.table-wrap table tbody tr:last-child td {
  border-bottom: none !important;
}

table[role="grid"] tbody tr,
.table-wrap table tbody tr {
  transition: background-color 150ms ease !important;
  transform: none !important;
}

table[role="grid"] tbody tr:hover td,
.table-wrap table tbody tr:hover td {
  background: var(--hover) !important;
  transform: none !important;
}

table[role="grid"] td button,
.table-wrap table td button {
  background: transparent !important;
  border: none !important;
  color: inherit !important;
  width: 100% !important;
  text-align: left !important;
  padding: 0 !important;
  font-family: var(--font) !important;
  font-size: inherit !important;
  box-shadow: none !important;
  border-radius: 0 !important;
}

/* Native date form (calendar pickers) */
.date-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.date-field label {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
}

.date-field input[type="date"] {
  width: 100% !important;
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: var(--ink) !important;
  font-family: var(--font) !important;
  font-size: 14px !important;
  line-height: 1.5 !important;
  padding: 9px 11px !important;
  min-height: 40px !important;
  outline: none !important;
  box-shadow: none !important;
  transition: border-color 150ms ease, box-shadow 150ms ease !important;
}

.date-field input[type="date"]:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(46, 170, 220, 0.25) !important;
}

/* Hidden Gradio mirrors for date form values (kept in DOM for submit) */
.date-sync-box,
.date-sync-box .block,
.date-sync-box textarea,
.date-sync-box input {
  width: 1px !important;
  min-height: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
  opacity: 0 !important;
  position: absolute !important;
  pointer-events: none !important;
  overflow: hidden !important;
}

/* DateTime fallback — force visible if Gradio DateTime is used */
#ingest-from .timebox,
#ingest-to .timebox,
.datetime .timebox {
  display: flex !important;
  min-height: 40px !important;
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  overflow: hidden !important;
  opacity: 1 !important;
  visibility: visible !important;
}

#ingest-from input.time,
#ingest-to input.time,
.datetime input.time {
  display: block !important;
  min-height: 40px !important;
  padding: 9px 11px !important;
  background: var(--card) !important;
  color: var(--ink) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) 0 0 var(--radius) !important;
  opacity: 1 !important;
  visibility: visible !important;
  font-family: var(--font) !important;
  width: 100% !important;
}

#ingest-from button.calendar,
#ingest-to button.calendar,
.datetime button.calendar {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-width: 42px !important;
  min-height: 40px !important;
  background: var(--canvas) !important;
  border: 1px solid var(--border) !important;
  border-left: none !important;
  border-radius: 0 var(--radius) var(--radius) 0 !important;
  opacity: 1 !important;
  visibility: visible !important;
  color: var(--ink) !important;
}

/* DateTime widgets */
.gradio-container .datetime,
.gradio-container input[type="datetime-local"],
.gradio-container input[type="date"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: var(--ink) !important;
  font-family: var(--font) !important;
  box-shadow: none !important;
}

.gradio-container .datetime:focus,
.gradio-container input[type="date"]:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(46, 170, 220, 0.25) !important;
}

/* Slider / checkbox / dropdown */
.gradio-container input[type="range"] {
  accent-color: var(--accent) !important;
}

.gradio-container .slider {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.gradio-container input[type="checkbox"] {
  accent-color: var(--accent) !important;
  width: 15px !important;
  height: 15px !important;
  border-radius: 3px !important;
}

.gradio-container .checkbox,
.gradio-container .form {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.gradio-container .dropdown,
.gradio-container select {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: var(--ink) !important;
  font-family: var(--font) !important;
}

/* Footer */
.site-footer {
  margin-top: 18px;
  padding: 14px 4px 0;
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 12.5px;
  line-height: 1.6;
}

.site-footer code {
  font-family: var(--mono);
  font-size: 11.5px;
  color: var(--ink);
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 5px;
}

.site-footer a {
  color: var(--accent);
  text-decoration: none;
}

.site-footer a:hover {
  text-decoration: underline;
  text-underline-offset: 2px;
}

/* Hide Gradio branding */
.gradio-container .show-api,
.gradio-container .built-with,
.gradio-container #footer {
  display: none !important;
}

.gradio-container .progress-bar {
  background: var(--accent) !important;
}

.gradio-container .markdown {
  color: var(--ink) !important;
  font-family: var(--font) !important;
  background: transparent !important;
}

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; text-underline-offset: 2px; }

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 6px;
}

:focus-visible {
  outline: none !important;
  box-shadow: 0 0 0 2px rgba(46, 170, 220, 0.35) !important;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    transform: none !important;
  }
}

@media (max-width: 720px) {
  #main-shell {
    width: calc(100% - 20px);
    padding-top: 12px;
  }
  .page-title { font-size: 26px; }
  .top-bar { flex-direction: column; align-items: flex-start; }
}
""".replace("__FONT__", FONT).replace("__MONO__", MONO)


TAB_JS = r"""
() => {
  function setValue(el, value) {
    if (!el) return false;
    var proto = el.tagName === "TEXTAREA"
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
    var setter = Object.getOwnPropertyDescriptor(proto, "value").set;
    if (setter) setter.call(el, value);
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  function findGradioField(hintId) {
    var root = document.getElementById(hintId);
    if (!root) return null;
    if (root.tagName === "TEXTAREA" || root.tagName === "INPUT") return root;
    return root.querySelector("textarea, input:not([type=checkbox]):not([type=range]):not([type=hidden]):not([type=date])");
  }

  function bindNativeDate(nativeId, fieldId) {
    var native = document.getElementById(nativeId);
    if (!native || native.dataset.bound === "1") return;
    native.dataset.bound = "1";
    native.addEventListener("change", function () {
      var target = findGradioField(fieldId);
      if (!target) {
        // Fallback: mirror by order of .date-sync-box textareas
        var boxes = document.querySelectorAll(".date-sync-box textarea, .date-sync-box input[type=text]");
        var idx = nativeId.indexOf("to-") === 0 ? 1 : 0;
        target = boxes[idx] || boxes[0];
      }
      if (target) setValue(target, native.value || "");
    });
  }

  function enhance() {
    bindNativeDate("from-date-native", "from-date-box");
    bindNativeDate("to-date-native", "to-date-box");
    document.querySelectorAll(".table-wrap").forEach(function (el) {
      el.style.overflowX = "auto";
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", enhance);
  } else {
    enhance();
  }
  var mo = new MutationObserver(enhance);
  mo.observe(document.documentElement, { childList: true, subtree: true });
}
"""


# ---------------------------------------------------------------------------
# HTML builders
# ---------------------------------------------------------------------------


def top_bar() -> str:
    return """
<div class="top-bar">
  <div class="brand"><span class="mark">A</span> arXiv Paper Curator · 论文策展</div>
  <div class="pills">
    <span class="pill"><span class="dot"></span> API 就绪 · Ready</span>
    <span class="pill">混合检索 · Hybrid</span>
  </div>
</div>
"""


def page_head() -> str:
    return """
<header>
  <h1 class="page-title">研究工作台 · Research workspace</h1>
  <p class="page-desc">
    在 arXiv 论文库上提问、抓取新论文，并一键打开本地 PDF。
    Ask grounded questions, ingest papers, and open local PDFs — three tools, one calm workspace.
  </p>
</header>
"""


def placeholder_answer() -> str:
    return """
<div class="placeholder">
  <div class="title">准备就绪 · Ready for a question</div>
  <div class="desc">
    在下方输入研究问题，答案将流式输出，并附带可打开的编号来源。
    Type a research question below — the answer streams in with numbered sources.
  </div>
</div>
"""


def answer_html(
    body_html: str,
    *,
    mode: str = "",
    chunks: int | str = "",
    source_count: int | str = "",
    streaming: bool = False,
    error: bool = False,
) -> str:
    meta = []
    if mode:
        meta.append(f'<span class="meta-chip">模式 · <b>{html.escape(str(mode))}</b></span>')
    if chunks != "":
        meta.append(f'<span class="meta-chip">片段 · <b>{html.escape(str(chunks))}</b></span>')
    if source_count != "":
        meta.append(f'<span class="meta-chip">来源 · <b>{html.escape(str(source_count))}</b></span>')
    if error:
        meta.append('<span class="meta-chip">状态 · <b>错误</b></span>')
    elif streaming:
        meta.append('<span class="meta-chip">状态 · <b>输出中</b></span>')
    elif body_html and "placeholder" not in body_html:
        meta.append('<span class="meta-chip">状态 · <b>完成</b></span>')
    else:
        meta.append('<span class="meta-chip">状态 · <b>待命</b></span>')

    cursor = '<span class="stream-cursor" aria-hidden="true"></span>' if streaming else ""
    meta_html = f'<div class="meta-strip">{"".join(meta)}</div>' if meta else ""

    return f"""
<div class="answer-shell">
  <div class="answer-toolbar">
    <div class="title">回答 · Answer</div>
    <div>流式 · streamed</div>
  </div>
  <div class="answer-body answer-prose">{body_html}{cursor}</div>
  {meta_html}
</div>
"""


def sources_html(sources: Sequence[str]) -> str:
    if not sources:
        return ""
    items = []
    for i, src in enumerate(sources[:8], 1):
        url = html.escape(src, quote=True)
        pid = src.rstrip("/").split("/")[-1] or f"src-{i}"
        items.append(
            f"""
<li class="ref-item">
  <span class="n">{i}</span>
  <span>
    <a href="{url}" target="_blank" rel="noopener noreferrer">arXiv:{html.escape(pid)}</a>
    <span class="rid">{html.escape(src)}</span>
  </span>
</li>
"""
        )
    more = ""
    if len(sources) > 8:
        more = f'<p class="field-hint">另有 {len(sources) - 8} 条来源 · {len(sources) - 8} more</p>'
    return (
        '<div class="sources">'
        '<div class="sources-title">来源 · Sources</div>'
        f'<ul class="ref-list">{"".join(items)}</ul>{more}'
        "</div>"
    )


def ingest_running_html(categories: Sequence[str], max_results: int, process_pdfs: bool, elapsed: float) -> str:
    """Live status card shown while POST /ingest is in flight (elapsed ticks per yield)."""
    cats = ", ".join(categories) if categories else "全部 · all"
    pdf_note = "是 · yes" if process_pdfs else "否 · no"
    return f"""
<div class="ingest-running">
  <div class="ingest-spinner" aria-hidden="true"></div>
  <div>
    <div class="title">正在抓取 · Ingesting…<span class="elapsed">{elapsed:.0f}s</span></div>
    <div class="desc">
      分类 · Categories: <b>{html.escape(cats)}</b> · 最多 · Max: <b>{max_results}</b> · 解析 PDF · Parse PDFs: <b>{pdf_note}</b><br />
      正在从 arXiv 抓取、入库并索引，完成后此处显示结果，通常 10–60 秒。
      Fetching, storing and indexing — the summary appears here when done, usually within 10–60s.<br />
      若超过 2 分钟，多半是嵌入服务 api.jina.ai 不可达（每篇论文最多等 30 秒）。
      Beyond ~2 min the embedding API is likely unreachable.
    </div>
  </div>
</div>
"""


def ingest_log_html(message: str, *, ok: bool = True) -> str:
    lines = html.escape(message).split("\n")
    formatted = []
    for line in lines:
        if line.startswith("##"):
            formatted.append(f'<div class="hl">{line}</div>')
        elif "失败" in line or "failed" in line.lower() or "Error" in line:
            formatted.append(f'<div class="err">{line}</div>')
        elif line.startswith("-"):
            formatted.append(f'<div class="dim">{line}</div>')
        else:
            formatted.append(f"<div>{line}</div>")
    body = "\n".join(formatted) or '<div class="dim">空闲 · Idle. 运行抓取以查看结果。</div>'
    return f"""
<div class="log-shell">
  <div class="log-head">抓取日志 · Ingest log · POST /api/v1/ingest</div>
  <div class="log-body">{body}</div>
</div>
"""


def paper_list_html(items: Iterable[dict[str, Any]]) -> str:
    items = list(items)
    if not items:
        return (
            '<div class="empty-state">暂无论文 · No papers yet. 请先在「抓取」入库后刷新。Ingest some papers, then refresh.</div>'
        )
    rows = []
    for i, item in enumerate(items, 1):
        title = item.get("title") or "Untitled · 无标题"
        arxiv_id = item.get("arxiv_id") or ""
        date = (item.get("published_date") or "")[:10]
        cats = item.get("categories") or []
        abs_url = item.get("abs_url") or f"https://arxiv.org/abs/{arxiv_id}"
        pdf_url = item.get("pdf_url") or f"https://arxiv.org/pdf/{arxiv_id}"
        local_pdf_http = item.get("local_pdf_http") or ""
        pdf_processed = bool(item.get("pdf_processed"))
        local_pdf_path = item.get("local_pdf_path") or ""

        meta_bits = []
        if arxiv_id:
            meta_bits.append(f'<span class="tag">{html.escape(arxiv_id)}</span>')
        if date:
            meta_bits.append(f'<span class="tag">{html.escape(date)}</span>')
        for c in cats[:3]:
            meta_bits.append(f'<span class="tag accent">{html.escape(c)}</span>')

        if local_pdf_http and pdf_processed:
            local_link = (
                f'<a class="open-local" href="{html.escape(local_pdf_http, quote=True)}" '
                f'target="_blank" rel="noopener noreferrer">打开本地 PDF · Open local</a>'
            )
            local_note = f'<div class="local-file">{html.escape(local_pdf_path or local_pdf_http)}</div>'
        elif local_pdf_http:
            local_link = (
                f'<a class="open-local" href="{html.escape(local_pdf_http, quote=True)}" '
                f'target="_blank" rel="noopener noreferrer">本地 PDF · Local</a>'
            )
            local_note = '<div class="local-file">未下载则可能 404 · may 404 if not downloaded</div>'
        else:
            local_link = ""
            local_note = ""

        rows.append(
            f"""
<article class="paper-row">
  <div class="drag" aria-hidden="true">⋮⋮</div>
  <div>
    <a class="title" href="{html.escape(abs_url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(title[:140])}</a>
    <div class="meta">{"".join(meta_bits)}</div>
    <div class="links">
      <a href="{html.escape(abs_url, quote=True)}" target="_blank" rel="noopener noreferrer">摘要 · Abstract</a>
      <a href="{html.escape(pdf_url, quote=True)}" target="_blank" rel="noopener noreferrer">arXiv PDF</a>
      {local_link}
    </div>
    {local_note}
  </div>
</article>
"""
        )
    return f'<div class="paper-list">{"".join(rows)}</div>'


def footer_html() -> str:
    return """
<footer class="site-footer">
  <div>
    需 API · Requires API · <code>http://localhost:8000</code>
    · 抓取 · Ingest <code>POST /api/v1/ingest</code>
    · 列表 · Library <code>GET /api/v1/papers</code>
  </div>
  <div>
    命令行 · CLI · <code>uv run python scripts/ingest.py --categories cs.AI --max 15</code>
  </div>
</footer>
"""


def build_theme():
    import gradio as gr

    class NotionSoft(gr.themes.Base):
        def __init__(self):
            super().__init__(
                primary_hue=gr.themes.colors.sky,
                secondary_hue=gr.themes.colors.gray,
                neutral_hue=gr.themes.colors.gray,
                font=[
                    "ui-sans-serif",
                    "-apple-system",
                    "Segoe UI",
                    "Noto Sans SC",
                    "Microsoft YaHei",
                    "sans-serif",
                ],
                font_mono=["ui-monospace", "Consolas", "monospace"],
            )
            self.set(
                body_background_fill="#f7f6f3",
                body_background_fill_dark="#f7f6f3",
                body_text_color="#37352f",
                body_text_color_dark="#37352f",
                body_text_color_subdued="#787774",
                body_text_color_subdued_dark="#787774",
                background_fill_primary="#f7f6f3",
                background_fill_primary_dark="#f7f6f3",
                background_fill_secondary="#ffffff",
                background_fill_secondary_dark="#ffffff",
                block_background_fill="#ffffff",
                block_background_fill_dark="#ffffff",
                block_border_color="#e5e5e5",
                block_border_color_dark="#e5e5e5",
                block_radius="8px",
                block_padding="12px",
                block_title_text_color="#37352f",
                block_title_text_color_dark="#37352f",
                block_label_text_color="#787774",
                block_label_text_color_dark="#787774",
                input_background_fill="#ffffff",
                input_background_fill_dark="#ffffff",
                input_border_color="#e5e5e5",
                input_border_color_dark="#e5e5e5",
                input_border_color_focus="#2eaadc",
                input_border_color_focus_dark="#2eaadc",
                input_radius="6px",
                button_primary_background_fill="#2eaadc",
                button_primary_background_fill_dark="#2eaadc",
                button_primary_background_fill_hover="#2498c4",
                button_primary_background_fill_hover_dark="#2498c4",
                button_primary_text_color="#ffffff",
                button_primary_text_color_dark="#ffffff",
                button_secondary_background_fill="transparent",
                button_secondary_background_fill_dark="transparent",
                button_secondary_text_color="#37352f",
                button_secondary_text_color_dark="#37352f",
                button_large_radius="6px",
                button_medium_radius="6px",
                button_small_radius="6px",
                slider_color="#2eaadc",
                slider_color_dark="#2eaadc",
                accordion_text_color="#37352f",
                accordion_text_color_dark="#37352f",
                link_text_color="#2eaadc",
                link_text_color_dark="#2eaadc",
                loader_color="#2eaadc",
                loader_color_dark="#2eaadc",
                code_background_fill="#f7f6f3",
                code_background_fill_dark="#f7f6f3",
                checkbox_background_color_selected="#2eaadc",
                checkbox_background_color_selected_dark="#2eaadc",
                checkbox_border_radius="3px",
            )

    return NotionSoft()
