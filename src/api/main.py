"""
Urbanclear - Smart City Traffic Optimization System - Main API
"""
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
import random

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from pydantic import BaseModel, Field
import uvicorn
from loguru import logger

from api.models import (
    TrafficCondition, TrafficPrediction, RouteRequest, RouteResponse,
    IncidentReport, AnalyticsSummary, SignalOptimizationRequest
)
from api.dependencies import get_db, get_cache, get_current_user
from data.traffic_service import TrafficService
from models.prediction import TrafficPredictor
from models.optimization import RouteOptimizer
from models.incident_detection import IncidentDetector

# Initialize FastAPI app
app = FastAPI(
    title="Urbanclear API",
    description="AI-powered traffic management system for smart cities",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics setup
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# Custom metrics
TRAFFIC_REQUESTS_TOTAL = Counter('traffic_requests_total', 'Total traffic API requests', ['endpoint', 'method'])
TRAFFIC_PROCESSING_TIME = Histogram('traffic_processing_seconds', 'Time spent processing traffic requests', ['endpoint'])
ACTIVE_INCIDENTS = Gauge('active_incidents_total', 'Number of active traffic incidents', ['severity'])
TRAFFIC_FLOW_RATE = Gauge('traffic_flow_rate', 'Current traffic flow rate', ['location', 'direction'])
ROUTE_OPTIMIZATION_TIME = Histogram('route_optimization_seconds', 'Time spent optimizing routes')
SIGNAL_OPTIMIZATION_COUNT = Counter('signal_optimization_total', 'Total signal optimizations performed')
PREDICTION_ACCURACY = Gauge('prediction_accuracy', 'Current prediction model accuracy', ['model_type'])

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

# Initialize services
traffic_service = TrafficService()
traffic_predictor = TrafficPredictor()
route_optimizer = RouteOptimizer()
incident_detector = IncidentDetector()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Urbanclear - Smart City Traffic Optimization System",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "operational",
            "database": "connected",
            "cache": "connected",
            "ml_models": "loaded"
        }
    }

# Traffic Data Endpoints
@app.get("/api/v1/traffic/current", response_model=List[TrafficCondition])
async def get_current_traffic(
    location: Optional[str] = Query(None, description="Filter by location"),
    radius: Optional[float] = Query(None, description="Search radius in km")
):
    """Get current traffic conditions"""
    try:
        TRAFFIC_REQUESTS_TOTAL.labels(endpoint="current", method="GET").inc()
        with TRAFFIC_PROCESSING_TIME.labels(endpoint="current").time():
            conditions = await traffic_service.get_current_conditions(
                location=location,
                radius=radius
            )
            logger.info(f"Retrieved {len(conditions)} traffic conditions")
            return conditions
    except Exception as e:
        logger.error(f"Error getting current traffic: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve traffic data: {str(e)}")

@app.get("/api/v1/traffic/predict", response_model=List[TrafficPrediction])
async def predict_traffic(
    location: str = Query(..., description="Location for prediction"),
    hours_ahead: int = Query(1, ge=1, le=24, description="Hours to predict ahead")
):
    """Get traffic predictions"""
    try:
        TRAFFIC_REQUESTS_TOTAL.labels(endpoint="predict", method="GET").inc()
        with TRAFFIC_PROCESSING_TIME.labels(endpoint="predict").time():
            predictions = await traffic_predictor.predict(
                location=location,
                hours_ahead=hours_ahead
            )
            logger.info(f"Generated {len(predictions)} predictions for {location}")
            return predictions
    except Exception as e:
        logger.error(f"Error predicting traffic: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate predictions: {str(e)}")

@app.get("/api/v1/traffic/historical")
async def get_historical_traffic(
    location: str = Query(..., description="Location"),
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date")
):
    """Get historical traffic data"""
    try:
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        data = await traffic_service.get_historical_data(
            location=location,
            start_date=start_date,
            end_date=end_date
        )
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve historical data: {str(e)}")

