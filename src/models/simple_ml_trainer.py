#!/usr/bin/env python3
"""
Simple ML Training System for Urbanclear
Basic implementation without complex dependencies
"""

import json
import pickle
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple
from pathlib import Path
import logging

# Basic imports that should work
import math
import random
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleLinearRegression:
    """Simple linear regression implementation"""
    
    def __init__(self):
        self.weights = None
        self.bias = None
        self.is_trained = False
    
    def fit(self, X: List[List[float]], y: List[float]):
        """Train the model using least squares"""
        if not X or not y:
            raise ValueError("Empty training data")
        
        n_samples = len(X)
        n_features = len(X[0])
        
        # Initialize weights and bias
        self.weights = [0.0] * n_features
        self.bias = 0.0
        
        # Simple gradient descent
        learning_rate = 0.001  # Smaller learning rate to prevent overflow
        epochs = 1000
        
        for epoch in range(epochs):
            # Calculate predictions
            predictions = [self.predict_single(x) for x in X]
            
            # Calculate loss
            loss = sum((pred - actual) ** 2 for pred, actual in zip(predictions, y)) / n_samples
            
            # Check for overflow
            if loss > 1e10:
                logger.warning(f"Loss too large at epoch {epoch}: {loss}")
                break
            
            # Calculate gradients
            weight_gradients = [0.0] * n_features
            bias_gradient = 0.0
            
            for i, (pred, actual) in enumerate(zip(predictions, y)):
                error = pred - actual
                bias_gradient += error
                for j in range(n_features):
                    weight_gradients[j] += error * X[i][j]
            
            # Update weights and bias with clipping
            bias_update = learning_rate * bias_gradient / n_samples
            self.bias -= max(-1.0, min(1.0, bias_update))  # Clip updates
            
            for j in range(n_features):
                weight_update = learning_rate * weight_gradients[j] / n_samples
                self.weights[j] -= max(-1.0, min(1.0, weight_update))  # Clip updates
            
            if epoch % 100 == 0:
                logger.info(f"Epoch {epoch}, Loss: {loss:.4f}")
        
        self.is_trained = True
        logger.info("Linear regression training completed")
    
    def predict_single(self, x: List[float]) -> float:
        """Make prediction for single sample"""
        if self.weights is None or self.bias is None:
            # During training, we can still make predictions with current weights
            if self.weights is None:
                return 0.0
            
        prediction = self.bias if self.bias is not None else 0.0
        for i, feature in enumerate(x):
            if i < len(self.weights):
                prediction += self.weights[i] * feature
        
        return prediction
    
    def predict(self, X: List[List[float]]) -> List[float]:
        """Make predictions for multiple samples"""
        return [self.predict_single(x) for x in X]


