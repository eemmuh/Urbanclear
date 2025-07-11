"""
Real Data Service - Unified interface for all traffic data sources
Handles fallback strategies, data aggregation, and caching
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from cachetools import TTLCache

from .real_data_config import real_data_config, DataSourceType
from .osm_client import OSMOverpassClient, OSMPlace, OSMRoad
from .geoapify_client import (
    GeoapifyClient,
    GeoapifyPlace,
    GeoapifyRoute,
    GeoapifyGeocode,
)
from .openrouteservice_client import (
    OpenRouteServiceClient,
    ORSRoute,
    ORSMatrix,
    ORSIsochrone,
)

logger = logging.getLogger(__name__)

# Redis support disabled for now due to compatibility issues with Python 3.12
# TODO: Enable Redis when aioredis is compatible with Python 3.12
REDIS_AVAILABLE = False
logger.info("Using in-memory cache only (Redis disabled for compatibility)")


class DataQuality(Enum):
    """Data quality levels"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CACHED = "cached"
    FALLBACK = "fallback"


@dataclass
class TrafficDataResult:
    """Unified traffic data result"""

    data: Any
    source: str
    quality: DataQuality
    timestamp: datetime
    cache_hit: bool = False
    fallback_used: bool = False
    error_details: Optional[str] = None


@dataclass
class RouteResult:
    """Unified route result"""

    distance_meters: float
    duration_seconds: float
    geometry: List[Tuple[float, float]]
    steps: List[Dict[str, Any]]
    source: str
    quality: DataQuality
    summary: str
    warnings: List[str] = None


@dataclass
class PlaceResult:
    """Unified place result"""

    name: str
    latitude: float
    longitude: float
    address: str
    categories: List[str]
    source: str
    distance: Optional[float] = None
    properties: Dict[str, Any] = None


