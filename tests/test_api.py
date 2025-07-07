"""
Comprehensive API tests for Urbanclear traffic system
"""

import pytest
from unittest.mock import patch

from tests.conftest import (
    assert_response_structure,
    assert_valid_timestamp,
    assert_valid_coordinates,
)


class TestHealthEndpoints:
    """Test health and status endpoints"""

    @pytest.mark.api
    def test_root_endpoint(self, test_client):
        """Test root endpoint returns basic info"""
        response = test_client.get("/")
        assert response.status_code == 200

        data = response.json()
        expected_keys = ["message", "version", "timestamp", "status"]
        assert_response_structure(data, expected_keys)

        assert "Urbanclear" in data["message"]
        assert data["status"] == "operational"
        assert assert_valid_timestamp(data["timestamp"])

    @pytest.mark.api
    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        expected_keys = ["status", "timestamp", "services"]
        assert_response_structure(data, expected_keys)

        assert data["status"] == "healthy"
        assert "api" in data["services"]
        assert assert_valid_timestamp(data["timestamp"])

    @pytest.mark.api
    def test_metrics_endpoint(self, test_client):
        """Test Prometheus metrics endpoint"""
        response = test_client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


class TestTrafficEndpoints:
    """Test traffic data endpoints"""

    @pytest.mark.api
    def test_get_current_traffic_success(self, test_client, sample_traffic_data):
        """Test successful retrieval of current traffic data"""
        with patch(
            "src.data.traffic_service.TrafficService.get_current_conditions"
        ) as mock_service:
            mock_service.return_value = sample_traffic_data

            response = test_client.get("/api/v1/traffic/current")
            assert response.status_code == 200

            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2

            # Check structure of first item
            first_item = data[0]
            expected_keys = [
                "sensor_id",
                "location",
                "speed",
                "volume",
                "density",
                "severity",
                "timestamp",
            ]
            assert_response_structure(first_item, expected_keys)

            # Validate coordinates
            location = first_item["location"]
            assert_valid_coordinates(location["latitude"], location["longitude"])

    @pytest.mark.api
    def test_get_current_traffic_with_location_filter(
        self, test_client, sample_traffic_data
    ):
        """Test traffic data with location filter"""
        with patch(
            "src.data.traffic_service.TrafficService.get_current_conditions"
        ) as mock_service:
            mock_service.return_value = [sample_traffic_data[0]]  # Return filtered data

            response = test_client.get("/api/v1/traffic/current?location=Central Park")
            assert response.status_code == 200

            data = response.json()
            assert len(data) == 1
            assert "Central Park" in data[0]["location"]["address"]

    @pytest.mark.api
    def test_get_current_traffic_with_radius(self, test_client, sample_traffic_data):
        """Test traffic data with radius filter"""
        with patch(
            "src.data.traffic_service.TrafficService.get_current_conditions"
        ) as mock_service:
            mock_service.return_value = sample_traffic_data

            response = test_client.get("/api/v1/traffic/current?radius=5.0")
            assert response.status_code == 200

            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.api
    def test_get_current_traffic_service_error(self, test_client):
        """Test error handling when traffic service fails"""
        with patch(
            "src.data.traffic_service.TrafficService.get_current_conditions"
        ) as mock_service:
            mock_service.side_effect = Exception("Service unavailable")

            response = test_client.get("/api/v1/traffic/current")
            assert response.status_code == 500

            data = response.json()
            assert "detail" in data
            assert "Failed to retrieve traffic data" in data["detail"]

    @pytest.mark.api
    def test_get_traffic_predictions_success(self, test_client):
        """Test successful traffic predictions"""
        mock_predictions = [
            {
                "timestamp": "2024-01-01T13:00:00Z",
                "location": "Central Park South",
                "predicted_speed": 22.5,
                "predicted_volume": 1350,
                "confidence": 0.85,
            }
        ]

        with patch("src.models.prediction.TrafficPredictor.predict") as mock_predictor:
            mock_predictor.return_value = mock_predictions

            response = test_client.get(
                "/api/v1/traffic/predict?location=Central Park&hours_ahead=2"
            )
            assert response.status_code == 200

            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1

            prediction = data[0]
            expected_keys = [
                "timestamp",
                "location",
                "predicted_speed",
                "predicted_volume",
                "confidence",
            ]
            assert_response_structure(prediction, expected_keys)

            assert 0 <= prediction["confidence"] <= 1

    @pytest.mark.api
    def test_get_traffic_predictions_invalid_hours(self, test_client):
        """Test traffic predictions with invalid hours_ahead parameter"""
        response = test_client.get(
            "/api/v1/traffic/predict?location=Central Park&hours_ahead=25"
        )
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "hours_ahead must be between 1 and 24" in data["detail"]


