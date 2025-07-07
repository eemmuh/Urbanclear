"""
Machine Learning Model Training Pipeline for Traffic System
"""

import logging
import joblib
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    RandomForestClassifier,
    GradientBoostingClassifier,
)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import (
    mean_squared_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.preprocessing import StandardScaler

from src.data.mock_data_generator import MockDataGenerator

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Advanced ML model trainer for traffic optimization"""

    def __init__(self, models_dir: str = "models/trained"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.mock_generator = MockDataGenerator()

        # Model configurations
        self.model_configs = {
            "traffic_flow_predictor": {
                "type": "regression",
                "algorithms": {
                    "random_forest": RandomForestRegressor(),
                    "gradient_boosting": GradientBoostingRegressor(),
                    "neural_network": MLPRegressor(hidden_layer_sizes=(100, 50)),
                    "linear_regression": LinearRegression(),
                },
                "param_grids": {
                    "random_forest": {
                        "n_estimators": [50, 100, 200],
                        "max_depth": [5, 10, None],
                        "min_samples_split": [2, 5, 10],
                    },
                    "gradient_boosting": {
                        "n_estimators": [50, 100, 200],
                        "learning_rate": [0.01, 0.1, 0.2],
                        "max_depth": [3, 5, 7],
                    },
                },
            },
            "route_optimizer": {
                "type": "regression",
                "algorithms": {
                    "random_forest": RandomForestRegressor(),
                    "gradient_boosting": GradientBoostingRegressor(),
                    "neural_network": MLPRegressor(hidden_layer_sizes=(50, 25)),
                },
            },
            "incident_detector": {
                "type": "classification",
                "algorithms": {
                    "random_forest": RandomForestClassifier(),
                    "gradient_boosting": GradientBoostingClassifier(),
                    "neural_network": MLPClassifier(hidden_layer_sizes=(100, 50)),
                    "logistic_regression": LogisticRegression(),
                },
                "param_grids": {
                    "random_forest": {
                        "n_estimators": [50, 100, 200],
                        "max_depth": [5, 10, None],
                        "min_samples_split": [2, 5, 10],
                    }
                },
            },
            "signal_optimizer": {
                "type": "regression",
                "algorithms": {
                    "random_forest": RandomForestRegressor(),
                    "linear_regression": LinearRegression(),
                },
            },
        }

        self.trained_models = {}
        self.model_metrics = {}
        self.scalers = {}

    def generate_training_data(
        self, model_type: str, samples: int = 10000
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Generate synthetic training data for specified model type"""
        logger.info(f"Generating {samples} training samples for {model_type}")

        if model_type == "traffic_flow_predictor":
            return self._generate_traffic_prediction_data(samples)
        elif model_type == "route_optimizer":
            return self._generate_route_optimization_data(samples)
        elif model_type == "incident_detector":
            return self._generate_incident_detection_data(samples)
        elif model_type == "signal_optimizer":
            return self._generate_signal_optimization_data(samples)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def _generate_traffic_prediction_data(
        self, samples: int
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Generate traffic flow prediction training data"""
        data = []

        for _ in range(samples):
            # Time features
            timestamp = datetime.now() - timedelta(
                days=np.random.randint(0, 365),
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60),
            )

            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            month = timestamp.month

            # Weather features
            weather_clear = np.random.choice([0, 1], p=[0.3, 0.7])
            temperature = np.random.normal(20, 10)

            # Historical traffic features
            historical_avg = np.random.normal(500, 200)
            recent_trend = np.random.normal(0, 50)

            # Location features
            location_id = np.random.randint(0, 8)
            is_highway = np.random.choice([0, 1], p=[0.6, 0.4])
            lanes = np.random.choice([2, 3, 4, 6])

            # Special events
            is_event_day = np.random.choice([0, 1], p=[0.9, 0.1])

            # Target: traffic flow rate
            base_flow = historical_avg

            # Time-based adjustments
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                base_flow *= np.random.uniform(1.5, 2.5)
            elif 22 <= hour or hour <= 6:  # Night hours
                base_flow *= np.random.uniform(0.2, 0.6)

            # Weather adjustments
            if not weather_clear:
                base_flow *= np.random.uniform(0.7, 1.3)

            # Weekend adjustments
            if day_of_week >= 5:  # Weekend
                base_flow *= np.random.uniform(0.6, 1.2)

            # Event adjustments
            if is_event_day:
                base_flow *= np.random.uniform(1.2, 1.8)

            target_flow = max(0, base_flow + recent_trend + np.random.normal(0, 50))

            data.append(
                {
                    "hour": hour,
                    "day_of_week": day_of_week,
                    "month": month,
                    "weather_clear": weather_clear,
                    "temperature": temperature,
                    "historical_avg": historical_avg,
                    "recent_trend": recent_trend,
                    "location_id": location_id,
                    "is_highway": is_highway,
                    "lanes": lanes,
                    "is_event_day": is_event_day,
                    "target_flow": target_flow,
                }
            )

        df = pd.DataFrame(data)
        X = df.drop("target_flow", axis=1)
        y = df["target_flow"]

        return X, y

    def _generate_route_optimization_data(
        self, samples: int
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Generate route optimization training data"""
        data = []

        for _ in range(samples):
            # Route characteristics
            distance = np.random.uniform(1, 50)  # km
            num_intersections = np.random.randint(1, 20)
            highway_ratio = np.random.uniform(0, 1)

            # Traffic conditions
            avg_congestion = np.random.uniform(0, 1)
            current_incidents = np.random.randint(0, 5)

            # Time features
            hour = np.random.randint(0, 24)
            is_rush_hour = 1 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0

            # Weather
            weather_impact = np.random.uniform(0.8, 1.5)

            # Calculate expected travel time (target)
            base_time = distance * 2  # 2 minutes per km base

            # Adjustments
            base_time += num_intersections * 0.5  # 30 seconds per intersection
            base_time *= 1 + avg_congestion  # Congestion impact
            base_time += current_incidents * 5  # 5 minutes per incident
            base_time *= weather_impact

            if is_rush_hour:
                base_time *= np.random.uniform(1.3, 1.8)

            target_time = max(distance * 0.5, base_time + np.random.normal(0, 5))

            data.append(
                {
                    "distance": distance,
                    "num_intersections": num_intersections,
                    "highway_ratio": highway_ratio,
                    "avg_congestion": avg_congestion,
                    "current_incidents": current_incidents,
                    "hour": hour,
                    "is_rush_hour": is_rush_hour,
                    "weather_impact": weather_impact,
                    "target_time": target_time,
                }
            )

        df = pd.DataFrame(data)
        X = df.drop("target_time", axis=1)
        y = df["target_time"]

        return X, y

    def _generate_incident_detection_data(
        self, samples: int
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Generate incident detection training data"""
        data = []

        for _ in range(samples):
            # Traffic flow features
            flow_rate = np.random.normal(500, 200)
            flow_variance = np.random.uniform(0, 100)
            speed_avg = np.random.uniform(20, 80)
            speed_variance = np.random.uniform(0, 20)

            # Congestion features
            congestion_level = np.random.uniform(0, 1)
            queue_length = np.random.uniform(0, 2000)  # meters

            # Time features
            hour = np.random.randint(0, 24)
            day_of_week = np.random.randint(0, 7)

            # Weather features
            visibility = np.random.uniform(100, 10000)  # meters
            road_condition = np.random.choice([0, 1], p=[0.8, 0.2])  # 0=good, 1=poor

            # Historical features
            historical_incidents = np.random.poisson(
                2
            )  # Average 2 incidents per time period

            # Determine if there's an incident (target)
            incident_probability = 0.05  # Base 5% chance

            # Increase probability based on conditions
            if congestion_level > 0.7:
                incident_probability *= 2
            if speed_variance > 15:
                incident_probability *= 1.5
            if visibility < 1000:
                incident_probability *= 1.8
            if road_condition == 1:
                incident_probability *= 2
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                incident_probability *= 1.3

            has_incident = np.random.choice(
                [0, 1], p=[1 - incident_probability, incident_probability]
            )

            data.append(
                {
                    "flow_rate": flow_rate,
                    "flow_variance": flow_variance,
                    "speed_avg": speed_avg,
                    "speed_variance": speed_variance,
                    "congestion_level": congestion_level,
                    "queue_length": queue_length,
                    "hour": hour,
                    "day_of_week": day_of_week,
                    "visibility": visibility,
                    "road_condition": road_condition,
                    "historical_incidents": historical_incidents,
                    "has_incident": has_incident,
                }
            )

        df = pd.DataFrame(data)
        X = df.drop("has_incident", axis=1)
        y = df["has_incident"]

        return X, y

    def _generate_signal_optimization_data(
        self, samples: int
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Generate signal timing optimization training data"""
        data = []

        for _ in range(samples):
            # Intersection characteristics
            num_approaches = np.random.choice([3, 4])
            total_lanes = np.random.randint(6, 16)

            # Traffic volumes per approach
            north_south_volume = np.random.normal(400, 150)
            east_west_volume = np.random.normal(350, 120)

            # Current signal timing
            current_cycle_length = np.random.uniform(60, 180)
            green_ratio_ns = np.random.uniform(0.3, 0.7)

            # Time features
            hour = np.random.randint(0, 24)
            is_peak = 1 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0

            # Calculate optimal cycle length (target)
            total_volume = north_south_volume + east_west_volume

            # Webster's formula approximation
            optimal_cycle = (1.5 * 5 + 5) / (1 - min(0.9, total_volume / 3600))
            optimal_cycle = max(60, min(180, optimal_cycle))

            # Add noise
            target_cycle = optimal_cycle + np.random.normal(0, 10)
            target_cycle = max(60, min(180, target_cycle))

            data.append(
                {
                    "num_approaches": num_approaches,
                    "total_lanes": total_lanes,
                    "north_south_volume": north_south_volume,
                    "east_west_volume": east_west_volume,
                    "current_cycle_length": current_cycle_length,
                    "green_ratio_ns": green_ratio_ns,
                    "hour": hour,
                    "is_peak": is_peak,
                    "target_cycle": target_cycle,
                }
            )

        df = pd.DataFrame(data)
        X = df.drop("target_cycle", axis=1)
        y = df["target_cycle"]

        return X, y

    def train_model(
        self,
        model_type: str,
        algorithm: str = "auto",
        samples: int = 10000,
        use_grid_search: bool = True,
    ) -> Dict[str, Any]:
        """Train a specific model with given algorithm"""
        logger.info(f"Training {model_type} with {algorithm} algorithm")

        # Generate training data
        X, y = self.generate_training_data(model_type, samples)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Store scaler
        self.scalers[model_type] = scaler

        # Get model configuration
        config = self.model_configs[model_type]

        # Select algorithm
        if algorithm == "auto":
            # Try all algorithms and select best
            best_model, best_score, best_algo = self._select_best_algorithm(
                config, X_train_scaled, y_train, X_test_scaled, y_test, use_grid_search
            )
        else:
            if algorithm not in config["algorithms"]:
                raise ValueError(
                    f"Algorithm {algorithm} not available for {model_type}"
                )

            model = config["algorithms"][algorithm]

            if use_grid_search and algorithm in config.get("param_grids", {}):
                # Use grid search for hyperparameter tuning
                grid_search = GridSearchCV(
                    model,
                    config["param_grids"][algorithm],
                    cv=5,
                    scoring=(
                        "neg_mean_squared_error"
                        if config["type"] == "regression"
                        else "accuracy"
                    ),
                )
                grid_search.fit(X_train_scaled, y_train)
                best_model = grid_search.best_estimator_
                logger.info(f"Best parameters: {grid_search.best_params_}")
            else:
                # Train with default parameters
                best_model = model
                best_model.fit(X_train_scaled, y_train)

            best_algo = algorithm

        # Evaluate model
        metrics = self._evaluate_model(
            best_model, X_test_scaled, y_test, config["type"]
        )

        # Store model and metrics
        self.trained_models[model_type] = {
            "model": best_model,
            "algorithm": best_algo,
            "scaler": scaler,
            "trained_at": datetime.now(),
            "samples_used": samples,
        }

        self.model_metrics[model_type] = metrics

        # Save model to disk
        self._save_model(model_type, best_model, scaler, metrics)

        logger.info(f"Training completed for {model_type}. Metrics: {metrics}")

        return {
            "model_type": model_type,
            "algorithm": best_algo,
            "metrics": metrics,
            "trained_at": datetime.now().isoformat(),
        }

    def _select_best_algorithm(
        self,
        config: Dict,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        use_grid_search: bool,
    ) -> Tuple[Any, float, str]:
        """Select the best algorithm based on cross-validation performance"""
        best_model = None
        best_score = float("-inf") if config["type"] == "regression" else 0
        best_algo = None

        for algo_name, model in config["algorithms"].items():
            try:
                if use_grid_search and algo_name in config.get("param_grids", {}):
                    # Use grid search
                    grid_search = GridSearchCV(
                        model,
                        config["param_grids"][algo_name],
                        cv=3,
                        scoring=(
                            "neg_mean_squared_error"
                            if config["type"] == "regression"
                            else "accuracy"
                        ),
                    )
                    grid_search.fit(X_train, y_train)
                    current_model = grid_search.best_estimator_
                else:
                    # Use default parameters
                    current_model = model
                    current_model.fit(X_train, y_train)

                # Evaluate
                if config["type"] == "regression":
                    score = -mean_squared_error(y_test, current_model.predict(X_test))
                else:
                    score = accuracy_score(y_test, current_model.predict(X_test))

                logger.info(f"Algorithm {algo_name} score: {score}")

                if (config["type"] == "regression" and score > best_score) or (
                    config["type"] == "classification" and score > best_score
                ):
                    best_model = current_model
                    best_score = score
                    best_algo = algo_name

            except Exception as e:
                logger.error(f"Error training {algo_name}: {e}")
                continue

        return best_model, best_score, best_algo

    def _evaluate_model(
        self, model: Any, X_test: np.ndarray, y_test: np.ndarray, model_type: str
    ) -> Dict[str, float]:
        """Evaluate model performance"""
        predictions = model.predict(X_test)

        if model_type == "regression":
            return {
                "mse": mean_squared_error(y_test, predictions),
                "rmse": np.sqrt(mean_squared_error(y_test, predictions)),
                "r2_score": r2_score(y_test, predictions),
                "mae": np.mean(np.abs(y_test - predictions)),
            }
        else:  # classification
            return {
                "accuracy": accuracy_score(y_test, predictions),
                "precision": precision_score(y_test, predictions, average="weighted"),
                "recall": recall_score(y_test, predictions, average="weighted"),
                "f1_score": f1_score(y_test, predictions, average="weighted"),
            }

    def _save_model(self, model_type: str, model: Any, scaler: Any, metrics: Dict):
        """Save trained model to disk"""
        model_path = self.models_dir / f"{model_type}.joblib"
        scaler_path = self.models_dir / f"{model_type}_scaler.joblib"
        metrics_path = self.models_dir / f"{model_type}_metrics.json"

        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)

        # Save metrics as JSON
        import json

        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Model saved to {model_path}")

    def load_model(self, model_type: str) -> bool:
        """Load a trained model from disk"""
        model_path = self.models_dir / f"{model_type}.joblib"
        scaler_path = self.models_dir / f"{model_type}_scaler.joblib"

        if not model_path.exists() or not scaler_path.exists():
            logger.warning(f"Model files not found for {model_type}")
            return False

        try:
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)

            self.trained_models[model_type] = {
                "model": model,
                "scaler": scaler,
                "loaded_at": datetime.now(),
            }

            logger.info(f"Model {model_type} loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error loading model {model_type}: {e}")
            return False

    def train_all_models(self, samples: int = 10000) -> Dict[str, Any]:
        """Train all available models"""
        results = {}

        for model_type in self.model_configs.keys():
            try:
                result = self.train_model(model_type, samples=samples)
                results[model_type] = result
            except Exception as e:
                logger.error(f"Error training {model_type}: {e}")
                results[model_type] = {"error": str(e)}

        return results

    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        status = {}

        for model_type in self.model_configs.keys():
            if model_type in self.trained_models:
                model_info = self.trained_models[model_type]
                metrics = self.model_metrics.get(model_type, {})

                status[model_type] = {
                    "trained": True,
                    "algorithm": model_info.get("algorithm", "unknown"),
                    "trained_at": model_info.get("trained_at", "unknown"),
                    "metrics": metrics,
                }
            else:
                status[model_type] = {
                    "trained": False,
                    "available_algorithms": list(
                        self.model_configs[model_type]["algorithms"].keys()
                    ),
                }

        return status


# Convenience function for batch training
def train_all_urbanclear_models(
    samples: int = 10000, models_dir: str = "models/trained"
) -> Dict[str, Any]:
    """Train all Urbanclear ML models"""
    trainer = ModelTrainer(models_dir)
    return trainer.train_all_models(samples)


if __name__ == "__main__":
    # Example usage
    print("🤖 Starting Urbanclear ML Training System")

    trainer = ModelTrainer()

    # Train all models
    results = trainer.train_all_models(samples=5000)

    print("\n📊 Training Results:")
    for model_type, result in results.items():
        if "error" in result:
            print(f"❌ {model_type}: {result['error']}")
        else:
            print(f"✅ {model_type}: {result['algorithm']} - {result['metrics']}")

    print("\n🎯 All models trained successfully!")
