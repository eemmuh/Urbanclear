"""
WebSocket handler for real-time traffic updates
"""

import asyncio
import json
from typing import Dict, Set, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import redis.asyncio as redis
from loguru import logger

from src.data.mock_data_generator import MockDataGenerator


class WebSocketMessage(BaseModel):
    """WebSocket message structure"""

    type: str
    data: Dict
    timestamp: str
    source: str = "urbanclear"


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> set of connection_ids
        self.redis_client: Optional[redis.Redis] = None
        self.data_generator = MockDataGenerator()

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()
        logger.info(f"WebSocket client {client_id} connected")

    async def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
        logger.info(f"WebSocket client {client_id} disconnected")

    async def subscribe(self, client_id: str, topic: str):
        """Subscribe client to a topic"""
        if client_id not in self.subscriptions:
            self.subscriptions[client_id] = set()
        self.subscriptions[client_id].add(topic)
        logger.info(f"Client {client_id} subscribed to {topic}")

    async def unsubscribe(self, client_id: str, topic: str):
        """Unsubscribe client from a topic"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].discard(topic)
        logger.info(f"Client {client_id} unsubscribed from {topic}")

    async def send_personal_message(self, message: str, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                await self.disconnect(client_id)

    async def broadcast_to_topic(self, topic: str, message: WebSocketMessage):
        """Broadcast message to all clients subscribed to topic"""
        message_json = message.model_dump_json()

        disconnected_clients = []
        for client_id, websocket in self.active_connections.items():
            if (
                client_id in self.subscriptions
                and topic in self.subscriptions[client_id]
            ):
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)

    async def broadcast_to_all(self, message: WebSocketMessage):
        """Broadcast message to all connected clients"""
        message_json = message.model_dump_json()

        disconnected_clients = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)

    async def start_data_streaming(self):
        """Start streaming real-time data"""
        logger.info("Starting real-time data streaming")

        while True:
            try:
                # Generate traffic data
                traffic_data = await self._generate_traffic_update()
                await self.broadcast_to_topic("traffic", traffic_data)

                # Generate incident data
                incident_data = await self._generate_incident_update()
                await self.broadcast_to_topic("incidents", incident_data)

                # Generate prediction data
                prediction_data = await self._generate_prediction_update()
                await self.broadcast_to_topic("predictions", prediction_data)

                await asyncio.sleep(5)  # Update every 5 seconds

            except Exception as e:
                logger.error(f"Error in data streaming: {e}")
                await asyncio.sleep(10)  # Wait longer on error

    async def _generate_traffic_update(self) -> WebSocketMessage:
        """Generate real-time traffic update"""
        traffic_conditions = self.data_generator.generate_traffic_conditions(count=8)

        return WebSocketMessage(
            type="traffic_update",
            data={
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
            timestamp=datetime.now().isoformat(),
        )

    async def _generate_incident_update(self) -> WebSocketMessage:
        """Generate incident update"""
        incidents = self.data_generator.generate_incidents()

        return WebSocketMessage(
            type="incident_update",
            data={
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
            timestamp=datetime.now().isoformat(),
        )

    async def _generate_prediction_update(self) -> WebSocketMessage:
        """Generate prediction update"""
        predictions = self.data_generator.generate_traffic_predictions(
            location="Times Square", hours_ahead=6
        )

        return WebSocketMessage(
            type="prediction_update",
            data={
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
            timestamp=datetime.now().isoformat(),
        )


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket, client_id)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Handle different message types
            if message_data.get("type") == "subscribe":
                topic = message_data.get("topic")
                if topic:
                    await manager.subscribe(client_id, topic)
                    await manager.send_personal_message(
                        json.dumps({"type": "subscription_success", "topic": topic}),
                        client_id,
                    )

            elif message_data.get("type") == "unsubscribe":
                topic = message_data.get("topic")
                if topic:
                    await manager.unsubscribe(client_id, topic)
                    await manager.send_personal_message(
                        json.dumps({"type": "unsubscription_success", "topic": topic}),
                        client_id,
                    )

            elif message_data.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps(
                        {"type": "pong", "timestamp": datetime.now().isoformat()}
                    ),
                    client_id,
                )

    except WebSocketDisconnect:
        await manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await manager.disconnect(client_id)


async def start_background_streaming():
    """Start background data streaming"""
    await manager.start_data_streaming()
