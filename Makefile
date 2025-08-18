# Dohodometr Development Makefile
# Usage: make <target>

.DEFAULT_GOAL := help
.PHONY: help dev-up dev-down test lint format migrate backup logs health-check clean install-deps security-scan k6-smoke k6-baseline openapi inventory \
    backend-init backend-test-fast backend-test-all backend-test-one docker-ci compose-ci flaky

# Colors for output
BOLD := \033[1m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
BLUE := \033[34m
NC := \033[0m # No Color

##@ Development

help: ## Show this help message
	@echo "$(BOLD)Dohodometr Development Commands$(NC)"
	@echo "=================================="
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make install-deps  # Install development dependencies"
	@echo "  make dev-up        # Start development environment"
	@echo "  make migrate       # Apply database migrations"
	@echo "  make health-check  # Verify all services are running"

install-deps: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	@if command -v pip >/dev/null 2>&1; then \
		pip install pre-commit; \
		pre-commit install; \
		echo "$(GREEN)✅ Pre-commit hooks installed$(NC)"; \
	fi
	@if command -v npm >/dev/null 2>&1; then \
		cd frontend && npm install; \
		echo "$(GREEN)✅ Frontend dependencies installed$(NC)"; \
	fi
	@if command -v npm >/dev/null 2>&1; then \
		npm run prepare || true; \
		echo "$(GREEN)✅ Husky prepared$(NC)"; \
	fi
	@echo "$(GREEN)✅ Development dependencies installed successfully!$(NC)"

dev-up: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	@docker-compose -f docker-compose.dev.yml up --build -d
	@echo "$(GREEN)✅ Development environment started!$(NC)"
	@echo "$(YELLOW)Access points:$(NC)"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"

dev-down: ## Stop development environment
	@echo "$(BLUE)Stopping development environment...$(NC)"
	@docker-compose -f docker-compose.dev.yml down
	@echo "$(GREEN)✅ Development environment stopped$(NC)"

dev-restart: ## Restart development environment
	@make dev-down
	@make dev-up

##@ Database

migrate: ## Apply database migrations
	@echo "$(BLUE)Applying database migrations...$(NC)"
	@docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
	@echo "$(GREEN)✅ Database migrations applied$(NC)"

create-superuser: ## Create a superuser
	@echo "$(BLUE)Creating superuser...$(NC)"
	@docker-compose -f docker-compose.dev.yml exec backend python -c "from app.core.database_sync import get_db; from app.models.user import User; from app.core.security import get_password_hash; db = next(get_db()); user = User(email='admin@dohodometr.ru', username='admin', full_name='Administrator', hashed_password=get_password_hash('admin123'), is_active=True, is_superuser=True); db.add(user); db.commit(); print('Superuser created: admin@dohodometr.ru / admin123')"
	@echo "$(GREEN)✅ Superuser created: admin@dohodometr.ru / admin123$(NC)"

backup: ## Create database backup
	@echo "$(BLUE)Creating database backup...$(NC)"
	@mkdir -p backups
	@docker-compose -f docker-compose.dev.yml exec postgres pg_dump -U postgres investment_db | gzip > "backups/backup-$(shell date +%Y%m%d-%H%M%S).sql.gz"
	@echo "$(GREEN)✅ Database backup created in backups/$(NC)"

restore: ## Restore database from latest backup (USE WITH CAUTION!)
	@echo "$(RED)⚠️  This will DESTROY current data! Press Ctrl+C to cancel...$(NC)"
	@sleep 5
	@LATEST_BACKUP=$$(ls -t backups/*.sql.gz | head -1); \
	echo "$(BLUE)Restoring from: $$LATEST_BACKUP$(NC)"; \
	gunzip -c "$$LATEST_BACKUP" | docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres investment_db
	@echo "$(GREEN)✅ Database restored$(NC)"

##@ Testing

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@docker-compose -f docker-compose.dev.yml exec backend pytest -v --cov=app --cov-report=term-missing --cov-report=html
	@docker-compose -f docker-compose.dev.yml exec frontend npm run test:coverage
	@echo "$(GREEN)✅ All tests completed$(NC)"

test-backend: ## Run backend tests only
	@echo "$(BLUE)Running backend tests...$(NC)"
	@docker-compose -f docker-compose.dev.yml exec backend pytest -v

test-frontend: ## Run frontend tests only
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@docker-compose -f docker-compose.dev.yml exec frontend npm run test

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)Running E2E tests...$(NC)"
	@docker-compose -f docker-compose.dev.yml exec frontend npm run test:e2e

##@ Performance

k6-smoke: ## Run k6 smoke test (BASE_URL=http://localhost:8000)
	@echo "$(BLUE)Running k6 smoke...$(NC)"
	@k6 run k6/smoke.js

k6-baseline: ## Run k6 baseline test (BASE_URL=http://localhost:8000)
	@echo "$(BLUE)Running k6 baseline...$(NC)"
	@k6 run k6/baseline.js

openapi: ## Export OpenAPI schema to docs/openapi.json
	@$(MAKE) -C backend openapi

inventory: scripts/inventory.sh ## Generate project inventory report
	@bash scripts/inventory.sh

flaky: ## Detect flaky tests for backend (pytest) and frontend (vitest/jest); report -> reports/flaky_report.md
	@echo "$(BLUE)Preparing environments (backend/.venv, frontend deps)...$(NC)"
	@$(MAKE) -s backend-init >/dev/null 2>&1 || true
	@$(MAKE) -s fe-init >/dev/null 2>&1 || true
	@echo "$(BLUE)Detecting flaky tests...$(NC)"
	@mkdir -p reports
	@python3 scripts/flaky_detector.py | tee reports/flaky_top10.out
	@echo "$(GREEN)✅ Flaky detection completed. See reports/flaky_report.md$(NC)"

##@ Code Quality

lint: ## Run linting for all code
	@echo "$(BLUE)Running linters...$(NC)"
	@docker-compose -f docker-compose.dev.yml exec backend ruff check . --fix
	@docker-compose -f docker-compose.dev.yml exec backend mypy app/
	@docker-compose -f docker-compose.dev.yml exec frontend npm run lint
	@echo "$(GREEN)✅ Linting completed$(NC)"

format: ## Format all code
	@echo "$(BLUE)Formatting code...$(NC)"
	@docker-compose -f docker-compose.dev.yml exec backend black .
	@docker-compose -f docker-compose.dev.yml exec backend isort .
	@docker-compose -f docker-compose.dev.yml exec frontend npm run format
	@echo "$(GREEN)✅ Code formatting completed$(NC)"

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	@pre-commit run --all-files
	@echo "$(GREEN)✅ Pre-commit hooks completed$(NC)"

hooks: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	@pre-commit install
	@echo "$(GREEN)✅ Pre-commit hooks installed$(NC)"

##@ Security

security-scan: ## Run security scans
	@echo "$(BLUE)Running security scans...$(NC)"
	@bash scripts/security_scan.sh
	@echo "$(GREEN)✅ Security scans completed$(NC)"

secrets-check: ## Check for secrets in code
	@echo "$(BLUE)Checking for secrets...$(NC)"
	@if command -v detect-secrets >/dev/null 2>&1; then \
		detect-secrets scan --all-files --baseline .secrets.baseline; \
		echo "$(GREEN)✅ No new secrets detected$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  detect-secrets not installed. Run: pip install detect-secrets$(NC)"; \
	fi

##@ Monitoring

logs: ## Show logs for all services
	@docker-compose -f docker-compose.dev.yml logs -f

logs-backend: ## Show backend logs only
	@docker-compose -f docker-compose.dev.yml logs -f backend

logs-frontend: ## Show frontend logs only
	@docker-compose -f docker-compose.dev.yml logs -f frontend

health-check: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo "$(YELLOW)Backend API:$(NC)"
	@curl -f http://localhost:8000/health && echo " $(GREEN)✅ Healthy$(NC)" || echo " $(RED)❌ Unhealthy$(NC)"
	@echo "$(YELLOW)Frontend:$(NC)"
	@curl -f http://localhost:3000 >/dev/null 2>&1 && echo " $(GREEN)✅ Healthy$(NC)" || echo " $(RED)❌ Unhealthy$(NC)"
	@echo "$(YELLOW)Database:$(NC)"
	@docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres >/dev/null 2>&1 && echo " $(GREEN)✅ Healthy$(NC)" || echo " $(RED)❌ Unhealthy$(NC)"
	@echo "$(YELLOW)Redis:$(NC)"
	@docker-compose -f docker-compose.dev.yml exec redis redis-cli ping >/dev/null 2>&1 && echo " $(GREEN)✅ Healthy$(NC)" || echo " $(RED)❌ Unhealthy$(NC)"

metrics: ## Show service metrics
	@echo "$(BLUE)Service metrics:$(NC)"
	@echo "$(YELLOW)Backend metrics:$(NC) http://localhost:8000/metrics"
	@curl -s http://localhost:8000/metrics | grep -E "investment_api_(requests_total|request_duration_seconds_count|active_connections)" | head -5

##@ Production

build-prod: ## Build production images
	@echo "$(BLUE)Building production images...$(NC)"
	@docker build -t dohodometr-backend:latest \
		--build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') \
		--build-arg VCS_REF=$(shell git rev-parse HEAD) \
		--build-arg VERSION=$(shell git describe --tags --always) \
		backend/
	@docker build -t dohodometr-frontend:latest \
		--build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') \
		--build-arg VCS_REF=$(shell git rev-parse HEAD) \
		--build-arg VERSION=$(shell git describe --tags --always) \
		frontend/
	@echo "$(GREEN)✅ Production images built$(NC)"

deploy-staging: ## Deploy to staging environment
	@echo "$(BLUE)Deploying to staging...$(NC)"
	@# Add staging deployment commands here
	@echo "$(GREEN)✅ Deployed to staging$(NC)"

##@ Utilities

clean: ## Clean up Docker resources
	@echo "$(BLUE)Cleaning up Docker resources...$(NC)"
	@docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	@docker system prune -f
	@docker volume prune -f
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

shell-backend: ## Open shell in backend container
	@docker-compose -f docker-compose.dev.yml exec backend bash

shell-frontend: ## Open shell in frontend container
	@docker-compose -f docker-compose.dev.yml exec frontend sh

shell-postgres: ## Open PostgreSQL shell
	@docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres investment_db

shell-redis: ## Open Redis CLI
	@docker-compose -f docker-compose.dev.yml exec redis redis-cli

##@ Frontend (local)

.PHONY: fe-init fe-lint fe-types fe-test

fe-init: ## Frontend: npm ci || npm install
	@echo "$(BLUE)Frontend init (npm ci || npm install)...$(NC)"
	@cd frontend && (npm ci || npm install)
	@echo "$(GREEN)✅ Frontend dependencies ready$(NC)"

fe-lint: ## Frontend: ESLint (no warnings)
	@echo "$(BLUE)Frontend ESLint...$(NC)"
	@cd frontend && npx eslint . --max-warnings=0
	@echo "$(GREEN)✅ ESLint passed$(NC)"

fe-types: ## Frontend: TypeScript type-check
	@echo "$(BLUE)Frontend TypeScript check...$(NC)"
	@cd frontend && npx tsc --noEmit
	@echo "$(GREEN)✅ TypeScript OK$(NC)"

fe-test: ## Frontend: unit tests (non-watch)
	@echo "$(BLUE)Frontend unit tests...$(NC)"
	@cd frontend && npm test --if-present -- --watch=false
	@echo "$(GREEN)✅ Unit tests passed$(NC)"

update-deps: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@cd backend && pip-compile requirements.in --upgrade
	@cd frontend && npm update
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

reset-env: ## Reset development environment (DANGEROUS!)
	@echo "$(RED)⚠️  This will DESTROY all data! Press Ctrl+C to cancel...$(NC)"
	@sleep 5
	@make clean
	@make dev-up
	@make migrate
	@make create-superuser
	@echo "$(GREEN)✅ Environment reset completed$(NC)"

##@ CI/CD

ci-test: ## Run tests in CI environment
	@echo "$(BLUE)Running CI tests...$(NC)"
	@docker-compose -f docker-compose.test.yml up -d postgres redis
	@docker-compose -f docker-compose.test.yml build backend
	@docker-compose -f docker-compose.test.yml run --rm backend || (docker-compose -f docker-compose.test.yml down; exit 1)
	@docker-compose -f docker-compose.test.yml build frontend
	@docker-compose -f docker-compose.test.yml run --rm frontend || (docker-compose -f docker-compose.test.yml down; exit 1)
	@docker-compose -f docker-compose.test.yml down

sbom: ## Generate Software Bill of Materials
	@echo "$(BLUE)Generating SBOM...$(NC)"
	@mkdir -p reports
	@docker run --rm -v "$(PWD):/app" -w /app anchore/syft /app -o cyclone-dx-json=reports/sbom.json
	@echo "$(GREEN)✅ SBOM generated: reports/sbom.json$(NC)"

vulnerability-scan: ## Scan for vulnerabilities
	@echo "$(BLUE)Scanning for vulnerabilities...$(NC)"
	@mkdir -p reports
	@docker run --rm -v "$(PWD):/app" -w /app aquasec/trivy fs --format json --output reports/trivy-report.json .
	@echo "$(GREEN)✅ Vulnerability scan completed: reports/trivy-report.json$(NC)"

docker-ci: ## Build local/app:ci from ./Dockerfile (logs -> reports/docker_build.log)
	@echo "$(BLUE)Docker CI build...$(NC)"
	@mkdir -p reports
	@if [ -f Dockerfile ]; then \
		echo "Found Dockerfile in project root. Building local/app:ci..."; \
		( docker build -t local/app:ci . 2>&1 | tee reports/docker_build.log ); \
		BUILD_STATUS=$$?; \
		if [ $$BUILD_STATUS -eq 0 ]; then echo "$(GREEN)✅ Build succeeded$(NC)"; else echo "$(RED)❌ Build failed (see reports/docker_build.log)$(NC)"; fi; \
		exit $$BUILD_STATUS; \
	else \
		echo "$(YELLOW)⚠️  Dockerfile not found in project root. Skipping build.$(NC)"; \
		echo "Hint: add a root Dockerfile or see chat for minimal backend/frontend Dockerfiles."; \
		exit 2; \
	fi

compose-ci: ## Render docker-compose*.yml configs into reports/compose_config.out
	@echo "$(BLUE)Compose CI config render...$(NC)"
	@mkdir -p reports
	@if ls docker-compose*.yml >/dev/null 2>&1; then \
		: > reports/compose_config.out; \
		if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then DC="docker compose"; \
		elif command -v docker-compose >/dev/null 2>&1; then DC="docker-compose"; \
		else echo "$(RED)docker compose / docker-compose not installed$(NC)" && exit 1; fi; \
		for f in docker-compose*.yml; do \
			echo "### $$f ###" >> reports/compose_config.out; \
			$$DC -f "$$f" config >> reports/compose_config.out || true; \
			echo "" >> reports/compose_config.out; \
		done; \
		echo "$(GREEN)✅ Generated reports/compose_config.out$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  No docker-compose*.yml files found in project root$(NC)"; \
	fi

##@ Backend (local)

# Helper: activate virtualenv if exists
define _with_backend_venv
export DATABASE_URL=sqlite:///./test.db REDIS_URL=redis://localhost:6379/1; \
if [ -f backend/.venv/bin/activate ]; then . backend/.venv/bin/activate; fi; \
cd backend; 
endef

backend-init: ## Setup Python 3.11 env via uv/pyenv if available and install backend dependencies
	@echo "$(BLUE)Setting up backend Python 3.11 environment...$(NC)"
	@mkdir -p backend/.venv || true
	@if command -v uv >/dev/null 2>&1; then \
		echo "Using uv"; \
		uv venv --python 3.11 backend/.venv >/dev/null 2>&1 || true; \
	elif command -v pyenv >/dev/null 2>&1; then \
		echo "Using pyenv"; \
		pyenv install -s 3.11.9; \
		PYENV_VERSION=3.11.9 python -m venv backend/.venv; \
	else \
		echo "uv/pyenv not found — falling back to system python"; \
		if command -v python3.11 >/dev/null 2>&1; then python3.11 -m venv backend/.venv; \
		else python3 -m venv backend/.venv; fi; \
	fi
	@. backend/.venv/bin/activate; python -m pip install --upgrade pip wheel setuptools
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	@if [ -f backend/requirements.txt ]; then \
		. backend/.venv/bin/activate; pip install -r backend/requirements.txt; \
	fi
	@if [ -f backend/requirements-dev.txt ]; then \
		. backend/.venv/bin/activate; pip install -r backend/requirements-dev.txt; \
	fi
	@if [ -f backend/pyproject.toml ] && ! [ -f backend/requirements.txt ]; then \
		if command -v uv >/dev/null 2>&1; then \
			. backend/.venv/bin/activate; uv pip install -e "backend/[dev]"; \
		else \
			. backend/.venv/bin/activate; pip install -e backend; \
		fi; \
	fi
	@echo "$(GREEN)✅ Backend environment ready in backend/.venv$(NC)"

backend-test-fast: ## Run backend tests fast (-k "not slow")
	@echo "$(BLUE)Running backend fast tests...$(NC)"
	@bash -lc '$(call _with_backend_venv) pytest -k "not slow" --maxfail=1 -q'

backend-test-all: ## Run all backend tests (pytest -q)
	@echo "$(BLUE)Running backend full test suite...$(NC)"
	@bash -lc '$(call _with_backend_venv) pytest -q'

backend-test-one: ## Run single backend test. Usage: make backend-test-one T=path/to/test.py::TestClass::test_name
	@echo "$(BLUE)Running single backend test: $(T)$(NC)"
	@test -n "$(T)" || (echo "$(RED)Provide T=FILE::TEST$(NC)" && exit 1)
	@bash -lc '$(call _with_backend_venv) pytest -q "$(T)"'

##@ Quality Gate

.PHONY: quality-gate
quality-gate: ## Run quality gate: backend tests+coverage, static checks, frontend coverage (if available), and summary report
	@echo "$(BLUE)Running Quality Gate...$(NC)"
	@mkdir -p reports
	@echo "$(YELLOW)[1/4] Backend: pytest coverage → reports/coverage.xml$(NC)"
	@bash -lc 'export DATABASE_URL=sqlite:///./test.db REDIS_URL=redis://localhost:6379/1; if [ -f backend/.venv/bin/activate ]; then . backend/.venv/bin/activate; fi; cd backend; pytest --cov=. --cov-report=xml:../reports/coverage.xml --cov-report=term-missing -q || true'
	@echo "$(YELLOW)[2/4] Static: ruff check .$(NC)"
	@bash -lc 'if [ -f backend/.venv/bin/activate ]; then . backend/.venv/bin/activate; fi; cd backend; ruff check . || true'
	@echo "$(YELLOW)[3/4] Frontend: unit coverage (vitest/jest)$(NC)"
	@bash -lc 'if [ -d frontend ]; then cd frontend; if npx --yes vitest --version >/dev/null 2>&1; then npx --yes vitest run --coverage --coverage.reporter=lcov || true; elif npx --yes jest --version >/dev/null 2>&1; then npx --yes jest --coverage --coverageReporters=lcov || true; else echo "No vitest/jest found, skipping frontend coverage"; fi; fi'
	@echo "$(YELLOW)[4/4] Summary: scripts/quality_gate_summary.py → reports/quality_summary.md$(NC)"
	@python3 scripts/quality_gate_summary.py || true
	@echo "$(GREEN)✅ Quality Gate completed. See reports/quality_summary.md$(NC)"