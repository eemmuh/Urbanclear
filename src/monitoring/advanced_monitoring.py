"""
Advanced Monitoring and Alerting System for Urbanclear
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import psutil
import aiohttp
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    CollectorRegistry,
    start_http_server,
)
from loguru import logger
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import redis
from src.core.config import get_settings


class AlertSeverity(str, Enum):
    """Alert severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertType(str, Enum):
    """Types of alerts"""

    SYSTEM_HEALTH = "system_health"
    API_PERFORMANCE = "api_performance"
    DATABASE_CONNECTIVITY = "database_connectivity"
    TRAFFIC_ANOMALY = "traffic_anomaly"
    SECURITY_INCIDENT = "security_incident"
    RESOURCE_USAGE = "resource_usage"
    PREDICTION_ACCURACY = "prediction_accuracy"


@dataclass
class Alert:
    """Alert data structure"""

    id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime
    affected_component: str
    metrics: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class HealthCheck:
    """Health check result"""

    service: str
    status: str
    response_time: float
    details: Dict[str, Any]
    timestamp: datetime
    healthy: bool


class MetricsCollector:
    """Advanced metrics collection"""

    def __init__(self):
        self.registry = CollectorRegistry()
        self.setup_metrics()

    def setup_metrics(self):
        """Setup comprehensive metrics"""
        # API Metrics
        self.api_requests_total = Counter(
            "urbanclear_api_requests_total",
            "Total API requests by endpoint and status",
            ["endpoint", "method", "status_code"],
            registry=self.registry,
        )

        self.api_request_duration = Histogram(
            "urbanclear_api_request_duration_seconds",
            "API request duration",
            ["endpoint", "method"],
            registry=self.registry,
        )

        self.api_concurrent_requests = Gauge(
            "urbanclear_api_concurrent_requests",
            "Number of concurrent API requests",
            registry=self.registry,
        )

        # Traffic Metrics
        self.traffic_sensors_active = Gauge(
            "urbanclear_traffic_sensors_active",
            "Number of active traffic sensors",
            registry=self.registry,
        )

        self.traffic_flow_rate = Gauge(
            "urbanclear_traffic_flow_rate",
            "Traffic flow rate by location",
            ["location", "direction"],
            registry=self.registry,
        )

        self.congestion_level = Gauge(
            "urbanclear_congestion_level",
            "Traffic congestion level by location",
            ["location"],
            registry=self.registry,
        )

        self.incidents_active = Gauge(
            "urbanclear_incidents_active",
            "Number of active traffic incidents",
            ["severity", "type"],
            registry=self.registry,
        )

        # ML Model Metrics
        self.model_prediction_accuracy = Gauge(
            "urbanclear_model_prediction_accuracy",
            "ML model prediction accuracy",
            ["model_type"],
            registry=self.registry,
        )

        self.model_inference_time = Histogram(
            "urbanclear_model_inference_time_seconds",
            "Model inference time",
            ["model_type"],
            registry=self.registry,
        )

        self.model_training_duration = Gauge(
            "urbanclear_model_training_duration_seconds",
            "Model training duration",
            ["model_type"],
            registry=self.registry,
        )

        # System Metrics
        self.cpu_usage_percent = Gauge(
            "urbanclear_cpu_usage_percent",
            "CPU usage percentage",
            registry=self.registry,
        )

        self.memory_usage_bytes = Gauge(
            "urbanclear_memory_usage_bytes",
            "Memory usage in bytes",
            registry=self.registry,
        )

        self.disk_usage_percent = Gauge(
            "urbanclear_disk_usage_percent",
            "Disk usage percentage",
            ["mountpoint"],
            registry=self.registry,
        )

        # Database Metrics
        self.database_connections_active = Gauge(
            "urbanclear_database_connections_active",
            "Active database connections",
            ["database_type"],
            registry=self.registry,
        )

        self.database_query_duration = Histogram(
            "urbanclear_database_query_duration_seconds",
            "Database query duration",
            ["database_type", "operation"],
            registry=self.registry,
        )

        self.cache_hit_rate = Gauge(
            "urbanclear_cache_hit_rate", "Cache hit rate", registry=self.registry
        )

        # Business Metrics
        self.route_optimizations_total = Counter(
            "urbanclear_route_optimizations_total",
            "Total route optimizations performed",
            registry=self.registry,
        )

        self.signal_optimizations_total = Counter(
            "urbanclear_signal_optimizations_total",
            "Total signal optimizations performed",
            registry=self.registry,
        )

        self.data_points_processed_total = Counter(
            "urbanclear_data_points_processed_total",
            "Total data points processed",
            ["data_type"],
            registry=self.registry,
        )


