"""
Logging Service for Urbanclear Traffic System
Integrates with MongoDB for structured logging and analytics
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
import logging
from loguru import logger

from .mongodb_client import (
    MongoDBClient, LogEntry, AnalyticsEvent, LogLevel, AnalyticsEventType, mongodb_client
)


@dataclass
class LogContext:
    """Logging context for request tracking"""
    request_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    service: str = "api"


class LoggingService:
    """Centralized logging service with MongoDB integration"""

    def __init__(self):
        self.mongodb = mongodb_client
        self.context_stack: List[LogContext] = []
        self._batch_size = 10
        self._batch_timeout = 5.0  # seconds
        self._pending_logs: List[LogEntry] = []
        self._pending_analytics: List[AnalyticsEvent] = []
        self._batch_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the logging service"""
        if self._running:
            return

        # Connect to MongoDB
        await self.mongodb.connect()
        
        # Start batch processing
        self._running = True
        self._batch_task = asyncio.create_task(self._batch_processor())
        
        logger.info("Logging service started")

    async def stop(self):
        """Stop the logging service"""
        if not self._running:
            return

        self._running = False
        
        # Flush pending logs
        await self._flush_pending_logs()
        await self._flush_pending_analytics()
        
        # Cancel batch task
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect from MongoDB
        await self.mongodb.disconnect()
        
        logger.info("Logging service stopped")

    @asynccontextmanager
    async def log_context(
        self,
        service: str = "api",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Context manager for logging with request tracking"""
        context = LogContext(
            request_id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            service=service
        )
        
        self.context_stack.append(context)
        
        try:
            yield context
        finally:
            if self.context_stack:
                self.context_stack.pop()

    def _get_current_context(self) -> Optional[LogContext]:
        """Get the current logging context"""
        return self.context_stack[-1] if self.context_stack else None

    async def log(
        self,
        level: LogLevel,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        service: Optional[str] = None
    ):
        """Log a message with current context"""
        context = self._get_current_context()
        
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            service=service or (context.service if context else "system"),
            message=message,
            details=details,
            user_id=context.user_id if context else None,
            session_id=context.session_id if context else None,
            request_id=context.request_id if context else None,
            ip_address=context.ip_address if context else None
        )

        # Add to batch for processing
        self._pending_logs.append(log_entry)

        # Also log to console/file for immediate visibility
        log_method = getattr(logger, level.value, logger.info)
        log_method(f"[{log_entry.service}] {message}")

    async def log_analytics(
        self,
        event_type: AnalyticsEventType,
        data: Dict[str, Any],
        location: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        service: Optional[str] = None
    ):
        """Log an analytics event"""
        context = self._get_current_context()
        
        event = AnalyticsEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            service=service or (context.service if context else "system"),
            data=data,
            user_id=context.user_id if context else None,
            session_id=context.session_id if context else None,
            location=location,
            metadata=metadata
        )

        # Add to batch for processing
        self._pending_analytics.append(event)

    async def log_traffic_data(
        self,
        sensor_id: str,
        speed: float,
        volume: int,
        density: float,
        congestion_level: float,
        location: Optional[Dict[str, float]] = None
    ):
        """Log traffic data event"""
        data = {
            "sensor_id": sensor_id,
            "speed": speed,
            "volume": volume,
            "density": density,
            "congestion_level": congestion_level
        }
        
        await self.log_analytics(
            event_type=AnalyticsEventType.TRAFFIC_DATA,
            data=data,
            location=location,
            service="traffic_service"
        )

    async def log_incident(
        self,
        incident_id: str,
        incident_type: str,
        severity: str,
        location: Dict[str, float],
        description: str
    ):
        """Log incident event"""
        data = {
            "incident_id": incident_id,
            "incident_type": incident_type,
            "severity": severity,
            "description": description
        }
        
        await self.log_analytics(
            event_type=AnalyticsEventType.INCIDENT_REPORT,
            data=data,
            location=location,
            service="incident_service"
        )

    async def log_route_optimization(
        self,
        origin: Dict[str, float],
        destination: Dict[str, float],
        optimization_time: float,
        route_length: float,
        preferences: Optional[Dict[str, Any]] = None
    ):
        """Log route optimization event"""
        data = {
            "origin": origin,
            "destination": destination,
            "optimization_time": optimization_time,
            "route_length": route_length,
            "preferences": preferences
        }
        
        await self.log_analytics(
            event_type=AnalyticsEventType.ROUTE_OPTIMIZATION,
            data=data,
            service="route_service"
        )

    async def log_api_request(
        self,
        endpoint: str,
        method: str,
        response_code: int,
        response_time: float,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None
    ):
        """Log API request event"""
        data = {
            "endpoint": endpoint,
            "method": method,
            "response_code": response_code,
            "response_time": response_time,
            "request_size": request_size,
            "response_size": response_size
        }
        
        await self.log_analytics(
            event_type=AnalyticsEventType.API_REQUEST,
            data=data,
            service="api"
        )

    async def log_system_event(
        self,
        component: str,
        event: str,
        details: Dict[str, Any]
    ):
        """Log system event"""
        data = {
            "component": component,
            "event": event,
            "details": details
        }
        
        await self.log_analytics(
            event_type=AnalyticsEventType.SYSTEM_EVENT,
            data=data,
            service="system"
        )

    async def _batch_processor(self):
        """Background task for batch processing logs"""
        while self._running:
            try:
                # Wait for batch timeout or batch size
                await asyncio.sleep(self._batch_timeout)
                
                # Flush pending logs
                await self._flush_pending_logs()
                await self._flush_pending_analytics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(1)

    async def _flush_pending_logs(self):
        """Flush pending logs to MongoDB"""
        if not self._pending_logs:
            return

        logs_to_process = self._pending_logs[:self._batch_size]
        self._pending_logs = self._pending_logs[self._batch_size:]

        tasks = []
        for log_entry in logs_to_process:
            task = self.mongodb.log_entry(log_entry)
            tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            failed_count = sum(1 for r in results if isinstance(r, Exception))
            if failed_count > 0:
                logger.warning(f"Failed to store {failed_count} log entries")

    async def _flush_pending_analytics(self):
        """Flush pending analytics to MongoDB"""
        if not self._pending_analytics:
            return

        analytics_to_process = self._pending_analytics[:self._batch_size]
        self._pending_analytics = self._pending_analytics[self._batch_size:]

        tasks = []
        for event in analytics_to_process:
            task = self.mongodb.log_analytics_event(event)
            tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            failed_count = sum(1 for r in results if isinstance(r, Exception))
            if failed_count > 0:
                logger.warning(f"Failed to store {failed_count} analytics events")

    async def get_logs(
        self,
        service: Optional[str] = None,
        level: Optional[LogLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve logs from MongoDB"""
        return await self.mongodb.get_logs(
            service=service,
            level=level,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

    async def get_analytics_events(
        self,
        event_type: Optional[AnalyticsEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve analytics events from MongoDB"""
        return await self.mongodb.get_analytics_events(
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

    async def get_analytics_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics summary from MongoDB"""
        return await self.mongodb.get_analytics_summary(
            start_time=start_time,
            end_time=end_time
        )

    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data from MongoDB"""
        await self.mongodb.cleanup_old_data(days_to_keep)


# Global logging service instance
logging_service = LoggingService()


# Convenience functions for easy logging
async def log_info(message: str, details: Optional[Dict[str, Any]] = None, service: Optional[str] = None):
    """Log info message"""
    await logging_service.log(LogLevel.INFO, message, details, service)


async def log_warning(message: str, details: Optional[Dict[str, Any]] = None, service: Optional[str] = None):
    """Log warning message"""
    await logging_service.log(LogLevel.WARNING, message, details, service)


async def log_error(message: str, details: Optional[Dict[str, Any]] = None, service: Optional[str] = None):
    """Log error message"""
    await logging_service.log(LogLevel.ERROR, message, details, service)


async def log_debug(message: str, details: Optional[Dict[str, Any]] = None, service: Optional[str] = None):
    """Log debug message"""
    await logging_service.log(LogLevel.DEBUG, message, details, service) 