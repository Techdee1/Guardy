"""
Training script for Flood Nowcasting LSTM Model.

This script trains the FloodNowcaster model on historical flood data with
time-series sequences of weather patterns.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from loguru import logger
import matplotlib.pyplot as plt
import seaborn as sns

from app.ml.flood_nowcaster import FloodNowcaster


def plot_training_history(history: dict, save_path: str = "figures/nowcaster_training.png"):
    """Plot training history (loss and accuracy curves)."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Loss curves
    axes[0, 0].plot(history['loss'], label='Train Loss', linewidth=2)
    if 'val_loss' in history:
        axes[0, 0].plot(history['val_loss'], label='Val Loss', linewidth=2)
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].set_title('Training and Validation Loss')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Accuracy curves
    axes[0, 1].plot(history['accuracy'], label='Train Accuracy', linewidth=2)
    if 'val_accuracy' in history:
        axes[0, 1].plot(history['val_accuracy'], label='Val Accuracy', linewidth=2)
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('Accuracy')
    axes[0, 1].set_title('Training and Validation Accuracy')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Precision curves
    axes[1, 0].plot(history['precision'], label='Train Precision', linewidth=2)
    if 'val_precision' in history:
        axes[1, 0].plot(history['val_precision'], label='Val Precision', linewidth=2)
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('Precision')
    axes[1, 0].set_title('Training and Validation Precision')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Recall curves
    axes[1, 1].plot(history['recall'], label='Train Recall', linewidth=2)
    if 'val_recall' in history:
        axes[1, 1].plot(history['val_recall'], label='Val Recall', linewidth=2)
    axes[1, 1].set_xlabel('Epoch')
    axes[1, 1].set_ylabel('Recall')
    axes[1, 1].set_title('Training and Validation Recall')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Create figures directory if it doesn't exist
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    logger.info(f"Training history plot saved to {save_path}")
    plt.close()


