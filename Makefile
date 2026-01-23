.PHONY: help uv-sync uv-install uv-install-dev uv-install-ci uv-status uv-clean install install-full install-core install-conda dev-install quick-start quick-start-minimal start stop restart down logs clean test-api test-endpoints demo check-services logs-api logs-docker clean-logs reset-all dev-all dev-api-only api init-db setup-dashboards

help: ## Show this help message
	@echo "🚀 Urbanclear - Smart City Traffic Optimization System"
	@echo ""
	@echo "📋 Available commands:"
	@echo ""
	@echo "🚀 UV Package Management:"
	@echo "  uv-sync          Sync dependencies with uv.lock"
	@echo "  uv-install       Install all dependencies"
	@echo "  uv-install-dev   Install with development dependencies"
	@echo "  uv-install-ci    Install with CI dependencies"
	@echo "  uv-status        Check uv environment status"
	@echo "  uv-clean         Clean uv cache and lock file"
	@echo ""
	@echo "📦 Installation:"
	@echo "  install          Install minimal dependencies"
	@echo "  install-full     Install all ML/AI packages"
	@echo "  install-core     Install essential packages only"
	@echo "  install-conda    Install with conda"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  quick-start      Complete setup with minimal deps"
	@echo "  quick-start-minimal  Basic setup only"
	@echo ""
	@echo "🐳 Docker Services:"
	@echo "  start           Start Docker services"
	@echo "  stop            Stop Docker services"
	@echo "  restart         Restart Docker services"
	@echo "  down            Stop and remove containers"
	@echo ""
	@echo "🌐 API & Testing:"
	@echo "  api             Start API server"
	@echo "  test-api        Test API functionality"
	@echo "  test-endpoints  Test with curl"
	@echo "  demo            Run demo endpoints"
	@echo ""
	@echo "📊 Database & Setup:"
	@echo "  init-db         Initialize database"
	@echo "  setup-dashboards Setup Grafana dashboards"
	@echo ""
	@echo "🔍 Monitoring & Health:"
	@echo "  check-services  Check service status"
	@echo "  health-check    Comprehensive health check"
	@echo "  system-status   Quick status check"
	@echo "  logs-api        View API logs"
	@echo "  logs-docker     View Docker logs"
	@echo ""
	@echo "🔧 Fixes & Restarts:"
	@echo "  quick-fix       Auto-fix common issues"
	@echo "  restart-api     Restart API server only"
	@echo "  restart-dashboard Restart dashboard only"
	@echo "  fix-all         Nuclear option: reset everything"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  clean           Clean build artifacts"
	@echo "  clean-logs      Clean log files"
	@echo "  reset-all       Reset entire system"
	@echo ""
	@echo "💡 Tip: Use uv for fast dependency management!"
	@echo "   uv sync  # Install dependencies"
	@echo "   uv run python script.py  # Run scripts"

# UV Package Management commands
uv-sync:
	@echo "🔄 Syncing dependencies with uv..."
	uv sync

uv-install:
	@echo "🔧 Installing all Urbanclear dependencies with uv..."
	uv sync

uv-install-dev:
	@echo "🔧 Installing with development dependencies..."
	uv sync --extra dev

uv-install-ci:
	@echo "🔧 Installing with CI dependencies..."
	uv sync --extra ci

uv-status:
	@echo "🔍 UV Environment Status:"
	@echo "Current Python: $$(which python)"
	@echo "Python version: $$(python --version)"
	@echo "UV version: $$(uv --version)"
	@echo "Lock file: $$(if [ -f uv.lock ]; then echo "✅ Present"; else echo "❌ Missing"; fi)"

uv-clean:
	@echo "🧹 Cleaning uv cache and lock file..."
	rm -f uv.lock
	uv cache clean
	@echo "✅ UV cache cleaned"

# Installation commands (legacy - now use uv commands above)
install: uv-install
	@echo "✅ Dependencies installed with uv"

install-full: uv-install
	@echo "✅ All dependencies installed with uv"

install-core:
	@echo "🔧 Installing core dependencies only..."
	uv add fastapi uvicorn pydantic pydantic-settings pandas numpy loguru requests python-dotenv pyyaml psycopg2-binary

dev-install: uv-install-dev
	@echo "✅ Development dependencies installed with uv"

start: ## Start all services with Docker Compose
	docker-compose up -d

stop: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

run-system: ## Start the complete Urbanclear system (Docker + API)
	@echo "🚀 Starting complete Urbanclear system..."
	make start
	sleep 5
	make api

quick-demo: ## Quick demo setup with sample data
	@echo "🎭 Setting up quick demo..."
	make start
	sleep 10
	make init-db
	make api

run-simple: ## Start simplified Urbanclear system (API only)
	@echo "🚀 Starting simplified Urbanclear system..."
	make api

init-db: ## Initialize the database
	uv run python scripts/init_database.py

api: ## Start the API server in development mode
	uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	uv run pytest tests/ -v

test-quick: ## Run quick tests only
	uv run pytest tests/unit/ -v --tb=short

lint: ## Run linting
	uv run ruff check src/ tests/
	uv run black --check src/ tests/

format: ## Format code
	uv run ruff check --fix src/ tests/
	uv run black src/ tests/
	uv run isort src/ tests/

clean: ## Clean temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/
	rm -rf .mypy_cache/ .ruff_cache/

clean-all: clean uv-clean ## Clean everything including uv cache
	rm -rf .venv/

setup-env: ## Set up development environment
	uv run python scripts/dev_setup.py

health: ## Check system health
	curl -s http://localhost:8000/health | python -m json.tool

