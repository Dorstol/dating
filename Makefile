.PHONY: help install format lint typecheck test check clean \
       run run-bot run-web \
       up down logs restart build \
       prod-up prod-down prod-logs prod-build prod-restart \
       migrate migrate-down migrate-new migrate-history \
       seed backup shell db-shell redis-shell

# ─── Help ─────────────────────────────────────────────────────────
help: ## Show available commands
	@echo "Usage: make <command>\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Setup ────────────────────────────────────────────────────────
install: ## Install all dependencies (dev included)
	uv sync --group dev
	cd web && npm install

# ─── Code Quality ─────────────────────────────────────────────────
format: ## Format code (ruff)
	uv run ruff format app_src/ bot/
	uv run ruff check --fix app_src/ bot/

lint: ## Run linter
	uv run ruff check app_src/ bot/
	uv run ruff format --check app_src/ bot/

typecheck: ## Run mypy type checker
	uv run mypy app_src/ bot/ --ignore-missing-imports

test: ## Run all tests
	uv run pytest -v

test-api: ## Run backend tests only
	uv run pytest app_src/tests/ -v

test-bot: ## Run bot tests only
	uv run pytest bot/tests/ -v

test-cov: ## Run tests with coverage
	uv run pytest --cov=app_src --cov=bot --cov-report=term-missing

check: format lint test ## Format, lint, and test (full CI check)

# ─── Run Locally ──────────────────────────────────────────────────
run: ## Run API server (dev mode with reload)
	uv run python app_src/main.py

run-bot: ## Run Telegram bot
	uv run python -m bot

run-web: ## Run Vue frontend (dev server)
	cd web && npm run dev

# ─── Docker (dev) ────────────────────────────────────────────────
up: ## Start dev Docker services
	docker compose up -d

down: ## Stop dev Docker services
	docker compose down

logs: ## Tail dev Docker logs
	docker compose logs -f

restart: ## Restart dev Docker services
	docker compose restart

build: ## Rebuild dev Docker images
	docker compose build --no-cache

# ─── Docker (production) ─────────────────────────────────────────
prod-up: ## Start production stack
	docker compose -f docker-compose.prod.yml up -d --build

prod-down: ## Stop production stack
	docker compose -f docker-compose.prod.yml down

prod-logs: ## Tail production logs
	docker compose -f docker-compose.prod.yml logs -f

prod-build: ## Rebuild production images
	docker compose -f docker-compose.prod.yml build --no-cache

prod-restart: ## Restart production stack
	docker compose -f docker-compose.prod.yml restart

# ─── Database ─────────────────────────────────────────────────────
migrate: ## Apply all pending migrations
	uv run alembic upgrade head

migrate-down: ## Rollback one migration
	uv run alembic downgrade -1

migrate-new: ## Create new migration (usage: make migrate-new msg="add users table")
	uv run alembic revision --autogenerate -m "$(msg)"

migrate-history: ## Show migration history
	uv run alembic history

seed: ## Seed database with test data
	uv run python scripts/seed.py

backup: ## Backup PostgreSQL database
	./scripts/backup-db.sh

# ─── Shell Access ─────────────────────────────────────────────────
shell: ## Open Python shell with app context
	uv run python -i -c "import asyncio; from app_src.core.models import db_helper; print('db_helper available')"

db-shell: ## Open psql shell (Docker)
	docker compose exec pg psql -U user -d dating

redis-shell: ## Open redis-cli (Docker)
	docker compose exec redis redis-cli

# ─── Cleanup ──────────────────────────────────────────────────────
clean: ## Remove caches and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
