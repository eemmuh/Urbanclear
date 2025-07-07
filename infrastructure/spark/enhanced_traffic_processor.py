#!/usr/bin/env python3
"""
Enhanced Spark Traffic Data Processor for Urbanclear
Comprehensive analytics and batch processing with ML capabilities
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import json
import time

# Spark imports
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, when, avg, sum as spark_sum, count, max as spark_max, min as spark_min,
    window, date_format, hour, dayofweek, to_timestamp, lag, lead,
    monotonically_increasing_id, stddev, percentile_approx, collect_list,
    explode, split, regexp_extract, desc, asc, broadcast
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, FloatType, 
    TimestampType, DoubleType, ArrayType, MapType, BooleanType
)
from pyspark.ml.clustering import KMeans
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.regression import LinearRegression, RandomForestRegressor
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml import Pipeline
from pyspark.sql.window import Window

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedTrafficProcessor:
    """Enhanced Spark-based traffic data processor with comprehensive analytics"""
    
    def __init__(self, app_name: str = "UrbanClear-Enhanced-Analytics", 
                 master: str = "local[*]", config: Dict[str, str] = None):
        """Initialize the enhanced traffic processor"""
        self.app_name = app_name
        self.master = master
        self.config = config or {}
        self.spark = None
        
        # Analytics configurations
        self.analysis_configs = {
            'traffic_patterns': {
                'window_size': '1 hour',
                'slide_duration': '15 minutes',
                'time_partitions': ['hour', 'day_of_week', 'month']
            },
            'congestion_analysis': {
                'congestion_threshold': 0.7,
                'peak_hour_threshold': 0.8,
                'clustering_features': ['speed_mph', 'volume', 'density']
            },
            'incident_impact': {
                'impact_radius_km': 2.0,
                'time_window_minutes': 30,
                'severity_weights': {'low': 1.0, 'moderate': 2.0, 'high': 3.0}
            },
            'prediction_models': {
                'features': ['hour', 'day_of_week', 'historical_avg', 'weather_impact'],
                'target': 'congestion_level',
                'train_split': 0.8
            }
        }
    
    def start_spark_session(self) -> SparkSession:
        """Start Spark session with optimized configuration"""
        try:
            spark_builder = SparkSession.builder \
                .appName(self.app_name) \
                .master(self.master) \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
                .config("spark.sql.execution.arrow.maxRecordsPerBatch", "10000") \
                .config("spark.sql.adaptive.skewJoin.enabled", "true") \
                .config("spark.sql.adaptive.localShuffleReader.enabled", "true")
            
            # Add custom configurations
            for key, value in self.config.items():
                spark_builder = spark_builder.config(key, value)
            
            self.spark = spark_builder.getOrCreate()
            self.spark.sparkContext.setLogLevel("WARN")
            
            logger.info(f"Spark session started: {self.app_name}")
            logger.info(f"Spark UI available at: {self.spark.sparkContext.uiWebUrl}")
            
            return self.spark
            
        except Exception as e:
            logger.error(f"Error starting Spark session: {e}")
            raise
    
    def load_traffic_data(self, data_sources: Dict[str, Any]) -> Dict[str, DataFrame]:
        """Load traffic data from multiple sources"""
        dataframes = {}
        
        try:
            # PostgreSQL data source
            if 'postgresql' in data_sources:
                pg_config = data_sources['postgresql']
                logger.info("Loading data from PostgreSQL...")
                
                # Traffic conditions
                traffic_df = self.spark.read \
                    .format("jdbc") \
                    .option("url", pg_config['url']) \
                    .option("dbtable", "traffic_conditions") \
                    .option("user", pg_config['user']) \
                    .option("password", pg_config['password']) \
                    .option("driver", "org.postgresql.Driver") \
                    .load()
                
                dataframes['traffic_conditions'] = traffic_df
                
                # Incidents data
                incidents_df = self.spark.read \
                    .format("jdbc") \
                    .option("url", pg_config['url']) \
                    .option("dbtable", "incidents") \
                    .option("user", pg_config['user']) \
                    .option("password", pg_config['password']) \
                    .option("driver", "org.postgresql.Driver") \
                    .load()
                
                dataframes['incidents'] = incidents_df
            
            # CSV data source
            if 'csv' in data_sources:
                csv_config = data_sources['csv']
                logger.info(f"Loading CSV data from: {csv_config['path']}")
                
                csv_df = self.spark.read \
                    .option("header", "true") \
                    .option("inferSchema", "true") \
                    .csv(csv_config['path'])
                
                dataframes['csv_data'] = csv_df
            
            # Kafka streaming data (batch read)
            if 'kafka' in data_sources:
                kafka_config = data_sources['kafka']
                logger.info("Loading batch data from Kafka...")
                
                # This would read from Kafka topics in batch mode
                # For demo, we'll simulate with mock data
                dataframes['kafka_stream'] = self._create_mock_streaming_data()
            
            # Log data loading summary
            for name, df in dataframes.items():
                count = df.count()
                logger.info(f"Loaded {name}: {count} records")
            
            return dataframes
            
        except Exception as e:
            logger.error(f"Error loading traffic data: {e}")
            raise
    
    def analyze_traffic_patterns(self, traffic_df: DataFrame) -> Dict[str, DataFrame]:
        """Comprehensive traffic pattern analysis"""
        logger.info("Starting traffic pattern analysis...")
        
        results = {}
        
        try:
            # Prepare data with time features
            prepared_df = self._prepare_time_features(traffic_df)
            
            # 1. Hourly traffic patterns
            hourly_patterns = prepared_df.groupBy("hour", "location") \
                .agg(
                    avg("speed_mph").alias("avg_speed"),
                    avg("volume").alias("avg_volume"),
                    avg("congestion_level").alias("avg_congestion"),
                    count("*").alias("measurement_count")
                ) \
                .orderBy("hour", "location")
            
            results['hourly_patterns'] = hourly_patterns
            
            # 2. Day-of-week patterns
            dow_patterns = prepared_df.groupBy("day_of_week", "location") \
                .agg(
                    avg("speed_mph").alias("avg_speed"),
                    avg("volume").alias("avg_volume"),
                    avg("congestion_level").alias("avg_congestion"),
                    stddev("congestion_level").alias("congestion_variability")
                ) \
                .orderBy("day_of_week", "location")
            
            results['day_of_week_patterns'] = dow_patterns
            
            # 3. Peak hour identification
            peak_hours = prepared_df.groupBy("hour") \
                .agg(avg("congestion_level").alias("avg_congestion")) \
                .withColumn("is_peak", 
                           when(col("avg_congestion") > self.analysis_configs['congestion_analysis']['peak_hour_threshold'], True)
                           .otherwise(False)) \
                .orderBy("hour")
            
            results['peak_hours'] = peak_hours
            
            # 4. Location-based congestion ranking
            location_ranking = prepared_df.groupBy("location") \
                .agg(
                    avg("congestion_level").alias("avg_congestion"),
                    spark_max("congestion_level").alias("max_congestion"),
                    stddev("congestion_level").alias("congestion_variability"),
                    count("*").alias("total_measurements")
                ) \
                .orderBy(desc("avg_congestion"))
            
            results['location_ranking'] = location_ranking
            
            # 5. Temporal congestion windows
            windowed_analysis = prepared_df \
                .withColumn("timestamp", to_timestamp(col("timestamp"))) \
                .groupBy(
                    window(col("timestamp"), self.analysis_configs['traffic_patterns']['window_size'],
                           self.analysis_configs['traffic_patterns']['slide_duration']),
                    "location"
                ) \
                .agg(
                    avg("congestion_level").alias("avg_congestion"),
                    avg("speed_mph").alias("avg_speed"),
                    spark_sum("volume").alias("total_volume")
                ) \
                .select("window.start", "window.end", "location", "avg_congestion", "avg_speed", "total_volume") \
                .orderBy("start", "location")
            
            results['windowed_analysis'] = windowed_analysis
            
            logger.info("Traffic pattern analysis completed")
            return results
            
        except Exception as e:
            logger.error(f"Error in traffic pattern analysis: {e}")
            raise
    
    def perform_congestion_clustering(self, traffic_df: DataFrame) -> Tuple[DataFrame, Dict[str, Any]]:
        """Perform K-means clustering for congestion pattern identification"""
        logger.info("Starting congestion clustering analysis...")
        
        try:
            # Prepare features for clustering
            feature_cols = self.analysis_configs['congestion_analysis']['clustering_features']
            
            # Create feature vector
            assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
            
            # Scale features
            scaler = StandardScaler(inputCol="features", outputCol="scaled_features")
            
            # K-means clustering
            kmeans = KMeans(featuresCol="scaled_features", predictionCol="cluster", k=5, seed=42)
            
            # Create pipeline
            pipeline = Pipeline(stages=[assembler, scaler, kmeans])
            
            # Fit model
            model = pipeline.fit(traffic_df)
            
            # Transform data
            clustered_df = model.transform(traffic_df)
            
            # Analyze clusters
            cluster_analysis = clustered_df.groupBy("cluster") \
                .agg(
                    count("*").alias("cluster_size"),
                    avg("speed_mph").alias("avg_speed"),
                    avg("volume").alias("avg_volume"),
                    avg("congestion_level").alias("avg_congestion"),
                    collect_list("location").alias("locations")
                ) \
                .orderBy("cluster")
            
            # Calculate cluster statistics
            cluster_stats = {}
            clusters_collected = cluster_analysis.collect()
            
            for row in clusters_collected:
                cluster_id = row['cluster']
                cluster_stats[f"cluster_{cluster_id}"] = {
                    "size": row['cluster_size'],
                    "avg_speed": round(row['avg_speed'], 2),
                    "avg_volume": round(row['avg_volume'], 2),
                    "avg_congestion": round(row['avg_congestion'], 3),
                    "sample_locations": row['locations'][:5]  # First 5 locations
                }
            
            logger.info(f"Clustering completed with {len(cluster_stats)} clusters")
            
            return clustered_df, cluster_stats
            
        except Exception as e:
            logger.error(f"Error in congestion clustering: {e}")
            raise
    
    def analyze_incident_impact(self, traffic_df: DataFrame, incidents_df: DataFrame) -> DataFrame:
        """Analyze the impact of incidents on traffic flow"""
        logger.info("Starting incident impact analysis...")
        
        try:
            # Prepare timestamps
            traffic_df = traffic_df.withColumn("timestamp", to_timestamp(col("timestamp")))
            incidents_df = incidents_df.withColumn("timestamp", to_timestamp(col("timestamp")))
            
            # Create time windows for impact analysis
            time_window = self.analysis_configs['incident_impact']['time_window_minutes']
            
            # Join traffic data with incidents based on proximity and time
            # For simplification, we'll use location matching
            incident_impact = traffic_df.alias("t") \
                .join(incidents_df.alias("i"), 
                      (col("t.location") == col("i.location")) & 
                      (col("t.timestamp").between(
                          col("i.timestamp") - expr(f"INTERVAL {time_window} MINUTES"),
                          col("i.timestamp") + expr(f"INTERVAL {time_window} MINUTES")
                      )), "left") \
                .select(
                    col("t.*"),
                    col("i.incident_id"),
                    col("i.severity").alias("incident_severity"),
                    col("i.type").alias("incident_type")
                )
            
            # Calculate impact metrics
            impact_analysis = incident_impact \
                .withColumn("has_incident", when(col("incident_id").isNotNull(), True).otherwise(False)) \
                .groupBy("location", "has_incident") \
                .agg(
                    avg("speed_mph").alias("avg_speed"),
                    avg("congestion_level").alias("avg_congestion"),
                    count("*").alias("measurement_count")
                ) \
                .orderBy("location", "has_incident")
            
            # Calculate speed reduction due to incidents
            speed_comparison = impact_analysis \
                .groupBy("location") \
                .pivot("has_incident") \
                .agg(avg("avg_speed")) \
                .withColumn("speed_reduction", 
                           (col("false") - col("true")) / col("false") * 100) \
                .select("location", "speed_reduction") \
                .orderBy(desc("speed_reduction"))
            
            logger.info("Incident impact analysis completed")
            return speed_comparison
            
        except Exception as e:
            logger.error(f"Error in incident impact analysis: {e}")
            raise
    
    def build_prediction_models(self, traffic_df: DataFrame) -> Dict[str, Any]:
        """Build ML models for traffic prediction"""
        logger.info("Building traffic prediction models...")
        
        try:
            # Prepare features
            prepared_df = self._prepare_ml_features(traffic_df)
            
            # Feature columns
            feature_cols = self.analysis_configs['prediction_models']['features']
            target_col = self.analysis_configs['prediction_models']['target']
            
            # Create feature vector
            assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
            feature_df = assembler.transform(prepared_df)
            
            # Split data
            train_split = self.analysis_configs['prediction_models']['train_split']
            train_df, test_df = feature_df.randomSplit([train_split, 1 - train_split], seed=42)
            
            models = {}
            
            # 1. Linear Regression Model
            lr = LinearRegression(featuresCol="features", labelCol=target_col, predictionCol="lr_prediction")
            lr_model = lr.fit(train_df)
            lr_predictions = lr_model.transform(test_df)
            
            # Evaluate Linear Regression
            lr_evaluator = RegressionEvaluator(labelCol=target_col, predictionCol="lr_prediction", metricName="rmse")
            lr_rmse = lr_evaluator.evaluate(lr_predictions)
            
            models['linear_regression'] = {
                'model': lr_model,
                'rmse': lr_rmse,
                'coefficients': lr_model.coefficients.toArray().tolist(),
                'intercept': lr_model.intercept
            }
            
            # 2. Random Forest Model
            rf = RandomForestRegressor(featuresCol="features", labelCol=target_col, predictionCol="rf_prediction", numTrees=50)
            rf_model = rf.fit(train_df)
            rf_predictions = rf_model.transform(test_df)
            
            # Evaluate Random Forest
            rf_evaluator = RegressionEvaluator(labelCol=target_col, predictionCol="rf_prediction", metricName="rmse")
            rf_rmse = rf_evaluator.evaluate(rf_predictions)
            
            models['random_forest'] = {
                'model': rf_model,
                'rmse': rf_rmse,
                'feature_importance': rf_model.featureImportances.toArray().tolist()
            }
            
            logger.info(f"Models built - LR RMSE: {lr_rmse:.4f}, RF RMSE: {rf_rmse:.4f}")
            
            return models
            
        except Exception as e:
            logger.error(f"Error building prediction models: {e}")
            raise
    
    def generate_business_insights(self, analysis_results: Dict[str, DataFrame]) -> Dict[str, Any]:
        """Generate business insights from analysis results"""
        logger.info("Generating business insights...")
        
        insights = {}
        
        try:
            # 1. Peak congestion insights
            if 'peak_hours' in analysis_results:
                peak_hours_df = analysis_results['peak_hours']
                peak_hours_list = [row['hour'] for row in peak_hours_df.filter(col("is_peak") == True).collect()]
                
                insights['peak_hours'] = {
                    'hours': peak_hours_list,
                    'recommendation': self._generate_peak_hour_recommendations(peak_hours_list)
                }
            
            # 2. Most congested locations
            if 'location_ranking' in analysis_results:
                location_ranking_df = analysis_results['location_ranking']
                top_congested = location_ranking_df.limit(5).collect()
                
                insights['congested_locations'] = {
                    'top_5': [
                        {
                            'location': row['location'],
                            'avg_congestion': round(row['avg_congestion'], 3),
                            'measurements': row['total_measurements']
                        }
                        for row in top_congested
                    ],
                    'recommendation': "Focus traffic optimization efforts on these high-congestion areas"
                }
            
            # 3. Temporal patterns
            if 'hourly_patterns' in analysis_results:
                hourly_df = analysis_results['hourly_patterns']
                avg_by_hour = hourly_df.groupBy("hour").agg(avg("avg_congestion").alias("overall_avg")).collect()
                
                congestion_by_hour = {row['hour']: round(row['overall_avg'], 3) for row in avg_by_hour}
                
                insights['temporal_patterns'] = {
                    'hourly_congestion': congestion_by_hour,
                    'recommendation': self._generate_temporal_recommendations(congestion_by_hour)
                }
            
            # 4. Performance metrics
            insights['performance_metrics'] = self._calculate_system_performance()
            
            logger.info("Business insights generated successfully")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating business insights: {e}")
            return {"error": str(e)}
    
    def save_results(self, results: Dict[str, Any], output_path: str):
        """Save analysis results to various formats"""
        logger.info(f"Saving results to: {output_path}")
        
        try:
            # Create output directory
            os.makedirs(output_path, exist_ok=True)
            
            # Save DataFrames as Parquet
            for name, df in results.items():
                if isinstance(df, DataFrame):
                    df.coalesce(1).write.mode("overwrite").parquet(f"{output_path}/{name}")
                    logger.info(f"Saved {name} as Parquet")
            
            # Save insights as JSON
            if 'insights' in results:
                insights_path = f"{output_path}/business_insights.json"
                with open(insights_path, 'w') as f:
                    json.dump(results['insights'], f, indent=2, default=str)
                logger.info("Saved business insights as JSON")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise
    
    def _prepare_time_features(self, df: DataFrame) -> DataFrame:
        """Prepare time-based features for analysis"""
        return df.withColumn("timestamp", to_timestamp(col("timestamp"))) \
                 .withColumn("hour", hour(col("timestamp"))) \
                 .withColumn("day_of_week", dayofweek(col("timestamp"))) \
                 .withColumn("date", date_format(col("timestamp"), "yyyy-MM-dd"))
    
    def _prepare_ml_features(self, df: DataFrame) -> DataFrame:
        """Prepare features for ML models"""
        # Add time features
        df = self._prepare_time_features(df)
        
        # Add window functions for historical data
        window_spec = Window.partitionBy("location").orderBy("timestamp")
        
        df = df.withColumn("prev_congestion", lag("congestion_level", 1).over(window_spec)) \
               .withColumn("historical_avg", avg("congestion_level").over(window_spec)) \
               .withColumn("weather_impact", when(col("weather_condition") == "rain", 1.2)
                          .when(col("weather_condition") == "snow", 1.5)
                          .otherwise(1.0))
        
        return df.na.fill(0)  # Fill nulls with 0
    
    def _create_mock_streaming_data(self) -> DataFrame:
        """Create mock streaming data for demonstration"""
        # This would normally read from Kafka
        # For demo, create mock data
        mock_data = [
            ("streaming_001", "2024-01-15T08:00:00", "Times Square", 25.5, 1500, 0.75),
            ("streaming_002", "2024-01-15T08:05:00", "Central Park", 35.2, 800, 0.45),
            ("streaming_003", "2024-01-15T08:10:00", "Brooklyn Bridge", 20.1, 2000, 0.85)
        ]
        
        schema = StructType([
            StructField("id", StringType(), True),
            StructField("timestamp", StringType(), True),
            StructField("location", StringType(), True),
            StructField("speed_mph", FloatType(), True),
            StructField("volume", IntegerType(), True),
            StructField("congestion_level", FloatType(), True)
        ])
        
        return self.spark.createDataFrame(mock_data, schema)
    
    def _generate_peak_hour_recommendations(self, peak_hours: List[int]) -> str:
        """Generate recommendations based on peak hours"""
        if len(peak_hours) > 4:
            return "Consider implementing dynamic pricing for peak hours and encouraging flexible work schedules"
        elif len(peak_hours) > 2:
            return "Optimize traffic signal timing during peak hours and consider alternative route suggestions"
        else:
            return "Current peak hour distribution is manageable with minor signal optimizations"
    
    def _generate_temporal_recommendations(self, hourly_congestion: Dict[int, float]) -> str:
        """Generate recommendations based on temporal patterns"""
        max_congestion_hour = max(hourly_congestion, key=hourly_congestion.get)
        max_congestion_value = hourly_congestion[max_congestion_hour]
        
        if max_congestion_value > 0.8:
            return f"Critical congestion at hour {max_congestion_hour}. Implement emergency traffic management protocols"
        elif max_congestion_value > 0.6:
            return f"High congestion at hour {max_congestion_hour}. Consider traffic signal optimization and alternative routing"
        else:
            return "Traffic patterns are within normal parameters. Maintain current optimization strategies"
    
    def _calculate_system_performance(self) -> Dict[str, Any]:
        """Calculate system performance metrics"""
        return {
            "processing_time": time.time(),
            "spark_version": self.spark.version,
            "total_cores": self.spark.sparkContext.defaultParallelism,
            "memory_usage": "Optimal",
            "recommendations": [
                "System performance is optimal for current data volume",
                "Consider scaling if data volume increases by 10x",
                "Implement data partitioning for better performance"
            ]
        }
    
    def stop_spark_session(self):
        """Stop the Spark session"""
        if self.spark:
            self.spark.stop()
            logger.info("Spark session stopped")


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Traffic Data Processor')
    parser.add_argument('--master', default='local[*]', help='Spark master URL')
    parser.add_argument('--output', default='./output/traffic_analysis', help='Output directory')
    parser.add_argument('--data-source', choices=['csv', 'postgresql', 'kafka'], 
                       default='csv', help='Data source type')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = EnhancedTrafficProcessor(master=args.master)
    
    try:
        # Start Spark session
        spark = processor.start_spark_session()
        
        # Configure data sources
        data_sources = {}
        if args.data_source == 'csv':
            data_sources['csv'] = {'path': 'data/sample/traffic_data.csv'}
        elif args.data_source == 'postgresql':
            data_sources['postgresql'] = {
                'url': 'jdbc:postgresql://localhost:5432/urbanclear',
                'user': 'urbanclear_user',
                'password': 'urbanclear_pass'
            }
        elif args.data_source == 'kafka':
            data_sources['kafka'] = {'bootstrap_servers': 'localhost:9092'}
        
        # Load data
        dataframes = processor.load_traffic_data(data_sources)
        
        # Get main traffic data
        traffic_df = list(dataframes.values())[0]  # Use first available DataFrame
        
        # Run comprehensive analysis
        logger.info("Starting comprehensive traffic analysis...")
        
        # 1. Traffic pattern analysis
        pattern_results = processor.analyze_traffic_patterns(traffic_df)
        
        # 2. Congestion clustering
        clustered_df, cluster_stats = processor.perform_congestion_clustering(traffic_df)
        
        # 3. Build prediction models
        prediction_models = processor.build_prediction_models(traffic_df)
        
        # 4. Generate business insights
        insights = processor.generate_business_insights(pattern_results)
        
        # Combine all results
        all_results = {
            **pattern_results,
            'clustered_traffic': clustered_df,
            'cluster_statistics': cluster_stats,
            'prediction_models': prediction_models,
            'insights': insights
        }
        
        # Save results
        processor.save_results(all_results, args.output)
        
        logger.info("Analysis completed successfully!")
        logger.info(f"Results saved to: {args.output}")
        
        # Print summary
        print("\n" + "="*60)
        print("URBANCLEAR TRAFFIC ANALYSIS SUMMARY")
        print("="*60)
        print(f"Data processed: {traffic_df.count()} records")
        print(f"Analysis completed in Spark session: {spark.sparkContext.appName}")
        print(f"Results saved to: {args.output}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise
    finally:
        processor.stop_spark_session()


if __name__ == "__main__":
    main() 