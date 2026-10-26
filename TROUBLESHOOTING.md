# TROUBLESHOOTING

## 1. 端口占用

**现象：** `rag-api` 启动失败，日志出现 `port is already allocated`。

```powershell
# 查看谁占了 8000
netstat -ano | findstr :8000
docker ps
# 停掉占用端口的其它项目容器，或改 compose 端口映射
```

## 2. API 起不来

```powershell
docker-compose logs -f api
docker-compose up -d --force-recreate api
```

常见原因：`.env` 缺少 `DEEPSEEK_API_KEY`、OpenSearch/Postgres 未就绪。

## 3. OpenSearch 卡住 / 变 unhealthy

```powershell
docker-compose logs opensearch
# 内存不足时，降低 compose 里 OPENSEARCH_JAVA_OPTS
docker-compose restart opensearch
```

## 4. 问答无结果 / 检索为空

1. 是否已入库：Gradio「论文库」或 `GET /api/v1/papers`
2. 混合检索是否正常：`POST /api/v1/hybrid-search/`
3. 索引名是否 `arxiv-papers` / `*-chunks`
4. Embedding 是否可用（Jina key 或 BGE 模型已下载）

## 5. PDF「源文件」404

PDF 未下载成功。入库时勾选 PDF；查看 `data/arxiv_pdfs/` 是否有对应文件。

## 6. Docling 首次解析很慢

布局模型会下载到 `~/.cache/huggingface`（已挂载进 API 容器）。首次之后应变快。国内可设置 `HF_ENDPOINT=https://hf-mirror.com`。

## 7. arXiv 429

降低篇数、拉长间隔；避免多个入口同时抓取。`ARXIV__RATE_LIMIT_DELAY` 默认 3s。

## 8. Gradio 打不开

- 使用 `http://127.0.0.1:7861`（不要用 `0.0.0.0`）
- 确认进程还在：`uv run python gradio_launcher.py`
- API 需已启动（Gradio 调 `:8000`）

## 9. 飞书不回消息

见 [docs/FEISHU.md](docs/FEISHU.md) 排障表。先 `docker-compose logs -f api` 看 `Feishu bot` 相关日志。

## 10. 磁盘 / 镜像过大

API 镜像含 torch/docling，体积大。只删本项目构建缓存时不要用 `docker system prune -a`（会波及其它项目）。

```powershell
docker-compose down
# 只清理本项目停止的容器
docker container prune
```

## 11. Windows 无 `docker compose`

Makefile 会自动回退到 `docker-compose`。也可手动用 `docker-compose`。

## 12. 测试失败

```powershell
uv sync
uv run pytest -v
```

测试配置在 `.env.test`。集成测试依赖 testcontainers / Docker。
