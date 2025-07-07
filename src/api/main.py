"""
Urbanclear - Smart City Traffic Optimization System - Main API
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional
import random
import asyncio
import uuid

from fastapi import FastAPI, HTTPException, Depends, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import uvicorn
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import (
    TrafficCondition,
    IncidentReport,
    AnalyticsSummary,
    SignalOptimizationRequest,
    PredictionResponse,
    RouteOptimizationRequest,
    RouteOptimizationResponse,
    AnalyticsResponse
)
from api.dependencies import (
    get_db_session
)
from data.traffic_service import TrafficService
from models.prediction import TrafficPredictor
from models.optimization import RouteOptimizer
from models.incident_detection import IncidentDetector
from api.websocket_handler import (
    websocket_endpoint,
    start_background_streaming,
    manager,
)

# Initialize FastAPI app
app = FastAPI(
    title="Urbanclear API",
    description="AI-powered traffic management system for smart cities",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
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
TRAFFIC_REQUESTS_TOTAL = Counter(
    "traffic_requests_total", "Total traffic API requests", ["endpoint", "method"]
)
TRAFFIC_PROCESSING_TIME = Histogram(
    "traffic_processing_seconds", "Time spent processing traffic requests", ["endpoint"]
)
ACTIVE_INCIDENTS = Gauge(
    "active_incidents_total", "Number of active traffic incidents", ["severity"]
)
TRAFFIC_FLOW_RATE = Gauge(
    "traffic_flow_rate", "Current traffic flow rate", ["location", "direction"]
)
ROUTE_OPTIMIZATION_TIME = Histogram(
    "route_optimization_seconds", "Time spent optimizing routes"
)
SIGNAL_OPTIMIZATION_COUNT = Counter(
    "signal_optimization_total", "Total signal optimizations performed"
)
PREDICTION_ACCURACY = Gauge(
    "prediction_accuracy", "Current prediction model accuracy", ["model_type"]
)


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
        "status": "operational",
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
            "ml_models": "loaded",
        },
    }


# Traffic Data Endpoints
@app.get("/api/v1/traffic/current", response_model=List[TrafficCondition])
async def get_current_traffic(
    location: Optional[str] = Query(None, description="Filter by location"),
    radius: Optional[float] = Query(None, description="Search radius in km"),
):
    """Get current traffic conditions"""
    try:
        TRAFFIC_REQUESTS_TOTAL.labels(endpoint="current", method="GET").inc()
        with TRAFFIC_PROCESSING_TIME.labels(endpoint="current").time():
            conditions = await traffic_service.get_current_conditions(
                location=location, radius=radius
            )
            logger.info(f"Retrieved {len(conditions)} traffic conditions")
            return conditions
    except Exception as e:
        logger.error(f"Error getting current traffic: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve traffic data: {str(e)}"
        )


@app.get("/api/v1/traffic/predict")
async def predict_traffic(
    location: str = Query(..., description="Location for prediction"),
    hours_ahead: int = Query(1, ge=1, le=24, description="Hours ahead"),
    db: AsyncSession = Depends(get_db_session)
) -> PredictionResponse:
    """Get traffic predictions for a specific location"""
    try:
        TRAFFIC_REQUESTS_TOTAL.labels(endpoint="predict", method="GET").inc()
        with TRAFFIC_PROCESSING_TIME.labels(endpoint="predict").time():
            predictions = await traffic_predictor.predict(
                location=location, hours_ahead=hours_ahead
            )
            logger.info(f"Generated {len(predictions)} predictions for {location}")
            return PredictionResponse(predictions=predictions)
    except Exception as e:
        logger.error(f"Error predicting traffic: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate predictions: {str(e)}"
        )


@app.get("/api/v1/traffic/historical")
async def get_historical_traffic(
    location: str = Query(..., description="Location"),
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
):
    """Get historical traffic data"""
    try:
        if start_date >= end_date:
            raise HTTPException(
                status_code=400, detail="Start date must be before end date"
            )

        data = await traffic_service.get_historical_data(
            location=location, start_date=start_date, end_date=end_date
        )
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve historical data: {str(e)}"
        )


# Route Optimization Endpoints
@app.post("/api/v1/routes/optimize")
async def optimize_route(
    request: RouteOptimizationRequest,
    db: AsyncSession = Depends(get_db_session)
) -> RouteOptimizationResponse:
    """Optimize a route based on current traffic conditions"""
    try:
        ROUTE_OPTIMIZATION_TIME.observe(0.5)  # Mock timing
        optimized_route = await route_optimizer.optimize(request)
        logger.info(
            f"Optimized route from {request.origin.address} to {request.destination.address}"
        )
        return optimized_route
    except Exception as e:
        logger.error(f"Error optimizing route: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to optimize route: {str(e)}"
        )


@app.get("/api/v1/routes/alternatives")
async def get_route_alternatives(
    origin: str = Query(..., description="Origin location"),
    destination: str = Query(..., description="Destination location"),
    max_alternatives: int = Query(3, ge=1, le=5, description="Max alternatives"),
):
    """Get alternative routes"""
    try:
        alternatives = await route_optimizer.get_alternatives(
            origin=origin, destination=destination, max_alternatives=max_alternatives
        )
        return alternatives
    except Exception as e:
        logger.error(f"Error getting route alternatives: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get alternatives: {str(e)}"
        )


# Incident Management Endpoints
@app.get("/api/v1/incidents/active", response_model=List[IncidentReport])
async def get_active_incidents(
    location: Optional[str] = Query(None, description="Filter by location"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db=Depends(get_db_session),
):
    """Get active traffic incidents"""
    try:
        incidents = await incident_detector.get_active_incidents(
            location=location, severity=severity
        )
        return incidents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/incidents/report")
async def report_incident(incident: IncidentReport, db=Depends(get_db_session)):
    """Report a new traffic incident"""
    try:
        result = await incident_detector.report_incident(incident)
        return {"status": "success", "incident_id": result.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str, db=Depends(get_db_session)):
    """Resolve a traffic incident"""
    try:
        await incident_detector.resolve_incident(incident_id)
        return {"status": "resolved", "incident_id": incident_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Signal Optimization Endpoints
@app.post("/api/v1/signals/optimize")
async def optimize_signals(request: SignalOptimizationRequest, db=Depends(get_db_session)):
    """Optimize traffic signal timing"""
    try:
        optimization = await traffic_service.optimize_signals(request)
        return optimization
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/signals/status")
async def get_signal_status(
    intersection_id: Optional[str] = Query(None, description="Specific intersection"),
    db=Depends(get_db_session),
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
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}",
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
        raise HTTPException(
            status_code=500, detail=f"Failed to generate analytics: {str(e)}"
        )


@app.get("/api/v1/analytics/performance")
async def get_performance_analytics(
    metric_type: str = Query(..., description="Type of performance metric"),
    db: AsyncSession = Depends(get_db_session)
) -> AnalyticsResponse:
    """Get performance analytics for various metrics"""
    try:
        valid_metrics = ["congestion", "throughput", "emissions", "efficiency"]
        if metric_type not in valid_metrics:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric type. Must be one of: {', '.join(valid_metrics)}",
            )

        metrics = await traffic_service.get_performance_metrics(
            metric_type=metric_type, location=None
        )
        return AnalyticsResponse(metrics=metrics)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve metrics: {str(e)}"
        )


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

        return {
            "status": "success",
            "message": f"{model_type} model retrained",
            "result": result,
        }
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


# WebSocket endpoint for real-time updates
@app.websocket("/ws/traffic/{client_id}")
async def websocket_traffic_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time traffic updates"""
    await websocket_endpoint(websocket, client_id)


