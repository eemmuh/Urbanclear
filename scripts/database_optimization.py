"""
Database Optimization Script for Urbanclear Traffic System
Implements indexes, partitioning, and performance improvements for PostgreSQL
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import asyncpg
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings


class DatabaseOptimizer:
    """Database optimization and performance tuning"""
    
    def __init__(self):
        self.settings = get_settings()
        self.postgres_config = self.settings.database.postgres
        self.connection = None
        
    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = await asyncpg.connect(
                host=self.postgres_config.host,
                port=self.postgres_config.port,
                user=self.postgres_config.username,
                password=self.postgres_config.password,
                database=self.postgres_config.database
            )
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from database"""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from database")
    
    async def create_traffic_data_table(self):
        """Create optimized traffic_data table with partitioning"""
        try:
            # Create main table with partitioning
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS traffic_data (
                id BIGSERIAL,
                sensor_id VARCHAR(50) NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                location_lat DECIMAL(10,8),
                location_lng DECIMAL(11,8),
                location_address TEXT,
                speed_mph DECIMAL(5,2),
                volume INTEGER,
                occupancy DECIMAL(5,4),
                congestion_level DECIMAL(3,2),
                weather_condition VARCHAR(50),
                visibility_meters INTEGER,
                road_condition VARCHAR(20),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            ) PARTITION BY RANGE (timestamp);
            """
            
            await self.connection.execute(create_table_sql)
            logger.info("Created partitioned traffic_data table")
            
            # Create partitions for current and future months
            await self.create_monthly_partitions()
            
        except Exception as e:
            logger.error(f"Failed to create traffic_data table: {e}")
            raise
    
    async def create_monthly_partitions(self):
        """Create monthly partitions for traffic data"""
        try:
            # Create partitions for last 6 months and next 6 months
            current_date = datetime.now()
            
            for i in range(-6, 7):  # 6 months back, current, 6 months forward
                partition_date = current_date.replace(day=1) + timedelta(days=32*i)
                partition_date = partition_date.replace(day=1)  # First day of month
                
                next_month = partition_date.replace(day=28) + timedelta(days=4)
                next_month = next_month.replace(day=1)
                
                partition_name = f"traffic_data_{partition_date.strftime('%Y_%m')}"
                
                create_partition_sql = f"""
                CREATE TABLE IF NOT EXISTS {partition_name} 
                PARTITION OF traffic_data 
                FOR VALUES FROM ('{partition_date.strftime('%Y-%m-%d')}') 
                TO ('{next_month.strftime('%Y-%m-%d')}');
                """
                
                await self.connection.execute(create_partition_sql)
                logger.info(f"Created partition: {partition_name}")
                
        except Exception as e:
            logger.error(f"Failed to create partitions: {e}")
            raise
    
    async def create_indexes(self):
        """Create optimized indexes for traffic data"""
        try:
            indexes = [
                # Primary performance indexes
                {
                    "name": "idx_traffic_data_timestamp",
                    "table": "traffic_data",
                    "columns": ["timestamp"],
                    "method": "BTREE",
                    "description": "Timestamp range queries"
                },
                {
                    "name": "idx_traffic_data_sensor_id",
                    "table": "traffic_data", 
                    "columns": ["sensor_id"],
                    "method": "BTREE",
                    "description": "Sensor-based filtering"
                },
                {
                    "name": "idx_traffic_data_location",
                    "table": "traffic_data",
                    "columns": ["location_lat", "location_lng"],
                    "method": "BTREE",
                    "description": "Geospatial queries"
                },
                {
                    "name": "idx_traffic_data_congestion",
                    "table": "traffic_data",
                    "columns": ["congestion_level"],
                    "method": "BTREE",
                    "description": "Congestion filtering"
                },
                
                # Composite indexes for common query patterns
                {
                    "name": "idx_traffic_data_sensor_timestamp",
                    "table": "traffic_data",
                    "columns": ["sensor_id", "timestamp"],
                    "method": "BTREE",
                    "description": "Sensor time-series queries"
                },
                {
                    "name": "idx_traffic_data_time_congestion",
                    "table": "traffic_data",
                    "columns": ["timestamp", "congestion_level"],
                    "method": "BTREE",
                    "description": "Time-based congestion analysis"
                },
                {
                    "name": "idx_traffic_data_speed_volume",
                    "table": "traffic_data",
                    "columns": ["speed_mph", "volume"],
                    "method": "BTREE", 
                    "description": "Speed-volume correlation queries"
                },
                
                # GiST index for geospatial operations
                {
                    "name": "idx_traffic_data_location_gist",
                    "table": "traffic_data",
                    "columns": ["ST_MakePoint(location_lng, location_lat)"],
                    "method": "GIST",
                    "description": "Advanced geospatial operations"
                },
                
                # Partial indexes for common filters
                {
                    "name": "idx_traffic_data_high_congestion",
                    "table": "traffic_data",
                    "columns": ["timestamp", "sensor_id"],
                    "method": "BTREE",
                    "condition": "congestion_level > 0.7",
                    "description": "High congestion incidents"
                },
                {
                    "name": "idx_traffic_data_recent",
                    "table": "traffic_data",
                    "columns": ["sensor_id", "speed_mph", "volume"],
                    "method": "BTREE",
                    "condition": "timestamp >= NOW() - INTERVAL '24 hours'",
                    "description": "Recent data analysis"
                }
            ]
            
            for index in indexes:
                await self.create_index(index)
                
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    async def create_index(self, index_config: Dict[str, Any]):
        """Create a single index"""
        try:
            columns_str = ", ".join(index_config["columns"])
            index_sql = f"""
            CREATE INDEX IF NOT EXISTS {index_config['name']} 
            ON {index_config['table']} 
            USING {index_config['method']} ({columns_str})
            """
            
            # Add WHERE clause for partial indexes
            if "condition" in index_config:
                index_sql += f" WHERE {index_config['condition']}"
            
            await self.connection.execute(index_sql)
            logger.info(f"Created index: {index_config['name']} - {index_config['description']}")
            
        except Exception as e:
            logger.error(f"Failed to create index {index_config['name']}: {e}")
            raise
    
    async def create_incidents_table(self):
        """Create optimized incidents table"""
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS traffic_incidents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                incident_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                location_lat DECIMAL(10,8),
                location_lng DECIMAL(11,8),
                location_address TEXT,
                description TEXT,
                reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                resolved_at TIMESTAMPTZ,
                estimated_duration INTEGER, -- minutes
                affected_lanes INTEGER,
                traffic_impact DECIMAL(3,2), -- 0-1 scale
                reporter_id VARCHAR(50),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
            
            await self.connection.execute(create_table_sql)
            logger.info("Created traffic_incidents table")
            
            # Create indexes for incidents
            incident_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_incidents_status ON traffic_incidents(status) WHERE status = 'active';",
                "CREATE INDEX IF NOT EXISTS idx_incidents_reported_at ON traffic_incidents(reported_at);",
                "CREATE INDEX IF NOT EXISTS idx_incidents_severity ON traffic_incidents(severity);",
                "CREATE INDEX IF NOT EXISTS idx_incidents_location ON traffic_incidents(location_lat, location_lng);",
                "CREATE INDEX IF NOT EXISTS idx_incidents_type_severity ON traffic_incidents(incident_type, severity);"
            ]
            
            for index_sql in incident_indexes:
                await self.connection.execute(index_sql)
                
            logger.info("Created incidents table indexes")
            
        except Exception as e:
            logger.error(f"Failed to create incidents table: {e}")
            raise
    
    async def create_analytics_views(self):
        """Create materialized views for analytics"""
        try:
            # Hourly traffic summary view
            hourly_view_sql = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS traffic_hourly_summary AS
            SELECT 
                sensor_id,
                DATE_TRUNC('hour', timestamp) as hour,
                AVG(speed_mph) as avg_speed,
                MAX(speed_mph) as max_speed,
                MIN(speed_mph) as min_speed,
                AVG(volume) as avg_volume,
                MAX(volume) as max_volume,
                AVG(congestion_level) as avg_congestion,
                MAX(congestion_level) as max_congestion,
                COUNT(*) as record_count,
                STDDEV(speed_mph) as speed_variance
            FROM traffic_data
            WHERE timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY sensor_id, DATE_TRUNC('hour', timestamp)
            ORDER BY hour DESC, sensor_id;
            """
            
            await self.connection.execute(hourly_view_sql)
            
            # Create index on materialized view
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_hourly_summary_hour_sensor 
                ON traffic_hourly_summary(hour, sensor_id);
            """)
            
            # Daily traffic summary view
            daily_view_sql = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS traffic_daily_summary AS
            SELECT 
                sensor_id,
                DATE_TRUNC('day', timestamp) as date,
                AVG(speed_mph) as avg_speed,
                AVG(volume) as avg_volume,
                AVG(congestion_level) as avg_congestion,
                COUNT(*) as total_records,
                COUNT(CASE WHEN congestion_level > 0.7 THEN 1 END) as high_congestion_periods,
                MAX(congestion_level) as peak_congestion,
                MIN(speed_mph) as min_speed_recorded
            FROM traffic_data
            WHERE timestamp >= NOW() - INTERVAL '90 days'
            GROUP BY sensor_id, DATE_TRUNC('day', timestamp)
            ORDER BY date DESC, sensor_id;
            """
            
            await self.connection.execute(daily_view_sql)
            
            # Create index on daily view
            await self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_summary_date_sensor 
                ON traffic_daily_summary(date, sensor_id);
            """)
            
            logger.info("Created materialized views for analytics")
            
        except Exception as e:
            logger.error(f"Failed to create analytics views: {e}")
            raise
    
    async def setup_database_functions(self):
        """Create useful database functions for traffic analysis"""
        try:
            functions = [
                # Function to calculate distance between two points
                """
                CREATE OR REPLACE FUNCTION calculate_distance(
                    lat1 DECIMAL, lng1 DECIMAL, 
                    lat2 DECIMAL, lng2 DECIMAL
                ) RETURNS DECIMAL AS $$
                BEGIN
                    RETURN 6371 * acos(
                        cos(radians(lat1)) * 
                        cos(radians(lat2)) * 
                        cos(radians(lng2) - radians(lng1)) + 
                        sin(radians(lat1)) * 
                        sin(radians(lat2))
                    );
                END;
                $$ LANGUAGE plpgsql IMMUTABLE;
                """,
                
                # Function to get congestion level description
                """
                CREATE OR REPLACE FUNCTION get_congestion_description(level DECIMAL)
                RETURNS TEXT AS $$
                BEGIN
                    CASE 
                        WHEN level < 0.3 THEN RETURN 'Light';
                        WHEN level < 0.6 THEN RETURN 'Moderate';
                        WHEN level < 0.8 THEN RETURN 'Heavy';
                        ELSE RETURN 'Severe';
                    END CASE;
                END;
                $$ LANGUAGE plpgsql IMMUTABLE;
                """,
                
                # Function to check if time is rush hour
                """
                CREATE OR REPLACE FUNCTION is_rush_hour(ts TIMESTAMPTZ)
                RETURNS BOOLEAN AS $$
                BEGIN
                    RETURN EXTRACT(hour FROM ts) BETWEEN 7 AND 9 
                        OR EXTRACT(hour FROM ts) BETWEEN 17 AND 19;
                END;
                $$ LANGUAGE plpgsql IMMUTABLE;
                """,
                
                # Function to update materialized views
                """
                CREATE OR REPLACE FUNCTION refresh_traffic_views()
                RETURNS VOID AS $$
                BEGIN
                    REFRESH MATERIALIZED VIEW CONCURRENTLY traffic_hourly_summary;
                    REFRESH MATERIALIZED VIEW CONCURRENTLY traffic_daily_summary;
                END;
                $$ LANGUAGE plpgsql;
                """
            ]
            
            for function_sql in functions:
                await self.connection.execute(function_sql)
                
            logger.info("Created database functions")
            
        except Exception as e:
            logger.error(f"Failed to create database functions: {e}")
            raise
    
    async def setup_triggers(self):
        """Setup database triggers for automatic maintenance"""
        try:
            # Trigger to update updated_at timestamp
            trigger_sql = """
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            DROP TRIGGER IF EXISTS update_traffic_data_updated_at ON traffic_data;
            CREATE TRIGGER update_traffic_data_updated_at
                BEFORE UPDATE ON traffic_data
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
                
            DROP TRIGGER IF EXISTS update_incidents_updated_at ON traffic_incidents;
            CREATE TRIGGER update_incidents_updated_at
                BEFORE UPDATE ON traffic_incidents
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """
            
            await self.connection.execute(trigger_sql)
            logger.info("Created database triggers")
            
        except Exception as e:
            logger.error(f"Failed to create triggers: {e}")
            raise
    
    async def optimize_postgresql_settings(self):
        """Apply PostgreSQL performance optimizations"""
        try:
            # These settings require superuser privileges
            # In production, these should be set in postgresql.conf
            optimizations = [
                "SET random_page_cost = 1.1;",  # For SSD storage
                "SET effective_cache_size = '1GB';",
                "SET maintenance_work_mem = '256MB';",
                "SET checkpoint_completion_target = 0.7;",
                "SET wal_buffers = '16MB';",
                "SET default_statistics_target = 100;",
            ]
            
            for optimization in optimizations:
                try:
                    await self.connection.execute(optimization)
                    logger.info(f"Applied optimization: {optimization}")
                except Exception as e:
                    logger.warning(f"Could not apply optimization {optimization}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to apply optimizations: {e}")
    
    async def analyze_tables(self):
        """Analyze tables to update statistics"""
        try:
            tables = ['traffic_data', 'traffic_incidents']
            
            for table in tables:
                await self.connection.execute(f"ANALYZE {table};")
                logger.info(f"Analyzed table: {table}")
                
        except Exception as e:
            logger.error(f"Failed to analyze tables: {e}")
            raise
    
    async def setup_scheduled_maintenance(self):
        """Setup scheduled maintenance tasks"""
        try:
            # Create a maintenance log table
            maintenance_table_sql = """
            CREATE TABLE IF NOT EXISTS maintenance_log (
                id SERIAL PRIMARY KEY,
                task_name VARCHAR(100) NOT NULL,
                executed_at TIMESTAMPTZ DEFAULT NOW(),
                duration_seconds INTEGER,
                status VARCHAR(20) DEFAULT 'success',
                details TEXT
            );
            """
            
            await self.connection.execute(maintenance_table_sql)
            
            # Function to log maintenance tasks
            log_function_sql = """
            CREATE OR REPLACE FUNCTION log_maintenance_task(
                task_name TEXT, 
                duration_seconds INTEGER DEFAULT NULL,
                status TEXT DEFAULT 'success',
                details TEXT DEFAULT NULL
            ) RETURNS VOID AS $$
            BEGIN
                INSERT INTO maintenance_log (task_name, duration_seconds, status, details)
                VALUES (task_name, duration_seconds, status, details);
            END;
            $$ LANGUAGE plpgsql;
            """
            
            await self.connection.execute(log_function_sql)
            logger.info("Created maintenance logging system")
            
        except Exception as e:
            logger.error(f"Failed to setup maintenance logging: {e}")
            raise
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        try:
            stats = {}
            
            # Table sizes
            size_query = """
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """
            
            table_sizes = await self.connection.fetch(size_query)
            stats['table_sizes'] = [dict(row) for row in table_sizes]
            
            # Index usage
            index_query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan as times_used,
                pg_size_pretty(pg_relation_size(indexrelid)) as size
            FROM pg_stat_user_indexes 
            ORDER BY idx_scan DESC;
            """
            
            index_stats = await self.connection.fetch(index_query)
            stats['index_usage'] = [dict(row) for row in index_stats]
            
            # Connection stats
            connection_query = """
            SELECT 
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections
            FROM pg_stat_activity;
            """
            
            connection_stats = await self.connection.fetchrow(connection_query)
            stats['connections'] = dict(connection_stats)
            
            logger.info("Retrieved performance statistics")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {}
    
    async def run_full_optimization(self):
        """Run complete database optimization"""
        try:
            logger.info("Starting comprehensive database optimization")
            
            await self.connect()
            
            # Create optimized tables
            await self.create_traffic_data_table()
            await self.create_incidents_table()
            
            # Create indexes
            await self.create_indexes()
            
            # Create views and functions
            await self.create_analytics_views()
            await self.setup_database_functions()
            await self.setup_triggers()
            
            # Setup maintenance
            await self.setup_scheduled_maintenance()
            
            # Apply optimizations
            await self.optimize_postgresql_settings()
            await self.analyze_tables()
            
            # Get performance stats
            stats = await self.get_performance_stats()
            logger.info(f"Optimization completed. Performance stats: {stats}")
            
            logger.info("✅ Database optimization completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Database optimization failed: {e}")
            raise
        finally:
            await self.disconnect()


async def main():
    """Main function to run database optimization"""
    optimizer = DatabaseOptimizer()
    await optimizer.run_full_optimization()


if __name__ == "__main__":
    asyncio.run(main()) 