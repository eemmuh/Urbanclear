"""
Urbanclear - Configuration management for the traffic optimization system
"""
import os
from typing import List, Dict, Any, Optional
from functools import lru_cache

import yaml
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from loguru import logger


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "traffic_db"
    username: str = "traffic_user"
    password: str = "password"
    pool_size: int = 10
    max_overflow: int = 20


class MongoConfig(BaseSettings):
    """MongoDB configuration"""
    host: str = "localhost"
    port: int = 27017
    database: str = "traffic_logs"
    username: str = "mongo_user"
    password: str = "password"


class RedisConfig(BaseSettings):
    """Redis configuration"""
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: str = "password"


class DatabaseSettings(BaseSettings):
    """All database settings"""
    postgres: DatabaseConfig = DatabaseConfig()
    mongodb: MongoConfig = MongoConfig()
    redis: RedisConfig = RedisConfig()


class KafkaConfig(BaseSettings):
    """Kafka configuration"""
    bootstrap_servers: List[str] = ["localhost:9092"]
    topics: Dict[str, str] = {
        "traffic_data": "traffic-data",
        "incidents": "traffic-incidents",
        "predictions": "traffic-predictions",
        "alerts": "traffic-alerts"
    }
    consumer: Dict[str, Any] = {
        "group_id": "traffic-system",
        "auto_offset_reset": "latest"
    }
    producer: Dict[str, Any] = {
        "acks": "all",
        "retries": 3
    }


class SparkConfig(BaseSettings):
    """Spark configuration"""
    master: str = "local[*]"
    app_name: str = "TrafficOptimization"
    config: Dict[str, Any] = {
        "spark.sql.adaptive.enabled": True,
        "spark.sql.adaptive.coalescePartitions.enabled": True,
        "spark.serializer": "org.apache.spark.serializer.KryoSerializer"
    }


class ModelConfig(BaseSettings):
    """ML model configuration"""
    traffic_prediction: Dict[str, Any] = {
        "type": "lstm",
        "sequence_length": 24,
        "prediction_horizon": 6,
        "update_frequency": "hourly",
        "model_path": "models/traffic_lstm.pkl"
    }
    route_optimization: Dict[str, Any] = {
        "algorithm": "genetic",
        "population_size": 100,
        "generations": 50,
        "mutation_rate": 0.1
    }
    incident_detection: Dict[str, Any] = {
        "type": "isolation_forest",
        "contamination": 0.1,
        "n_estimators": 100,
        "model_path": "models/incident_detector.pkl"
    }


class DataSourceConfig(BaseSettings):
    """Data source configuration"""
    traffic_sensors: Dict[str, Any] = {
        "enabled": True,
        "update_interval": 30,
        "api_endpoint": "http://city-sensors.api/v1/traffic",
        "api_key": "your_sensor_api_key"
    }
    weather: Dict[str, Any] = {
        "enabled": True,
        "provider": "openweathermap",
        "api_key": "your_weather_api_key",
        "update_interval": 300
    }
    cameras: Dict[str, Any] = {
        "enabled": True,
        "processing_interval": 60,
        "model_path": "models/yolo_traffic.weights"
    }
    gps_data: Dict[str, Any] = {
        "enabled": False,
        "anonymization": True,
        "retention_days": 7
    }


class MonitoringConfig(BaseSettings):
    """Monitoring configuration"""
    prometheus: Dict[str, Any] = {
        "enabled": True,
        "port": 9090,
        "scrape_interval": 30
    }
    grafana: Dict[str, Any] = {
        "enabled": True,
        "port": 3000,
        "admin_password": "your_grafana_password"
    }
    alerts: Dict[str, Any] = {
        "email": {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "alerts@yourcompany.com",
            "password": "your_email_password"
        },
        "slack": {
            "enabled": False,
            "webhook_url": "https://hooks.slack.com/your/webhook/url"
        }
    }


class APIConfig(BaseSettings):
    """API configuration"""
    rate_limiting: Dict[str, Any] = {
        "enabled": True,
        "requests_per_minute": 100
    }
    authentication: Dict[str, Any] = {
        "enabled": False,
        "jwt_secret": "your_jwt_secret_key",
        "token_expiry": 3600
    }
    cors: Dict[str, Any] = {
        "enabled": True,
        "allowed_origins": ["*"]
    }


class GeographyConfig(BaseSettings):
    """Geographic configuration"""
    city_bounds: Dict[str, float] = {
        "north": 40.7831,
        "south": 40.7489,
        "east": -73.9441,
        "west": -73.9927
    }
    coordinate_system: str = "EPSG:4326"
    default_zoom: int = 12


class FeatureConfig(BaseSettings):
    """Feature engineering configuration"""
    time_windows: List[int] = [5, 15, 30, 60]
    spatial_aggregation: int = 500
    weather_features: List[str] = ["temperature", "precipitation", "wind_speed"]
    temporal_features: List[str] = ["hour", "day_of_week", "month", "is_holiday"]