class HealthCheckManager:
    """Comprehensive health check system"""

    def __init__(self):
        self.checks = {}
        self.results = []
        self.settings = get_settings()

    def register_check(self, name: str, check_func: Callable, interval: int = 60):
        """Register a health check"""
        self.checks[name] = {
            "func": check_func,
            "interval": interval,
            "last_run": None,
            "next_run": datetime.now(),
        }
        logger.info(f"Registered health check: {name}")

    async def run_check(self, name: str) -> HealthCheck:
        """Run a specific health check"""
        check = self.checks[name]
        start_time = time.time()

        try:
            result = await check["func"]()
            response_time = time.time() - start_time

            health_check = HealthCheck(
                service=name,
                status="healthy" if result.get("healthy", True) else "unhealthy",
                response_time=response_time,
                details=result,
                timestamp=datetime.now(),
                healthy=result.get("healthy", True),
            )

        except Exception as e:
            response_time = time.time() - start_time
            health_check = HealthCheck(
                service=name,
                status="error",
                response_time=response_time,
                details={"error": str(e)},
                timestamp=datetime.now(),
                healthy=False,
            )
            logger.error(f"Health check failed for {name}: {e}")

        self.results.append(health_check)
        self.checks[name]["last_run"] = datetime.now()

        return health_check

    async def run_all_checks(self) -> List[HealthCheck]:
        """Run all registered health checks"""
        results = []
        for name in self.checks:
            result = await self.run_check(name)
            results.append(result)
        return results

    async def continuous_monitoring(self):
        """Continuous health monitoring"""
        while True:
            now = datetime.now()
            for name, check in self.checks.items():
                if now >= check["next_run"]:
                    await self.run_check(name)
                    check["next_run"] = now + timedelta(seconds=check["interval"])

            await asyncio.sleep(10)  # Check every 10 seconds

    def get_service_status(self) -> Dict[str, Any]:
        """Get overall service status"""
        if not self.results:
            return {"status": "unknown", "services": {}}

        recent_results = {}
        for result in self.results[
            -len(self.checks) :
        ]:  # Latest results for each service
            recent_results[result.service] = result

        all_healthy = all(result.healthy for result in recent_results.values())
        status = "healthy" if all_healthy else "degraded"

        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                name: {
                    "status": result.status,
                    "healthy": result.healthy,
                    "response_time": result.response_time,
                    "last_check": result.timestamp.isoformat(),
                }
                for name, result in recent_results.items()
            },
        }


