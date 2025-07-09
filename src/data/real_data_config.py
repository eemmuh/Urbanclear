"""
Real Data Configuration for Traffic Management System
Handles multiple API sources with fallback strategies and rate limiting
"""

import os
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)


class APITier(Enum):
    """API tiers based on cost and capability"""
    FREE = "free"
    FREEMIUM = "freemium"  # Free with rate limits
    PREMIUM = "premium"


class DataSourceType(Enum):
    """Types of traffic data sources"""
    TRAFFIC_FLOW = "traffic_flow"
    INCIDENTS = "incidents"
    ROUTING = "routing"
    GEOCODING = "geocoding"
    PLACES = "places"
    WEATHER = "weather"


@dataclass
class RateLimit:
    """Rate limiting configuration"""
    requests_per_minute: int = 100
    requests_per_hour: int = 5000
    requests_per_day: int = 50000
    requests_per_month: int = 1000000
    concurrent_requests: int = 10
    
    # Internal tracking
    minute_count: int = field(default=0, init=False)
    hour_count: int = field(default=0, init=False)
    day_count: int = field(default=0, init=False)
    month_count: int = field(default=0, init=False)
    last_reset: datetime = field(default_factory=datetime.now, init=False)


@dataclass
class APICredentials:
    """API credentials and configuration"""
    api_key: Optional[str] = None
    secret: Optional[str] = None
    base_url: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataSourceConfig:
    """Configuration for a single data source"""
    name: str
    tier: APITier
    supported_types: List[DataSourceType]
    credentials: APICredentials
    rate_limits: RateLimit
    priority: int = 1  # Lower number = higher priority
    enabled: bool = True
    health_check_url: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3
    fallback_sources: List[str] = field(default_factory=list)


