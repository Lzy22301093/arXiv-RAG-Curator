"""Quick connectivity check for DeepSeek and Jina from host or container."""
from __future__ import annotations

import os
import urllib.error
import urllib.request


def post_json(url: str, payload: bytes, headers: dict[str, str], timeout: int = 20) -> None:
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read(300)
        print(f"OK {resp.status} {url}")
        print(body[:200])
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} {url}")
        print(e.read()[:300])
    except Exception as e:  # noqa: BLE001
        print(f"FAIL {type(e).__name__}: {e} {url}")


def main() -> None:
    jina_key = os.environ.get("JINA_API_KEY", "")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
    deepseek_base = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    print(f"JINA_API_KEY len={len(jina_key)}")
    print(f"DEEPSEEK_API_KEY len={len(deepseek_key)} prefix={deepseek_key[:8]}")
    print(f"DEEPSEEK_BASE_URL={deepseek_base}")

    post_json(
        "https://api.jina.ai/v1/embeddings",
        b'{"model":"jina-embeddings-v3","input":["hello"]}',
        {"Authorization": f"Bearer {jina_key}", "Content-Type": "application/json"},
    )
    post_json(
        f"{deepseek_base.rstrip('/')}/chat/completions",
        b'{"model":"deepseek-flash","messages":[{"role":"user","content":"ping"}],"max_tokens":5}',
        {"Authorization": f"Bearer {deepseek_key}", "Content-Type": "application/json"},
    )


if __name__ == "__main__":
    main()
