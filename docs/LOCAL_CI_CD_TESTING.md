# Local CI/CD Testing Guide

This guide shows you how to test your CI/CD pipeline locally before pushing to GitHub.

## 🚀 **Method 1: Using GitHub Actions Locally with `act`**

### Install `act`
```bash
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Windows
choco install act-cli
```

### Basic Usage
```bash
# Test all jobs
act

# Test specific job
act -j unit-tests

# Test with different event
act push
act pull_request

# Test with secrets (create .secrets file)
act -s GITHUB_TOKEN=your_token

# Test with custom environment
act --env-file .env.local
```

### Advanced Act Usage
```bash
# Test specific workflow
act -W .github/workflows/ci-cd.yml

# Test with verbose output
act -v

# Test with specific platform
act -P ubuntu-latest=node:16-buster-slim

# Dry run (show what would be executed)
act --dry-run

# Test with custom input
act workflow_dispatch --input key=value
```

---

## 🛠️ **Method 2: Manual Component Testing**

### 1. **Code Quality Tests**
```bash
# Install development dependencies
pip install black flake8 mypy bandit safety

# Format checking
black --check --diff src/ tests/

# Linting
flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503

# Type checking
mypy src/ --ignore-missing-imports

# Security scanning
bandit -r src/ -f json -o bandit-report.json
safety check --json --output safety-report.json
```

### 2. **Unit Tests**
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run tests with coverage
pytest tests/unit/ -v --cov=src --cov-report=xml --cov-report=html

# Test with multiple Python versions (using pyenv)
pyenv install 3.9 3.10 3.11
pyenv local 3.9 3.10 3.11
for version in 3.9 3.10 3.11; do
    echo "Testing with Python $version"
    python$version -m pytest tests/unit/ -v
done
```

### 3. **Integration Tests with Services**
```bash
# Start required services using Docker Compose
docker-compose up -d postgres redis mongodb

# Wait for services to be ready
./scripts/wait-for-services.sh

# Run integration tests
export DATABASE_URL="postgresql://test_user:test_password@localhost:5432/test_traffic_db"
export REDIS_URL="redis://localhost:6379/0"
export MONGODB_URL="mongodb://test_user:test_password@localhost:27017/test_traffic_logs"
pytest tests/integration/ -v --maxfail=3

# Cleanup
docker-compose down
```

### 4. **API Tests**
```bash
# Start API server in background
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for server to start
sleep 10

# Run API tests
pytest tests/api/ -v

# Health check
curl -f http://localhost:8000/health || exit 1

# Cleanup
kill $API_PID
```

### 5. **Performance Tests**
```bash
# Install Locust
pip install locust

# Start API server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
sleep 10

# Run performance tests
locust -f tests/performance/locustfile.py --headless \
  --users 50 --spawn-rate 10 --run-time 60s \
  --host http://localhost:8000 \
  --html performance-report.html

# View results
open performance-report.html
```

### 6. **Security Scanning**
```bash
# Install Trivy
# macOS
brew install trivy

# Linux
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Filesystem scan
trivy fs . --format sarif --output trivy-results.sarif

# Container scan (after building image)
docker build -t urbanclear:test .
trivy image urbanclear:test --format sarif --output trivy-container-results.sarif
```

### 7. **Docker Build Tests**
```bash
# Build Docker image
docker build -t urbanclear:test .

# Test Docker image
docker run --rm urbanclear:test python -c "import src.api.main; print('Import successful')"

# Run container with health check
docker run -d --name urbanclear-test -p 8000:8000 urbanclear:test
sleep 10
curl -f http://localhost:8000/health
docker stop urbanclear-test
docker rm urbanclear-test
```

---

## 🎯 **Method 3: Automated Local Testing Script**

Create a comprehensive test script that mimics your CI/CD pipeline:

```bash
#!/bin/bash
# File: scripts/test-ci-cd-locally.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Local CI/CD Pipeline Test${NC}"
echo "================================="

# 1. Code Quality
echo -e "${YELLOW}📋 Running Code Quality Checks...${NC}"
black --check src/ tests/ || { echo -e "${RED}❌ Code formatting failed${NC}"; exit 1; }
flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503 || { echo -e "${RED}❌ Linting failed${NC}"; exit 1; }
mypy src/ --ignore-missing-imports || { echo -e "${RED}❌ Type checking failed${NC}"; exit 1; }
echo -e "${GREEN}✅ Code quality checks passed${NC}"

# 2. Unit Tests
echo -e "${YELLOW}🧪 Running Unit Tests...${NC}"
pytest tests/unit/ -v --cov=src --cov-report=xml || { echo -e "${RED}❌ Unit tests failed${NC}"; exit 1; }
echo -e "${GREEN}✅ Unit tests passed${NC}"

# 3. Security Scanning
echo -e "${YELLOW}🔒 Running Security Scans...${NC}"
bandit -r src/ -f json -o bandit-report.json
safety check --json --output safety-report.json
echo -e "${GREEN}✅ Security scans completed${NC}"

# 4. Docker Build
echo -e "${YELLOW}🐳 Building Docker Image...${NC}"
docker build -t urbanclear:test . || { echo -e "${RED}❌ Docker build failed${NC}"; exit 1; }
echo -e "${GREEN}✅ Docker build successful${NC}"

