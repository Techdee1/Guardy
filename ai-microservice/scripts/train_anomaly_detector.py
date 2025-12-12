"""
Training script for Sensor Anomaly Detection Model.

This script trains the SensorAnomalyDetector using Isolation Forest
to detect anomalous sensor readings in the flood monitoring system.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from loguru import logger
import matplotlib.pyplot as plt
import seaborn as sns

from app.ml.anomaly_detector import SensorAnomalyDetector


def inject_synthetic_anomalies(
    df: pd.DataFrame,
    feature_columns: List[str],
    anomaly_rate: float = 0.05
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Inject synthetic anomalies for evaluation purposes.
    
    Args:
        df: Original dataframe
        feature_columns: Features to inject anomalies into
        anomaly_rate: Proportion of samples to make anomalous
        
    Returns:
        Tuple of (modified df, anomaly labels)
    """
    df = df.copy()
    n_samples = len(df)
    n_anomalies = int(n_samples * anomaly_rate)
    
    # Randomly select indices for anomalies
    anomaly_indices = np.random.choice(n_samples, n_anomalies, replace=False)
    labels = np.zeros(n_samples, dtype=int)
    labels[anomaly_indices] = 1
    
    # Inject anomalies by adding extreme values
    for idx in anomaly_indices:
        for col in feature_columns:
            if col in df.columns:
                # Add extreme outlier (3-5 std deviations)
                mean = df[col].mean()
                std = df[col].std()
                multiplier = np.random.choice([-1, 1]) * np.random.uniform(3, 5)
                df.loc[df.index[idx], col] = mean + multiplier * std
    
    logger.info(f"Injected {n_anomalies} synthetic anomalies ({anomaly_rate:.1%})")
    return df, labels


