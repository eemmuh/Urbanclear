# 🛠️ Scripts Directory

This directory contains utility scripts for development, testing, and deployment of the Urbanclear Traffic System.

## 📋 Available Scripts

### 🚀 **Deployment & Startup**
- **`fast-docker-build.sh`** - Fast Docker build script for development
- **Note**: Use `python start_api.py` from project root to start the API server

### 🧪 **Testing & Quality**
- **`test-ci-cd-locally.sh`** - Comprehensive local CI/CD pipeline test (recommended)
- **`test_api.py`** - API endpoint testing script
- **`run-performance-tests.sh`** - Performance testing with Locust

### 🔧 **Database & Setup**
- **`init_database.py`** - Database initialization and setup
- **`database_optimization.py`** - Database optimization and maintenance
- **`setup_dashboards.py`** - Grafana dashboard setup

### 🔍 **Monitoring & Health**
- **`health_check.py`** - System health check and monitoring

## 🎯 Most Commonly Used Scripts

### 1. **Local CI/CD Testing**
```bash
# Run complete CI/CD pipeline locally
./scripts/test-ci-cd-locally.sh
```

### 2. **API Testing**
```bash
# Test API endpoints
python scripts/test_api.py
```

### 3. **Performance Testing**
```bash
# Run performance tests
./scripts/run-performance-tests.sh
```

### 4. **Database Setup**
```bash
# Initialize database
python scripts/init_database.py
```

### 5. **Health Check**
```bash
# Check system health
python scripts/health_check.py
```

## 🔧 Script Permissions

Make sure shell scripts are executable:
```bash
chmod +x scripts/*.sh
```

## 📚 Usage Examples

### Complete Pre-Push Testing
```bash
# Run all tests before pushing to GitHub
./scripts/test-ci-cd-locally.sh

# If all tests pass, you can safely push
git push
```

### API Development Workflow
```bash
# Start API server
python start_api.py

# In another terminal, test the API
python scripts/test_api.py

# Run health check
python scripts/health_check.py
```

### Database Management
```bash
# Initialize database
python scripts/init_database.py

# Optimize database performance
python scripts/database_optimization.py
```

## 📊 Script Dependencies

Most scripts require the development environment to be set up:
```bash
# Install development dependencies
pip install -r requirements-ci.txt

# Ensure virtual environment is activated
source urbanclear-env/bin/activate
```

## 🛡️ Security Note

Scripts may contain sensitive operations. Always review scripts before execution, especially:
- Database initialization scripts
- Deployment scripts  
- Scripts that modify system configurations

## 📝 Adding New Scripts

When adding new scripts:
1. Follow the naming convention: `verb_noun.py` or `verb-noun.sh`
2. Add executable permissions for shell scripts
3. Include proper documentation headers
4. Update this README with the new script description

## 🔗 Related Documentation

- **Main README**: [../README.md](../README.md)
- **CI/CD Testing Guide**: [../docs/LOCAL_CI_CD_TESTING.md](../docs/LOCAL_CI_CD_TESTING.md)
- **Development Guides**: [../docs/guides/](../docs/guides/) 