#!/usr/bin/env python3
"""
Train Flood Risk Scoring Model

This script trains the FloodRiskScorer ensemble model on the engineered features dataset.

Usage:
    python scripts/train_risk_scorer.py

Author: Guardy AI Team
Date: December 12, 2024
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from loguru import logger

from app.ml.flood_risk_scorer import FloodRiskScorer

# Configure logging
logger.add("logs/train_risk_scorer_{time}.log", rotation="1 day")

# Paths
DATA_FILE = Path("data/training/engineered_features_flood_dataset.csv")
MODEL_FILE = Path("models/flood_risk_scorer_v1.pkl")
FIGURES_DIR = Path("figures")


def plot_confusion_matrix(cm, save_path):
    """Plot confusion matrix heatmap."""
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=['No Flood', 'Flood'],
        yticklabels=['No Flood', 'Flood']
    )
    plt.title('Confusion Matrix (Ensemble Model)')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    logger.info(f"✅ Confusion matrix saved to {save_path}")
    plt.close()


def plot_feature_importance(feature_importance, top_n=15, save_path=None):
    """Plot top N feature importances."""
    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:top_n]
    features, importances = zip(*top_features)
    
    plt.figure(figsize=(10, 8))
    plt.barh(range(len(features)), importances, color='steelblue')
    plt.yticks(range(len(features)), features)
    plt.xlabel('Feature Importance')
    plt.title(f'Top {top_n} Most Important Features')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    logger.info(f"✅ Feature importance plot saved to {save_path}")
    plt.close()


def main():
    """Main training pipeline."""
    logger.info("="*70)
    logger.info("FLOOD RISK SCORER TRAINING PIPELINE")
    logger.info("="*70)
    
    # Create directories
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load dataset
    logger.info(f"\n📂 Loading dataset from {DATA_FILE}")
    if not DATA_FILE.exists():
        logger.error(f"❌ Dataset not found: {DATA_FILE}")
        logger.error("   Run feature engineering first: python scripts/feature_engineering.py")
        return
    
    df = pd.read_csv(DATA_FILE)
    logger.info(f"✅ Loaded {len(df)} records")
    logger.info(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    logger.info(f"   Columns: {len(df.columns)}")
    
    # Initialize model
    logger.info("\n🤖 Initializing FloodRiskScorer...")
    model = FloodRiskScorer(
        use_scaling=False,  # Tree-based models don't need scaling
        rf_params={
            'n_estimators': 200,
            'max_depth': 15,
            'min_samples_split': 10,
            'min_samples_leaf': 4,
            'max_features': 'sqrt',
            'random_state': 42,
            'n_jobs': -1,
            'class_weight': 'balanced'
        },
        gb_params={
            'n_estimators': 200,
            'learning_rate': 0.1,
            'max_depth': 7,
            'min_samples_split': 10,
            'min_samples_leaf': 4,
            'subsample': 0.8,
            'random_state': 42
        }
    )
    
    # Train model
    logger.info("\n🚀 Starting model training...")
    results = model.train(
        df=df,
        target_col='flood_occurred',
        test_size=0.2,
        perform_cv=False  # Skip CV for speed (can enable later)
    )
    
    # Display final results
    logger.info("\n" + "="*70)
    logger.info("TRAINING RESULTS SUMMARY")
    logger.info("="*70)
    
    metrics = results['metrics']['ensemble']
    logger.info(f"\n📊 Ensemble Model Performance:")
    logger.info(f"   Accuracy:  {metrics['test_accuracy']:.4f} ({metrics['test_accuracy']*100:.2f}%)")
    logger.info(f"   Precision: {metrics['precision']:.4f}")
    logger.info(f"   Recall:    {metrics['recall']:.4f}")
    logger.info(f"   F1-Score:  {metrics['f1_score']:.4f}")
    logger.info(f"   ROC-AUC:   {metrics['roc_auc']:.4f}")
    
    # Check if target accuracy achieved
    target_accuracy = 0.85
    if metrics['test_accuracy'] >= target_accuracy:
        logger.info(f"\n✅ TARGET ACHIEVED! Accuracy {metrics['test_accuracy']:.4f} >= {target_accuracy}")
    else:
        logger.warning(f"\n⚠️  Target accuracy {target_accuracy} not reached (got {metrics['test_accuracy']:.4f})")
        logger.warning("   Consider: more data, feature engineering, hyperparameter tuning")
    
    # Visualizations
    logger.info("\n📊 Creating visualizations...")
    
    # Feature importance plot
    plot_feature_importance(
        model.feature_importance,
        top_n=15,
        save_path=FIGURES_DIR / "feature_importance.png"
    )
    
    # Save model
    logger.info(f"\n💾 Saving trained model to {MODEL_FILE}")
    model.save(MODEL_FILE)
    
    model_size_mb = MODEL_FILE.stat().st_size / (1024 * 1024)
    logger.info(f"   Model size: {model_size_mb:.2f} MB")
    
    # Test model loading
    logger.info("\n🔄 Testing model loading...")
    loaded_model = FloodRiskScorer.load(MODEL_FILE)
    logger.info("✅ Model successfully loaded!")
    
    # Quick prediction test
    logger.info("\n🧪 Testing predictions on sample data...")
    test_sample = df.sample(5)
    predictions = loaded_model.predict_risk_score(test_sample)
    
    logger.info("\nSample Predictions:")
    for i in range(len(test_sample)):
        actual = test_sample.iloc[i]['flood_occurred']
        pred = predictions['predictions'][i]
        prob = predictions['probabilities'][i]
        risk_score = predictions['risk_scores'][i]
        risk_cat = predictions['risk_categories'][i]
        confidence = predictions['confidence_levels'][i]
        
        match_emoji = "✅" if actual == pred else "❌"
        logger.info(
            f"  {match_emoji} Sample {i+1}: "
            f"Actual={actual}, Predicted={pred}, "
            f"Probability={prob:.3f}, Risk Score={risk_score}, "
            f"Category={risk_cat}, Confidence={confidence}"
        )
    
    # Final summary
    logger.info("\n" + "="*70)
    logger.info("✅ TRAINING PIPELINE COMPLETE!")
    logger.info("="*70)
    logger.info(f"\n📁 Outputs:")
    logger.info(f"   Model: {MODEL_FILE}")
    logger.info(f"   Feature importance plot: {FIGURES_DIR / 'feature_importance.png'}")
    logger.info(f"\n🎯 Next Steps:")
    logger.info("   1. Review feature importance rankings")
    logger.info("   2. Test model on new data")
    logger.info("   3. Integrate with FastAPI endpoints")
    logger.info("   4. Consider hyperparameter tuning if accuracy < 85%")
    logger.info("   5. Train nowcasting model (Task 2)")


if __name__ == "__main__":
    main()
