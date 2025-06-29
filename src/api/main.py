"""
Urbanclear - Smart City Traffic Optimization System - Main API
"""
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from loguru import logger

from src.api.models import (
    TrafficCondition, TrafficPrediction, RouteRequest, RouteResponse,
    IncidentReport, AnalyticsSummary, SignalOptimizationRequest
)
from src.api.dependencies import get_db, get_cache, get_current_user
from src.data.traffic_service import TrafficService
from src.models.prediction import TrafficPredictor
from src.models.optimization import RouteOptimizer
from src.models.incident_detection import IncidentDetector

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
        conditions = await traffic_service.get_current_conditions(
            location=location,
            radius=radius
        )
        return conditions
    except Exception as e:
        logger.error(f"Error getting current traffic: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/traffic/predict", response_model=List[TrafficPrediction])
async def predict_traffic(
    location: str = Query(..., description="Location for prediction"),
    hours_ahead: int = Query(1, ge=1, le=24, description="Hours to predict ahead"),
    db=Depends(get_db)
):
    """Get traffic predictions"""
    try:
        predictions = await traffic_predictor.predict(
            location=location,
            hours_ahead=hours_ahead
        )
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/traffic/historical")
async def get_historical_traffic(
    location: str = Query(..., description="Location"),
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    db=Depends(get_db)
):
    """Get historical traffic data"""
    try:
        data = await traffic_service.get_historical_data(
            location=location,
            start_date=start_date,
            end_date=end_date
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route Optimization Endpoints
@app.post("/api/v1/routes/optimize", response_model=RouteResponse)
async def optimize_route(
    route_request: RouteRequest,
    db=Depends(get_db)
):
    """Optimize route based on current traffic conditions"""
    try:
        optimized_route = await route_optimizer.optimize(route_request)
        return optimized_route
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/routes/alternatives")
async def get_route_alternatives(
    origin: str = Query(..., description="Origin location"),
    destination: str = Query(..., description="Destination location"),
    max_alternatives: int = Query(3, ge=1, le=5, description="Max alternatives"),
    db=Depends(get_db)
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
        raise HTTPException(status_code=500, detail=str(e))

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
        summary = await traffic_service.get_analytics_summary(period)
        return summary
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/performance")
async def get_performance_metrics(
    metric_type: str = Query("congestion", description="Type of metric"),
    location: Optional[str] = Query(None, description="Filter by location"),
    db=Depends(get_db)
):
    """Get system performance metrics"""
    try:
        metrics = await traffic_service.get_performance_metrics(
            metric_type=metric_type,
            location=location
        )
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

# Demo endpoints for showcasing functionality
@app.get("/api/v1/demo/rush-hour-simulation")
async def simulate_rush_hour():
    """Simulate rush hour traffic conditions"""
    try:
        from src.data.mock_data_generator import MockDataGenerator
        import datetime
        
        # Create a new generator for simulation
        demo_generator = MockDataGenerator()
        
        # Override time to simulate morning rush hour (8 AM)
        original_time = datetime.datetime.now
        datetime.datetime.now = lambda: original_time().replace(hour=8, minute=30)
        
        conditions = demo_generator.generate_current_conditions()
        incidents = demo_generator.generate_incidents()
        
        # Reset time
        datetime.datetime.now = original_time
        
        return {
            "scenario": "Morning Rush Hour (8:30 AM)",
            "traffic_conditions": conditions,
            "active_incidents": incidents,
            "summary": {
                "total_sensors": len(conditions),
                "avg_speed": sum(c.speed_mph for c in conditions) / len(conditions),
                "high_congestion_areas": [c.location.address for c in conditions if c.congestion_level > 0.7],
                "total_incidents": len(incidents)
            }
        }
    except Exception as e:
        logger.error(f"Error simulating rush hour: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/demo/location-filter")
async def demo_location_filter():
    """Demo filtering traffic data by location"""
    try:
        # Show different location filters
        all_traffic = await traffic_service.get_current_conditions()
        central_park = await traffic_service.get_current_conditions(location="Central Park")
        broadway = await traffic_service.get_current_conditions(location="Broadway")
        
        return {
            "demo": "Location Filtering",
            "results": {
                "all_locations": {
                    "count": len(all_traffic),
                    "locations": [t.location.address for t in all_traffic]
                },
                "central_park_area": {
                    "count": len(central_park),
                    "locations": [t.location.address for t in central_park]
                },
                "broadway_area": {
                    "count": len(broadway),
                    "locations": [t.location.address for t in broadway]
                }
            }
        }
    except Exception as e:
        logger.error(f"Error in location filter demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/demo/analytics-comparison")
async def demo_analytics_comparison():
    """Demo analytics for different time periods"""
    try:
        analytics_1h = await traffic_service.get_analytics_summary("1h")
        analytics_24h = await traffic_service.get_analytics_summary("24h")
        analytics_7d = await traffic_service.get_analytics_summary("7d")
        
        return {
            "demo": "Analytics Period Comparison",
            "comparison": {
                "1_hour": {
                    "vehicles": analytics_1h.total_vehicles,
                    "avg_speed": analytics_1h.average_speed,
                    "efficiency": analytics_1h.system_efficiency
                },
                "24_hours": {
                    "vehicles": analytics_24h.total_vehicles,
                    "avg_speed": analytics_24h.average_speed,
                    "efficiency": analytics_24h.system_efficiency
                },
                "7_days": {
                    "vehicles": analytics_7d.total_vehicles,
                    "avg_speed": analytics_7d.average_speed,
                    "efficiency": analytics_7d.system_efficiency
                }
            },
            "insights": {
                "daily_vehicle_growth": analytics_24h.total_vehicles / analytics_1h.total_vehicles,
                "weekly_efficiency_trend": f"{((analytics_7d.system_efficiency - analytics_1h.system_efficiency) * 100):+.1f}%"
            }
        }
    except Exception as e:
        logger.error(f"Error in analytics comparison demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    ) 