class TestRouteEndpoints:
    """Test route optimization endpoints"""

    @pytest.mark.api
    def test_optimize_route_success(self, test_client):
        """Test successful route optimization"""
        route_request = {
            "origin": {"latitude": 40.7831, "longitude": -73.9712},
            "destination": {"latitude": 40.7505, "longitude": -73.9934},
            "preferences": {"avoid_highways": False, "fastest_route": True},
        }

        mock_response = {
            "route_id": "route_123",
            "total_distance": 5.2,
            "estimated_time": 18,
            "optimization_score": 0.89,
            "waypoints": [
                {"latitude": 40.7831, "longitude": -73.9712, "instruction": "Start"},
                {
                    "latitude": 40.7505,
                    "longitude": -73.9934,
                    "instruction": "Destination",
                },
            ],
        }

        with patch(
            "src.models.optimization.RouteOptimizer.optimize_route"
        ) as mock_optimizer:
            mock_optimizer.return_value = mock_response

            response = test_client.post("/api/v1/routes/optimize", json=route_request)
            assert response.status_code == 200

            data = response.json()
            expected_keys = [
                "route_id",
                "total_distance",
                "estimated_time",
                "optimization_score",
                "waypoints",
            ]
            assert_response_structure(data, expected_keys)

            assert data["total_distance"] > 0
            assert data["estimated_time"] > 0
            assert 0 <= data["optimization_score"] <= 1

    @pytest.mark.api
    def test_optimize_route_invalid_coordinates(self, test_client):
        """Test route optimization with invalid coordinates"""
        route_request = {
            "origin": {"latitude": 91.0, "longitude": -73.9712},  # Invalid latitude
            "destination": {"latitude": 40.7505, "longitude": -73.9934},
        }

        response = test_client.post("/api/v1/routes/optimize", json=route_request)
        assert response.status_code == 422  # Validation error

    @pytest.mark.api
    def test_optimize_route_missing_destination(self, test_client):
        """Test route optimization with missing destination"""
        route_request = {
            "origin": {"latitude": 40.7831, "longitude": -73.9712}
            # Missing destination
        }

        response = test_client.post("/api/v1/routes/optimize", json=route_request)
        assert response.status_code == 422  # Validation error


class TestIncidentEndpoints:
    """Test incident management endpoints"""

    @pytest.mark.api
    def test_get_active_incidents_success(self, test_client, sample_incident_data):
        """Test successful retrieval of active incidents"""
        with patch(
            "src.models.incident_detection.IncidentDetector.get_active_incidents"
        ) as mock_detector:
            mock_detector.return_value = sample_incident_data

            response = test_client.get("/api/v1/incidents/active")
            assert response.status_code == 200

            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1

            incident = data[0]
            expected_keys = [
                "id",
                "type",
                "severity",
                "location",
                "description",
                "reported_at",
                "status",
            ]
            assert_response_structure(incident, expected_keys)

            assert incident["status"] == "active"
            assert assert_valid_timestamp(incident["reported_at"])

    @pytest.mark.api
    def test_get_active_incidents_with_filters(self, test_client, sample_incident_data):
        """Test incident retrieval with filters"""
        with patch(
            "src.models.incident_detection.IncidentDetector.get_active_incidents"
        ) as mock_detector:
            mock_detector.return_value = sample_incident_data

            response = test_client.get(
                "/api/v1/incidents/active?location=42nd St&severity=high"
            )
            assert response.status_code == 200

            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.api
    def test_create_incident_report_success(self, test_client):
        """Test successful incident report creation"""
        incident_data = {
            "type": "construction",
            "severity": "moderate",
            "location": {
                "latitude": 40.7589,
                "longitude": -73.9851,
                "address": "42nd St & 8th Ave",
            },
            "description": "Road construction causing lane closure",
        }

        with patch(
            "src.models.incident_detection.IncidentDetector.create_incident"
        ) as mock_detector:
            mock_detector.return_value = {
                "id": "incident_456",
                "status": "reported",
                "created_at": "2024-01-01T12:00:00Z",
            }

            response = test_client.post("/api/v1/incidents/report", json=incident_data)
            assert response.status_code == 201

            data = response.json()
            assert data["status"] == "reported"
            assert "id" in data