class AlertManager:
    """Advanced alerting system"""

    def __init__(self):
        self.alerts = []
        self.alert_rules = []
        self.notification_channels = []
        self.settings = get_settings()

    def add_alert_rule(self, rule: Dict[str, Any]):
        """Add an alert rule"""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule['name']}")

    def add_notification_channel(self, channel_type: str, config: Dict[str, Any]):
        """Add notification channel"""
        self.notification_channels.append({"type": channel_type, "config": config})
        logger.info(f"Added notification channel: {channel_type}")

    async def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        description: str,
        affected_component: str,
        metrics: Dict[str, Any],
    ) -> Alert:
        """Create a new alert"""
        alert = Alert(
            id=f"alert_{int(time.time())}_{len(self.alerts)}",
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            timestamp=datetime.now(),
            affected_component=affected_component,
            metrics=metrics,
        )

        self.alerts.append(alert)
        logger.warning(f"Alert created: {alert.title} ({alert.severity})")

        # Send notifications
        await self.send_notifications(alert)

        return alert

    async def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolution_time = datetime.now()
                logger.info(f"Alert resolved: {alert.title}")
                break

    async def send_notifications(self, alert: Alert):
        """Send alert notifications"""
        for channel in self.notification_channels:
            try:
                if channel["type"] == "email":
                    await self._send_email_notification(alert, channel["config"])
                elif channel["type"] == "slack":
                    await self._send_slack_notification(alert, channel["config"])
                elif channel["type"] == "webhook":
                    await self._send_webhook_notification(alert, channel["config"])
            except Exception as e:
                logger.error(f"Failed to send notification via {channel['type']}: {e}")

    async def _send_email_notification(self, alert: Alert, config: Dict[str, Any]):
        """Send email notification"""
        msg = MIMEMultipart()
        msg["From"] = config["from_email"]
        msg["To"] = config["to_email"]
        msg["Subject"] = f"[Urbanclear Alert] {alert.title}"

        body = f"""
        Alert: {alert.title}
        Severity: {alert.severity}
        Component: {alert.affected_component}
        Time: {alert.timestamp}
        
        Description:
        {alert.description}
        
        Metrics:
        {json.dumps(alert.metrics, indent=2)}
        """

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
        server.starttls()
        server.login(config["username"], config["password"])
        server.send_message(msg)
        server.quit()

    async def _send_slack_notification(self, alert: Alert, config: Dict[str, Any]):
        """Send Slack notification"""
        webhook_url = config["webhook_url"]

        color = {
            AlertSeverity.CRITICAL: "#FF0000",
            AlertSeverity.HIGH: "#FF8000",
            AlertSeverity.MEDIUM: "#FFFF00",
            AlertSeverity.LOW: "#00FF00",
            AlertSeverity.INFO: "#0080FF",
        }.get(alert.severity, "#808080")

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"Urbanclear Alert: {alert.title}",
                    "fields": [
                        {"title": "Severity", "value": alert.severity, "short": True},
                        {
                            "title": "Component",
                            "value": alert.affected_component,
                            "short": True,
                        },
                        {
                            "title": "Description",
                            "value": alert.description,
                            "short": False,
                        },
                    ],
                    "timestamp": int(alert.timestamp.timestamp()),
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Slack webhook failed: {response.status}")

    async def _send_webhook_notification(self, alert: Alert, config: Dict[str, Any]):
        """Send webhook notification"""
        payload = {"alert": asdict(alert), "timestamp": alert.timestamp.isoformat()}

        async with aiohttp.ClientSession() as session:
            async with session.post(config["url"], json=payload) as response:
                if response.status not in [200, 201, 202]:
                    raise Exception(f"Webhook failed: {response.status}")

    def get_active_alerts(self) -> List[Alert]:
        """Get active (unresolved) alerts"""
        return [alert for alert in self.alerts if not alert.resolved]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        active_alerts = self.get_active_alerts()

        by_severity = {}
        for severity in AlertSeverity:
            by_severity[severity.value] = len(
                [a for a in active_alerts if a.severity == severity]
            )

        by_type = {}
        for alert_type in AlertType:
            by_type[alert_type.value] = len(
                [a for a in active_alerts if a.alert_type == alert_type]
            )

        return {
            "total_active": len(active_alerts),
            "by_severity": by_severity,
            "by_type": by_type,
            "last_updated": datetime.now().isoformat(),
        }


