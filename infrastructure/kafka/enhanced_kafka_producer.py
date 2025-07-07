#!/usr/bin/env python3
"""
Enhanced Kafka Producer for Urbanclear Traffic System
Streams real-time traffic data to multiple topics with realistic simulation
"""

import asyncio
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrafficEvent:
    """Traffic event data structure"""
    event_id: str
    timestamp: str
    event_type: str
    location: Dict[str, Any]
    data: Dict[str, Any]
    source: str = "urbanclear-sensor"


class EnhancedKafkaProducer:
    """Enhanced Kafka producer for real-time traffic data streaming"""
    
    def __init__(self, bootstrap_servers: List[str] = None):
        self.bootstrap_servers = bootstrap_servers or ['localhost:9092']
        self.running = False
        
        # Topic configuration
        self.topics = {
            'traffic-data': {
                'description': 'Real-time traffic flow data',
                'interval': 5  # seconds
            },
            'incidents': {
                'description': 'Traffic incidents and alerts',
                'interval': 30  # seconds
            },
            'predictions': {
                'description': 'ML model predictions',
                'interval': 60  # seconds
            }
        }
        
        # Event counters
        self.event_counters = {topic: 0 for topic in self.topics.keys()}
        self.start_time = time.time()
    
    async def start(self):
        """Start the Kafka producer"""
        try:
            logger.info(f"Kafka producer started (simulated)")
            self.running = True
            
            # Start streaming tasks for each topic
            tasks = []
            for topic_name, topic_config in self.topics.items():
                task = asyncio.create_task(
                    self._stream_topic_data(topic_name, topic_config)
                )
                tasks.append(task)
            
            # Start monitoring task
            monitor_task = asyncio.create_task(self._monitor_producer())
            tasks.append(monitor_task)
            
            # Wait for all tasks
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Error starting Kafka producer: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop the Kafka producer"""
        self.running = False
        logger.info("Kafka producer stopped")
    
    async def _stream_topic_data(self, topic_name: str, topic_config: Dict[str, Any]):
        """Stream data to a specific topic"""
        logger.info(f"Starting data stream for topic: {topic_name}")
        
        while self.running:
            try:
                # Generate mock events
                events = await self._generate_mock_events(topic_name)
                
                # Simulate sending events
                for event in events:
                    logger.debug(f"Sending to {topic_name}: {event['event_id']}")
                    self.event_counters[topic_name] += 1
                
                # Wait for next interval
                await asyncio.sleep(topic_config['interval'])
                
            except Exception as e:
                logger.error(f"Error streaming to topic {topic_name}: {e}")
                await asyncio.sleep(10)
    
    async def _generate_mock_events(self, topic_name: str) -> List[Dict[str, Any]]:
        """Generate mock events for testing"""
        events = []
        
        if topic_name == 'traffic-data':
            # Generate traffic events
            locations = ['Central Park', 'Times Square', 'Brooklyn Bridge']
            for location in locations:
                event = TrafficEvent(
                    event_id=f"traffic_{int(time.time())}_{location.replace(' ', '_')}",
                    timestamp=datetime.now().isoformat(),
                    event_type="traffic_measurement",
                    location={"name": location},
                    data={
                        "speed_mph": random.uniform(15, 50),
                        "volume": random.randint(500, 2000),
                        "congestion_level": random.uniform(0.3, 0.9)
                    }
                )
                events.append(asdict(event))
        
        elif topic_name == 'incidents':
            # Generate incident events occasionally
            if random.random() < 0.3:
                event = {
                    "incident_id": f"incident_{int(time.time())}",
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "incident_report",
                    "location": {"name": random.choice(['FDR Drive', 'Lincoln Tunnel'])},
                    "severity": random.choice(['low', 'moderate', 'high']),
                    "description": "Traffic incident detected"
                }
                events.append(event)
        
        elif topic_name == 'predictions':
            # Generate prediction events
            models = ['traffic_flow_predictor', 'route_optimizer']
            for model in models:
                event = {
                    "prediction_id": f"pred_{model}_{int(time.time())}",
                    "timestamp": datetime.now().isoformat(),
                    "model_type": model,
                    "prediction_data": {
                        "predicted_value": random.uniform(0.5, 1.0),
                        "confidence": random.uniform(0.8, 0.95)
                    }
                }
                events.append(event)
        
        return events
    
    async def _monitor_producer(self):
        """Monitor producer performance"""
        while self.running:
            try:
                total_events = sum(self.event_counters.values())
                runtime = time.time() - self.start_time
                events_per_second = total_events / runtime if runtime > 0 else 0
                
                logger.info(f"Producer Stats - Total: {total_events}, Rate: {events_per_second:.2f}/s")
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in monitoring: {e}")
                await asyncio.sleep(30)


async def main():
    """Main function"""
    producer = EnhancedKafkaProducer()
    
    try:
        await producer.start()
    except KeyboardInterrupt:
        logger.info("Producer interrupted by user")
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main()) 