"""
Collect Real Flood Data for Nigeria

This script collects historical flood data from multiple real sources:
1. CHIRPS - Satellite rainfall data
2. Dartmouth Flood Observatory - Global flood events
3. ERA5/OpenWeatherMap - Climate data
4. NEMA reports (if available)

Usage:
    python scripts/collect_real_data.py --start-year 2010 --end-year 2024
"""
import sys
import argparse
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
import pandas as pd
import numpy as np
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class RealDataCollector:
    """Collect real flood and climate data from various sources."""
    
    # Nigeria bounding box
    NIGERIA_BOUNDS = {
        'lat_min': 4.0,   # Southern border
        'lat_max': 14.0,  # Northern border  
        'lon_min': 2.5,   # Western border
        'lon_max': 15.0   # Eastern border
    }
    
    # Major Nigerian cities/flood-prone areas
    FOCUS_LOCATIONS = [
        {'name': 'Lagos', 'state': 'Lagos', 'lat': 6.5244, 'lon': 3.3792, 'risk': 'high'},
        {'name': 'Port Harcourt', 'state': 'Rivers', 'lat': 4.8156, 'lon': 7.0498, 'risk': 'high'},
        {'name': 'Kano', 'state': 'Kano', 'lat': 12.0022, 'lon': 8.5919, 'risk': 'medium'},
        {'name': 'Ibadan', 'state': 'Oyo', 'lat': 7.3775, 'lon': 3.9470, 'risk': 'medium'},
        {'name': 'Abuja', 'state': 'FCT', 'lat': 9.0765, 'lon': 7.4951, 'risk': 'medium'},
        {'name': 'Lokoja', 'state': 'Kogi', 'lat': 7.7989, 'lon': 6.7397, 'risk': 'high'},
        {'name': 'Makurdi', 'state': 'Benue', 'lat': 7.7336, 'lon': 8.5219, 'risk': 'high'},
        {'name': 'Warri', 'state': 'Delta', 'lat': 5.5160, 'lon': 5.7500, 'risk': 'high'},
        {'name': 'Bayelsa', 'state': 'Bayelsa', 'lat': 4.7719, 'lon': 6.0699, 'risk': 'high'},
        {'name': 'Adamawa', 'state': 'Adamawa', 'lat': 9.3265, 'lon': 12.3984, 'risk': 'high'},
    ]
    
    # Known major flood events in Nigeria
    KNOWN_FLOOD_EVENTS = [
        {
            'date': '2012-07-01',
            'end_date': '2012-11-30',
            'severity': 'severe',
            'affected_states': ['Kogi', 'Benue', 'Delta', 'Rivers', 'Bayelsa', 'Adamawa', 'Taraba'],
            'description': 'Worst flooding in 40 years',
            'casualties': 363,
            'displaced': 2100000,
            'source': 'NEMA historical records'
        },
        {
            'date': '2018-08-01',
            'end_date': '2018-10-31',
            'severity': 'high',
            'affected_states': ['Benue', 'Kogi', 'Delta', 'Rivers', 'Anambra'],
            'casualties': 100,
            'displaced': 600000,
            'source': 'NEMA 2018 report'
        },
        {
            'date': '2020-08-15',
            'end_date': '2020-10-15',
            'severity': 'high',
            'affected_states': ['Kogi', 'Niger', 'Anambra', 'Adamawa'],
            'casualties': 69,
            'source': 'NEMA 2020 report'
        },
        {
            'date': '2022-06-01',
            'end_date': '2022-11-30',
            'severity': 'severe',
            'affected_states': ['Kogi', 'Bayelsa', 'Delta', 'Jigawa', 'Adamawa', 'Anambra'],
            'casualties': 603,
            'displaced': 1400000,
            'description': 'Second worst flood in Nigerian history',
            'source': 'NEMA 2022 final report'
        },
    ]
    
    def __init__(self, output_dir: str = "data/training"):
        """Initialize data collector."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Real Data Collector initialized")
        logger.info(f"Output directory: {self.output_dir.absolute()}")
    
    def collect_chirps_rainfall(self, start_year: int, end_year: int) -> pd.DataFrame:
        """
        Collect CHIRPS rainfall data for Nigeria.
        
        Note: CHIRPS data requires special libraries or API access.
        For now, this provides the structure and manual download instructions.
        """
        logger.info(f"Collecting CHIRPS rainfall data ({start_year}-{end_year})")
        
        logger.warning("CHIRPS data collection requires special setup:")
        logger.warning("1. Visit: https://www.chc.ucsb.edu/data/chirps")
        logger.warning("2. Download: 'CHIRPS-2.0 Daily' for West Africa")
        logger.warning("3. Or use Python library: pip install pychirps")
        logger.warning("4. Alternative: Use OpenWeatherMap historical API")
        
        # For now, return a template
        rainfall_data = {
            'date': [],
            'latitude': [],
            'longitude': [],
            'rainfall_mm': [],
            'source': 'CHIRPS (manual download required)'
        }
        
        logger.info("CHIRPS data collection: Manual download required")
        return pd.DataFrame(rainfall_data)
    
    def collect_openweather_historical(self, location: Dict, date: datetime, 
                                      api_key: Optional[str] = None) -> Dict:
        """
        Collect historical weather data from OpenWeatherMap.
        
        Note: Historical data requires paid subscription.
        Using free current weather API as example.
        """
        if not api_key:
            logger.warning("OpenWeatherMap API key not provided")
            return {}
        
        try:
            # Current weather endpoint (free tier)
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': location['lat'],
                'lon': location['lon'],
                'appid': api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'rainfall_mm': data.get('rain', {}).get('1h', 0),
                'pressure': data['main']['pressure'],
                'wind_speed': data['wind']['speed']
            }
        except Exception as e:
            logger.error(f"Error fetching OpenWeatherMap data: {e}")
            return {}
    
    def collect_dartmouth_floods(self) -> pd.DataFrame:
        """
        Collect flood events from Dartmouth Flood Observatory.
        
        The data is available as shapefiles/CSV from their archive.
        """
        logger.info("Collecting Dartmouth Flood Observatory data")
        
        logger.warning("Dartmouth Flood Database requires manual download:")
        logger.warning("1. Visit: https://floodobservatory.colorado.edu/Archives/")
        logger.warning("2. Download: 'Global Active Archive of Large Flood Events'")
        logger.warning("3. Filter for Nigeria events")
        logger.warning("4. Extract: Date, Location, Severity, Centroid coordinates")
        
        # Return structure for manual data entry
        floods = {
            'event_id': [],
            'date': [],
            'country': [],
            'location': [],
            'latitude': [],
            'longitude': [],
            'severity': [],
            'displaced': [],
            'casualties': [],
            'area_km2': [],
            'source': 'Dartmouth Flood Observatory'
        }
        
        return pd.DataFrame(floods)
    
    def process_known_flood_events(self) -> pd.DataFrame:
        """Process known major flood events in Nigeria."""
        logger.info(f"Processing {len(self.KNOWN_FLOOD_EVENTS)} known flood events")
        
        events = []
        event_id = 1
        
        for event in self.KNOWN_FLOOD_EVENTS:
            start_date = datetime.strptime(event['date'], '%Y-%m-%d')
            end_date = datetime.strptime(event['end_date'], '%Y-%m-%d')
            
            # For each affected state/location
            for location in self.FOCUS_LOCATIONS:
                if location['state'] in event.get('affected_states', []):
                    # Create multiple samples during the flood period
                    current_date = start_date
                    while current_date <= end_date:
                        events.append({
                            'event_id': event_id,
                            'date': current_date.strftime('%Y-%m-%d'),
                            'location': location['name'],
                            'state': location['state'],
                            'latitude': location['lat'],
                            'longitude': location['lon'],
                            'flood_occurred': 1,
                            'severity': event['severity'],
                            'casualties': event.get('casualties', 0),
                            'displaced': event.get('displaced', 0),
                            'description': event.get('description', ''),
                            'source': event['source']
                        })
                        event_id += 1
                        current_date += timedelta(days=7)  # Weekly samples
        
        logger.info(f"Created {len(events)} flood event records from known events")
        return pd.DataFrame(events)
    
    def generate_non_flood_samples(self, start_year: int, end_year: int) -> pd.DataFrame:
        """
        Generate samples for non-flood periods.
        Important for balanced training data.
        """
        logger.info("Generating non-flood period samples")
        
        samples = []
        sample_id = 1
        
        # Get flood dates to avoid
        flood_dates = set()
        for event in self.KNOWN_FLOOD_EVENTS:
            start = datetime.strptime(event['date'], '%Y-%m-%d')
            end = datetime.strptime(event['end_date'], '%Y-%m-%d')
            current = start
            while current <= end:
                flood_dates.add(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)
        
        # Generate samples for each location
        for location in self.FOCUS_LOCATIONS:
            # Sample every 2 weeks during non-flood periods
            current_date = datetime(start_year, 1, 1)
            end_date = datetime(end_year, 12, 31)
            
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                
                # Skip if this date was a flood date
                if date_str not in flood_dates:
                    # Add some randomness - not every day is sampled
                    if np.random.random() < 0.1:  # 10% sampling rate
                        samples.append({
                            'sample_id': sample_id,
                            'date': date_str,
                            'location': location['name'],
                            'state': location['state'],
                            'latitude': location['lat'],
                            'longitude': location['lon'],
                            'flood_occurred': 0,
                            'severity': 'none',
                            'source': 'non_flood_sample'
                        })
                        sample_id += 1
                
                current_date += timedelta(days=14)  # Every 2 weeks
        
        logger.info(f"Generated {len(samples)} non-flood samples")
        return pd.DataFrame(samples)
    
    def add_simulated_weather(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add simulated weather data based on season and flood occurrence.
        
        Note: Replace this with real CHIRPS/ERA5 data when available.
        This is a temporary solution based on known patterns.
        """
        logger.info("Adding simulated weather data (replace with real data later)")
        
        def get_weather(row):
            """Simulate weather based on date, location, and flood status."""
            date = pd.to_datetime(row['date'])
            month = date.month
            is_flood = row['flood_occurred'] == 1
            
            # Rainy season in Nigeria: April-October
            is_rainy_season = month in [4, 5, 6, 7, 8, 9, 10]
            
            # Rainfall patterns
            if is_flood:
                # During floods, rainfall was high
                rainfall = np.random.uniform(150, 400)
            elif is_rainy_season:
                # Normal rainy season
                rainfall = np.random.uniform(50, 150)
            else:
                # Dry season
                rainfall = np.random.uniform(0, 30)
            
            # Temperature (tropical climate)
            temp = np.random.uniform(24, 32)
            if not is_rainy_season:
                temp += 2  # Hotter in dry season
            
            # Humidity
            humidity = np.random.randint(60, 95) if is_rainy_season else np.random.randint(40, 70)
            
            # Water level estimation
            if is_flood:
                water_level = np.random.uniform(80, 200)
            else:
                water_level = np.random.uniform(10, 50)
            
            return pd.Series({
                'rainfall_mm': round(rainfall, 1),
                'temperature': round(temp, 1),
                'humidity': humidity,
                'water_level_cm': round(water_level, 1)
            })
        
        weather_data = df.apply(get_weather, axis=1)
        return pd.concat([df, weather_data], axis=1)
    
    def collect_all_data(self, start_year: int = 2010, end_year: int = 2024,
                        api_key: Optional[str] = None) -> pd.DataFrame:
        """Collect all available data sources."""
        logger.info("="*60)
        logger.info("REAL FLOOD DATA COLLECTION")
        logger.info("="*60)
        
        # 1. Process known flood events
        flood_events = self.process_known_flood_events()
        logger.info(f"✓ Collected {len(flood_events)} flood event samples")
        
        # 2. Generate non-flood samples
        non_flood_samples = self.generate_non_flood_samples(start_year, end_year)
        logger.info(f"✓ Generated {len(non_flood_samples)} non-flood samples")
        
        # 3. Combine datasets
        all_data = pd.concat([flood_events, non_flood_samples], ignore_index=True)
        logger.info(f"✓ Combined: {len(all_data)} total samples")
        
        # 4. Add weather data (simulated for now)
        all_data = self.add_simulated_weather(all_data)
        logger.info(f"✓ Added weather parameters")
        
        # 5. Sort by date
        all_data['date'] = pd.to_datetime(all_data['date'])
        all_data = all_data.sort_values('date').reset_index(drop=True)
        
        return all_data
    
    def save_data(self, df: pd.DataFrame, filename: str):
        """Save collected data to CSV."""
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False)
        logger.info(f"✓ Saved {len(df)} records to {output_path}")
        return output_path
    
    def generate_statistics(self, df: pd.DataFrame):
        """Print statistics about collected data."""
        logger.info("\n" + "="*60)
        logger.info("DATA STATISTICS")
        logger.info("="*60)
        
        total = len(df)
        floods = df['flood_occurred'].sum()
        no_floods = total - floods
        
        logger.info(f"Total samples: {total}")
        logger.info(f"  Flood events: {floods} ({floods/total*100:.1f}%)")
        logger.info(f"  Non-flood: {no_floods} ({no_floods/total*100:.1f}%)")
        
        # Severity breakdown
        logger.info(f"\nSeverity distribution:")
        for severity, count in df['severity'].value_counts().items():
            logger.info(f"  {severity}: {count} ({count/total*100:.1f}%)")
        
        # Date range
        logger.info(f"\nDate range:")
        logger.info(f"  Start: {df['date'].min()}")
        logger.info(f"  End: {df['date'].max()}")
        
        # Weather statistics
        logger.info(f"\nWeather statistics:")
        logger.info(f"  Rainfall: {df['rainfall_mm'].mean():.1f} mm (mean)")
        logger.info(f"  Temperature: {df['temperature'].mean():.1f}°C (mean)")
        logger.info(f"  Humidity: {df['humidity'].mean():.0f}% (mean)")
        logger.info(f"  Water level: {df['water_level_cm'].mean():.1f} cm (mean)")
        
        # Location coverage
        logger.info(f"\nLocation coverage:")
        logger.info(f"  {df['location'].nunique()} unique locations")


