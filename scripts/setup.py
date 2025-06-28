#!/usr/bin/env python3
"""
Setup script for Urbanclear - Smart City Traffic Optimization System
This script handles the initial setup of the project environment
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "models",
        "data/sample",
        "docker/postgres",
        "docker/mongodb", 
        "docker/prometheus",
        "docker/grafana/provisioning/datasources",
        "docker/grafana/provisioning/dashboards",
        "docker/grafana/dashboards",
        "tests/unit",
        "tests/integration",
        "tests/fixtures"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def copy_config_files():
    """Copy example configuration files"""
    if not os.path.exists("config/config.yaml"):
        if os.path.exists("config/config.example.yaml"):
            shutil.copy("config/config.example.yaml", "config/config.yaml")
            print("✓ Created config/config.yaml from example")
        else:
            print("⚠ Warning: config.example.yaml not found")


def create_env_file():
    """Create .env file with default values"""
    env_content = """# Environment Configuration
ENVIRONMENT=development

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=traffic_db
POSTGRES_USER=traffic_user
POSTGRES_PASSWORD=traffic_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# MongoDB Configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=mongo_user
MONGODB_PASSWORD=mongo_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
JWT_SECRET=your_jwt_secret_key_here

# External APIs
WEATHER_API_KEY=your_openweathermap_api_key_here
TRAFFIC_SENSOR_API_KEY=your_sensor_api_key_here

# Monitoring
GRAFANA_ADMIN_PASSWORD=grafana_password
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✓ Created .env file with default values")
    else:
        print("✓ .env file already exists")


def create_docker_configs():
    """Create Docker configuration files"""
    
    # PostgreSQL init script
    postgres_init = """
-- Initialize PostgreSQL database for traffic system
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create application user and database
-- (These are handled by Docker environment variables)
"""
    
    with open("docker/postgres/init.sql", "w") as f:
        f.write(postgres_init)
    print("✓ Created PostgreSQL init script")
    
    # MongoDB init script
    mongodb_init = """
// Initialize MongoDB database for traffic system
db = db.getSiblingDB('traffic_logs');

// Create collections
db.createCollection('sensor_logs');
db.createCollection('incident_logs');
db.createCollection('api_logs');
db.createCollection('system_logs');

// Create indexes
db.sensor_logs.createIndex({"timestamp": 1});
db.sensor_logs.createIndex({"sensor_id": 1, "timestamp": 1});
db.incident_logs.createIndex({"timestamp": 1});
db.api_logs.createIndex({"timestamp": 1, "endpoint": 1});

print("MongoDB initialized successfully");
"""
    
    with open("docker/mongodb/init.js", "w") as f:
        f.write(mongodb_init)
    print("✓ Created MongoDB init script")
    
    # Prometheus configuration
    prometheus_config = """
global:
  scrape_interval: 30s
  evaluation_interval: 30s

rule_files:
  # - "first_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'traffic-api'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s
"""
    
    with open("docker/prometheus/prometheus.yml", "w") as f:
        f.write(prometheus_config)
    print("✓ Created Prometheus configuration")
    
    # Grafana datasource configuration
    grafana_datasource = """
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
"""
    
    with open("docker/grafana/provisioning/datasources/prometheus.yml", "w") as f:
        f.write(grafana_datasource)
    print("✓ Created Grafana datasource configuration")
    
    # Grafana dashboard configuration
    grafana_dashboard_config = """
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
"""
    
    with open("docker/grafana/provisioning/dashboards/dashboards.yml", "w") as f:
        f.write(grafana_dashboard_config)
    print("✓ Created Grafana dashboard configuration")


def create_sample_data():
    """Create sample data files"""
    sample_traffic_data = """timestamp,sensor_id,speed_mph,volume,density,occupancy
2024-01-01T08:00:00Z,sensor_001,35.5,1200,45.2,0.65
2024-01-01T08:00:00Z,sensor_002,28.3,1450,52.1,0.78
2024-01-01T08:00:00Z,sensor_003,42.1,980,38.7,0.55
2024-01-01T08:05:00Z,sensor_001,32.2,1350,48.9,0.72
2024-01-01T08:05:00Z,sensor_002,25.8,1520,55.3,0.82
2024-01-01T08:05:00Z,sensor_003,39.7,1050,41.2,0.58
"""
    
    with open("data/sample/traffic_data.csv", "w") as f:
        f.write(sample_traffic_data)
    print("✓ Created sample traffic data")


def create_gitignore():
    """Create .gitignore file"""
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Jupyter Notebook
.ipynb_checkpoints

# Logs
logs/
*.log

# Models
models/*.pkl
models/*.h5
models/*.joblib

# Data
data/raw/*
data/processed/*
data/interim/*
!data/raw/.gitkeep
!data/processed/.gitkeep
!data/interim/.gitkeep

# Database
*.db
*.sqlite

# Docker
.docker/

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# Config (keep examples)
config/config.yaml
!config/config.example.yaml

# Temporary files
tmp/
temp/
"""
    
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w") as f:
            f.write(gitignore_content)
        print("✓ Created .gitignore file")


def create_makefile():
    """Create Makefile for common tasks"""
    makefile_content = """
.PHONY: help install dev-install start stop restart logs clean test lint format

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@egrep '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}'

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

"""
    
    with open("Makefile", "w") as f:
        f.write(makefile_content)
    print("✓ Created Makefile")


def create_readme_files():
    """Create README files for subdirectories"""
    readme_files = {
        "data/raw/README.md": "# Raw Data\n\nThis directory contains raw traffic data from various sources.\n",
        "data/processed/README.md": "# Processed Data\n\nThis directory contains cleaned and processed traffic data.\n",
        "data/interim/README.md": "# Interim Data\n\nThis directory contains intermediate data processing results.\n",
        "models/README.md": "# Models\n\nThis directory contains trained machine learning models.\n",
        "logs/README.md": "# Logs\n\nThis directory contains application log files.\n",
        "tests/README.md": "# Tests\n\nThis directory contains all test files for the project.\n"
    }
    
    for filepath, content in readme_files.items():
        with open(filepath, "w") as f:
            f.write(content)
        print(f"✓ Created {filepath}")


def check_dependencies():
    """Check if required dependencies are available"""
    required_tools = ["docker", "docker-compose", "python"]
    missing_tools = []
    
    for tool in required_tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
            print(f"✓ {tool} is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append(tool)
            print(f"✗ {tool} is not available")
    
    if missing_tools:
        print(f"\n⚠ Warning: Missing required tools: {', '.join(missing_tools)}")
        print("Please install them before proceeding.")
        return False
    
    return True


def main():
    """Main setup function"""
    print("🚀 Setting up Urbanclear - Smart City Traffic Optimization System")
    print("=" * 60)
    
    # Check dependencies
    print("\n1. Checking dependencies...")
    check_dependencies()
    
    # Create directories
    print("\n2. Creating directories...")
    create_directories()
    
    # Create configuration files
    print("\n3. Setting up configuration...")
    copy_config_files()
    create_env_file()
    
    # Create Docker configurations
    print("\n4. Setting up Docker configurations...")
    create_docker_configs()
    
    # Create sample data
    print("\n5. Creating sample data...")
    create_sample_data()
    
    # Create project files
    print("\n6. Creating project files...")
    create_gitignore()
    create_makefile()
    create_readme_files()
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Review and update config/config.yaml with your settings")
    print("2. Update .env file with your API keys and passwords")
    print("3. Start the infrastructure: make start")
    print("4. Initialize the database: make init-db")
    print("5. Start the API server: make api")
    print("\nFor more commands, run: make help")


if __name__ == "__main__":
    main() 