def plot_predictions(y_true: np.ndarray, y_pred: np.ndarray, save_path: str = "figures/nowcaster_predictions.png"):
    """Plot actual vs predicted values."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Scatter plot
    axes[0].scatter(y_true, y_pred, alpha=0.5, s=20)
    axes[0].plot([0, 1], [0, 1], 'r--', linewidth=2, label='Perfect Prediction')
    axes[0].set_xlabel('Actual Flood Probability')
    axes[0].set_ylabel('Predicted Flood Probability')
    axes[0].set_title('Actual vs Predicted Flood Probabilities')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Distribution comparison
    axes[1].hist(y_true, bins=20, alpha=0.5, label='Actual', density=True)
    axes[1].hist(y_pred, bins=20, alpha=0.5, label='Predicted', density=True)
    axes[1].set_xlabel('Flood Probability')
    axes[1].set_ylabel('Density')
    axes[1].set_title('Distribution of Actual vs Predicted')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    logger.info(f"Prediction plot saved to {save_path}")
    plt.close()


def main():
    """Main training pipeline."""
    logger.info("=" * 60)
    logger.info("FLOOD NOWCASTER (LSTM) TRAINING")
    logger.info("=" * 60)
    
    # Load data
    data_path = "data/training/engineered_features_flood_dataset.csv"
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Sort by location and date for proper time-series sequences
    df = df.sort_values(['location', 'date']).reset_index(drop=True)
    
    logger.info(f"Dataset: {len(df)} samples")
    logger.info(f"Locations: {df['location'].nunique()}")
    logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
    logger.info(f"Flood rate: {df['flood_occurred'].mean():.1%}")
    
    # Select features for LSTM
    # Use time-varying features (exclude location encoding, constant features)
    feature_columns = [
        'rainfall_mm', 'temperature', 'humidity',
        'rainfall_7d_sum', 'rainfall_7d_mean', 'rainfall_7d_max',
        'rainfall_30d_sum', 'rainfall_30d_mean', 'rainfall_30d_max',
        'month', 'day_of_year', 'is_rainy_season',
        'month_sin', 'month_cos',
        'rainfall_humidity_interaction', 'temp_humidity_ratio',
        'rainfall_deviation', 'temp_deviation_seasonal',
        'heavy_rain_flag', 'extreme_humidity_flag', 'wet_soil_proxy'
    ]
    
    logger.info(f"Using {len(feature_columns)} features for sequences")
    
    # Initialize model
    nowcaster = FloodNowcaster(
        sequence_length=7,  # 7-day sequences
        lstm_units=[64, 32],
        dropout_rate=0.3,  # Higher dropout for small dataset
        learning_rate=0.001
    )
    
    # Prepare sequences
    logger.info("Preparing time-series sequences...")
    X, y = nowcaster.prepare_sequences(
        df=df,
        feature_columns=feature_columns,
        target_column='flood_occurred'
    )
    
    logger.info(f"Created {len(X)} sequences")
    logger.info(f"Sequence shape: {X.shape}")
    logger.info(f"Target shape: {y.shape}")
    logger.info(f"Flood rate in sequences: {y.mean():.1%}")
    
    # Split into train/val/test
    # First split: 80% train+val, 20% test
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Second split: 75% train, 25% val (of the 80%)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
    )
    
    logger.info(f"Train set: {len(X_train)} sequences ({y_train.mean():.1%} flood rate)")
    logger.info(f"Val set: {len(X_val)} sequences ({y_val.mean():.1%} flood rate)")
    logger.info(f"Test set: {len(X_test)} sequences ({y_test.mean():.1%} flood rate)")
    
    # Train model
    logger.info("\nTraining LSTM model...")
    logger.info("-" * 60)
    
    metrics = nowcaster.train(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        epochs=100,  # Will stop early if no improvement
        batch_size=16,  # Smaller batch for small dataset
        verbose=1
    )
    
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 60)
    
    # Print final metrics
    logger.info("\nFinal Training Metrics:")
    logger.info(f"  Loss:      {metrics['train_loss']:.4f}")
    logger.info(f"  Accuracy:  {metrics['train_accuracy']:.4f} ({metrics['train_accuracy']:.1%})")
    logger.info(f"  Precision: {metrics['train_precision']:.4f}")
    logger.info(f"  Recall:    {metrics['train_recall']:.4f}")
    
    if 'val_accuracy' in metrics:
        logger.info("\nValidation Metrics:")
        logger.info(f"  Loss:      {metrics['val_loss']:.4f}")
        logger.info(f"  Accuracy:  {metrics['val_accuracy']:.4f} ({metrics['val_accuracy']:.1%})")
        logger.info(f"  Precision: {metrics['val_precision']:.4f}")
        logger.info(f"  Recall:    {metrics['val_recall']:.4f}")
    
    # Evaluate on test set
    logger.info("\nEvaluating on test set...")
    test_metrics = nowcaster.model.evaluate(X_test, y_test, verbose=0)
    logger.info("Test Set Metrics:")
    logger.info(f"  Loss:      {test_metrics[0]:.4f}")
    logger.info(f"  Accuracy:  {test_metrics[1]:.4f} ({test_metrics[1]:.1%})")
    logger.info(f"  Precision: {test_metrics[2]:.4f}")
    logger.info(f"  Recall:    {test_metrics[3]:.4f}")
    
    # Make predictions on test set
    y_pred_proba = nowcaster.predict_proba(X_test)
    y_pred = nowcaster.predict(X_test)
    
    # Calculate additional metrics
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    logger.info(f"\nConfusion Matrix:")
    logger.info(f"  TN={cm[0,0]}, FP={cm[0,1]}")
    logger.info(f"  FN={cm[1,0]}, TP={cm[1,1]}")
    
    # ROC-AUC
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    logger.info(f"\nROC-AUC Score: {roc_auc:.4f} ({roc_auc:.1%})")
    
    # Classification report
    logger.info("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['No Flood', 'Flood']))
    
    # Plot training history
    logger.info("\nGenerating visualizations...")
    plot_training_history(nowcaster.training_history)
    plot_predictions(y_test, y_pred_proba)
    
    # Save model
    model_path = "models/nowcast_lstm_v1.h5"
    logger.info(f"\nSaving model to {model_path}")
    nowcaster.save(model_path)
    
    # Get file size
    model_size = Path(model_path).stat().st_size / (1024 * 1024)
    logger.info(f"Model size: {model_size:.2f} MB")
    
    # Test model loading
    logger.info("\nTesting model loading...")
    loaded_model = FloodNowcaster.load(model_path)
    
    # Test predictions
    test_sample = X_test[:5]
    test_labels = y_test[:5]
    predictions = loaded_model.predict_proba(test_sample)
    
    logger.info("\nSample predictions (loaded model):")
    for i, (actual, pred) in enumerate(zip(test_labels, predictions)):
        logger.info(f"  Sample {i+1}: Actual={actual}, Predicted={pred:.3f}")
    
    # Test nowcast functionality
    logger.info("\nTesting nowcast functionality...")
    nowcast = loaded_model.predict_nowcast(test_sample[0])
    logger.info("Multi-horizon nowcast:")
    for hours, prediction in nowcast.items():
        logger.info(f"  {hours}h: {prediction['probability']:.3f} ({prediction['risk_level']}, confidence={prediction['confidence']:.3f})")
    
    logger.info("\n" + "=" * 60)
    logger.info("NOWCASTER TRAINING PIPELINE COMPLETE!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