class AdvancedMonitoringSystem:
    """Main monitoring system coordinator"""

    def __init__(self):
        self.metrics = MetricsCollector()
        self.health_checks = HealthCheckManager()
        self.alerts = AlertManager()
        self.running = False

        # Setup default health checks
        self._setup_default_health_checks()

        # Setup default alert rules
        self._setup_default_alert_rules()

    def _setup_default_health_checks(self):
        """Setup default health checks"""

        async def api_health_check():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "http://localhost:8000/health", timeout=5
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {"healthy": True, "details": data}
                        else:
                            return {"healthy": False, "status_code": response.status}
            except Exception as e:
                return {"healthy": False, "error": str(e)}

        async def database_health_check():
            try:
                # Check PostgreSQL
                import psycopg2

                conn = psycopg2.connect(
                    host=self.settings.database.postgres.host,
                    port=self.settings.database.postgres.port,
                    database=self.settings.database.postgres.database,
                    user=self.settings.database.postgres.username,
                    password=self.settings.database.postgres.password,
                )
                conn.close()
                return {"healthy": True, "database": "postgresql"}
            except Exception as e:
                return {"healthy": False, "error": str(e)}

        async def redis_health_check():
            try:
                r = redis.Redis(
                    host=self.settings.database.redis.host,
                    port=self.settings.database.redis.port,
                    db=self.settings.database.redis.database,
                )
                r.ping()
                return {"healthy": True, "cache": "redis"}
            except Exception as e:
                return {"healthy": False, "error": str(e)}

        async def system_resources_check():
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Update metrics
            self.metrics.cpu_usage_percent.set(cpu_percent)
            self.metrics.memory_usage_bytes.set(memory.used)
            self.metrics.disk_usage_percent.labels(mountpoint="/").set(disk.percent)

            healthy = cpu_percent < 90 and memory.percent < 90 and disk.percent < 90

            return {
                "healthy": healthy,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
            }

        # Register health checks
        self.health_checks.register_check("api", api_health_check, 30)
        self.health_checks.register_check("database", database_health_check, 60)
        self.health_checks.register_check("redis", redis_health_check, 60)
        self.health_checks.register_check(
            "system_resources", system_resources_check, 30
        )

    def _setup_default_alert_rules(self):
        """Setup default alert rules"""
        self.alerts.add_alert_rule(
            {
                "name": "high_cpu_usage",
                "condition": "cpu_usage > 80",
                "severity": AlertSeverity.HIGH,
                "duration": 300,  # 5 minutes
            }
        )

        self.alerts.add_alert_rule(
            {
                "name": "api_response_time",
                "condition": "api_response_time > 5",
                "severity": AlertSeverity.MEDIUM,
                "duration": 180,  # 3 minutes
            }
        )

        self.alerts.add_alert_rule(
            {
                "name": "prediction_accuracy_low",
                "condition": "prediction_accuracy < 0.7",
                "severity": AlertSeverity.MEDIUM,
                "duration": 600,  # 10 minutes
            }
        )

    async def start(self):
        """Start the monitoring system"""
        self.running = True
        logger.info("Starting advanced monitoring system")

        # Start Prometheus metrics server
        start_http_server(9091, registry=self.metrics.registry)
        logger.info("Prometheus metrics server started on port 9091")

        # Start health check monitoring
        asyncio.create_task(self.health_checks.continuous_monitoring())

        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())

    async def stop(self):
        """Stop the monitoring system"""
        self.running = False
        logger.info("Stopping advanced monitoring system")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check for alert conditions
                await self._check_alert_conditions()

                # Update business metrics
                await self._update_business_metrics()

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)

    async def _check_alert_conditions(self):
        """Check alert conditions"""
        # Get latest health check results
        status = self.health_checks.get_service_status()

        # Check for unhealthy services
        for service_name, service_status in status.get("services", {}).items():
            if not service_status["healthy"]:
                await self.alerts.create_alert(
                    alert_type=AlertType.SYSTEM_HEALTH,
                    severity=AlertSeverity.HIGH,
                    title=f"Service {service_name} unhealthy",
                    description=f"Service {service_name} is reporting unhealthy status",
                    affected_component=service_name,
                    metrics=service_status,
                )

    async def _update_business_metrics(self):
        """Update business-specific metrics"""
        # This would be implemented based on your specific business logic
        # For example, counting active sensors, processing rates, etc.

    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        return {
            "health_status": self.health_checks.get_service_status(),
            "alert_summary": self.alerts.get_alert_summary(),
            "active_alerts": [
                asdict(alert) for alert in self.alerts.get_active_alerts()
            ],
            "metrics_endpoint": "http://localhost:9091/metrics",
            "timestamp": datetime.now().isoformat(),
        }


# Global monitoring instance
monitoring_system = AdvancedMonitoringSystem()


# Example usage
async def main():
    """Example usage of the monitoring system"""
    # Start monitoring
    await monitoring_system.start()

    # Add notification channels
    monitoring_system.alerts.add_notification_channel(
        "email",
        {
            "from_email": "alerts@urbanclear.com",
            "to_email": "admin@urbanclear.com",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "alerts@urbanclear.com",
            "password": "your-password",
        },
    )

    # Simulate running for a while
    await asyncio.sleep(300)  # 5 minutes

    # Get dashboard data
    dashboard_data = monitoring_system.get_monitoring_dashboard_data()
    print(json.dumps(dashboard_data, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