class OptimizationConfig(BaseSettings):
    """System optimization configuration"""
    signal_timing: Dict[str, int] = {
        "min_green_time": 10,
        "max_green_time": 120,
        "yellow_time": 3,
        "all_red_time": 2
    }
    route_calculation: Dict[str, Any] = {
        "max_alternatives": 3,
        "max_distance_factor": 1.5,
        "avoid_construction": True,
        "consider_real_time": True
    }


class SecurityConfig(BaseSettings):
    """Security configuration"""
    encryption: Dict[str, Any] = {
        "enabled": True,
        "algorithm": "AES-256"
    }
    audit_logging: Dict[str, Any] = {
        "enabled": True,
        "retention_days": 90
    }
    api_security: Dict[str, Any] = {
        "https_only": True,
        "certificate_path": "/path/to/ssl/cert.pem",
        "private_key_path": "/path/to/ssl/private.key"
    }


class AppSettings(BaseSettings):
    """Main application settings"""
    name: str = "Urbanclear"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000


class Settings(BaseSettings):
    """Complete system settings"""
    app: AppSettings = AppSettings()
    database: DatabaseSettings = DatabaseSettings()
    kafka: KafkaConfig = KafkaConfig()
    spark: SparkConfig = SparkConfig()
    models: ModelConfig = ModelConfig()
    data_sources: DataSourceConfig = DataSourceConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    api: APIConfig = APIConfig()
    geography: GeographyConfig = GeographyConfig()
    features: FeatureConfig = FeatureConfig()
    optimization: OptimizationConfig = OptimizationConfig()
    security: SecurityConfig = SecurityConfig()

    class Config:
        env_file = ".env"
        case_sensitive = False

    @classmethod
    def load_from_yaml(cls, config_path: str = "config/config.yaml"):
        """Load settings from YAML file"""
        try:
            with open(config_path, 'r') as file:
                config_data = yaml.safe_load(file)
            
            # Convert nested dict to flat dict for Pydantic
            flat_config = {}
            
            def flatten_dict(d, prefix=''):
                for key, value in d.items():
                    if isinstance(value, dict):
                        flatten_dict(value, f"{prefix}{key}__" if prefix else f"{key}__")
                    else:
                        flat_config[f"{prefix}{key}"] = value
            
            flatten_dict(config_data)
            
            # Set environment variables for Pydantic to pick up
            for key, value in flat_config.items():
                os.environ[key.upper()] = str(value)
            
            return cls()
            
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found. Using default settings.")
            return cls()
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            return cls()


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    # Try to load from YAML first, fallback to environment variables
    config_path = os.getenv("CONFIG_PATH", "config/config.yaml")
    
    if os.path.exists(config_path):
        return Settings.load_from_yaml(config_path)
    else:
        logger.info("Loading settings from environment variables")
        return Settings()


def get_database_url(settings: Settings = None) -> str:
    """Get database URL for SQLAlchemy"""
    if settings is None:
        settings = get_settings()
    
    db_config = settings.database.postgres
    return (
        f"postgresql://{db_config.username}:{db_config.password}@"
        f"{db_config.host}:{db_config.port}/{db_config.database}"
    )


def get_mongodb_url(settings: Settings = None) -> str:
    """Get MongoDB URL"""
    if settings is None:
        settings = get_settings()
    
    mongo_config = settings.database.mongodb
    return (
        f"mongodb://{mongo_config.username}:{mongo_config.password}@"
        f"{mongo_config.host}:{mongo_config.port}/{mongo_config.database}"
    )


def get_redis_url(settings: Settings = None) -> str:
    """Get Redis URL"""
    if settings is None:
        settings = get_settings()
    
    redis_config = settings.database.redis
    return f"redis://:{redis_config.password}@{redis_config.host}:{redis_config.port}/{redis_config.database}"


def setup_logging(settings: Settings = None):
    """Setup logging configuration"""
    if settings is None:
        settings = get_settings()
    
    # Configure loguru
    logger.remove()  # Remove default handler
    
    # Add console handler
    logger.add(
        sink=lambda message: print(message, end=""),
        level=settings.app.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file handler
    logger.add(
        "logs/traffic_system.log",
        rotation="1 day",
        retention="30 days",
        level=settings.app.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        compression="zip"
    )
    
    # Add error file handler
    logger.add(
        "logs/traffic_system_errors.log",
        rotation="1 day",
        retention="90 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        compression="zip"
    )
    
    logger.info("Logging configured successfully")


# Environment-specific settings
def get_environment() -> str:
    """Get current environment"""
    return os.getenv("ENVIRONMENT", "development").lower()


def is_production() -> bool:
    """Check if running in production"""
    return get_environment() == "production"


def is_development() -> bool:
    """Check if running in development"""
    return get_environment() == "development"


def is_testing() -> bool:
    """Check if running in testing"""
    return get_environment() == "testing" 