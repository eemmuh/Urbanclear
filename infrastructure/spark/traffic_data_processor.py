"""
Spark Jobs for Traffic Data Processing and Analytics
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, avg, max, min, count, when, window, 
    lag, lead, stddev, percentile_approx, 
    date_format, hour, dayofweek, month,
    regexp_extract, split, explode, 
    collect_list, struct, to_timestamp
)
from pyspark.sql.types import (
    StructType, StructField, StringType, 
    IntegerType, FloatType, TimestampType, 
    BooleanType, ArrayType
)
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.stat import Correlation
from loguru import logger

from src.core.config import get_settings


class TrafficDataProcessor:
    """Spark-based traffic data processor for batch analytics"""
    
    def __init__(self, app_name: str = "TrafficDataProcessor"):
        self.app_name = app_name
        self.spark = None
        self.settings = get_settings()
        
    def initialize_spark(self) -> SparkSession:
        """Initialize Spark session with optimized configuration"""
        try:
            self.spark = SparkSession.builder \
                .appName(self.app_name) \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.sql.adaptive.skewJoin.enabled", "true") \
                .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
                .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
                .config("spark.sql.adaptive.advisoryPartitionSizeInBytes", "128MB") \
                .config("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB") \
                .getOrCreate()
            
            self.spark.sparkContext.setLogLevel("WARN")
            logger.info(f"Spark session initialized: {self.app_name}")
            return self.spark
            
        except Exception as e:
            logger.error(f"Failed to initialize Spark session: {e}")
            raise
    
    def load_traffic_data(self, data_source: str, start_date: str, end_date: str) -> DataFrame:
        """Load traffic data from various sources"""
        try:
            if data_source == "postgres":
                return self._load_from_postgres(start_date, end_date)
            elif data_source == "kafka":
                return self._load_from_kafka(start_date, end_date)
            elif data_source == "csv":
                return self._load_from_csv(start_date, end_date)
            else:
                raise ValueError(f"Unsupported data source: {data_source}")
                
        except Exception as e:
            logger.error(f"Failed to load traffic data: {e}")
            raise
    
    def _load_from_postgres(self, start_date: str, end_date: str) -> DataFrame:
        """Load data from PostgreSQL"""
        postgres_config = self.settings.database.postgres
        
        df = self.spark.read \
            .format("jdbc") \
            .option("url", f"jdbc:postgresql://{postgres_config.host}:{postgres_config.port}/{postgres_config.database}") \
            .option("dbtable", f"""
                (SELECT * FROM traffic_data 
                 WHERE timestamp >= '{start_date}' AND timestamp <= '{end_date}') as traffic_subset
            """) \
            .option("user", postgres_config.username) \
            .option("password", postgres_config.password) \
            .option("driver", "org.postgresql.Driver") \
            .load()
        
        logger.info(f"Loaded {df.count()} records from PostgreSQL")
        return df
    
    def _load_from_kafka(self, start_date: str, end_date: str) -> DataFrame:
        """Load data from Kafka (for streaming processing)"""
        kafka_config = self.settings.kafka
        
        df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", ",".join(kafka_config.bootstrap_servers)) \
            .option("subscribe", kafka_config.topics["traffic_data"]) \
            .option("startingOffsets", "earliest") \
            .load()
        
        # Parse JSON data
        traffic_schema = StructType([
            StructField("sensor_id", StringType(), True),
            StructField("timestamp", TimestampType(), True),
            StructField("location", StructType([
                StructField("latitude", FloatType(), True),
                StructField("longitude", FloatType(), True),
                StructField("address", StringType(), True)
            ]), True),
            StructField("speed_mph", FloatType(), True),
            StructField("volume", IntegerType(), True),
            StructField("occupancy", FloatType(), True),
            StructField("congestion_level", FloatType(), True)
        ])
        
        parsed_df = df.select(
            col("timestamp").alias("kafka_timestamp"),
            col("value").cast("string").alias("json_data")
        ).select(
            col("kafka_timestamp"),
            from_json(col("json_data"), traffic_schema).alias("data")
        ).select(
            col("kafka_timestamp"),
            col("data.*")
        )
        
        logger.info("Configured Kafka streaming source")
        return parsed_df
    
    def _load_from_csv(self, start_date: str, end_date: str) -> DataFrame:
        """Load data from CSV files"""
        data_path = "data/processed/traffic_data.csv"
        
        df = self.spark.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .option("timestampFormat", "yyyy-MM-dd HH:mm:ss") \
            .csv(data_path)
        
        # Filter by date range
        df = df.filter(
            (col("timestamp") >= start_date) & 
            (col("timestamp") <= end_date)
        )
        
        logger.info(f"Loaded {df.count()} records from CSV")
        return df
    
    def analyze_traffic_patterns(self, df: DataFrame) -> Dict[str, DataFrame]:
        """Analyze traffic patterns and generate insights"""
        try:
            results = {}
            
            # 1. Hourly traffic patterns
            hourly_patterns = df.groupBy(
                hour(col("timestamp")).alias("hour")
            ).agg(
                avg("speed_mph").alias("avg_speed"),
                avg("volume").alias("avg_volume"),
                avg("congestion_level").alias("avg_congestion"),
                count("*").alias("record_count")
            ).orderBy("hour")
            
            results["hourly_patterns"] = hourly_patterns
            
            # 2. Daily traffic patterns
            daily_patterns = df.groupBy(
                dayofweek(col("timestamp")).alias("day_of_week")
            ).agg(
                avg("speed_mph").alias("avg_speed"),
                avg("volume").alias("avg_volume"),
                avg("congestion_level").alias("avg_congestion"),
                count("*").alias("record_count")
            ).orderBy("day_of_week")
            
            results["daily_patterns"] = daily_patterns
            
            # 3. Location-based analysis
            location_analysis = df.groupBy("sensor_id").agg(
                avg("speed_mph").alias("avg_speed"),
                max("speed_mph").alias("max_speed"),
                min("speed_mph").alias("min_speed"),
                avg("volume").alias("avg_volume"),
                avg("congestion_level").alias("avg_congestion"),
                stddev("speed_mph").alias("speed_variance"),
                count("*").alias("total_records")
            ).orderBy(col("avg_congestion").desc())
            
            results["location_analysis"] = location_analysis
            
            # 4. Rush hour analysis
            rush_hour_analysis = df.withColumn(
                "hour", hour(col("timestamp"))
            ).withColumn(
                "is_rush_hour", 
                when((col("hour") >= 7) & (col("hour") <= 9), "Morning Rush")
                .when((col("hour") >= 17) & (col("hour") <= 19), "Evening Rush")
                .otherwise("Regular")
            ).groupBy("is_rush_hour").agg(
                avg("speed_mph").alias("avg_speed"),
                avg("volume").alias("avg_volume"),
                avg("congestion_level").alias("avg_congestion"),
                count("*").alias("record_count")
            )
            
            results["rush_hour_analysis"] = rush_hour_analysis
            
            # 5. Congestion hotspots
            congestion_hotspots = df.filter(
                col("congestion_level") > 0.7
            ).groupBy("sensor_id").agg(
                count("*").alias("congestion_events"),
                avg("congestion_level").alias("avg_congestion_level"),
                avg("speed_mph").alias("avg_speed_during_congestion")
            ).orderBy(col("congestion_events").desc())
            
            results["congestion_hotspots"] = congestion_hotspots
            
            logger.info("Traffic pattern analysis completed")
            return results
            
        except Exception as e:
            logger.error(f"Failed to analyze traffic patterns: {e}")
            raise
    
    def detect_anomalies(self, df: DataFrame) -> DataFrame:
        """Detect traffic anomalies using statistical methods"""
        try:
            # Calculate percentiles for anomaly detection
            speed_percentiles = df.select(
                percentile_approx("speed_mph", 0.05).alias("speed_p5"),
                percentile_approx("speed_mph", 0.95).alias("speed_p95"),
                percentile_approx("volume", 0.05).alias("volume_p5"),
                percentile_approx("volume", 0.95).alias("volume_p95")
            ).collect()[0]
            
            # Mark anomalies
            anomalies = df.withColumn(
                "speed_anomaly",
                when(
                    (col("speed_mph") < speed_percentiles["speed_p5"]) |
                    (col("speed_mph") > speed_percentiles["speed_p95"]),
                    True
                ).otherwise(False)
            ).withColumn(
                "volume_anomaly",
                when(
                    (col("volume") < speed_percentiles["volume_p5"]) |
                    (col("volume") > speed_percentiles["volume_p95"]),
                    True
                ).otherwise(False)
            ).withColumn(
                "is_anomaly",
                col("speed_anomaly") | col("volume_anomaly")
            )
            
            anomaly_summary = anomalies.filter(col("is_anomaly") == True)
            
            logger.info(f"Detected {anomaly_summary.count()} anomalies")
            return anomaly_summary
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            raise
    
    def cluster_traffic_patterns(self, df: DataFrame, k: int = 5) -> DataFrame:
        """Cluster traffic patterns using K-means"""
        try:
            # Prepare features for clustering
            feature_cols = ["speed_mph", "volume", "congestion_level"]
            assembler = VectorAssembler(
                inputCols=feature_cols,
                outputCol="features"
            )
            
            # Scale features
            scaler = StandardScaler(
                inputCol="features",
                outputCol="scaledFeatures"
            )
            
            # Prepare data
            feature_df = assembler.transform(df)
            scaler_model = scaler.fit(feature_df)
            scaled_df = scaler_model.transform(feature_df)
            
            # Apply K-means clustering
            kmeans = KMeans(
                k=k,
                featuresCol="scaledFeatures",
                predictionCol="cluster",
                seed=42
            )
            
            model = kmeans.fit(scaled_df)
            clustered_df = model.transform(scaled_df)
            
            # Analyze clusters
            cluster_summary = clustered_df.groupBy("cluster").agg(
                count("*").alias("count"),
                avg("speed_mph").alias("avg_speed"),
                avg("volume").alias("avg_volume"),
                avg("congestion_level").alias("avg_congestion")
            ).orderBy("cluster")
            
            logger.info(f"Created {k} traffic pattern clusters")
            return cluster_summary
            
        except Exception as e:
            logger.error(f"Failed to cluster traffic patterns: {e}")
            raise
    
    def generate_insights(self, analysis_results: Dict[str, DataFrame]) -> Dict[str, str]:
        """Generate business insights from analysis results"""
        try:
            insights = {}
            
            # Peak hour insights
            hourly_data = analysis_results["hourly_patterns"].collect()
            peak_congestion_hour = max(hourly_data, key=lambda x: x.avg_congestion)
            insights["peak_congestion_hour"] = f"Peak congestion occurs at {peak_congestion_hour.hour}:00 with {peak_congestion_hour.avg_congestion:.2f} congestion level"
            
            # Location insights
            location_data = analysis_results["location_analysis"].collect()
            most_congested_location = location_data[0]  # Already ordered by congestion desc
            insights["most_congested_location"] = f"Location {most_congested_location.sensor_id} has the highest average congestion at {most_congested_location.avg_congestion:.2f}"
            
            # Rush hour impact
            rush_hour_data = analysis_results["rush_hour_analysis"].collect()
            rush_hour_impact = {}
            for row in rush_hour_data:
                rush_hour_impact[row.is_rush_hour] = row.avg_speed
            
            if "Morning Rush" in rush_hour_impact and "Regular" in rush_hour_impact:
                speed_drop = rush_hour_impact["Regular"] - rush_hour_impact["Morning Rush"]
                insights["rush_hour_impact"] = f"Average speed drops by {speed_drop:.1f} mph during morning rush hour"
            
            logger.info("Generated business insights")
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return {}
    
    def save_results(self, results: Dict[str, DataFrame], output_path: str):
        """Save analysis results to various formats"""
        try:
            for name, df in results.items():
                # Save as Parquet for efficient storage
                df.coalesce(1).write \
                    .mode("overwrite") \
                    .option("compression", "snappy") \
                    .parquet(f"{output_path}/{name}.parquet")
                
                # Save as CSV for easy viewing
                df.coalesce(1).write \
                    .mode("overwrite") \
                    .option("header", "true") \
                    .csv(f"{output_path}/{name}.csv")
                
                logger.info(f"Saved {name} results to {output_path}")
                
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise
    
    def run_batch_processing(self, start_date: str, end_date: str, output_path: str = "data/processed/batch_results"):
        """Run complete batch processing pipeline"""
        try:
            logger.info(f"Starting batch processing for {start_date} to {end_date}")
            
            # Initialize Spark
            self.initialize_spark()
            
            # Load data
            df = self.load_traffic_data("postgres", start_date, end_date)
            
            # Analyze patterns
            analysis_results = self.analyze_traffic_patterns(df)
            
            # Detect anomalies
            anomalies = self.detect_anomalies(df)
            analysis_results["anomalies"] = anomalies
            
            # Cluster patterns
            clusters = self.cluster_traffic_patterns(df)
            analysis_results["clusters"] = clusters
            
            # Generate insights
            insights = self.generate_insights(analysis_results)
            
            # Save results
            self.save_results(analysis_results, output_path)
            
            # Log insights
            for insight_type, insight_text in insights.items():
                logger.info(f"INSIGHT - {insight_type}: {insight_text}")
            
            logger.info("Batch processing completed successfully")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise
        finally:
            if self.spark:
                self.spark.stop()
                logger.info("Spark session closed")


def main():
    """Main function for running traffic data processing"""
    processor = TrafficDataProcessor()
    
    # Calculate date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Run batch processing
    processor.run_batch_processing(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        output_path="data/processed/batch_results"
    )


if __name__ == "__main__":
    main() 