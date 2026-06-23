.PHONY: help db-up db-down db-reset api api-test api-lint web web-build web-lint test check

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# === Database ===

db-up: ## Start PostgreSQL
	docker compose up -d db
	@echo "Waiting for PostgreSQL..."
	@sleep 3
	@docker compose exec db pg_isready -U novel_forge

db-down: ## Stop PostgreSQL
	docker compose down

db-reset: ## Reset database (destroy and recreate)
	docker compose down -v
	docker compose up -d db
	@sleep 3

# === Backend ===

api: ## Start FastAPI dev server
	cd apps/api && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

api-test: ## Run backend tests
	cd apps/api && uv run pytest -v

api-lint: ## Lint backend code
	cd apps/api && uv run ruff check .
	cd apps/api && uv run ruff format --check .

api-format: ## Format backend code
	cd apps/api && uv run ruff format .

api-migrate: ## Generate Alembic migration
	cd apps/api && uv run alembic revision --autogenerate -m "$(msg)"

api-upgrade: ## Apply migrations
	cd apps/api && uv run alembic upgrade head

# === Frontend ===

web: ## Start Next.js dev server
	cd apps/web && pnpm dev --port 3001

web-build: ## Build frontend
	cd apps/web && pnpm build

web-lint: ## Lint frontend code
	cd apps/web && pnpm lint

web-typecheck: ## TypeScript type check
	cd apps/web && pnpm tsc --noEmit

# === All ===

test: api-test ## Run all tests

check: api-lint api-test web-lint web-typecheck ## Run all checks
