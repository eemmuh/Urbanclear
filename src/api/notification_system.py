"""
Notification System for Traffic Alerts and Incidents
"""

import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
from loguru import logger
from pydantic import BaseModel

from src.core.config import get_settings


class NotificationChannel(Enum):
    """Notification channels"""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    PUSH = "push"


class NotificationPriority(Enum):
    """Notification priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationTemplate(BaseModel):
    """Notification template structure"""

    subject: str
    body: str
    html_body: Optional[str] = None
    priority: NotificationPriority = NotificationPriority.MEDIUM


class NotificationRequest(BaseModel):
    """Notification request structure"""

    channel: NotificationChannel
    recipients: List[str]
    template: NotificationTemplate
    data: Dict[str, Any]
    incident_id: Optional[str] = None
    location: Optional[str] = None


class NotificationService:
    """Service for sending notifications"""

    def __init__(self):
        self.settings = get_settings()
        self.templates = self._load_templates()
        self.sent_notifications = {}  # Track sent notifications

    def _load_templates(self) -> Dict[str, NotificationTemplate]:
        """Load notification templates"""
        return {
            "traffic_incident": NotificationTemplate(
                subject="🚨 Traffic Incident Alert - {location}",
                body="""
Traffic Incident Alert

Location: {location}
Type: {incident_type}
Severity: {severity}
Status: {status}
Estimated Duration: {duration}

Details: {description}

Time: {timestamp}

Please take alternate routes and drive safely.

Urbanclear Traffic Management System
                """,
                html_body="""
<html>
<body>
<h2>🚨 Traffic Incident Alert</h2>
<p><strong>Location:</strong> {location}</p>
<p><strong>Type:</strong> {incident_type}</p>
<p><strong>Severity:</strong> <span style="color: {severity_color};">{severity}</span></p>
<p><strong>Status:</strong> {status}</p>
<p><strong>Estimated Duration:</strong> {duration}</p>
<p><strong>Details:</strong> {description}</p>
<p><strong>Time:</strong> {timestamp}</p>
<hr>
<p>Please take alternate routes and drive safely.</p>
<p><em>Urbanclear Traffic Management System</em></p>
</body>
</html>
                """,
                priority=NotificationPriority.HIGH,
            ),
            "congestion_alert": NotificationTemplate(
                subject="🚦 Heavy Traffic Alert - {location}",
                body="""
Heavy Traffic Alert

Location: {location}
Current Speed: {speed} mph
Congestion Level: {congestion}%
Expected Delay: {delay} minutes

Alternative routes are recommended.

Time: {timestamp}

Urbanclear Traffic Management System
                """,
                priority=NotificationPriority.MEDIUM,
            ),
            "system_alert": NotificationTemplate(
                subject="⚠️ System Alert - Urbanclear",
                body="""
System Alert

Component: {component}
Status: {status}
Message: {message}

Time: {timestamp}

Urbanclear Traffic Management System
                """,
                priority=NotificationPriority.CRITICAL,
            ),
            "incident_resolved": NotificationTemplate(
                subject="✅ Incident Resolved - {location}",
                body="""
Incident Resolved

Location: {location}
Type: {incident_type}
Duration: {duration}
Status: Resolved

Traffic flow has returned to normal.

Time: {timestamp}

