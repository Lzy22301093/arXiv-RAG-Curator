FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS base

WORKDIR /app

# Copy configuration files
COPY pyproject.toml uv.lock ./

# UV_COMPILE_BYTECODE for generating .pyc files -> faster application startup.
# UV_LINK_MODE=copy to silence warnings about not being able to use hard links
# since the cache and sync target are on separate file systems.
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_HTTP_TIMEOUT=300

# Install dependencies (plain RUN for classic builder / no buildx)
RUN uv sync --frozen --no-dev

# Copy source code
COPY src /app/src

# Note: BGE model will be downloaded at first startup (not during build)
# This avoids network issues during Docker build
# Set HF_HOME to persist model downloads across container restarts
ENV HF_HOME=/app/.cache/huggingface
ENV HF_ENDPOINT=https://hf-mirror.com

FROM python:3.12.8-slim AS final

EXPOSE 8000

# PYTHONUNBUFFERED=1 to disable output buffering
ENV PYTHONUNBUFFERED=1
ARG VERSION=0.1.0
ENV APP_VERSION=$VERSION

WORKDIR /app

# Copy the virtual environment from the base stage
COPY --from=base /app /app

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"] 