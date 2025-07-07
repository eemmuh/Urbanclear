from datetime import datetime, timedelta
import pytest

from src.data.traffic_service import TrafficService
from src.data.mock_data_generator import MockDataGenerator


class TestTrafficService:
    """Test cases for TrafficService"""

    def test_init(self):
        """Test TrafficService initialization"""
        service = TrafficService()
        assert service is not None
        assert hasattr(service, "get_current_conditions")
        assert hasattr(service, "get_historical_data")
        assert hasattr(service, "get_analytics_summary")

    @pytest.mark.asyncio
    async def test_get_current_conditions(self):
        """Test that get_current_conditions returns data"""
        service = TrafficService()
        result = await service.get_current_conditions()
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_get_historical_data(self):
        """Test that get_historical_data returns data"""
        service = TrafficService()
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        result = await service.get_historical_data("Times Square", start_date, end_date)
        assert isinstance(result, dict)
        assert "location" in result
        assert "data_points" in result

    @pytest.mark.asyncio
    async def test_get_analytics_summary(self):
        """Test that get_analytics_summary returns data"""
        service = TrafficService()
        result = await service.get_analytics_summary("daily")
        assert result is not None
        assert hasattr(result, "period")

    @pytest.mark.asyncio
    async def test_get_system_stats(self):
        """Test that get_system_stats returns data"""
        service = TrafficService()
        result = await service.get_system_stats()
        assert isinstance(result, dict)
        assert "uptime" in result


class TestMockDataGenerator:
    """Test cases for MockDataGenerator"""

    def test_init(self):
        """Test MockDataGenerator initialization"""
        generator = MockDataGenerator()
        assert generator is not None
        assert hasattr(generator, "generate_current_conditions")
        assert hasattr(generator, "generate_incidents")
        assert hasattr(generator, "generate_traffic_predictions")

    def test_generate_current_conditions(self):
        """Test that generate_current_conditions returns data"""
        generator = MockDataGenerator()
        data = generator.generate_current_conditions()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_generate_incidents(self):
        """Test that generate_incidents returns data"""
        generator = MockDataGenerator()
        data = generator.generate_incidents()
        assert isinstance(data, list)
        # Note: incidents may be empty if no incidents are generated

    def test_generate_traffic_predictions(self):
        """Test that generate_traffic_predictions returns data"""
        generator = MockDataGenerator()
        data = generator.generate_traffic_predictions("Times Square", 2)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_generate_real_time_data(self):
        """Test that generate_real_time_data returns data"""
        generator = MockDataGenerator()
        data = generator.generate_real_time_data()
        assert isinstance(data, dict)
        assert "summary" in data
        assert "timestamp" in data["summary"]

    def test_generate_traffic_conditions(self):
        """Test that generate_traffic_conditions returns data"""
        generator = MockDataGenerator()
        data = generator.generate_traffic_conditions()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_generate_performance_data(self):
        """Test that generate_performance_data returns data"""
        generator = MockDataGenerator()
        data = generator.generate_performance_data()
        assert isinstance(data, dict)
        assert "cpu_usage" in data or "memory_usage" in data

    def test_generate_geographic_data(self):
        """Test that generate_geographic_data returns data"""
        generator = MockDataGenerator()
        data = generator.generate_geographic_data()
        assert isinstance(data, dict)
        assert "zones" in data or "citywide_metrics" in data

    def test_generate_analytics_summary(self):
        """Test that generate_analytics_summary returns data"""
        generator = MockDataGenerator()
        data = generator.generate_analytics_summary("daily")
        assert isinstance(data, dict)
        assert "period" in data
