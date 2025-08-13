# Investment Service - Development Automation
# ==================================================

# Configuration
SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[0;37m
RESET := \033[0m

# Project variables
PROJECT_NAME := investment-service
BACKEND_DIR := backend
FRONTEND_DIR := frontend
DOCKER_COMPOSE_DEV := docker-compose.dev.yml
DOCKER_COMPOSE_PROD := docker-compose.dohodometr.yml

# Python variables
PYTHON := python3
PIP := pip
VENV_DIR := $(BACKEND_DIR)/venv
PYTHON_VENV := $(VENV_DIR)/bin/python
PIP_VENV := $(VENV_DIR)/bin/pip

# Node variables
NODE := node
NPM := npm
FRONTEND_NODE_MODULES := $(FRONTEND_DIR)/node_modules

# Docker variables
DOCKER := docker
DOCKER_COMPOSE := docker-compose

# ==================================================
# Help
# ==================================================

help: ## Show this help message
	@echo ""
	@echo "$(CYAN)🚀 Investment Service - Development Commands$(RESET)"
	@echo ""
	@echo "$(YELLOW)📋 Available commands:$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)💡 Examples:$(RESET)"
	@echo "  make setup          # Complete project setup"
	@echo "  make dev            # Start development environment"
	@echo "  make test           # Run all tests"
	@echo "  make lint           # Run all linting"
	@echo "  make clean          # Clean up everything"
	@echo ""

# ==================================================
# Setup and Installation
# ==================================================

setup: ## Complete project setup (first time)
	@echo "$(CYAN)🔧 Setting up Investment Service development environment...$(RESET)"
	@$(MAKE) setup-backend
	@$(MAKE) setup-frontend
	@$(MAKE) setup-hooks
	@$(MAKE) setup-env
	@echo "$(GREEN)✅ Setup complete! Run 'make dev' to start development.$(RESET)"

setup-backend: ## Setup backend environment
	@echo "$(BLUE)🐍 Setting up backend environment...$(RESET)"
	@cd $(BACKEND_DIR) && $(PYTHON) -m venv venv
	@$(PIP_VENV) install --upgrade pip
	@$(PIP_VENV) install -r $(BACKEND_DIR)/requirements-dev.txt
	@echo "$(GREEN)✅ Backend setup complete$(RESET)"

setup-frontend: ## Setup frontend environment
	@echo "$(BLUE)⚛️ Setting up frontend environment...$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) install
	@echo "$(GREEN)✅ Frontend setup complete$(RESET)"

setup-hooks: ## Install pre-commit hooks
	@echo "$(BLUE)🪝 Installing pre-commit hooks...$(RESET)"
	@$(PIP) install pre-commit
	@pre-commit install
	@echo "$(GREEN)✅ Pre-commit hooks installed$(RESET)"

setup-env: ## Copy environment template
	@echo "$(BLUE)⚙️ Setting up environment files...$(RESET)"
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "$(YELLOW)📝 .env file created from template. Please edit it with your settings.$(RESET)"; \
	else \
		echo "$(YELLOW)📝 .env file already exists$(RESET)"; \
	fi

# ==================================================
# Development
# ==================================================

dev: ## Start development environment
	@echo "$(CYAN)🚀 Starting development environment...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_DEV) up -d
	@echo "$(GREEN)✅ Development environment started!$(RESET)"
	@echo ""
	@echo "$(BLUE)🌐 Services available at:$(RESET)"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  Grafana:   http://localhost:3001 (admin/admin)"
	@echo ""

dev-stop: ## Stop development environment
	@echo "$(YELLOW)⏹️ Stopping development environment...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_DEV) down
	@echo "$(GREEN)✅ Development environment stopped$(RESET)"

dev-restart: ## Restart development environment
	@$(MAKE) dev-stop
	@$(MAKE) dev

dev-logs: ## Show development logs
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_DEV) logs -f

dev-status: ## Show development environment status
	@echo "$(BLUE)📊 Development environment status:$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_DEV) ps

# ==================================================
# Backend Development
# ==================================================

backend-shell: ## Open backend shell
	@echo "$(BLUE)🐍 Opening backend shell...$(RESET)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && bash

backend-run: ## Run backend locally (outside Docker)
	@echo "$(BLUE)🐍 Starting backend locally...$(RESET)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-migrate: ## Run database migrations
	@echo "$(BLUE)🗃️ Running database migrations...$(RESET)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && alembic upgrade head
	@echo "$(GREEN)✅ Migrations complete$(RESET)"

backend-migration: ## Create new migration (usage: make backend-migration MSG="description")
	@echo "$(BLUE)🗃️ Creating new migration...$(RESET)"
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)❌ Please provide a message: make backend-migration MSG='description'$(RESET)"; \
		exit 1; \
	fi
	@cd $(BACKEND_DIR) && source venv/bin/activate && alembic revision --autogenerate -m "$(MSG)"
	@echo "$(GREEN)✅ Migration created$(RESET)"

