"""
Enhanced ML Pipeline for Traffic Prediction with MLOps Best Practices
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import lightgbm as lgb
from loguru import logger
import mlflow
import mlflow.sklearn
from dataclasses import dataclass
import optuna
from optuna.samplers import TPESampler
import pickle


@dataclass
class ModelConfig:
    """Configuration for ML models"""

    model_type: str
    hyperparameters: Dict[str, Any]
    feature_columns: List[str]
    target_column: str
    validation_split: float = 0.2
    cross_validation_folds: int = 5


@dataclass
class ModelMetrics:
    """Model performance metrics"""

    mse: float
    mae: float
    rmse: float
    r2: float
    mape: float
    cv_score: float
    training_time: float
    prediction_time: float


class EnhancedMLPipeline:
    """Enhanced ML pipeline with advanced models and MLOps practices"""

    def __init__(self, experiment_name: str = "urbanclear_traffic_prediction"):
        self.experiment_name = experiment_name
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        self.model_configs = {}
        self.metrics_history = []

        # Initialize MLflow
        mlflow.set_experiment(experiment_name)

        # Model registry
        self.available_models = {
            "random_forest": RandomForestRegressor,
            "gradient_boosting": GradientBoostingRegressor,
            "neural_network": MLPRegressor,
            "xgboost": xgb.XGBRegressor,
            "lightgbm": lgb.LGBMRegressor,
        }

        logger.info(
            f"Enhanced ML Pipeline initialized for experiment: {experiment_name}"
        )

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Advanced feature engineering"""
        logger.info("Preparing features for ML pipeline")

        # Time-based features
        df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
        df["day_of_week"] = pd.to_datetime(df["timestamp"]).dt.dayofweek
        df["month"] = pd.to_datetime(df["timestamp"]).dt.month
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        df["is_rush_hour"] = ((df["hour"].isin([7, 8, 9, 17, 18, 19]))).astype(int)

        # Weather impact features
        if "weather_temp" in df.columns:
            df["temp_category"] = pd.cut(
                df["weather_temp"],
                bins=[-float("inf"), 0, 15, 25, float("inf")],
                labels=["cold", "cool", "mild", "warm"],
            )

        # Traffic pattern features
        if "speed" in df.columns and "volume" in df.columns:
            df["traffic_density"] = df["volume"] / (
                df["speed"] + 1
            )  # Avoid division by zero
            df["flow_efficiency"] = df["speed"] / df["volume"]
            df["congestion_index"] = 1 - (df["speed"] / df["speed"].max())

        # Lag features for time series
        if "speed" in df.columns:
            df["speed_lag_1h"] = df["speed"].shift(1)
            df["speed_lag_24h"] = df["speed"].shift(24)
            df["speed_rolling_mean_3h"] = df["speed"].rolling(window=3).mean()
            df["speed_rolling_std_3h"] = df["speed"].rolling(window=3).std()

        # Location-based features
        if "location_lat" in df.columns and "location_lng" in df.columns:
            # Distance from city center (using Manhattan as example)
            city_center_lat, city_center_lng = 40.7831, -73.9712
            df["distance_from_center"] = np.sqrt(
                (df["location_lat"] - city_center_lat) ** 2
                + (df["location_lng"] - city_center_lng) ** 2
            )

        # Interaction features
        if "hour" in df.columns and "day_of_week" in df.columns:
            df["hour_day_interaction"] = df["hour"] * df["day_of_week"]

        # Remove rows with NaN values created by lag features
        df = df.dropna()

        logger.info(f"Feature engineering complete. Dataset shape: {df.shape}")
        return df

    def optimize_hyperparameters(
        self, model_type: str, X: pd.DataFrame, y: pd.Series, n_trials: int = 100
    ) -> Dict[str, Any]:
        """Hyperparameter optimization using Optuna"""
        logger.info(f"Optimizing hyperparameters for {model_type}")

        def objective(trial):
            if model_type == "random_forest":
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                    "max_depth": trial.suggest_int("max_depth", 3, 20),
                    "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
                    "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
                    "random_state": 42,
                }
            elif model_type == "gradient_boosting":
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
                    "max_depth": trial.suggest_int("max_depth", 3, 15),
                    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                    "random_state": 42,
                }
            elif model_type == "xgboost":
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
                    "max_depth": trial.suggest_int("max_depth", 3, 15),
                    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                    "colsample_bytree": trial.suggest_float(
                        "colsample_bytree", 0.6, 1.0
                    ),
                    "random_state": 42,
                }
            elif model_type == "lightgbm":
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
                    "max_depth": trial.suggest_int("max_depth", 3, 15),
                    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                    "colsample_bytree": trial.suggest_float(
                        "colsample_bytree", 0.6, 1.0
                    ),
                    "random_state": 42,
                    "verbosity": -1,
                }
            else:
                params = {}

            # Train model with suggested parameters
            model = self.available_models[model_type](**params)

            # Cross-validation
            scores = cross_val_score(
                model, X, y, cv=5, scoring="neg_mean_squared_error"
            )
            return -scores.mean()

        # Run optimization
        study = optuna.create_study(direction="minimize", sampler=TPESampler(seed=42))
        study.optimize(objective, n_trials=n_trials)

        logger.info(f"Best parameters for {model_type}: {study.best_params}")
        return study.best_params

    def train_model(
        self,
        config: ModelConfig,
        X: pd.DataFrame,
        y: pd.Series,
        optimize_hyperparameters: bool = True,
    ) -> ModelMetrics:
        """Train a model with the given configuration"""
        logger.info(f"Training {config.model_type} model")

        start_time = datetime.now()

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=config.validation_split, random_state=42
        )

        # Optimize hyperparameters if requested
        if optimize_hyperparameters:
            best_params = self.optimize_hyperparameters(
                config.model_type, X_train, y_train
            )
            config.hyperparameters.update(best_params)

        # Initialize model
        model = self.available_models[config.model_type](**config.hyperparameters)

        # Scale features if needed
        if config.model_type in ["neural_network"]:
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            self.scalers[config.model_type] = scaler
        else:
            X_train_scaled = X_train
            X_test_scaled = X_test

        # Train model
        model.fit(X_train_scaled, y_train)

        # Calculate training time
        training_time = (datetime.now() - start_time).total_seconds()

        # Make predictions
        pred_start = datetime.now()
        y_pred = model.predict(X_test_scaled)
        prediction_time = (datetime.now() - pred_start).total_seconds()

        # Calculate metrics
        metrics = ModelMetrics(
            mse=mean_squared_error(y_test, y_pred),
            mae=mean_absolute_error(y_test, y_pred),
            rmse=np.sqrt(mean_squared_error(y_test, y_pred)),
            r2=r2_score(y_test, y_pred),
            mape=np.mean(np.abs((y_test - y_pred) / y_test)) * 100,
            cv_score=cross_val_score(
                model, X_train_scaled, y_train, cv=config.cross_validation_folds
            ).mean(),
            training_time=training_time,
            prediction_time=prediction_time,
        )

        # Store model and config
        self.models[config.model_type] = model
        self.model_configs[config.model_type] = config

        # Store feature importance if available
        if hasattr(model, "feature_importances_"):
            self.feature_importance[config.model_type] = dict(
                zip(X.columns, model.feature_importances_)
            )

        # Log to MLflow
        with mlflow.start_run(run_name=f"{config.model_type}_training"):
            mlflow.log_params(config.hyperparameters)
            mlflow.log_metrics(
                {
                    "mse": metrics.mse,
                    "mae": metrics.mae,
                    "rmse": metrics.rmse,
                    "r2": metrics.r2,
                    "mape": metrics.mape,
                    "cv_score": metrics.cv_score,
                    "training_time": metrics.training_time,
                }
            )
            mlflow.sklearn.log_model(model, f"{config.model_type}_model")

        logger.info(
            f"Model {config.model_type} trained successfully. "
            f"R² score: {metrics.r2:.4f}"
        )
        return metrics

    def ensemble_prediction(
        self, X: pd.DataFrame, models: List[str], weights: Optional[List[float]] = None
    ) -> np.ndarray:
        """Make ensemble predictions using multiple models"""
        if weights is None:
            weights = [1.0] * len(models)

        predictions = []
        for model_type in models:
            if model_type not in self.models:
                logger.warning(f"Model {model_type} not found in trained models")
                continue

            model = self.models[model_type]

            # Apply scaling if needed
            if model_type in self.scalers:
                X_scaled = self.scalers[model_type].transform(X)
            else:
                X_scaled = X

            pred = model.predict(X_scaled)
            predictions.append(pred)

        # Weighted ensemble
        weighted_predictions = np.average(
            predictions, axis=0, weights=weights[: len(predictions)]
        )
        logger.info(f"Ensemble prediction completed using {len(predictions)} models")

        return weighted_predictions

    def save_pipeline(self, filepath: str):
        """Save the entire pipeline to disk"""
        pipeline_data = {
            "models": self.models,
            "scalers": self.scalers,
            "encoders": self.encoders,
            "feature_importance": self.feature_importance,
            "model_configs": self.model_configs,
            "metrics_history": self.metrics_history,
        }

        with open(filepath, "wb") as f:
            pickle.dump(pipeline_data, f)

        logger.info(f"Pipeline saved to {filepath}")

    def load_pipeline(self, filepath: str):
        """Load pipeline from disk"""
        with open(filepath, "rb") as f:
            pipeline_data = pickle.load(f)

        self.models = pipeline_data["models"]
        self.scalers = pipeline_data["scalers"]
        self.encoders = pipeline_data["encoders"]
        self.feature_importance = pipeline_data["feature_importance"]
        self.model_configs = pipeline_data["model_configs"]
        self.metrics_history = pipeline_data["metrics_history"]

        logger.info(f"Pipeline loaded from {filepath}")

    def get_feature_importance_report(self) -> Dict[str, Any]:
        """Generate feature importance report across all models"""
        report = {}

        for model_type, importances in self.feature_importance.items():
            sorted_features = sorted(
                importances.items(), key=lambda x: x[1], reverse=True
            )
            report[model_type] = {
                "top_10_features": sorted_features[:10],
                "total_features": len(sorted_features),
                "importance_sum": sum(importances.values()),
            }

        return report

    def model_comparison_report(self) -> pd.DataFrame:
        """Generate model comparison report"""
        comparison_data = []

        for model_type, model in self.models.items():
            config = self.model_configs.get(model_type, {})

            comparison_data.append(
                {
                    "model_type": model_type,
                    "parameters": (
                        len(config.hyperparameters)
                        if hasattr(config, "hyperparameters")
                        else 0
                    ),
                    "features": (
                        len(config.feature_columns)
                        if hasattr(config, "feature_columns")
                        else 0
                    ),
                    "model_size": len(pickle.dumps(model)),
                }
            )

        return pd.DataFrame(comparison_data)


