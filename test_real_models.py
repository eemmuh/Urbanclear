#!/usr/bin/env python3
"""
Test script to verify that real trained models are working
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append('src')

from src.models.prediction import TrafficPredictor
from src.models.incident_detection import IncidentDetector
from src.models.optimization import RouteOptimizer
from src.api.models import RouteRequest, Location


async def test_traffic_predictor():
    """Test traffic prediction model"""
    print("🚗 Testing Traffic Predictor...")
    
    predictor = TrafficPredictor()
    
    # Test model loading
    model_loaded = predictor.load_model()
    print(f"   Model loaded: {model_loaded}")
    
    # Test prediction
    try:
        predictions = await predictor.predict("Times Square", hours_ahead=3)
        print(f"   Generated {len(predictions)} predictions")
        
        if predictions:
            first_pred = predictions[0]
            print(f"   First prediction: {first_pred.predicted_flow:.2f} flow, {first_pred.congestion_level:.3f} congestion")
            print(f"   Conditions: {first_pred.conditions}")
            
        # Test model info
        model_info = predictor.get_model_info()
        print(f"   Model type: {model_info['model_type']}")
        print(f"   Is loaded: {model_info['is_loaded']}")
        
        return True
        
    except Exception as e:
        print(f"   Error: {e}")
        return False


async def test_incident_detector():
    """Test incident detection model"""
    print("\n🚨 Testing Incident Detector...")
    
    detector = IncidentDetector()
    
    # Test model loading
    model_loaded = detector.load_models()
    print(f"   Model loaded: {model_loaded}")
    
    # Test incident detection
    try:
        sensor_data = {
            "flow_rate": 800,
            "speed": 15,
            "congestion_level": 0.8,
            "weather_condition": 0.3,
            "latitude": 40.7580,
            "longitude": -73.9855,
            "address": "Times Square"
        }
        
        incidents = await detector.detect_incidents(sensor_data)
        print(f"   Detected {len(incidents)} incidents")
        
        if incidents:
            incident = incidents[0]
            print(f"   Incident type: {incident.type}")
            print(f"   Severity: {incident.severity}")
            print(f"   Description: {incident.description}")
        
        # Test statistics
        stats = detector.get_incident_statistics()
        print(f"   Detection accuracy: {stats['detection_accuracy']:.3f}")
        print(f"   Using real model: {stats['is_using_real_model']}")
        
        return True
        
    except Exception as e:
        print(f"   Error: {e}")
        return False


async def test_route_optimizer():
    """Test route optimization model"""
    print("\n🗺️ Testing Route Optimizer...")
    
    optimizer = RouteOptimizer()
    
    # Test model loading
    model_loaded = optimizer.load_model()
    print(f"   Model loaded: {model_loaded}")
    
    # Test route optimization
    try:
        origin = Location(latitude=40.7580, longitude=-73.9855, address="Times Square")
        destination = Location(latitude=40.7829, longitude=-73.9654, address="Central Park")
        
        route_request = RouteRequest(
            origin=origin,
            destination=destination
        )
        
        response = await optimizer.optimize(route_request)
        print(f"   Optimization time: {response.optimization_time:.3f} seconds")
        print(f"   Total distance: {response.primary_route.total_distance:.2f} km")
        print(f"   Total time: {response.primary_route.total_time:.2f} minutes")
        print(f"   Traffic score: {response.primary_route.traffic_score:.3f}")
        print(f"   Factors considered: {response.factors_considered}")
        
        # Test statistics
        stats = optimizer.get_optimization_stats()
        print(f"   Using real model: {stats['is_using_real_model']}")
        print(f"   Average improvement: {stats['average_improvement']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"   Error: {e}")
        return False


async def test_model_retraining():
    """Test model retraining functionality"""
    print("\n🔄 Testing Model Retraining...")
    
    predictor = TrafficPredictor()
    
    try:
        result = await predictor.retrain()
        print(f"   Retraining status: {result['status']}")
        
        if result['status'] == 'completed':
            print(f"   Algorithm: {result['algorithm']}")
            print(f"   MSE: {result['mse']:.2f}")
            print(f"   MAE: {result['mae']:.2f}")
            print(f"   Training time: {result['training_time']:.2f} seconds")
            print(f"   Samples used: {result['samples_used']}")
        
        return True
        
    except Exception as e:
        print(f"   Error: {e}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Testing Real ML Models Implementation")
    print("=" * 50)
    
    # Check if models exist
    models_dir = Path("models/simple_trained")
    if not models_dir.exists():
        print("❌ Models directory not found. Please run the ML trainer first.")
        print("   Run: python src/models/simple_ml_trainer.py")
        return
    
    # Check individual model files
    required_models = ["traffic_predictor.pkl", "incident_detector.pkl", "route_optimizer.pkl"]
    missing_models = []
    
    for model_file in required_models:
        if not (models_dir / model_file).exists():
            missing_models.append(model_file)
    
    if missing_models:
        print(f"❌ Missing model files: {missing_models}")
        print("   Run: python src/models/simple_ml_trainer.py")
        return
    
    print("✅ All model files found!")
    
    # Run tests
    results = []
    
    results.append(await test_traffic_predictor())
    results.append(await test_incident_detector())
    results.append(await test_route_optimizer())
    results.append(await test_model_retraining())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    tests = [
        "Traffic Predictor",
        "Incident Detector", 
        "Route Optimizer",
        "Model Retraining"
    ]
    
    for i, (test_name, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    total_passed = sum(results)
    print(f"\n🎯 Overall: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("🎉 All tests passed! Real ML models are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main()) 