backend-reset-db: ## Reset database (WARNING: This will delete all data)
	@echo "$(RED)⚠️ This will delete all database data. Are you sure? [y/N]$(RESET)"
	@read -r confirm && [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ] || exit 1
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_DEV) down -v
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_DEV) up -d postgres redis minio
	@sleep 5
	@$(MAKE) backend-migrate
	@echo "$(GREEN)✅ Database reset complete$(RESET)"

# ==================================================
# Frontend Development
# ==================================================

frontend-shell: ## Open frontend shell
	@echo "$(BLUE)⚛️ Opening frontend shell...$(RESET)"
	@cd $(FRONTEND_DIR) && bash

frontend-run: ## Run frontend locally (outside Docker)
	@echo "$(BLUE)⚛️ Starting frontend locally...$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) run dev

frontend-build: ## Build frontend for production
	@echo "$(BLUE)⚛️ Building frontend for production...$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) run build
	@echo "$(GREEN)✅ Frontend build complete$(RESET)"

frontend-deps: ## Update frontend dependencies
	@echo "$(BLUE)⚛️ Updating frontend dependencies...$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) update
	@echo "$(GREEN)✅ Frontend dependencies updated$(RESET)"

# ==================================================
# Testing
# ==================================================

test: ## Run all tests
	@echo "$(CYAN)🧪 Running all tests...$(RESET)"
	@$(MAKE) test-backend
	@$(MAKE) test-frontend
	@echo "$(GREEN)✅ All tests complete$(RESET)"

test-backend: ## Run backend tests
	@echo "$(BLUE)🐍 Running backend tests...$(RESET)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && pytest -v --cov=app --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✅ Backend tests complete$(RESET)"

test-frontend: ## Run frontend tests
	@echo "$(BLUE)⚛️ Running frontend tests...$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) run test
	@echo "$(GREEN)✅ Frontend tests complete$(RESET)"

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)🎭 Running E2E tests...$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) run test:e2e
	@echo "$(GREEN)✅ E2E tests complete$(RESET)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)👀 Running tests in watch mode...$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) run test:watch

test-coverage: ## Generate test coverage report
	@echo "$(BLUE)📊 Generating test coverage report...$(RESET)"
	@$(MAKE) test-backend
	@$(MAKE) test-frontend
	@echo "$(GREEN)✅ Coverage reports generated:$(RESET)"
	@echo "  Backend:  $(BACKEND_DIR)/htmlcov/index.html"
	@echo "  Frontend: $(FRONTEND_DIR)/coverage/index.html"

# ==================================================
# Code Quality
# ==================================================

lint: ## Run all linting
	@echo "$(CYAN)🎨 Running all linting...$(RESET)"
	@$(MAKE) lint-backend
	@$(MAKE) lint-frontend
	@echo "$(GREEN)✅ All linting complete$(RESET)"

lint-backend: ## Run backend linting
	@echo "$(BLUE)🐍 Running backend linting...$(RESET)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && ruff check . && ruff format --check .
	@cd $(BACKEND_DIR) && source venv/bin/activate && mypy .
	@echo "$(GREEN)✅ Backend linting complete$(RESET)"

lint-frontend: ## Run frontend linting
	@echo "$(BLUE)⚛️ Running frontend linting...$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) run lint
	@cd $(FRONTEND_DIR) && $(NPM) run type-check
	@echo "$(GREEN)✅ Frontend linting complete$(RESET)"

format: ## Format all code
	@echo "$(CYAN)✨ Formatting all code...$(RESET)"
	@$(MAKE) format-backend
	@$(MAKE) format-frontend
	@echo "$(GREEN)✅ All code formatted$(RESET)"

format-backend: ## Format backend code
	@echo "$(BLUE)🐍 Formatting backend code...$(RESET)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && ruff format .
	@cd $(BACKEND_DIR) && source venv/bin/activate && ruff check . --fix
	@echo "$(GREEN)✅ Backend code formatted$(RESET)"

format-frontend: ## Format frontend code
	@echo "$(BLUE)⚛️ Formatting frontend code...$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) run lint:fix
	@cd $(FRONTEND_DIR) && npx prettier --write .
	@echo "$(GREEN)✅ Frontend code formatted$(RESET)"

# ==================================================
# Security
# ==================================================

security: ## Run security checks
	@echo "$(CYAN)🔒 Running security checks...$(RESET)"
	@$(MAKE) security-backend
	@$(MAKE) security-frontend
	@$(MAKE) security-secrets
	@echo "$(GREEN)✅ Security checks complete$(RESET)"

