"""
MongoDB API Endpoints for Urbanclear Traffic System
Provides access to logs, analytics, and document-based data
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from loguru import logger

from src.data.logging_service import logging_service
from src.data.mongodb_client import LogLevel, AnalyticsEventType
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/api/mongodb", tags=["mongodb"])


@router.get("/logs")
async def get_logs(
    service: Optional[str] = Query(None, description="Filter by service"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    """Get logs from MongoDB"""
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

        # Parse log level
        log_level = None
        if level:
            try:
                log_level = LogLevel(level.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid log level: {level}. Valid levels: {[l.value for l in LogLevel]}"
                )

        # Get logs from MongoDB
        logs = await logging_service.get_logs(
            service=service,
            level=log_level,
            start_time=start_dt,
            end_time=end_dt,
            limit=limit
        )

        return JSONResponse({
            "status": "success",
            "data": logs,
            "count": len(logs),
            "filters": {
                "service": service,
                "level": level,
                "start_time": start_time,
                "end_time": end_time,
                "limit": limit
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")


@router.get("/analytics/events")
async def get_analytics_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of events to return"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    """Get analytics events from MongoDB"""
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

        # Parse event type
        analytics_event_type = None
        if event_type:
            try:
                analytics_event_type = AnalyticsEventType(event_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid event type: {event_type}. Valid types: {[e.value for e in AnalyticsEventType]}"
                )

        # Get analytics events from MongoDB
        events = await logging_service.get_analytics_events(
            event_type=analytics_event_type,
            start_time=start_dt,
            end_time=end_dt,
            limit=limit
        )

        return JSONResponse({
            "status": "success",
            "data": events,
            "count": len(events),
            "filters": {
                "event_type": event_type,
                "start_time": start_time,
                "end_time": end_time,
                "limit": limit
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving analytics events: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics events")


@router.get("/analytics/summary")
async def get_analytics_summary(
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    """Get analytics summary from MongoDB"""
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

        # Get analytics summary from MongoDB
        summary = await logging_service.get_analytics_summary(
            start_time=start_dt,
            end_time=end_dt
        )

        return JSONResponse({
            "status": "success",
            "data": summary,
            "filters": {
                "start_time": start_time,
                "end_time": end_time
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics summary")


@router.get("/logs/services")
async def get_log_services(
    user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    """Get list of available log services"""
    try:
        # Get logs from the last 24 hours to find services
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        logs = await logging_service.get_logs(
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )

        # Extract unique services
        services = list(set(log.get("service") for log in logs if log.get("service")))
        services.sort()

        return JSONResponse({
            "status": "success",
            "data": {
                "services": services,
                "count": len(services)
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving log services: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve log services")


@router.get("/analytics/event-types")
async def get_analytics_event_types(
    user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    """Get list of available analytics event types"""
    try:
        # Get analytics events from the last 24 hours to find event types
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        events = await logging_service.get_analytics_events(
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )

        # Extract unique event types
        event_types = list(set(event.get("event_type") for event in events if event.get("event_type")))
        event_types.sort()

        return JSONResponse({
            "status": "success",
            "data": {
                "event_types": event_types,
                "count": len(event_types)
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving analytics event types: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics event types")


@router.get("/logs/recent")
async def get_recent_logs(
    hours: int = Query(1, ge=1, le=168, description="Number of hours to look back"),
    limit: int = Query(50, ge=1, le=500, description="Number of logs to return"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    """Get recent logs from MongoDB"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        logs = await logging_service.get_logs(
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        return JSONResponse({
            "status": "success",
            "data": logs,
            "count": len(logs),
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving recent logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent logs")


@router.get("/analytics/recent")
async def get_recent_analytics(
    hours: int = Query(1, ge=1, le=168, description="Number of hours to look back"),
    limit: int = Query(50, ge=1, le=500, description="Number of events to return"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    """Get recent analytics events from MongoDB"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        events = await logging_service.get_analytics_events(
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        return JSONResponse({
            "status": "success",
            "data": events,
            "count": len(events),
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving recent analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent analytics")


@router.post("/logs/search")
async def search_logs(
    query: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    """Search logs with custom query"""
    try:
        # Extract search parameters
        service = query.get("service")
        level = query.get("level")
        message_pattern = query.get("message_pattern")
        start_time_str = query.get("start_time")
        end_time_str = query.get("end_time")
        limit = query.get("limit", 100)

        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time_str:
            start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        if end_time_str:
            end_dt = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))

        # Parse log level
        log_level = None
        if level:
            try:
                log_level = LogLevel(level.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid log level: {level}"
                )

        # Get logs from MongoDB
        logs = await logging_service.get_logs(
            service=service,
            level=log_level,
            start_time=start_dt,
            end_time=end_dt,
            limit=limit
        )

        # Filter by message pattern if provided
        if message_pattern:
            import re
            pattern = re.compile(message_pattern, re.IGNORECASE)
            logs = [log for log in logs if pattern.search(log.get("message", ""))]

        return JSONResponse({
            "status": "success",
            "data": logs,
            "count": len(logs),
            "query": query
        })

    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to search logs")


@router.delete("/cleanup")
async def cleanup_old_data(
    days_to_keep: int = Query(90, ge=1, le=365, description="Number of days to keep"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    """Clean up old data from MongoDB"""
    try:
        await logging_service.cleanup_old_data(days_to_keep)
        
        return JSONResponse({
            "status": "success",
            "message": f"Cleaned up data older than {days_to_keep} days",
            "days_to_keep": days_to_keep
        })

    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup old data")


@router.get("/health")
async def mongodb_health_check() -> JSONResponse:
    """Check MongoDB connection health"""
    try:
        is_connected = logging_service.mongodb.is_connected()
        
        return JSONResponse({
            "status": "success",
            "mongodb_connected": is_connected,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error checking MongoDB health: {e}")
        return JSONResponse({
            "status": "error",
            "mongodb_connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }) 