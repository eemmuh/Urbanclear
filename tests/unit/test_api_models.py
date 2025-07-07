import pytest
from pydantic import ValidationError
from datetime import datetime

from src.api.models import (
    TrafficDataRequest,
    TrafficDataResponse,
    PredictionRequest,
    PredictionResponse,
    RouteOptimizationRequest,
    RouteOptimizationResponse,
)


class TestTrafficDataRequest:
    """Test cases for TrafficDataRequest model"""

    def test_valid_request(self):
        """Test valid traffic data request"""
        request = TrafficDataRequest(
            location="Manhattan Bridge",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        assert request.location == "Manhattan Bridge"
        assert isinstance(request.start_time, datetime)
        assert isinstance(request.end_time, datetime)

    def test_optional_fields(self):
        """Test request with optional fields"""
        request = TrafficDataRequest()
        assert request.location is None
        assert request.start_time is None
        assert request.end_time is None

    def test_location_validation(self):
        """Test location field validation"""
        request = TrafficDataRequest(location="")
        assert request.location == ""  # Empty string is allowed

        request = TrafficDataRequest(location="Valid Location")
        assert request.location == "Valid Location"


class TestTrafficDataResponse:
    """Test cases for TrafficDataResponse model"""

    def test_valid_response(self):
        """Test valid traffic data response"""
        response = TrafficDataResponse(
            data=[
                {
                    "location": "Manhattan Bridge",
                    "flow_rate": 100.5,
                    "speed": 45.0,
                    "timestamp": "2023-01-01T12:00:00",
                }
            ],
            total_records=1,
        )
        assert len(response.data) == 1
        assert response.total_records == 1
        assert response.data[0]["location"] == "Manhattan Bridge"

    def test_empty_response(self):
        """Test empty response"""
        response = TrafficDataResponse(data=[], total_records=0)
        assert len(response.data) == 0
        assert response.total_records == 0


class TestPredictionRequest:
    """Test cases for PredictionRequest model"""

    def test_valid_request(self):
        """Test valid prediction request"""
        request = PredictionRequest(
            location="Manhattan Bridge",
            prediction_horizon=60,
            features={"current_flow": 100.0, "weather": "clear", "time_of_day": "peak"},
        )
        assert request.location == "Manhattan Bridge"
        assert request.prediction_horizon == 60
        assert request.features["current_flow"] == 100.0

    def test_required_fields(self):
        """Test that required fields are enforced"""
        with pytest.raises(ValidationError):
            PredictionRequest()

    def test_prediction_horizon_validation(self):
        """Test prediction horizon validation"""
        request = PredictionRequest(location="Test Location", prediction_horizon=30)
        assert request.prediction_horizon == 30

        # Test negative horizon
        with pytest.raises(ValidationError):
            PredictionRequest(location="Test Location", prediction_horizon=-10)


class TestPredictionResponse:
    """Test cases for PredictionResponse model"""

    def test_valid_response(self):
        """Test valid prediction response"""
        response = PredictionResponse(
            location="Manhattan Bridge",
            predicted_flow=120.5,
            confidence=0.85,
            prediction_time=datetime.now(),
        )
        assert response.location == "Manhattan Bridge"
        assert response.predicted_flow == 120.5
        assert response.confidence == 0.85
        assert isinstance(response.prediction_time, datetime)

    def test_confidence_validation(self):
        """Test confidence score validation"""
        # Valid confidence
        response = PredictionResponse(
            location="Test", predicted_flow=100.0, confidence=0.95
        )
        assert response.confidence == 0.95

        # Invalid confidence (outside 0-1 range)
        with pytest.raises(ValidationError):
            PredictionResponse(location="Test", predicted_flow=100.0, confidence=1.5)


class TestRouteOptimizationRequest:
    """Test cases for RouteOptimizationRequest model"""

    def test_valid_request(self):
        """Test valid route optimization request"""
        request = RouteOptimizationRequest(
            start_location="Point A",
            end_location="Point B",
            optimization_criteria=["time", "distance"],
            preferences={"avoid_tolls": True},
        )
        assert request.start_location == "Point A"
        assert request.end_location == "Point B"
        assert "time" in request.optimization_criteria
        assert request.preferences["avoid_tolls"] is True

    def test_required_fields(self):
        """Test that required fields are enforced"""
        with pytest.raises(ValidationError):
            RouteOptimizationRequest()

    def test_optimization_criteria_validation(self):
        """Test optimization criteria validation"""
        request = RouteOptimizationRequest(
            start_location="A", end_location="B", optimization_criteria=["time"]
        )
        assert request.optimization_criteria == ["time"]


class TestRouteOptimizationResponse:
    """Test cases for RouteOptimizationResponse model"""

    def test_valid_response(self):
        """Test valid route optimization response"""
        response = RouteOptimizationResponse(
            route_id="route_123",
            waypoints=["Point A", "Point B", "Point C"],
            estimated_time=30.5,
            estimated_distance=25.0,
            optimization_score=0.9,
        )
        assert response.route_id == "route_123"
        assert len(response.waypoints) == 3
        assert response.estimated_time == 30.5
        assert response.estimated_distance == 25.0
        assert response.optimization_score == 0.9

    def test_empty_waypoints(self):
        """Test response with empty waypoints"""
        response = RouteOptimizationResponse(
            route_id="route_123",
            waypoints=[],
            estimated_time=0.0,
            estimated_distance=0.0,
        )
        assert len(response.waypoints) == 0
        assert response.estimated_time == 0.0
