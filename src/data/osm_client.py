"""
OpenStreetMap Overpass API Client
Provides free geographic and road network data from OpenStreetMap
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
class OSMPlace:
    """OpenStreetMap place data"""
    osm_id: str
    name: str
    latitude: float
    longitude: float
    place_type: str
    tags: Dict[str, Any]
    address: Optional[str] = None


@dataclass
class OSMRoad:
    """OpenStreetMap road data"""
    osm_id: str
    name: str
    highway_type: str
    coordinates: List[Tuple[float, float]]
    max_speed: Optional[int] = None
    lanes: Optional[int] = None
    tags: Dict[str, Any] = None


class OSMOverpassClient:
    """Client for OpenStreetMap Overpass API"""
    
    def __init__(self):
        self.config = real_data_config.data_sources["openstreetmap"]
        self.base_url = self.config.credentials.base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=self.config.rate_limits.concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.config.credentials.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, query: str) -> Dict[str, Any]:
        """Make a request to the Overpass API"""
        if not real_data_config.can_make_request("openstreetmap"):
            raise Exception("Rate limit exceeded for OpenStreetMap API")
        
        if not self.session:
            raise Exception("Session not initialized. Use async context manager.")
        
        url = f"{self.base_url}/interpreter"
        
        try:
            real_data_config.record_request("openstreetmap")
            
            async with self.session.post(url, data={"data": query}) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"OSM API request successful: {len(data.get('elements', []))} elements")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"OSM API error {response.status}: {error_text}")
                    raise Exception(f"OSM API error: {response.status}")
        
        except aiohttp.ClientError as e:
            logger.error(f"OSM API connection error: {e}")
            raise Exception(f"OSM API connection error: {e}")
    
    def _build_bbox_query(self, south: float, west: float, north: float, east: float) -> str:
        """Build a bounding box filter for Overpass queries"""
        return f"({south},{west},{north},{east})"
    
    def _build_radius_query(self, lat: float, lon: float, radius_meters: int) -> str:
        """Build a radius filter for Overpass queries"""
        return f"(around:{radius_meters},{lat},{lon})"
    
    async def get_places_in_area(self, south: float, west: float, north: float, east: float,
                               place_types: Optional[List[str]] = None) -> List[OSMPlace]:
        """Get places within a bounding box"""
        
        # Default place types to search for
        if place_types is None:
            place_types = [
                "amenity",
                "shop", 
                "tourism",
                "leisure",
                "office",
                "public_transport"
            ]
        
        bbox = self._build_bbox_query(south, west, north, east)
        
        # Build query for multiple place types
        type_filters = []
        for place_type in place_types:
            type_filters.append(f'node["{place_type}"]{bbox};')
            type_filters.append(f'way["{place_type}"]{bbox};')
        
        query = f"""
        [out:json][timeout:25];
        (
            {' '.join(type_filters)}
        );
        out center meta;
        """
        
        try:
            result = await self._make_request(query)
            places = []
            
            for element in result.get("elements", []):
                tags = element.get("tags", {})
                
                # Determine place type and name
                place_type = None
                name = tags.get("name", "Unknown")
                
                for ptype in place_types:
                    if ptype in tags:
                        place_type = f"{ptype}:{tags[ptype]}"
                        break
                
                if not place_type:
                    continue
                
                # Get coordinates
                if element.get("type") == "node":
                    lat, lon = element.get("lat"), element.get("lon")
                elif element.get("center"):
                    lat, lon = element["center"].get("lat"), element["center"].get("lon")
                else:
                    continue
                
                # Build address from tags
                address_parts = []
                for key in ["addr:housenumber", "addr:street", "addr:city"]:
                    if key in tags:
                        address_parts.append(tags[key])
                address = ", ".join(address_parts) if address_parts else None
                
                places.append(OSMPlace(
                    osm_id=f"{element['type']}/{element['id']}",
                    name=name,
                    latitude=lat,
                    longitude=lon,
                    place_type=place_type,
                    tags=tags,
                    address=address
                ))
            
            logger.info(f"Found {len(places)} places in area")
            return places
        
        except Exception as e:
            logger.error(f"Error fetching places from OSM: {e}")
            return []
    
    async def get_roads_in_area(self, south: float, west: float, north: float, east: float,
                              highway_types: Optional[List[str]] = None) -> List[OSMRoad]:
        """Get road network within a bounding box"""
        
        # Default highway types to include
        if highway_types is None:
            highway_types = [
                "motorway", "motorway_link",
                "trunk", "trunk_link", 
                "primary", "primary_link",
                "secondary", "secondary_link",
                "tertiary", "tertiary_link",
                "residential", "service"
            ]
        
        bbox = self._build_bbox_query(south, west, north, east)
        
        # Build highway type filter
        highway_filter = "|".join(highway_types)
        
        query = f"""
        [out:json][timeout:25];
        (
            way["highway"~"^({highway_filter})$"]{bbox};
        );
        out geom meta;
        """
        
        try:
            result = await self._make_request(query)
            roads = []
            
            for element in result.get("elements", []):
                if element.get("type") != "way":
                    continue
                
                tags = element.get("tags", {})
                highway_type = tags.get("highway", "unknown")
                name = tags.get("name", "Unnamed Road")
                
                # Extract coordinates
                coordinates = []
                for node in element.get("geometry", []):
                    coordinates.append((node["lat"], node["lon"]))
                
                if not coordinates:
                    continue
                
                # Extract road properties
                max_speed = None
                if "maxspeed" in tags:
                    try:
                        max_speed = int(tags["maxspeed"].replace("mph", "").replace("km/h", "").strip())
                    except (ValueError, AttributeError):
                        pass
                
                lanes = None
                if "lanes" in tags:
                    try:
                        lanes = int(tags["lanes"])
                    except (ValueError, TypeError):
                        pass
                
                roads.append(OSMRoad(
                    osm_id=f"way/{element['id']}",
                    name=name,
                    highway_type=highway_type,
                    coordinates=coordinates,
                    max_speed=max_speed,
                    lanes=lanes,
                    tags=tags
                ))
            
            logger.info(f"Found {len(roads)} roads in area")
            return roads
        
        except Exception as e:
            logger.error(f"Error fetching roads from OSM: {e}")
            return []
    
    async def search_places_by_name(self, name: str, lat: float, lon: float, 
                                  radius_km: int = 10) -> List[OSMPlace]:
        """Search for places by name within a radius"""
        
        radius_meters = radius_km * 1000
        radius_filter = self._build_radius_query(lat, lon, radius_meters)
        
        query = f"""
        [out:json][timeout:25];
        (
            node["name"~"{name}",i]{radius_filter};
            way["name"~"{name}",i]{radius_filter};
        );
        out center meta;
        """
        
        try:
            result = await self._make_request(query)
            places = []
            
            for element in result.get("elements", []):
                tags = element.get("tags", {})
                place_name = tags.get("name", "Unknown")
                
                # Get coordinates
                if element.get("type") == "node":
                    lat, lon = element.get("lat"), element.get("lon")
                elif element.get("center"):
                    lat, lon = element["center"].get("lat"), element["center"].get("lon")
                else:
                    continue
                
                # Determine place type
                place_type = "unknown"
                for key in ["amenity", "shop", "tourism", "leisure"]:
                    if key in tags:
                        place_type = f"{key}:{tags[key]}"
                        break
                
                places.append(OSMPlace(
                    osm_id=f"{element['type']}/{element['id']}",
                    name=place_name,
                    latitude=lat,
                    longitude=lon,
                    place_type=place_type,
                    tags=tags
                ))
            
            logger.info(f"Found {len(places)} places matching '{name}'")
            return places
        
        except Exception as e:
            logger.error(f"Error searching places in OSM: {e}")
            return []
    
    async def get_traffic_features(self, south: float, west: float, north: float, east: float) -> Dict[str, Any]:
        """Get traffic-related features like traffic lights, construction, etc."""
        
        bbox = self._build_bbox_query(south, west, north, east)
        
        query = f"""
        [out:json][timeout:25];
        (
            node["highway"="traffic_signals"]{bbox};
            node["barrier"]{bbox};
            way["construction"]{bbox};
            way["highway"="construction"]{bbox};
            relation["restriction"]{bbox};
        );
        out center meta;
        """
        
        try:
            result = await self._make_request(query)
            
            traffic_features = {
                "traffic_signals": [],
                "barriers": [],
                "construction": [],
                "restrictions": []
            }
            
            for element in result.get("elements", []):
                tags = element.get("tags", {})
                
                # Get coordinates
                if element.get("type") == "node":
                    lat, lon = element.get("lat"), element.get("lon")
                elif element.get("center"):
                    lat, lon = element["center"].get("lat"), element["center"].get("lon")
                else:
                    continue
                
                # Categorize traffic features
                if "highway" in tags and tags["highway"] == "traffic_signals":
                    traffic_features["traffic_signals"].append({
                        "osm_id": f"{element['type']}/{element['id']}",
                        "latitude": lat,
                        "longitude": lon,
                        "tags": tags
                    })
                elif "barrier" in tags:
                    traffic_features["barriers"].append({
                        "osm_id": f"{element['type']}/{element['id']}",
                        "latitude": lat,
                        "longitude": lon,
                        "barrier_type": tags["barrier"],
                        "tags": tags
                    })
                elif "construction" in tags or (tags.get("highway") == "construction"):
                    traffic_features["construction"].append({
                        "osm_id": f"{element['type']}/{element['id']}",
                        "latitude": lat,
                        "longitude": lon,
                        "construction_type": tags.get("construction", "unknown"),
                        "tags": tags
                    })
                elif element.get("type") == "relation" and "restriction" in tags:
                    traffic_features["restrictions"].append({
                        "osm_id": f"{element['type']}/{element['id']}",
                        "restriction_type": tags["restriction"],
                        "tags": tags
                    })
            
            logger.info(f"Found traffic features: {len(traffic_features['traffic_signals'])} signals, "
                       f"{len(traffic_features['barriers'])} barriers, "
                       f"{len(traffic_features['construction'])} construction")
            
            return traffic_features
        
        except Exception as e:
            logger.error(f"Error fetching traffic features from OSM: {e}")
            return {"traffic_signals": [], "barriers": [], "construction": [], "restrictions": []}
    
    async def health_check(self) -> bool:
        """Check if the OSM Overpass API is healthy"""
        try:
            # Simple query to test API availability
            query = "[out:json][timeout:5]; node(0); out;"
            
            if not self.session:
                async with self:
                    await self._make_request(query)
            else:
                await self._make_request(query)
            
            return True
        except Exception as e:
            logger.error(f"OSM health check failed: {e}")
            return False


# Convenience functions for easy usage
async def get_osm_places(south: float, west: float, north: float, east: float,
                        place_types: Optional[List[str]] = None) -> List[OSMPlace]:
    """Get OSM places in bounding box"""
    async with OSMOverpassClient() as client:
        return await client.get_places_in_area(south, west, north, east, place_types)


async def get_osm_roads(south: float, west: float, north: float, east: float,
                       highway_types: Optional[List[str]] = None) -> List[OSMRoad]:
    """Get OSM roads in bounding box"""
    async with OSMOverpassClient() as client:
        return await client.get_roads_in_area(south, west, north, east, highway_types)


async def search_osm_places(name: str, lat: float, lon: float, radius_km: int = 10) -> List[OSMPlace]:
    """Search OSM places by name"""
    async with OSMOverpassClient() as client:
        return await client.search_places_by_name(name, lat, lon, radius_km) 