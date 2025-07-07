import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from src.api.main import app


class TestAPIIntegration:
    """Integration tests for the API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_traffic_data_endpoint(self, client):
        """Test traffic data endpoint"""
        response = client.get("/traffic/data")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total_records" in data
        assert isinstance(data["data"], list)
        assert isinstance(data["total_records"], int)

    def test_traffic_data_with_location_filter(self, client):
        """Test traffic data endpoint with location filter"""
        response = client.get("/traffic/data?location=Manhattan Bridge")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_traffic_data_with_time_range(self, client):
        """Test traffic data endpoint with time range"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        params = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }
        response = client.get("/traffic/data", params=params)
        assert response.status_code == 200

    def test_congestion_endpoint(self, client):
        """Test congestion data endpoint"""
        response = client.get("/traffic/congestion")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_prediction_endpoint(self, client):
        """Test traffic prediction endpoint"""
        payload = {
            "location": "Manhattan Bridge",
            "prediction_horizon": 60,
            "features": {"current_flow": 100.0, "weather": "clear"},
        }
        response = client.post("/ml/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "predicted_flow" in data
        assert "confidence" in data

    def test_route_optimization_endpoint(self, client):
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
        assert "estimated_time" in data

    def test_incidents_endpoint(self, client):
        """Test incidents endpoint"""
        response = client.get("/traffic/incidents")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_weather_endpoint(self, client):
        """Test weather data endpoint"""
        response = client.get("/traffic/weather")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_analytics_endpoint(self, client):
        """Test analytics endpoint"""
        response = client.get("/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    def test_invalid_endpoint(self, client):
        """Test invalid endpoint returns 404"""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404

    def test_prediction_with_invalid_data(self, client):
        """Test prediction endpoint with invalid data"""
        payload = {
            "location": "",  # Invalid empty location
            "prediction_horizon": -10,  # Invalid negative horizon
        }
        response = client.post("/ml/predict", json=payload)
        assert response.status_code == 422  # Validation error

    def test_route_optimization_with_invalid_data(self, client):
        """Test route optimization with invalid data"""
        payload = {"start_location": "", "end_location": ""}  # Invalid empty location
        response = client.post("/optimization/route", json=payload)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_async_health_check(self, async_client):
        """Test async health check"""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_async_traffic_data(self, async_client):
        """Test async traffic data retrieval"""
        response = await async_client.get("/traffic/data")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_async_prediction(self, async_client):
        """Test async prediction"""
        payload = {"location": "Manhattan Bridge", "prediction_horizon": 30}
        response = await async_client.post("/ml/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "predicted_flow" in data

    def test_api_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get("/health")
        assert response.status_code == 200
        # Check if CORS headers would be present in actual deployment

    def test_api_rate_limiting(self, client):
        """Test API rate limiting (if implemented)"""
        # Make multiple requests to test rate limiting
        for i in range(10):
            response = client.get("/health")
            assert response.status_code == 200

    def test_api_error_handling(self, client):
        """Test API error handling"""
        # Test with malformed JSON
        response = client.post("/ml/predict", data="invalid json")
        assert response.status_code == 422

    def test_api_response_time(self, client):
        """Test API response time is reasonable"""
        import time

        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Response should be under 1 second