# Example usage
def main():
    """Example usage of Enhanced ML Pipeline"""
    # Initialize pipeline
    pipeline = EnhancedMLPipeline("traffic_prediction_enhanced")

    # Sample data (in practice, load from your data source)
    np.random.seed(42)
    sample_data = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=1000, freq="H"),
            "speed": np.random.normal(30, 10, 1000),
            "volume": np.random.normal(1000, 300, 1000),
            "weather_temp": np.random.normal(15, 10, 1000),
            "location_lat": np.random.normal(40.7831, 0.01, 1000),
            "location_lng": np.random.normal(-73.9712, 0.01, 1000),
        }
    )

    # Prepare features
    df = pipeline.prepare_features(sample_data)

    # Define features and target
    feature_columns = [col for col in df.columns if col not in ["timestamp", "speed"]]
    X = df[feature_columns]
    y = df["speed"]

    # Train multiple models
    models_to_train = ["random_forest", "gradient_boosting", "xgboost"]

    for model_type in models_to_train:
        config = ModelConfig(
            model_type=model_type,
            hyperparameters={},
            feature_columns=feature_columns,
            target_column="speed",
        )

        metrics = pipeline.train_model(config, X, y, optimize_hyperparameters=True)
        print(f"{model_type} - R² Score: {metrics.r2:.4f}")

    # Make ensemble prediction
    ensemble_pred = pipeline.ensemble_prediction(X.iloc[:100], models_to_train)
    print(f"Ensemble prediction shape: {ensemble_pred.shape}")

    # Generate reports
    feature_report = pipeline.get_feature_importance_report()
    print("Feature Importance Report:", feature_report)

    comparison_report = pipeline.model_comparison_report()
    print("Model Comparison Report:")
    print(comparison_report)


if __name__ == "__main__":
    main()