@app.websocket("/ws/traffic")
async def websocket_traffic_auto_endpoint(websocket: WebSocket):
    """WebSocket endpoint with auto-generated client ID"""
    client_id = str(uuid.uuid4())
    await websocket_endpoint(websocket, client_id)


@app.on_event("startup")
async def startup_event():
    """Start background services"""
    # Start WebSocket data streaming in background
    asyncio.create_task(start_background_streaming())
    logger.info("Background streaming started")


@app.get("/api/v1/websocket/status")
async def get_websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": len(manager.active_connections),
        "topics": list(manager.subscriptions.keys()) if manager.subscriptions else [],
        "status": "active" if manager.active_connections else "inactive",
    }


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
            "locations": [],
        }

        # Use mock generator for realistic data
        conditions = await traffic_service.get_current_conditions()

        for condition in conditions[:5]:  # Limit to 5 locations for demo
            # Simulate rush hour impact
            rush_condition = {
                "location": condition.location.address,
                "coordinates": {
                    "lat": condition.location.latitude,
                    "lng": condition.location.longitude,
                },
                "normal_speed": condition.speed_mph
                * 1.5,  # What speed would be normally
                "rush_hour_speed": condition.speed_mph,
                "congestion_increase": "40-60%",
                "estimated_delay": f"{random.randint(5, 15)} minutes",
                "volume": condition.volume,
                "severity": condition.severity,
            }
            rush_hour_data["locations"].append(rush_condition)

        rush_hour_data["summary"] = {
            "total_locations_monitored": len(rush_hour_data["locations"]),
            "average_speed_reduction": "35%",
            "total_estimated_delays": f"{sum(random.randint(5, 15) for _ in rush_hour_data['locations'])} minutes",
            "most_congested": (
                max(rush_hour_data["locations"], key=lambda x: x["volume"])["location"]
                if rush_hour_data["locations"]
                else "N/A"
            ),
        }

        return rush_hour_data

    except Exception as e:
        logger.error(f"Error generating rush hour simulation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate simulation: {str(e)}"
        )