class RealDataService:
    """Unified service for accessing real traffic data from multiple sources"""

    def __init__(self):
        self.config = real_data_config
        self.cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute cache
        self.redis_client = None  # Redis disabled for compatibility

        # Initialize clients
        self.osm_client = OSMOverpassClient()
        self.geoapify_client = GeoapifyClient()
        self.ors_client = OpenRouteServiceClient()

        # Source priority for different operations
        self.routing_priority = ["geoapify", "openrouteservice", "mock"]
        self.geocoding_priority = ["geoapify", "mock"]
        self.places_priority = ["geoapify", "openstreetmap", "openrouteservice", "mock"]

        logger.info("Real Data Service initialized")

    async def __aenter__(self):
        """Async context manager entry"""
        # Redis initialization removed for compatibility
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Redis cleanup removed for compatibility
        pass

    async def _get_cached_data(self, cache_key: str) -> Optional[TrafficDataResult]:
        """Get data from cache"""
        try:
            # Try in-memory cache
            if cache_key in self.cache:
                data = self.cache[cache_key]
                return TrafficDataResult(
                    data=data,
                    source="cache",
                    quality=DataQuality.CACHED,
                    timestamp=datetime.now(),
                    cache_hit=True,
                )

            # Redis cache disabled for compatibility

        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")

        return None

    async def _set_cached_data(self, cache_key: str, data: Any, ttl_seconds: int = 300):
        """Set data in cache"""
        try:
            # Store in memory cache
            self.cache[cache_key] = data

            # Redis cache disabled for compatibility

        except Exception as e:
            logger.warning(f"Cache storage error: {e}")

    async def geocode_address(
        self, address: str, prefer_source: Optional[str] = None
    ) -> Optional[TrafficDataResult]:
        """Geocode an address using the best available source"""
        cache_key = f"geocode:{address}"

        # Check cache first
        cached = await self._get_cached_data(cache_key)
        if cached:
            return cached

        sources = (
            [prefer_source] + self.geocoding_priority
            if prefer_source
            else self.geocoding_priority
        )

        for source in sources:
            if not source or not self.config.is_source_available(source):
                continue

            try:
                if source == "geoapify":
                    async with self.geoapify_client as client:
                        results = await client.geocode_address(address, limit=1)
                        if results:
                            result_data = {
                                "latitude": results[0].latitude,
                                "longitude": results[0].longitude,
                                "formatted_address": results[0].formatted_address,
                                "confidence": results[0].confidence,
                                "country": results[0].country,
                                "city": results[0].city,
                                "street": results[0].street,
                            }

                            result = TrafficDataResult(
                                data=result_data,
                                source=source,
                                quality=DataQuality.HIGH,
                                timestamp=datetime.now(),
                            )

                            await self._set_cached_data(
                                cache_key, result_data, 3600
                            )  # Cache for 1 hour
                            return result

                elif source == "mock":
                    # Fallback to mock geocoding
                    mock_result = await self._generate_mock_geocoding(address)
                    if mock_result:
                        result = TrafficDataResult(
                            data=mock_result,
                            source=source,
                            quality=DataQuality.FALLBACK,
                            timestamp=datetime.now(),
                        )
                        await self._set_cached_data(
                            cache_key, mock_result, 300
                        )  # Cache for 5 minutes
                        return result

                # Add other geocoding sources here as implemented

            except Exception as e:
                logger.warning(f"Geocoding failed for source {source}: {e}")
                continue

        logger.error(f"All geocoding sources failed for address: {address}")
        return None

    async def get_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        mode: str = "drive",
        prefer_source: Optional[str] = None,
    ) -> Optional[RouteResult]:
        """Get route using the best available source"""
        cache_key = f"route:{start_lat}:{start_lon}:{end_lat}:{end_lon}:{mode}"

        # Check cache first
        cached = await self._get_cached_data(cache_key)
        if cached and cached.data:
            return RouteResult(**cached.data)

        sources = (
            [prefer_source] + self.routing_priority
            if prefer_source
            else self.routing_priority
        )

        for source in sources:
            if not source or not self.config.is_source_available(source):
                continue

            try:
                route_data = None

                if source == "geoapify":
                    async with self.geoapify_client as client:
                        route = await client.get_route(
                            start_lat, start_lon, end_lat, end_lon, mode
                        )
                        if route:
                            route_data = RouteResult(
                                distance_meters=route.distance_meters,
                                duration_seconds=route.duration_seconds,
                                geometry=route.geometry,
                                steps=route.steps,
                                source=source,
                                quality=DataQuality.HIGH,
                                summary=route.summary,
                            )

                elif source == "openrouteservice":
                    async with self.ors_client as client:
                        coords = [(start_lat, start_lon), (end_lat, end_lon)]
                        profile = f"{mode}-car" if mode == "drive" else mode
                        route = await client.get_directions(coords, profile)
                        if route:
                            route_data = RouteResult(
                                distance_meters=route.distance_meters,
                                duration_seconds=route.duration_seconds,
                                geometry=route.geometry,
                                steps=route.steps,
                                source=source,
                                quality=DataQuality.MEDIUM,
                                summary=route.summary,
                                warnings=route.warnings,
                            )

                elif source == "mock":
                    # Fallback to mock data
                    route_data = await self._generate_mock_route(
                        start_lat, start_lon, end_lat, end_lon
                    )

                if route_data:
                    # Cache successful route
                    cache_data = {
                        "distance_meters": route_data.distance_meters,
                        "duration_seconds": route_data.duration_seconds,
                        "geometry": route_data.geometry,
                        "steps": route_data.steps,
                        "source": route_data.source,
                        "quality": route_data.quality.value,
                        "summary": route_data.summary,
                        "warnings": route_data.warnings,
                    }
                    await self._set_cached_data(
                        cache_key, cache_data, 1800
                    )  # Cache for 30 minutes
                    return route_data

            except Exception as e:
                logger.warning(f"Routing failed for source {source}: {e}")
                continue

        logger.error(
            f"All routing sources failed for route: {start_lat},{start_lon} -> {end_lat},{end_lon}"
        )
        return None

    async def search_places(
        self,
        query: str,
        latitude: float,
        longitude: float,
        radius_km: int = 10,
        limit: int = 20,
        prefer_source: Optional[str] = None,
    ) -> List[PlaceResult]:
        """Search for places using the best available sources"""
        cache_key = f"places:{query}:{latitude}:{longitude}:{radius_km}:{limit}"

        # Check cache first
        cached = await self._get_cached_data(cache_key)
        if cached and cached.data:
            return [PlaceResult(**place) for place in cached.data]

        sources = (
            [prefer_source] + self.places_priority
            if prefer_source
            else self.places_priority
        )
        all_places = []

        for source in sources:
            if not source or not self.config.is_source_available(source):
                continue

            try:
                places = []

                if source == "geoapify":
                    async with self.geoapify_client as client:
                        geo_places = await client.search_places(
                            query, latitude, longitude, radius_km, limit=limit
                        )
                        for place in geo_places:
                            places.append(
                                PlaceResult(
                                    name=place.name,
                                    latitude=place.latitude,
                                    longitude=place.longitude,
                                    address=place.address,
                                    categories=place.categories,
                                    source=source,
                                    distance=place.distance,
                                    properties=place.properties,
                                )
                            )

                elif source == "openstreetmap":
                    async with self.osm_client as client:
                        # Calculate bounding box
                        lat_delta = radius_km / 111.0  # Rough conversion
                        lon_delta = radius_km / (111.0 * abs(latitude))

                        osm_places = await client.get_places_in_area(
                            latitude - lat_delta,
                            longitude - lon_delta,
                            latitude + lat_delta,
                            longitude + lon_delta,
                        )

                        for place in osm_places[:limit]:
                            if query.lower() in place.name.lower():
                                places.append(
                                    PlaceResult(
                                        name=place.name,
                                        latitude=place.latitude,
                                        longitude=place.longitude,
                                        address=place.address or "",
                                        categories=[place.place_type],
                                        source=source,
                                        properties=place.tags,
                                    )
                                )

                elif source == "openrouteservice":
                    async with self.ors_client as client:
                        pois = await client.get_pois(
                            "pois",
                            {
                                "geojson": {
                                    "type": "Point",
                                    "coordinates": [longitude, latitude],
                                },
                                "buffer": radius_km * 1000,
                            },
                            limit=limit,
                        )

                        for poi in pois:
                            if query.lower() in poi["name"].lower():
                                places.append(
                                    PlaceResult(
                                        name=poi["name"],
                                        latitude=poi["latitude"],
                                        longitude=poi["longitude"],
                                        address="",
                                        categories=[poi["category"]],
                                        source=source,
                                        distance=poi.get("distance"),
                                        properties=poi.get("tags", {}),
                                    )
                                )

                elif source == "mock":
                    # Fallback to mock places
                    mock_places = await self._generate_mock_places(
                        query, latitude, longitude, radius_km, limit
                    )
                    if mock_places:
                        places.extend(mock_places)
                        logger.info(
                            f"Found {len(mock_places)} mock places for '{query}'"
                        )

                if places:
                    all_places.extend(places)
                    logger.info(f"Found {len(places)} places from {source}")

            except Exception as e:
                logger.warning(f"Place search failed for source {source}: {e}")
                continue

        # Remove duplicates and sort by relevance/distance
        unique_places = self._deduplicate_places(all_places)

        if unique_places:
            # Cache results
            cache_data = [
                {
                    "name": place.name,
                    "latitude": place.latitude,
                    "longitude": place.longitude,
                    "address": place.address,
                    "categories": place.categories,
                    "source": place.source,
                    "distance": place.distance,
                    "properties": place.properties,
                }
                for place in unique_places
            ]
            await self._set_cached_data(
                cache_key, cache_data, 600
            )  # Cache for 10 minutes

        return unique_places

    async def get_traffic_matrix(
        self, locations: List[Tuple[float, float]], prefer_source: Optional[str] = None
    ) -> Optional[TrafficDataResult]:
        """Get distance/duration matrix between locations"""
        cache_key = f"matrix:{hash(str(locations))}"

        # Check cache first
        cached = await self._get_cached_data(cache_key)
        if cached:
            return cached

        sources = (
            [prefer_source] + self.routing_priority
            if prefer_source
            else self.routing_priority
        )

        for source in sources:
            if not source or not self.config.is_source_available(source):
                continue

            try:
                if source == "openrouteservice" and len(locations) <= 25:  # ORS limit
                    async with self.ors_client as client:
                        matrix = await client.get_matrix(locations)
                        if matrix:
                            result_data = {
                                "durations": matrix.durations,
                                "distances": matrix.distances,
                                "sources": matrix.sources,
                                "destinations": matrix.destinations,
                            }

                            result = TrafficDataResult(
                                data=result_data,
                                source=source,
                                quality=DataQuality.MEDIUM,
                                timestamp=datetime.now(),
                            )

                            await self._set_cached_data(cache_key, result_data, 1800)
                            return result

                elif source == "mock":
                    # Fallback to mock matrix
                    mock_matrix = await self._generate_mock_matrix(locations)
                    if mock_matrix:
                        result = TrafficDataResult(
                            data=mock_matrix,
                            source=source,
                            quality=DataQuality.FALLBACK,
                            timestamp=datetime.now(),
                        )
                        await self._set_cached_data(
                            cache_key, mock_matrix, 600
                        )  # Cache for 10 minutes
                        return result

                elif source == "mock":
                    # Fallback to mock matrix
                    mock_matrix = await self._generate_mock_matrix(locations)
                    if mock_matrix:
                        result = TrafficDataResult(
                            data=mock_matrix,
                            source=source,
                            quality=DataQuality.FALLBACK,
                            timestamp=datetime.now(),
                        )
                        await self._set_cached_data(
                            cache_key, mock_matrix, 600
                        )  # Cache for 10 minutes
                        return result

                # Add other matrix sources here

            except Exception as e:
                logger.warning(f"Matrix calculation failed for source {source}: {e}")
                continue

        return None

    async def get_isochrones(
        self,
        latitude: float,
        longitude: float,
        time_minutes: List[float],
        mode: str = "drive",
        prefer_source: Optional[str] = None,
    ) -> Optional[TrafficDataResult]:
        """Get isochrones (reachable areas) for location"""
        cache_key = f"isochrone:{latitude}:{longitude}:{time_minutes}:{mode}"

        # Check cache first
        cached = await self._get_cached_data(cache_key)
        if cached:
            return cached

        sources = [prefer_source] + ["geoapify", "openrouteservice", "mock"]

        for source in sources:
            if not source or not self.config.is_source_available(source):
                continue

            try:
                if source == "geoapify":
                    async with self.geoapify_client as client:
                        isochrones = []
                        for time_min in time_minutes:
                            iso = await client.get_isochrone(
                                latitude, longitude, int(time_min), mode
                            )
                            if iso:
                                isochrones.append(iso)

                        if isochrones:
                            result = TrafficDataResult(
                                data=isochrones,
                                source=source,
                                quality=DataQuality.HIGH,
                                timestamp=datetime.now(),
                            )
                            await self._set_cached_data(cache_key, isochrones, 1800)
                            return result

                elif source == "openrouteservice":
                    async with self.ors_client as client:
                        locations = [(latitude, longitude)]
                        isochrones = await client.get_isochrones(
                            locations, time_minutes, "time", f"{mode}-car"
                        )

                        if isochrones:
                            iso_data = [
                                {
                                    "center": iso.center,
                                    "value": iso.value,
                                    "area_sqm": iso.area_sqm,
                                    "geometry": iso.geometry,
                                    "properties": iso.properties,
                                }
                                for iso in isochrones
                            ]

                            result = TrafficDataResult(
                                data=iso_data,
                                source=source,
                                quality=DataQuality.MEDIUM,
                                timestamp=datetime.now(),
                            )
                            await self._set_cached_data(cache_key, iso_data, 1800)
                            return result

                elif source == "mock":
                    # Fallback to mock isochrones
                    mock_isochrones = await self._generate_mock_isochrones(
                        latitude, longitude, time_minutes, mode
                    )
                    if mock_isochrones:
                        result = TrafficDataResult(
                            data=mock_isochrones,
                            source=source,
                            quality=DataQuality.FALLBACK,
                            timestamp=datetime.now(),
                        )
                        await self._set_cached_data(cache_key, mock_isochrones, 1800)
                        return result

            except Exception as e:
                logger.warning(f"Isochrone calculation failed for source {source}: {e}")
                continue

        return None

    def _deduplicate_places(self, places: List[PlaceResult]) -> List[PlaceResult]:
        """Remove duplicate places based on proximity and name similarity"""
        unique_places = []

        for place in places:
            is_duplicate = False

            for existing in unique_places:
                # Check if places are very close (within 50 meters) and have similar names
                distance = self._calculate_distance(
                    place.latitude,
                    place.longitude,
                    existing.latitude,
                    existing.longitude,
                )

                name_similarity = self._calculate_name_similarity(
                    place.name, existing.name
                )

                if (
                    distance < 0.05 and name_similarity > 0.8
                ):  # 50m and 80% name similarity
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_places.append(place)

        # Sort by distance if available, otherwise by name
        unique_places.sort(key=lambda p: (p.distance or float("inf"), p.name))

        return unique_places

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points in kilometers"""
        import math

        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()

        if name1 == name2:
            return 1.0

        # Simple Jaccard similarity
        set1 = set(name1.split())
        set2 = set(name2.split())

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    async def _generate_mock_places(
        self, query: str, latitude: float, longitude: float, radius_km: int, limit: int
    ) -> List[PlaceResult]:
        """Generate mock places for search queries"""
        import random

        # Mock places database categorized by type
        mock_places_db = {
            "coffee": [
                {"name": "Starbucks Coffee", "categories": ["coffee", "cafe"]},
                {
                    "name": "Local Coffee Roasters",
                    "categories": ["coffee", "cafe", "local"],
                },
                {
                    "name": "The Daily Grind",
                    "categories": ["coffee", "cafe", "breakfast"],
                },
                {"name": "Blue Bottle Coffee", "categories": ["coffee", "specialty"]},
                {"name": "Corner Cafe", "categories": ["coffee", "cafe", "quick"]},
            ],
            "restaurant": [
                {
                    "name": "Tony's Italian Kitchen",
                    "categories": ["restaurant", "italian"],
                },
                {
                    "name": "Burger Palace",
                    "categories": ["restaurant", "american", "fast food"],
                },
                {
                    "name": "Sushi Zen",
                    "categories": ["restaurant", "japanese", "sushi"],
                },
                {
                    "name": "The Green Table",
                    "categories": ["restaurant", "healthy", "vegetarian"],
                },
                {
                    "name": "Pizza Corner",
                    "categories": ["restaurant", "pizza", "italian"],
                },
            ],
            "gas": [
                {"name": "Shell Gas Station", "categories": ["gas station", "fuel"]},
                {
                    "name": "BP Service Station",
                    "categories": ["gas station", "fuel", "convenience"],
                },
                {"name": "Chevron", "categories": ["gas station", "fuel"]},
                {
                    "name": "ExxonMobil",
                    "categories": ["gas station", "fuel", "convenience"],
                },
                {
                    "name": "Local Fuel Stop",
                    "categories": ["gas station", "fuel", "local"],
                },
            ],
            "hotel": [
                {"name": "Grand Hotel", "categories": ["hotel", "luxury"]},
                {"name": "Budget Inn", "categories": ["hotel", "budget"]},
                {"name": "Business Suites", "categories": ["hotel", "business"]},
                {"name": "Cozy B&B", "categories": ["hotel", "bed and breakfast"]},
                {"name": "Downtown Lodge", "categories": ["hotel", "urban"]},
            ],
            "bank": [
                {"name": "First National Bank", "categories": ["bank", "atm"]},
                {"name": "City Credit Union", "categories": ["bank", "credit union"]},
                {"name": "Chase Bank", "categories": ["bank", "atm", "financial"]},
                {"name": "Community Bank", "categories": ["bank", "local"]},
                {"name": "Wells Fargo", "categories": ["bank", "atm", "financial"]},
            ],
            "store": [
                {
                    "name": "SuperMart",
                    "categories": ["store", "grocery", "supermarket"],
                },
                {"name": "Corner Store", "categories": ["store", "convenience"]},
                {"name": "Electronics Plus", "categories": ["store", "electronics"]},
                {
                    "name": "Fashion Boutique",
                    "categories": ["store", "clothing", "fashion"],
                },
                {
                    "name": "Hardware Store",
                    "categories": ["store", "hardware", "tools"],
                },
            ],
        }

        # Find matching places based on query
        query_lower = query.lower()
        matching_places = []

        # Check each category for matches
        for category, places in mock_places_db.items():
            if category in query_lower or any(
                cat in query_lower for cat in ["shop", "store", "restaurant", "cafe"]
            ):
                matching_places.extend(places)
            else:
                # Check individual places for name matches
                for place in places:
                    if any(
                        word in place["name"].lower() for word in query_lower.split()
                    ):
                        matching_places.append(place)

        # If no specific matches, return some general places
        if not matching_places:
            # Return a mix of common places
            all_places = []
            for places in mock_places_db.values():
                all_places.extend(places)
            matching_places = random.sample(all_places, min(8, len(all_places)))

        # Generate mock places around the given coordinates
        results = []
        for i, place_template in enumerate(matching_places[:limit]):
            # Generate random coordinates within radius
            angle = random.uniform(0, 2 * 3.14159)
            distance = random.uniform(0.1, radius_km)

            # Convert to coordinate offset (rough approximation)
            lat_offset = (distance / 111.0) * random.choice(
                [-1, 1]
            )  # 111 km per degree latitude
            lon_offset = (distance / (111.0 * abs(latitude))) * random.choice([-1, 1])

            mock_lat = latitude + lat_offset
            mock_lon = longitude + lon_offset

            # Calculate distance from search center
            actual_distance = self._calculate_distance(
                latitude, longitude, mock_lat, mock_lon
            )

            result = PlaceResult(
                name=place_template["name"],
                latitude=mock_lat,
                longitude=mock_lon,
                address=f"{place_template['name']}, {int(mock_lat * 1000) % 999} Main St",
                categories=place_template["categories"],
                source="mock",
                distance=actual_distance,
                properties={
                    "mock": True,
                    "opening_hours": (
                        "9:00-21:00"
                        if "restaurant" in place_template["categories"]
                        else "24/7"
                    ),
                    "rating": round(random.uniform(3.5, 4.8), 1),
                    "price_level": random.choice(["$", "$$", "$$$"]),
                },
            )
            results.append(result)

        return results

    async def _generate_mock_matrix(
        self, locations: List[Tuple[float, float]]
    ) -> Dict[str, Any]:
        """Generate mock traffic matrix as fallback"""
        import random

        num_locations = len(locations)

        # Generate distance and duration matrices
        distances = []
        durations = []

        for i in range(num_locations):
            dist_row = []
            duration_row = []

            for j in range(num_locations):
                if i == j:
                    # Same location
                    dist_row.append(0.0)
                    duration_row.append(0.0)
                else:
                    # Calculate estimated distance and duration
                    lat1, lon1 = locations[i]
                    lat2, lon2 = locations[j]

                    distance_km = self._calculate_distance(lat1, lon1, lat2, lon2)
                    distance_m = distance_km * 1000

                    # Estimate duration based on distance (with traffic factors)
                    base_speed_kmh = random.uniform(25, 45)  # 25-45 km/h average speed
                    duration_hours = distance_km / base_speed_kmh
                    duration_seconds = duration_hours * 3600

                    dist_row.append(round(distance_m, 1))
                    duration_row.append(round(duration_seconds, 1))

            distances.append(dist_row)
            durations.append(duration_row)

        return {
            "durations": durations,
            "distances": distances,
            "sources": list(range(num_locations)),
            "destinations": list(range(num_locations)),
            "metadata": {
                "service": "mock",
                "timestamp": datetime.now().isoformat(),
                "engine": "mock_traffic_engine",
                "units": {"distance": "meters", "duration": "seconds"},
            },
        }

    async def _generate_mock_isochrones(
        self, latitude: float, longitude: float, time_minutes: List[float], mode: str
    ) -> List[Dict[str, Any]]:
        """Generate mock isochrones as fallback"""
        import random
        import math

        isochrones = []

        for time_min in time_minutes:
            # Estimate reachable radius based on time and mode
            if mode == "walk":
                speed_kmh = 5  # Walking speed
            elif mode == "bike":
                speed_kmh = 15  # Cycling speed
            elif mode == "drive":
                speed_kmh = random.uniform(30, 50)  # Driving speed with traffic
            else:
                speed_kmh = 40  # Default

            # Calculate radius (with some randomness for traffic)
            radius_km = (time_min / 60) * speed_kmh * random.uniform(0.7, 1.1)
            radius_degrees = radius_km / 111.0  # Rough conversion

            # Generate a simple circular polygon (approximation)
            num_points = 16
            coordinates = []

            for i in range(num_points + 1):  # +1 to close the polygon
                angle = (i * 2 * math.pi) / num_points
                point_lat = latitude + radius_degrees * math.cos(angle)
                point_lon = longitude + radius_degrees * math.sin(angle) / math.cos(
                    math.radians(latitude)
                )
                coordinates.append([point_lon, point_lat])  # GeoJSON format: [lon, lat]

            # Estimate area
            area_sqm = math.pi * (radius_km * 1000) ** 2

            isochrone = {
                "type": "isochrone",
                "center": {"latitude": latitude, "longitude": longitude},
                "value": time_min,
                "area_sqm": round(area_sqm, 2),
                "geometry": {"type": "Polygon", "coordinates": [coordinates]},
                "properties": {
                    "group_index": len(isochrones),
                    "value": time_min,
                    "center": [longitude, latitude],
                    "mode": mode,
                    "units": "minutes",
                    "area": round(area_sqm, 2),
                    "reach_factor": round(random.uniform(0.8, 1.0), 2),
                    "traffic_factor": round(random.uniform(0.9, 1.3), 2),
                },
            }

            isochrones.append(isochrone)

        return isochrones

    async def _generate_mock_geocoding(self, address: str) -> Optional[Dict[str, Any]]:
        """Generate mock geocoding as fallback"""
        # Mock geocoding for common addresses
        mock_locations = {
            "times square": {
                "latitude": 40.7580,
                "longitude": -73.9855,
                "formatted_address": "Times Square, New York, NY, USA",
                "confidence": 0.9,
                "country": "United States",
                "city": "New York",
                "street": "Times Square",
            },
            "golden gate bridge": {
                "latitude": 37.8199,
                "longitude": -122.4783,
                "formatted_address": "Golden Gate Bridge, San Francisco, CA, USA",
                "confidence": 0.9,
                "country": "United States",
                "city": "San Francisco",
                "street": "Golden Gate Bridge",
            },
            "1600 pennsylvania avenue": {
                "latitude": 38.8977,
                "longitude": -77.0365,
                "formatted_address": "1600 Pennsylvania Avenue NW, Washington, DC, USA",
                "confidence": 0.9,
                "country": "United States",
                "city": "Washington",
                "street": "1600 Pennsylvania Avenue NW",
            },
            "empire state building": {
                "latitude": 40.7484,
                "longitude": -73.9857,
                "formatted_address": "Empire State Building, New York, NY, USA",
                "confidence": 0.9,
                "country": "United States",
                "city": "New York",
                "street": "350 5th Avenue",
            },
            "brooklyn bridge": {
                "latitude": 40.7061,
                "longitude": -73.9969,
                "formatted_address": "Brooklyn Bridge, New York, NY, USA",
                "confidence": 0.9,
                "country": "United States",
                "city": "New York",
                "street": "Brooklyn Bridge",
            },
            "central park": {
                "latitude": 40.7812,
                "longitude": -73.9665,
                "formatted_address": "Central Park, New York, NY, USA",
                "confidence": 0.9,
                "country": "United States",
                "city": "New York",
                "street": "Central Park",
            },
        }

        # Normalize address for lookup
        normalized = address.lower().strip()

        # Try exact match first
        if normalized in mock_locations:
            return mock_locations[normalized]

        # Try partial matches
        for key, location in mock_locations.items():
            if key in normalized or normalized in key:
                return location

        # If no match found, generate a location in NYC area
        return {
            "latitude": 40.7589
            + (random.random() - 0.5) * 0.1,  # Random point around NYC
            "longitude": -73.9851 + (random.random() - 0.5) * 0.1,
            "formatted_address": f"{address} (estimated location)",
            "confidence": 0.3,
            "country": "United States",
            "city": "New York",
            "street": address,
        }

    async def _generate_mock_route(
        self, start_lat: float, start_lon: float, end_lat: float, end_lon: float
    ) -> RouteResult:
        """Generate mock route as fallback"""
        distance = (
            self._calculate_distance(start_lat, start_lon, end_lat, end_lon) * 1000
        )  # Convert to meters
        duration = distance / 13.89  # Assume ~50 km/h average speed

        return RouteResult(
            distance_meters=distance,
            duration_seconds=duration,
            geometry=[(start_lat, start_lon), (end_lat, end_lon)],
            steps=[
                {
                    "instruction": f"Drive from start to destination",
                    "distance": distance,
                    "duration": duration,
                }
            ],
            source="mock",
            quality=DataQuality.FALLBACK,
            summary=f"{distance/1000:.1f} km, {duration/60:.0f} min (estimated)",
        )

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all data sources"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "healthy",
            "sources": {},
        }

        unhealthy_count = 0

        # Check each source
        for source_name in ["openstreetmap", "geoapify", "openrouteservice"]:
            try:
                if source_name == "openstreetmap":
                    healthy = await self.osm_client.health_check()
                elif source_name == "geoapify":
                    if self.geoapify_client.api_key:
                        async with self.geoapify_client as client:
                            healthy = await client.health_check()
                    else:
                        healthy = False
                elif source_name == "openrouteservice":
                    if self.ors_client.api_key:
                        async with self.ors_client as client:
                            healthy = await client.health_check()
                    else:
                        healthy = False

                status["sources"][source_name] = {
                    "healthy": healthy,
                    "available": self.config.is_source_available(source_name),
                    "rate_limit_remaining": self.config.get_remaining_requests(
                        source_name
                    ),
                }

                if not healthy:
                    unhealthy_count += 1

            except Exception as e:
                status["sources"][source_name] = {"healthy": False, "error": str(e)}
                unhealthy_count += 1

        # Set overall health
        total_sources = len(status["sources"])
        if unhealthy_count == 0:
            status["overall_health"] = "healthy"
        elif unhealthy_count < total_sources:
            status["overall_health"] = "degraded"
        else:
            status["overall_health"] = "unhealthy"

        return status


# Global instance for easy access
real_data_service = RealDataService()
