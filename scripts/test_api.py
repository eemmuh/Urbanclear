#!/usr/bin/env python3
"""
Urbanclear API Test Script
Test all major API endpoints to ensure they're working correctly
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the src directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

try:
    from api.models import RouteRequest, Location, IncidentReport, IncidentType, TrafficSeverity
    from data.traffic_service import TrafficService
    from models.prediction import TrafficPredictor
    from models.optimization import RouteOptimizer
    from models.incident_detection import IncidentDetector
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"Make sure you're running from the project root directory")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    print(f"Src path: {src_path}")
    sys.exit(1)


async def test_traffic_service():
    """Test traffic service endpoints"""
    print("🚦 Testing Traffic Service...")
    service = TrafficService()
    
    try:
        # Test current conditions
        conditions = await service.get_current_conditions()
        print(f"✅ Current conditions: {len(conditions)} locations")
        
        # Test with location filter
        filtered = await service.get_current_conditions(location="Central Park")
        print(f"✅ Filtered conditions: {len(filtered)} locations")
        
        # Test analytics
        analytics = await service.get_analytics_summary("24h")
        print(f"✅ Analytics: {analytics.total_vehicles} vehicles, {analytics.average_speed} mph avg")
        
        # Test performance metrics
        metrics = await service.get_performance_metrics("congestion")
        print(f"✅ Performance metrics: {metrics}")
        
        return True
    except Exception as e:
        print(f"❌ Traffic service error: {e}")
        return False


async def test_prediction_service():
    """Test traffic prediction service"""
    print("🔮 Testing Prediction Service...")
    predictor = TrafficPredictor()
    
    try:
        # Test predictions
        predictions = await predictor.predict("Central Park", 3)
        print(f"✅ Predictions: {len(predictions)} forecasts")
        
        # Test model info
        model_info = predictor.get_model_info()
        print(f"✅ Model info: {model_info['model_type']} v{model_info['version']}")
        
        return True
    except Exception as e:
        print(f"❌ Prediction service error: {e}")
        return False


async def test_route_optimization():
    """Test route optimization service"""
    print("🛣️  Testing Route Optimization...")
    optimizer = RouteOptimizer()
    
    try:
        # Create test route request
        origin = Location(latitude=40.7831, longitude=-73.9712, address="Central Park, NY")
        destination = Location(latitude=40.7505, longitude=-73.9934, address="Times Square, NY")
        
        route_request = RouteRequest(
            origin=origin,
            destination=destination,
            departure_time=datetime.now()
        )
        
        # Test route optimization
        route_response = await optimizer.optimize(route_request)
        print(f"✅ Route optimization: {route_response.primary_route.total_distance:.1f} miles, {route_response.primary_route.total_time} min")
        print(f"✅ Alternative routes: {len(route_response.alternative_routes)}")
        
        # Test alternatives
        alternatives = await optimizer.get_alternatives("Central Park", "Times Square", 2)
        print(f"✅ Route alternatives: {len(alternatives)}")
        
        return True
    except Exception as e:
        print(f"❌ Route optimization error: {e}")
        return False


async def test_incident_detection():
    """Test incident detection service"""
    print("🚨 Testing Incident Detection...")
    detector = IncidentDetector()
    
    try:
        # Test getting active incidents
        incidents = await detector.get_active_incidents()
        print(f"✅ Active incidents: {len(incidents)}")
        
        # Test reporting an incident
        test_incident = IncidentReport(
            type=IncidentType.ACCIDENT,
            location=Location(latitude=40.7831, longitude=-73.9712, address="Test Location"),
            severity=TrafficSeverity.MODERATE,
            description="Test incident for API verification"
        )
        
        reported = await detector.report_incident(test_incident)
        print(f"✅ Incident reported: {reported.id}")
        
        return True
    except Exception as e:
        print(f"❌ Incident detection error: {e}")
        return False


async def test_data_generation():
    """Test mock data generation"""
    print("📊 Testing Data Generation...")
    
    try:
        from data.mock_data_generator import MockDataGenerator
        generator = MockDataGenerator()
        
        # Test current conditions
        conditions = generator.generate_current_conditions()
        print(f"✅ Generated conditions: {len(conditions)} sensors")
        
        # Test incidents
        incidents = generator.generate_incidents()
        print(f"✅ Generated incidents: {len(incidents)}")
        
        # Test analytics
        analytics = generator.generate_analytics_summary("24h")
        print(f"✅ Generated analytics: {analytics['total_vehicles']} vehicles")
        
        # Test predictions
        predictions = generator.generate_traffic_predictions("Central Park", 3)
        print(f"✅ Generated predictions: {len(predictions)} forecasts")
        
        # Test route data
        origin = Location(latitude=40.7831, longitude=-73.9712, address="Central Park")
        destination = Location(latitude=40.7505, longitude=-73.9934, address="Times Square")
        route_data = generator.generate_route_data(origin, destination)
        print(f"✅ Generated route: {route_data['total_distance']:.1f} miles, {route_data['total_time']} min")
        
        return True
    except Exception as e:
        print(f"❌ Data generation error: {e}")
        return False


async def test_configuration():
    """Test configuration loading"""
    print("⚙️  Testing Configuration...")
    
    try:
        from core.config import get_settings
        settings = get_settings()
        
        print(f"✅ App name: {settings.app.name}")
        print(f"✅ Database host: {settings.database.postgres.host}")
        print(f"✅ API port: {settings.app.port}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("🏁 Starting Urbanclear API Tests\n")
    
    tests = [
        ("Configuration", test_configuration),
        ("Data Generation", test_data_generation),
        ("Traffic Service", test_traffic_service),
        ("Prediction Service", test_prediction_service),
        ("Route Optimization", test_route_optimization),
        ("Incident Detection", test_incident_detection),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
        print(f"{'='*50}")
    
    # Summary
    print(f"\n🏆 TEST SUMMARY")
    print(f"{'='*50}")
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    print(f"{'='*50}")
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1) 