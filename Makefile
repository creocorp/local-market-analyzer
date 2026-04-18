.PHONY: help install dev backend frontend build clean lint

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Install ────────────────────────────────────────────

install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install backend Python dependencies
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -e "."

install-frontend: ## Install frontend Node dependencies
	cd frontend && npm install

# ── Development ────────────────────────────────────────

dev: ## Run backend + frontend concurrently
	@echo "Starting backend on :8000 and frontend on :5173..."
	@$(MAKE) -j2 backend frontend

backend: ## Start FastAPI backend (port 8000)
	cd backend && . .venv/bin/activate && uvicorn app.api.app:app --reload --host 0.0.0.0 --port 8000

frontend: ## Start Vite dev server (port 5173)
	cd frontend && npm run dev

# ── Build ──────────────────────────────────────────────

build: build-frontend ## Build for production

build-frontend: ## Build frontend for production
	cd frontend && npm run build

# ── Quality ────────────────────────────────────────────

lint: lint-backend lint-frontend ## Lint all code

lint-backend: ## Lint Python code with ruff
	cd backend && . .venv/bin/activate && ruff check app/

lint-frontend: ## Lint frontend with eslint
	cd frontend && npm run lint

typecheck: ## Type-check frontend
	cd frontend && npx tsc --noEmit

# ── Setup ──────────────────────────────────────────────

setup: install env ## Full project setup

env: ## Copy .env.example to .env if missing
	@test -f backend/.env || cp backend/.env.example backend/.env && echo "Created backend/.env"

# ── Clean ──────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	rm -rf frontend/dist
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
