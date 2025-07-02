"""
Urbanclear - Mock Data Generator for Realistic Traffic Simulation
"""
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import numpy as np
try:
    from api.models import (
        TrafficCondition, IncidentReport, TrafficSeverity, IncidentType, Location,
        TrafficPrediction, Route, RoutePoint, RouteResponse
    )
except ImportError:
    # Fallback for when running from different contexts
    from src.api.models import (
        TrafficCondition, IncidentReport, TrafficSeverity, IncidentType, Location,
        TrafficPrediction, Route, RoutePoint, RouteResponse
    )


@dataclass
class TrafficSensor:
    """Traffic sensor configuration"""
    id: str
    name: str
    location: Location
    baseline_speed: float
    max_volume: int
    road_type: str  # highway, arterial, local
    

class MockDataGenerator:
    """Generate realistic mock traffic data"""
    
    def __init__(self):
        self.sensors = self._initialize_sensors()
        self.incidents = []
        self.base_time = datetime.now()
        
    def _initialize_sensors(self) -> List[TrafficSensor]:
        """Initialize traffic sensors with realistic NYC locations"""
        sensors = [
            TrafficSensor(
                id="sensor_001",
                name="Central Park South & 5th Avenue",
                location=Location(latitude=40.7831, longitude=-73.9712, address="Central Park South & 5th Ave"),
                baseline_speed=25.0,
                max_volume=1800,
                road_type="arterial"
            ),
            TrafficSensor(
                id="sensor_002", 
                name="Times Square & Broadway",
                location=Location(latitude=40.7505, longitude=-73.9934, address="Times Square & Broadway"),
                baseline_speed=15.0,
                max_volume=2200,
                road_type="arterial"
            ),
            TrafficSensor(
                id="sensor_003",
                name="FDR Drive @ 42nd Street",
                location=Location(latitude=40.7505, longitude=-73.9681, address="FDR Drive northbound @ 42nd St"),
                baseline_speed=45.0,
                max_volume=3500,
                road_type="highway"
            ),
            TrafficSensor(
                id="sensor_004",
                name="Brooklyn Bridge Entrance",
                location=Location(latitude=40.7061, longitude=-73.9969, address="Brooklyn Bridge entrance"),
                baseline_speed=20.0,
                max_volume=2800,
                road_type="arterial"
            ),
            TrafficSensor(
                id="sensor_005",
                name="Lincoln Tunnel Approach",
                location=Location(latitude=40.7614, longitude=-73.9776, address="Lincoln Tunnel approach"),
                baseline_speed=18.0,
                max_volume=4200,
                road_type="highway"
            ),
            TrafficSensor(
                id="sensor_006",
                name="Central Park West & 72nd",
                location=Location(latitude=40.7767, longitude=-73.9761, address="Central Park West & 72nd St"),
                baseline_speed=30.0,
                max_volume=1500,
                road_type="local"
            ),
            TrafficSensor(
                id="sensor_007",
                name="Houston Street & Broadway",
                location=Location(latitude=40.7255, longitude=-73.9990, address="Houston Street & Broadway"),
                baseline_speed=22.0,
                max_volume=1900,
                road_type="arterial"
            ),
            TrafficSensor(
                id="sensor_008",
                name="Williamsburg Bridge",
                location=Location(latitude=40.7133, longitude=-73.9798, address="Williamsburg Bridge"),
                baseline_speed=35.0,
                max_volume=3200,
                road_type="highway"
            )
        ]
        return sensors
    
    def _get_time_factor(self) -> float:
        """Get traffic factor based on time of day"""
        now = datetime.now()
        hour = now.hour
        
        # Rush hour patterns
        if 7 <= hour <= 9:  # Morning rush
            return 0.4 + 0.3 * math.sin((hour - 7) * math.pi / 2)
        elif 17 <= hour <= 19:  # Evening rush
            return 0.3 + 0.4 * math.sin((hour - 17) * math.pi / 2)
        elif 10 <= hour <= 16:  # Daytime
            return 0.7 + 0.2 * random.random()
        elif 20 <= hour <= 23:  # Evening
            return 0.8 + 0.1 * random.random()
        else:  # Late night/early morning
            return 0.9 + 0.1 * random.random()
    
    def _get_day_factor(self) -> float:
        """Get traffic factor based on day of week"""
        weekday = datetime.now().weekday()
        if weekday < 5:  # Monday-Friday
            return 1.0
        elif weekday == 5:  # Saturday
            return 0.8
        else:  # Sunday
            return 0.6
    
    def _get_weather_factor(self) -> float:
        """Simulate weather impact on traffic"""
        # Randomly simulate different weather conditions
        weather_chance = random.random()
        if weather_chance < 0.7:  # Clear weather
            return 1.0
        elif weather_chance < 0.85:  # Light rain
            return 0.8
        elif weather_chance < 0.95:  # Heavy rain
            return 0.6
        else:  # Snow/severe weather
            return 0.4
    
    def generate_current_conditions(self, location_filter: Optional[str] = None) -> List[TrafficCondition]:
        """Generate current traffic conditions for all sensors"""
        conditions = []
        time_factor = self._get_time_factor()
        day_factor = self._get_day_factor() 
        weather_factor = self._get_weather_factor()
        
        for sensor in self.sensors:
            # Filter by location if specified
            if location_filter and location_filter.lower() not in sensor.name.lower():
                continue
                
            # Calculate realistic speed based on factors
            speed_reduction = (1 - time_factor) * (1 - day_factor) * (1 - weather_factor)
            current_speed = sensor.baseline_speed * (1 - speed_reduction) * (0.8 + 0.4 * random.random())
            current_speed = max(5.0, min(sensor.baseline_speed * 1.2, current_speed))
            
            # Calculate volume based on speed (inverse relationship)
            volume_factor = (sensor.baseline_speed - current_speed) / sensor.baseline_speed
            current_volume = int(sensor.max_volume * (0.3 + 0.7 * volume_factor) * time_factor * day_factor)
            
            # Calculate density (vehicles per mile)
            density = current_volume / max(current_speed, 1) * 0.5
            
            # Determine severity based on speed reduction
            speed_ratio = current_speed / sensor.baseline_speed
            if speed_ratio > 0.8:
                severity = TrafficSeverity.LOW
            elif speed_ratio > 0.6:
                severity = TrafficSeverity.MODERATE
            elif speed_ratio > 0.4:
                severity = TrafficSeverity.HIGH
            else:
                severity = TrafficSeverity.SEVERE
            
            # Calculate congestion level and travel time index
            congestion_level = max(0, min(1, (sensor.baseline_speed - current_speed) / sensor.baseline_speed))
            travel_time_index = max(1.0, sensor.baseline_speed / max(current_speed, 1))
            
            condition = TrafficCondition(
                id=sensor.id,
                location=sensor.location,
                timestamp=datetime.now(),
                speed_mph=round(current_speed, 1),
                volume=current_volume,
                density=round(density, 1),
                severity=severity,
                congestion_level=round(congestion_level, 2),
                travel_time_index=round(travel_time_index, 1)
            )
            conditions.append(condition)
        
        return conditions
    
    def generate_incidents(self) -> List[IncidentReport]:
        """Generate realistic traffic incidents"""
        # Clear old incidents periodically
        now = datetime.now()
        self.incidents = [inc for inc in self.incidents if (now - inc.reported_time).seconds < 3600]
        
        # Generate new incidents occasionally
        if random.random() < 0.1:  # 10% chance of new incident
            incident_types = [IncidentType.ACCIDENT, IncidentType.CONSTRUCTION, 
                            IncidentType.BREAKDOWN, IncidentType.ROAD_CLOSURE]
            incident_type = random.choice(incident_types)
            
            # Choose random sensor location
            sensor = random.choice(self.sensors)
            
            # Add some location variation
            lat_offset = (random.random() - 0.5) * 0.01
            lng_offset = (random.random() - 0.5) * 0.01
            
            incident_location = Location(
                latitude=sensor.location.latitude + lat_offset,
                longitude=sensor.location.longitude + lng_offset,
                address=f"{sensor.name} vicinity"
            )
            
            # Generate incident details based on type
            if incident_type == IncidentType.ACCIDENT:
                descriptions = [
                    "Multi-vehicle accident blocking lanes",
                    "Fender bender in right lane", 
                    "Vehicle rollover on shoulder",
                    "Emergency vehicles responding to crash"
                ]
                severity = random.choice([TrafficSeverity.MODERATE, TrafficSeverity.HIGH, TrafficSeverity.SEVERE])
                duration = random.randint(30, 120)
                lanes = random.randint(1, 3)
            elif incident_type == IncidentType.CONSTRUCTION:
                descriptions = [
                    "Lane closure for utility work",
                    "Road surface repair in progress",
                    "Bridge maintenance work",
                    "Traffic signal installation"
                ]
                severity = random.choice([TrafficSeverity.LOW, TrafficSeverity.MODERATE])
                duration = random.randint(120, 480)
                lanes = random.randint(1, 2)
            elif incident_type == IncidentType.BREAKDOWN:
                descriptions = [
                    "Disabled vehicle in travel lane",
                    "Vehicle with flat tire on shoulder",
                    "Overheated vehicle blocking lane",
                    "Stalled truck in right lane"
                ]
                severity = random.choice([TrafficSeverity.LOW, TrafficSeverity.MODERATE])
                duration = random.randint(15, 60)
                lanes = 1
            else:  # ROAD_CLOSURE
                descriptions = [
                    "Emergency road closure",
                    "Police investigation blocking road",
                    "Hazmat spill cleanup in progress",
                    "Temporary closure for special event"
                ]
                severity = TrafficSeverity.SEVERE
                duration = random.randint(60, 240)
                lanes = random.randint(2, 4)
            
            incident = IncidentReport(
                id=f"incident_{len(self.incidents) + 1:03d}",
                type=incident_type,
                location=incident_location,
                severity=severity,
                description=random.choice(descriptions),
                reported_time=now - timedelta(minutes=random.randint(0, 60)),
                estimated_duration=duration,
                lanes_affected=lanes,
                is_resolved=False,
                impact_radius=0.3 + random.random() * 0.7
            )
            
            self.incidents.append(incident)
        
        return self.incidents
    
    def generate_analytics_summary(self, period: str) -> Dict[str, Any]:
        """Generate realistic analytics summary"""
        # Base metrics that vary by period
        period_multipliers = {
            "1h": 1,
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30
        }
        
        multiplier = period_multipliers.get(period, 24)
        
        # Generate realistic metrics with some randomness
        base_vehicles_per_hour = 5200
        total_vehicles = int(base_vehicles_per_hour * multiplier * (0.8 + 0.4 * random.random()))
        
        # Average speed varies by time and conditions
        avg_speed = 28.5 + random.random() * 10 - 5
        
        # Incidents scale with time period
        congestion_incidents = int(2 * multiplier * random.random())
        resolved_incidents = int(congestion_incidents * 0.85)
        
        # Environmental benefits
        fuel_savings = total_vehicles * 0.02 * random.random()
        time_savings = int(total_vehicles * 0.12 * random.random())
        emission_reduction = fuel_savings * 19.6  # lbs CO2 per gallon
        
        # System efficiency (higher during off-peak)
        hour = datetime.now().hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            efficiency = 0.65 + 0.15 * random.random()
        else:
            efficiency = 0.75 + 0.2 * random.random()
        
        return {
            "period": period,
            "total_vehicles": total_vehicles,
            "average_speed": round(avg_speed, 1),
            "congestion_incidents": congestion_incidents,
            "resolved_incidents": resolved_incidents,
            "fuel_savings": round(fuel_savings, 1),
            "time_savings": time_savings,
            "emission_reduction": round(emission_reduction, 1),
            "system_efficiency": round(efficiency, 2),
            "peak_congestion_hours": [8, 9, 17, 18, 19]
        }

    def generate_traffic_predictions(self, location: str, hours_ahead: int) -> List[TrafficPrediction]:
        """Generate realistic traffic predictions"""
        predictions = []
        
        # Find closest sensor to the location
        base_sensor = self.sensors[0]  # Default to first sensor
        for sensor in self.sensors:
            if location.lower() in sensor.name.lower():
                base_sensor = sensor
                break
        
        for hour in range(1, hours_ahead + 1):
            prediction_time = datetime.now() + timedelta(hours=hour)
            hour_of_day = prediction_time.hour
            
            # Predict speed based on time patterns
            if hour_of_day in [8, 9, 17, 18, 19]:  # Rush hours
                predicted_speed = base_sensor.baseline_speed * 0.6
                predicted_volume = int(base_sensor.max_volume * 1.2)
                severity = TrafficSeverity.HIGH
            elif hour_of_day in [10, 11, 12, 13, 14, 15, 16]:  # Daytime
                predicted_speed = base_sensor.baseline_speed * 0.8
                predicted_volume = int(base_sensor.max_volume * 0.8)
                severity = TrafficSeverity.MODERATE
            else:  # Night/early morning
                predicted_speed = base_sensor.baseline_speed * 1.1
                predicted_volume = int(base_sensor.max_volume * 0.4)
                severity = TrafficSeverity.LOW
            
            # Add some randomness
            predicted_speed *= (0.9 + 0.2 * random.random())
            predicted_volume = int(predicted_volume * (0.8 + 0.4 * random.random()))
            
            prediction = TrafficPrediction(
                location=base_sensor.location,
                prediction_time=prediction_time,
                predicted_speed=round(predicted_speed, 1),
                predicted_volume=predicted_volume,
                predicted_severity=severity,
                confidence=0.9 - (hour * 0.05),  # Confidence decreases with time
                factors=self._get_prediction_factors(hour_of_day)
            )
            predictions.append(prediction)
        
        return predictions
    
    def _get_prediction_factors(self, hour: int) -> List[str]:
        """Get factors affecting the prediction"""
        factors = ["historical_patterns", "time_of_day"]
        
        if hour in [8, 9, 17, 18, 19]:
            factors.append("rush_hour")
        
        if random.random() < 0.3:
            factors.append("weather_impact")
        
        if random.random() < 0.1:
            factors.append("special_event")
        
        return factors

    def generate_route_data(self, origin: Location, destination: Location) -> Dict[str, Any]:
        """Generate realistic route data"""
        # Calculate basic route metrics
        lat_diff = destination.latitude - origin.latitude
        lng_diff = destination.longitude - origin.longitude
        
        # Estimate distance using Haversine formula (simplified)
        distance = math.sqrt(lat_diff**2 + lng_diff**2) * 69  # Rough miles conversion
        distance = max(1.0, distance)  # Minimum 1 mile
        
        # Generate route points
        num_points = min(8, max(3, int(distance * 2)))  # 2 points per mile, max 8
        route_points = []
        
        cumulative_distance = 0.0
        cumulative_time = 0
        
        for i in range(num_points):
            # Interpolate between origin and destination
            progress = i / (num_points - 1) if num_points > 1 else 0
            
            lat = origin.latitude + (lat_diff * progress)
            lng = origin.longitude + (lng_diff * progress)
            
            if i == 0:
                address = origin.address or "Starting point"
            elif i == num_points - 1:
                address = destination.address or "Destination"
            else:
                address = f"Via point {i}"
            
            # Calculate segment metrics
            segment_distance = distance / (num_points - 1) if num_points > 1 else distance
            segment_speed = 25 + random.uniform(-5, 10)  # 20-35 mph average
            segment_time = (segment_distance / segment_speed) * 60  # Convert to minutes
            
            cumulative_distance += segment_distance
            cumulative_time += segment_time
            
            point = RoutePoint(
                location=Location(
                    latitude=round(lat, 6),
                    longitude=round(lng, 6),
                    address=address
                ),
                estimated_travel_time=int(cumulative_time),
                distance_from_start=round(cumulative_distance, 1)
            )
            route_points.append(point)
        
        return {
            "points": route_points,
            "total_distance": round(distance, 1),
            "total_time": int(cumulative_time),
            "traffic_score": random.uniform(0.6, 0.9)
        }


# Global instance for the app
mock_generator = MockDataGenerator() 