class TestAnalyticsEndpoints:
    """Test analytics and reporting endpoints"""

    @pytest.mark.api
    def test_get_analytics_summary_success(self, test_client):
        """Test successful analytics summary retrieval"""
        mock_summary = {
            "total_vehicles": 12500,
            "average_speed": 28.5,
            "congestion_level": 0.65,
            "incidents_count": 3,
            "period": "24h",
            "generated_at": "2024-01-01T12:00:00Z",
        }

        with patch(
            "src.data.traffic_service.TrafficService.get_analytics_summary"
        ) as mock_service:
            mock_service.return_value = mock_summary

            response = test_client.get("/api/v1/analytics/summary?period=24h")
            assert response.status_code == 200

            data = response.json()
            expected_keys = [
                "total_vehicles",
                "average_speed",
                "congestion_level",
                "incidents_count",
            ]
            assert_response_structure(data, expected_keys)

            assert data["total_vehicles"] > 0
            assert data["average_speed"] > 0
            assert 0 <= data["congestion_level"] <= 1

    @pytest.mark.api
    def test_get_analytics_summary_invalid_period(self, test_client):
        """Test analytics summary with invalid period"""
        response = test_client.get("/api/v1/analytics/summary?period=invalid")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "Invalid period" in data["detail"]

    @pytest.mark.api
    def test_get_performance_metrics_success(self, test_client):
        """Test successful performance metrics retrieval"""
        mock_metrics = {
            "current_level": 0.65,
            "trend": "stable",
            "historical_average": 0.68,
            "improvement": "5%",
        }

        with patch(
            "src.data.traffic_service.TrafficService.get_performance_metrics"
        ) as mock_service:
            mock_service.return_value = mock_metrics

            response = test_client.get(
                "/api/v1/analytics/performance?metric_type=congestion"
            )
            assert response.status_code == 200

            data = response.json()
            expected_keys = ["current_level", "trend", "historical_average"]
            assert_response_structure(data, expected_keys)

    @pytest.mark.api
    def test_get_performance_metrics_invalid_type(self, test_client):
        """Test performance metrics with invalid metric type"""
        response = test_client.get("/api/v1/analytics/performance?metric_type=invalid")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "Invalid metric type" in data["detail"]


class TestSignalEndpoints:
    """Test traffic signal optimization endpoints"""

    @pytest.mark.api
    def test_optimize_signals_success(self, test_client):
        """Test successful signal optimization"""
        optimization_request = {
            "intersection_id": "intersection_123",
            "optimization_period": 60,
            "priority_direction": "north_south",
            "consider_pedestrians": True,
            "emergency_override": False,
        }

        mock_response = {
            "intersection_id": "intersection_123",
            "optimization_score": 0.82,
            "recommended_timing": {
                "north_south": 50,
                "east_west": 40,
                "pedestrian": 15,
            },
            "estimated_improvement": "15% reduction in wait time",
        }

        with patch(
            "src.data.traffic_service.TrafficService.optimize_signals"
        ) as mock_service:
            mock_service.return_value = mock_response

            response = test_client.post(
                "/api/v1/signals/optimize", json=optimization_request
            )
            assert response.status_code == 200

            data = response.json()
            expected_keys = [
                "intersection_id",
                "optimization_score",
                "recommended_timing",
                "estimated_improvement",
            ]
            assert_response_structure(data, expected_keys)

            assert 0 <= data["optimization_score"] <= 1

    @pytest.mark.api
    def test_get_signal_status_success(self, test_client):
        """Test successful signal status retrieval"""
        mock_status = {
            "intersection_id": "intersection_123",
            "status": "operational",
            "current_phase": "north_south",
            "time_remaining": 25,
            "last_optimization": "2024-01-01T10:00:00Z",
        }

        with patch(
            "src.data.traffic_service.TrafficService.get_signal_status"
        ) as mock_service:
            mock_service.return_value = mock_status

            response = test_client.get(
                "/api/v1/signals/status?intersection_id=intersection_123"
            )
            assert response.status_code == 200

            data = response.json()
            expected_keys = [
                "intersection_id",
                "status",
                "current_phase",
                "time_remaining",
            ]
            assert_response_structure(data, expected_keys)

            assert data["status"] == "operational"
            assert data["time_remaining"] >= 0


