#!/usr/bin/env python3
"""
Development setup script for Urbanclear Traffic System.
This script helps new developers set up their environment quickly.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f" {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f" {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f" {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_prerequisites():
    """Check if required tools are installed."""
    print(" Checking prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 9):
        print(f" Python 3.9+ required, found {python_version.major}.{python_version.minor}")
        return False
    print(f" Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check uv
    if shutil.which("uv") is None:
        print(" uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False
    print(" uv found")
    
    # Check Node.js (for dashboard)
    if shutil.which("node") is None:
        print("  Node.js not found. Dashboard will not work without it.")
    else:
        print(" Node.js found")
    
    # Check Docker (optional)
    if shutil.which("docker") is None:
        print("  Docker not found. Some features may not work.")
    else:
        print(" Docker found")
    
    return True


def setup_python_environment():
    """Set up Python environment with uv."""
    print("\n Setting up Python environment...")
    
    # Install dependencies
    if not run_command("uv sync --extra dev", "Installing Python dependencies"):
        return False
    
    # Verify installation
    if not run_command(
        "uv run python -c 'import fastapi, numpy, sklearn; print(\"Core dependencies working\")'",
        "Verifying core dependencies",
    ):
        return False
    
    return True


def setup_dashboard():
    """Set up React dashboard."""
    dashboard_dir = Path("dashboard")
    if not dashboard_dir.exists():
        print("  Dashboard directory not found, skipping dashboard setup")
        return True
    
    print("\n  Setting up React dashboard...")
    
    # Check if npm is available
    if shutil.which("npm") is None:
        print(" npm not found. Install Node.js to use the dashboard.")
        return False
    
    # Install npm dependencies
    os.chdir(dashboard_dir)
    if not run_command("npm install", "Installing npm dependencies"):
        os.chdir("..")
        return False
    
    os.chdir("..")
    print(" Dashboard setup completed")
    return True


def create_config_file():
    """Create a sample config file if it doesn't exist."""
    config_file = Path("config/config.yaml")
    example_config = Path("config/config.example.yaml")
    
    if config_file.exists():
        print(" Config file already exists")
        return True
    
    if example_config.exists():
        print(" Creating config file from example...")
        shutil.copy(example_config, config_file)
        print(" Config file created. Edit config/config.yaml to add your API keys.")
    else:
        print("  No example config found. Create config/config.yaml manually.")
    
    return True


def run_tests():
    """Run a quick test to verify setup."""
    print("\n Running quick test...")
    
    if run_command("uv run pytest tests/unit/ -x", "Running unit tests"):
        print(" All tests passed!")
        return True
    else:
        print("  Some tests failed. Check the output above.")
        return False


def main():
    """Main setup function."""
    print(" Urbanclear Traffic System - Development Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n Prerequisites check failed. Please install required tools.")
        sys.exit(1)
    
    # Setup Python environment
    if not setup_python_environment():
        print("\n Python environment setup failed.")
        sys.exit(1)
    
    # Setup dashboard
    setup_dashboard()
    
    # Create config file
    create_config_file()
    
    # Run tests
    run_tests()
    
    print("\n Setup completed successfully!")
    print("\n Next steps:")
    print("1. Edit config/config.yaml to add your API keys (optional)")
    print("2. Start the API: make api")
    print("3. Start the dashboard: cd dashboard && npm run dev")
    print("4. View API docs: http://localhost:8000/docs")
    print("5. View dashboard: http://localhost:3000")
    
    print("\n Useful commands:")
    print("- make help          # Show all available commands")
    print("- make test          # Run all tests")
    print("- make format        # Format code")
    print("- make lint          # Check code quality")
    print("- uv run python script.py  # Run any Python script")


if __name__ == "__main__":
    main() 