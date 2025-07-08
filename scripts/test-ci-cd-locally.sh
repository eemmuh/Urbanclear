#!/bin/bash
# Local CI/CD Pipeline Test Script
# This script mimics the GitHub Actions workflow locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print section headers
print_section() {
    echo -e "\n${PURPLE}=====================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${PURPLE}=====================================${NC}"
}

# Function to print success message
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error message
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to print warning message
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print info message
print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local timeout=${2:-30}
    local counter=0
    
    while [ $counter -lt $timeout ]; do
        if curl -f -s "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        counter=$((counter + 1))
    done
    return 1
}

# Cleanup function
cleanup() {
    print_info "Cleaning up background processes..."
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    if [ ! -z "$DOCKER_COMPOSE_RUNNING" ]; then
        docker-compose down >/dev/null 2>&1 || true
    fi
}

# Set up cleanup trap
trap cleanup EXIT

# Start of script
print_section "🚀 Local CI/CD Pipeline Test"
echo -e "${CYAN}Testing UrbanClear Traffic System CI/CD Pipeline locally...${NC}\n"

# Check prerequisites
print_section "🔍 Prerequisites Check"

if ! command_exists python3; then
    print_error "Python 3 is required but not installed"
    exit 1
fi
print_success "Python 3 found: $(python3 --version)"

if ! command_exists pip; then
    print_error "pip is required but not installed"
    exit 1
fi
print_success "pip found: $(pip --version)"

if ! command_exists docker; then
    print_warning "Docker not found - skipping Docker tests"
    SKIP_DOCKER=true
else
    print_success "Docker found: $(docker --version)"
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ "$PYTHON_VERSION" != "3.9" ]]; then
    print_warning "CI uses Python 3.9, you're using Python $PYTHON_VERSION"
fi

# Install dependencies
print_section "📦 Installing Dependencies"
print_info "Installing development dependencies..."
pip install -q black flake8 mypy bandit safety pytest pytest-cov pytest-asyncio locust || {
    print_error "Failed to install dependencies"
    exit 1
}
print_success "Development dependencies installed"

print_info "Installing project dependencies..."
pip install -q -r requirements.txt || {
    print_error "Failed to install project dependencies"
    exit 1
}
print_success "Project dependencies installed"

# 1. Code Quality Tests
print_section "📋 Code Quality Tests"

print_info "Running Black code formatting check..."
if black --check --diff src/ tests/ >/dev/null 2>&1; then
    print_success "Code formatting check passed"
else
    print_error "Code formatting check failed"
    echo -e "${YELLOW}Run 'black src/ tests/' to fix formatting${NC}"
    exit 1
fi

print_info "Running flake8 linting..."
if flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503 >/dev/null 2>&1; then
    print_success "Linting check passed"
else
    print_error "Linting check failed"
    echo -e "${YELLOW}Run 'flake8 src/ tests/' to see issues${NC}"
    exit 1
fi

print_info "Running mypy type checking..."
if mypy src/ --ignore-missing-imports >/dev/null 2>&1; then
    print_success "Type checking passed"
else
    print_warning "Type checking failed (non-blocking)"
fi

# 2. Security Scanning
print_section "🔒 Security Scanning"

print_info "Running bandit security scan..."
if bandit -r src/ -f json -o bandit-report.json >/dev/null 2>&1; then
    print_success "Bandit security scan completed"
else
    print_warning "Bandit scan failed (non-blocking)"
fi

print_info "Running safety dependency check..."
if safety check --json --output safety-report.json >/dev/null 2>&1; then
    print_success "Safety dependency check passed"
else
    print_warning "Safety check failed (non-blocking)"
fi

# 3. Unit Tests
print_section "🧪 Unit Tests"

print_info "Running unit tests with coverage..."
if pytest tests/unit/ -v --cov=src --cov-report=xml --cov-report=html >/dev/null 2>&1; then
    print_success "Unit tests passed"
    
    # Show coverage summary
    if [ -f htmlcov/index.html ]; then
        print_info "Coverage report generated: htmlcov/index.html"
    fi
else
    print_error "Unit tests failed"
    exit 1
fi

# 4. Docker Build Tests
if [ "$SKIP_DOCKER" != true ]; then
    print_section "🐳 Docker Build Tests"
    
    print_info "Building Docker image..."
    if docker build -t urbanclear:test . >/dev/null 2>&1; then
        print_success "Docker build successful"
        
        print_info "Testing Docker image..."
        if docker run --rm urbanclear:test python -c "import src.api.main; print('Import successful')" >/dev/null 2>&1; then
            print_success "Docker image test passed"
        else
            print_error "Docker image test failed"
            exit 1
        fi
    else
        print_error "Docker build failed"
        exit 1
    fi
