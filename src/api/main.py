"""
Urbanclear - Smart City Traffic Optimization System - Main API
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional
import random
import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import uvicorn
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
import socketio

from src.api.models import (
    TrafficCondition,
    IncidentReport,
    AnalyticsSummary,
    SignalOptimizationRequest,
    PredictionResponse,
    RouteOptimizationRequest,
    RouteOptimizationResponse,
    AnalyticsResponse,
)
from src.api.dependencies import get_db
from src.data.traffic_service import TrafficService
from src.data.real_data_service import real_data_service
from src.models.prediction import TrafficPredictor
from src.models.optimization import RouteOptimizer
from src.models.incident_detection import IncidentDetector
from src.api.websocket_handler import (
    websocket_endpoint,
    start_background_streaming,
    manager,
)
from src.api.socketio_handler import socketio_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("Starting up Urbanclear API...")
    asyncio.create_task(start_background_streaming())
    asyncio.create_task(socketio_handler.start_data_streaming())
    logger.info("Background streaming started")

    yield

    # Shutdown
    logger.info("Shutting down Urbanclear API...")


# Initialize FastAPI app
app = FastAPI(
    title="Urbanclear API",
    description="AI-powered traffic management system for smart cities",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
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

# Mount Socket.io app
# app = socketio.ASGIApp(socketio_handler.sio, app) # This line is moved to the end

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
    prediction_horizon: int = Query(
        60, ge=0, le=1440, description="Prediction horizon in minutes"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Predict traffic conditions for a specific location and time horizon
    """
    try:
        # Generate predictions using the ML model
        hours_ahead = max(1, prediction_horizon // 60)  # Convert minutes to hours
        predictions = await traffic_predictor.predict(
            location=location, hours_ahead=hours_ahead
        )

        logger.info(f"Generated {len(predictions)} predictions for {location}")

        # Create the response in the expected format
        if predictions:
            first_prediction = predictions[0]
            response_data = {
                "prediction": {
                    "location": location,
                    "predicted_speed": first_prediction.predicted_speed,
                    "predicted_volume": first_prediction.predicted_volume,
                    "predicted_severity": first_prediction.predicted_severity,
                },
                "confidence": first_prediction.confidence,
                "predictions": [
                    pred.model_dump() for pred in predictions
                ],  # Convert to dicts
            }
            return PredictionResponse(**response_data)
        else:
            # Default response if no predictions
            response_data = {
                "prediction": {
                    "location": location,
                    "predicted_speed": 30.0,
                    "predicted_volume": 1000,
                    "predicted_severity": "moderate",
                },
                "confidence": 0.8,
                "predictions": [],
            }
            return PredictionResponse(**response_data)

    except Exception as e:
        logger.error(f"Error predicting traffic: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate predictions: {e}"
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
    request: RouteOptimizationRequest, db: AsyncSession = Depends(get_db)
) -> RouteOptimizationResponse:
    """Optimize a route based on current traffic conditions"""
    try:
        ROUTE_OPTIMIZATION_TIME.observe(0.5)  # Mock timing
        optimized_route = await route_optimizer.optimize(request)

        # Convert the RouteResponse to the expected format
        optimized_route_dict = {
            "route_id": f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "primary_route": (
                optimized_route.primary_route.model_dump()
                if hasattr(optimized_route, "primary_route")
                else {}
            ),
            "alternatives": (
                [route.model_dump() for route in optimized_route.alternative_routes]
                if hasattr(optimized_route, "alternative_routes")
                else []
            ),
            "optimization_time": (
                optimized_route.optimization_time
                if hasattr(optimized_route, "optimization_time")
                else 0.1
            ),
            "factors_considered": (
                optimized_route.factors_considered
                if hasattr(optimized_route, "factors_considered")
                else []
            ),
        }

        return RouteOptimizationResponse(
            route_id=optimized_route_dict["route_id"],
            optimized_route=optimized_route_dict,
            alternatives=optimized_route_dict["alternatives"],
            optimization_metrics={"time_saved": 5.0, "distance_saved": 0.8},
        )
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
            origin=origin,
            destination=destination,
            max_alternatives=max_alternatives,
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
    db=Depends(get_db),
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
async def report_incident(incident: IncidentReport, db=Depends(get_db)):
    """Report a new traffic incident"""
    try:
        result = await incident_detector.report_incident(incident)
        return {"status": "success", "incident_id": result.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str, db=Depends(get_db)):
    """Resolve a traffic incident"""
    try:
        await incident_detector.resolve_incident(incident_id)
        return {"status": "resolved", "incident_id": incident_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Signal Optimization Endpoints
@app.post("/api/v1/signals/optimize")
async def optimize_signals(request: SignalOptimizationRequest, db=Depends(get_db)):
    """Optimize traffic signal timing"""
    try:
        optimization = await traffic_service.optimize_signals(request)
        return optimization
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/signals/status")
async def get_signal_status(
    intersection_id: Optional[str] = Query(None, description="Specific intersection"),
    db=Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
) -> AnalyticsResponse:
    """Get performance analytics for various metrics"""
    try:
        valid_metrics = ["congestion", "throughput", "emissions", "efficiency"]
        if metric_type not in valid_metrics:
            metrics_list = ", ".join(valid_metrics)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric type. Must be one of: {metrics_list}",
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


@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics for the frontend"""
    try:
        # Get current traffic data
        traffic_conditions = await traffic_service.get_current_conditions()
        
        # Get active incidents
        incidents = await traffic_service.get_incidents()
        active_incidents = [inc for inc in incidents if not inc.get('is_resolved', False)]
        
        # Calculate statistics
        total_intersections = len(traffic_conditions)
        avg_speed = sum(cond.speed_mph for cond in traffic_conditions) / max(total_intersections, 1)
        avg_congestion = sum(cond.congestion_level for cond in traffic_conditions) / max(total_intersections, 1)
        
        # Determine system health based on incidents and congestion
        if len(active_incidents) > 5 or avg_congestion > 0.7:
            system_health = "degraded"
        elif len(active_incidents) > 2 or avg_congestion > 0.4:
            system_health = "warning"
        else:
            system_health = "healthy"
        
        return {
            "total_intersections": total_intersections,
            "active_incidents": len(active_incidents),
            "average_speed": round(avg_speed, 1),
            "congestion_percentage": round(avg_congestion * 100, 1),
            "system_health": system_health,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
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


@app.get("/api/v1/websocket/status")
async def get_websocket_status():
    """Get WebSocket connection status"""
    return {
        "status": "operational",
        "connections": manager.get_connection_count(),
        "streaming": True,
        "timestamp": datetime.now().isoformat(),
    }


# Real Data Integration Endpoints
@app.post("/api/v1/real-data/geocode")
async def geocode_address_endpoint(
    address: str = Query(..., description="Address to geocode"),
    prefer_source: Optional[str] = Query(None, description="Preferred data source"),
):
    """Geocode an address using real data sources"""
    try:
        async with real_data_service as service:
            result = await service.geocode_address(address, prefer_source)

            if result:
                return {
                    "success": True,
                    "data": result.data,
                    "source": result.source,
                    "quality": result.quality.value,
                    "timestamp": result.timestamp.isoformat(),
                    "cache_hit": result.cache_hit,
                }
            else:
                raise HTTPException(
                    status_code=404, detail=f"Could not geocode address: {address}"
                )
    except Exception as e:
        logger.error(f"Error geocoding address {address}: {e}")
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {str(e)}")


@app.post("/api/v1/real-data/route")
async def get_real_route(
    start_lat: float = Query(..., description="Start latitude"),
    start_lon: float = Query(..., description="Start longitude"),
    end_lat: float = Query(..., description="End latitude"),
    end_lon: float = Query(..., description="End longitude"),
    mode: str = Query("drive", description="Transportation mode"),
    prefer_source: Optional[str] = Query(None, description="Preferred data source"),
):
    """Get real route using external APIs"""
    try:
        async with real_data_service as service:
            route = await service.get_route(
                start_lat, start_lon, end_lat, end_lon, mode, prefer_source
            )

            if route:
                return {
                    "success": True,
                    "route": {
                        "distance_meters": route.distance_meters,
                        "duration_seconds": route.duration_seconds,
                        "geometry": route.geometry,
                        "steps": route.steps,
                        "summary": route.summary,
                        "warnings": route.warnings,
                    },
                    "source": route.source,
                    "quality": route.quality.value,
                }
            else:
                raise HTTPException(status_code=404, detail="Could not calculate route")
    except Exception as e:
        logger.error(f"Error calculating route: {e}")
        raise HTTPException(
            status_code=500, detail=f"Route calculation failed: {str(e)}"
        )


@app.get("/api/v1/real-data/places/search")
async def search_real_places(
    query: str = Query(..., description="Search query"),
    latitude: float = Query(..., description="Center latitude"),
    longitude: float = Query(..., description="Center longitude"),
    radius_km: int = Query(10, description="Search radius in kilometers"),
    limit: int = Query(20, description="Maximum results"),
    prefer_source: Optional[str] = Query(None, description="Preferred data source"),
):
    """Search for places using real data sources"""
    try:
        async with real_data_service as service:
            places = await service.search_places(
                query, latitude, longitude, radius_km, limit, prefer_source
            )

            return {
                "success": True,
                "places": [
                    {
                        "name": place.name,
                        "latitude": place.latitude,
                        "longitude": place.longitude,
                        "address": place.address,
                        "categories": place.categories,
                        "distance": place.distance,
                        "source": place.source,
                        "properties": place.properties,
                    }
                    for place in places
                ],
                "count": len(places),
                "query": query,
                "center": {"latitude": latitude, "longitude": longitude},
                "radius_km": radius_km,
            }
    except Exception as e:
        logger.error(f"Error searching places: {e}")
        raise HTTPException(status_code=500, detail=f"Place search failed: {str(e)}")


@app.get("/api/v1/real-data/matrix")
async def get_real_matrix(
    locations: str = Query(..., description="Comma-separated lat,lon pairs"),
    prefer_source: Optional[str] = Query(None, description="Preferred data source"),
):
    """Get distance/duration matrix using real data sources"""
    try:
        # Parse locations string: "lat1,lon1;lat2,lon2;..."
        location_pairs = []
        for pair in locations.split(";"):
            lat, lon = map(float, pair.split(","))
            location_pairs.append((lat, lon))

        if len(location_pairs) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 locations required for matrix calculation",
            )

        async with real_data_service as service:
            result = await service.get_traffic_matrix(location_pairs, prefer_source)

            if result:
                return {
                    "success": True,
                    "matrix": result.data,
                    "source": result.source,
                    "quality": result.quality.value,
                    "timestamp": result.timestamp.isoformat(),
                    "cache_hit": result.cache_hit,
                }
            else:
                raise HTTPException(
                    status_code=404, detail="Could not calculate matrix"
                )
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid location format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error calculating matrix: {e}")
        raise HTTPException(
            status_code=500, detail=f"Matrix calculation failed: {str(e)}"
        )


@app.get("/api/v1/real-data/isochrones")
async def get_real_isochrones(
    latitude: float = Query(..., description="Center latitude"),
    longitude: float = Query(..., description="Center longitude"),
    time_minutes: str = Query(
        "15,30", description="Comma-separated time values in minutes"
    ),
    mode: str = Query("drive", description="Transportation mode"),
    prefer_source: Optional[str] = Query(None, description="Preferred data source"),
):
    """Get isochrones (reachable areas) using real data sources"""
    try:
        # Parse time values
        time_values = [float(t.strip()) for t in time_minutes.split(",")]

        async with real_data_service as service:
            result = await service.get_isochrones(
                latitude, longitude, time_values, mode, prefer_source
            )

            if result:
                return {
                    "success": True,
                    "isochrones": result.data,
                    "source": result.source,
                    "quality": result.quality.value,
                    "timestamp": result.timestamp.isoformat(),
                    "cache_hit": result.cache_hit,
                    "center": {"latitude": latitude, "longitude": longitude},
                    "time_minutes": time_values,
                    "mode": mode,
                }
            else:
                raise HTTPException(
                    status_code=404, detail="Could not calculate isochrones"
                )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {str(e)}")
    except Exception as e:
        logger.error(f"Error calculating isochrones: {e}")
        raise HTTPException(
            status_code=500, detail=f"Isochrone calculation failed: {str(e)}"
        )


@app.get("/api/v1/real-data/health")
async def get_real_data_health():
    """Get health status of all real data sources"""
    try:
        async with real_data_service as service:
            health_status = await service.get_health_status()
            return health_status
    except Exception as e:
        logger.error(f"Error getting real data health: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "error",
            "error": str(e),
            "sources": {},
        }


# Demo Endpoints
@app.get("/api/v1/demo/rush-hour-simulation")
async def simulate_rush_hour():
    """Simulate rush hour traffic patterns for demonstration"""
    try:
        logger.info("Generating rush hour simulation")

        # Generate comprehensive rush hour data
        rush_hour_data = {
            "simulation_id": f"rush_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "period": "morning_rush",
            "duration_minutes": 180,
            "traffic_flow": {
                "peak_volume": random.randint(4500, 6000),
                "average_speed": random.randint(15, 25),
                "congestion_index": random.randint(75, 95),
                "incidents_count": random.randint(8, 15),
            },
            "affected_routes": [
                {
                    "route": "I-95 Northbound",
                    "delay_minutes": random.randint(15, 35),
                    "volume_increase": f"{random.randint(200, 400)}%",
                    "speed_reduction": f"{random.randint(40, 60)}%",
                },
                {
                    "route": "FDR Drive",
                    "delay_minutes": random.randint(20, 45),
                    "volume_increase": f"{random.randint(150, 350)}%",
                    "speed_reduction": f"{random.randint(45, 65)}%",
                },
                {
                    "route": "Brooklyn Bridge",
                    "delay_minutes": random.randint(10, 25),
                    "volume_increase": f"{random.randint(180, 320)}%",
                    "speed_reduction": f"{random.randint(35, 55)}%",
                },
            ],
            "hotspots": [
                {
                    "location": "Midtown Manhattan",
                    "severity": "critical",
                    "congestion_score": random.randint(85, 100),
                    "estimated_delays": f"{random.randint(25, 45)} minutes",
                },
                {
                    "location": "Downtown Brooklyn",
                    "severity": "high",
                    "congestion_score": random.randint(70, 85),
                    "estimated_delays": f"{random.randint(15, 30)} minutes",
                },
            ],
            "predictions": {
                "peak_time": (datetime.now() + timedelta(minutes=30)).isoformat(),
                "recovery_time": (datetime.now() + timedelta(hours=2)).isoformat(),
                "max_delay_expected": f"{random.randint(35, 60)} minutes",
                "alternative_routes": [
                    "Use public transportation",
                    "Consider remote work",
                    "Delay non-essential trips",
                ],
            },
            "real_time_data": traffic_service.mock_generator.generate_real_time_data(
                location="citywide", include_predictions=True
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
    # Security: Use environment variable for host, default to localhost
    # For production, set HOST=0.0.0.0 only when needed
    host = os.getenv("HOST", "127.0.0.1")  # Secure default
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )

app = socketio.ASGIApp(socketio_handler.sio, app)
