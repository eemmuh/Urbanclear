"""
Pytest configuration and fixtures for Urbanclear testing
"""

import pytest
import asyncio
import os
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import shutil

# Import the main app and dependencies
from src.api.main import app
from src.api.dependencies import get_db, get_cache, get_current_user
from src.data.traffic_service import TrafficService
from src.models.prediction import TrafficPredictor
from src.models.optimization import RouteOptimizer
from src.models.incident_detection import IncidentDetector


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Test configuration settings"""
    return {
        "database": {
            "postgres": {
                "host": "localhost",
                "port": 5432,
                "database": "test_traffic_db",
                "username": "test_user",
                "password": "test_password",
                "pool_size": 5,
                "max_overflow": 10,
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "database": 1,  # Use different DB for testing
                "password": None,
            },
            "mongodb": {
                "host": "localhost",
                "port": 27017,
                "database": "test_traffic_logs",
                "username": "test_user",
                "password": "test_password",
            },
        },
        "api": {
            "rate_limiting": {"enabled": False},  # Disable rate limiting in tests
            "authentication": {
                "enabled": False  # Disable auth in tests unless specifically testing
            },
        },
    }


@pytest.fixture(scope="session")
def test_database():
    """Create test database engine"""
    database_url = "sqlite:///./test.db"  # Use SQLite for testing
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    # Create tables
    from src.api.models import Base

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal

    # Cleanup
    os.remove("./test.db")


@pytest.fixture
def test_db_session(test_database):
    """Create a test database session"""
    session = test_database()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.exists.return_value = True
    mock_redis.ping.return_value = True
    mock_redis.incr.return_value = 1
    mock_redis.lpush.return_value = 1
    mock_redis.ltrim.return_value = True
    return mock_redis


@pytest.fixture
def mock_user():
    """Mock authenticated user for testing"""
    return {
        "id": "test_user_123",
        "username": "test_user",
        "email": "test@example.com",
        "role": "admin",
        "permissions": ["read:all", "write:all", "admin:all"],
        "is_active": True,
    }


@pytest.fixture
def test_client(test_db_session, mock_redis, mock_user):
    """Create test client with mocked dependencies"""

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    def override_get_cache():
        return mock_redis

    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache] = override_get_cache
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_traffic_data():
    """Sample traffic data for testing"""
    return [
        {
            "sensor_id": "sensor_001",
            "location": {
                "latitude": 40.7831,
                "longitude": -73.9712,
                "address": "Central Park South & 5th Ave",
            },
            "speed": 25.5,
            "volume": 1200,
            "density": 48.0,
            "severity": "moderate",
            "timestamp": "2024-01-01T12:00:00Z",
        },
        {
            "sensor_id": "sensor_002",
            "location": {
                "latitude": 40.7505,
                "longitude": -73.9934,
                "address": "Times Square & Broadway",
            },
            "speed": 15.2,
            "volume": 1800,
            "density": 118.4,
            "severity": "high",
            "timestamp": "2024-01-01T12:00:00Z",
        },
    ]


@pytest.fixture
def sample_incident_data():
    """Sample incident data for testing"""
    return [
        {
            "id": "incident_001",
            "type": "accident",
            "severity": "high",
            "location": {
                "latitude": 40.7589,
                "longitude": -73.9851,
                "address": "42nd St & 8th Ave",
            },
            "description": "Multi-vehicle collision",
            "reported_at": "2024-01-01T11:30:00Z",
            "status": "active",
            "estimated_clearance": "2024-01-01T13:00:00Z",
        }
    ]


@pytest.fixture
def mock_traffic_service():
    """Mock traffic service for testing"""
    service = Mock(spec=TrafficService)
    service.get_current_conditions = AsyncMock(return_value=[])
    service.get_analytics_summary = AsyncMock(
        return_value={
            "total_vehicles": 12500,
            "average_speed": 28.5,
            "congestion_level": 0.65,
            "incidents_count": 3,
        }
    )
    service.get_performance_metrics = AsyncMock(
        return_value={
            "current_level": 0.65,
            "trend": "stable",
            "historical_average": 0.68,
        }
    )
    service.optimize_signals = AsyncMock(
        return_value={
            "intersection_id": "test_intersection",
            "optimization_score": 0.82,
            "estimated_improvement": "15% reduction in wait time",
        }
    )
    return service


@pytest.fixture
def mock_traffic_predictor():
    """Mock traffic predictor for testing"""
    predictor = Mock(spec=TrafficPredictor)
    predictor.predict = AsyncMock(
        return_value=[
            {
                "timestamp": "2024-01-01T13:00:00Z",
                "location": "Central Park South",
                "predicted_speed": 22.5,
                "predicted_volume": 1350,
                "confidence": 0.85,
            }
        ]
    )
    predictor.retrain = AsyncMock(return_value={"status": "success", "accuracy": 0.87})
    return predictor


@pytest.fixture
def mock_route_optimizer():
    """Mock route optimizer for testing"""
    optimizer = Mock(spec=RouteOptimizer)
    optimizer.optimize_route = AsyncMock(
        return_value={
            "route_id": "route_123",
            "total_distance": 5.2,
            "estimated_time": 18,
            "optimization_score": 0.89,
            "waypoints": [],
        }
    )
    return optimizer


@pytest.fixture
def mock_incident_detector():
    """Mock incident detector for testing"""
    detector = Mock(spec=IncidentDetector)
    detector.get_active_incidents = AsyncMock(return_value=[])
    detector.detect_incidents = AsyncMock(return_value=[])
    detector.retrain = AsyncMock(return_value={"status": "success", "accuracy": 0.91})
    return detector


@pytest.fixture
def temp_directory():
    """Create temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_external_apis():
    """Mock external API responses"""
    return {
        "weather_api": {
            "temperature": 22.5,
            "humidity": 65,
            "precipitation": 0.0,
            "wind_speed": 10.2,
        },
        "traffic_sensors": {
            "sensor_001": {"speed": 25.5, "volume": 1200},
            "sensor_002": {"speed": 15.2, "volume": 1800},
        },
    }


# Helper functions for testing
def assert_response_structure(response_data: Dict[str, Any], expected_keys: list):
    """Assert that response has expected structure"""
    for key in expected_keys:
        assert key in response_data, f"Missing key: {key}"


def assert_valid_timestamp(timestamp_str: str):
    """Assert that timestamp is valid ISO format"""
    from datetime import datetime

    try:
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def assert_valid_coordinates(lat: float, lng: float):
    """Assert that coordinates are valid"""
    assert -90 <= lat <= 90, f"Invalid latitude: {lat}"
    assert -180 <= lng <= 180, f"Invalid longitude: {lng}"


# Pytest markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow
pytest.mark.api = pytest.mark.api
pytest.mark.ml = pytest.mark.ml
pytest.mark.database = pytest.mark.database
