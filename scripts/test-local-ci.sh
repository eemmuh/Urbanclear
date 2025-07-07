#!/bin/bash
# Local CI/CD Testing Script
# Run this before pushing to GitHub

set -e  # Exit on any error

echo "🔍 Starting Local CI/CD Tests..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function print_step() {
    echo -e "${YELLOW}$1${NC}"
}

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Code Quality
print_step "1. Testing Code Quality..."

echo "  → Running flake8 linting..."
if flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503; then
    print_success "Linting passed"
else
    print_error "Linting failed"
    exit 1
fi

echo "  → Checking Black formatting..."
if black --check src/ tests/ --line-length=88; then
    print_success "Formatting is correct"
else
    print_error "Formatting check failed - run: black src/ tests/ --line-length=88"
    exit 1
fi

# Step 2: Unit Tests
print_step "2. Running Unit Tests..."
if pytest tests/unit/ -v --cov=src --cov-report=term-missing; then
    print_success "Unit tests passed"
else
    print_error "Unit tests failed"
    exit 1
fi

# Step 3: Integration Tests
print_step "3. Running Integration Tests..."
if pytest tests/integration/ -v; then
    print_success "Integration tests passed"
else
    print_error "Integration tests failed"
    exit 1
fi

# Step 4: Security Scans
print_step "4. Running Security Scans..."
echo "  → Checking dependencies for vulnerabilities..."
if safety check; then
    print_success "Dependency security check passed"
else
    echo "⚠️  Security vulnerabilities found (non-blocking)"
fi

echo "  → Scanning code for security issues..."
if bandit -r src/ -q; then
    print_success "Code security scan passed"
else
    echo "⚠️  Security issues found (non-blocking)"
fi

# Step 5: API Tests (if server is running)
print_step "5. Testing API (if running)..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  → API server detected, running tests..."
    if python scripts/test_api.py; then
        print_success "API tests passed"
    else
        print_error "API tests failed"
        exit 1
    fi
else
    echo "  → API server not running, skipping API tests"
fi

# Step 6: Docker Build Test
print_step "6. Testing Docker Build..."
if docker build -t traffic-system:local-test . > /dev/null 2>&1; then
    print_success "Docker build successful"
    
    # Test if container runs
    if docker run --rm traffic-system:local-test --help > /dev/null 2>&1; then
        print_success "Docker container runs correctly"
    else
        echo "⚠️  Docker container may have issues"
    fi
    
    # Clean up
    docker rmi traffic-system:local-test > /dev/null 2>&1
else
    print_error "Docker build failed"
    exit 1
fi

print_success "🎉 All local CI/CD tests passed! Ready to push to GitHub."

echo ""
echo "📋 Summary:"
echo "  ✅ Code quality checks passed"
echo "  ✅ Unit tests passed"
echo "  ✅ Integration tests passed"
echo "  ✅ Security scans completed"
echo "  ✅ API tests passed (if applicable)"
echo "  ✅ Docker build successful"
echo ""
echo "🚀 You can now safely run: git push" 