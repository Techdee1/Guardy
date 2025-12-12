"""
Sensor Anomaly Detection using Isolation Forest.

This module implements a SensorAnomalyDetector class that uses Isolation Forest
to detect anomalous sensor readings (water level, rainfall, temperature, humidity).
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pickle
from loguru import logger

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
except ImportError:
    logger.warning("scikit-learn not installed. Install with: pip install scikit-learn")
    IsolationForest = None
    StandardScaler = None


class SensorAnomalyDetector:
    """
    Isolation Forest-based anomaly detection for sensor readings.
    
    Detects anomalies in:
    - Water level measurements
    - Rainfall intensity
    - Temperature readings
    - Humidity levels
    - Sensor behavior patterns
    """
    
    def __init__(
        self,
        contamination: float = 0.05,
        n_estimators: int = 100,
        max_samples: int = 256,
        random_state: int = 42
    ):
        """
        Initialize the SensorAnomalyDetector.
        
        Args:
            contamination: Expected proportion of anomalies (default: 0.05 = 5%)
            n_estimators: Number of isolation trees (default: 100)
            max_samples: Number of samples to draw for each tree (default: 256)
            random_state: Random seed for reproducibility
        """
        if IsolationForest is None:
            raise ImportError("scikit-learn is required. Install with: pip install scikit-learn")
        
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.random_state = random_state
        
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            max_samples=max_samples,
            random_state=random_state,
            n_jobs=-1
        )
        
        self.scaler = StandardScaler()
        self.feature_names = None
        self.is_trained = False
        self.training_stats = {}
        
        logger.info(f"Initialized SensorAnomalyDetector (contamination={contamination}, n_estimators={n_estimators})")
    
    def prepare_features(
        self,
        df: pd.DataFrame,
        feature_columns: List[str]
    ) -> np.ndarray:
        """
        Prepare features for anomaly detection.
        
        Args:
            df: DataFrame with sensor readings
            feature_columns: List of feature column names
            
        Returns:
            Scaled feature array
        """
        self.feature_names = feature_columns
        
        # Extract features
        X = df[feature_columns].values
        
        # Scale features
        if not self.is_trained:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        return X_scaled
    
    def train(
        self,
        X: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> Dict:
        """
        Train the Isolation Forest model.
        
        Args:
            X: Feature array (samples, features)
            feature_names: List of feature names (optional)
            
        Returns:
            Dictionary with training statistics
        """
        logger.info(f"Training Isolation Forest on {len(X)} samples...")
        
        if feature_names is not None:
            self.feature_names = feature_names
        
        # Fit the model
        self.model.fit(X)
        self.is_trained = True
        
        # Get anomaly predictions on training data
        predictions = self.model.predict(X)
        anomaly_scores = self.model.score_samples(X)
        
        # Calculate statistics
        n_anomalies = (predictions == -1).sum()
        anomaly_rate = n_anomalies / len(X)
        
        self.training_stats = {
            'n_samples': len(X),
            'n_features': X.shape[1],
            'n_anomalies_detected': int(n_anomalies),
            'anomaly_rate': float(anomaly_rate),
            'mean_anomaly_score': float(anomaly_scores.mean()),
            'std_anomaly_score': float(anomaly_scores.std()),
            'min_anomaly_score': float(anomaly_scores.min()),
            'max_anomaly_score': float(anomaly_scores.max())
        }
        
        logger.info(f"Training complete - Detected {n_anomalies} anomalies ({anomaly_rate:.1%})")
        return self.training_stats
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict anomalies (binary: -1 for anomaly, 1 for normal).
        
        Args:
            X: Feature array
            
        Returns:
            Array of predictions (-1 = anomaly, 1 = normal)
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict anomaly scores (lower = more anomalous).
        
        Args:
            X: Feature array
            
        Returns:
            Array of anomaly scores
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        return self.model.score_samples(X)
    
    def detect_anomalies(
        self,
        X: np.ndarray,
        return_scores: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Detect anomalies and optionally return scores.
        
        Args:
            X: Feature array
            return_scores: Whether to return anomaly scores
            
        Returns:
            Tuple of (is_anomaly array, anomaly_scores array)
            is_anomaly: Boolean array (True = anomaly)
            anomaly_scores: Anomaly scores (if return_scores=True)
        """
        predictions = self.predict(X)
        is_anomaly = predictions == -1
        
        if return_scores:
            scores = self.predict_proba(X)
            return is_anomaly, scores
        else:
            return is_anomaly, None
    
    def detect_single(
        self,
        features: Dict[str, float]
    ) -> Dict:
        """
        Detect anomaly for a single sensor reading.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Dictionary with detection results:
                - is_anomaly: Boolean
                - anomaly_score: Anomaly score (lower = more anomalous)
                - severity: 'normal', 'low', 'medium', 'high'
                - confidence: Detection confidence (0-1)
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        if self.feature_names is None:
            raise ValueError("Feature names not set. Retrain model with feature names.")
        
        # Prepare feature array
        feature_array = np.array([[features.get(name, 0) for name in self.feature_names]])
        
        # Get prediction and score
        prediction = self.predict(feature_array)[0]
        score = self.predict_proba(feature_array)[0]
        
        is_anomaly = prediction == -1
        
        # Calculate severity based on score
        # Scores are negative, with more negative = more anomalous
        if is_anomaly:
            if score < self.training_stats['mean_anomaly_score'] - 2 * self.training_stats['std_anomaly_score']:
                severity = 'high'
                confidence = 0.9
            elif score < self.training_stats['mean_anomaly_score'] - self.training_stats['std_anomaly_score']:
                severity = 'medium'
                confidence = 0.7
            else:
                severity = 'low'
                confidence = 0.5
        else:
            severity = 'normal'
            confidence = 0.8
        
        return {
            'is_anomaly': bool(is_anomaly),
            'anomaly_score': float(score),
            'severity': severity,
            'confidence': float(confidence),
            'threshold': float(self.training_stats['mean_anomaly_score'])
        }
    
    def get_feature_importance(self, X: np.ndarray) -> Dict[str, float]:
        """
        Estimate feature importance based on anomaly score variance.
        
        Args:
            X: Feature array
            
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        if self.feature_names is None:
            raise ValueError("Feature names not set.")
        
        # Get baseline scores
        baseline_scores = self.predict_proba(X)
        
        # Calculate importance by permuting each feature
        importances = {}
        for i, feature_name in enumerate(self.feature_names):
            X_permuted = X.copy()
            np.random.shuffle(X_permuted[:, i])
            permuted_scores = self.predict_proba(X_permuted)
            
            # Importance = change in average score
            importance = np.abs(permuted_scores.mean() - baseline_scores.mean())
            importances[feature_name] = float(importance)
        
        # Normalize to sum to 1
        total = sum(importances.values())
        if total > 0:
            importances = {k: v/total for k, v in importances.items()}
        
        return importances
    
    def save(self, model_path: str):
        """
        Save model, scaler, and metadata.
        
        Args:
            model_path: Path to save model (.pkl)
        """
        if not self.is_trained:
            raise ValueError("No trained model to save.")
        
        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'training_stats': self.training_stats,
            'contamination': self.contamination,
            'n_estimators': self.n_estimators,
            'max_samples': self.max_samples,
            'random_state': self.random_state
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {model_path}")
    
    @classmethod
    def load(cls, model_path: str) -> 'SensorAnomalyDetector':
        """
        Load saved model.
        
        Args:
            model_path: Path to saved model file
            
        Returns:
            Loaded SensorAnomalyDetector instance
        """
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        # Create instance
        instance = cls(
            contamination=model_data['contamination'],
            n_estimators=model_data['n_estimators'],
            max_samples=model_data['max_samples'],
            random_state=model_data['random_state']
        )
        
        # Load trained model and metadata
        instance.model = model_data['model']
        instance.scaler = model_data['scaler']
        instance.feature_names = model_data['feature_names']
        instance.training_stats = model_data['training_stats']
        instance.is_trained = True
        
        logger.info(f"Model loaded from {model_path}")
        return instance
