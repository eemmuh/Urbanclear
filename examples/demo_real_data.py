#!/usr/bin/env python3
"""
Real Data Integration Demo Script
Demonstrates the new real data capabilities of the traffic management system
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Optional
import httpx


class RealDataDemo:
    """Demo class for testing real data integration"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
    
    def print_section(self, title: str):
        """Print a formatted section header"""
        print(f"\n{'='*60}")
        print(f" {title}")
        print('='*60)
    
    def print_result(self, data: dict, title: str = "Result"):
        """Print formatted JSON result"""
        print(f"\n{title}:")
        print(json.dumps(data, indent=2, default=str))
    
    async def check_api_health(self):
        """Check if the API is running"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print(" API is healthy and running")
                return True
            else:
                print(f" API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f" Could not connect to API: {e}")
            return False
    
    async def demo_geocoding(self):
        """Demonstrate geocoding functionality"""
        self.print_section("GEOCODING DEMO")
        
        test_addresses = [
            "Times Square, New York, NY",
            "Golden Gate Bridge, San Francisco, CA",
            "1600 Pennsylvania Avenue, Washington, DC"
        ]
        
        for address in test_addresses:
            try:
                print(f"\n Geocoding: {address}")
                
                response = await self.client.post(
                    f"{self.base_url}/api/v1/real-data/geocode",
                    params={"address": address}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data["success"]:
                        result = data["data"]
                        print(f" Found: {result.get('formatted_address', 'Unknown')}")
                        print(f"    Coordinates: {result.get('latitude', 0):.6f}, {result.get('longitude', 0):.6f}")
                        print(f"     Source: {data['source']} (Quality: {data['quality']})")
                        print(f"    Cache hit: {data['cache_hit']}")
                    else:
                        print(" Geocoding failed")
                else:
                    print(f" API error: {response.status_code}")
                    
            except Exception as e:
                print(f" Error geocoding {address}: {e}")
    
    async def demo_routing(self):
        """Demonstrate routing functionality"""
        self.print_section("ROUTING DEMO")
        
        test_routes = [
            {
                "name": "NYC: Times Square to Central Park",
                "start": (40.7589, -73.9851),
                "end": (40.7829, -73.9654)
            },
            {
                "name": "SF: Golden Gate to Lombard Street",
                "start": (37.8199, -122.4783),
                "end": (37.8021, -122.4187)
            }
        ]
        
        for route in test_routes:
            try:
                print(f"\n  Calculating route: {route['name']}")
                start_lat, start_lon = route["start"]
                end_lat, end_lon = route["end"]
                
                response = await self.client.post(
                    f"{self.base_url}/api/v1/real-data/route",
                    params={
                        "start_lat": start_lat,
                        "start_lon": start_lon,
                        "end_lat": end_lat,
                        "end_lon": end_lon,
                        "mode": "drive"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data["success"]:
                        route_info = data["route"]
                        print(f" Route calculated successfully")
                        print(f"    Distance: {route_info['distance_meters']/1000:.2f} km")
                        print(f"     Duration: {route_info['duration_seconds']/60:.1f} minutes")
                        print(f"     Source: {data['source']} (Quality: {data['quality']})")
                        print(f"    Summary: {route_info['summary']}")
                        print(f"    Steps: {len(route_info['steps'])} navigation instructions")
                        
                        if route_info.get('warnings'):
                            print(f"     Warnings: {len(route_info['warnings'])}")
                    else:
                        print(" Route calculation failed")
                else:
                    print(f" API error: {response.status_code}")
                    
            except Exception as e:
                print(f" Error calculating route {route['name']}: {e}")
    
    async def demo_places_search(self):
        """Demonstrate places search functionality"""
        self.print_section("PLACES SEARCH DEMO")
        
        test_searches = [
            {
                "query": "coffee shop",
                "location": (40.7614, -73.9776),  # NYC
                "city": "New York"
            },
            {
                "query": "gas station",
                "location": (37.7749, -122.4194),  # SF
                "city": "San Francisco"
            }
        ]
        
        for search in test_searches:
            try:
                print(f"\n Searching for '{search['query']}' near {search['city']}")
                lat, lon = search["location"]
                
                response = await self.client.get(
                    f"{self.base_url}/api/v1/real-data/places/search",
                    params={
                        "query": search["query"],
                        "latitude": lat,
                        "longitude": lon,
                        "radius_km": 5,
                        "limit": 10
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data["success"]:
                        places = data["places"]
                        print(f" Found {data['count']} places")
                        
                        for i, place in enumerate(places[:3]):  # Show first 3
                            print(f"   {i+1}. {place['name']}")
                            print(f"       {place['address'] or 'Address not available'}")
                            print(f"        Categories: {', '.join(place['categories'])}")
                            if place['distance']:
                                print(f"       Distance: {place['distance']:.0f}m")
                            print(f"       Source: {place['source']}")
                    else:
                        print(" Places search failed")
                else:
                    print(f" API error: {response.status_code}")
                    
            except Exception as e:
                print(f" Error searching places: {e}")
    
    async def demo_matrix(self):
        """Demonstrate matrix calculation"""
        self.print_section("TRAFFIC MATRIX DEMO")
        
        # Test with NYC locations
        locations = [
            (40.7589, -73.9851),  # Times Square
            (40.7829, -73.9654),  # Central Park
            (40.7614, -73.9776),  # Grand Central
            (40.7505, -73.9934)   # Empire State Building
        ]
        
        location_names = ["Times Square", "Central Park", "Grand Central", "Empire State"]
        
        try:
            print("\n  Calculating traffic matrix for NYC locations:")
            for i, name in enumerate(location_names):
                print(f"   {i}: {name}")
            
            # Format locations as string
            locations_str = ";".join([f"{lat},{lon}" for lat, lon in locations])
            
            response = await self.client.get(
                f"{self.base_url}/api/v1/real-data/matrix",
                params={"locations": locations_str}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    matrix_data = data["matrix"]
                    print(f" Matrix calculated successfully")
                    print(f"     Source: {data['source']} (Quality: {data['quality']})")
                    print(f"    Cache hit: {data['cache_hit']}")
                    
                    # Show duration matrix (first few entries)
                    if "durations" in matrix_data and matrix_data["durations"]:
                        print(f"\n     Duration Matrix (seconds):")
                        durations = matrix_data["durations"]
                        for i in range(min(3, len(durations))):
                            for j in range(min(3, len(durations[i]))):
                                print(f"     {location_names[i]} → {location_names[j]}: {durations[i][j]:.0f}s")
                else:
                    print(" Matrix calculation failed")
            else:
                print(f" API error: {response.status_code}")
                
        except Exception as e:
            print(f" Error calculating matrix: {e}")
    
    async def demo_isochrones(self):
        """Demonstrate isochrone calculation"""
        self.print_section("ISOCHRONES DEMO")
        
        test_location = (40.7589, -73.9851)  # Times Square
        time_values = [15, 30]  # 15 and 30 minutes
        
        try:
            print(f"\n Calculating {time_values} minute isochrones from Times Square")
            
            response = await self.client.get(
                f"{self.base_url}/api/v1/real-data/isochrones",
                params={
                    "latitude": test_location[0],
                    "longitude": test_location[1],
                    "time_minutes": ",".join(map(str, time_values)),
                    "mode": "drive"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    isochrones = data["isochrones"]
                    print(f" Isochrones calculated successfully")
                    print(f"     Source: {data['source']} (Quality: {data['quality']})")
                    print(f"    Cache hit: {data['cache_hit']}")
                    print(f"    Time values: {data['time_minutes']} minutes")
                    print(f"    Mode: {data['mode']}")
                    print(f"    Generated {len(isochrones)} isochrone zones")
                    
                    for i, iso in enumerate(isochrones):
                        if isinstance(iso, dict) and 'value' in iso:
                            print(f"     Zone {i+1}: {iso['value']:.0f} min reachable area")
                            if 'area_sqm' in iso:
                                print(f"              Area: {iso['area_sqm']/1000000:.2f} km²")
                else:
                    print(" Isochrone calculation failed")
            else:
                print(f" API error: {response.status_code}")
                
        except Exception as e:
            print(f" Error calculating isochrones: {e}")
    
    async def demo_health_status(self):
        """Demonstrate health status check"""
        self.print_section("REAL DATA HEALTH STATUS")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/real-data/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f" Overall Health: {data['overall_health'].upper()}")
                print(f" Timestamp: {data['timestamp']}")
                
                if "sources" in data:
                    print(f"\n Data Sources Status:")
                    for source, status in data["sources"].items():
                        health_icon = "" if status.get("healthy", False) else ""
                        available_icon = "" if status.get("available", False) else ""
                        print(f"   {health_icon} {source.title()}")
                        print(f"      Available: {available_icon}")
                        if "rate_limit_remaining" in status:
                            print(f"      Rate limit: {status['rate_limit_remaining']} requests remaining")
                        if "error" in status:
                            print(f"      Error: {status['error']}")
                
                if "error" in data:
                    print(f"\n Error: {data['error']}")
            else:
                print(f" API error: {response.status_code}")
                
        except Exception as e:
            print(f" Error checking health status: {e}")
    
    async def run_full_demo(self):
        """Run the complete demonstration"""
        print(" Starting Real Data Integration Demo")
        print(f" API Base URL: {self.base_url}")
        print(f" Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check API health first
        if not await self.check_api_health():
            print("\n Cannot proceed - API is not available")
            print("Make sure the API server is running with: python start_api.py")
            return
        
        # Run all demos
        await self.demo_health_status()
        await self.demo_geocoding()
        await self.demo_routing()
        await self.demo_places_search()
        await self.demo_matrix()
        await self.demo_isochrones()
        
        self.print_section("DEMO COMPLETED")
        print(" Real Data Integration Demo completed successfully!")
        print("\n Summary:")
        print("   - Geocoding: Convert addresses to coordinates")
        print("   - Routing: Calculate real routes between points")
        print("   - Places: Search for businesses and points of interest")
        print("   - Matrix: Calculate travel times between multiple locations")
        print("   - Isochrones: Find reachable areas within time limits")
        print("   - Health: Monitor data source availability and performance")
        print("\n Next Steps:")
        print("   1. Set up API keys for premium data sources (optional)")
        print("   2. Configure Redis for better caching performance")
        print("   3. Integrate real data into your frontend applications")
        print("   4. Monitor usage and performance with the health endpoints")


async def main():
    """Main demo function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Real Data Integration Demo")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000", 
        help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--test",
        choices=["geocoding", "routing", "places", "matrix", "isochrones", "health"],
        help="Run only a specific test"
    )
    
    args = parser.parse_args()
    
    async with RealDataDemo(args.url) as demo:
        if args.test:
            # Run specific test
            test_method = getattr(demo, f"demo_{args.test}")
            await demo.check_api_health()
            await test_method()
        else:
            # Run full demo
            await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main()) 