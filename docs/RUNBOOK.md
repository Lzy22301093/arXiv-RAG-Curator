# RUNBOOK

日常启动、排障与运维说明。

## 服务与端口

| 服务 | 端口 | 说明 |
|------|------|------|
| FastAPI | 8000 | 主 API + 飞书 Webhook `/feishu/` |
| Gradio | 7861 | 本地 UI（宿主机 `uv run python gradio_launcher.py`） |
| OpenSearch | 9200 | 混合检索 |
| OpenSearch Dashboards | 5601 | 可选索引调试 |
| PostgreSQL | 5432 | 论文元数据 |
| Redis | 6379 | 答案缓存 |

## 启动顺序

```powershell
# 基础设施 + API
docker-compose up --build -d
# 或 make start

# 健康检查
make health
# 或浏览器打开 http://127.0.0.1:8000/api/v1/health

# Gradio（宿主机）
uv sync
uv run python gradio_launcher.py
```

## 入库

不依赖调度器，两种方式：

1. **Gradio**「抓取论文」页：填领域 / 日期 / 篇数，可选下载 PDF  
2. **脚本：**

```powershell
uv run python scripts/ingest.py --categories cs.AI --max 15
```

PDF 解析冒烟：

```powershell
uv run python scripts/test_pdf_parse.py
```

## 常用命令

```powershell
docker-compose ps
docker-compose logs -f api
docker-compose restart api     # 含飞书 bot
docker-compose down
```

Windows 无 `docker compose` 插件时用 `docker-compose`。

## 配置要点

- 生成：`DEEPSEEK_*`（小米 DeepSeek API）
- 向量：`JINA_API_KEY`（主）或本地 BGE（`BGE_*`）
- PDF：`PDF_PARSER__MAX_PAGES` / `PDF_PARSER__MAX_FILE_SIZE_MB`
- 缓存：`REDIS__*`
- 飞书：`FEISHU__*`（默认 `FEISHU__ENABLED=false`）

见 `.env.example`。

## 排障

| 现象 | 处理 |
|------|------|
| 8000 被占用 | `docker ps` 看是否有其它项目容器占端口 |
| arXiv 429 | 降低篇数、拉长间隔；避免并发入库 |
| 检索有结果但答案差 | 先 `/api/v1/hybrid-search/` 看 chunk，再查 prompt |
| 源文件 404 | PDF 未下载成功；入库时勾选 PDF |
| Docling 首次慢 | 模型在 `~/.cache/huggingface`，已挂载进容器 |

## 构建注意

- API 镜像含 torch/docling，体积大；Docker 盘尽量放空间充足的盘  
- 不要对本项目执行 `docker system prune -a`（会波及其它项目镜像）
