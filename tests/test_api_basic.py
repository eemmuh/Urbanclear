"""
Basic API tests for Urbanclear traffic system
"""

import pytest


class TestBasicAPI:
    """Basic API tests"""

    @pytest.mark.api
    def test_root_endpoint(self, test_client):
        """Test root endpoint"""
        response = test_client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "Urbanclear" in data["message"]
        assert data["status"] == "operational"

    @pytest.mark.api
    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data

    @pytest.mark.api
    def test_traffic_current_endpoint(self, test_client):
        """Test current traffic endpoint"""
        response = test_client.get("/api/v1/traffic/current")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
