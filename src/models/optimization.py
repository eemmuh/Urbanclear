"""
Route optimization algorithms for traffic management
"""

from typing import List, Dict, Any
import asyncio
import random
from datetime import datetime
from loguru import logger

from src.api.models import RouteRequest, RouteResponse, Route, RoutePoint, Location
from src.core.config import get_settings
from src.data.mock_data_generator import MockDataGenerator

# Create a global instance
_mock_generator = MockDataGenerator()


class RouteOptimizer:
    """Route optimization service using various algorithms"""

    def __init__(self):
        self.settings = get_settings()
        self.mock_generator = _mock_generator
        logger.info("RouteOptimizer initialized")

    async def optimize(self, route_request: RouteRequest) -> RouteResponse:
        """Optimize a route request and return the best route with alternatives"""
        start_time = datetime.now()

        waypoints = getattr(route_request, "waypoints", [])
        waypoint_count = len(waypoints) if waypoints else 0
        logger.info(
            f"Optimizing route from {route_request.origin} to "
            f"{route_request.destination} with {waypoint_count} waypoints"
        )

        # Convert dict to Location objects if needed
        # (for RouteOptimizationRequest compatibility)
        if isinstance(route_request.origin, dict):
            route_request.origin = Location(
                latitude=route_request.origin.get("lat", 0.0),
                longitude=route_request.origin.get("lng", 0.0),
                address="Origin",
            )

        if isinstance(route_request.destination, dict):
            route_request.destination = Location(
                latitude=route_request.destination.get("lat", 0.0),
                longitude=route_request.destination.get("lng", 0.0),
                address="Destination",
            )

        try:
            # Calculate the optimal route
            primary_route = await self._calculate_optimal_route(route_request)

            # Calculate alternative routes
            alternative_routes = await self._calculate_alternative_routes(
                route_request, num_alternatives=2
            )

            optimization_time = (datetime.now() - start_time).total_seconds()

            return RouteResponse(
                primary_route=primary_route,
                alternative_routes=alternative_routes,
                optimization_time=optimization_time,
                factors_considered=[
                    "current_traffic",
                    "historical_patterns",
                    "incidents",
                    "weather_conditions",
                ],
            )

        except Exception as e:
            logger.error(f"Error optimizing route: {e}")
            # Return a minimal fallback route
            return self._create_fallback_route(route_request)

    async def _calculate_optimal_route(self, request: RouteRequest) -> Route:
        """Calculate the optimal route"""
        # Mock route calculation - replace with actual algorithm
        await asyncio.sleep(0.1)  # Simulate processing time

        # Generate mock route points
        route_points = self._generate_route_points(
            request.origin, request.destination, 5  # Number of intermediate points
        )

        total_distance = sum(point.distance_from_start for point in route_points[-1:])
        total_time = sum(point.estimated_travel_time for point in route_points)

        return Route(
            points=route_points,
            total_distance=total_distance or 5.2,
            total_time=total_time or 18,
            total_fuel_cost=self._calculate_fuel_cost(total_distance or 5.2),
            toll_cost=0.0,  # No tolls for this route
            carbon_footprint=self._calculate_carbon_footprint(total_distance or 5.2),
            traffic_score=0.75,
        )

    async def _calculate_alternative_routes(
        self, request: RouteRequest, num_alternatives: int
    ) -> List[Route]:
        """Calculate alternative routes"""
        alternatives = []

        for i in range(num_alternatives):
            await asyncio.sleep(0.05)  # Simulate processing time

            # Generate slightly different routes
            route_points = self._generate_route_points(
                request.origin, request.destination, 4 + i  # Vary the number of points
            )

            # Add some variation to make alternatives different
            distance_modifier = 1.0 + (i * 0.2)
            time_modifier = 1.0 + (i * 0.15)

            total_distance = (
                sum(point.distance_from_start for point in route_points[-1:]) or 5.2
            ) * distance_modifier
            total_time = (
                sum(point.estimated_travel_time for point in route_points) or 18
            ) * time_modifier

            alternative = Route(
                points=route_points,
                total_distance=total_distance,
                total_time=int(total_time),
                total_fuel_cost=self._calculate_fuel_cost(total_distance),
                toll_cost=2.50 if i == 1 else 0.0,  # Second alternative has tolls
                carbon_footprint=self._calculate_carbon_footprint(total_distance),
                traffic_score=0.75 - (i * 0.1),
            )

            alternatives.append(alternative)

        return alternatives

    def _generate_route_points(
        self, origin: Location, destination: Location, num_points: int
    ) -> List[RoutePoint]:
        """Generate route points between origin and destination"""
        points = []

        # Calculate incremental changes
        lat_step = (destination.latitude - origin.latitude) / (num_points + 1)
        lng_step = (destination.longitude - origin.longitude) / (num_points + 1)

        cumulative_distance = 0.0
        cumulative_time = 0

        for i in range(num_points + 2):  # +2 to include origin and destination
            if i == 0:
                # Origin point
                lat, lng = origin.latitude, origin.longitude
                address = origin.address or "Origin"
            elif i == num_points + 1:
                # Destination point
                lat, lng = destination.latitude, destination.longitude
                address = destination.address or "Destination"
            else:
                # Intermediate points
                lat = origin.latitude + (lat_step * i)
                lng = origin.longitude + (lng_step * i)
                address = f"Route point {i}"

            # Calculate distance and time for this segment
            segment_distance = random.uniform(
                0.8, 1.5
            )  # Mock: 0.8-1.5 miles per segment
            segment_time = random.randint(2, 5)  # Mock: 2-5 minutes per segment

            cumulative_distance += segment_distance
            cumulative_time += segment_time

            point = RoutePoint(
                location=Location(latitude=lat, longitude=lng, address=address),
                estimated_travel_time=cumulative_time,
                distance_from_start=cumulative_distance,
            )

            points.append(point)

        return points

    def _calculate_fuel_cost(self, distance: float) -> float:
        """Calculate estimated fuel cost"""
        # Mock calculation: assume 25 mpg and $3.50/gallon
        mpg = 25.0
        gas_price = 3.50
        return (distance / mpg) * gas_price

    def _calculate_carbon_footprint(self, distance: float) -> float:
        """Calculate carbon footprint in kg CO2"""
        # Mock calculation: assume 0.89 lbs CO2 per mile
        co2_per_mile = 0.89  # lbs
        lbs_to_kg = 0.453592
        return distance * co2_per_mile * lbs_to_kg

    async def get_alternatives(
        self, origin: str, destination: str, max_alternatives: int
    ) -> List[Dict[str, Any]]:
        """Get alternative routes without full optimization"""
        logger.info(f"Getting {max_alternatives} alternative routes")

        # TODO: Implement actual alternative route finding
        alternatives = []

        for i in range(max_alternatives):
            alternative = {
                "route_id": f"alt_{i + 1}",
                "summary": f"Alternative route {i + 1}",
                "distance": 5.2 + (i * 0.5),
                "time": 18 + (i * 3),
                "traffic_level": ["low", "moderate", "high"][i % 3],
                "highlights": [
                    "Avoids downtown area" if i == 0 else "Uses highway",
                    "Scenic route" if i == 1 else "Fastest route",
                ],
            }
            alternatives.append(alternative)

        return alternatives

    def _create_fallback_route(self, route_request: RouteRequest) -> RouteResponse:
        """Create a basic fallback route when optimization fails"""
        # Convert dict to Location objects if needed
        if isinstance(route_request.origin, dict):
            origin = Location(
                latitude=route_request.origin.get("lat", 0.0),
                longitude=route_request.origin.get("lng", 0.0),
                address="Origin",
            )
        else:
            origin = route_request.origin

        if isinstance(route_request.destination, dict):
            destination = Location(
                latitude=route_request.destination.get("lat", 0.0),
                longitude=route_request.destination.get("lng", 0.0),
                address="Destination",
            )
        else:
            destination = route_request.destination

        fallback_points = [
            RoutePoint(
                location=origin,
                estimated_travel_time=0,
                distance_from_start=0.0,
            ),
            RoutePoint(
                location=destination,
                estimated_travel_time=15,
                distance_from_start=3.0,
            ),
        ]

        fallback_route = Route(
            points=fallback_points,
            total_distance=3.0,
            total_time=15,
            total_fuel_cost=0.50,
            toll_cost=0.0,
            carbon_footprint=1.2,
            traffic_score=0.7,
        )

        return RouteResponse(
            primary_route=fallback_route,
            alternative_routes=[],
            optimization_time=0.1,
            factors_considered=["basic_distance"],
        )