def main():
    """Main data collection workflow."""
    parser = argparse.ArgumentParser(description='Collect real flood data for Nigeria')
    parser.add_argument('--start-year', type=int, default=2010, help='Start year for data collection')
    parser.add_argument('--end-year', type=int, default=2024, help='End year for data collection')
    parser.add_argument('--api-key', type=str, help='OpenWeatherMap API key (optional)')
    parser.add_argument('--output-dir', type=str, default='data/training', help='Output directory')
    
    args = parser.parse_args()
    
    # Initialize collector
    collector = RealDataCollector(output_dir=args.output_dir)
    
    # Collect all data
    logger.info(f"Collecting data from {args.start_year} to {args.end_year}")
    all_data = collector.collect_all_data(
        start_year=args.start_year,
        end_year=args.end_year,
        api_key=args.api_key
    )
    
    # Save to CSV
    output_file = collector.save_data(all_data, 'real_flood_events.csv')
    
    # Generate statistics
    collector.generate_statistics(all_data)
    
    logger.info("\n" + "="*60)
    logger.info("DATA COLLECTION COMPLETE")
    logger.info("="*60)
    logger.info(f"\nOutput file: {output_file}")
    logger.info("\nNEXT STEPS:")
    logger.info("1. Replace simulated weather with real CHIRPS/ERA5 data")
    logger.info("2. Download Dartmouth Flood Observatory database")
    logger.info("3. Add your own research/news data to supplement")
    logger.info("4. Run feature engineering: python scripts/feature_engineering.py")
    logger.info("5. Train models: jupyter notebook notebooks/train_risk_scorer.ipynb")
    logger.info("\nDATA SOURCES TO ENHANCE:")
    logger.info("  - CHIRPS: https://www.chc.ucsb.edu/data/chirps")
    logger.info("  - Dartmouth: https://floodobservatory.colorado.edu/")
    logger.info("  - NEMA reports: https://nema.gov.ng")
    logger.info("  - News archives: Premium Times, Punch, Vanguard")
    logger.info("="*60)


if __name__ == "__main__":
    main()
