#!/bin/bash
# Performance Testing Script for UrbanClear Traffic System

set -e

echo "🚀 UrbanClear Performance Testing Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if server is running
check_server() {
    echo -e "${BLUE}Checking if API server is running...${NC}"
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API server is running${NC}"
        return 0
    else
        echo -e "${RED}❌ API server is not running${NC}"
        return 1
    fi
}

# Function to start server
start_server() {
    echo -e "${YELLOW}Starting API server...${NC}"
    echo "Run this command in another terminal:"
    echo "uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    echo "Then press Enter to continue..."
    read -r
}

# Function to run performance tests
run_performance_tests() {
    echo -e "${BLUE}Running performance tests...${NC}"
    
    # Basic performance test
    echo -e "${YELLOW}1. Running basic performance test (30 seconds, 10 users)${NC}"
    locust -f tests/performance/locustfile.py --headless -u 10 -r 2 -t 30s --host=http://localhost:8000
    
    echo ""
    echo -e "${YELLOW}2. Running stress test (60 seconds, 50 users)${NC}"
    locust -f tests/performance/locustfile.py --headless -u 50 -r 5 -t 60s --host=http://localhost:8000
    
    echo ""
    echo -e "${YELLOW}3. Running load test (2 minutes, 100 users)${NC}"
    locust -f tests/performance/locustfile.py --headless -u 100 -r 10 -t 120s --host=http://localhost:8000
}

# Function to run web interface
run_web_interface() {
    echo -e "${BLUE}Starting Locust web interface...${NC}"
    echo "Open your browser to: http://localhost:8089"
    locust -f tests/performance/locustfile.py --host=http://localhost:8000
}

# Main menu
echo ""
echo "Choose an option:"
echo "1. Run automated performance tests"
echo "2. Start Locust web interface"
echo "3. Quick test (check if setup works)"
echo "4. Exit"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        if check_server; then
            run_performance_tests
        else
            start_server
            if check_server; then
                run_performance_tests
            else
                echo -e "${RED}❌ Server still not running. Please start the API server first.${NC}"
                exit 1
            fi
        fi
        ;;
    2)
        if check_server; then
            run_web_interface
        else
            start_server
            if check_server; then
                run_web_interface
            else
                echo -e "${RED}❌ Server still not running. Please start the API server first.${NC}"
                exit 1
            fi
        fi
        ;;
    3)
        if check_server; then
            echo -e "${GREEN}✅ Setup is working correctly!${NC}"
            echo "Running quick test..."
            locust -f tests/performance/locustfile.py --headless -u 1 -r 1 -t 10s --host=http://localhost:8000
        else
            echo -e "${RED}❌ API server is not running. Please start it first.${NC}"
            echo "Command: uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"
        fi
        ;;
    4)
        echo -e "${BLUE}Goodbye!${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Invalid choice. Please run the script again.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎉 Performance testing completed!${NC}" 