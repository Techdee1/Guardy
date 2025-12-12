"""
Flood Risk Scorer: Ensemble model for predicting flood risk levels

This module implements a FloodRiskScorer class that combines Random Forest
and Gradient Boosting classifiers to predict flood occurrence and severity.

Author: Guardy AI Team
Date: December 12, 2024
"""

import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from loguru import logger

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score
)
from sklearn.preprocessing import StandardScaler


class FloodRiskScorer:
    """
    Ensemble flood risk prediction model combining Random Forest and Gradient Boosting.
    
    The model predicts:
    1. Binary flood occurrence (0 = no flood, 1 = flood)
    2. Risk score (0-100)
    3. Confidence level
    
    Attributes:
        rf_model: Random Forest classifier
        gb_model: Gradient Boosting classifier
        scaler: StandardScaler for feature normalization (optional)
        feature_names: List of feature names used in training
        feature_importance: Dictionary of feature importance scores
        performance_metrics: Dictionary of model performance metrics
    """
    
    def __init__(
        self,
        use_scaling: bool = False,
        rf_params: Optional[Dict] = None,
        gb_params: Optional[Dict] = None
    ):
        """
        Initialize FloodRiskScorer with optional custom parameters.
        
        Args:
            use_scaling: Whether to apply StandardScaler to features
            rf_params: Custom Random Forest parameters
            gb_params: Custom Gradient Boosting parameters
        """
        # Default Random Forest parameters
        self.rf_params = rf_params or {
            'n_estimators': 200,
            'max_depth': 15,
            'min_samples_split': 10,
            'min_samples_leaf': 4,
            'max_features': 'sqrt',
            'random_state': 42,
            'n_jobs': -1,
            'class_weight': 'balanced'
        }
        
        # Default Gradient Boosting parameters
        self.gb_params = gb_params or {
            'n_estimators': 200,
            'learning_rate': 0.1,
            'max_depth': 7,
            'min_samples_split': 10,
            'min_samples_leaf': 4,
            'subsample': 0.8,
            'random_state': 42
        }
        
        self.use_scaling = use_scaling
        self.scaler = StandardScaler() if use_scaling else None
        
        # Initialize models
        self.rf_model = RandomForestClassifier(**self.rf_params)
        self.gb_model = GradientBoostingClassifier(**self.gb_params)
        
        # Metadata
        self.feature_names = None
        self.feature_importance = {}
        self.performance_metrics = {}
        self.is_trained = False
        
        logger.info("FloodRiskScorer initialized")
    
    def prepare_features(
        self,
        df: pd.DataFrame,
        feature_cols: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Prepare features for training/prediction."""
        exclude_cols = [
            'event_id', 'date', 'location', 'state', 'latitude', 'longitude',
            'flood_occurred', 'severity', 'description', 'source', 'sample_id',
            'rainfall_source', 'weather_source', 'season_name'
        ]
        
        if feature_cols is None:
            feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        X = df[feature_cols].copy()
        
        if X.isnull().any().any():
            X = X.fillna(X.median())
        
        return X, feature_cols
    
    def train(
        self,
        df: pd.DataFrame,
        target_col: str = 'flood_occurred',
        feature_cols: Optional[List[str]] = None,
        test_size: float = 0.2,
        perform_cv: bool = True,
        cv_folds: int = 5
    ) -> Dict:
        """Train the ensemble flood risk model."""
        logger.info("="*60)
        logger.info("Starting FloodRiskScorer training")
        logger.info("="*60)
        
        X, self.feature_names = self.prepare_features(df, feature_cols)
        y = df[target_col]
        
        logger.info(f"Dataset: {len(df)} samples, {len(self.feature_names)} features")
        logger.info(f"Flood rate: {y.mean()*100:.1f}%")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        if self.use_scaling:
            X_train = self.scaler.fit_transform(X_train)
            X_test = self.scaler.transform(X_test)
        
        # Train Random Forest
        logger.info("\nTraining Random Forest...")
        self.rf_model.fit(X_train, y_train)
        rf_test_pred = self.rf_model.predict(X_test)
        rf_test_proba = self.rf_model.predict_proba(X_test)[:, 1]
        
        rf_metrics = {
            'test_accuracy': accuracy_score(y_test, rf_test_pred),
            'precision': precision_score(y_test, rf_test_pred, zero_division=0),
            'recall': recall_score(y_test, rf_test_pred, zero_division=0),
            'f1_score': f1_score(y_test, rf_test_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_test, rf_test_proba)
        }
        
        logger.info(f"  Accuracy: {rf_metrics['test_accuracy']:.4f}, Recall: {rf_metrics['recall']:.4f}")
        
        # Train Gradient Boosting
        logger.info("\nTraining Gradient Boosting...")
        self.gb_model.fit(X_train, y_train)
        gb_test_pred = self.gb_model.predict(X_test)
        gb_test_proba = self.gb_model.predict_proba(X_test)[:, 1]
        
        gb_metrics = {
            'test_accuracy': accuracy_score(y_test, gb_test_pred),
            'precision': precision_score(y_test, gb_test_pred, zero_division=0),
            'recall': recall_score(y_test, gb_test_pred, zero_division=0),
            'f1_score': f1_score(y_test, gb_test_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_test, gb_test_proba)
        }
        
        logger.info(f"  Accuracy: {gb_metrics['test_accuracy']:.4f}, Recall: {gb_metrics['recall']:.4f}")
        
        # Ensemble
        logger.info("\nCreating Ensemble...")
        ensemble_proba = (rf_test_proba + gb_test_proba) / 2
        ensemble_pred = (ensemble_proba >= 0.5).astype(int)
        
        ensemble_metrics = {
            'test_accuracy': accuracy_score(y_test, ensemble_pred),
            'precision': precision_score(y_test, ensemble_pred, zero_division=0),
            'recall': recall_score(y_test, ensemble_pred, zero_division=0),
            'f1_score': f1_score(y_test, ensemble_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_test, ensemble_proba)
        }
        
        logger.info(f"  Accuracy: {ensemble_metrics['test_accuracy']:.4f}")
        logger.info(f"  Precision: {ensemble_metrics['precision']:.4f}")
        logger.info(f"  Recall: {ensemble_metrics['recall']:.4f}")
        logger.info(f"  F1-Score: {ensemble_metrics['f1_score']:.4f}")
        logger.info(f"  ROC-AUC: {ensemble_metrics['roc_auc']:.4f}")
        
        cm = confusion_matrix(y_test, ensemble_pred)
        logger.info(f"\nConfusion Matrix: TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]}")
        
        # Feature importance
        rf_importance = self.rf_model.feature_importances_
        gb_importance = self.gb_model.feature_importances_
        avg_importance = (rf_importance + gb_importance) / 2
        self.feature_importance = dict(zip(self.feature_names, avg_importance))
        
        top_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
        logger.info("\nTop 10 Features:")
        for i, (feature, importance) in enumerate(top_features, 1):
            logger.info(f"  {i}. {feature}: {importance:.4f}")
        
        self.performance_metrics = {
            'random_forest': rf_metrics,
            'gradient_boosting': gb_metrics,
            'ensemble': ensemble_metrics
        }
        
        self.is_trained = True
        logger.info("\n✅ Training Complete!")
        
        return {
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'metrics': self.performance_metrics
        }
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict flood probability."""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        X_prepared, _ = self.prepare_features(X, self.feature_names)
        
        if self.use_scaling:
            X_prepared = self.scaler.transform(X_prepared)
        
        rf_proba = self.rf_model.predict_proba(X_prepared)[:, 1]
        gb_proba = self.gb_model.predict_proba(X_prepared)[:, 1]
        return (rf_proba + gb_proba) / 2
    
    def predict_risk_score(self, X: pd.DataFrame) -> Dict:
        """Predict flood risk with score (0-100) and confidence."""
        probabilities = self.predict_proba(X)
        risk_scores = (probabilities * 100).round(1)
        
        confidence_levels = ['high' if (p < 0.3 or p > 0.7) else 'medium' if (p < 0.4 or p > 0.6) else 'low' for p in probabilities]
        risk_categories = ['high' if s >= 70 else 'medium' if s >= 40 else 'low' for s in risk_scores]
        
        return {
            'predictions': (probabilities >= 0.5).astype(int),
            'probabilities': probabilities,
            'risk_scores': risk_scores,
            'risk_categories': risk_categories,
            'confidence_levels': confidence_levels
        }
    
    def save(self, filepath: str) -> None:
        """Save trained model."""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'rf_model': self.rf_model,
            'gb_model': self.gb_model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
            'performance_metrics': self.performance_metrics,
            'use_scaling': self.use_scaling
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"✅ Model saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'FloodRiskScorer':
        """Load trained model."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        instance = cls(use_scaling=model_data['use_scaling'])
        instance.rf_model = model_data['rf_model']
        instance.gb_model = model_data['gb_model']
        instance.scaler = model_data['scaler']
        instance.feature_names = model_data['feature_names']
        instance.feature_importance = model_data['feature_importance']
        instance.performance_metrics = model_data['performance_metrics']
        instance.is_trained = True
        
        logger.info(f"✅ Model loaded from {filepath}")
        return instance