security-backend: ## Run backend security checks
	@echo "$(BLUE)🐍 Running backend security checks...$(RESET)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && bandit -r app/ -f json -o bandit-report.json || true
	@cd $(BACKEND_DIR) && source venv/bin/activate && safety check || true
	@echo "$(GREEN)✅ Backend security checks complete$(RESET)"

security-frontend: ## Run frontend security checks
	@echo "$(BLUE)⚛️ Running frontend security checks...$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) audit || true
	@echo "$(GREEN)✅ Frontend security checks complete$(RESET)"

security-secrets: ## Check for secrets in code
	@echo "$(BLUE)🔍 Checking for secrets...$(RESET)"
	@detect-secrets scan --baseline .secrets.baseline
	@echo "$(GREEN)✅ Secret scan complete$(RESET)"

# ==================================================
# Production
# ==================================================

build: ## Build production images
	@echo "$(CYAN)🏗️ Building production images...$(RESET)"
	@$(DOCKER) build -t $(PROJECT_NAME)-backend:latest $(BACKEND_DIR)
	@$(DOCKER) build -t $(PROJECT_NAME)-frontend:latest $(FRONTEND_DIR)
	@echo "$(GREEN)✅ Production images built$(RESET)"

deploy: ## Deploy to production
	@echo "$(CYAN)🚀 Deploying to production...$(RESET)"
	@echo "$(YELLOW)⚠️ Make sure you have configured your production environment!$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_PROD) up -d
	@echo "$(GREEN)✅ Deployment complete$(RESET)"

backup: ## Create database backup
	@echo "$(BLUE)💾 Creating database backup...$(RESET)"
	@mkdir -p backups
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_PROD) exec -T postgres pg_dump -U postgres investment_db | gzip > backups/backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "$(GREEN)✅ Backup created in backups/ directory$(RESET)"

# ==================================================
# Monitoring
# ==================================================

logs: ## Show application logs
	@echo "$(BLUE)📋 Showing application logs...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_DEV) logs -f backend frontend

logs-backend: ## Show backend logs
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_DEV) logs -f backend

logs-frontend: ## Show frontend logs
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_DEV) logs -f frontend

logs-db: ## Show database logs
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_DEV) logs -f postgres

health: ## Check service health
	@echo "$(BLUE)🏥 Checking service health...$(RESET)"
	@curl -s http://localhost:8000/health || echo "$(RED)❌ Backend health check failed$(RESET)"
	@curl -s http://localhost:3000 > /dev/null && echo "$(GREEN)✅ Frontend is responding$(RESET)" || echo "$(RED)❌ Frontend health check failed$(RESET)"

# ==================================================
# Utilities
# ==================================================

clean: ## Clean up development environment
	@echo "$(YELLOW)🧹 Cleaning up development environment...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_DEV) down -v --remove-orphans
	@$(DOCKER) system prune -f
	@$(DOCKER) volume prune -f
	@echo "$(GREEN)✅ Cleanup complete$(RESET)"

clean-full: ## Full cleanup including built images
	@echo "$(RED)🗑️ Performing full cleanup (including images)...$(RESET)"
	@$(MAKE) clean
	@$(DOCKER) image prune -a -f
	@echo "$(GREEN)✅ Full cleanup complete$(RESET)"

update-deps: ## Update all dependencies
	@echo "$(CYAN)⬆️ Updating all dependencies...$(RESET)"
	@$(MAKE) update-backend-deps
	@$(MAKE) update-frontend-deps
	@echo "$(GREEN)✅ All dependencies updated$(RESET)"

update-backend-deps: ## Update backend dependencies
	@echo "$(BLUE)🐍 Updating backend dependencies...$(RESET)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && pip install --upgrade pip
	@cd $(BACKEND_DIR) && source venv/bin/activate && pip-review --auto || pip list --outdated
	@echo "$(GREEN)✅ Backend dependencies updated$(RESET)"

update-frontend-deps: ## Update frontend dependencies
	@$(MAKE) frontend-deps

shell: ## Open project shell with environment loaded
	@echo "$(BLUE)🐚 Opening project shell...$(RESET)"
	@bash

db-shell: ## Connect to database shell
	@echo "$(BLUE)🗃️ Opening database shell...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_DEV) exec postgres psql -U postgres -d investment_db

redis-shell: ## Connect to Redis shell
	@echo "$(BLUE)📦 Opening Redis shell...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_DEV) exec redis redis-cli

# ==================================================
# Documentation
# ==================================================

docs: ## Generate documentation
	@echo "$(BLUE)📚 Generating documentation...$(RESET)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && mkdocs build
	@echo "$(GREEN)✅ Documentation generated$(RESET)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)📚 Serving documentation at http://localhost:8001...$(RESET)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && mkdocs serve -a 0.0.0.0:8001

# ==================================================
# Git Hooks and Validation
# ==================================================

