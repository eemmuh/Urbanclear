"""
Real-time metrics publisher for Urbanclear Traffic System.
Streams traffic metrics to Prometheus for dashboard visualization.
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, start_http_server, push_to_gateway
import threading

from .mock_data_generator import MockDataGenerator

logger = logging.getLogger(__name__)

class MetricsPublisher:
    """Real-time metrics publisher for traffic system monitoring"""
    
    def __init__(self, port: int = 8001, push_gateway_url: Optional[str] = None):
        self.port = port
        self.push_gateway_url = push_gateway_url
        self.registry = CollectorRegistry()
        self.mock_generator = MockDataGenerator()
        self.running = False
        
        # Initialize Prometheus metrics
        self._setup_metrics()
        
    def _setup_metrics(self):
        """Setup Prometheus metrics"""
        # Traffic flow metrics
        self.traffic_flow_rate = Gauge(
            'traffic_flow_rate',
            'Current traffic flow rate by location and direction',
            ['location', 'direction'],
            registry=self.registry
        )
        
        # Congestion metrics
        self.congestion_level = Gauge(
            'congestion_level',
            'Current congestion level (0-1) by location',
            ['location'],
            registry=self.registry
        )
        
        # Incident metrics
        self.active_incidents_total = Gauge(
            'active_incidents_total',
            'Number of active incidents by severity',
            ['severity'],
            registry=self.registry
        )
        
        # Prediction accuracy metrics
        self.prediction_accuracy = Gauge(
            'prediction_accuracy',
            'ML model prediction accuracy',
            ['model_type'],
            registry=self.registry
        )
        
        # Route optimization metrics
        self.route_optimization_seconds = Histogram(
            'route_optimization_seconds',
            'Time taken for route optimization requests',
            registry=self.registry
        )
        
        # System performance metrics
        self.api_requests_total = Counter(
            'api_requests_total',
            'Total API requests by endpoint and status',
            ['endpoint', 'status'],
            registry=self.registry
        )
        
        # Weather impact metrics
        self.weather_impact_factor = Gauge(
            'weather_impact_factor',
            'Current weather impact on traffic (0-2)',
            ['weather_condition'],
            registry=self.registry
        )
        
    async def start_publishing(self):
        """Start publishing metrics"""
        self.running = True
        logger.info(f"Starting metrics publisher on port {self.port}")
        
        # Start Prometheus HTTP server in a separate thread
        server_thread = threading.Thread(
            target=lambda: start_http_server(self.port, registry=self.registry)
        )
        server_thread.daemon = True
        server_thread.start()
        
        # Start metrics publishing loop
        await self._publish_loop()
        
    async def stop_publishing(self):
        """Stop publishing metrics"""
        self.running = False
        logger.info("Stopping metrics publisher")
        
    async def _publish_loop(self):
        """Main publishing loop"""
        while self.running:
            try:
                # Update traffic flow metrics
                await self._update_traffic_metrics()
                
                # Update incident metrics
                await self._update_incident_metrics()
                
                # Update prediction metrics
                await self._update_prediction_metrics()
                
                # Update system performance metrics
                await self._update_system_metrics()
                
                # Sleep for 5 seconds before next update
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in metrics publishing loop: {e}")
                await asyncio.sleep(10)  # Wait longer on error
                
    async def _update_traffic_metrics(self):
        """Update traffic flow and congestion metrics"""
        try:
            # Get current traffic data
            traffic_data = self.mock_generator.generate_real_time_data()
            
            for sensor in traffic_data['sensors']:
                location = sensor['location']
                
                # Update flow rate metrics
                self.traffic_flow_rate.labels(
                    location=location,
                    direction='northbound'
                ).set(sensor['flow_rate'] * random.uniform(0.8, 1.2))
                
                self.traffic_flow_rate.labels(
                    location=location,
                    direction='southbound'
                ).set(sensor['flow_rate'] * random.uniform(0.7, 1.1))
                
                # Update congestion metrics
                congestion = min(sensor['congestion_level'], 1.0)
                self.congestion_level.labels(location=location).set(congestion)
                
            # Update weather impact
            weather_conditions = ['clear', 'rain', 'snow', 'fog']
            for condition in weather_conditions:
                if condition == 'clear':
                    impact = random.uniform(0.9, 1.1)
                elif condition == 'rain':
                    impact = random.uniform(1.2, 1.5)
                elif condition == 'snow':
                    impact = random.uniform(1.5, 2.0)
                else:  # fog
                    impact = random.uniform(1.1, 1.3)
                    
                self.weather_impact_factor.labels(weather_condition=condition).set(impact)
                
        except Exception as e:
            logger.error(f"Error updating traffic metrics: {e}")
            
    async def _update_incident_metrics(self):
        """Update incident-related metrics"""
        try:
            # Simulate different incident severities
            severity_counts = {
                'low': random.randint(0, 3),
                'medium': random.randint(0, 2),
                'high': random.randint(0, 1),
                'critical': random.randint(0, 1) if random.random() < 0.1 else 0
            }
            
            for severity, count in severity_counts.items():
                self.active_incidents_total.labels(severity=severity).set(count)
                
        except Exception as e:
            logger.error(f"Error updating incident metrics: {e}")
            
    async def _update_prediction_metrics(self):
        """Update ML model prediction accuracy metrics"""
        try:
            model_accuracies = {
                'traffic_flow_predictor': random.uniform(0.82, 0.95),
                'route_optimizer': random.uniform(0.78, 0.92),
                'incident_detector': random.uniform(0.85, 0.97),
                'signal_optimizer': random.uniform(0.75, 0.88)
            }
            
            for model_type, accuracy in model_accuracies.items():
                self.prediction_accuracy.labels(model_type=model_type).set(accuracy)
                
        except Exception as e:
            logger.error(f"Error updating prediction metrics: {e}")
            
    async def _update_system_metrics(self):
        """Update system performance metrics"""
        try:
            # Simulate route optimization timing
            optimization_time = random.uniform(0.1, 2.5)
            self.route_optimization_seconds.observe(optimization_time)
            
            # Simulate API request metrics
            endpoints = ['traffic_current', 'analytics_summary', 'predictions', 'optimization']
            statuses = ['200', '400', '500']
            
            for endpoint in endpoints:
                for status in statuses:
                    # Most requests should be successful
                    if status == '200':
                        count = random.randint(50, 200)
                    elif status == '400':
                        count = random.randint(1, 10)
                    else:  # 500
                        count = random.randint(0, 5)
                        
                    # Note: Counter increment is not exposed, so we'll track separately
                    # In a real implementation, this would be incremented by actual API calls
                    
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
            
    def push_metrics(self):
        """Push metrics to Pushgateway if configured"""
        if self.push_gateway_url:
            try:
                push_to_gateway(
                    self.push_gateway_url,
                    job='urbanclear_traffic_system',
                    registry=self.registry
                )
                logger.debug("Metrics pushed to gateway successfully")
            except Exception as e:
                logger.error(f"Error pushing metrics to gateway: {e}")

class MetricsServer:
    """Standalone metrics server runner"""
    
    def __init__(self, port: int = 8001):
        self.publisher = MetricsPublisher(port=port)
        self.loop = None
        
    def start(self):
        """Start the metrics server in a separate thread"""
        def run_server():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.publisher.start_publishing())
            
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        return server_thread
        
    def stop(self):
        """Stop the metrics server"""
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.publisher.stop_publishing(),
                self.loop
            )

# Convenience function for standalone usage
def start_metrics_server(port: int = 8001) -> MetricsServer:
    """Start a standalone metrics server"""
    server = MetricsServer(port)
    server.start()
    return server

if __name__ == "__main__":
    # Example usage
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    
    print(f"Starting Urbanclear Metrics Publisher on port {port}")
    print("Metrics available at: http://localhost:{}/metrics".format(port))
    print("Press Ctrl+C to stop")
    
    server = start_metrics_server(port)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping metrics server...")
        server.stop()
        print("Stopped.") 