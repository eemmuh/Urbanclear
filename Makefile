
.PHONY: help install dev-install start stop restart logs clean test lint format

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@egrep '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

dev-install: ## Install development dependencies
	pip install -r requirements.txt
	pip install -e .

start: ## Start all services with Docker Compose
	docker-compose up -d

stop: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

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