class SimpleDecisionTree:
    """Simple decision tree implementation"""
    
    def __init__(self, max_depth=10):
        self.max_depth = max_depth
        self.tree = None
        self.is_trained = False
    
    def fit(self, X: List[List[float]], y: List[float]):
        """Train the decision tree"""
        self.tree = self._build_tree(X, y, depth=0)
        self.is_trained = True
        logger.info("Decision tree training completed")
    
    def _build_tree(self, X: List[List[float]], y: List[float], depth: int) -> Dict:
        """Build decision tree recursively"""
        if depth >= self.max_depth or len(set(y)) == 1 or len(X) < 2:
            return {"type": "leaf", "value": sum(y) / len(y)}
        
        best_feature = 0
        best_threshold = 0
        best_score = float('inf')
        
        n_features = len(X[0])
        
        # Find best split
        for feature in range(n_features):
            values = [x[feature] for x in X]
            unique_values = sorted(set(values))
            
            for i in range(len(unique_values) - 1):
                threshold = (unique_values[i] + unique_values[i + 1]) / 2
                
                left_y = [y[j] for j in range(len(X)) if X[j][feature] <= threshold]
                right_y = [y[j] for j in range(len(X)) if X[j][feature] > threshold]
                
                if len(left_y) == 0 or len(right_y) == 0:
                    continue
                
                # Calculate weighted MSE
                left_mse = sum((yi - sum(left_y) / len(left_y)) ** 2 for yi in left_y) / len(left_y)
                right_mse = sum((yi - sum(right_y) / len(right_y)) ** 2 for yi in right_y) / len(right_y)
                
                weighted_mse = (len(left_y) * left_mse + len(right_y) * right_mse) / len(y)
                
                if weighted_mse < best_score:
                    best_score = weighted_mse
                    best_feature = feature
                    best_threshold = threshold
        
        # Split data
        left_X = [X[i] for i in range(len(X)) if X[i][best_feature] <= best_threshold]
        left_y = [y[i] for i in range(len(X)) if X[i][best_feature] <= best_threshold]
        right_X = [X[i] for i in range(len(X)) if X[i][best_feature] > best_threshold]
        right_y = [y[i] for i in range(len(X)) if X[i][best_feature] > best_threshold]
        
        return {
            "type": "split",
            "feature": best_feature,
            "threshold": best_threshold,
            "left": self._build_tree(left_X, left_y, depth + 1),
            "right": self._build_tree(right_X, right_y, depth + 1)
        }
    
    def predict_single(self, x: List[float]) -> float:
        """Make prediction for single sample"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        return self._predict_tree(x, self.tree)
    
    def _predict_tree(self, x: List[float], node: Dict) -> float:
        """Predict using tree recursively"""
        if node["type"] == "leaf":
            return node["value"]
        
        if x[node["feature"]] <= node["threshold"]:
            return self._predict_tree(x, node["left"])
        else:
            return self._predict_tree(x, node["right"])
    
    def predict(self, X: List[List[float]]) -> List[float]:
        """Make predictions for multiple samples"""
        return [self.predict_single(x) for x in X]


class SimpleMLTrainer:
    """Simple ML trainer without complex dependencies"""
    
    def __init__(self, models_dir: str = "models/simple_trained"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.trained_models = {}
        self.model_metrics = {}
        
        logger.info(f"Simple ML Trainer initialized, models dir: {self.models_dir}")
    
    def generate_synthetic_data(self, samples: int = 1000) -> Tuple[List[List[float]], List[float]]:
        """Generate synthetic training data"""
        X = []
        y = []
        
        for _ in range(samples):
            # Generate features: [hour, day_of_week, weather_score, location_factor]
            hour = random.randint(0, 23)
            day_of_week = random.randint(0, 6)
            weather_score = random.uniform(0, 1)
            location_factor = random.uniform(0, 1)
            
            # Generate realistic traffic flow based on features
            base_flow = 500
            
            # Rush hour effect
            if 7 <= hour <= 9 or 17 <= hour <= 19:
                base_flow *= 1.5
            elif 22 <= hour or hour <= 5:
                base_flow *= 0.3
            
            # Weekend effect
            if day_of_week >= 5:
                base_flow *= 0.7
            
            # Weather effect
            base_flow *= (1 - weather_score * 0.3)
            
            # Location effect
            base_flow *= (0.5 + location_factor * 0.5)
            
            # Add noise
            flow = base_flow + random.gauss(0, 50)
            flow = max(0, flow)  # Ensure non-negative
            
            X.append([hour, day_of_week, weather_score, location_factor])
            y.append(flow)
        
        logger.info(f"Generated {samples} synthetic training samples")
        return X, y
    
    def train_traffic_predictor(self, samples: int = 1000) -> Dict[str, Any]:
        """Train traffic prediction model"""
        logger.info("Training traffic prediction model")
        
        X, y = self.generate_synthetic_data(samples)
        
        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train models
        models = {
            "linear_regression": SimpleLinearRegression(),
            "decision_tree": SimpleDecisionTree(max_depth=10)
        }
        
        results = {}
        
        for name, model in models.items():
            logger.info(f"Training {name}")
            
            # Train model
            start_time = datetime.now()
            model.fit(X_train, y_train)
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Evaluate model
            predictions = model.predict(X_test)
            mse = sum((pred - actual) ** 2 for pred, actual in zip(predictions, y_test)) / len(y_test)
            mae = sum(abs(pred - actual) for pred, actual in zip(predictions, y_test)) / len(y_test)
            
            results[name] = {
                "model": model,
                "mse": mse,
                "mae": mae,
                "training_time": training_time
            }
            
            logger.info(f"{name} - MSE: {mse:.2f}, MAE: {mae:.2f}")
        
        # Select best model
        best_model_name = min(results.keys(), key=lambda x: results[x]["mse"])
        best_model = results[best_model_name]
        
        # Save model
        model_path = self.models_dir / "traffic_predictor.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(best_model["model"], f)
        
        # Save metadata
        metadata = {
            "model_type": "traffic_predictor",
            "algorithm": best_model_name,
            "mse": best_model["mse"],
            "mae": best_model["mae"],
            "training_time": best_model["training_time"],
            "trained_at": datetime.now().isoformat(),
            "samples_used": samples
        }
        
        with open(self.models_dir / "traffic_predictor_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.trained_models["traffic_predictor"] = best_model["model"]
        self.model_metrics["traffic_predictor"] = metadata
        
        logger.info(f"Traffic predictor trained successfully with {best_model_name}")
        return metadata
    
    def train_incident_detector(self, samples: int = 1000) -> Dict[str, Any]:
        """Train incident detection model"""
        logger.info("Training incident detection model")
        
        X = []
        y = []
        
        for _ in range(samples):
            # Features: [flow_rate, speed, congestion_level, weather_condition]
            flow_rate = random.uniform(0, 1000)
            speed = random.uniform(10, 80)
            congestion_level = random.uniform(0, 1)
            weather_condition = random.uniform(0, 1)  # 0=good, 1=bad
            
            # Generate incident probability
            incident_prob = 0.1  # Base 10% chance
            
            # Higher congestion increases incident probability
            incident_prob += congestion_level * 0.2
            
            # Bad weather increases incident probability
            incident_prob += weather_condition * 0.15
            
            # Very high flow increases incident probability
            if flow_rate > 800:
                incident_prob += 0.1
            
            # Low speed increases incident probability
            if speed < 20:
                incident_prob += 0.1
            
            has_incident = 1 if random.random() < incident_prob else 0
            
            X.append([flow_rate, speed, congestion_level, weather_condition])
            y.append(has_incident)
        
        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train decision tree (good for classification)
        model = SimpleDecisionTree(max_depth=8)
        model.fit(X_train, y_train)
        
        # Evaluate
        predictions = model.predict(X_test)
        # Convert to binary predictions
        binary_predictions = [1 if p > 0.5 else 0 for p in predictions]
        
        accuracy = sum(pred == actual for pred, actual in zip(binary_predictions, y_test)) / len(y_test)
        
        # Save model
        model_path = self.models_dir / "incident_detector.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        metadata = {
            "model_type": "incident_detector",
            "algorithm": "decision_tree",
            "accuracy": accuracy,
            "trained_at": datetime.now().isoformat(),
            "samples_used": samples
        }
        
        with open(self.models_dir / "incident_detector_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.trained_models["incident_detector"] = model
        self.model_metrics["incident_detector"] = metadata
        
        logger.info(f"Incident detector trained successfully with accuracy: {accuracy:.3f}")
        return metadata
    
    def train_route_optimizer(self, samples: int = 1000) -> Dict[str, Any]:
        """Train route optimization model"""
        logger.info("Training route optimization model")
        
        X = []
        y = []
        
        for _ in range(samples):
            # Features: [distance, current_traffic, historical_average, weather, time_of_day]
            distance = random.uniform(1, 50)  # km
            current_traffic = random.uniform(0, 1)
            historical_average = random.uniform(0, 1)
            weather = random.uniform(0, 1)
            time_of_day = random.uniform(0, 1)
            
            # Calculate travel time based on features with bounds checking
            base_time = distance * 2  # 2 minutes per km base
            
            # Traffic impact (limit multiplier)
            traffic_multiplier = 1 + min(current_traffic * 0.8, 0.8)
            
            # Historical patterns (limit multiplier)
            historical_multiplier = 1 + min(historical_average * 0.3, 0.3)
            
            # Weather impact (limit multiplier)
            weather_multiplier = 1 + min(weather * 0.2, 0.2)
            
            # Time of day impact (limit multiplier)
            time_multiplier = 1 + min(time_of_day * 0.3, 0.3)
            
            travel_time = base_time * traffic_multiplier * historical_multiplier * weather_multiplier * time_multiplier
            
            # Ensure reasonable bounds
            travel_time = max(distance * 0.5, min(travel_time, distance * 10))
            
            X.append([distance, current_traffic, historical_average, weather, time_of_day])
            y.append(travel_time)
        
        # Normalize features to prevent overflow
        X_normalized = []
        for features in X:
            normalized = [
                features[0] / 50.0,  # distance normalized by max distance
                features[1],  # traffic already 0-1
                features[2],  # historical already 0-1
                features[3],  # weather already 0-1
                features[4]   # time already 0-1
            ]
            X_normalized.append(normalized)
        
        # Split data
        split_idx = int(len(X_normalized) * 0.8)
        X_train, X_test = X_normalized[:split_idx], X_normalized[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train linear regression with smaller learning rate
        model = SimpleLinearRegression()
        model.fit(X_train, y_train)
        
        # Evaluate
        predictions = model.predict(X_test)
        mse = sum((pred - actual) ** 2 for pred, actual in zip(predictions, y_test)) / len(y_test)
        mae = sum(abs(pred - actual) for pred, actual in zip(predictions, y_test)) / len(y_test)
        
        # Save model
        model_path = self.models_dir / "route_optimizer.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        metadata = {
            "model_type": "route_optimizer",
            "algorithm": "linear_regression",
            "mse": mse,
            "mae": mae,
            "trained_at": datetime.now().isoformat(),
            "samples_used": samples
        }
        
        with open(self.models_dir / "route_optimizer_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.trained_models["route_optimizer"] = model
        self.model_metrics["route_optimizer"] = metadata
        
        logger.info(f"Route optimizer trained successfully - MSE: {mse:.2f}, MAE: {mae:.2f}")
        return metadata
    
    def train_all_models(self, samples: int = 1000) -> Dict[str, Any]:
        """Train all models"""
        logger.info("Training all models")
        
        results = {}
        
        try:
            results["traffic_predictor"] = self.train_traffic_predictor(samples)
        except Exception as e:
            logger.error(f"Error training traffic predictor: {e}")
            results["traffic_predictor"] = {"error": str(e)}
        
        try:
            results["incident_detector"] = self.train_incident_detector(samples)
        except Exception as e:
            logger.error(f"Error training incident detector: {e}")
            results["incident_detector"] = {"error": str(e)}
        
        try:
            results["route_optimizer"] = self.train_route_optimizer(samples)
        except Exception as e:
            logger.error(f"Error training route optimizer: {e}")
            results["route_optimizer"] = {"error": str(e)}
        
        logger.info("All models training completed")
        return results
    
    def load_model(self, model_type: str) -> Any:
        """Load a trained model"""
        model_path = self.models_dir / f"{model_type}.pkl"
        
        if not model_path.exists():
            logger.warning(f"Model file not found: {model_path}")
            return None
        
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            logger.info(f"Model {model_type} loaded successfully")
            return model
        except Exception as e:
            logger.error(f"Error loading model {model_type}: {e}")
            return None
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        status = {}
        
        for model_type in ["traffic_predictor", "incident_detector", "route_optimizer"]:
            model_path = self.models_dir / f"{model_type}.pkl"
            metadata_path = self.models_dir / f"{model_type}_metadata.json"
            
            if model_path.exists() and metadata_path.exists():
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    status[model_type] = {
                        "trained": True,
                        "metadata": metadata
                    }
                except Exception as e:
                    status[model_type] = {
                        "trained": False,
                        "error": f"Error loading metadata: {e}"
                    }
            else:
                status[model_type] = {
                    "trained": False,
                    "error": "Model files not found"
                }
        
        return status


def main():
    """Main function to train all models"""
    print("🤖 Starting Simple ML Training System")
    
    trainer = SimpleMLTrainer()
    
    # Train all models
    results = trainer.train_all_models(samples=2000)
    
    print("\n📊 Training Results:")
    for model_type, result in results.items():
        if "error" in result:
            print(f"❌ {model_type}: {result['error']}")
        else:
            print(f"✅ {model_type}: {result.get('algorithm', 'unknown')} - Trained successfully")
    
    # Show model status
    print("\n📋 Model Status:")
    status = trainer.get_model_status()
    for model_type, info in status.items():
        if info["trained"]:
            metadata = info["metadata"]
            print(f"✅ {model_type}: {metadata['algorithm']} - {metadata['trained_at']}")
        else:
            print(f"❌ {model_type}: {info['error']}")
    
    print("\n🎯 All models trained successfully!")


if __name__ == "__main__":
    main() 