fi

# 5. API Tests
print_section "🌐 API Tests"

print_info "Checking if port 8000 is available..."
if ! check_port 8000; then
    print_error "Port 8000 is already in use"
    exit 1
fi

print_info "Starting API server..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 >/dev/null 2>&1 &
API_PID=$!

print_info "Waiting for API server to start..."
if wait_for_service "http://localhost:8000/health" 30; then
    print_success "API server started successfully"
else
    print_error "API server failed to start"
    exit 1
fi

print_info "Running API tests..."
if pytest tests/api/ -v >/dev/null 2>&1; then
    print_success "API tests passed"
else
    print_error "API tests failed"
    exit 1
fi

print_info "Running API health check..."
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    print_success "API health check passed"
else
    print_error "API health check failed"
    exit 1
fi

# 6. Performance Tests
print_section "⚡ Performance Tests"

print_info "Running performance tests..."
if locust -f tests/performance/locustfile.py --headless \
    --users 10 --spawn-rate 2 --run-time 30s \
    --host http://localhost:8000 \
    --html performance-report.html >/dev/null 2>&1; then
    print_success "Performance tests completed"
    print_info "Performance report generated: performance-report.html"
else
    print_warning "Performance tests failed (non-blocking)"
fi

# Kill API server
kill $API_PID 2>/dev/null || true
API_PID=""

# 7. Integration Tests (optional)
if command_exists docker-compose; then
    print_section "🔗 Integration Tests"
    
    print_info "Starting database services..."
    if docker-compose up -d postgres redis mongodb >/dev/null 2>&1; then
        DOCKER_COMPOSE_RUNNING=true
        print_success "Database services started"
        
        print_info "Waiting for services to be ready..."
        sleep 30
        
        print_info "Running integration tests..."
        export DATABASE_URL="postgresql://test_user:test_password@localhost:5432/test_traffic_db"
        export REDIS_URL="redis://localhost:6379/0"
        export MONGODB_URL="mongodb://test_user:test_password@localhost:27017/test_traffic_logs"
        
        if pytest tests/integration/ -v --maxfail=3 >/dev/null 2>&1; then
            print_success "Integration tests passed"
        else
            print_warning "Integration tests failed (non-blocking)"
        fi
        
        print_info "Stopping database services..."
        docker-compose down >/dev/null 2>&1
        DOCKER_COMPOSE_RUNNING=""
    else
        print_warning "Failed to start database services - skipping integration tests"
    fi
else
    print_warning "Docker Compose not found - skipping integration tests"
fi

# 8. Security Vulnerability Scanning
if command_exists trivy; then
    print_section "🛡️  Vulnerability Scanning"
    
    print_info "Running filesystem vulnerability scan..."
    if trivy fs . --format sarif --output trivy-results.sarif >/dev/null 2>&1; then
        print_success "Filesystem vulnerability scan completed"
        print_info "Trivy results: trivy-results.sarif"
    else
        print_warning "Filesystem vulnerability scan failed (non-blocking)"
    fi
    
    if [ "$SKIP_DOCKER" != true ]; then
        print_info "Running container vulnerability scan..."
        if trivy image urbanclear:test --format sarif --output trivy-container-results.sarif >/dev/null 2>&1; then
            print_success "Container vulnerability scan completed"
            print_info "Container scan results: trivy-container-results.sarif"
        else
            print_warning "Container vulnerability scan failed (non-blocking)"
        fi
    fi
else
    print_warning "Trivy not found - skipping vulnerability scanning"
    print_info "Install with: brew install trivy (macOS) or check https://aquasecurity.github.io/trivy/"
fi

# Final Summary
print_section "🎉 Test Summary"

print_success "CI/CD Pipeline Test Completed Successfully!"
echo ""
echo -e "${CYAN}📊 Generated Reports:${NC}"
echo -e "   • Coverage Report: ${YELLOW}htmlcov/index.html${NC}"
echo -e "   • Performance Report: ${YELLOW}performance-report.html${NC}"
echo -e "   • Security Reports: ${YELLOW}bandit-report.json, safety-report.json${NC}"
if [ -f trivy-results.sarif ]; then
    echo -e "   • Vulnerability Scan: ${YELLOW}trivy-results.sarif${NC}"
fi
echo ""
echo -e "${CYAN}🚀 Next Steps:${NC}"
echo -e "   • Review reports for any issues"
echo -e "   • Fix any warnings or failed tests"
echo -e "   • Commit and push your changes"
echo -e "   • Monitor the CI/CD pipeline on GitHub"
echo ""
echo -e "${GREEN}✨ Your code is ready for production! ✨${NC}" 