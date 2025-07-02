.PHONY: help venv-create venv-activate venv-install venv-status venv-deactivate venv-clean venv-recreate install install-full install-core install-conda dev-install quick-start quick-start-minimal start stop restart down logs clean test-api test-endpoints demo check-services logs-api logs-docker clean-logs reset-all dev-all dev-api-only api init-db setup-dashboards

help: ## Show this help message
	@echo "🚀 Urbanclear - Smart City Traffic Optimization System"
	@echo ""
	@echo "📋 Available commands:"
	@echo ""
	@echo "🐍 Virtual Environment:"
	@echo "  venv-create      Create virtual environment"
	@echo "  venv-activate    Show activation command"
	@echo "  venv-install     Install packages in venv"
	@echo "  venv-status      Check venv status"
	@echo "  venv-deactivate  Show deactivation command"
	@echo "  venv-clean       Remove virtual environment"
	@echo "  venv-recreate    Recreate virtual environment"
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
	@echo "💡 Tip: Always activate virtual environment first!"
	@echo "   source urbanclear-env/bin/activate"

# Installation commands
install:
	@echo "🔧 Installing Urbanclear dependencies..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠️  Warning: Virtual environment not activated!"; \
		echo "📝 Consider running: source urbanclear-env/bin/activate"; \
		sleep 2; \
	fi
	pip install --upgrade pip setuptools wheel
	pip install -r requirements-minimal.txt

install-full:
	@echo "🔧 Installing all Urbanclear dependencies (this may take a while)..."
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt

install-core:
	@echo "🔧 Installing core dependencies only..."
	pip install --upgrade pip setuptools wheel
	pip install fastapi uvicorn pydantic pydantic-settings pandas numpy loguru requests python-dotenv pyyaml psycopg2-binary

dev-install: install
	@echo "🔧 Installing development dependencies..."
	pip install pytest pytest-asyncio black flake8 mypy

start: ## Start all services with Docker Compose
	docker-compose up -d

stop: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

run-system: ## Start the complete Urbanclear system (Docker + API + ML + Dashboard)
	@echo "🚀 Starting complete Urbanclear system..."
	python scripts/start_urbanclear.py

quick-demo: ## Quick demo setup with sample data
	@echo "🎭 Setting up quick demo..."
	make start
	sleep 10
	make init-db
	python scripts/start_urbanclear.py

run-simple: ## Start simplified Urbanclear system (API + Dashboard only)
	@echo "🚀 Starting simplified Urbanclear system..."
	python scripts/start_simple.py

init-db: ## Initialize the database
	python scripts/init_database.py

api: ## Start the API server in development mode
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	pytest tests/ -v

lint: ## Run linting
	flake8 src/ tests/
	black --check src/ tests/

format: ## Format code
	black src/ tests/
	isort src/ tests/

clean: ## Clean temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/

setup-env: ## Set up development environment
	python scripts/setup.py

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
	python scripts/setup_dashboards.py

# Testing commands
test-api:
	@echo "🧪 Testing API functionality..."
	python scripts/test_api.py

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
	cd src && python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Cleanup commands
clean-logs:
	@echo "🧹 Cleaning logs..."
	rm -rf logs/*
	mkdir -p logs

reset-all: down clean clean-logs
	@echo "🔄 Resetting entire system..."
	docker system prune -f
	@make quick-start

# Virtual Environment commands
venv-create:
	@echo "🐍 Creating virtual environment..."
	python -m venv urbanclear-env
	@echo "✅ Virtual environment created in urbanclear-env/"
	@echo "📝 Activate with: source urbanclear-env/bin/activate"

venv-activate:
	@echo "📝 To activate virtual environment, run:"
	@echo "   source urbanclear-env/bin/activate"
	@echo "🔍 Check if activated by looking for (urbanclear-env) in your prompt"

venv-install: 
	@echo "🔧 Installing packages in virtual environment..."
	@echo "⚠️  Make sure virtual environment is activated first!"
	pip install --upgrade pip setuptools wheel
	pip install -r requirements-minimal.txt

venv-status:
	@echo "🔍 Virtual Environment Status:"
	@echo "Current Python: $$(which python)"
	@echo "Python version: $$(python --version)"
	@echo "Virtual env: $$VIRTUAL_ENV"
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		echo "✅ Virtual environment is ACTIVATED"; \
	else \
		echo "❌ Virtual environment is NOT activated"; \
		echo "📝 Run: source urbanclear-env/bin/activate"; \
	fi

venv-deactivate:
	@echo "📝 To deactivate virtual environment, run:"
	@echo "   deactivate"

venv-clean:
	@echo "🧹 Removing virtual environment..."
	rm -rf urbanclear-env
	@echo "✅ Virtual environment removed"

venv-recreate: venv-clean venv-create
	@echo "🔄 Recreating virtual environment..."
	@echo "📝 Don't forget to activate: source urbanclear-env/bin/activate"
	@echo "📦 Then install packages: make venv-install"

# ==========================================
# System Health & Fixes
# ==========================================

health-check: ## Run comprehensive system health check
	@echo "🔍 Running comprehensive system health check..."
	@python scripts/health_check.py

quick-fix: ## Automatically fix common issues
	@echo "🔧 Running quick fixes..."
	@pkill -f "uvicorn\|streamlit" 2>/dev/null || true
	@sleep 2
	@echo "Starting API server..."
	@python run_api.py &
	@sleep 5
	@echo "Starting Streamlit dashboard..."
	@nohup streamlit run src/visualization/web_dashboard.py --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false > /dev/null 2>&1 &
	@echo "✅ Services restarted!"

system-status: ## Check status of all services quickly
	@echo "📊 System Status:"
	@echo "=================="
	@curl -s http://localhost:8000/health 2>/dev/null | python -c "import sys,json; print('API: ' + json.load(sys.stdin)['status'])" || echo "API: Not running"
	@curl -s http://localhost:8501 > /dev/null 2>&1 && echo "Streamlit: Running" || echo "Streamlit: Not running"
	@docker ps --format "Docker: {{.Names}}" | head -3 2>/dev/null || echo "Docker: Not running"

restart-api: ## Restart API server only
	@echo "🔄 Restarting API server..."
	@pkill -f uvicorn 2>/dev/null || true
	@sleep 2
	@python run_api.py &
	@echo "✅ API server restarted"

restart-dashboard: ## Restart Streamlit dashboard only
	@echo "🔄 Restarting Streamlit dashboard..."
	@pkill -f streamlit 2>/dev/null || true
	@sleep 2
	@nohup streamlit run src/visualization/web_dashboard.py --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false > /dev/null 2>&1 &
	@echo "✅ Dashboard restarted"

fix-all: stop clean quick-fix ## Nuclear option: reset and restart everything
	@echo "💥 Complete system reset and restart..."
	@sleep 3
	@make start
	@sleep 10
	@make init-db
	@echo "🎉 System completely refreshed!"

