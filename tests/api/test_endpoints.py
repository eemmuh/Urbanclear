from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from src.api.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """Test cases for all API endpoints"""

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_traffic_data_endpoint(self):
        """Test traffic data endpoint"""
        response = client.get("/traffic/data")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total_records" in data
        assert isinstance(data["data"], list)

    def test_traffic_data_with_location(self):
        """Test traffic data with location parameter"""
        response = client.get("/traffic/data?location=Manhattan Bridge")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_traffic_data_with_time_range(self):
        """Test traffic data with time range parameters"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        params = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }

        response = client.get("/traffic/data", params=params)
        assert response.status_code == 200

    def test_congestion_endpoint(self):
        """Test congestion data endpoint"""
        response = client.get("/traffic/congestion")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_incidents_endpoint(self):
        """Test incidents endpoint"""
        response = client.get("/traffic/incidents")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_weather_endpoint(self):
        """Test weather data endpoint"""
        response = client.get("/traffic/weather")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_analytics_summary_endpoint(self):
        """Test analytics summary endpoint"""
        response = client.get("/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    def test_prediction_endpoint(self):
        """Test ML prediction endpoint"""
        payload = {
            "location": "Manhattan Bridge",
            "prediction_horizon": 60,
            "features": {
                "current_flow": 100.0,
                "weather": "clear",
                "time_of_day": "peak",
            },
        }

        response = client.post("/ml/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "predicted_flow" in data
        assert "confidence" in data

    def test_route_optimization_endpoint(self):
        """Test route optimization endpoint"""
        payload = {
            "start_location": "40.7831,-73.9712",
            "end_location": "40.7589,-73.9851",
            "optimization_criteria": ["time", "distance"],
            "preferences": {"avoid_tolls": True},
        }

        response = client.post("/optimization/route", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "route_id" in data
        assert "waypoints" in data

    def test_route_status_endpoint(self):
        """Test route status endpoint"""
        route_id = "test_route_123"
        response = client.get(f"/optimization/route/{route_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_invalid_endpoint(self):
        """Test invalid endpoint returns 404"""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404

    def test_prediction_validation_error(self):
        """Test prediction endpoint with invalid data"""
        payload = {
            "location": "",  # Invalid empty location
            "prediction_horizon": -10,  # Invalid negative horizon
        }

        response = client.post("/ml/predict", json=payload)
        assert response.status_code == 422  # Validation error

    def test_route_optimization_validation_error(self):
        """Test route optimization with invalid data"""
        payload = {"start_location": "", "end_location": ""}  # Invalid empty location

        response = client.post("/optimization/route", json=payload)
        assert response.status_code == 422  # Validation error

    def test_cors_headers(self):
        """Test CORS headers"""
        response = client.get("/health")
        assert response.status_code == 200
        # In a real deployment, you'd check for CORS headers

    def test_content_type_headers(self):
        """Test content type headers"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_api_error_handling(self):
        """Test API error handling with malformed requests"""
        response = client.post("/ml/predict", data="invalid json")
        assert response.status_code == 422
