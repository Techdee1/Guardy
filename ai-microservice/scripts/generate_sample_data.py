"""
Generate Sample Training Data

Creates synthetic flood events and sensor readings for testing model training
when real historical data is not yet available.

Usage:
    python scripts/generate_sample_data.py [--events 100] [--readings 10000]
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class SampleDataGenerator:
    """Generate synthetic training data for ML models."""
    
    # Lagos region coordinates
    LAGOS_COORDS = {
        'lat_min': 6.4, 'lat_max': 6.7,
        'lon_min': 3.2, 'lon_max': 3.6
    }
    
    # Nigerian cities for variety
    LOCATIONS = [
        {'name': 'Lagos Island', 'lat': 6.4541, 'lon': 3.3947, 'flood_prone': 0.8},
        {'name': 'Victoria Island', 'lat': 6.4281, 'lon': 3.4219, 'flood_prone': 0.7},
        {'name': 'Ikeja', 'lat': 6.6018, 'lon': 3.3515, 'flood_prone': 0.5},
        {'name': 'Lekki', 'lat': 6.4698, 'lon': 3.5852, 'flood_prone': 0.6},
        {'name': 'Ikorodu', 'lat': 6.6194, 'lon': 3.5098, 'flood_prone': 0.9},
        {'name': 'Port Harcourt', 'lat': 4.8156, 'lon': 7.0498, 'flood_prone': 0.8},
        {'name': 'Abuja', 'lat': 9.0765, 'lon': 7.3986, 'flood_prone': 0.4},
        {'name': 'Kano', 'lat': 12.0022, 'lon': 8.5919, 'flood_prone': 0.3},
    ]
    
    def __init__(self, output_dir: str = "data/training"):
        """Initialize sample data generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized SampleDataGenerator")
        logger.info(f"Output directory: {self.output_dir.absolute()}")
    
    def generate_flood_events(self, n_events: int = 100) -> pd.DataFrame:
        """
        Generate synthetic flood events.
        
        Args:
            n_events: Number of flood events to generate
            
        Returns:
            DataFrame with synthetic flood events
        """
        logger.info(f"Generating {n_events} synthetic flood events...")
        
        events = []
        start_date = datetime.now() - timedelta(days=730)  # 2 years ago
        
        for i in range(n_events):
            # Select random location (weighted by flood_prone score)
            location = np.random.choice(
                self.LOCATIONS,
                p=[loc['flood_prone'] / sum(l['flood_prone'] for l in self.LOCATIONS) 
                   for loc in self.LOCATIONS]
            )
            
            # Random date (more floods during rainy season: April-October)
            days_offset = np.random.randint(0, 730)
            event_date = start_date + timedelta(days=days_offset)
            month = event_date.month
            
            # Higher rainfall during rainy season
            is_rainy_season = 4 <= month <= 10
            base_rainfall = 150 if is_rainy_season else 80
            rainfall_mm = np.random.normal(base_rainfall, 50)
            rainfall_mm = max(50, min(400, rainfall_mm))  # Clamp to realistic range
            
            # Water level correlates with rainfall
            water_level_cm = rainfall_mm * 0.5 + np.random.normal(0, 15)
            water_level_cm = max(30, min(200, water_level_cm))
            
            # Severity based on water level
            if water_level_cm > 120:
                severity = 'critical'
            elif water_level_cm > 80:
                severity = 'high'
            elif water_level_cm > 50:
                severity = 'medium'
            else:
                severity = 'low'
            
            # Affected population scales with severity
            severity_multiplier = {'low': 100, 'medium': 500, 'high': 2000, 'critical': 5000}
            affected_pop = int(np.random.normal(severity_multiplier[severity], 500))
            
            events.append({
                'id': i + 1,
                'latitude': location['lat'] + np.random.normal(0, 0.01),
                'longitude': location['lon'] + np.random.normal(0, 0.01),
                'location_name': location['name'],
                'severity': severity,
                'description': f"Flooding in {location['name']} due to heavy rainfall",
                'rainfall_mm': round(rainfall_mm, 2),
                'water_level_cm': round(water_level_cm, 2),
                'affected_population': max(10, affected_pop),
                'occurred_at': event_date.isoformat(),
                'reported_at': (event_date + timedelta(hours=np.random.randint(1, 6))).isoformat(),
                'created_at': (event_date + timedelta(hours=np.random.randint(1, 12))).isoformat()
            })
        
        df = pd.DataFrame(events)
        logger.success(f"Generated {len(df)} flood events")
        logger.info(f"Severity distribution: {df['severity'].value_counts().to_dict()}")
        
        return df
    
    def generate_sensor_readings(self, n_readings: int = 10000) -> pd.DataFrame:
        """
        Generate synthetic sensor readings.
        
        Args:
            n_readings: Number of sensor readings to generate
            
        Returns:
            DataFrame with synthetic sensor readings
        """
        logger.info(f"Generating {n_readings} synthetic sensor readings...")
        
        # Create virtual sensors at different locations
        n_sensors = min(10, n_readings // 1000 + 1)
        sensors = []
        for i in range(n_sensors):
            location = self.LOCATIONS[i % len(self.LOCATIONS)]
            sensors.append({
                'device_id': f"ESP32_{i+1:03d}",
                'latitude': location['lat'] + np.random.normal(0, 0.005),
                'longitude': location['lon'] + np.random.normal(0, 0.005),
                'location_name': location['name'],
                'flood_prone': location['flood_prone']
            })
        
        readings = []
        start_date = datetime.now() - timedelta(days=365)
        
        for sensor in sensors:
            # Each sensor generates readings every 10 minutes
            n_sensor_readings = n_readings // n_sensors
            
            for i in range(n_sensor_readings):
                # Timestamp with 10-minute intervals
                timestamp = start_date + timedelta(minutes=i * 10)
                month = timestamp.month
                is_rainy_season = 4 <= month <= 10
                
                # Simulate water level patterns
                # Base level with seasonal variation
                base_level = 30 if is_rainy_season else 20
                
                # Add daily cycle (higher during evening)
                hour_effect = 10 * np.sin((timestamp.hour - 6) * np.pi / 12)
                
                # Random rainfall events (more during rainy season)
                rainfall_event = np.random.random() < (0.3 if is_rainy_season else 0.1)
                rainfall_effect = np.random.uniform(20, 80) if rainfall_event else 0
                
                # Flood-prone locations have higher baseline
                location_effect = sensor['flood_prone'] * 15
                
                water_level = base_level + hour_effect + rainfall_effect + location_effect
                water_level += np.random.normal(0, 3)  # Sensor noise
                water_level = max(0, min(150, water_level))
                
                # Temperature (tropical climate)
                temperature = 27 + 5 * np.sin((timestamp.month - 3) * np.pi / 6)
                temperature += np.random.normal(0, 2)
                
                # Humidity (higher during rainy season)
                humidity = 75 if is_rainy_season else 60
                humidity += np.random.normal(0, 10)
                humidity = max(30, min(100, int(humidity)))
                
                # Battery voltage (3.3-4.2V, degrades over time)
                days_since_start = (timestamp - start_date).days
                battery_voltage = 4.2 - (days_since_start / 365) * 0.5
                battery_voltage += np.random.normal(0, 0.1)
                battery_voltage = max(2.8, min(4.2, battery_voltage))
                
                # Signal strength
                signal_strength = np.random.randint(-80, -40)
                
                readings.append({
                    'id': len(readings) + 1,
                    'device_id': sensor['device_id'],
                    'latitude': sensor['latitude'],
                    'longitude': sensor['longitude'],
                    'location_name': sensor['location_name'],
                    'water_level_cm': round(water_level, 2),
                    'temperature': round(temperature, 2),
                    'humidity': humidity,
                    'battery_voltage': round(battery_voltage, 2),
                    'signal_strength': signal_strength,
                    'timestamp': timestamp.isoformat()
                })
        
        df = pd.DataFrame(readings)
        logger.success(f"Generated {len(df)} sensor readings from {n_sensors} sensors")
        logger.info(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        return df
    
    def generate_sensor_alerts(self, sensor_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate sensor alerts based on sensor readings.
        
        Args:
            sensor_df: Sensor readings DataFrame
            
        Returns:
            DataFrame with synthetic sensor alerts
        """
        logger.info("Generating sensor alerts from readings...")
        
        alerts = []
        alert_id = 1
        
        # Group by device
        for device_id, group in sensor_df.groupby('device_id'):
            # Find high water level events
            high_water = group[group['water_level_cm'] > 80]
            
            for _, row in high_water.iterrows():
                alerts.append({
                    'id': alert_id,
                    'device_id': device_id,
                    'latitude': row['latitude'],
                    'longitude': row['longitude'],
                    'alert_type': 'high_water_level',
                    'severity': 'high' if row['water_level_cm'] > 100 else 'medium',
                    'threshold_value': 80.0,
                    'actual_value': row['water_level_cm'],
                    'message': f"Water level exceeded threshold: {row['water_level_cm']:.1f}cm",
                    'status': 'resolved' if np.random.random() > 0.3 else 'active',
                    'triggered_at': row['timestamp'],
                    'resolved_at': (pd.to_datetime(row['timestamp']) + 
                                   timedelta(hours=np.random.randint(2, 12))).isoformat() 
                                   if np.random.random() > 0.3 else None
                })
                alert_id += 1
            
            # Low battery alerts
            low_battery = group[group['battery_voltage'] < 3.0]
            if len(low_battery) > 0:
                row = low_battery.iloc[0]
                alerts.append({
                    'id': alert_id,
                    'device_id': device_id,
                    'latitude': row['latitude'],
                    'longitude': row['longitude'],
                    'alert_type': 'low_battery',
                    'severity': 'low',
                    'threshold_value': 3.0,
                    'actual_value': row['battery_voltage'],
                    'message': f"Battery voltage low: {row['battery_voltage']:.2f}V",
                    'status': 'active',
                    'triggered_at': row['timestamp'],
                    'resolved_at': None
                })
                alert_id += 1
        
        df = pd.DataFrame(alerts)
        logger.success(f"Generated {len(df)} sensor alerts")
        
        return df
    
    def run(self, n_events: int = 100, n_readings: int = 10000):
        """Execute sample data generation pipeline."""
        logger.info("Starting sample data generation...")
        
        # Generate data
        flood_df = self.generate_flood_events(n_events)
        sensor_df = self.generate_sensor_readings(n_readings)
        alert_df = self.generate_sensor_alerts(sensor_df)
        
        # Export to CSV
        flood_path = self.output_dir / "flood_events.csv"
        sensor_path = self.output_dir / "sensor_readings.csv"
        alert_path = self.output_dir / "sensor_alerts.csv"
        
        flood_df.to_csv(flood_path, index=False)
        sensor_df.to_csv(sensor_path, index=False)
        alert_df.to_csv(alert_path, index=False)
        
        logger.success(f"Exported flood events to {flood_path}")
        logger.success(f"Exported sensor readings to {sensor_path}")
        logger.success(f"Exported sensor alerts to {alert_path}")
        
        # Generate summary
        print("\n" + "="*60)
        print("Sample Data Generation Summary")
        print("="*60)
        print(f"✅ Flood Events: {len(flood_df)} records")
        print(f"   - Date Range: {flood_df['occurred_at'].min()} to {flood_df['occurred_at'].max()}")
        print(f"   - Severity: {flood_df['severity'].value_counts().to_dict()}")
        print()
        print(f"✅ Sensor Readings: {len(sensor_df)} records")
        print(f"   - Devices: {sensor_df['device_id'].nunique()}")
        print(f"   - Date Range: {sensor_df['timestamp'].min()} to {sensor_df['timestamp'].max()}")
        print()
        print(f"✅ Sensor Alerts: {len(alert_df)} records")
        print(f"   - Alert Types: {alert_df['alert_type'].value_counts().to_dict()}")
        print("="*60)
        print()
        logger.success("✅ Sample data generation completed successfully!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic training data for model testing"
    )
    parser.add_argument(
        "--events",
        type=int,
        default=100,
        help="Number of flood events to generate (default: 100)"
    )
    parser.add_argument(
        "--readings",
        type=int,
        default=10000,
        help="Number of sensor readings to generate (default: 10000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/training",
        help="Output directory for CSV files (default: data/training)"
    )
    
    args = parser.parse_args()
    
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Run generator
    generator = SampleDataGenerator(output_dir=args.output)
    generator.run(n_events=args.events, n_readings=args.readings)


if __name__ == "__main__":
    main()
