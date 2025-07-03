"""
Kafka producer for real-time traffic data streaming
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
from loguru import logger
import pandas as pd
from src.core.config import get_settings


class TrafficDataProducer:
    """Kafka producer for traffic data streaming"""
    
    def __init__(self):
        self.settings = get_settings()
        self.producer = None
        self.is_connected = False
        self.topics = {
            'traffic_data': 'traffic-data',
            'incidents': 'traffic-incidents',
            'predictions': 'traffic-predictions',
            'alerts': 'traffic-alerts'
        }
    
    async def connect(self):
        """Connect to Kafka cluster"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.settings.kafka.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None,
                acks=self.settings.kafka.producer.acks,
                retries=self.settings.kafka.producer.retries,
                compression_type='gzip',
                batch_size=16384,
                linger_ms=100,
                buffer_memory=33554432
            )
            self.is_connected = True
            logger.info("Connected to Kafka cluster")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.is_connected = False
    
    async def send_traffic_data(self, sensor_data: Dict[str, Any]) -> bool:
        """Send traffic sensor data to Kafka"""
        if not self.is_connected:
            await self.connect()
        
        try:
            # Add metadata
            message = {
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'traffic_sensor',
                'data': sensor_data,
                'schema_version': '1.0'
            }
            
            # Use sensor_id as partition key for ordered processing
            key = sensor_data.get('sensor_id')
            
            future = self.producer.send(
                self.topics['traffic_data'],
                value=message,
                key=key
            )
            
            # Wait for delivery
            record_metadata = future.get(timeout=10)
            logger.debug(f"Sent traffic data to partition {record_metadata.partition}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send traffic data: {e}")
            return False
    
    async def send_incident_alert(self, incident_data: Dict[str, Any]) -> bool:
        """Send incident alert to Kafka"""
        if not self.is_connected:
            await self.connect()
        
        try:
            message = {
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'incident_detector',
                'alert_type': 'traffic_incident',
                'priority': incident_data.get('severity', 'medium'),
                'data': incident_data,
                'schema_version': '1.0'
            }
            
            future = self.producer.send(
                self.topics['incidents'],
                value=message,
                key=incident_data.get('id')
            )
            
            record_metadata = future.get(timeout=10)
            logger.info(f"Sent incident alert: {incident_data.get('id')}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send incident alert: {e}")
            return False
    
    async def send_prediction_data(self, prediction_data: Dict[str, Any]) -> bool:
        """Send prediction data to Kafka"""
        if not self.is_connected:
            await self.connect()
        
        try:
            message = {
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'traffic_predictor',
                'prediction_horizon': prediction_data.get('hours_ahead', 1),
                'data': prediction_data,
                'schema_version': '1.0'
            }
            
            future = self.producer.send(
                self.topics['predictions'],
                value=message,
                key=prediction_data.get('location')
            )
            
            record_metadata = future.get(timeout=10)
            logger.debug(f"Sent prediction data for {prediction_data.get('location')}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send prediction data: {e}")
            return False
    
    async def send_batch_data(self, data_batch: List[Dict[str, Any]], topic: str) -> int:
        """Send batch of data to specified topic"""
        if not self.is_connected:
            await self.connect()
        
        sent_count = 0
        for data in data_batch:
            try:
                message = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'batch_processor',
                    'data': data,
                    'schema_version': '1.0'
                }
                
                self.producer.send(topic, value=message)
                sent_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send batch item: {e}")
        
        # Flush to ensure all messages are sent
        self.producer.flush()
        logger.info(f"Sent {sent_count}/{len(data_batch)} items to {topic}")
        return sent_count
    
    async def close(self):
        """Close producer connection"""
        if self.producer:
            self.producer.close()
            self.is_connected = False
            logger.info("Kafka producer closed")


class StreamingMetrics:
    """Metrics for streaming operations"""
    
    def __init__(self):
        self.messages_sent = 0
        self.messages_failed = 0
        self.bytes_sent = 0
        self.start_time = datetime.utcnow()
    
    def record_success(self, message_size: int):
        """Record successful message send"""
        self.messages_sent += 1
        self.bytes_sent += message_size
    
    def record_failure(self):
        """Record failed message send"""
        self.messages_failed += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics"""
        runtime = (datetime.utcnow() - self.start_time).total_seconds()
        return {
            'messages_sent': self.messages_sent,
            'messages_failed': self.messages_failed,
            'bytes_sent': self.bytes_sent,
            'runtime_seconds': runtime,
            'messages_per_second': self.messages_sent / runtime if runtime > 0 else 0,
            'success_rate': self.messages_sent / (self.messages_sent + self.messages_failed) if (self.messages_sent + self.messages_failed) > 0 else 0
        }


# Example usage and testing
async def main():
    """Example usage of TrafficDataProducer"""
    producer = TrafficDataProducer()
    
    # Sample traffic data
    sample_data = {
        'sensor_id': 'sensor_001',
        'location': {
            'latitude': 40.7831,
            'longitude': -73.9712,
            'address': 'Central Park South & 5th Ave'
        },
        'speed': 25.5,
        'volume': 1200,
        'density': 48.0,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Send data
    success = await producer.send_traffic_data(sample_data)
    if success:
        logger.info("Successfully sent traffic data")
    
    await producer.close()


if __name__ == "__main__":
    asyncio.run(main()) 