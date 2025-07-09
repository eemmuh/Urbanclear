"""
OpenRouteService API Client
Provides free routing and isochrones based on OpenStreetMap data
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
class ORSRoute:
    """OpenRouteService route data"""
    distance_meters: float
    duration_seconds: float
    ascent_meters: Optional[float]
    descent_meters: Optional[float]
    geometry: List[Tuple[float, float]]
    steps: List[Dict[str, Any]]
    summary: str
    warnings: List[str] = None


@dataclass
class ORSMatrix:
    """OpenRouteService matrix data"""
    durations: List[List[float]]  # Duration matrix
    distances: List[List[float]]  # Distance matrix
    sources: List[Tuple[float, float]]
    destinations: List[Tuple[float, float]]


@dataclass
class ORSIsochrone:
    """OpenRouteService isochrone data"""
    center: Tuple[float, float]
    value: float  # Time or distance value
    area_sqm: float
    geometry: Dict[str, Any]  # GeoJSON geometry
    properties: Dict[str, Any]


class OpenRouteServiceClient:
    """Client for OpenRouteService API"""
    
    def __init__(self):
        self.config = real_data_config.data_sources["openrouteservice"]
        self.base_url = self.config.credentials.base_url
        self.api_key = self.config.credentials.api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("No OpenRouteService API key provided. Service will be disabled.")
    
    async def __aenter__(self):
        """Async context manager entry"""
        if not self.api_key:
            raise Exception("OpenRouteService API key not configured")
        
        connector = aiohttp.TCPConnector(limit=self.config.rate_limits.concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        headers = self.config.credentials.headers.copy()
        headers["Authorization"] = self.api_key
        headers["Content-Type"] = "application/json"
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, method: str = "POST", 
                          data: Optional[Dict[str, Any]] = None,
                          params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the OpenRouteService API"""
        if not real_data_config.can_make_request("openrouteservice"):
            raise Exception("Rate limit exceeded for OpenRouteService API")
        
        if not self.session:
            raise Exception("Session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            real_data_config.record_request("openrouteservice")
            
            if method.upper() == "POST":
                async with self.session.post(url, json=data, params=params) as response:
                    return await self._handle_response(response, endpoint)
            else:
                async with self.session.get(url, params=params) as response:
                    return await self._handle_response(response, endpoint)
        
        except aiohttp.ClientError as e:
            logger.error(f"OpenRouteService API connection error: {e}")
            raise Exception(f"OpenRouteService API connection error: {e}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse, endpoint: str) -> Dict[str, Any]:
        """Handle API response"""
        if response.status == 200:
            data = await response.json()
            logger.info(f"OpenRouteService API request successful: {endpoint}")
            return data
        else:
            error_text = await response.text()
            logger.error(f"OpenRouteService API error {response.status}: {error_text}")
            raise Exception(f"OpenRouteService API error: {response.status}")
    
    async def get_directions(self, coordinates: List[Tuple[float, float]],
                           profile: str = "driving-car",
                           format_type: str = "json",
                           instructions: bool = True,
                           geometry: bool = True,
                           elevation: bool = False) -> Optional[ORSRoute]:
        """Get directions between multiple points"""
        
        # Convert coordinates to [lon, lat] format for ORS
        coords = [[lon, lat] for lat, lon in coordinates]
        
        data = {
            "coordinates": coords,
            "format": format_type,
            "instructions": instructions,
            "geometry": geometry,
            "elevation": elevation
        }
        
        try:
            result = await self._make_request(f"/v2/directions/{profile}", data=data)
            
            if "routes" not in result or not result["routes"]:
                return None
            
            route_data = result["routes"][0]
            summary = route_data.get("summary", {})
            
            # Extract geometry
            geometry_coords = []
            if "geometry" in route_data:
                # Decode geometry if it's encoded
                if isinstance(route_data["geometry"], str):
                    geometry_coords = self._decode_polyline(route_data["geometry"])
                else:
                    # Already decoded coordinates
                    geometry_coords = [(coord[1], coord[0]) for coord in route_data["geometry"]]
            
            # Extract steps
            steps = []
            for segment in route_data.get("segments", []):
                for step in segment.get("steps", []):
                    steps.append({
                        "instruction": step.get("instruction", ""),
                        "distance": step.get("distance", 0),
                        "duration": step.get("duration", 0),
                        "type": step.get("type", 0),
                        "name": step.get("name", "")
                    })
            
            # Extract warnings
            warnings = []
            for segment in route_data.get("segments", []):
                warnings.extend(segment.get("warnings", []))
            
            return ORSRoute(
                distance_meters=summary.get("distance", 0),
                duration_seconds=summary.get("duration", 0),
                ascent_meters=summary.get("ascent"),
                descent_meters=summary.get("descent"),
                geometry=geometry_coords,
                steps=steps,
                summary=f"{summary.get('distance', 0)/1000:.1f} km, {summary.get('duration', 0)/60:.0f} min",
                warnings=[w.get("message", "") for w in warnings]
            )
        
        except Exception as e:
            logger.error(f"Error getting directions from OpenRouteService: {e}")
            return None
    
    async def get_matrix(self, locations: List[Tuple[float, float]],
                       profile: str = "driving-car",
                       sources: Optional[List[int]] = None,
                       destinations: Optional[List[int]] = None,
                       metrics: List[str] = None) -> Optional[ORSMatrix]:
        """Get distance/duration matrix between locations"""
        
        if metrics is None:
            metrics = ["distance", "duration"]
        
        # Convert coordinates to [lon, lat] format
        coords = [[lon, lat] for lat, lon in locations]
        
        data = {
            "locations": coords,
            "metrics": metrics
        }
        
        if sources is not None:
            data["sources"] = sources
        if destinations is not None:
            data["destinations"] = destinations
        
        try:
            result = await self._make_request(f"/v2/matrix/{profile}", data=data)
            
            # Extract source and destination coordinates
            source_coords = []
            dest_coords = []
            
            if sources is not None:
                source_coords = [locations[i] for i in sources]
            else:
                source_coords = locations
            
            if destinations is not None:
                dest_coords = [locations[i] for i in destinations]
            else:
                dest_coords = locations
            
            return ORSMatrix(
                durations=result.get("durations", []),
                distances=result.get("distances", []),
                sources=source_coords,
                destinations=dest_coords
            )
        
        except Exception as e:
            logger.error(f"Error getting matrix from OpenRouteService: {e}")
            return None
    
    async def get_isochrones(self, locations: List[Tuple[float, float]],
                           range_values: List[float],
                           range_type: str = "time",
                           profile: str = "driving-car",
                           interval: Optional[float] = None) -> List[ORSIsochrone]:
        """Get isochrones (reachable areas) for locations"""
        
        # Convert coordinates to [lon, lat] format
        coords = [[lon, lat] for lat, lon in locations]
        
        data = {
            "locations": coords,
            "range": range_values,
            "range_type": range_type  # "time" or "distance"
        }
        
        if interval:
            data["interval"] = interval
        
        try:
            result = await self._make_request(f"/v2/isochrones/{profile}", data=data)
            
            isochrones = []
            for feature in result.get("features", []):
                properties = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                
                # Extract center coordinates
                center_coords = properties.get("center", [0, 0])
                center = (center_coords[1], center_coords[0])  # Convert to lat, lon
                
                isochrones.append(ORSIsochrone(
                    center=center,
                    value=properties.get("value", 0),
                    area_sqm=properties.get("area", 0),
                    geometry=geometry,
                    properties=properties
                ))
            
            logger.info(f"Generated {len(isochrones)} isochrones")
            return isochrones
        
        except Exception as e:
            logger.error(f"Error getting isochrones from OpenRouteService: {e}")
            return []
    
    async def get_pois(self, request_type: str, geometry: Dict[str, Any],
                      filters: Optional[Dict[str, Any]] = None,
                      limit: int = 200) -> List[Dict[str, Any]]:
        """Get Points of Interest using OpenRouteService"""
        
        data = {
            "request": request_type,  # "pois", "stats", "list"
            "geometry": geometry
        }
        
        if filters:
            data["filters"] = filters
        
        if limit:
            data["limit"] = limit
        
        try:
            result = await self._make_request("/pois", data=data)
            
            pois = []
            for feature in result.get("features", []):
                properties = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coordinates = geometry.get("coordinates", [0, 0])
                
                pois.append({
                    "osm_id": properties.get("osm_id"),
                    "name": properties.get("osm_tags", {}).get("name", "Unknown"),
                    "latitude": coordinates[1],
                    "longitude": coordinates[0],
                    "category": properties.get("category_ids", {}).get("category_name", "unknown"),
                    "tags": properties.get("osm_tags", {}),
                    "distance": properties.get("distance")
                })
            
            logger.info(f"Found {len(pois)} POIs")
            return pois
        
        except Exception as e:
            logger.error(f"Error getting POIs from OpenRouteService: {e}")
            return []
    
    async def optimize_route(self, jobs: List[Dict[str, Any]], 
                           vehicles: List[Dict[str, Any]],
                           options: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Solve Vehicle Routing Problem using OpenRouteService optimization"""
        
        data = {
            "jobs": jobs,
            "vehicles": vehicles
        }
        
        if options:
            data["options"] = options
        
        try:
            result = await self._make_request("/optimization", data=data)
            logger.info("Route optimization completed successfully")
            return result
        
        except Exception as e:
            logger.error(f"Error optimizing route with OpenRouteService: {e}")
            return None
    
    def _decode_polyline(self, encoded: str) -> List[Tuple[float, float]]:
        """Decode polyline string to coordinates"""
        # Simple polyline decoder - for production use proper library
        coords = []
        index = 0
        lat = 0
        lng = 0
        
        while index < len(encoded):
            b = 0
            shift = 0
            result = 0
            
            # Decode latitude
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            
            dlat = ~(result >> 1) if result & 1 else result >> 1
            lat += dlat
            
            shift = 0
            result = 0
            
            # Decode longitude
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            
            dlng = ~(result >> 1) if result & 1 else result >> 1
            lng += dlng
            
            coords.append((lat / 1e5, lng / 1e5))
        
        return coords
    
    async def health_check(self) -> bool:
        """Check if the OpenRouteService API is healthy"""
        try:
            # Simple route request to test API
            coords = [(40.7589, -73.9851), (40.7614, -73.9776)]  # NYC area
            await self.get_directions(coords)
            return True
        except Exception as e:
            logger.error(f"OpenRouteService health check failed: {e}")
            return False


# Convenience functions for easy usage
async def ors_route(coordinates: List[Tuple[float, float]], 
                   profile: str = "driving-car") -> Optional[ORSRoute]:
    """Get route using OpenRouteService"""
    async with OpenRouteServiceClient() as client:
        return await client.get_directions(coordinates, profile)


async def ors_matrix(locations: List[Tuple[float, float]], 
                    profile: str = "driving-car") -> Optional[ORSMatrix]:
    """Get distance/duration matrix using OpenRouteService"""
    async with OpenRouteServiceClient() as client:
        return await client.get_matrix(locations, profile)


async def ors_isochrones(locations: List[Tuple[float, float]], 
                        range_minutes: List[float],
                        profile: str = "driving-car") -> List[ORSIsochrone]:
    """Get isochrones using OpenRouteService"""
    async with OpenRouteServiceClient() as client:
        return await client.get_isochrones(locations, range_minutes, "time", profile)


async def ors_pois_nearby(latitude: float, longitude: float, 
                         radius_meters: int = 1000) -> List[Dict[str, Any]]:
    """Get POIs near location using OpenRouteService"""
    geometry = {
        "bbox": [
            [longitude - 0.01, latitude - 0.01],
            [longitude + 0.01, latitude + 0.01]
        ],
        "geojson": {
            "type": "Point",
            "coordinates": [longitude, latitude]
        },
        "buffer": radius_meters
    }
    
    async with OpenRouteServiceClient() as client:
        return await client.get_pois("pois", geometry) 