Urbanclear Traffic Management System
                """,
                priority=NotificationPriority.LOW,
            ),
        }

    async def send_notification(self, request: NotificationRequest) -> bool:
        """Send notification via specified channel"""
        try:
            if request.channel == NotificationChannel.EMAIL:
                return await self._send_email(request)
            elif request.channel == NotificationChannel.SLACK:
                return await self._send_slack(request)
            elif request.channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook(request)
            elif request.channel == NotificationChannel.SMS:
                return await self._send_sms(request)
            elif request.channel == NotificationChannel.PUSH:
                return await self._send_push(request)
            else:
                logger.error(f"Unsupported notification channel: {request.channel}")
                return False
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    async def _send_email(self, request: NotificationRequest) -> bool:
        """Send email notification"""
        try:
            # Format template with data
            subject = request.template.subject.format(**request.data)
            body = request.template.body.format(**request.data)

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = "noreply@urbanclear.com"
            msg["To"] = ", ".join(request.recipients)

            # Add plain text
            text_part = MIMEText(body, "plain")
            msg.attach(text_part)

            # Add HTML if available
            if request.template.html_body:
                html_body = request.template.html_body.format(**request.data)
                html_part = MIMEText(html_body, "html")
                msg.attach(html_part)

            # Send email (mock implementation)
            logger.info(f"📧 Email sent to {request.recipients}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def _send_slack(self, request: NotificationRequest) -> bool:
        """Send Slack notification"""
        try:
            # Format message for Slack
            message = {
                "text": request.template.subject.format(**request.data),
                "attachments": [
                    {
                        "color": self._get_priority_color(request.template.priority),
                        "fields": [
                            {
                                "title": "Location",
                                "value": request.data.get("location", "N/A"),
                                "short": True,
                            },
                            {
                                "title": "Time",
                                "value": request.data.get("timestamp", "N/A"),
                                "short": True,
                            },
                            {
                                "title": "Details",
                                "value": request.template.body.format(**request.data),
                                "short": False,
                            },
                        ],
                    }
                ],
            }

            # Mock Slack webhook call
            logger.info(f"📱 Slack message sent: {message['text']}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    async def _send_webhook(self, request: NotificationRequest) -> bool:
        """Send webhook notification"""
        try:
            payload = {
                "channel": request.channel.value,
                "template": request.template.subject.format(**request.data),
                "data": request.data,
                "timestamp": datetime.now().isoformat(),
                "priority": request.template.priority.value,
            }

            # Mock webhook call
            logger.info(f"🔗 Webhook sent: {json.dumps(payload, indent=2)}")
            return True

        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False

    async def _send_sms(self, request: NotificationRequest) -> bool:
        """Send SMS notification"""
        try:
            # Simplified SMS message
            message = (
                f"Urbanclear Alert: {request.template.subject.format(**request.data)}"
            )

            # Mock SMS service
            logger.info(f"📱 SMS sent to {request.recipients}: {message}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    async def _send_push(self, request: NotificationRequest) -> bool:
        """Send push notification"""
        try:
            # Mock push notification
            logger.info(f"📲 Push notification sent to {request.recipients}")
            return True

        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False

    def _get_priority_color(self, priority: NotificationPriority) -> str:
        """Get color for priority level"""
        color_map = {
            NotificationPriority.LOW: "good",
            NotificationPriority.MEDIUM: "warning",
            NotificationPriority.HIGH: "danger",
            NotificationPriority.CRITICAL: "#ff0000",
        }
        return color_map.get(priority, "good")

    async def send_incident_alert(self, incident_data: Dict[str, Any]) -> bool:
        """Send incident alert notification"""
        try:
            # Add severity color for HTML template
            severity_colors = {
                "low": "green",
                "medium": "orange",
                "high": "red",
                "critical": "darkred",
            }
            incident_data["severity_color"] = severity_colors.get(
                incident_data.get("severity", "medium"), "orange"
            )

            template = self.templates["traffic_incident"]
            request = NotificationRequest(
                channel=NotificationChannel.EMAIL,
                recipients=["traffic@urbanclear.com"],  # Configure recipients
                template=template,
                data=incident_data,
                incident_id=incident_data.get("id"),
                location=incident_data.get("location"),
            )

            return await self.send_notification(request)

        except Exception as e:
            logger.error(f"Failed to send incident alert: {e}")
            return False

    async def send_congestion_alert(self, congestion_data: Dict[str, Any]) -> bool:
        """Send congestion alert notification"""
        try:
            template = self.templates["congestion_alert"]
            request = NotificationRequest(
                channel=NotificationChannel.SLACK,
                recipients=["#traffic-alerts"],
                template=template,
                data=congestion_data,
                location=congestion_data.get("location"),
            )

            return await self.send_notification(request)

        except Exception as e:
            logger.error(f"Failed to send congestion alert: {e}")
            return False

    async def send_system_alert(self, system_data: Dict[str, Any]) -> bool:
        """Send system alert notification"""
        try:
            template = self.templates["system_alert"]
            request = NotificationRequest(
                channel=NotificationChannel.WEBHOOK,
                recipients=["system-admin"],
                template=template,
                data=system_data,
            )

            return await self.send_notification(request)

        except Exception as e:
            logger.error(f"Failed to send system alert: {e}")
            return False

    async def send_incident_resolved(self, incident_data: Dict[str, Any]) -> bool:
        """Send incident resolved notification"""
        try:
            template = self.templates["incident_resolved"]
            request = NotificationRequest(
                channel=NotificationChannel.EMAIL,
                recipients=["traffic@urbanclear.com"],
                template=template,
                data=incident_data,
                incident_id=incident_data.get("id"),
                location=incident_data.get("location"),
            )

            return await self.send_notification(request)

        except Exception as e:
            logger.error(f"Failed to send resolved notification: {e}")
            return False

    async def send_bulk_notifications(
        self, notifications: List[NotificationRequest]
    ) -> Dict[str, int]:
        """Send multiple notifications"""
        results = {"sent": 0, "failed": 0}

        # Send notifications concurrently
        tasks = [self.send_notification(request) for request in notifications]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for response in responses:
            if isinstance(response, Exception):
                results["failed"] += 1
            elif response:
                results["sent"] += 1
            else:
                results["failed"] += 1

        logger.info(f"Bulk notification results: {results}")
        return results


# Global notification service instance
notification_service = NotificationService()


# Example usage functions
async def demo_notifications():
    """Demo notification system"""

    # Incident alert
    incident_data = {
        "location": "Times Square & Broadway",
        "incident_type": "Vehicle Accident",
        "severity": "high",
        "status": "Active",
        "duration": "30-45 minutes",
        "description": "Multi-vehicle accident blocking 2 lanes",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    await notification_service.send_incident_alert(incident_data)

    # Congestion alert
    congestion_data = {
        "location": "Brooklyn Bridge",
        "speed": "8",
        "congestion": "85",
        "delay": "15",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    await notification_service.send_congestion_alert(congestion_data)

    # System alert
    system_data = {
        "component": "Traffic Predictor",
        "status": "Degraded",
        "message": "Model accuracy below threshold",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    await notification_service.send_system_alert(system_data)


if __name__ == "__main__":
    asyncio.run(demo_notifications())
