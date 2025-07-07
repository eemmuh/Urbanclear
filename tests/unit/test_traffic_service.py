import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data.traffic_service import TrafficDataService
from src.data.mock_data_generator import MockTrafficDataGenerator


class TestTrafficDataService:
    """Test cases for TrafficDataService"""

    def test_init(self):
        """Test TrafficDataService initialization"""
        service = TrafficDataService()
        assert service is not None
        assert hasattr(service, 'get_traffic_data')

    def test_get_traffic_data_returns_dataframe(self):
        """Test that get_traffic_data returns a DataFrame"""
        service = TrafficDataService()
        data = service.get_traffic_data()
        assert isinstance(data, pd.DataFrame)
        assert not data.empty

    def test_get_traffic_data_has_required_columns(self):
        """Test that traffic data has required columns"""
        service = TrafficDataService()
        data = service.get_traffic_data()
        
        required_columns = ['location', 'flow_rate', 'speed', 'timestamp']
        for col in required_columns:
            assert col in data.columns

    def test_get_traffic_data_with_location_filter(self):
        """Test filtering traffic data by location"""
        service = TrafficDataService()
        location = "Manhattan Bridge"
        data = service.get_traffic_data(location=location)
        
        if not data.empty:
            assert all(data['location'] == location)

    def test_get_traffic_data_with_time_range(self):
        """Test filtering traffic data by time range"""
        service = TrafficDataService()
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        data = service.get_traffic_data(start_time=start_time, end_time=end_time)
        assert isinstance(data, pd.DataFrame)


class TestMockTrafficDataGenerator:
    """Test cases for MockTrafficDataGenerator"""

    def test_init(self):
        """Test MockTrafficDataGenerator initialization"""
        generator = MockTrafficDataGenerator()
        assert generator is not None
        assert hasattr(generator, 'generate_traffic_data')

    def test_generate_traffic_data_returns_dataframe(self):
        """Test that generate_traffic_data returns a DataFrame"""
        generator = MockTrafficDataGenerator()
        data = generator.generate_traffic_data()
        assert isinstance(data, pd.DataFrame)
        assert not data.empty

    def test_generate_traffic_data_with_rows(self):
        """Test generating specific number of rows"""
        generator = MockTrafficDataGenerator()
        rows = 10
        data = generator.generate_traffic_data(rows=rows)
        assert len(data) == rows

    def test_generate_traffic_data_has_required_columns(self):
        """Test that generated data has required columns"""
        generator = MockTrafficDataGenerator()
        data = generator.generate_traffic_data()
        
        required_columns = ['location', 'flow_rate', 'speed', 'timestamp']
        for col in required_columns:
            assert col in data.columns

    def test_generate_traffic_data_column_types(self):
        """Test that generated data has correct column types"""
        generator = MockTrafficDataGenerator()
        data = generator.generate_traffic_data()
        
        assert data['flow_rate'].dtype in [np.float64, np.int64]
        assert data['speed'].dtype in [np.float64, np.int64]
        assert pd.api.types.is_datetime64_any_dtype(data['timestamp'])

    def test_generate_traffic_data_values_in_range(self):
        """Test that generated values are within reasonable ranges"""
        generator = MockTrafficDataGenerator()
        data = generator.generate_traffic_data()
        
        # Flow rate should be non-negative
        assert all(data['flow_rate'] >= 0)
        
        # Speed should be reasonable (0-100 mph)
        assert all(data['speed'] >= 0)
        assert all(data['speed'] <= 100)

    def test_generate_congestion_data(self):
        """Test generating congestion data"""
        generator = MockTrafficDataGenerator()
        data = generator.generate_congestion_data()
        assert isinstance(data, pd.DataFrame)
        assert 'congestion_level' in data.columns

    def test_generate_incident_data(self):
        """Test generating incident data"""
        generator = MockTrafficDataGenerator()
        data = generator.generate_incident_data()
        assert isinstance(data, pd.DataFrame)
        assert 'incident_type' in data.columns

    def test_generate_weather_data(self):
        """Test generating weather data"""
        generator = MockTrafficDataGenerator()
        data = generator.generate_weather_data()
        assert isinstance(data, pd.DataFrame)
        assert 'weather_condition' in data.columns 