# 5. API Tests
echo -e "${YELLOW}🌐 Running API Tests...${NC}"
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!
sleep 10
pytest tests/api/ -v || { echo -e "${RED}❌ API tests failed${NC}"; kill $API_PID; exit 1; }
curl -f http://localhost:8000/health || { echo -e "${RED}❌ Health check failed${NC}"; kill $API_PID; exit 1; }
kill $API_PID
echo -e "${GREEN}✅ API tests passed${NC}"

# 6. Performance Tests
echo -e "${YELLOW}⚡ Running Performance Tests...${NC}"
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!
sleep 10
locust -f tests/performance/locustfile.py --headless \
  --users 10 --spawn-rate 2 --run-time 30s \
  --host http://localhost:8000 \
  --html performance-report.html || { echo -e "${RED}❌ Performance tests failed${NC}"; kill $API_PID; exit 1; }
kill $API_PID
echo -e "${GREEN}✅ Performance tests passed${NC}"

# 7. Integration Tests (optional - requires services)
if command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}🔗 Running Integration Tests...${NC}"
    docker-compose up -d postgres redis mongodb
    sleep 30
    export DATABASE_URL="postgresql://test_user:test_password@localhost:5432/test_traffic_db"
    export REDIS_URL="redis://localhost:6379/0"
    export MONGODB_URL="mongodb://test_user:test_password@localhost:27017/test_traffic_logs"
    pytest tests/integration/ -v --maxfail=3 || { echo -e "${RED}❌ Integration tests failed${NC}"; docker-compose down; exit 1; }
    docker-compose down
    echo -e "${GREEN}✅ Integration tests passed${NC}"
fi

echo -e "${GREEN}🎉 All CI/CD tests passed locally!${NC}"
echo "Reports generated:"
echo "- Coverage: htmlcov/index.html"
echo "- Performance: performance-report.html"
echo "- Security: bandit-report.json, safety-report.json"
```

---

## 🔧 **Method 4: Docker-based CI Environment**

Create a Docker setup that mimics your CI environment:

```dockerfile
# File: Dockerfile.ci
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install pytest pytest-cov pytest-asyncio black flake8 mypy bandit safety locust

# Copy source code
COPY . /app
WORKDIR /app

# Run CI pipeline
CMD ["bash", "scripts/test-ci-cd-locally.sh"]
```

```bash
# Build and run CI container
docker build -f Dockerfile.ci -t urbanclear-ci .
docker run --rm -v $(pwd):/app urbanclear-ci
```

---

## 📊 **Method 5: Individual Job Testing**

Test each CI/CD job separately:

```bash
# Test code quality job
./scripts/test-code-quality.sh

# Test unit tests job
./scripts/test-unit-tests.sh

# Test integration tests job
./scripts/test-integration.sh

# Test API tests job
./scripts/test-api.sh

# Test security scanning job
./scripts/test-security.sh

# Test Docker build job
./scripts/test-docker-build.sh

# Test performance tests job
./scripts/test-performance.sh
```

---

## 🎪 **Method 6: Using VS Code with GitHub Actions Extension**

1. Install the GitHub Actions extension in VS Code
2. Open the workflow file
3. Use the "Run workflow" feature to test locally

---

## 🌟 **Best Practices for Local CI/CD Testing**

### 1. **Environment Consistency**
- Use the same Python version as CI
- Use the same dependency versions
- Use Docker to match CI environment exactly

### 2. **Test Order**
- Run fast tests first (linting, unit tests)
- Run slow tests last (integration, performance)
- Fail fast on critical issues

### 3. **Data Management**
- Use test databases for integration tests
- Clean up test data after each run
- Use fixtures for consistent test data

### 4. **Monitoring**
- Track test execution time
- Monitor resource usage
- Log test results for debugging

### 5. **Automation**
- Use pre-commit hooks for code quality
- Automate test data setup/teardown
- Use make or scripts for common tasks

---

## 📋 **Quick Reference Commands**

```bash
# Full pipeline test
act

# Specific job test
act -j unit-tests

# Manual full test
./scripts/test-ci-cd-locally.sh

# Code quality only
black --check src/ tests/ && flake8 src/ tests/

# Unit tests only
pytest tests/unit/ -v

# API tests only
uvicorn src.api.main:app --port 8000 & pytest tests/api/ -v

# Performance tests only
./scripts/run-performance-tests.sh

# Docker build test
docker build -t urbanclear:test . && docker run --rm urbanclear:test python -c "import src.api.main"
```

---

## 🚨 **Troubleshooting Common Issues**

### Act Issues
- **Permission denied**: Run with `sudo` or fix Docker permissions
- **Out of space**: Clean up Docker images with `docker system prune`
- **Missing secrets**: Create `.secrets` file with required tokens

### Service Issues
- **Database connection**: Ensure services are running and accessible
- **Port conflicts**: Check if ports are already in use
- **Service startup**: Add proper wait times for services to initialize

### Test Issues
- **Import errors**: Ensure all dependencies are installed
- **Path issues**: Run tests from project root
- **Environment variables**: Set required environment variables

Ready to test your CI/CD pipeline locally! 🚀 