@app.get("/api/v1/demo/real-time-dashboard")
async def get_real_time_dashboard():
    """Get comprehensive real-time data for dashboard demonstration"""
    try:
        logger.info("Generating real-time dashboard data")

        # Get real-time data from mock generator
        real_time_data = traffic_service.mock_generator.generate_real_time_data()
        performance_data = traffic_service.mock_generator.generate_performance_data()
        geographic_data = traffic_service.mock_generator.generate_geographic_data()

        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "traffic_data": real_time_data,
            "performance_metrics": performance_data,
            "geographic_overview": geographic_data,
            "system_status": {
                "api_status": "operational",
                "database_status": "connected",
                "ml_models_status": "loaded",
                "real_time_processing": "active",
                "data_quality": "excellent",
            },
        }

        return dashboard_data

    except Exception as e:
        logger.error(f"Error generating dashboard data: {e}")
        return {
            "error": str(e),
            "fallback_data": {
                "timestamp": datetime.now().isoformat(),
                "status": "degraded",
                "message": "Using fallback data due to service error",
            },
        }


@app.get("/api/v1/demo/ml-showcase")
async def ml_showcase():
    """Showcase ML capabilities with sample predictions and optimizations"""
    try:
        logger.info("Generating ML capabilities showcase")

        # Sample predictions for different locations
        sample_locations = ["Central Park", "Times Square", "Brooklyn Bridge"]
        ml_demo = {
            "traffic_predictions": [],
            "route_optimizations": [],
            "incident_detection": {
                "model_accuracy": "94.2%",
                "detection_latency": "< 30 seconds",
                "false_positive_rate": "2.1%",
                "recent_detections": [
                    {
                        "location": "FDR Drive @ 42nd St",
                        "type": "congestion_anomaly",
                        "confidence": 0.89,
                        "detected_at": (
                            datetime.now() - timedelta(minutes=5)
                        ).isoformat(),
                    },
                    {
                        "location": "Lincoln Tunnel Approach",
                        "type": "incident_likely",
                        "confidence": 0.76,
                        "detected_at": (
                            datetime.now() - timedelta(minutes=12)
                        ).isoformat(),
                    },
                ],
            },
            "signal_optimization": {
                "optimized_intersections": 147,
                "average_improvement": "18.5% reduction in wait time",
                "fuel_savings": "2,850 gallons/day",
                "co2_reduction": "28.5 tons/month",
                "recent_optimizations": [
                    {
                        "intersection": "5th Ave & 42nd St",
                        "improvement": "22% wait time reduction",
                        "updated_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                    },
                    {
                        "intersection": "Broadway & Houston",
                        "improvement": "15% throughput increase",
                        "updated_at": (datetime.now() - timedelta(hours=3)).isoformat(),
                    },
                ],
            },
        }

        # Generate predictions for each location
        for location in sample_locations:
            predictions = await traffic_predictor.predict(location, hours_ahead=6)
            prediction_summary = {
                "location": location,
                "predictions": [
                    {
                        "hour": i + 1,
                        "predicted_speed": pred.predicted_speed,
                        "predicted_volume": pred.predicted_volume,
                        "congestion_level": pred.predicted_severity,
                        "confidence": pred.confidence,
                    }
                    for i, pred in enumerate(predictions[:6])
                ],
                "model_info": {
                    "algorithm": "LSTM Neural Network",
                    "accuracy": "87.3%",
                    "last_trained": (datetime.now() - timedelta(days=2)).isoformat(),
                },
            }
            ml_demo["traffic_predictions"].append(prediction_summary)

        # Sample route optimizations
        sample_routes = [
            {"from": "JFK Airport", "to": "Manhattan", "savings": "12 minutes"},
            {"from": "Brooklyn", "to": "Queens", "savings": "8 minutes"},
            {"from": "Bronx", "to": "Staten Island", "savings": "15 minutes"},
        ]

        for route in sample_routes:
            optimization = {
                "route": f"{route['from']} → {route['to']}",
                "original_time": f"{random.randint(35, 65)} minutes",
                "optimized_time": f"{random.randint(25, 45)} minutes",
                "time_savings": route["savings"],
                "fuel_savings": f"{random.randint(2, 8)} gallons",
                "alternative_routes": random.randint(2, 5),
                "traffic_factors": [
                    "current_congestion",
                    "historical_patterns",
                    "incident_data",
                    "weather_conditions",
                ],
            }
            ml_demo["route_optimizations"].append(optimization)

        return ml_demo

    except Exception as e:
        logger.error(f"Error generating ML showcase: {e}")
        return {
            "error": str(e),
            "message": "ML showcase generation failed",
            "fallback": {
                "status": "ML models available",
                "capabilities": [
                    "traffic_prediction",
                    "route_optimization",
                    "incident_detection",
                    "signal_optimization",
                ],
            },
        }


@app.get("/api/v1/demo/performance-metrics")
async def get_performance_metrics_demo():
    """Demonstrate comprehensive system performance metrics"""
    try:
        logger.info("Generating performance metrics demo")

        performance_data = traffic_service.mock_generator.generate_performance_data()

        # Add additional metrics for comprehensive demo
        comprehensive_metrics = {
            **performance_data,
            "ml_performance": {
                "model_inference_time": f"{random.randint(50, 150)}ms",
                "batch_processing_rate": f"{random.randint(1000, 5000)} records/min",
                "prediction_accuracy_7d": f"{random.randint(85, 95)}%",
                "model_drift_score": round(random.uniform(0.1, 0.3), 3),
            },
            "data_pipeline": {
                "ingestion_rate": f"{random.randint(500, 2000)} events/sec",
                "processing_latency": f"{random.randint(100, 500)}ms",
                "data_quality_score": round(random.uniform(0.92, 0.99), 3),
                "storage_utilization": f"{random.randint(45, 75)}%",
            },
            "api_performance": {
                "requests_per_minute": random.randint(500, 2000),
                "p95_response_time": f"{random.randint(150, 300)}ms",
                "error_rate": f"{round(random.uniform(0.1, 2.0), 2)}%",
                "active_connections": random.randint(50, 200),
            },
            "infrastructure": {
                "containers_running": random.randint(8, 15),
                "kubernetes_pods": random.randint(12, 25),
                "load_balancer_requests": random.randint(1000, 5000),
                "cdn_cache_hit_rate": round(random.uniform(0.88, 0.97), 3),
            },
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": comprehensive_metrics,
            "alerts": [
                {
                    "level": "info",
                    "message": "Traffic volume 15% above normal for this time",
                    "metric": "traffic_volume",
                    "threshold": "normal_range",
                },
                {
                    "level": "warning",
                    "message": "API response time slightly elevated",
                    "metric": "api_response_time",
                    "threshold": "200ms",
                },
            ],
            "health_score": round(random.uniform(0.85, 0.98), 3),
        }

    except Exception as e:
        logger.error(f"Error generating performance metrics: {e}")
        return {
            "error": str(e),
            "basic_metrics": {
                "status": "operational",
                "uptime": "99.7%",
                "last_updated": datetime.now().isoformat(),
            },
        }


@app.get("/api/v1/demo/geographic-heatmap")
async def get_geographic_heatmap():
    """Generate geographic traffic heatmap data"""
    try:
        logger.info("Generating geographic heatmap data")

        geographic_data = traffic_service.mock_generator.generate_geographic_data()

        # Add heatmap-specific data
        heatmap_data = {
            **geographic_data,
            "heatmap_points": [],
            "traffic_corridors": [
                {
                    "name": "FDR Drive",
                    "coordinates": [
                        {"lat": 40.7505, "lng": -73.9681, "intensity": 0.8},
                        {"lat": 40.7831, "lng": -73.9442, "intensity": 0.9},
                        {"lat": 40.8176, "lng": -73.9429, "intensity": 0.7},
                    ],
                },
                {
                    "name": "West Side Highway",
                    "coordinates": [
                        {"lat": 40.7047, "lng": -74.0479, "intensity": 0.6},
                        {"lat": 40.7589, "lng": -73.9851, "intensity": 0.8},
                        {"lat": 40.8007, "lng": -73.9626, "intensity": 0.5},
                    ],
                },
            ],
        }

        # Generate heatmap points
        for _ in range(100):  # 100 random traffic intensity points
            heatmap_data["heatmap_points"].append(
                {
                    "lat": round(random.uniform(40.7047, 40.8176), 6),
                    "lng": round(random.uniform(-74.0479, -73.9442), 6),
                    "intensity": round(random.uniform(0.1, 1.0), 2),
                    "volume": random.randint(100, 2000),
                }
            )

        return heatmap_data

    except Exception as e:
        logger.error(f"Error generating geographic heatmap: {e}")
        return {
            "error": str(e),
            "fallback_zones": ["Manhattan", "Brooklyn", "Queens", "Bronx"],
            "message": "Heatmap data generation failed",
        }


@app.get("/api/v1/demo/incident-timeline")
async def get_incident_timeline():
    """Generate incident timeline data for demonstration"""
    try:
        logger.info("Generating incident timeline data")

        # Generate incidents for the last 24 hours
        timeline_data = {
            "period": "24 hours",
            "total_incidents": 0,
            "resolved_incidents": 0,
            "timeline": [],
        }

        # Generate hourly incident data
        for hour in range(24):
            timestamp = datetime.now() - timedelta(hours=23 - hour)

            # More incidents during rush hours
            if hour in [7, 8, 17, 18, 19]:
                incident_count = random.randint(2, 6)
            else:
                incident_count = random.randint(0, 3)

            timeline_data["total_incidents"] += incident_count

            hour_data = {
                "hour": timestamp.strftime("%H:00"),
                "timestamp": timestamp.isoformat(),
                "incidents": incident_count,
                "resolved": random.randint(0, max(1, incident_count - 1)),
                "types": {
                    "accidents": random.randint(0, max(1, incident_count // 2)),
                    "construction": random.randint(0, 1),
                    "breakdowns": random.randint(0, max(1, incident_count // 3)),
                    "other": random.randint(0, 1),
                },
            }

            timeline_data["resolved_incidents"] += hour_data["resolved"]
            timeline_data["timeline"].append(hour_data)

        # Add summary statistics
        timeline_data["resolution_rate"] = round(
            timeline_data["resolved_incidents"]
            / max(1, timeline_data["total_incidents"]),
            2,
        )
        timeline_data["peak_hour"] = max(
            timeline_data["timeline"], key=lambda x: x["incidents"]
        )["hour"]

        return timeline_data

    except Exception as e:
        logger.error(f"Error generating incident timeline: {e}")
        return {
            "error": str(e),
            "period": "24 hours",
            "message": "Timeline generation failed",
        }


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )
