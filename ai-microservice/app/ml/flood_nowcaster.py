"""
Flood Nowcasting Model using LSTM for time-series prediction.

This module implements a FloodNowcaster class that uses LSTM (Long Short-Term Memory)
neural networks to predict flood probability for the next 1-24 hours based on 
recent weather patterns and sensor data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import pickle
from loguru import logger

try:
    from tensorflow import keras
    from tensorflow.keras import layers, models, callbacks
    from tensorflow.keras.models import load_model as keras_load_model
except ImportError:
    logger.warning("TensorFlow not installed. Install with: pip install tensorflow")
    keras = None


class FloodNowcaster:
    """
    LSTM-based flood nowcasting model for short-term (1-24 hour) predictions.
    
    Uses time-series sequences of weather data (rainfall, temperature, humidity)
    to predict flood probability in the near future.
    """
    
    def __init__(
        self,
        sequence_length: int = 7,
        lstm_units: List[int] = [64, 32],
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001
    ):
        """
        Initialize the FloodNowcaster model.
        
        Args:
            sequence_length: Number of time steps to look back (default: 7 days)
            lstm_units: List of units for each LSTM layer (default: [64, 32])
            dropout_rate: Dropout rate for regularization (default: 0.2)
            learning_rate: Learning rate for Adam optimizer (default: 0.001)
        """
        if keras is None:
            raise ImportError("TensorFlow is required for FloodNowcaster. Install with: pip install tensorflow")
        
        self.sequence_length = sequence_length
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        
        self.model = None
        self.feature_names = None
        self.scaler = None
        self.training_history = None
        
        logger.info(f"Initialized FloodNowcaster (sequence_length={sequence_length}, lstm_units={lstm_units})")
    
    def _build_model(self, n_features: int) -> models.Sequential:
        """
        Build LSTM model architecture.
        
        Args:
            n_features: Number of input features
            
        Returns:
            Compiled Keras Sequential model
        """
        model = models.Sequential(name="flood_nowcaster")
        
        # First LSTM layer
        model.add(layers.Input(shape=(self.sequence_length, n_features)))
        model.add(layers.LSTM(
            units=self.lstm_units[0],
            return_sequences=len(self.lstm_units) > 1,
            name="lstm_1"
        ))
        model.add(layers.Dropout(self.dropout_rate, name="dropout_1"))
        
        # Additional LSTM layers
        for i, units in enumerate(self.lstm_units[1:], start=2):
            return_seq = i < len(self.lstm_units)
            model.add(layers.LSTM(
                units=units,
                return_sequences=return_seq,
                name=f"lstm_{i}"
            ))
            model.add(layers.Dropout(self.dropout_rate, name=f"dropout_{i}"))
        
        # Dense output layer for binary classification
        model.add(layers.Dense(1, activation='sigmoid', name="output"))
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
        )
        
        logger.info(f"Built LSTM model with {n_features} features")
        return model
    
    def prepare_sequences(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        target_column: str = 'flood_occurred'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare time-series sequences from dataframe.
        
        Args:
            df: DataFrame with time-series data (must be sorted by location, date)
            feature_columns: List of feature column names
            target_column: Name of target column
            
        Returns:
            Tuple of (X sequences, y targets)
        """
        from sklearn.preprocessing import StandardScaler
        
        # Store feature names
        self.feature_names = feature_columns
        
        # Scale features
        if self.scaler is None:
            self.scaler = StandardScaler()
            scaled_features = self.scaler.fit_transform(df[feature_columns])
        else:
            scaled_features = self.scaler.transform(df[feature_columns])
        
        # Create sequences per location to maintain temporal continuity
        X, y = [], []
        locations = df['location'].unique() if 'location' in df.columns else [None]
        
        for location in locations:
            if location is not None:
                loc_mask = df['location'] == location
                loc_features = scaled_features[loc_mask]
                loc_targets = df[loc_mask][target_column].values
            else:
                loc_features = scaled_features
                loc_targets = df[target_column].values
            
            # Create sequences for this location
            for i in range(len(loc_features) - self.sequence_length):
                X.append(loc_features[i:i + self.sequence_length])
                y.append(loc_targets[i + self.sequence_length])
        
        X = np.array(X)
        y = np.array(y)
        
        logger.info(f"Created {len(X)} sequences (shape: {X.shape})")
        return X, y
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 50,
        batch_size: int = 32,
        verbose: int = 1
    ) -> Dict:
        """
        Train the LSTM model.
        
        Args:
            X_train: Training sequences (samples, sequence_length, features)
            y_train: Training targets
            X_val: Validation sequences (optional)
            y_val: Validation targets (optional)
            epochs: Number of training epochs
            batch_size: Batch size for training
            verbose: Verbosity level (0=silent, 1=progress, 2=epoch)
            
        Returns:
            Dictionary with training metrics
        """
        n_features = X_train.shape[2]
        
        # Build model if not already built
        if self.model is None:
            self.model = self._build_model(n_features)
        
        # Setup callbacks
        callback_list = [
            callbacks.EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            callbacks.ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=5,
                verbose=1,
                min_lr=1e-7
            )
        ]
        
        # Prepare validation data
        validation_data = (X_val, y_val) if X_val is not None and y_val is not None else None
        
        # Train model
        logger.info(f"Training LSTM model (epochs={epochs}, batch_size={batch_size})")
        history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callback_list,
            verbose=verbose
        )
        
        self.training_history = history.history
        
        # Calculate final metrics
        train_metrics = self.model.evaluate(X_train, y_train, verbose=0)
        metrics = {
            'train_loss': train_metrics[0],
            'train_accuracy': train_metrics[1],
            'train_precision': train_metrics[2],
            'train_recall': train_metrics[3]
        }
        
        if validation_data is not None:
            val_metrics = self.model.evaluate(X_val, y_val, verbose=0)
            metrics.update({
                'val_loss': val_metrics[0],
                'val_accuracy': val_metrics[1],
                'val_precision': val_metrics[2],
                'val_recall': val_metrics[3]
            })
        
        logger.info(f"Training complete - Train Acc: {metrics['train_accuracy']:.4f}")
        if validation_data is not None:
            logger.info(f"Validation Acc: {metrics['val_accuracy']:.4f}")
        
        return metrics
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict flood probability for sequences.
        
        Args:
            X: Input sequences (samples, sequence_length, features)
            
        Returns:
            Array of flood probabilities (0-1)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        probabilities = self.model.predict(X, verbose=0)
        return probabilities.flatten()
    
    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """
        Predict binary flood occurrence.
        
        Args:
            X: Input sequences
            threshold: Classification threshold (default: 0.5)
            
        Returns:
            Binary predictions (0 or 1)
        """
        probabilities = self.predict_proba(X)
        return (probabilities >= threshold).astype(int)
    
    def predict_nowcast(
        self,
        sequence: np.ndarray,
        hours_ahead: List[int] = [1, 3, 6, 12, 24]
    ) -> Dict[int, Dict[str, float]]:
        """
        Generate multi-horizon nowcast predictions.
        
        Args:
            sequence: Recent data sequence (sequence_length, features)
            hours_ahead: List of forecast horizons in hours
            
        Returns:
            Dictionary mapping hours to predictions
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Ensure sequence has batch dimension
        if sequence.ndim == 2:
            sequence = np.expand_dims(sequence, axis=0)
        
        # Get base prediction
        base_prob = self.predict_proba(sequence)[0]
        
        # Generate predictions for each horizon
        # Note: This is a simplified approach. In production, you'd train
        # separate models or use sequence-to-sequence architecture
        nowcasts = {}
        for hours in hours_ahead:
            # Apply time decay to probability (further ahead = more uncertainty)
            decay_factor = np.exp(-0.05 * hours)
            adjusted_prob = base_prob * (1 + (1 - decay_factor) * 0.1)
            adjusted_prob = np.clip(adjusted_prob, 0, 1)
            
            nowcasts[hours] = {
                'probability': float(adjusted_prob),
                'risk_level': self._get_risk_level(adjusted_prob),
                'confidence': float(decay_factor)
            }
        
        return nowcasts
    
    def _get_risk_level(self, probability: float) -> str:
        """Convert probability to risk level category."""
        if probability >= 0.7:
            return 'high'
        elif probability >= 0.4:
            return 'moderate'
        elif probability >= 0.2:
            return 'low'
        else:
            return 'very_low'
    
    def save(self, model_path: str, metadata_path: Optional[str] = None):
        """
        Save model and metadata.
        
        Args:
            model_path: Path to save Keras model (.h5 or .keras)
            metadata_path: Path to save metadata pickle (optional)
        """
        if self.model is None:
            raise ValueError("No model to save. Train model first.")
        
        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save Keras model
        self.model.save(model_path)
        logger.info(f"Model saved to {model_path}")
        
        # Save metadata
        if metadata_path is None:
            metadata_path = str(model_path).replace('.h5', '.meta.pkl').replace('.keras', '.meta.pkl')
        
        metadata = {
            'sequence_length': self.sequence_length,
            'lstm_units': self.lstm_units,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate,
            'feature_names': self.feature_names,
            'scaler': self.scaler,
            'training_history': self.training_history
        }
        
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"Metadata saved to {metadata_path}")
    
    @classmethod
    def load(cls, model_path: str, metadata_path: Optional[str] = None) -> 'FloodNowcaster':
        """
        Load model and metadata.
        
        Args:
            model_path: Path to Keras model file
            metadata_path: Path to metadata pickle (optional)
            
        Returns:
            Loaded FloodNowcaster instance
        """
        model_path = Path(model_path)
        
        if metadata_path is None:
            metadata_path = str(model_path).replace('.h5', '.meta.pkl').replace('.keras', '.meta.pkl')
        
        # Load metadata
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        # Create instance
        instance = cls(
            sequence_length=metadata['sequence_length'],
            lstm_units=metadata['lstm_units'],
            dropout_rate=metadata['dropout_rate'],
            learning_rate=metadata['learning_rate']
        )
        
        # Load Keras model
        instance.model = keras_load_model(model_path)
        instance.feature_names = metadata['feature_names']
        instance.scaler = metadata['scaler']
        instance.training_history = metadata['training_history']
        
        logger.info(f"Model loaded from {model_path}")
        return instance