class RealDataConfig:
    """Main configuration manager for real traffic data sources"""
    
    def __init__(self):
        self.data_sources: Dict[str, DataSourceConfig] = {}
        self._initialize_data_sources()
    
    def _initialize_data_sources(self):
        """Initialize all available data sources"""
        
        # Free OpenStreetMap Overpass API
        self.data_sources["openstreetmap"] = DataSourceConfig(
            name="OpenStreetMap Overpass API",
            tier=APITier.FREE,
            supported_types=[DataSourceType.PLACES, DataSourceType.ROUTING],
            credentials=APICredentials(
                base_url="https://overpass.private.coffee/api",
                headers={"User-Agent": "Urbanclear-Traffic-System/1.0 (contact@urbanclear.com)"}
            ),
            rate_limits=RateLimit(
                requests_per_minute=60,  # Be respectful of free service
                requests_per_hour=1000,
                requests_per_day=10000,
                concurrent_requests=5
            ),
            priority=3,
            health_check_url="https://overpass.private.coffee/api/status"
        )
        
        # Geoapify - 3000 requests/day free
        self.data_sources["geoapify"] = DataSourceConfig(
            name="Geoapify Location Platform",
            tier=APITier.FREEMIUM,
            supported_types=[
                DataSourceType.GEOCODING, 
                DataSourceType.ROUTING, 
                DataSourceType.PLACES
            ],
            credentials=APICredentials(
                api_key=os.getenv("GEOAPIFY_API_KEY"),
                base_url="https://api.geoapify.com/v1",
                headers={"User-Agent": "Urbanclear-Traffic-System/1.0"}
            ),
            rate_limits=RateLimit(
                requests_per_minute=100,
                requests_per_hour=500,
                requests_per_day=3000,  # Free tier limit
                requests_per_month=90000,
                concurrent_requests=10
            ),
            priority=2,
            fallback_sources=["openstreetmap"],
            health_check_url="https://api.geoapify.com/v1/status"
        )
        
        # OpenRouteService - Free routing based on OSM
        self.data_sources["openrouteservice"] = DataSourceConfig(
            name="OpenRouteService",
            tier=APITier.FREEMIUM,
            supported_types=[DataSourceType.ROUTING, DataSourceType.PLACES],
            credentials=APICredentials(
                api_key=os.getenv("OPENROUTESERVICE_API_KEY"),
                base_url="https://api.openrouteservice.org",
                headers={"User-Agent": "Urbanclear-Traffic-System/1.0"}
            ),
            rate_limits=RateLimit(
                requests_per_minute=40,
                requests_per_hour=1000,
                requests_per_day=2000,  # Free tier
                requests_per_month=60000,
                concurrent_requests=5
            ),
            priority=2,
            fallback_sources=["geoapify", "openstreetmap"]
        )
        
        # Google Maps Platform - 10K free requests/month
        self.data_sources["google_maps"] = DataSourceConfig(
            name="Google Maps Platform",
            tier=APITier.PREMIUM,
            supported_types=[
                DataSourceType.TRAFFIC_FLOW,
                DataSourceType.ROUTING,
                DataSourceType.GEOCODING,
                DataSourceType.PLACES
            ],
            credentials=APICredentials(
                api_key=os.getenv("GOOGLE_MAPS_API_KEY"),
                base_url="https://maps.googleapis.com/maps/api",
                headers={"User-Agent": "Urbanclear-Traffic-System/1.0"}
            ),
            rate_limits=RateLimit(
                requests_per_minute=1000,  # Very high limits for paid tier
                requests_per_hour=50000,
                requests_per_day=100000,
                requests_per_month=10000,  # Watch the free tier carefully
                concurrent_requests=50
            ),
            priority=1,  # Highest priority for premium features
            fallback_sources=["openrouteservice", "geoapify"],
            health_check_url="https://maps.googleapis.com/maps/api/js"
        )
        
        # HERE API - Alternative premium option
        self.data_sources["here_api"] = DataSourceConfig(
            name="HERE Location Services",
            tier=APITier.PREMIUM,
            supported_types=[
                DataSourceType.TRAFFIC_FLOW,
                DataSourceType.INCIDENTS,
                DataSourceType.ROUTING,
                DataSourceType.GEOCODING
            ],
            credentials=APICredentials(
                api_key=os.getenv("HERE_API_KEY"),
                base_url="https://router.hereapi.com/v8",
                headers={"User-Agent": "Urbanclear-Traffic-System/1.0"}
            ),
            rate_limits=RateLimit(
                requests_per_minute=1000,
                requests_per_hour=50000,
                requests_per_day=100000,
                requests_per_month=50000,  # Generous paid limits
                concurrent_requests=50
            ),
            priority=1,
            enabled=bool(os.getenv("HERE_API_KEY")),  # Only enable if key provided
            fallback_sources=["google_maps", "openrouteservice"]
        )
        
        # Local/Government APIs (example for NYC)
        self.data_sources["nyc_open_data"] = DataSourceConfig(
            name="NYC Open Data",
            tier=APITier.FREE,
            supported_types=[DataSourceType.INCIDENTS, DataSourceType.TRAFFIC_FLOW],
            credentials=APICredentials(
                base_url="https://data.cityofnewyork.us/resource",
                headers={"User-Agent": "Urbanclear-Traffic-System/1.0"}
            ),
            rate_limits=RateLimit(
                requests_per_minute=100,
                requests_per_hour=2000,
                requests_per_day=10000,
                concurrent_requests=10
            ),
            priority=2,
            enabled=True
        )
        
        # Mock data source - always available as fallback
        self.data_sources["mock"] = DataSourceConfig(
            name="Mock Data Generator",
            tier=APITier.FREE,
            supported_types=[
                DataSourceType.GEOCODING,
                DataSourceType.ROUTING,
                DataSourceType.PLACES,
                DataSourceType.TRAFFIC_FLOW,
                DataSourceType.INCIDENTS
            ],
            credentials=APICredentials(
                base_url="internal://mock",
                headers={"User-Agent": "Urbanclear-Traffic-System/1.0"}
            ),
            rate_limits=RateLimit(
                requests_per_minute=1000,  # No real limits for mock
                requests_per_hour=50000,
                requests_per_day=1000000,
                requests_per_month=1000000,
                concurrent_requests=100
            ),
            priority=10,  # Lowest priority (highest number)
            enabled=True
        )
    
    def get_remaining_requests(self, source_name: str) -> Dict[str, int]:
        """Get remaining requests for a data source based on rate limits"""
        if source_name not in self.data_sources:
            return {}
        
        source = self.data_sources[source_name]
        rate_limit = source.rate_limits
        
        return {
            "minute": max(0, rate_limit.requests_per_minute - rate_limit.minute_count),
            "hour": max(0, rate_limit.requests_per_hour - rate_limit.hour_count),
            "day": max(0, rate_limit.requests_per_day - rate_limit.day_count),
            "month": max(0, rate_limit.requests_per_month - rate_limit.month_count)
        }
    
    def is_source_available(self, source_name: str) -> bool:
        """Check if a data source is available and properly configured"""
        if source_name not in self.data_sources:
            return False
        
        source = self.data_sources[source_name]
        
        # Check if source is enabled
        if not source.enabled:
            return False
        
        # For premium/freemium sources, check if API key is available
        if source.tier in [APITier.FREEMIUM, APITier.PREMIUM]:
            if not source.credentials.api_key:
                return False
        
        # Check rate limits
        if not self.can_make_request(source_name):
            return False
        
        return True
    
    def get_sources_for_type(self, data_type: DataSourceType, 
                           enabled_only: bool = True) -> List[DataSourceConfig]:
        """Get all data sources that support a specific data type"""
        sources = []
        for source in self.data_sources.values():
            if data_type in source.supported_types:
                if not enabled_only or source.enabled:
                    sources.append(source)
        
        # Sort by priority (lower number = higher priority)
        return sorted(sources, key=lambda x: x.priority)
    
    def get_primary_source(self, data_type: DataSourceType) -> Optional[DataSourceConfig]:
        """Get the primary (highest priority) source for a data type"""
        sources = self.get_sources_for_type(data_type)
        return sources[0] if sources else None
    
    def get_fallback_chain(self, data_type: DataSourceType) -> List[DataSourceConfig]:
        """Get the complete fallback chain for a data type"""
        return self.get_sources_for_type(data_type)
    
    def can_make_request(self, source_name: str) -> bool:
        """Check if we can make a request to a source based on rate limits"""
        if source_name not in self.data_sources:
            return False
        
        source = self.data_sources[source_name]
        rate_limit = source.rate_limits
        now = datetime.now()
        
        # Reset counters if time periods have passed
        if now - rate_limit.last_reset > timedelta(minutes=1):
            rate_limit.minute_count = 0
        if now - rate_limit.last_reset > timedelta(hours=1):
            rate_limit.hour_count = 0
        if now - rate_limit.last_reset > timedelta(days=1):
            rate_limit.day_count = 0
        if now.month != rate_limit.last_reset.month:
            rate_limit.month_count = 0
        
        # Check all rate limits
        return (
            rate_limit.minute_count < rate_limit.requests_per_minute and
            rate_limit.hour_count < rate_limit.requests_per_hour and
            rate_limit.day_count < rate_limit.requests_per_day and
            rate_limit.month_count < rate_limit.requests_per_month
        )
    
    def record_request(self, source_name: str):
        """Record that a request was made to update rate limiting counters"""
        if source_name in self.data_sources:
            rate_limit = self.data_sources[source_name].rate_limits
            rate_limit.minute_count += 1
            rate_limit.hour_count += 1
            rate_limit.day_count += 1
            rate_limit.month_count += 1
            rate_limit.last_reset = datetime.now()
    
    def get_cost_estimate(self, source_name: str, requests: int) -> Dict[str, Any]:
        """Estimate cost for number of requests (for premium APIs)"""
        if source_name not in self.data_sources:
            return {"error": "Unknown source"}
        
        source = self.data_sources[source_name]
        
        # Cost estimates (rough) - update with actual pricing
        cost_per_1000 = {
            "google_maps": 5.0,  # Essentials tier
            "here_api": 4.0,
            "geoapify": 0.0,  # Free tier
            "openrouteservice": 0.0,
            "openstreetmap": 0.0,
            "nyc_open_data": 0.0
        }
        
        estimated_cost = (requests / 1000) * cost_per_1000.get(source_name, 0)
        
        return {
            "source": source.name,
            "tier": source.tier.value,
            "requests": requests,
            "estimated_cost_usd": round(estimated_cost, 2),
            "free_tier_remaining": max(0, source.rate_limits.requests_per_month - source.rate_limits.month_count)
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the configuration and return status"""
        status = {
            "valid": True,
            "sources": {},
            "missing_keys": [],
            "recommendations": []
        }
        
        for name, source in self.data_sources.items():
            source_status = {
                "enabled": source.enabled,
                "has_credentials": bool(source.credentials.api_key) if source.tier != APITier.FREE else True,
                "tier": source.tier.value,
                "supported_types": [t.value for t in source.supported_types]
            }
            
            # Check for missing API keys
            if source.tier in [APITier.FREEMIUM, APITier.PREMIUM] and not source.credentials.api_key:
                status["missing_keys"].append(f"{name.upper()}_API_KEY")
                source_status["has_credentials"] = False
                if source.enabled:
                    status["valid"] = False
            
            status["sources"][name] = source_status
        
        # Add recommendations
        if not any(s.tier == APITier.PREMIUM for s in self.data_sources.values() if s.enabled):
            status["recommendations"].append("Consider adding a premium API for better traffic data quality")
        
        if not os.getenv("GOOGLE_MAPS_API_KEY"):
            status["recommendations"].append("Add GOOGLE_MAPS_API_KEY for premium traffic data")
        
        return status


# Global configuration instance
real_data_config = RealDataConfig() 