class TestAdminEndpoints:
    """Test admin and system management endpoints"""

    @pytest.mark.api
    def test_retrain_models_success(self, test_client):
        """Test successful model retraining"""
        with patch("src.models.prediction.TrafficPredictor.retrain") as mock_retrain:
            mock_retrain.return_value = {"status": "success", "accuracy": 0.87}

            response = test_client.post(
                "/api/v1/admin/models/retrain?model_type=traffic_prediction"
            )
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "success"
            assert "accuracy" in data["result"]

    @pytest.mark.api
    def test_retrain_models_invalid_type(self, test_client):
        """Test model retraining with invalid model type"""
        response = test_client.post("/api/v1/admin/models/retrain?model_type=invalid")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "Invalid model type" in data["detail"]

    @pytest.mark.api
    def test_system_stats_success(self, test_client):
        """Test successful system stats retrieval"""
        mock_stats = {
            "uptime": 86400,
            "active_sensors": 147,
            "data_points_processed": 2500000,
            "prediction_accuracy": 0.87,
            "api_requests_today": 15420,
            "average_response_time": 125.5,
        }

        with patch(
            "src.data.traffic_service.TrafficService.get_system_stats"
        ) as mock_service:
            mock_service.return_value = mock_stats

            response = test_client.get("/api/v1/admin/stats")
            assert response.status_code == 200

            data = response.json()
            expected_keys = [
                "uptime",
                "active_sensors",
                "data_points_processed",
                "prediction_accuracy",
            ]
            assert_response_structure(data, expected_keys)

            assert data["uptime"] > 0
            assert data["active_sensors"] > 0
            assert 0 <= data["prediction_accuracy"] <= 1


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.api
    def test_404_for_nonexistent_endpoint(self, test_client):
        """Test 404 response for non-existent endpoint"""
        response = test_client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    @pytest.mark.api
    def test_method_not_allowed(self, test_client):
        """Test 405 response for wrong HTTP method"""
        response = test_client.post("/api/v1/traffic/current")
        assert response.status_code == 405

    @pytest.mark.api
    def test_malformed_json_request(self, test_client):
        """Test handling of malformed JSON in request body"""
        response = test_client.post(
            "/api/v1/routes/optimize",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.api
    def test_large_request_body(self, test_client):
        """Test handling of excessively large request body"""
        large_data = {"data": "x" * 1000000}  # 1MB of data
        response = test_client.post("/api/v1/routes/optimize", json=large_data)
        # Should be rejected due to size limits or validation
        assert response.status_code in [413, 422]


class TestRateLimiting:
    """Test rate limiting functionality"""

    @pytest.mark.api
    @pytest.mark.slow
    def test_rate_limiting_enforcement(self, test_client):
        """Test that rate limiting is enforced"""
        # This test would require enabling rate limiting in the test environment
        # and making multiple rapid requests
        pass  # Placeholder for actual rate limiting test


class TestSecurityHeaders:
    """Test security headers and CORS"""

    @pytest.mark.api
    def test_cors_headers_present(self, test_client):
        """Test that CORS headers are present"""
        response = test_client.options("/api/v1/traffic/current")
        assert "access-control-allow-origin" in response.headers

    @pytest.mark.api
    def test_security_headers(self, test_client):
        """Test that security headers are present"""
        response = test_client.get("/")
        # Check for security headers that should be present
        # This depends on your security middleware configuration
        assert response.status_code == 200
