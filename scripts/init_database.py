#!/usr/bin/env python3
"""
Database initialization script for Urbanclear - Traffic Optimization System
"""
import sys
import os
import asyncio
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from loguru import logger

from src.core.config import get_settings, setup_logging


def create_database():
    """Create the main database if it doesn't exist"""
    settings = get_settings()
    db_config = settings.database.postgres
    
    # Connect to PostgreSQL server (not specific database)
    conn = psycopg2.connect(
        host=db_config.host,
        port=db_config.port,
        user=db_config.username,
        password=db_config.password,
        database='postgres'  # Connect to default database
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    cursor = conn.cursor()
    
    try:
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (db_config.database,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database {db_config.database}")
            cursor.execute(f'CREATE DATABASE "{db_config.database}"')
            logger.info("Database created successfully")
        else:
            logger.info(f"Database {db_config.database} already exists")
            
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def create_tables():
    """Create database tables"""
    settings = get_settings()
    
    # Get database URL
    db_config = settings.database.postgres
    database_url = (
        f"postgresql://{db_config.username}:{db_config.password}@"
        f"{db_config.host}:{db_config.port}/{db_config.database}"
    )
    
    engine = create_engine(database_url)
    
    # SQL commands to create tables
    sql_commands = [
        # Traffic sensors table
        """
        CREATE TABLE IF NOT EXISTS traffic_sensors (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            location_lat DOUBLE PRECISION NOT NULL,
            location_lng DOUBLE PRECISION NOT NULL,
            address TEXT,
            sensor_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'active',
            installation_date TIMESTAMP,
            last_maintenance TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Traffic data table
        """
        CREATE TABLE IF NOT EXISTS traffic_data (
            id SERIAL PRIMARY KEY,
            sensor_id VARCHAR(50) REFERENCES traffic_sensors(id),
            timestamp TIMESTAMP NOT NULL,
            speed_mph DOUBLE PRECISION,
            volume INTEGER,
            density DOUBLE PRECISION,
            occupancy DOUBLE PRECISION,
            congestion_level DOUBLE PRECISION,
            travel_time_index DOUBLE PRECISION,
            weather_condition VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Traffic incidents table
        """
        CREATE TABLE IF NOT EXISTS traffic_incidents (
            id VARCHAR(50) PRIMARY KEY,
            incident_type VARCHAR(50) NOT NULL,
            location_lat DOUBLE PRECISION NOT NULL,
            location_lng DOUBLE PRECISION NOT NULL,
            address TEXT,
            severity VARCHAR(20) NOT NULL,
            description TEXT,
            reported_time TIMESTAMP NOT NULL,
            resolved_time TIMESTAMP,
            estimated_duration INTEGER,
            lanes_affected INTEGER,
            impact_radius DOUBLE PRECISION,
            is_resolved BOOLEAN DEFAULT FALSE,
            reporter_id VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Traffic predictions table
        """
        CREATE TABLE IF NOT EXISTS traffic_predictions (
            id SERIAL PRIMARY KEY,
            sensor_id VARCHAR(50) REFERENCES traffic_sensors(id),
            prediction_time TIMESTAMP NOT NULL,
            predicted_speed DOUBLE PRECISION,
            predicted_volume INTEGER,
            predicted_density DOUBLE PRECISION,
            predicted_severity VARCHAR(20),
            confidence DOUBLE PRECISION,
            model_version VARCHAR(20),
            factors JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Traffic signals table
        """
        CREATE TABLE IF NOT EXISTS traffic_signals (
            id VARCHAR(50) PRIMARY KEY,
            intersection_name VARCHAR(100) NOT NULL,
            location_lat DOUBLE PRECISION NOT NULL,
            location_lng DOUBLE PRECISION NOT NULL,
            address TEXT,
            signal_type VARCHAR(50),
            phases JSONB,
            current_timing JSONB,
            status VARCHAR(20) DEFAULT 'operational',
            last_optimization TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Route optimizations table
        """
        CREATE TABLE IF NOT EXISTS route_optimizations (
            id SERIAL PRIMARY KEY,
            request_id VARCHAR(50) UNIQUE,
            origin_lat DOUBLE PRECISION NOT NULL,
            origin_lng DOUBLE PRECISION NOT NULL,
            destination_lat DOUBLE PRECISION NOT NULL,
            destination_lng DOUBLE PRECISION NOT NULL,
            route_data JSONB NOT NULL,
            optimization_time DOUBLE PRECISION,
            preferences JSONB,
            factors_considered JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # System metrics table
        """
        CREATE TABLE IF NOT EXISTS system_metrics (
            id SERIAL PRIMARY KEY,
            metric_name VARCHAR(100) NOT NULL,
            metric_value DOUBLE PRECISION,
            metric_unit VARCHAR(20),
            location VARCHAR(100),
            timestamp TIMESTAMP NOT NULL,
            tags JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # User sessions table (for API authentication)
        """
        CREATE TABLE IF NOT EXISTS user_sessions (
            id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            session_token VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # API usage logs table
        """
        CREATE TABLE IF NOT EXISTS api_usage_logs (
            id SERIAL PRIMARY KEY,
            endpoint VARCHAR(200) NOT NULL,
            method VARCHAR(10) NOT NULL,
            user_id VARCHAR(50),
            ip_address INET,
            response_code INTEGER,
            response_time DOUBLE PRECISION,
            request_size INTEGER,
            response_size INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    
    # Create indexes
    index_commands = [
        "CREATE INDEX IF NOT EXISTS idx_traffic_data_sensor_timestamp ON traffic_data(sensor_id, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_traffic_data_timestamp ON traffic_data(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_traffic_incidents_location ON traffic_incidents(location_lat, location_lng)",
        "CREATE INDEX IF NOT EXISTS idx_traffic_incidents_time ON traffic_incidents(reported_time)",
        "CREATE INDEX IF NOT EXISTS idx_traffic_predictions_sensor_time ON traffic_predictions(sensor_id, prediction_time)",
        "CREATE INDEX IF NOT EXISTS idx_system_metrics_name_time ON system_metrics(metric_name, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint_time ON api_usage_logs(endpoint, timestamp)"
    ]
    
    try:
        with engine.connect() as conn:
            # Create tables
            for sql_command in sql_commands:
                logger.info(f"Creating table...")
                conn.execute(text(sql_command))
            
            # Create indexes
            for index_command in index_commands:
                logger.info(f"Creating index...")
                conn.execute(text(index_command))
            
            # Commit changes
            conn.commit()
            logger.info("All tables and indexes created successfully")
            
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise
    finally:
        engine.dispose()


def insert_sample_data():
    """Insert sample data for testing"""
    settings = get_settings()
    
    # Get database URL
    db_config = settings.database.postgres
    database_url = (
        f"postgresql://{db_config.username}:{db_config.password}@"
        f"{db_config.host}:{db_config.port}/{db_config.database}"
    )
    
    engine = create_engine(database_url)
    
    # Sample traffic sensors
    sample_sensors = [
        {
            'id': 'sensor_001',
            'name': 'Central Park South',
            'location_lat': 40.7831,
            'location_lng': -73.9712,
            'address': '5th Avenue & 59th Street, New York, NY',
            'sensor_type': 'inductive_loop',
            'installation_date': '2023-01-15'
        },
        {
            'id': 'sensor_002',
            'name': 'Times Square North',
            'location_lat': 40.7505,
            'location_lng': -73.9934,
            'address': 'Broadway & 47th Street, New York, NY',
            'sensor_type': 'radar',
            'installation_date': '2023-02-20'
        },
        {
            'id': 'sensor_003',
            'name': 'Brooklyn Bridge',
            'location_lat': 40.7061,
            'location_lng': -73.9969,
            'address': 'Brooklyn Bridge, New York, NY',
            'sensor_type': 'camera',
            'installation_date': '2023-03-10'
        }
    ]
    
    # Sample traffic signals
    sample_signals = [
        {
            'id': 'signal_001',
            'intersection_name': 'Central Park South & 5th Ave',
            'location_lat': 40.7831,
            'location_lng': -73.9712,
            'address': '5th Avenue & 59th Street, New York, NY',
            'signal_type': 'adaptive',
            'phases': '{"north_south": 45, "east_west": 35, "pedestrian": 15}',
            'current_timing': '{"cycle_length": 95, "last_updated": "2024-01-01T12:00:00"}'
        },
        {
            'id': 'signal_002',
            'intersection_name': 'Times Square & Broadway',
            'location_lat': 40.7505,
            'location_lng': -73.9934,
            'address': 'Broadway & 47th Street, New York, NY',
            'signal_type': 'fixed_time',
            'phases': '{"north_south": 40, "east_west": 40, "pedestrian": 20}',
            'current_timing': '{"cycle_length": 100, "last_updated": "2024-01-01T12:00:00"}'
        }
    ]
    
    try:
        with engine.connect() as conn:
            # Insert sample sensors
            for sensor in sample_sensors:
                conn.execute(text("""
                    INSERT INTO traffic_sensors (id, name, location_lat, location_lng, address, sensor_type, installation_date)
                    VALUES (:id, :name, :location_lat, :location_lng, :address, :sensor_type, :installation_date)
                    ON CONFLICT (id) DO NOTHING
                """), sensor)
            
            # Insert sample signals
            for signal in sample_signals:
                conn.execute(text("""
                    INSERT INTO traffic_signals (id, intersection_name, location_lat, location_lng, address, signal_type, phases, current_timing)
                    VALUES (:id, :intersection_name, :location_lat, :location_lng, :address, :signal_type, :phases, :current_timing)
                    ON CONFLICT (id) DO NOTHING
                """), signal)
            
            conn.commit()
            logger.info("Sample data inserted successfully")
            
    except Exception as e:
        logger.error(f"Error inserting sample data: {e}")
        raise
    finally:
        engine.dispose()


def main():
    """Main initialization function"""
    setup_logging()
    logger.info("Starting database initialization...")
    
    try:
        # Create database
        create_database()
        
        # Create tables
        create_tables()
        
        # Insert sample data
        insert_sample_data()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 