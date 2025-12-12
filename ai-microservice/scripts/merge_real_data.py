#!/usr/bin/env python3
"""
Merge downloaded real data sources with existing flood events dataset.

This script:
1. Loads the current dataset (with simulated weather)
2. Loads downloaded CHIRPS rainfall data
3. Loads downloaded ERA5 climate data
4. Merges real weather data to replace simulated values
5. Validates and saves enhanced dataset

Usage:
    python scripts/merge_real_data.py
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


class DataMerger:
    """Merge real data sources with existing flood events."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / 'data'
        
    def load_current_dataset(self) -> pd.DataFrame:
        """Load the current flood events dataset."""
        current_file = self.data_dir / 'training' / 'real_flood_events.csv'
        
        if not current_file.exists():
            logger.error(f"Current dataset not found: {current_file}")
            return pd.DataFrame()
        
        df = pd.read_csv(current_file)
        logger.info(f"Loaded current dataset: {len(df)} records")
        logger.info(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        logger.info(f"  Locations: {df['location'].nunique()}")
        
        return df
    
    def load_chirps_data(self) -> pd.DataFrame:
        """Load downloaded CHIRPS rainfall data."""
        chirps_file = self.data_dir / 'external' / 'chirps_nigeria.csv'
        
        if not chirps_file.exists():
            logger.warning(f"CHIRPS data not found: {chirps_file}")
            logger.warning("Run: python scripts/download_chirps.py --start-year 2010 --end-year 2024")
            return pd.DataFrame()
        
        df = pd.read_csv(chirps_file)
        logger.info(f"Loaded CHIRPS data: {len(df)} records")
        
        return df
    
    def load_era5_data(self) -> pd.DataFrame:
        """Load downloaded ERA5 climate data."""
        era5_file = self.data_dir / 'external' / 'era5_nigeria.csv'
        
        if not era5_file.exists():
            logger.warning(f"ERA5 data not found: {era5_file}")
            logger.warning("Run: python scripts/download_era5.py --start-year 2010 --end-year 2024")
            return pd.DataFrame()
        
        df = pd.read_csv(era5_file)
        logger.info(f"Loaded ERA5 data: {len(df)} records")
        
        return df
    
    def merge_rainfall_data(
        self,
        current: pd.DataFrame,
        chirps: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge CHIRPS rainfall data."""
        if chirps.empty:
            logger.warning("No CHIRPS data to merge")
            return current
        
        logger.info("Merging CHIRPS rainfall data...")
        
        # Prepare CHIRPS data
        chirps_clean = chirps[['date', 'location', 'rainfall_mm']].copy()
        chirps_clean.rename(columns={'rainfall_mm': 'chirps_rainfall'}, inplace=True)
        
        # Merge with current data
        merged = current.merge(
            chirps_clean,
            on=['date', 'location'],
            how='left'
        )
        
        # Replace simulated rainfall with real CHIRPS data where available
        merged['rainfall_source'] = 'simulated'
        mask = merged['chirps_rainfall'].notna()
        merged.loc[mask, 'rainfall_mm'] = merged.loc[mask, 'chirps_rainfall']
        merged.loc[mask, 'rainfall_source'] = 'CHIRPS'
        
        # Drop temporary column
        merged.drop(columns=['chirps_rainfall'], inplace=True)
        
        real_count = (merged['rainfall_source'] == 'CHIRPS').sum()
        logger.success(f"Replaced {real_count} records with real CHIRPS rainfall")
        
        return merged
    
    def merge_climate_data(
        self,
        current: pd.DataFrame,
        era5: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge ERA5 temperature and humidity data."""
        if era5.empty:
            logger.warning("No ERA5 data to merge")
            return current
        
        logger.info("Merging ERA5 climate data...")
        
        # Prepare ERA5 data
        era5_clean = era5[['date', 'location', 'temperature', 'humidity']].copy()
        era5_clean.rename(columns={
            'temperature': 'era5_temperature',
            'humidity': 'era5_humidity'
        }, inplace=True)
        
        # Merge with current data
        merged = current.merge(
            era5_clean,
            on=['date', 'location'],
            how='left'
        )
        
        # Replace simulated climate data with real ERA5 data
        if 'temperature' in merged.columns:
            mask = merged['era5_temperature'].notna()
            merged.loc[mask, 'temperature'] = merged.loc[mask, 'era5_temperature']
            temp_count = mask.sum()
            logger.success(f"Replaced {temp_count} temperature records with ERA5 data")
        
        if 'humidity' in merged.columns:
            mask = merged['era5_humidity'].notna()
            merged.loc[mask, 'humidity'] = merged.loc[mask, 'era5_humidity']
            humid_count = mask.sum()
            logger.success(f"Replaced {humid_count} humidity records with ERA5 data")
        
        # Drop temporary columns
        merged.drop(columns=['era5_temperature', 'era5_humidity'], inplace=True, errors='ignore')
        
        return merged
    
    def validate_dataset(self, df: pd.DataFrame) -> bool:
        """Validate the merged dataset."""
        logger.info("Validating merged dataset...")
        
        issues = []
        
        # Check for missing values
        missing = df.isnull().sum()
        critical_cols = ['date', 'location', 'latitude', 'longitude', 
                        'flood_occurred', 'rainfall_mm']
        
        for col in critical_cols:
            if col in missing and missing[col] > 0:
                issues.append(f"Missing values in {col}: {missing[col]}")
        
        # Check data ranges
        if 'rainfall_mm' in df.columns:
            if (df['rainfall_mm'] < 0).any():
                issues.append("Negative rainfall values found")
            if (df['rainfall_mm'] > 1000).any():
                logger.warning("Very high rainfall values (>1000mm) - verify these are correct")
        
        if 'temperature' in df.columns:
            if (df['temperature'] < 0).any() or (df['temperature'] > 50).any():
                issues.append("Temperature values out of expected range (0-50°C)")
        
        if 'humidity' in df.columns:
            if (df['humidity'] < 0).any() or (df['humidity'] > 100).any():
                issues.append("Humidity values out of valid range (0-100%)")
        
        # Check date format
        try:
            pd.to_datetime(df['date'])
        except Exception:
            issues.append("Invalid date format")
        
        # Report issues
        if issues:
            logger.warning("Validation issues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")
            return False
        else:
            logger.success("Validation passed!")
            return True
    
    def generate_statistics(self, df: pd.DataFrame):
        """Generate statistics for the enhanced dataset."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("ENHANCED DATASET STATISTICS")
        logger.info("=" * 60)
        
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
            logger.info(f"  Min: {df['rainfall_mm'].min():.1f}")
            logger.info(f"  Max: {df['rainfall_mm'].max():.1f}")
        
        if 'temperature' in df.columns:
            logger.info(f"\nTemperature (°C):")
            logger.info(f"  Mean: {df['temperature'].mean():.1f}")
            logger.info(f"  Min: {df['temperature'].min():.1f}")
            logger.info(f"  Max: {df['temperature'].max():.1f}")
        
        if 'humidity' in df.columns:
            logger.info(f"\nHumidity (%):")
            logger.info(f"  Mean: {df['humidity'].mean():.1f}")
            logger.info(f"  Min: {df['humidity'].min():.1f}")
            logger.info(f"  Max: {df['humidity'].max():.1f}")
        
        # Data source breakdown
        if 'rainfall_source' in df.columns:
            logger.info(f"\nData Sources:")
            source_counts = df['rainfall_source'].value_counts()
            for source, count in source_counts.items():
                logger.info(f"  {source}: {count} ({count/len(df)*100:.1f}%)")
        
        logger.info("=" * 60)
    
    def merge_all(self) -> pd.DataFrame:
        """Main merge workflow."""
        # Load all datasets
        current = self.load_current_dataset()
        if current.empty:
            logger.error("Cannot proceed without current dataset")
            return pd.DataFrame()
        
        chirps = self.load_chirps_data()
        era5 = self.load_era5_data()
        
        if chirps.empty and era5.empty:
            logger.error("No real data sources available")
            logger.error("Please download data using:")
            logger.error("  python scripts/download_chirps.py --start-year 2010 --end-year 2024")
            logger.error("  python scripts/download_era5.py --start-year 2010 --end-year 2024")
            return pd.DataFrame()
        
        # Merge datasets
        enhanced = current.copy()
        
        if not chirps.empty:
            enhanced = self.merge_rainfall_data(enhanced, chirps)
        
        if not era5.empty:
            enhanced = self.merge_climate_data(enhanced, era5)
        
        # Validate
        self.validate_dataset(enhanced)
        
        # Generate statistics
        self.generate_statistics(enhanced)
        
        return enhanced


def main():
    """Main entry point."""
    logger.info("Starting data merge process...")
    
    merger = DataMerger()
    enhanced_df = merger.merge_all()
    
    if enhanced_df.empty:
        logger.error("Merge failed")
        return 1
    
    # Save enhanced dataset
    output_dir = merger.data_dir / 'training'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup original file
    original_file = output_dir / 'real_flood_events.csv'
    backup_file = output_dir / f'real_flood_events_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    if original_file.exists():
        import shutil
        shutil.copy2(original_file, backup_file)
        logger.info(f"Backed up original to: {backup_file.name}")
    
    # Save enhanced dataset
    output_file = output_dir / 'enhanced_flood_events.csv'
    enhanced_df.to_csv(output_file, index=False)
    logger.success(f"Saved enhanced dataset to: {output_file}")
    
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Review the enhanced dataset")
    logger.info("2. If satisfied, rename to real_flood_events.csv")
    logger.info("3. Proceed with feature engineering: Phase 3.2")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
