.PHONY: help start stop restart status logs health setup format lint test test-cov clean

# Prefer Docker Compose v2 plugin; fall back to standalone docker-compose.exe (Windows)
COMPOSE := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Service management
start: ## Start all services
	$(COMPOSE) up --build -d

stop: ## Stop all services
	$(COMPOSE) down

restart: ## Restart all services
	$(COMPOSE) restart

status: ## Show service status
	$(COMPOSE) ps

logs: ## Show service logs
	$(COMPOSE) logs -f

# Health checks
health: ## Check all services health
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq . || echo "API not responding"
	@curl -s http://localhost:9200/_cluster/health | jq . || echo "OpenSearch not responding"

# Development
setup: ## Install Python dependencies
	uv sync

format: ## Format code
	uv run ruff format

lint: ## Lint and type check
	uv run ruff check --fix
	uv run mypy src/

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=src --cov-report=html

# Cleanup
clean: ## Clean up everything
	$(COMPOSE) down -v
	docker system prune -f