dashboards: ## Open Grafana dashboards in browser
	@echo "Opening Grafana dashboards..."
	@echo "URL: http://localhost:3000"
	@echo "Username: admin"
	@echo "Password: grafana_password"
	@if command -v open >/dev/null 2>&1; then open http://localhost:3000; fi
	@if command -v xdg-open >/dev/null 2>&1; then xdg-open http://localhost:3000; fi

metrics: ## Show Prometheus metrics endpoint
	@echo "Prometheus metrics available at:"
	@echo "- API metrics: http://localhost:8000/metrics"
	@echo "- Prometheus UI: http://localhost:9090"
	@if curl -s http://localhost:8000/metrics >/dev/null 2>&1; then \
		echo "✓ API metrics endpoint is accessible"; \
	else \
		echo "✗ API metrics endpoint is not accessible"; \
	fi

monitor: ## Start only monitoring services (Prometheus + Grafana)
	docker-compose up -d prometheus grafana postgres-exporter redis-exporter

monitoring-status: ## Check status of monitoring services
	@echo "Monitoring Services Status:"
	@echo "=========================="
	@docker-compose ps prometheus grafana postgres-exporter redis-exporter

setup-dashboards: ## Setup and verify dashboard system
	uv run python scripts/setup_dashboards.py

# Testing commands
test-api:
	@echo "🧪 Testing API functionality..."
	uv run python scripts/test_api.py

test-endpoints:
	@echo "🌐 Testing API endpoints with curl..."
	@echo "Testing health endpoint..."
	curl -s http://localhost:8000/health | jq .
	@echo "\nTesting current traffic..."
	curl -s "http://localhost:8000/api/v1/traffic/current" | jq '.[:2]'
	@echo "\nTesting analytics..."
	curl -s "http://localhost:8000/api/v1/analytics/summary?period=24h" | jq .

# Demo commands
demo:
	@echo "🎭 Running API demos..."
	@echo "Rush hour simulation:"
	curl -s "http://localhost:8000/api/v1/demo/rush-hour-simulation" | jq .
	@echo "\nLocation filtering demo:"
	curl -s "http://localhost:8000/api/v1/demo/location-filter" | jq .
	@echo "\nAnalytics comparison demo:"
	curl -s "http://localhost:8000/api/v1/demo/analytics-comparison" | jq .

# Quick start command
quick-start: install start init-db
	@echo "🚀 Quick starting Urbanclear system..."
	@sleep 5
	@make test-api
	@echo "✅ System ready! Visit http://localhost:8000/docs for API documentation"

quick-start-minimal: install-core start
	@echo "🚀 Quick starting Urbanclear with minimal dependencies..."
	@sleep 3
	@echo "✅ Basic system ready! Run 'make api' to start the server"

# Alternative installation methods
install-conda:
	@echo "🔧 Installing with conda..."
	conda install -c conda-forge fastapi uvicorn pandas numpy psycopg2 redis-py pyyaml loguru requests

# Monitoring commands
check-services:
	@echo "🔍 Checking service status..."
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

logs-api:
	@echo "📝 API logs..."
	@if [ -f logs/urbanclear.log ]; then tail -f logs/urbanclear.log; else echo "No API logs found. Start the API first."; fi

logs-docker:
	@echo "📝 Docker logs..."
	docker-compose logs -f --tail=50

# Enhanced development
dev-all: start init-db api
	@echo "🔥 Full development environment started!"

dev-api-only:
	@echo "🔧 Starting API in development mode..."
	cd src && uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Cleanup commands
clean-logs:
	@echo "🧹 Cleaning logs..."
	rm -rf logs/*
	mkdir -p logs

reset-all: down clean clean-logs
	@echo "🔄 Resetting entire system..."
	docker system prune -f
	@make quick-start

# UV Environment commands (replacing old venv commands)
uv-create:
	@echo "🚀 Creating uv environment..."
	uv init
	@echo "✅ UV environment created"
	@echo "📝 Run: uv sync  # to install dependencies"

uv-recreate: uv-clean uv-sync
	@echo "🔄 Recreating uv environment..."
	@echo "✅ UV environment recreated with fresh dependencies"

# ==========================================
# System Health & Fixes
# ==========================================

health-check: ## Run comprehensive system health check
	@echo "🔍 Running comprehensive system health check..."
	@uv run python scripts/health_check.py

quick-fix: ## Automatically fix common issues
	@echo "🔧 Running quick fixes..."
	@pkill -f "uvicorn" 2>/dev/null || true
	@sleep 2
	@echo "Starting API server..."
	@uv run python start_api.py &
	@sleep 5
	@echo "✅ Services restarted!"

system-status: ## Check status of all services quickly
	@echo "📊 System Status:"
	@echo "=================="
	@curl -s http://localhost:8000/health 2>/dev/null | python -c "import sys,json; print('API: ' + json.load(sys.stdin)['status'])" || echo "API: Not running"
	@curl -s http://localhost:3000 > /dev/null 2>&1 && echo "React Dashboard: Running" || echo "React Dashboard: Not running"
	@docker ps --format "Docker: {{.Names}}" | head -3 2>/dev/null || echo "Docker: Not running"

restart-api: ## Restart API server only
	@echo "🔄 Restarting API server..."
	@pkill -f uvicorn 2>/dev/null || true
	@sleep 2
	@python run_api.py &
	@echo "✅ API server restarted"

restart-dashboard: ## Restart React dashboard only
	@echo "🔄 Restarting React dashboard..."
	@cd dashboard && npm run dev &
	@echo "✅ Dashboard restarted (run 'cd dashboard && npm run dev' manually)"

fix-all: stop clean quick-fix ## Nuclear option: reset and restart everything
	@echo "💥 Complete system reset and restart..."
	@sleep 3
	@make start
	@sleep 10
	@make init-db
	@echo "🎉 System completely refreshed!"

