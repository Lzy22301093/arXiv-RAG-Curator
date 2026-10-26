"""Check external reachability from host or container."""
from __future__ import annotations

import os
import urllib.error
import urllib.request

TARGETS = [
    ("arxiv", "https://export.arxiv.org/api/query?search_query=all:electron&start=0&max_results=1", "GET", None),
    ("jina", "https://api.jina.ai/v1/embeddings", "POST", b'{"model":"jina-embeddings-v3","input":["hi"]}'),
    ("deepseek", "https://api.deepseek.com/v1/models", "GET", None),
    ("huggingface", "https://huggingface.co", "GET", None),
    ("pypi", "https://pypi.org", "GET", None),
]

print("HTTP_PROXY=", os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy"))
print("HTTPS_PROXY=", os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"))
print("NO_PROXY=", os.environ.get("NO_PROXY") or os.environ.get("no_proxy"))

for name, url, method, data in TARGETS:
    headers = {"User-Agent": "conn-check/1.0"}
    if name == "jina":
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=12)
        print(f"{name}: OK {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"{name}: HTTP {e.code} (reachable)")
    except Exception as e:  # noqa: BLE001
        print(f"{name}: FAIL {type(e).__name__}: {str(e)[:140]}")
