.PHONY: setup dev test lint typecheck clean help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install development dependencies
	@echo "No build tooling configured yet. See docs/development/ for planned setup instructions."

dev: ## Run development server
	@echo "No development server configured yet."

test: ## Run all tests
	@echo "Running test suite..."

test-unit: ## Run unit tests only
	@echo "Running unit tests..."

test-integration: ## Run integration tests only
	@echo "Running integration tests..."

test-e2e: ## Run end-to-end tests only
	@echo "Running end-to-end tests..."

lint: ## Run linters
	@echo "Running linters..."

typecheck: ## Run type checkers
	@echo "Running type checkers..."

clean: ## Clean build artifacts
	@echo "Cleaning build artifacts..."

build: ## Build all components
	@echo "Building all components..."