hooks: ## Run pre-commit hooks on all files
	@echo "$(BLUE)🪝 Running pre-commit hooks...$(RESET)"
	@pre-commit run --all-files
	@echo "$(GREEN)✅ Pre-commit hooks complete$(RESET)"

validate: ## Validate project setup
	@echo "$(CYAN)✅ Validating project setup...$(RESET)"
	@$(MAKE) lint
	@$(MAKE) test
	@$(MAKE) security
	@echo "$(GREEN)✅ Project validation complete$(RESET)"

# ==================================================
# CI/CD Simulation
# ==================================================

ci: ## Simulate CI pipeline locally
	@echo "$(CYAN)🚀 Simulating CI pipeline...$(RESET)"
	@$(MAKE) lint
	@$(MAKE) security
	@$(MAKE) test
	@$(MAKE) build
	@echo "$(GREEN)✅ CI simulation complete$(RESET)"

# ==================================================
# Quick Commands
# ==================================================

quick-start: setup dev ## Quick start: setup and run development environment

quick-test: lint test ## Quick test: lint and test

quick-fix: format lint ## Quick fix: format and lint code

# ==================================================
# Platform-specific targets
# ==================================================

install-mac: ## Install dependencies on macOS
	@echo "$(BLUE)🍎 Installing macOS dependencies...$(RESET)"
	@brew install python@3.12 node@20 docker docker-compose
	@$(MAKE) setup

install-ubuntu: ## Install dependencies on Ubuntu
	@echo "$(BLUE)🐧 Installing Ubuntu dependencies...$(RESET)"
	@sudo apt update
	@sudo apt install -y python3.12 python3.12-venv nodejs npm docker.io docker-compose-v2
	@$(MAKE) setup

# ==================================================
# Debug and Troubleshooting
# ==================================================

debug: ## Show debug information
	@echo "$(CYAN)🐞 Debug Information$(RESET)"
	@echo ""
	@echo "$(BLUE)Environment:$(RESET)"
	@echo "  Python: $$(python3 --version 2>/dev/null || echo 'Not installed')"
	@echo "  Node: $$(node --version 2>/dev/null || echo 'Not installed')"
	@echo "  Docker: $$(docker --version 2>/dev/null || echo 'Not installed')"
	@echo "  Docker Compose: $$(docker-compose --version 2>/dev/null || echo 'Not installed')"
	@echo ""
	@echo "$(BLUE)Project Status:$(RESET)"
	@echo "  Backend venv: $$([ -d $(VENV_DIR) ] && echo 'Exists' || echo 'Missing')"
	@echo "  Frontend node_modules: $$([ -d $(FRONTEND_NODE_MODULES) ] && echo 'Exists' || echo 'Missing')"
	@echo "  Environment file: $$([ -f .env ] && echo 'Exists' || echo 'Missing')"
	@echo ""

troubleshoot: ## Common troubleshooting steps
	@echo "$(CYAN)🔧 Running troubleshooting steps...$(RESET)"
	@echo ""
	@echo "$(BLUE)1. Checking Docker...$(RESET)"
	@docker --version || echo "$(RED)❌ Docker not found$(RESET)"
	@echo ""
	@echo "$(BLUE)2. Checking network conflicts...$(RESET)"
	@docker network ls | grep youinvest || echo "$(GREEN)✅ No network conflicts$(RESET)"
	@echo ""
	@echo "$(BLUE)3. Checking port conflicts...$(RESET)"
	@lsof -i :3000,8000,5432,6379 || echo "$(GREEN)✅ No port conflicts$(RESET)"
	@echo ""
	@echo "$(BLUE)4. Checking disk space...$(RESET)"
	@df -h . | tail -1
	@echo ""
	@echo "$(GREEN)✅ Troubleshooting complete$(RESET)"

# ==================================================
# Special targets
# ==================================================

.PHONY: $(BACKEND_DIR)/venv
$(BACKEND_DIR)/venv:
	@$(MAKE) setup-backend

.PHONY: $(FRONTEND_NODE_MODULES)
$(FRONTEND_NODE_MODULES):
	@$(MAKE) setup-frontend

# Ensure required commands are available
check-python:
	@which python3 > /dev/null || (echo "$(RED)❌ Python 3 is required$(RESET)" && exit 1)

check-node:
	@which node > /dev/null || (echo "$(RED)❌ Node.js is required$(RESET)" && exit 1)

check-docker:
	@which docker > /dev/null || (echo "$(RED)❌ Docker is required$(RESET)" && exit 1)

# ==================================================
# Development shortcuts
# ==================================================

be: backend-run ## Shortcut: Run backend
fe: frontend-run ## Shortcut: Run frontend
mg: backend-migrate ## Shortcut: Run migrations
db: db-shell ## Shortcut: Open database shell
ht: health ## Shortcut: Health check
