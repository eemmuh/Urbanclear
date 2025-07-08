# 🧪 Local CI/CD Testing Guide

## Overview
This guide shows you how to test your CI/CD pipeline locally before pushing to GitHub, saving time and preventing failed builds.

## 🚀 Method 1: Using `act` (GitHub Actions Locally)

### Install and Setup
```bash
# Install act (already done)
brew install act

# List all available workflows
act --list

# Test specific jobs
act -j unit-tests --container-architecture linux/amd64
act -j code-quality --container-architecture linux/amd64
act -j docker-build --container-architecture linux/amd64
```

### Benefits:
- ✅ Runs exact same environment as GitHub Actions
- ✅ Tests the entire workflow
- ✅ Catches environment-specific issues

### Limitations:
- ⚠️ Can be slow (downloads Docker images)
- ⚠️ M1 Mac compatibility issues sometimes
- ⚠️ Some GitHub-specific features won't work

## 🔧 Method 2: Manual Step-by-Step Testing

### 1. Code Quality Testing
```bash
# Test linting (exactly as CI does)
flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503

# Test formatting (exactly as CI does)
black --check src/ tests/ --line-length=88

# Fix formatting if needed
black src/ tests/ --line-length=88

# Test import sorting
isort --check-only --profile black src/ tests/

# Fix import sorting if needed
isort --profile black src/ tests/
```

### 2. Unit Tests
```bash
# Run tests with coverage (exactly as CI does)
pytest tests/unit/ -v --cov=src --cov-report=xml --cov-report=term-missing

# Check if all tests pass
echo "Exit code: $?"
```

### 3. Integration Tests
```bash
# Run integration tests
pytest tests/integration/ -v

# Run API tests
python scripts/test_api.py
```

### 4. Security Scanning
```bash
# Install security tools
pip install safety bandit

# Run security scan (like CI does)
safety check --json --output safety-report.json || true
bandit -r src/ -f json -o bandit-report.json || true

# Check results
cat safety-report.json
cat bandit-report.json
```

### 5. Docker Build Testing
```bash
# Test Docker build (exactly as CI does)
docker build -t traffic-system:test .

# Test if container runs
docker run --rm traffic-system:test --help

# Clean up
docker rmi traffic-system:test
```

## 🐳 Method 3: Local Docker Environment Testing

### Create test environment
```bash
# Build and run with docker-compose
docker-compose up --build -d

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/traffic/current

# Check logs
docker-compose logs api

# Clean up
docker-compose down
```

## 🎯 Method 4: Makefile for Easy Testing

### Create automated testing commands
```bash
# Run all local tests
make test-local

# Run specific test suites
make test-unit
make test-integration
make test-lint
make test-format
make test-security
make test-docker
```

## 📊 Method 5: Performance Testing

### Test performance locally
```bash
# Install locust
pip install locust

# Run performance tests
locust -f tests/performance/test_api_performance.py --host=http://localhost:8000
```

## 🔍 Method 6: Pre-commit Hooks

### Setup pre-commit hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## 🛡️ Method 7: Security Testing

### Local vulnerability scanning
```bash
# Scan Python dependencies
safety check

# Scan code for security issues
bandit -r src/

# Scan Docker image (if built)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image traffic-system:latest
```

## 📋 Complete Local CI/CD Test Script

### Run everything at once
```bash
#!/bin/bash
set -e

echo "🔍 Running Local CI/CD Tests..."

# 1. Code Quality
echo "1. Testing Code Quality..."
flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
black --check src/ tests/ --line-length=88
isort --check-only --profile black src/ tests/

# 2. Unit Tests
echo "2. Running Unit Tests..."
pytest tests/unit/ -v --cov=src --cov-report=term-missing

# 3. Integration Tests
echo "3. Running Integration Tests..."
pytest tests/integration/ -v

# 4. Security Scans
echo "4. Running Security Scans..."
safety check --json --output safety-report.json || true
bandit -r src/ -f json -o bandit-report.json || true

# 5. Docker Build
echo "5. Testing Docker Build..."
docker build -t traffic-system:test .

# 6. API Tests
echo "6. Running API Tests..."
python scripts/test_api.py

echo "✅ All local CI/CD tests completed!"
```

## 💡 Best Practices

### 1. Test Before Every Push
```bash
# Always run this before git push
make test-local && git push
```

### 2. Use Same Tool Versions
```bash
# Pin versions in requirements-dev.txt
black==23.12.1
flake8==6.1.0
pytest==7.4.3
```

### 3. Environment Variables
```bash
# Create .env.test file
export DATABASE_URL="sqlite:///test.db"
export API_KEY="test-key"
export DEBUG=true
```

### 4. Clean Between Tests
```bash
# Clean up before each test run
rm -rf .pytest_cache/
rm -rf __pycache__/
docker system prune -f
```

## 🚨 Common Issues and Solutions

### Issue 1: Docker Build Fails
```bash
# Solution: Check .dockerignore
echo "Check .dockerignore file"
cat .dockerignore

# Solution: Build with no cache
docker build --no-cache -t traffic-system:test .
```

### Issue 2: Tests Fail Locally But Pass in CI
```bash
# Solution: Use same Python version
pyenv install 3.9.18
pyenv local 3.9.18

# Solution: Use same dependencies
pip install -r requirements.txt --no-cache-dir
```

### Issue 3: Permission Errors
```bash
# Solution: Fix file permissions
chmod +x scripts/test_api.py
chmod +x scripts/setup.py
```

## 🎯 Quick Test Commands

### Essential commands to remember:
```bash
# Quick lint check
flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503

# Quick format check
black --check src/ tests/ --line-length=88

# Quick test run
pytest tests/unit/ -v

# Quick security check
safety check && bandit -r src/

# Quick Docker test
docker build -t test . && docker run --rm test --help
```

## 📈 Next Steps

1. **Set up pre-commit hooks** for automatic testing
2. **Create a Makefile** for easy command execution
3. **Add more integration tests** for better coverage
4. **Set up local monitoring** with Grafana/Prometheus
5. **Create test data fixtures** for consistent testing

---

**Pro Tip:** Always test the complete pipeline locally before pushing to avoid "works on my machine" issues! 🚀 