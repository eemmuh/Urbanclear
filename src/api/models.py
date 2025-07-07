"""
Pydantic models for API request/response validation
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field


class TrafficSeverity(str, Enum):
    """Traffic severity levels"""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


class IncidentType(str, Enum):
    """Types of traffic incidents"""

    ACCIDENT = "accident"
    CONSTRUCTION = "construction"
    ROAD_CLOSURE = "road_closure"
    WEATHER = "weather"
    EVENT = "event"
    BREAKDOWN = "breakdown"
    OTHER = "other"


class RoutePreference(str, Enum):
    """Route optimization preferences"""

    FASTEST = "fastest"
    SHORTEST = "shortest"
    MOST_FUEL_EFFICIENT = "most_fuel_efficient"
    AVOID_TOLLS = "avoid_tolls"
    AVOID_HIGHWAYS = "avoid_highways"


class Location(BaseModel):
    """Geographic location"""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: Optional[str] = Field(None, description="Human-readable address")

    model_config = {
        "json_schema_extra": {
            "example": {
                "latitude": 40.7831,
                "longitude": -73.9712,
                "address": "Central Park, New York, NY",
            }
        }
    }


class TrafficCondition(BaseModel):
    """Current traffic condition at a location"""

    id: str = Field(..., description="Unique identifier")
    location: Location
    timestamp: datetime = Field(..., description="When the data was recorded")
    speed_mph: float = Field(..., ge=0, description="Average speed in mph")
    volume: int = Field(..., ge=0, description="Number of vehicles per hour")
    density: float = Field(..., ge=0, description="Vehicles per mile")
    severity: TrafficSeverity
    congestion_level: float = Field(
        ..., ge=0, le=1, description="Congestion level (0-1)"
    )
    travel_time_index: float = Field(
        ..., ge=1, description="Travel time compared to free flow"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "sensor_001",
                "location": {
                    "latitude": 40.7831,
                    "longitude": -73.9712,
                    "address": "5th Avenue & 59th Street",
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "speed_mph": 25.5,
                "volume": 1200,
                "density": 45.0,
                "severity": "moderate",
                "congestion_level": 0.6,
                "travel_time_index": 1.8,
            }
        }
    }


class TrafficPrediction(BaseModel):
    """Traffic prediction for a location"""

    location: Location
    prediction_time: datetime = Field(..., description="When the prediction is for")
    predicted_speed: float = Field(..., ge=0, description="Predicted speed in mph")
    predicted_volume: int = Field(..., ge=0, description="Predicted volume")
    predicted_severity: TrafficSeverity
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")
    factors: List[str] = Field(default=[], description="Factors affecting prediction")

    model_config = {
        "json_schema_extra": {
            "example": {
                "location": {
                    "latitude": 40.7831,
                    "longitude": -73.9712,
                    "address": "5th Avenue & 59th Street",
                },
                "prediction_time": "2024-01-01T13:00:00Z",
                "predicted_speed": 22.0,
                "predicted_volume": 1400,
                "predicted_severity": "high",
                "confidence": 0.85,
                "factors": ["rush_hour", "weather_rain", "event_nearby"],
            }
        }
    }


class RoutePoint(BaseModel):
    """A point along a route"""

    location: Location
    estimated_travel_time: int = Field(
        ..., description="Travel time to this point in minutes"
    )
    distance_from_start: float = Field(..., description="Distance from start in miles")
    traffic_conditions: Optional[TrafficCondition] = None


class Route(BaseModel):
    """A route between two points"""

    points: List[RoutePoint]
    total_distance: float = Field(..., description="Total distance in miles")
    total_time: int = Field(..., description="Total time in minutes")
    total_fuel_cost: Optional[float] = Field(None, description="Estimated fuel cost")
    toll_cost: Optional[float] = Field(None, description="Total toll cost")
    carbon_footprint: Optional[float] = Field(None, description="CO2 emissions in kg")
    traffic_score: float = Field(..., ge=0, le=1, description="Overall traffic score")


class RouteRequest(BaseModel):
    """Request for route optimization"""

    origin: Location
    destination: Location
    departure_time: Optional[datetime] = Field(None, description="When to depart")
    preferences: List[RoutePreference] = Field(default=[RoutePreference.FASTEST])
    avoid_incidents: bool = Field(True, description="Avoid active incidents")
    vehicle_type: Optional[str] = Field(None, description="Type of vehicle")

    model_config = {
        "json_schema_extra": {
            "example": {
                "origin": {
                    "latitude": 40.7831,
                    "longitude": -73.9712,
                    "address": "Central Park, NY",
                },
                "destination": {
                    "latitude": 40.7505,
                    "longitude": -73.9934,
                    "address": "Times Square, NY",
                },
                "departure_time": "2024-01-01T08:00:00Z",
                "preferences": ["fastest"],
                "avoid_incidents": True,
                "vehicle_type": "car",
            }
        }
    }


class RouteResponse(BaseModel):
    """Response model for route queries"""

    route_id: str
    waypoints: List[Dict[str, Any]]
    total_distance: float
    estimated_time: float
    traffic_conditions: List[Dict[str, Any]]
    alternative_routes: List[Dict[str, Any]] = []

    model_config = {
        "json_schema_extra": {
            "example": {
                "route_id": "route_123",
                "waypoints": [
                    {"lat": 40.7831, "lng": -73.9712, "address": "Central Park"},
                    {"lat": 40.7505, "lng": -73.9934, "address": "Times Square"},
                ],
                "total_distance": 2.5,
                "estimated_time": 15.0,
                "traffic_conditions": [
                    {"segment": "segment_1", "congestion": "moderate", "delay": 3.0}
                ],
                "alternative_routes": [],
            }
        }
    }


class PredictionResponse(BaseModel):
    """Response model for traffic predictions"""

    predictions: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}
    confidence: float = 0.0
    generated_at: datetime = datetime.now(timezone.utc)

    model_config = {
        "json_schema_extra": {
            "example": {
                "predictions": [
                    {
                        "location": "Central Park South",
                        "predicted_flow": 1200,
                        "predicted_speed": 25.5,
                        "timestamp": "2024-01-01T13:00:00Z",
                        "confidence": 0.85,
                    }
                ],
                "metadata": {
                    "model_version": "1.0.0",
                    "prediction_horizon": "1_hour",
                    "features_used": ["historical_flow", "weather", "day_of_week"],
                },
                "confidence": 0.85,
                "generated_at": "2024-01-01T12:00:00Z",
            }
        }
    }


class IncidentReport(BaseModel):
    """Traffic incident report"""

    id: Optional[str] = Field(None, description="Incident ID (auto-generated)")
    type: IncidentType
    location: Location
    severity: TrafficSeverity
    description: str = Field(..., max_length=500, description="Incident description")
    reported_time: datetime = Field(default_factory=datetime.now)
    estimated_duration: Optional[int] = Field(
        None, description="Estimated duration in minutes"
    )
    lanes_affected: Optional[int] = Field(
        None, ge=0, description="Number of lanes affected"
    )
    is_resolved: bool = Field(False, description="Whether incident is resolved")
    resolved_time: Optional[datetime] = Field(
        None, description="When incident was resolved"
    )
    impact_radius: Optional[float] = Field(
        None, ge=0, description="Impact radius in miles"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "accident",
                "location": {
                    "latitude": 40.7831,
                    "longitude": -73.9712,
                    "address": "FDR Drive northbound",
                },
                "severity": "high",
                "description": "Multi-vehicle accident blocking 2 lanes",
                "estimated_duration": 60,
                "lanes_affected": 2,
                "impact_radius": 0.5,
            }
        }
    }


class SignalOptimizationRequest(BaseModel):
    """Request for traffic signal optimization"""

    intersection_id: str = Field(..., description="Intersection identifier")
    optimization_period: int = Field(
        60, ge=30, le=300, description="Optimization period in minutes"
    )
    priority_direction: Optional[str] = Field(
        None, description="Priority traffic direction"
    )
    consider_pedestrians: bool = Field(True, description="Consider pedestrian traffic")
    emergency_override: bool = Field(False, description="Emergency vehicle priority")


class SignalTiming(BaseModel):
    """Traffic signal timing configuration"""

    intersection_id: str
    phase_timings: Dict[str, int] = Field(..., description="Phase timings in seconds")
    cycle_length: int = Field(..., description="Total cycle length in seconds")
    optimization_score: float = Field(
        ..., ge=0, le=1, description="Optimization effectiveness"
    )
    last_updated: datetime = Field(default_factory=datetime.now)


class AnalyticsSummary(BaseModel):
    """Traffic analytics summary"""

    period: str = Field(..., description="Time period for analytics")
    total_vehicles: int = Field(..., ge=0, description="Total vehicles monitored")
    average_speed: float = Field(
        ..., ge=0, description="Average speed across all locations"
    )
    congestion_incidents: int = Field(
        ..., ge=0, description="Number of congestion incidents"
    )
    resolved_incidents: int = Field(
        ..., ge=0, description="Number of resolved incidents"
    )
    fuel_savings: float = Field(
        ..., ge=0, description="Estimated fuel savings in gallons"
    )
    time_savings: int = Field(
        ..., ge=0, description="Estimated time savings in minutes"
    )
    emission_reduction: float = Field(..., ge=0, description="CO2 reduction in kg")
    system_efficiency: float = Field(
        ..., ge=0, le=1, description="Overall system efficiency"
    )
    peak_congestion_hours: List[int] = Field(
        default=[], description="Hours with peak congestion"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "period": "24h",
                "total_vehicles": 125000,
                "average_speed": 28.5,
                "congestion_incidents": 45,
                "resolved_incidents": 42,
                "fuel_savings": 2500.0,
                "time_savings": 15000,
                "emission_reduction": 850.5,
                "system_efficiency": 0.78,
                "peak_congestion_hours": [8, 9, 17, 18, 19],
            }
        }
    }


class PerformanceMetric(BaseModel):
    """System performance metric"""

    metric_name: str
    value: Union[float, int, str]
    unit: str
    timestamp: datetime
    location: Optional[str] = None
    target_value: Optional[Union[float, int]] = None
    status: str = Field(
        default="normal", description="Status: normal, warning, critical"
    )


class SystemStats(BaseModel):
    """System statistics"""

    uptime: int = Field(..., description="System uptime in seconds")
    active_sensors: int = Field(..., ge=0, description="Number of active sensors")
    data_points_processed: int = Field(
        ..., ge=0, description="Data points processed today"
    )
    prediction_accuracy: float = Field(
        ..., ge=0, le=1, description="Recent prediction accuracy"
    )
    api_requests_today: int = Field(..., ge=0, description="API requests today")
    average_response_time: float = Field(
        ..., ge=0, description="Average API response time in ms"
    )
    database_size: float = Field(..., ge=0, description="Database size in GB")
    cache_hit_rate: float = Field(..., ge=0, le=1, description="Cache hit rate")


class ErrorResponse(BaseModel):
    """Error response model"""

    error: bool = Field(True)
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp: datetime = Field(default_factory=datetime.now)


class SuccessResponse(BaseModel):
    """Success response model"""

    success: bool = Field(True)
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.now)


class RouteOptimizationRequest(BaseModel):
    """Request model for route optimization"""

    origin: Dict[str, float]  # {"lat": float, "lng": float}
    destination: Dict[str, float]  # {"lat": float, "lng": float}
    waypoints: List[Dict[str, float]] = []
    preferences: Dict[str, Any] = {}
    constraints: Dict[str, Any] = {}

    model_config = {
        "json_schema_extra": {
            "example": {
                "origin": {"lat": 40.7831, "lng": -73.9712},
                "destination": {"lat": 40.7505, "lng": -73.9934},
                "waypoints": [{"lat": 40.7614, "lng": -73.9776}],
                "preferences": {"optimize_for": "time", "avoid_tolls": True},
                "constraints": {"max_distance": 50.0, "vehicle_type": "car"},
            }
        }
    }


class RouteOptimizationResponse(BaseModel):
    """Response model for route optimization"""

    route_id: str
    optimized_route: Dict[str, Any]
    alternatives: List[Dict[str, Any]] = []
    optimization_metrics: Dict[str, Any] = {}
    generated_at: datetime = datetime.now(timezone.utc)

    model_config = {
        "json_schema_extra": {
            "example": {
                "route_id": "opt_route_123",
                "optimized_route": {
                    "waypoints": [
                        {"lat": 40.7831, "lng": -73.9712, "address": "Central Park"},
                        {"lat": 40.7505, "lng": -73.9934, "address": "Times Square"},
                    ],
                    "total_distance": 2.5,
                    "estimated_time": 15.0,
                    "traffic_delay": 3.0,
                },
                "alternatives": [],
                "optimization_metrics": {
                    "time_saved": 5.0,
                    "distance_saved": 0.5,
                    "fuel_efficiency": 0.85,
                },
                "generated_at": "2024-01-01T12:00:00Z",
            }
        }
    }


class AnalyticsResponse(BaseModel):
    """Response model for analytics queries"""

    analytics: Dict[str, Any]
    summary: Dict[str, Any] = {}
    generated_at: datetime = datetime.now(timezone.utc)

    model_config = {
        "json_schema_extra": {
            "example": {
                "analytics": {
                    "congestion_levels": [
                        {
                            "location": "Times Square",
                            "level": 0.8,
                            "timestamp": "2024-01-01T12:00:00Z",
                        }
                    ],
                    "average_speed": 25.5,
                    "traffic_volume": 1200,
                },
                "summary": {
                    "total_incidents": 5,
                    "resolved_incidents": 3,
                    "average_response_time": 12.5,
                },
                "generated_at": "2024-01-01T12:00:00Z",
            }
        }
    }
