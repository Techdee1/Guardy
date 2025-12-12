#!/usr/bin/env python3
"""
Hydrate dataset with real temperature and humidity from Open-Meteo API.

Open-Meteo provides free access to ERA5 historical weather data without requiring
an account. This script replaces simulated temperature/humidity with real values.

Usage:
    python scripts/hydrate_with_openmeteo.py
"""

import sys
from pathlib import Path
from datetime import datetime
import time

import pandas as pd
import numpy as np
import requests
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")


class OpenMeteoHydrator:
    """Hydrate dataset with real weather data from Open-Meteo API."""
    
    API_URL = "https://archive-api.open-meteo.com/v1/archive"
    
    def __init__(self, input_file: str, output_file: str):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.session = requests.Session()
        
    def load_dataset(self) -> pd.DataFrame:
        """Load the current dataset."""
        if not self.input_file.exists():
            logger.error(f"Input file not found: {self.input_file}")
            return pd.DataFrame()
        
        df = pd.read_csv(self.input_file)
        logger.info(f"Loaded dataset: {len(df)} records")
        logger.info(f"Columns: {', '.join(df.columns)}")
        
        return df
    
    def fetch_weather(self, date: str, lat: float, lon: float) -> dict:
        """
        Fetch real weather data from Open-Meteo API.
        
        Args:
            date: Date in YYYY-MM-DD format
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with temperature, humidity, and other weather data
        """
        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': date,
            'end_date': date,
            'daily': [
                'temperature_2m_mean',
                'temperature_2m_max',
                'temperature_2m_min',
                'relative_humidity_2m_mean',
                'precipitation_sum'
            ],
            'timezone': 'Africa/Lagos'
        }
        
        try:
            response = self.session.get(self.API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'daily' in data and data['daily']:
                daily = data['daily']
                return {
                    'real_temperature': daily['temperature_2m_mean'][0] if daily['temperature_2m_mean'] else None,
                    'real_temp_max': daily['temperature_2m_max'][0] if daily['temperature_2m_max'] else None,
                    'real_temp_min': daily['temperature_2m_min'][0] if daily['temperature_2m_min'] else None,
                    'real_humidity': daily['relative_humidity_2m_mean'][0] if daily['relative_humidity_2m_mean'] else None,
                    'real_precipitation': daily['precipitation_sum'][0] if daily['precipitation_sum'] else None
                }
            else:
                return {
                    'real_temperature': None,
                    'real_temp_max': None,
                    'real_temp_min': None,
                    'real_humidity': None,
                    'real_precipitation': None
                }
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"API request failed for {date} at ({lat}, {lon}): {e}")
            return {
                'real_temperature': None,
                'real_temp_max': None,
                'real_temp_min': None,
                'real_humidity': None,
                'real_precipitation': None
            }
    
    def hydrate_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Hydrate dataset with real weather data.
        
        Fetches weather data for unique date/location combinations to avoid
        redundant API calls.
        """
        logger.info("Starting dataset hydration with Open-Meteo ERA5 data...")
        logger.info("This will take 10-15 minutes for 663 records...")
        
        # Get unique date/location combinations
        unique_combos = df[['date', 'latitude', 'longitude', 'location']].drop_duplicates()
        logger.info(f"Found {len(unique_combos)} unique date/location combinations")
        
        # Fetch weather data for each unique combination
        weather_cache = {}
        failed_requests = 0
        
        for idx, row in unique_combos.iterrows():
            key = (row['date'], row['latitude'], row['longitude'])
            
            # Progress indicator
            if (idx + 1) % 50 == 0:
                logger.info(f"Progress: {idx + 1}/{len(unique_combos)} ({(idx+1)/len(unique_combos)*100:.1f}%)")
            
            # Fetch weather
            weather = self.fetch_weather(row['date'], row['latitude'], row['longitude'])
            
            if weather['real_temperature'] is None:
                failed_requests += 1
            
            weather_cache[key] = weather
            
            # Rate limiting - be nice to the free API
            time.sleep(0.1)  # 100ms delay between requests
        
        logger.info(f"Fetched weather for {len(weather_cache)} combinations")
        if failed_requests > 0:
            logger.warning(f"Failed to fetch data for {failed_requests} combinations")
        
        # Apply weather data to dataframe
        def apply_weather(row):
            key = (row['date'], row['latitude'], row['longitude'])
            weather = weather_cache.get(key, {})
            
            return pd.Series({
                'real_temperature': weather.get('real_temperature'),
                'real_humidity': weather.get('real_humidity'),
                'openmeteo_precipitation': weather.get('real_precipitation')
            })
        
        logger.info("Applying weather data to dataset...")
        weather_df = df.apply(apply_weather, axis=1)
        
        # Merge with original dataframe
        df_hydrated = pd.concat([df, weather_df], axis=1)
        
        # Replace simulated values with real values where available
        df_hydrated['temperature_original'] = df_hydrated['temperature']
        df_hydrated['humidity_original'] = df_hydrated['humidity']
        
        mask_temp = df_hydrated['real_temperature'].notna()
        mask_humid = df_hydrated['real_humidity'].notna()
        
        df_hydrated.loc[mask_temp, 'temperature'] = df_hydrated.loc[mask_temp, 'real_temperature']
        df_hydrated.loc[mask_humid, 'humidity'] = df_hydrated.loc[mask_humid, 'real_humidity']
        
        # Update source tag
        df_hydrated['weather_source'] = 'simulated'
        df_hydrated.loc[mask_temp & mask_humid, 'weather_source'] = 'Open-Meteo (ERA5)'
        
        logger.success(f"Replaced {mask_temp.sum()} temperature values with real data")
        logger.success(f"Replaced {mask_humid.sum()} humidity values with real data")
        
        return df_hydrated
    
    def clean_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean dataset by dropping problematic columns identified by Gemini.
        
        Drops:
        - casualties, displaced (national totals, not per-location)
        - water_level_cm (uncalibrated/synthetic)
        - Original temperature/humidity backups
        """
        logger.info("Cleaning dataset...")
        
        columns_to_drop = [
            'casualties',
            'displaced',
            'water_level_cm',
            'temperature_original',
            'humidity_original',
            'real_temperature',
            'real_humidity',
            'openmeteo_precipitation'  # Keep CHIRPS rainfall instead
        ]
        
        # Drop only columns that exist
        existing_drops = [col for col in columns_to_drop if col in df.columns]
        df_clean = df.drop(columns=existing_drops)
        
        logger.info(f"Dropped columns: {', '.join(existing_drops)}")
        logger.info(f"Remaining columns: {', '.join(df_clean.columns)}")
        
        return df_clean
    
    def generate_report(self, df_original: pd.DataFrame, df_final: pd.DataFrame):
        """Generate hydration report."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("HYDRATION REPORT")
        logger.info("=" * 70)
        
        logger.info(f"\nOriginal dataset: {len(df_original)} records")
        logger.info(f"Final dataset: {len(df_final)} records")
        
        if 'weather_source' in df_final.columns:
            logger.info("\nWeather Data Sources:")
            for source, count in df_final['weather_source'].value_counts().items():
                logger.info(f"  {source}: {count} ({count/len(df_final)*100:.1f}%)")
        
        if 'rainfall_source' in df_final.columns:
            logger.info("\nRainfall Data Sources:")
            for source, count in df_final['rainfall_source'].value_counts().items():
                logger.info(f"  {source}: {count} ({count/len(df_final)*100:.1f}%)")
        
        logger.info("\nTemperature Statistics:")
        logger.info(f"  Mean: {df_final['temperature'].mean():.1f}°C")
        logger.info(f"  Range: {df_final['temperature'].min():.1f} - {df_final['temperature'].max():.1f}°C")
        
        logger.info("\nHumidity Statistics:")
        logger.info(f"  Mean: {df_final['humidity'].mean():.1f}%")
        logger.info(f"  Range: {df_final['humidity'].min():.1f} - {df_final['humidity'].max():.1f}%")
        
        logger.info("\nRainfall Statistics:")
        logger.info(f"  Mean: {df_final['rainfall_mm'].mean():.1f} mm")
        logger.info(f"  Max: {df_final['rainfall_mm'].max():.1f} mm")
        
        logger.info("=" * 70)
    
    def run(self):
        """Main hydration workflow."""
        # Load dataset
        df_original = self.load_dataset()
        if df_original.empty:
            return 1
        
        # Hydrate with real weather
        df_hydrated = self.hydrate_dataset(df_original)
        
        # Clean dataset
        df_clean = self.clean_dataset(df_hydrated)
        
        # Generate report
        self.generate_report(df_original, df_clean)
        
        # Backup original
        backup_file = self.input_file.parent / f"{self.input_file.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df_original.to_csv(backup_file, index=False)
        logger.info(f"\nBacked up original to: {backup_file.name}")
        
        # Save hydrated dataset
        df_clean.to_csv(self.output_file, index=False)
        logger.success(f"Saved hydrated dataset to: {self.output_file}")
        
        logger.info("\n✅ Dataset hydration complete!")
        logger.info("Next step: Phase 3.2 - Feature Engineering")
        
        return 0


def main():
    """Main entry point."""
    input_file = 'data/training/enhanced_flood_events.csv'
    output_file = 'data/training/production_flood_dataset.csv'
    
    logger.info("Open-Meteo Dataset Hydration")
    logger.info("=" * 70)
    logger.info("")
    logger.info("This script will:")
    logger.info("1. Fetch real temperature/humidity from Open-Meteo API (ERA5 data)")
    logger.info("2. Replace simulated weather values")
    logger.info("3. Drop problematic columns (casualties, displaced, water_level)")
    logger.info("4. Create production-ready dataset")
    logger.info("")
    logger.info("Estimated time: 10-15 minutes")
    logger.info("")
    
    hydrator = OpenMeteoHydrator(input_file, output_file)
    return hydrator.run()


if __name__ == '__main__':
    sys.exit(main())
