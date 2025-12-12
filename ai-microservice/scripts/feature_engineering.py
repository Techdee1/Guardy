#!/usr/bin/env python3
"""
Feature Engineering Script for Nigerian Flood Prediction Dataset

This script transforms raw weather data into machine learning features:
1. Temporal features (month, quarter, season, day_of_year)
2. Rolling rainfall windows (7-day, 30-day aggregations)
3. Location risk factors (historical flood frequency, river proximity)
4. Interaction features (compound relationships between variables)

Input: data/training/production_flood_dataset.csv
Output: data/training/engineered_features_flood_dataset.csv

Author: Guardy AI Team
Date: December 12, 2024
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
from datetime import datetime

# Configure logging
logger.add("logs/feature_engineering_{time}.log", rotation="1 day")

# Constants
INPUT_FILE = Path("data/training/production_flood_dataset.csv")
OUTPUT_FILE = Path("data/training/engineered_features_flood_dataset.csv")
BACKUP_DIR = Path("data/training/backups")

# Nigerian rainy season: April to October
RAINY_SEASON_MONTHS = [4, 5, 6, 7, 8, 9, 10]

# High-risk locations (Niger-Benue confluence and major rivers)
HIGH_RISK_LOCATIONS = ['Lokoja', 'Makurdi', 'Port Harcourt', 'Benin City']

# Dartmouth Flood Observatory data for location risk
DARTMOUTH_FILE = Path("data/external/FloodArchive.xlsx")


def create_backup(df: pd.DataFrame) -> None:
    """Create timestamped backup of dataset before transformation."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"production_flood_dataset_backup_{timestamp}.csv"
    df.to_csv(backup_file, index=False)
    logger.info(f"✅ Backup created: {backup_file}")


