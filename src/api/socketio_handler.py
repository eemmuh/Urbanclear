"""
Socket.io handler for real-time traffic updates
Compatible with React dashboard Socket.io client
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any
import socketio
from loguru import logger

from src.data.mock_data_generator import MockDataGenerator


class SocketIOHandler:
    """Socket.io handler for real-time updates"""

    def __init__(self):
        self.sio = socketio.AsyncServer(
            cors_allowed_origins="*",
            async_mode='asgi'
        )
        self.data_generator = MockDataGenerator()
        self.setup_handlers()

    def setup_handlers(self):
        """Setup Socket.io event handlers"""

        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection"""
            logger.info(f"Socket.io client {sid} connected")
            await self.sio.emit('connect_success', {'sid': sid}, room=sid)

        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            logger.info(f"Socket.io client {sid} disconnected")

        @self.sio.event
        async def subscribe(sid, data):
            """Handle topic subscription"""
            topic = data.get('topic')
            if topic:
                await self.sio.emit('subscription_success', {'topic': topic}, room=sid)
                logger.info(f"Client {sid} subscribed to {topic}")

        @self.sio.event
        async def unsubscribe(sid, data):
            """Handle topic unsubscription"""
            topic = data.get('topic')
            if topic:
                await self.sio.emit('unsubscription_success', {'topic': topic}, room=sid)
                logger.info(f"Client {sid} unsubscribed from {topic}")

        @self.sio.event
        async def ping(sid):
            """Handle ping request"""
            await self.sio.emit('pong', {
                'timestamp': datetime.now().isoformat()
            }, room=sid)

    async def start_data_streaming(self):
        """Start streaming real-time data to all connected clients"""
        logger.info("Starting Socket.io data streaming")

        while True:
            try:
                # Generate and broadcast traffic data
                traffic_data = await self._generate_traffic_update()
                await self.sio.emit('traffic_update', traffic_data)

                # Generate and broadcast incident data
                incident_data = await self._generate_incident_update()
                await self.sio.emit('incident_alert', incident_data)

                # Generate and broadcast prediction data
                prediction_data = await self._generate_prediction_update()
                await self.sio.emit('prediction_update', prediction_data)

                # Generate and broadcast system status
                system_status = await self._generate_system_status()
                await self.sio.emit('system_status', system_status)

                await asyncio.sleep(5)  # Update every 5 seconds

            except Exception as e:
                logger.error(f"Error in Socket.io data streaming: {e}")
                await asyncio.sleep(10)  # Wait longer on error

    async def _generate_traffic_update(self) -> Dict[str, Any]:
        """Generate real-time traffic update"""
        traffic_conditions = self.data_generator.generate_traffic_conditions(count=8)

        return {
            "type": "traffic_update",
            "data": {
                "sensors": [
                    {
                        "id": f"sensor_{i}",
                        "location": condition["location"]["address"],
                        "coordinates": {
                            "lat": condition["location"]["latitude"],
                            "lon": condition["location"]["longitude"],
                        },
                        "speed": condition["speed_mph"],
                        "volume": condition["volume"],
                        "congestion_level": condition["congestion_level"],
                        "flow_rate": condition["volume"] * condition["speed_mph"] / 60,
                    }
                    for i, condition in enumerate(traffic_conditions)
                ]
            },
            "timestamp": datetime.now().isoformat(),
        }

    async def _generate_incident_update(self) -> Dict[str, Any]:
        """Generate incident update"""
        incidents = self.data_generator.generate_incidents()

        return {
            "type": "incident_alert",
            "data": {
                "incidents": [
                    {
                        "id": incident.id,
                        "type": incident.type,
                        "location": incident.location.address,
                        "severity": incident.severity,
                        "status": "active" if not incident.is_resolved else "resolved",
                        "estimated_duration": incident.estimated_duration,
                        "coordinates": {
                            "lat": incident.location.latitude,
                            "lon": incident.location.longitude,
                        },
                    }
                    for incident in incidents
                ]
            },
            "timestamp": datetime.now().isoformat(),
        }

    async def _generate_prediction_update(self) -> Dict[str, Any]:
        """Generate prediction update"""
        predictions = self.data_generator.generate_traffic_predictions(
            location="Times Square", hours_ahead=6
        )

        return {
            "type": "prediction_update",
            "data": {
                "predictions": [
                    {
                        "timestamp": pred.prediction_time.isoformat(),
                        "location": pred.location.address,
                        "predicted_speed": pred.predicted_speed,
                        "predicted_volume": pred.predicted_volume,
                        "confidence": pred.confidence,
                        "congestion_forecast": pred.predicted_severity,
                    }
                    for pred in predictions
                ]
            },
            "timestamp": datetime.now().isoformat(),
        }

    async def _generate_system_status(self) -> Dict[str, Any]:
        """Generate system status update"""
        # Get active connections count safely
        try:
            active_connections = len(self.sio.rooms) if hasattr(self.sio, 'rooms') else 0
        except:
            active_connections = 0
            
        return {
            "type": "system_status",
            "data": {
                "status": "healthy",
                "active_connections": active_connections,
                "uptime": "00:15:30",
                "last_update": datetime.now().isoformat(),
                "system_metrics": {
                    "cpu_usage": 45.2,
                    "memory_usage": 67.8,
                    "api_requests_per_minute": 120,
                    "websocket_connections": active_connections,
                }
            },
            "timestamp": datetime.now().isoformat(),
        }


# Global Socket.io handler instance
socketio_handler = SocketIOHandler() 