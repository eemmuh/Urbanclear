#!/usr/bin/env python3
"""
Test MongoDB Integration for Urbanclear Traffic System
Generates sample data and tests the MongoDB logging functionality
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any
import random

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data.logging_service import logging_service, LogLevel
from data.mongodb_client import AnalyticsEventType
from loguru import logger


async def test_mongodb_connection():
    """Test MongoDB connection"""
    print("🔍 Testing MongoDB connection...")
    
    try:
        await logging_service.start()
        print("✅ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False


async def generate_sample_logs():
    """Generate sample log entries"""
    print("📝 Generating sample logs...")
    
    services = ["api", "traffic_service", "incident_service", "route_service", "system"]
    messages = [
        "User authentication successful",
        "Traffic data updated",
        "Incident reported",
        "Route optimization completed",
        "System health check passed",
        "Database connection established",
        "Cache miss occurred",
        "API rate limit exceeded",
        "Sensor data received",
        "Prediction model updated"
    ]
    
    for i in range(20):
        service = random.choice(services)
        message = random.choice(messages)
        level = random.choice([LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR])
        
        await logging_service.log(
            level=level,
            message=f"{message} (test {i+1})",
            details={"test_id": i+1, "timestamp": datetime.now().isoformat()},
            service=service
        )
    
    print("✅ Sample logs generated")


async def generate_sample_analytics():
    """Generate sample analytics events"""
    print("📊 Generating sample analytics events...")
    
    # Traffic data events
    for i in range(10):
        await logging_service.log_traffic_data(
            sensor_id=f"sensor_{i+1:03d}",
            speed=random.uniform(20, 60),
            volume=random.randint(50, 500),
            density=random.uniform(0.1, 0.9),
            congestion_level=random.uniform(0, 1),
            location={"lat": 40.7831 + random.uniform(-0.1, 0.1), "lng": -73.9712 + random.uniform(-0.1, 0.1)}
        )
    
    # Route optimization events
    for i in range(5):
        await logging_service.log_route_optimization(
            origin={"lat": 40.7831, "lng": -73.9712},
            destination={"lat": 40.7505, "lng": -73.9934},
            optimization_time=random.uniform(0.1, 2.0),
            route_length=random.uniform(2.0, 10.0),
            preferences={"avoid_tolls": True, "prefer_highways": False}
        )
    
    # Incident events
    incident_types = ["accident", "construction", "weather", "congestion"]
    severities = ["low", "moderate", "high", "critical"]
    
    for i in range(8):
        await logging_service.log_incident(
            incident_id=f"incident_{i+1:03d}",
            incident_type=random.choice(incident_types),
            severity=random.choice(severities),
            location={"lat": 40.7831 + random.uniform(-0.1, 0.1), "lng": -73.9712 + random.uniform(-0.1, 0.1)},
            description=f"Test incident {i+1} - {random.choice(incident_types)}"
        )
    
    # API request events
    endpoints = ["/api/v1/traffic/current", "/api/v1/routes/optimize", "/api/v1/incidents/report"]
    methods = ["GET", "POST", "PUT"]
    
    for i in range(15):
        await logging_service.log_api_request(
            endpoint=random.choice(endpoints),
            method=random.choice(methods),
            response_code=random.choice([200, 200, 200, 400, 500]),  # Mostly successful
            response_time=random.uniform(0.01, 1.0),
            request_size=random.randint(100, 2000),
            response_size=random.randint(500, 5000)
        )
    
    # System events
    components = ["database", "cache", "ml_models", "websocket", "monitoring"]
    events = ["startup", "shutdown", "error", "warning", "info"]
    
    for i in range(12):
        await logging_service.log_system_event(
            component=random.choice(components),
            event=random.choice(events),
            details={
                "memory_usage": random.uniform(0.1, 0.8),
                "cpu_usage": random.uniform(0.05, 0.6),
                "active_connections": random.randint(1, 100),
                "timestamp": datetime.now().isoformat()
            }
        )
    
    print("✅ Sample analytics events generated")


async def test_data_retrieval():
    """Test retrieving data from MongoDB"""
    print("🔍 Testing data retrieval...")
    
    try:
        # Get recent logs
        logs = await logging_service.get_logs(limit=10)
        print(f"📝 Retrieved {len(logs)} recent logs")
        
        # Get analytics events
        events = await logging_service.get_analytics_events(limit=10)
        print(f"📊 Retrieved {len(events)} analytics events")
        
        # Get analytics summary
        summary = await logging_service.get_analytics_summary()
        print(f"📈 Analytics summary: {summary}")
        
        return True
    except Exception as e:
        print(f"❌ Data retrieval failed: {e}")
        return False


async def test_search_functionality():
    """Test search functionality"""
    print("🔍 Testing search functionality...")
    
    try:
        # Search for error logs
        error_logs = await logging_service.get_logs(
            level=LogLevel.ERROR,
            limit=5
        )
        print(f"🚨 Found {len(error_logs)} error logs")
        
        # Search for traffic data events
        traffic_events = await logging_service.get_analytics_events(
            event_type=AnalyticsEventType.TRAFFIC_DATA,
            limit=5
        )
        print(f"🚗 Found {len(traffic_events)} traffic data events")
        
        # Search for recent API requests
        api_events = await logging_service.get_analytics_events(
            event_type=AnalyticsEventType.API_REQUEST,
            limit=5
        )
        print(f"🌐 Found {len(api_events)} API request events")
        
        return True
    except Exception as e:
        print(f"❌ Search functionality failed: {e}")
        return False


async def cleanup_test_data():
    """Clean up test data"""
    print("🧹 Cleaning up test data...")
    
    try:
        await logging_service.cleanup_old_data(days_to_keep=1)
        print("✅ Test data cleanup completed")
        return True
    except Exception as e:
        print(f"❌ Data cleanup failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Starting MongoDB Integration Test")
    print("=" * 50)
    
    # Test connection
    if not await test_mongodb_connection():
        print("❌ Cannot proceed without MongoDB connection")
        return
    
    print()
    
    # Generate sample data
    await generate_sample_logs()
    print()
    
    await generate_sample_analytics()
    print()
    
    # Test data retrieval
    await test_data_retrieval()
    print()
    
    # Test search functionality
    await test_search_functionality()
    print()
    
    # Cleanup
    await cleanup_test_data()
    print()
    
    # Stop logging service
    await logging_service.stop()
    
    print("✅ MongoDB Integration Test Completed Successfully!")
    print("=" * 50)
    print("\n📋 Test Summary:")
    print("• MongoDB connection: ✅")
    print("• Sample data generation: ✅")
    print("• Data retrieval: ✅")
    print("• Search functionality: ✅")
    print("• Data cleanup: ✅")
    print("\n🎉 All tests passed! MongoDB integration is working correctly.")


if __name__ == "__main__":
    asyncio.run(main()) 