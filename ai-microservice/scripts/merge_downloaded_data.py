#!/usr/bin/env python3
"""
Merge downloaded CHIRPS rainfall and Dartmouth flood data with existing dataset.

Usage:
    python scripts/merge_downloaded_data.py
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")


def load_chirps_data():
    """Load all downloaded CHIRPS CSV files."""
    data_dir = Path('data/external')
    chirps_files = list(data_dir.glob('chirps_*.csv'))
    
    if not chirps_files:
        logger.warning("No CHIRPS files found")
        return pd.DataFrame()
    
    logger.info(f"Found {len(chirps_files)} CHIRPS files")
    
    all_data = []
    for file in chirps_files:
        try:
            df = pd.read_csv(file)
            all_data.append(df)
            logger.info(f"  Loaded {file.name}: {len(df)} records")
        except Exception as e:
            logger.error(f"  Failed to load {file.name}: {e}")
    
    if not all_data:
        return pd.DataFrame()
    
    combined = pd.concat(all_data, ignore_index=True)
    logger.success(f"Combined CHIRPS data: {len(combined)} total records")
    
    return combined


def load_dartmouth_data():
    """Load Dartmouth Flood Archive Excel file."""
    dartmouth_file = Path('data/training/FloodArchive.xlsx')
    
    if not dartmouth_file.exists():
        logger.warning(f"Dartmouth file not found: {dartmouth_file}")
        return pd.DataFrame()
    
    try:
        # Read Excel file
        df = pd.read_excel(dartmouth_file)
        logger.info(f"Loaded Dartmouth data: {len(df)} records")
        logger.info(f"Columns: {', '.join(df.columns.tolist())}")
        
        # Filter for Nigeria
        if 'Country' in df.columns:
            nigeria_data = df[df['Country'].str.contains('Nigeria', case=False, na=False)]
            logger.info(f"Nigerian flood events: {len(nigeria_data)}")
            return nigeria_data
        else:
            logger.warning("'Country' column not found, returning all data")
            return df
            
    except Exception as e:
        logger.error(f"Failed to load Dartmouth file: {e}")
        return pd.DataFrame()


def load_current_dataset():
    """Load existing flood events dataset."""
    current_file = Path('data/training/real_flood_events.csv')
    
    if not current_file.exists():
        logger.error(f"Current dataset not found: {current_file}")
        return pd.DataFrame()
    
    df = pd.read_csv(current_file)
    logger.info(f"Loaded current dataset: {len(df)} records")
    
    return df


def merge_chirps_rainfall(current_df, chirps_df):
    """Merge CHIRPS rainfall data."""
    if chirps_df.empty:
        logger.warning("No CHIRPS data to merge")
        return current_df
    
    logger.info("Merging CHIRPS rainfall data...")
    
    # Prepare CHIRPS data for merge
    chirps_clean = chirps_df[['date', 'location', 'rainfall_mm']].copy()
    chirps_clean.rename(columns={'rainfall_mm': 'chirps_rainfall'}, inplace=True)
    
    # Merge
    merged = current_df.merge(
        chirps_clean,
        on=['date', 'location'],
        how='left'
    )
    
    # Replace simulated rainfall with real CHIRPS data
    merged['rainfall_source'] = 'simulated'
    mask = merged['chirps_rainfall'].notna()
    
    if mask.sum() > 0:
        merged.loc[mask, 'rainfall_mm'] = merged.loc[mask, 'chirps_rainfall']
        merged.loc[mask, 'rainfall_source'] = 'CHIRPS-2.0'
        logger.success(f"Replaced {mask.sum()} records with real CHIRPS rainfall")
    
    # Drop temporary column
    merged.drop(columns=['chirps_rainfall'], inplace=True)
    
    return merged


def add_dartmouth_events(current_df, dartmouth_df):
    """Add Dartmouth flood events that we don't have."""
    if dartmouth_df.empty:
        logger.warning("No Dartmouth data to add")
        return current_df
    
    logger.info("Processing Dartmouth flood events...")
    
    # Show sample of Dartmouth data
    logger.info(f"Dartmouth columns: {dartmouth_df.columns.tolist()}")
    if len(dartmouth_df) > 0:
        logger.info(f"Sample record:\n{dartmouth_df.iloc[0]}")
    
    # For now, just log the events for manual review
    logger.info(f"\nFound {len(dartmouth_df)} Nigerian flood events in Dartmouth archive")
    logger.info("These can be used to validate/enhance our dataset")
    
    return current_df


def generate_statistics(df):
    """Generate statistics for the dataset."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("ENHANCED DATASET STATISTICS")
    logger.info("=" * 70)
    
    logger.info(f"Total records: {len(df)}")
    logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
    logger.info(f"Locations: {df['location'].nunique()}")
    
    if 'flood_occurred' in df.columns:
        flood_count = (df['flood_occurred'] == 1).sum()
        logger.info(f"Flood events: {flood_count} ({flood_count/len(df)*100:.1f}%)")
        logger.info(f"Non-flood: {len(df)-flood_count} ({(len(df)-flood_count)/len(df)*100:.1f}%)")
    
    if 'rainfall_mm' in df.columns:
        logger.info(f"\nRainfall (mm):")
        logger.info(f"  Mean: {df['rainfall_mm'].mean():.1f}")
        logger.info(f"  Median: {df['rainfall_mm'].median():.1f}")
        logger.info(f"  Max: {df['rainfall_mm'].max():.1f}")
    
    if 'rainfall_source' in df.columns:
        logger.info(f"\nData Sources:")
        for source, count in df['rainfall_source'].value_counts().items():
            logger.info(f"  {source}: {count} ({count/len(df)*100:.1f}%)")
    
    logger.info("=" * 70)


def main():
    """Main merge workflow."""
    logger.info("Starting data merge process...")
    logger.info("")
    
    # Load all data
    current_df = load_current_dataset()
    if current_df.empty:
        logger.error("Cannot proceed without current dataset")
        return 1
    
    chirps_df = load_chirps_data()
    dartmouth_df = load_dartmouth_data()
    
    if chirps_df.empty and dartmouth_df.empty:
        logger.error("No new data to merge")
        return 1
    
    # Merge CHIRPS data
    enhanced_df = current_df.copy()
    if not chirps_df.empty:
        enhanced_df = merge_chirps_rainfall(enhanced_df, chirps_df)
    
    # Process Dartmouth data
    if not dartmouth_df.empty:
        enhanced_df = add_dartmouth_events(enhanced_df, dartmouth_df)
    
    # Generate statistics
    generate_statistics(enhanced_df)
    
    # Backup original
    backup_file = Path(f'data/training/real_flood_events_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    current_df.to_csv(backup_file, index=False)
    logger.info(f"\nBacked up original to: {backup_file.name}")
    
    # Save enhanced dataset
    output_file = Path('data/training/enhanced_flood_events.csv')
    enhanced_df.to_csv(output_file, index=False)
    logger.success(f"Saved enhanced dataset to: {output_file}")
    
    logger.info("")
    logger.info("✅ Data merge complete!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Review: data/training/enhanced_flood_events.csv")
    logger.info("2. Proceed with Phase 3.2: Feature Engineering")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
