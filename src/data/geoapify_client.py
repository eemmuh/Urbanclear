"""
Geoapify Location Platform API Client
Provides geocoding, routing, and places search with 3000 free requests/day
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import aiohttp
from dataclasses import dataclass

from .real_data_config import real_data_config, DataSourceType

logger = logging.getLogger(__name__)


@dataclass
class GeoapifyPlace:
    """Geoapify place data"""

    place_id: str
    name: str
    latitude: float
    longitude: float
    address: str
    categories: List[str]
    distance: Optional[float] = None
    properties: Dict[str, Any] = None


@dataclass
class GeoapifyRoute:
    """Geoapify route data"""

    distance_meters: float
    duration_seconds: float
    geometry: List[Tuple[float, float]]
    steps: List[Dict[str, Any]]
    summary: str


@dataclass
class GeoapifyGeocode:
    """Geoapify geocoding result"""

    latitude: float
    longitude: float
    formatted_address: str
    confidence: float
    place_type: str
    country: str
    state: Optional[str] = None
    city: Optional[str] = None
    street: Optional[str] = None
    housenumber: Optional[str] = None


class GeoapifyClient:
    """Client for Geoapify Location Platform API"""

    def __init__(self):
        self.config = real_data_config.data_sources["geoapify"]
        self.base_url = self.config.credentials.base_url
        self.api_key = self.config.credentials.api_key
        self.session: Optional[aiohttp.ClientSession] = None

        if not self.api_key:
            logger.warning("No Geoapify API key provided. Service will be disabled.")

    async def __aenter__(self):
        """Async context manager entry"""
        if not self.api_key:
            raise Exception("Geoapify API key not configured")

        connector = aiohttp.TCPConnector(
            limit=self.config.rate_limits.concurrent_requests
        )
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.config.credentials.headers,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _make_request(
        self, endpoint: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make a request to the Geoapify API"""
        if not real_data_config.can_make_request("geoapify"):
            raise Exception("Rate limit exceeded for Geoapify API")

        if not self.session:
            raise Exception("Session not initialized. Use async context manager.")

        # Add API key to params
        params["apiKey"] = self.api_key

        url = f"{self.base_url}{endpoint}"

        try:
            real_data_config.record_request("geoapify")

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Geoapify API request successful: {endpoint}")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Geoapify API error {response.status}: {error_text}")
                    raise Exception(f"Geoapify API error: {response.status}")

        except aiohttp.ClientError as e:
            logger.error(f"Geoapify API connection error: {e}")
            raise Exception(f"Geoapify API connection error: {e}")

    async def geocode_address(
        self, address: str, limit: int = 10
    ) -> List[GeoapifyGeocode]:
        """Geocode an address to coordinates"""

        params = {"text": address, "limit": limit, "format": "json"}

        try:
            result = await self._make_request("/geocode/search", params)
            geocodes = []

            for item in result.get("results", []):
                geocodes.append(
                    GeoapifyGeocode(
                        latitude=float(item["lat"]),
                        longitude=float(item["lon"]),
                        formatted_address=item.get("formatted", ""),
                        confidence=item.get("rank", {}).get("confidence", 0.0),
                        place_type=item.get("result_type", "unknown"),
                        country=item.get("country", ""),
                        state=item.get("state", ""),
                        city=item.get("city", ""),
                        street=item.get("street", ""),
                        housenumber=item.get("housenumber", ""),
                    )
                )

            logger.info(f"Geocoded '{address}' to {len(geocodes)} results")
            return geocodes

        except Exception as e:
            logger.error(f"Error geocoding address with Geoapify: {e}")
            return []

    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> Optional[GeoapifyGeocode]:
        """Reverse geocode coordinates to address"""

        params = {"lat": latitude, "lon": longitude, "format": "json"}

        try:
            result = await self._make_request("/geocode/reverse", params)
            results = result.get("results", [])

            if not results:
                return None

            item = results[0]
            return GeoapifyGeocode(
                latitude=float(item["lat"]),
                longitude=float(item["lon"]),
                formatted_address=item.get("formatted", ""),
                confidence=item.get("rank", {}).get("confidence", 0.0),
                place_type=item.get("result_type", "unknown"),
                country=item.get("country", ""),
                state=item.get("state", ""),
                city=item.get("city", ""),
                street=item.get("street", ""),
                housenumber=item.get("housenumber", ""),
            )

        except Exception as e:
            logger.error(f"Error reverse geocoding with Geoapify: {e}")
            return None

    async def search_places(
        self,
        query: str,
        latitude: float,
        longitude: float,
        radius_km: int = 10,
        categories: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[GeoapifyPlace]:
        """Search for places near a location"""

        params = {
            "text": query,
            "bias": f"proximity:{longitude},{latitude}",
            "filter": f"circle:{longitude},{latitude},{radius_km * 1000}",
            "limit": limit,
            "format": "json",
        }

        if categories:
            params["categories"] = ",".join(categories)

        try:
            result = await self._make_request("/geocode/search", params)
            places = []

            for item in result.get("results", []):
                # Calculate distance if coordinates provided
                distance = None
                if "distance" in item:
                    distance = item["distance"]

                places.append(
                    GeoapifyPlace(
                        place_id=item.get(
                            "place_id", f"geo_{item.get('lat')}_{item.get('lon')}"
                        ),
                        name=item.get("name", item.get("formatted", "Unknown")),
                        latitude=float(item["lat"]),
                        longitude=float(item["lon"]),
                        address=item.get("formatted", ""),
                        categories=item.get("categories", []),
                        distance=distance,
                        properties=item,
                    )
                )

            logger.info(f"Found {len(places)} places for query '{query}'")
            return places

        except Exception as e:
            logger.error(f"Error searching places with Geoapify: {e}")
            return []

    async def get_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        mode: str = "drive",
        waypoints: Optional[List[Tuple[float, float]]] = None,
    ) -> Optional[GeoapifyRoute]:
        """Calculate route between two points"""

        # Build waypoints string
        coordinates = [f"{start_lon},{start_lat}"]

        if waypoints:
            for lat, lon in waypoints:
                coordinates.append(f"{lon},{lat}")

        coordinates.append(f"{end_lon},{end_lat}")
        waypoints_str = "|".join(coordinates)

        params = {
            "waypoints": waypoints_str,
            "mode": mode,  # drive, walk, bicycle, approximated_transit
            "format": "json",
        }

        try:
            result = await self._make_request("/routing", params)
            features = result.get("features", [])

            if not features:
                return None

            route_data = features[0]
            properties = route_data.get("properties", {})
            geometry = route_data.get("geometry", {})

            # Extract route geometry
            coordinates = []
            if geometry.get("type") == "LineString":
                for coord in geometry.get("coordinates", []):
                    coordinates.append(
                        (coord[1], coord[0])
                    )  # Convert lon,lat to lat,lon

            # Extract route steps
            steps = []
            for step in properties.get("legs", [{}])[0].get("steps", []):
                steps.append(
                    {
                        "instruction": step.get("instruction", {}).get("text", ""),
                        "distance": step.get("distance", 0),
                        "duration": step.get("time", 0),
                    }
                )

            return GeoapifyRoute(
                distance_meters=properties.get("distance", 0),
                duration_seconds=properties.get("time", 0),
                geometry=coordinates,
                steps=steps,
                summary=f"{properties.get('distance', 0)/1000:.1f} km, {properties.get('time', 0)/60:.0f} min",
            )

        except Exception as e:
            logger.error(f"Error calculating route with Geoapify: {e}")
            return None

    async def get_isochrone(
        self,
        latitude: float,
        longitude: float,
        time_minutes: int = 15,
        mode: str = "drive",
    ) -> Optional[Dict[str, Any]]:
        """Get isochrone (reachable area) for given time and location"""

        params = {
            "lat": latitude,
            "lon": longitude,
            "time": time_minutes * 60,  # Convert to seconds
            "mode": mode,
            "format": "json",
        }

        try:
            result = await self._make_request("/isoline", params)
            features = result.get("features", [])

            if not features:
                return None

            return {
                "type": "isochrone",
                "time_minutes": time_minutes,
                "mode": mode,
                "center": {"latitude": latitude, "longitude": longitude},
                "geometry": features[0].get("geometry", {}),
                "properties": features[0].get("properties", {}),
            }

        except Exception as e:
            logger.error(f"Error calculating isochrone with Geoapify: {e}")
            return None

    async def autocomplete_address(
        self, text: str, latitude: float, longitude: float, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get address autocomplete suggestions"""

        params = {
            "text": text,
            "bias": f"proximity:{longitude},{latitude}",
            "limit": limit,
            "format": "json",
        }

        try:
            result = await self._make_request("/geocode/autocomplete", params)
            suggestions = []

            for item in result.get("results", []):
                suggestions.append(
                    {
                        "text": item.get("formatted", ""),
                        "latitude": float(item.get("lat", 0)),
                        "longitude": float(item.get("lon", 0)),
                        "place_type": item.get("result_type", "unknown"),
                        "country": item.get("country", ""),
                        "city": item.get("city", ""),
                    }
                )

            logger.info(f"Got {len(suggestions)} autocomplete suggestions for '{text}'")
            return suggestions

        except Exception as e:
            logger.error(f"Error getting autocomplete with Geoapify: {e}")
            return []

    async def get_places_by_category(
        self,
        latitude: float,
        longitude: float,
        categories: List[str],
        radius_km: int = 5,
        limit: int = 50,
    ) -> List[GeoapifyPlace]:
        """Get places by category within radius"""

        params = {
            "categories": ",".join(categories),
            "filter": f"circle:{longitude},{latitude},{radius_km * 1000}",
            "bias": f"proximity:{longitude},{latitude}",
            "limit": limit,
            "format": "json",
        }

        try:
            result = await self._make_request("/places", params)
            places = []

            for item in result.get("features", []):
                properties = item.get("properties", {})
                geometry = item.get("geometry", {})
                coordinates = geometry.get("coordinates", [0, 0])

                places.append(
                    GeoapifyPlace(
                        place_id=properties.get(
                            "place_id", f"geo_{coordinates[1]}_{coordinates[0]}"
                        ),
                        name=properties.get("name", "Unknown"),
                        latitude=coordinates[1],
                        longitude=coordinates[0],
                        address=properties.get("formatted", ""),
                        categories=properties.get("categories", []),
                        distance=properties.get("distance"),
                        properties=properties,
                    )
                )

            logger.info(f"Found {len(places)} places in categories {categories}")
            return places

        except Exception as e:
            logger.error(f"Error getting places by category with Geoapify: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if the Geoapify API is healthy"""
        try:
            # Simple geocoding request to test API
            await self.geocode_address("New York", limit=1)
            return True
        except Exception as e:
            logger.error(f"Geoapify health check failed: {e}")
            return False


# Convenience functions for easy usage
async def geoapify_geocode(address: str, limit: int = 10) -> List[GeoapifyGeocode]:
    """Geocode address using Geoapify"""
    async with GeoapifyClient() as client:
        return await client.geocode_address(address, limit)


async def geoapify_reverse_geocode(
    latitude: float, longitude: float
) -> Optional[GeoapifyGeocode]:
    """Reverse geocode coordinates using Geoapify"""
    async with GeoapifyClient() as client:
        return await client.reverse_geocode(latitude, longitude)


async def geoapify_search_places(
    query: str, latitude: float, longitude: float, radius_km: int = 10, limit: int = 20
) -> List[GeoapifyPlace]:
    """Search places using Geoapify"""
    async with GeoapifyClient() as client:
        return await client.search_places(
            query, latitude, longitude, radius_km, limit=limit
        )


async def geoapify_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    mode: str = "drive",
) -> Optional[GeoapifyRoute]:
    """Calculate route using Geoapify"""
    async with GeoapifyClient() as client:
        return await client.get_route(start_lat, start_lon, end_lat, end_lon, mode)
