.PHONY: help setup install lint format format-check test typecheck build clean doctor dev infra-up infra-down infra-status infra-logs

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: install infra-up doctor ## Full development environment setup

install: ## Install all dependencies (pnpm + uv)
	pnpm install
	uv sync --all-packages

lint: ## Run all linters
	pnpm exec biome check packages/ apps/
	uv run ruff check packages/ apps/

format: ## Format all code
	pnpm exec biome check --write packages/ apps/
	uv run ruff format packages/ apps/

format-check: ## Check formatting without changes
	pnpm exec biome check packages/ apps/
	uv run ruff format --check packages/ apps/

test: ## Run all tests
	pnpm turbo test
	uv run pytest

typecheck: ## Run type checkers
	uv run pyright

build: ## Build all packages
	pnpm turbo build

clean: ## Clean build artifacts
	pnpm turbo clean
	rm -rf .turbo
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf packages/*/dist apps/*/dist

doctor: ## Check development environment
	@echo "=== Environment Check ==="
	@command -v node >/dev/null 2>&1 && echo "  node    $$(node --version)" || echo "  node    (not found)"
	@command -v pnpm >/dev/null 2>&1 && echo "  pnpm    $$(pnpm --version)" || echo "  pnpm    (not found)"
	@command -v uv >/dev/null 2>&1 && echo "  uv      $$(uv --version)" || echo "  uv      (not found)"
	@command -v python3 >/dev/null 2>&1 && echo "  python  $$(python3 --version)" || echo "  python  (not found)"
	@command -v docker >/dev/null 2>&1 && echo "  docker  $$(docker --version | cut -d' ' -f3 | tr -d ',')" || echo "  docker  (not found)"
	@echo ""

dev: ## Start development services (Docker + dev servers)
	$(MAKE) infra-up

infra-up: ## Start Docker infrastructure services (PostgreSQL, Redis)
	docker compose up -d

infra-down: ## Stop Docker infrastructure services
	docker compose down

infra-status: ## Show infrastructure service status
	docker compose ps

infra-logs: ## Follow infrastructure service logs
	docker compose logs -f
