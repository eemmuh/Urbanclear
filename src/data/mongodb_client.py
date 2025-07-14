"""
MongoDB Client for Urbanclear Traffic System
Handles document-based storage for logs, analytics, and unstructured data
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from loguru import logger

try:
    from src.core.config import get_settings
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.core.config import get_settings


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AnalyticsEventType(str, Enum):
    """Analytics event types"""
    TRAFFIC_DATA = "traffic_data"
    INCIDENT_REPORT = "incident_report"
    ROUTE_OPTIMIZATION = "route_optimization"
    SIGNAL_OPTIMIZATION = "signal_optimization"
    PREDICTION_REQUEST = "prediction_request"
    API_REQUEST = "api_request"
    SYSTEM_EVENT = "system_event"
    USER_ACTION = "user_action"


@dataclass
class LogEntry:
    """Log entry structure"""
    timestamp: datetime
    level: LogLevel
    service: str
    message: str
    details: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None


@dataclass
class AnalyticsEvent:
    """Analytics event structure"""
    event_type: AnalyticsEventType
    timestamp: datetime
    service: str
    data: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None


class MongoDBClient:
    """MongoDB client for document storage"""

    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collections = {}
        self._connected = False

    async def connect(self) -> bool:
        """Connect to MongoDB"""
        try:
            mongo_config = self.settings.database.mongodb
            
            # Build connection string
            if mongo_config.username and mongo_config.password:
                connection_string = (
                    f"mongodb://{mongo_config.username}:{mongo_config.password}@"
                    f"{mongo_config.host}:{mongo_config.port}/{mongo_config.database}"
                    "?authSource=admin"
                )
            else:
                connection_string = (
                    f"mongodb://{mongo_config.host}:{mongo_config.port}/{mongo_config.database}"
                )

            # Create client with connection pooling
            self.client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                maxPoolSize=10,
                minPoolSize=1
            )

            # Test connection
            self.client.admin.command('ping')
            
            # Get database
            self.db = self.client[mongo_config.database]
            
            # Initialize collections
            await self._initialize_collections()
            
            self._connected = True
            logger.info("MongoDB connected successfully")
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection failed: {e}")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected MongoDB error: {e}")
            self._connected = False
            return False

    async def _initialize_collections(self):
        """Initialize MongoDB collections with indexes"""
        try:
            # Logs collection
            self.collections['logs'] = self.db['logs']
            self.collections['logs'].create_index([
                ("timestamp", DESCENDING),
                ("level", ASCENDING),
                ("service", ASCENDING)
            ])
            self.collections['logs'].create_index([
                ("service", ASCENDING),
                ("timestamp", DESCENDING)
            ])

            # Analytics collection
            self.collections['analytics'] = self.db['analytics']
            self.collections['analytics'].create_index([
                ("timestamp", DESCENDING),
                ("event_type", ASCENDING)
            ])
            self.collections['analytics'].create_index([
                ("event_type", ASCENDING),
                ("timestamp", DESCENDING)
            ])

            # Sensor logs collection
            self.collections['sensor_logs'] = self.db['sensor_logs']
            self.collections['sensor_logs'].create_index([
                ("timestamp", DESCENDING),
                ("sensor_id", ASCENDING)
            ])

            # Incident logs collection
            self.collections['incident_logs'] = self.db['incident_logs']
            self.collections['incident_logs'].create_index([
                ("timestamp", DESCENDING),
                ("incident_type", ASCENDING)
            ])

            # API logs collection
            self.collections['api_logs'] = self.db['api_logs']
            self.collections['api_logs'].create_index([
                ("timestamp", DESCENDING),
                ("endpoint", ASCENDING)
            ])

            # System logs collection
            self.collections['system_logs'] = self.db['system_logs']
            self.collections['system_logs'].create_index([
                ("timestamp", DESCENDING),
                ("component", ASCENDING)
            ])

            logger.info("MongoDB collections initialized with indexes")

        except Exception as e:
            logger.error(f"Failed to initialize MongoDB collections: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("MongoDB disconnected")

    def is_connected(self) -> bool:
        """Check if connected to MongoDB"""
        return self._connected

    async def log_entry(self, log_entry: LogEntry) -> bool:
        """Store a log entry"""
        if not self._connected:
            logger.warning("MongoDB not connected, skipping log entry")
            return False

        try:
            document = {
                "timestamp": log_entry.timestamp,
                "level": log_entry.level.value,
                "service": log_entry.service,
                "message": log_entry.message,
                "details": log_entry.details,
                "user_id": log_entry.user_id,
                "session_id": log_entry.session_id,
                "request_id": log_entry.request_id,
                "ip_address": log_entry.ip_address
            }

            result = self.collections['logs'].insert_one(document)
            return bool(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to store log entry: {e}")
            return False

    async def log_analytics_event(self, event: AnalyticsEvent) -> bool:
        """Store an analytics event"""
        if not self._connected:
            logger.warning("MongoDB not connected, skipping analytics event")
            return False

        try:
            document = {
                "event_type": event.event_type.value,
                "timestamp": event.timestamp,
                "service": event.service,
                "data": event.data,
                "user_id": event.user_id,
                "session_id": event.session_id,
                "location": event.location,
                "metadata": event.metadata
            }

            result = self.collections['analytics'].insert_one(document)
            return bool(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to store analytics event: {e}")
            return False

    async def store_sensor_log(self, sensor_id: str, data: Dict[str, Any]) -> bool:
        """Store sensor-specific log data"""
        if not self._connected:
            return False

        try:
            document = {
                "sensor_id": sensor_id,
                "timestamp": datetime.now(),
                "data": data
            }

            result = self.collections['sensor_logs'].insert_one(document)
            return bool(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to store sensor log: {e}")
            return False

    async def store_incident_log(self, incident_id: str, data: Dict[str, Any]) -> bool:
        """Store incident-specific log data"""
        if not self._connected:
            return False

        try:
            document = {
                "incident_id": incident_id,
                "timestamp": datetime.now(),
                "data": data
            }

            result = self.collections['incident_logs'].insert_one(document)
            return bool(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to store incident log: {e}")
            return False

    async def store_api_log(self, endpoint: str, method: str, data: Dict[str, Any]) -> bool:
        """Store API-specific log data"""
        if not self._connected:
            return False

        try:
            document = {
                "endpoint": endpoint,
                "method": method,
                "timestamp": datetime.now(),
                "data": data
            }

            result = self.collections['api_logs'].insert_one(document)
            return bool(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to store API log: {e}")
            return False

    async def store_system_log(self, component: str, data: Dict[str, Any]) -> bool:
        """Store system-specific log data"""
        if not self._connected:
            return False

        try:
            document = {
                "component": component,
                "timestamp": datetime.now(),
                "data": data
            }

            result = self.collections['system_logs'].insert_one(document)
            return bool(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to store system log: {e}")
            return False

    async def get_logs(
        self,
        service: Optional[str] = None,
        level: Optional[LogLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve logs with filters"""
        if not self._connected:
            return []

        try:
            query = {}
            
            if service:
                query["service"] = service
            if level:
                query["level"] = level.value
            if start_time or end_time:
                query["timestamp"] = {}
                if start_time:
                    query["timestamp"]["$gte"] = start_time
                if end_time:
                    query["timestamp"]["$lte"] = end_time

            cursor = self.collections['logs'].find(
                query,
                sort=[("timestamp", DESCENDING)]
            ).limit(limit)

            return list(cursor)

        except Exception as e:
            logger.error(f"Failed to retrieve logs: {e}")
            return []

    async def get_analytics_events(
        self,
        event_type: Optional[AnalyticsEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve analytics events with filters"""
        if not self._connected:
            return []

        try:
            query = {}
            
            if event_type:
                query["event_type"] = event_type.value
            if start_time or end_time:
                query["timestamp"] = {}
                if start_time:
                    query["timestamp"]["$gte"] = start_time
                if end_time:
                    query["timestamp"]["$lte"] = end_time

            cursor = self.collections['analytics'].find(
                query,
                sort=[("timestamp", DESCENDING)]
            ).limit(limit)

            return list(cursor)

        except Exception as e:
            logger.error(f"Failed to retrieve analytics events: {e}")
            return []

    async def get_analytics_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics summary with aggregations"""
        if not self._connected:
            return {}

        try:
            match_stage = {}
            if start_time or end_time:
                match_stage["timestamp"] = {}
                if start_time:
                    match_stage["timestamp"]["$gte"] = start_time
                if end_time:
                    match_stage["timestamp"]["$lte"] = end_time

            pipeline = [
                {"$match": match_stage} if match_stage else {"$match": {}},
                {
                    "$group": {
                        "_id": "$event_type",
                        "count": {"$sum": 1},
                        "last_event": {"$max": "$timestamp"}
                    }
                },
                {"$sort": {"count": DESCENDING}}
            ]

            results = list(self.collections['analytics'].aggregate(pipeline))
            
            summary = {
                "total_events": sum(r["count"] for r in results),
                "events_by_type": {r["_id"]: r["count"] for r in results},
                "period": {
                    "start": start_time.isoformat() if start_time else None,
                    "end": end_time.isoformat() if end_time else None
                }
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            return {}

    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to prevent database bloat"""
        if not self._connected:
            return

        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for collection_name in self.collections:
                collection = self.collections[collection_name]
                result = collection.delete_many({"timestamp": {"$lt": cutoff_date}})
                logger.info(f"Cleaned up {result.deleted_count} old documents from {collection_name}")

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")


# Global MongoDB client instance
mongodb_client = MongoDBClient() 