def plot_anomaly_scores(
    scores: np.ndarray,
    labels: np.ndarray,
    save_path: str = "figures/anomaly_scores.png"
):
    """Plot distribution of anomaly scores."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Score distribution by class
    normal_scores = scores[labels == 0]
    anomaly_scores = scores[labels == 1]
    
    axes[0].hist(normal_scores, bins=30, alpha=0.7, label='Normal', density=True)
    axes[0].hist(anomaly_scores, bins=30, alpha=0.7, label='Anomaly', density=True)
    axes[0].set_xlabel('Anomaly Score')
    axes[0].set_ylabel('Density')
    axes[0].set_title('Anomaly Score Distribution')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Box plot
    data_to_plot = [normal_scores, anomaly_scores]
    axes[1].boxplot(data_to_plot, labels=['Normal', 'Anomaly'])
    axes[1].set_ylabel('Anomaly Score')
    axes[1].set_title('Anomaly Score Comparison')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    logger.info(f"Anomaly score plot saved to {save_path}")
    plt.close()


def plot_feature_importance(
    importances: Dict[str, float],
    save_path: str = "figures/anomaly_feature_importance.png"
):
    """Plot feature importance for anomaly detection."""
    # Sort by importance
    sorted_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    features = [f[0] for f in sorted_features[:15]]  # Top 15
    values = [f[1] for f in sorted_features[:15]]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(features, values, color='coral')
    ax.set_xlabel('Importance Score')
    ax.set_title('Feature Importance for Anomaly Detection (Top 15)')
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    logger.info(f"Feature importance plot saved to {save_path}")
    plt.close()


def main():
    """Main training pipeline."""
    logger.info("=" * 60)
    logger.info("SENSOR ANOMALY DETECTOR TRAINING")
    logger.info("=" * 60)
    
    # Load data
    data_path = "data/training/engineered_features_flood_dataset.csv"
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    logger.info(f"Dataset: {len(df)} samples")
    logger.info(f"Features: {len(df.columns)} columns")
    
    # Select features for anomaly detection
    # Focus on sensor readings and derived metrics
    feature_columns = [
        'rainfall_mm', 'temperature', 'humidity',
        'rainfall_7d_mean', 'rainfall_7d_max',
        'rainfall_30d_mean', 'rainfall_30d_max',
        'rainfall_humidity_interaction',
        'temp_humidity_ratio',
        'rainfall_deviation',
        'temp_deviation_seasonal',
        'heavy_rain_flag',
        'extreme_humidity_flag',
        'wet_soil_proxy'
    ]
    
    logger.info(f"Using {len(feature_columns)} features for anomaly detection")
    
    # Inject synthetic anomalies for evaluation
    logger.info("\nInjecting synthetic anomalies for evaluation...")
    df_with_anomalies, true_labels = inject_synthetic_anomalies(
        df=df,
        feature_columns=feature_columns,
        anomaly_rate=0.05  # 5% anomalies
    )
    
    # Initialize detector
    detector = SensorAnomalyDetector(
        contamination=0.05,  # Expect 5% anomalies
        n_estimators=100,
        max_samples=256,
        random_state=42
    )
    
    # Prepare features
    logger.info("\nPreparing features...")
    X = detector.prepare_features(df_with_anomalies, feature_columns)
    
    logger.info(f"Feature matrix shape: {X.shape}")
    
    # Train model
    logger.info("\nTraining Isolation Forest...")
    logger.info("-" * 60)
    
    stats = detector.train(X, feature_names=feature_columns)
    
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 60)
    
    # Print training statistics
    logger.info("\nTraining Statistics:")
    logger.info(f"  Samples: {stats['n_samples']}")
    logger.info(f"  Features: {stats['n_features']}")
    logger.info(f"  Anomalies Detected: {stats['n_anomalies_detected']} ({stats['anomaly_rate']:.1%})")
    logger.info(f"  Mean Anomaly Score: {stats['mean_anomaly_score']:.4f}")
    logger.info(f"  Score Range: [{stats['min_anomaly_score']:.4f}, {stats['max_anomaly_score']:.4f}]")
    
    # Evaluate against true labels
    logger.info("\nEvaluating against synthetic anomaly labels...")
    predictions = detector.predict(X)
    predicted_anomalies = (predictions == -1).astype(int)
    
    from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score
    
    # Confusion matrix
    cm = confusion_matrix(true_labels, predicted_anomalies)
    logger.info(f"\nConfusion Matrix:")
    logger.info(f"  TN={cm[0,0]}, FP={cm[0,1]}")
    logger.info(f"  FN={cm[1,0]}, TP={cm[1,1]}")
    
    # Metrics
    precision = precision_score(true_labels, predicted_anomalies)
    recall = recall_score(true_labels, predicted_anomalies)
    f1 = f1_score(true_labels, predicted_anomalies)
    
    logger.info(f"\nPerformance Metrics:")
    logger.info(f"  Precision: {precision:.4f} ({precision:.1%})")
    logger.info(f"  Recall:    {recall:.4f} ({recall:.1%})")
    logger.info(f"  F1-Score:  {f1:.4f} ({f1:.1%})")
    
    # Classification report
    logger.info("\nClassification Report:")
    print(classification_report(true_labels, predicted_anomalies, target_names=['Normal', 'Anomaly']))
    
    # Get anomaly scores
    scores = detector.predict_proba(X)
    
    # Plot results
    logger.info("\nGenerating visualizations...")
    plot_anomaly_scores(scores, true_labels)
    
    # Calculate feature importance
    logger.info("\nCalculating feature importance...")
    importances = detector.get_feature_importance(X)
    
    logger.info("\nTop 10 Most Important Features:")
    sorted_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    for i, (feature, importance) in enumerate(sorted_features[:10], 1):
        logger.info(f"  {i}. {feature}: {importance:.4f}")
    
    plot_feature_importance(importances)
    
    # Save model
    model_path = "models/anomaly_detector_v1.pkl"
    logger.info(f"\nSaving model to {model_path}")
    detector.save(model_path)
    
    # Get file size
    model_size = Path(model_path).stat().st_size / (1024 * 1024)
    logger.info(f"Model size: {model_size:.2f} MB")
    
    # Test model loading
    logger.info("\nTesting model loading...")
    loaded_detector = SensorAnomalyDetector.load(model_path)
    
    # Test predictions
    test_samples = X[:5]
    test_labels = true_labels[:5]
    
    logger.info("\nSample predictions (loaded model):")
    for i in range(len(test_samples)):
        features_dict = {name: test_samples[i, j] for j, name in enumerate(feature_columns)}
        result = loaded_detector.detect_single(features_dict)
        
        logger.info(f"  Sample {i+1}: Actual={'Anomaly' if test_labels[i] == 1 else 'Normal'}, "
                   f"Predicted={'Anomaly' if result['is_anomaly'] else 'Normal'}, "
                   f"Score={result['anomaly_score']:.3f}, Severity={result['severity']}")
    
    # Test on original data (no injected anomalies)
    logger.info("\nTesting on original data (natural anomalies)...")
    X_original = detector.prepare_features(df, feature_columns)
    original_predictions = detector.predict(X_original)
    natural_anomalies = (original_predictions == -1).sum()
    
    logger.info(f"Natural anomalies detected: {natural_anomalies} ({natural_anomalies/len(df):.1%})")
    
    # Show examples of natural anomalies
    anomaly_mask = original_predictions == -1
    if anomaly_mask.sum() > 0:
        logger.info("\nExamples of naturally detected anomalies:")
        anomaly_df = df[anomaly_mask].head(5)
        for idx, row in anomaly_df.iterrows():
            logger.info(f"  Location: {row['location']}, Date: {row['date']}, "
                       f"Rainfall: {row['rainfall_mm']:.1f}mm, Temp: {row['temperature']:.1f}°C, "
                       f"Humidity: {row['humidity']}%")
    
    logger.info("\n" + "=" * 60)
    logger.info("ANOMALY DETECTOR TRAINING PIPELINE COMPLETE!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
