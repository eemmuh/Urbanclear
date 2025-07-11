"""Smoke test for CI environment verification."""

import sys
import pytest


def test_python_version():
    """Test that we're running on a supported Python version."""
    version = sys.version_info
    assert version.major == 3
    assert version.minor in [9, 10, 11, 12]  # Support 3.9-3.12


def test_basic_imports():
    """Test that basic imports work."""
    try:
        import pytest
        import coverage
        import fastapi
        import pydantic
        print("✅ All basic imports successful")
    except ImportError as e:
        pytest.fail(f"Failed to import required module: {e}")


def test_src_imports():
    """Test that our source code imports work."""
    try:
        import src
        import src.api
        import src.core
        import src.data
        import src.models
        print("✅ All src imports successful")
    except ImportError as e:
        pytest.fail(f"Failed to import src module: {e}")


def test_api_models():
    """Test that API models can be imported."""
    try:
        from src.api.models import TrafficDataRequest, TrafficDataResponse
        print("✅ API models import successful")
    except ImportError as e:
        pytest.fail(f"Failed to import API models: {e}")


def test_simple_math():
    """Simple math test to ensure basic functionality."""
    assert 2 + 2 == 4
    assert 10 * 5 == 50
    print("✅ Basic math operations work")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 