#  Dependency Installation Guide

**Canonical workflow for this repo:** use **[uv](https://docs.astral.sh/uv/)** with **`pyproject.toml`** and **`uv.lock`**: `uv sync`, `uv sync --extra dev`, or `uv sync --extra ci`. The `uv pip install -r requirements-*.txt` examples below are legacy compatibility patterns; prefer `uv sync` when possible.

##  **Problem: psycopg2-binary Build Failure**

**Error**: `pg_config executable not found` when installing `psycopg2-binary`

**Cause**: PostgreSQL development headers missing on macOS (common on Apple Silicon)

##  **Solutions (Choose One)**

### ** Option 1: Quick Start (Recommended)**
```bash
# Install from lockfile (creates/uses .venv)
uv sync

# Test your setup
uv run python -c "import src.api.main"
```

### ** Option 2: Install PostgreSQL Headers**
```bash
# Install PostgreSQL client libraries
brew install libpq

# Add to PATH
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"

# Add to your shell profile
echo 'export PATH="/opt/homebrew/opt/libpq/bin:$PATH"' >> ~/.zshrc

# Install all dependencies
source .venv/bin/activate
uv pip install -r requirements.txt
```

### ** Option 3: Use Compatible Requirements**
```bash
# Install with PostgreSQL issues resolved
source .venv/bin/activate
uv pip install -r requirements-compatible.txt
```

### ** Option 4: Force Binary Installation**
```bash
source .venv/bin/activate

# Install everything except problematic packages
uv pip install -r requirements.txt --exclude psycopg2-binary

# Force install psycopg2-binary as binary only
uv pip install psycopg2-binary --only-binary=psycopg2-binary
```

### ** Option 5: Step-by-Step Installation**
```bash
source .venv/bin/activate

# Install core API dependencies first
uv pip install fastapi uvicorn pydantic sqlalchemy asyncpg

# Install data science packages
uv pip install pandas numpy matplotlib seaborn

# Install development tools
uv pip install pytest black flake8 mypy

# Install remaining packages as needed
uv pip install python-dotenv pyyaml loguru
```

##  **Database Configuration**

### **Using asyncpg (Recommended)**
Your project already uses `asyncpg` which is better for async applications:

```python
# In your database configuration
# SQLAlchemy with asyncpg (no psycopg2 needed)
DATABASE_URL = "postgresql+asyncpg://user:pass@host/db"
```

### **If You Need psycopg2**
```python
# Only if you specifically need psycopg2
DATABASE_URL = "postgresql://user:pass@host/db"
```

##  **Testing Your Installation**

### **1. Verify Environment**
```bash
source .venv/bin/activate
python --version  # Should show Python 3.9.23
```

### **2. Test Database Connection**
```bash
# Test asyncpg (no psycopg2 needed)
python -c "import asyncpg; print(' asyncpg works!')"

# Test SQLAlchemy
python -c "import sqlalchemy; print(' SQLAlchemy works!')"
```

### **3. Test API Server**
```bash
# Start your API
python src/api/main.py

# In another terminal, test endpoint
curl http://localhost:8000/health
```

##  **Package Breakdown**

### **Essential (always install)**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `sqlalchemy` - Database ORM
- `asyncpg` - PostgreSQL async driver

### **Development (for coding)**
- `pytest` - Testing framework
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking

### **Data Science (install as needed)**
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `matplotlib` - Plotting
- `scikit-learn` - Machine learning

### **Heavy ML (install individually)**
- `tensorflow` - Deep learning
- `torch` - PyTorch
- `pyspark` - Big data processing

##  **Troubleshooting**

### **Still Getting Build Errors?**
```bash
# Clear pip cache
pip cache purge

# Or with uv
uv cache clean

# Reinstall with verbose output
uv pip install -v psycopg2-binary
```

### **macOS Specific Issues**
```bash
# Install Xcode command line tools
xcode-select --install

# Install PostgreSQL development headers
brew install postgresql
```

### **Alternative PostgreSQL Drivers**
```bash
# If psycopg2 keeps failing, use these alternatives:
uv pip install asyncpg          # For async applications
uv pip install psycopg2-binary --only-binary=all  # Force binary
```

##  **Performance Comparison**

| Package | Install Time | Performance | Use Case |
|---------|--------------|-------------|----------|
| `asyncpg` |  Fast |  Excellent | Async apps (recommended) |
| `psycopg2-binary` |  Slow |  Good | Sync apps |
| `psycopg2` |  Fails |  Good | Build from source |

##  **Recommended Workflow**

### **For Development**
```bash
# 1. Start with minimal dependencies
source .venv/bin/activate
uv pip install -r requirements-minimal.txt

# 2. Test your API
python src/api/main.py

# 3. Add packages as needed
uv pip install scikit-learn matplotlib

# 4. Update requirements
uv pip freeze > requirements-dev.txt
```

### **For Production**
```bash
# Use the compatible requirements file
uv pip install -r requirements-compatible.txt
```

##  **Success Checklist**

After installation, verify:

- [ ] **Environment Active**: `(.venv)` shows in terminal
- [ ] **Python Version**: `python --version` shows 3.9.23
- [ ] **Core Packages**: `python -c "import fastapi; print('')"`
- [ ] **Database**: `python -c "import asyncpg; print('')"`
- [ ] **API Server**: `python src/api/main.py` starts successfully
- [ ] **Tests**: `pytest tests/` runs without errors

##  **Next Steps**

1. **Choose your solution** from the options above
2. **Test the installation** with the checklist
3. **Start your development** with `python src/api/main.py`
4. **Add more packages** as needed for your specific features

**Your environment is ready for development!**  