# Route Optimization Endpoints
@app.post("/api/v1/routes/optimize", response_model=RouteResponse)
async def optimize_route(
    route_request: RouteRequest
):
    """Optimize route based on current traffic conditions"""
    try:
        ROUTE_OPTIMIZATION_TIME.observe(0.5)  # Mock timing
        optimized_route = await route_optimizer.optimize(route_request)
        logger.info(f"Optimized route from {route_request.origin.address} to {route_request.destination.address}")
        return optimized_route
    except Exception as e:
        logger.error(f"Error optimizing route: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize route: {str(e)}")

@app.get("/api/v1/routes/alternatives")
async def get_route_alternatives(
    origin: str = Query(..., description="Origin location"),
    destination: str = Query(..., description="Destination location"),
    max_alternatives: int = Query(3, ge=1, le=5, description="Max alternatives")
):
    """Get alternative routes"""
    try:
        alternatives = await route_optimizer.get_alternatives(
            origin=origin,
            destination=destination,
            max_alternatives=max_alternatives
        )
        return alternatives
    except Exception as e:
        logger.error(f"Error getting route alternatives: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alternatives: {str(e)}")

# Incident Management Endpoints
@app.get("/api/v1/incidents/active", response_model=List[IncidentReport])
async def get_active_incidents(
    location: Optional[str] = Query(None, description="Filter by location"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db=Depends(get_db)
):
    """Get active traffic incidents"""
    try:
        incidents = await incident_detector.get_active_incidents(
            location=location,
            severity=severity
        )
        return incidents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/incidents/report")
async def report_incident(
    incident: IncidentReport,
    db=Depends(get_db)
):
    """Report a new traffic incident"""
    try:
        result = await incident_detector.report_incident(incident)
        return {"status": "success", "incident_id": result.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    db=Depends(get_db)
):
    """Resolve a traffic incident"""
    try:
        await incident_detector.resolve_incident(incident_id)
        return {"status": "resolved", "incident_id": incident_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Signal Optimization Endpoints
@app.post("/api/v1/signals/optimize")
async def optimize_signals(
    request: SignalOptimizationRequest,
    db=Depends(get_db)
):
    """Optimize traffic signal timing"""
    try:
        optimization = await traffic_service.optimize_signals(request)
        return optimization
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/signals/status")
async def get_signal_status(
    intersection_id: Optional[str] = Query(None, description="Specific intersection"),
    db=Depends(get_db)
):
    """Get traffic signal status"""
    try:
        status = await traffic_service.get_signal_status(intersection_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints
@app.get("/api/v1/analytics/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    period: str = Query("24h", description="Time period (1h, 24h, 7d, 30d)")
):
    """Get traffic analytics summary"""
    try:
        valid_periods = ["1h", "24h", "7d", "30d"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
            )
        
        TRAFFIC_REQUESTS_TOTAL.labels(endpoint="analytics", method="GET").inc()
        with TRAFFIC_PROCESSING_TIME.labels(endpoint="analytics").time():
            summary = await traffic_service.get_analytics_summary(period)
            logger.info(f"Generated analytics summary for period: {period}")
            return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate analytics: {str(e)}")

@app.get("/api/v1/analytics/performance")
async def get_performance_metrics(
    metric_type: str = Query("congestion", description="Type of metric"),
    location: Optional[str] = Query(None, description="Filter by location")
):
    """Get system performance metrics"""
    try:
        valid_metrics = ["congestion", "throughput", "emissions", "efficiency"]
        if metric_type not in valid_metrics:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric type. Must be one of: {', '.join(valid_metrics)}"
            )
        
        metrics = await traffic_service.get_performance_metrics(
            metric_type=metric_type,
            location=location
        )
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")

# System Administration Endpoints
@app.post("/api/v1/admin/models/retrain")
async def retrain_models(
    model_type: str = Query(..., description="Type of model to retrain"),
    # user=Depends(get_current_user)  # Uncomment when authentication is enabled
):
    """Retrain ML models"""
    try:
        if model_type == "traffic_prediction":
            result = await traffic_predictor.retrain()
        elif model_type == "incident_detection":
            result = await incident_detector.retrain()
        else:
            raise HTTPException(status_code=400, detail="Invalid model type")
        
        return {"status": "success", "message": f"{model_type} model retrained", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/admin/system/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        stats = await traffic_service.get_system_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates (placeholder)
@app.websocket("/ws/traffic")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time traffic updates"""
    # Implementation for real-time traffic data streaming
    pass

# Demo Endpoints for Testing
@app.get("/api/v1/demo/rush-hour-simulation")
async def simulate_rush_hour():
    """Simulate rush hour traffic conditions"""
    try:
        logger.info("Generating rush hour simulation data")
        
        # Generate data for multiple locations during rush hour
        rush_hour_data = {
            "scenario": "Rush Hour Simulation",
            "time_period": "8:00 AM - 9:00 AM",
            "locations": []
        }
        
        # Use mock generator for realistic data
        conditions = await traffic_service.get_current_conditions()
        
        for condition in conditions[:5]:  # Limit to 5 locations for demo
            # Simulate rush hour impact
            rush_condition = {
                "location": condition.location.address,
                "coordinates": {
                    "lat": condition.location.latitude,
                    "lng": condition.location.longitude
                },
                "normal_speed": condition.speed_mph * 1.5,  # What speed would be normally
                "rush_hour_speed": condition.speed_mph,
                "congestion_increase": "40-60%",
                "estimated_delay": f"{random.randint(5, 15)} minutes",
                "volume": condition.volume,
                "severity": condition.severity
            }
            rush_hour_data["locations"].append(rush_condition)
        
        rush_hour_data["summary"] = {
            "total_locations_monitored": len(rush_hour_data["locations"]),
            "average_speed_reduction": "35%",
            "total_estimated_delays": f"{sum(random.randint(5, 15) for _ in rush_hour_data['locations'])} minutes",
            "most_congested": max(rush_hour_data["locations"], key=lambda x: x["volume"])["location"]
        }
        
        return rush_hour_data
        
    except Exception as e:
        logger.error(f"Error generating rush hour simulation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate simulation: {str(e)}")

@app.get("/api/v1/demo/location-filter")
async def demo_location_filter():
    """Demo traffic data filtering by location"""
    try:
        logger.info("Demonstrating location-based filtering")
        
        # Show traffic data for different location filters
        demo_data = {
            "demonstration": "Location-Based Traffic Filtering",
            "filters_tested": []
        }
        
        test_filters = ["Central Park", "Times Square", "Bridge", "Tunnel"]
        
        for filter_term in test_filters:
            filtered_conditions = await traffic_service.get_current_conditions(location=filter_term)
            
            filter_result = {
                "filter": filter_term,
                "matches_found": len(filtered_conditions),
                "locations": [
                    {
                        "name": condition.location.address,
                        "speed": condition.speed_mph,
                        "congestion": condition.congestion_level
                    }
                    for condition in filtered_conditions
                ]
            }
            demo_data["filters_tested"].append(filter_result)
        
        return demo_data
        
    except Exception as e:
        logger.error(f"Error in location filter demo: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run demo: {str(e)}")

@app.get("/api/v1/demo/analytics-comparison")
async def demo_analytics_comparison():
    """Demo analytics data for different time periods"""
    try:
        logger.info("Generating analytics comparison demo")
        
        # Generate analytics for multiple time periods
        periods = ["1h", "24h", "7d", "30d"]
        comparison_data = {
            "demonstration": "Traffic Analytics Comparison",
            "time_periods": []
        }
        
        for period in periods:
            summary = await traffic_service.get_analytics_summary(period)
            
            period_data = {
                "period": period,
                "total_vehicles": summary.total_vehicles,
                "average_speed": summary.average_speed,
                "incidents": summary.congestion_incidents,
                "efficiency": summary.system_efficiency,
                "fuel_savings": summary.fuel_savings,
                "emission_reduction": summary.emission_reduction
            }
            comparison_data["time_periods"].append(period_data)
        
        # Add insights
        comparison_data["insights"] = {
            "peak_efficiency_period": max(comparison_data["time_periods"], 
                                        key=lambda x: x["efficiency"])["period"],
            "highest_traffic_period": max(comparison_data["time_periods"], 
                                        key=lambda x: x["total_vehicles"])["period"],
            "best_fuel_savings": max(comparison_data["time_periods"], 
                                   key=lambda x: x["fuel_savings"])["fuel_savings"]
        }
        
        return comparison_data
        
    except Exception as e:
        logger.error(f"Error in analytics comparison demo: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run demo: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    ) 