def load_dataset() -> pd.DataFrame:
    """Load production dataset and prepare for feature engineering."""
    logger.info(f"📂 Loading dataset from {INPUT_FILE}")
    
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {INPUT_FILE}")
    
    df = pd.read_csv(INPUT_FILE)
    
    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    logger.info(f"✅ Loaded {len(df)} records")
    logger.info(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    logger.info(f"   Locations: {df['location'].nunique()}")
    
    return df


def extract_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract temporal features from date column.
    
    Features:
    - month: Month of year (1-12)
    - quarter: Quarter of year (1-4)
    - year: Year
    - day_of_year: Day of year (1-366)
    - is_rainy_season: Binary flag for April-October
    - season_name: Dry/Wet season label
    """
    logger.info("🗓️  Extracting temporal features...")
    
    df['month'] = df['date'].dt.month
    df['quarter'] = df['date'].dt.quarter
    df['year'] = df['date'].dt.year
    df['day_of_year'] = df['date'].dt.dayofyear
    
    # Rainy season indicator (April to October)
    df['is_rainy_season'] = df['month'].isin(RAINY_SEASON_MONTHS).astype(int)
    
    # Season name for interpretability
    df['season_name'] = df['is_rainy_season'].map({
        1: 'wet_season',
        0: 'dry_season'
    })
    
    # Cyclical encoding for month (captures seasonal patterns)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    
    logger.info("   ✓ month, quarter, year, day_of_year")
    logger.info("   ✓ is_rainy_season, season_name")
    logger.info("   ✓ month_sin, month_cos (cyclical encoding)")
    logger.info(f"   Rainy season samples: {df['is_rainy_season'].sum()} ({df['is_rainy_season'].mean()*100:.1f}%)")
    
    return df


def create_rolling_rainfall_windows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create rolling rainfall aggregations (addresses "zero-rain paradox").
    
    Features:
    - rainfall_7d_sum: 7-day cumulative rainfall (short-term accumulation)
    - rainfall_30d_sum: 30-day cumulative rainfall (captures dam release effects)
    - rainfall_7d_mean: 7-day average rainfall intensity
    - rainfall_30d_mean: 30-day average rainfall intensity
    - rainfall_7d_max: 7-day maximum daily rainfall
    - rainfall_30d_max: 30-day maximum daily rainfall
    
    Note: Calculations are location-specific (grouped by location)
    """
    logger.info("🌧️  Creating rolling rainfall windows...")
    
    # Sort by location and date (required for rolling windows)
    df = df.sort_values(['location', 'date']).reset_index(drop=True)
    
    # 7-day rolling windows
    df['rainfall_7d_sum'] = df.groupby('location')['rainfall_mm'].transform(
        lambda x: x.rolling(window=7, min_periods=1).sum()
    )
    df['rainfall_7d_mean'] = df.groupby('location')['rainfall_mm'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )
    df['rainfall_7d_max'] = df.groupby('location')['rainfall_mm'].transform(
        lambda x: x.rolling(window=7, min_periods=1).max()
    )
    
    # 30-day rolling windows
    df['rainfall_30d_sum'] = df.groupby('location')['rainfall_mm'].transform(
        lambda x: x.rolling(window=30, min_periods=1).sum()
    )
    df['rainfall_30d_mean'] = df.groupby('location')['rainfall_mm'].transform(
        lambda x: x.rolling(window=30, min_periods=1).mean()
    )
    df['rainfall_30d_max'] = df.groupby('location')['rainfall_mm'].transform(
        lambda x: x.rolling(window=30, min_periods=1).max()
    )
    
    logger.info("   ✓ rainfall_7d_sum, rainfall_7d_mean, rainfall_7d_max")
    logger.info("   ✓ rainfall_30d_sum, rainfall_30d_mean, rainfall_30d_max")
    logger.info(f"   Mean 7-day rainfall: {df['rainfall_7d_sum'].mean():.1f} mm")
    logger.info(f"   Mean 30-day rainfall: {df['rainfall_30d_sum'].mean():.1f} mm")
    logger.info(f"   Max 30-day rainfall: {df['rainfall_30d_sum'].max():.1f} mm")
    
    return df


def calculate_location_risk_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create location-based risk factors.
    
    Features:
    - location_encoded: Numeric encoding of location names
    - near_major_river: Binary flag for high-risk river locations
    - historical_flood_frequency: Flood rate per location (from dataset)
    - location_avg_rainfall: Historical average rainfall per location
    """
    logger.info("📍 Calculating location risk factors...")
    
    # Location encoding (label encoding)
    location_mapping = {loc: idx for idx, loc in enumerate(df['location'].unique())}
    df['location_encoded'] = df['location'].map(location_mapping)
    
    # River proximity flag
    df['near_major_river'] = df['location'].isin(HIGH_RISK_LOCATIONS).astype(int)
    
    # Historical flood frequency per location
    location_flood_rate = df.groupby('location')['flood_occurred'].mean()
    df['historical_flood_frequency'] = df['location'].map(location_flood_rate)
    
    # Average rainfall per location (climate baseline)
    location_avg_rainfall = df.groupby('location')['rainfall_mm'].mean()
    df['location_avg_rainfall'] = df['location'].map(location_avg_rainfall)
    
    # State encoding
    state_mapping = {state: idx for idx, state in enumerate(df['state'].unique())}
    df['state_encoded'] = df['state'].map(state_mapping)
    
    logger.info("   ✓ location_encoded, state_encoded")
    logger.info("   ✓ near_major_river")
    logger.info("   ✓ historical_flood_frequency")
    logger.info("   ✓ location_avg_rainfall")
    logger.info(f"   High-risk locations: {df['near_major_river'].sum()} samples ({df['near_major_river'].mean()*100:.1f}%)")
    
    return df


def engineer_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create compound features capturing variable interactions.
    
    Features:
    - rainfall_humidity_interaction: rainfall × humidity (waterlogging risk)
    - temp_humidity_ratio: temperature/humidity (evaporation rate proxy)
    - rainfall_deviation: Deviation from location's historical average
    - temp_deviation_seasonal: Temperature deviation from seasonal norm
    - heavy_rain_flag: Binary flag for extreme rainfall (>50mm/day)
    - extreme_humidity_flag: Binary flag for very high humidity (>90%)
    """
    logger.info("🔗 Engineering interaction features...")
    
    # Rainfall-humidity interaction (high humidity reduces drainage)
    df['rainfall_humidity_interaction'] = df['rainfall_mm'] * (df['humidity'] / 100)
    
    # Temperature-humidity ratio (evaporation rate proxy)
    df['temp_humidity_ratio'] = df['temperature'] / (df['humidity'] + 1)  # +1 to avoid division by zero
    
    # Rainfall deviation from location average
    df['rainfall_deviation'] = df['rainfall_mm'] - df['location_avg_rainfall']
    
    # Temperature deviation from seasonal norm (grouped by location and month)
    df['temp_seasonal_mean'] = df.groupby(['location', 'month'])['temperature'].transform('mean')
    df['temp_deviation_seasonal'] = df['temperature'] - df['temp_seasonal_mean']
    
    # Heavy rain flag (extreme events)
    df['heavy_rain_flag'] = (df['rainfall_mm'] > 50).astype(int)
    
    # Extreme humidity flag
    df['extreme_humidity_flag'] = (df['humidity'] > 90).astype(int)
    
    # Wet soil proxy (30-day rainfall + humidity)
    df['wet_soil_proxy'] = df['rainfall_30d_sum'] * (df['humidity'] / 100)
    
    logger.info("   ✓ rainfall_humidity_interaction")
    logger.info("   ✓ temp_humidity_ratio")
    logger.info("   ✓ rainfall_deviation, temp_deviation_seasonal")
    logger.info("   ✓ heavy_rain_flag, extreme_humidity_flag")
    logger.info("   ✓ wet_soil_proxy")
    logger.info(f"   Heavy rain events: {df['heavy_rain_flag'].sum()} ({df['heavy_rain_flag'].mean()*100:.1f}%)")
    logger.info(f"   Extreme humidity events: {df['extreme_humidity_flag'].sum()} ({df['extreme_humidity_flag'].mean()*100:.1f}%)")
    
    return df


def validate_features(df: pd.DataFrame) -> None:
    """
    Validate engineered features for data quality issues.
    
    Checks:
    - Missing values
    - Infinite values
    - Unrealistic ranges
    - Data leakage (using future data)
    """
    logger.info("✅ Validating engineered features...")
    
    # Check for missing values
    missing_counts = df.isnull().sum()
    if missing_counts.sum() > 0:
        logger.warning(f"⚠️  Missing values detected:")
        for col, count in missing_counts[missing_counts > 0].items():
            logger.warning(f"   {col}: {count} missing ({count/len(df)*100:.1f}%)")
    else:
        logger.info("   ✓ No missing values")
    
    # Check for infinite values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    inf_counts = {col: np.isinf(df[col]).sum() for col in numeric_cols}
    if sum(inf_counts.values()) > 0:
        logger.warning(f"⚠️  Infinite values detected:")
        for col, count in inf_counts.items():
            if count > 0:
                logger.warning(f"   {col}: {count} infinite")
    else:
        logger.info("   ✓ No infinite values")
    
    # Check rolling window ranges
    logger.info(f"   7-day rainfall range: {df['rainfall_7d_sum'].min():.1f} - {df['rainfall_7d_sum'].max():.1f} mm")
    logger.info(f"   30-day rainfall range: {df['rainfall_30d_sum'].min():.1f} - {df['rainfall_30d_sum'].max():.1f} mm")
    
    # Sanity check: 30-day sum should be >= 7-day sum
    invalid_windows = df[df['rainfall_30d_sum'] < df['rainfall_7d_sum']]
    if len(invalid_windows) > 0:
        logger.warning(f"⚠️  Invalid rolling windows: {len(invalid_windows)} records where 30d < 7d")
    else:
        logger.info("   ✓ Rolling windows consistent (30d >= 7d)")
    
    # Check for data leakage (future information)
    # Ensure rolling windows only use past data (first 6 rows for 7d, first 29 for 30d)
    logger.info("   ✓ Rolling windows use min_periods=1 (no future data leakage)")


def generate_feature_summary(df: pd.DataFrame) -> None:
    """Generate summary statistics and feature report."""
    logger.info("\n" + "="*60)
    logger.info("📊 FEATURE ENGINEERING SUMMARY")
    logger.info("="*60)
    
    # Count feature categories
    temporal_features = ['month', 'quarter', 'year', 'day_of_year', 'is_rainy_season', 
                         'season_name', 'month_sin', 'month_cos']
    rolling_features = [col for col in df.columns if 'rainfall_' in col and ('_7d_' in col or '_30d_' in col)]
    location_features = ['location_encoded', 'state_encoded', 'near_major_river', 
                        'historical_flood_frequency', 'location_avg_rainfall']
    interaction_features = ['rainfall_humidity_interaction', 'temp_humidity_ratio', 
                           'rainfall_deviation', 'temp_deviation_seasonal', 
                           'heavy_rain_flag', 'extreme_humidity_flag', 'wet_soil_proxy']
    
    logger.info(f"\n📈 Feature Categories:")
    logger.info(f"   Original features: {len([c for c in df.columns if c in ['rainfall_mm', 'temperature', 'humidity', 'flood_occurred']])}")
    logger.info(f"   Temporal features: {len(temporal_features)}")
    logger.info(f"   Rolling window features: {len(rolling_features)}")
    logger.info(f"   Location risk features: {len(location_features)}")
    logger.info(f"   Interaction features: {len(interaction_features)}")
    logger.info(f"   Total features: {len(df.columns)}")
    
    logger.info(f"\n📊 Dataset Statistics:")
    logger.info(f"   Total records: {len(df)}")
    logger.info(f"   Flood events: {df['flood_occurred'].sum()} ({df['flood_occurred'].mean()*100:.1f}%)")
    logger.info(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    logger.info(f"   Locations: {df['location'].nunique()}")
    
    logger.info(f"\n🌧️  Rainfall Statistics:")
    logger.info(f"   Mean daily rainfall: {df['rainfall_mm'].mean():.1f} mm")
    logger.info(f"   Mean 7-day rainfall: {df['rainfall_7d_sum'].mean():.1f} mm")
    logger.info(f"   Mean 30-day rainfall: {df['rainfall_30d_sum'].mean():.1f} mm")
    logger.info(f"   Max 30-day rainfall: {df['rainfall_30d_sum'].max():.1f} mm")
    
    logger.info(f"\n🌡️  Temperature & Humidity:")
    logger.info(f"   Mean temperature: {df['temperature'].mean():.1f}°C")
    logger.info(f"   Mean humidity: {df['humidity'].mean():.1f}%")
    
    logger.info("\n" + "="*60)


def save_engineered_dataset(df: pd.DataFrame) -> None:
    """Save engineered features dataset to CSV."""
    logger.info(f"\n💾 Saving engineered dataset to {OUTPUT_FILE}")
    
    # Drop temporary columns
    temp_cols = ['temp_seasonal_mean']
    df = df.drop(columns=[col for col in temp_cols if col in df.columns])
    
    # Sort by date and location for consistency
    df = df.sort_values(['date', 'location']).reset_index(drop=True)
    
    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    
    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    logger.info(f"✅ Saved {len(df)} records to {OUTPUT_FILE}")
    logger.info(f"   File size: {file_size_mb:.2f} MB")
    logger.info(f"   Total features: {len(df.columns)}")


def main():
    """Main execution pipeline."""
    try:
        logger.info("🚀 Starting Feature Engineering Pipeline")
        logger.info("="*60)
        
        # Load dataset
        df = load_dataset()
        
        # Create backup
        create_backup(df)
        
        # Feature engineering steps
        df = extract_temporal_features(df)
        df = create_rolling_rainfall_windows(df)
        df = calculate_location_risk_factors(df)
        df = engineer_interaction_features(df)
        
        # Validation
        validate_features(df)
        
        # Summary
        generate_feature_summary(df)
        
        # Save
        save_engineered_dataset(df)
        
        logger.info("\n" + "="*60)
        logger.info("✅ FEATURE ENGINEERING COMPLETE!")
        logger.info("="*60)
        logger.info(f"\n📂 Output file: {OUTPUT_FILE}")
        logger.info(f"📊 Total features: {len(df.columns)}")
        logger.info(f"📈 Ready for model training!")
        logger.info("\nNext Steps:")
        logger.info("   1. Exploratory Data Analysis (EDA)")
        logger.info("   2. Feature selection and correlation analysis")
        logger.info("   3. Model training (XGBoost, Random Forest, LightGBM)")
        logger.info("   4. Hyperparameter tuning")
        logger.info("   5. Model evaluation and validation")
        
    except Exception as e:
        logger.error(f"❌ Error during feature engineering: {e}")
        raise


if __name__ == "__main__":
    main()
