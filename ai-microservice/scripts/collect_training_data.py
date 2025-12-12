"""
Data Collection Script for ML Model Training

This script fetches historical data from PostgreSQL and exports it to CSV files
for training flood risk prediction and nowcasting models.

Usage:
    python scripts/collect_training_data.py [--days 365] [--output data/training]
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine, text
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings


class DataCollector:
    """Collect and export training data from PostgreSQL."""
    
    def __init__(self, days: int = 365, output_dir: str = "data/training"):
        """
        Initialize data collector.
        
        Args:
            days: Number of days of historical data to collect
            output_dir: Directory to save CSV files
        """
        self.days = days
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create database connection
        self.engine = create_engine(
            f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@"
            f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
        
        logger.info(f"Initialized DataCollector (last {days} days)")
        logger.info(f"Output directory: {self.output_dir.absolute()}")
    
    def collect_flood_events(self) -> pd.DataFrame:
        """
        Collect historical flood events for model training.
        
        Returns:
            DataFrame with flood event data
        """
        logger.info("Collecting flood events...")
        
        cutoff_date = datetime.now() - timedelta(days=self.days)
        
        query = text("""
            SELECT 
                id,
                latitude,
                longitude,
                location_name,
                severity,
                description,
                rainfall_mm,
                water_level_cm,
                affected_population,
                occurred_at,
                reported_at,
                created_at
            FROM flood_events
            WHERE occurred_at >= :cutoff_date
            ORDER BY occurred_at DESC
        """)
        
        try:
            df = pd.read_sql(query, self.engine, params={'cutoff_date': cutoff_date})
            logger.success(f"Collected {len(df)} flood events")
            
            if len(df) == 0:
                logger.warning("No flood events found in database!")
                logger.info("💡 This is expected for new installations.")
                logger.info("💡 You can import sample data or wait for real events.")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to collect flood events: {e}")
            logger.warning("Table might not exist yet - creating empty DataFrame")
            return pd.DataFrame()
    
    def collect_sensor_readings(self) -> pd.DataFrame:
        """
        Collect sensor readings for time-series analysis.
        
        Returns:
            DataFrame with sensor reading data
        """
        logger.info("Collecting sensor readings...")
        
        cutoff_date = datetime.now() - timedelta(days=self.days)
        
        query = text("""
            SELECT 
                sr.id,
                sr.device_id,
                sd.latitude,
                sd.longitude,
                sd.location_name,
                sr.water_level_cm,
                sr.temperature,
                sr.humidity,
                sr.battery_voltage,
                sr.signal_strength,
                sr.timestamp
            FROM sensor_readings sr
            JOIN sensor_devices sd ON sr.device_id = sd.device_id
            WHERE sr.timestamp >= :cutoff_date
            ORDER BY sr.device_id, sr.timestamp ASC
        """)
        
        try:
            df = pd.read_sql(query, self.engine, params={'cutoff_date': cutoff_date})
            logger.success(f"Collected {len(df)} sensor readings from {df['device_id'].nunique()} devices")
            
            if len(df) == 0:
                logger.warning("No sensor readings found in database!")
                logger.info("💡 This is expected if sensors haven't been deployed yet.")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to collect sensor readings: {e}")
            logger.warning("Table might not exist yet - creating empty DataFrame")
            return pd.DataFrame()
    
    def collect_sensor_alerts(self) -> pd.DataFrame:
        """
        Collect sensor alerts for anomaly detection training.
        
        Returns:
            DataFrame with sensor alert data
        """
        logger.info("Collecting sensor alerts...")
        
        cutoff_date = datetime.now() - timedelta(days=self.days)
        
        query = text("""
            SELECT 
                sa.id,
                sa.device_id,
                sd.latitude,
                sd.longitude,
                sa.alert_type,
                sa.severity,
                sa.threshold_value,
                sa.actual_value,
                sa.message,
                sa.status,
                sa.triggered_at,
                sa.resolved_at
            FROM sensor_alerts sa
            JOIN sensor_devices sd ON sa.device_id = sd.device_id
            WHERE sa.triggered_at >= :cutoff_date
            ORDER BY sa.triggered_at DESC
        """)
        
        try:
            df = pd.read_sql(query, self.engine, params={'cutoff_date': cutoff_date})
            logger.success(f"Collected {len(df)} sensor alerts")
            
            if len(df) == 0:
                logger.info("No sensor alerts found - this is normal for new systems")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to collect sensor alerts: {e}")
            logger.warning("Table might not exist yet - creating empty DataFrame")
            return pd.DataFrame()
    
    def clean_data(self, df: pd.DataFrame, name: str) -> pd.DataFrame:
        """
        Clean and validate collected data.
        
        Args:
            df: DataFrame to clean
            name: Dataset name for logging
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            logger.warning(f"Skipping cleaning for empty {name} dataset")
            return df
        
        logger.info(f"Cleaning {name} data...")
        
        initial_rows = len(df)
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Remove rows with critical missing values
        if 'latitude' in df.columns and 'longitude' in df.columns:
            df = df.dropna(subset=['latitude', 'longitude'])
        
        if 'water_level_cm' in df.columns:
            # Remove physically impossible values
            df = df[df['water_level_cm'] >= 0]
            df = df[df['water_level_cm'] <= 500]  # Max 5 meters
        
        if 'temperature' in df.columns:
            df = df[(df['temperature'] >= -10) & (df['temperature'] <= 60)]
        
        if 'humidity' in df.columns:
            df = df[(df['humidity'] >= 0) & (df['humidity'] <= 100)]
        
        removed_rows = initial_rows - len(df)
        if removed_rows > 0:
            logger.info(f"Removed {removed_rows} invalid rows ({removed_rows/initial_rows*100:.1f}%)")
        
        logger.success(f"Cleaned {name} data: {len(df)} valid rows")
        return df
    
    def export_to_csv(self, df: pd.DataFrame, filename: str):
        """
        Export DataFrame to CSV file.
        
        Args:
            df: DataFrame to export
            filename: Output filename (without path)
        """
        if df.empty:
            logger.warning(f"Skipping export of empty dataset: {filename}")
            return
        
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False)
        logger.success(f"Exported {len(df)} rows to {output_path}")
        
        # Show basic statistics
        logger.info(f"Dataset shape: {df.shape}")
        logger.info(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    def generate_statistics_report(self, flood_df: pd.DataFrame, 
                                   sensor_df: pd.DataFrame,
                                   alert_df: pd.DataFrame):
        """
        Generate and save statistics report.
        
        Args:
            flood_df: Flood events DataFrame
            sensor_df: Sensor readings DataFrame  
            alert_df: Sensor alerts DataFrame
        """
        logger.info("Generating statistics report...")
        
        report = []
        report.append("="*60)
        report.append("Training Data Collection Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Time Range: Last {self.days} days")
        report.append("="*60)
        report.append("")
        
        # Flood Events Statistics
        report.append("📊 FLOOD EVENTS")
        report.append("-" * 40)
        if not flood_df.empty:
            report.append(f"Total Events: {len(flood_df)}")
            report.append(f"Date Range: {flood_df['occurred_at'].min()} to {flood_df['occurred_at'].max()}")
            if 'severity' in flood_df.columns:
                report.append(f"Severity Distribution:")
                for severity, count in flood_df['severity'].value_counts().items():
                    report.append(f"  - {severity}: {count}")
            if 'rainfall_mm' in flood_df.columns:
                report.append(f"Rainfall (mm): {flood_df['rainfall_mm'].describe().to_string()}")
        else:
            report.append("No flood events data available")
        report.append("")
        
        # Sensor Readings Statistics
        report.append("📡 SENSOR READINGS")
        report.append("-" * 40)
        if not sensor_df.empty:
            report.append(f"Total Readings: {len(sensor_df)}")
            report.append(f"Unique Devices: {sensor_df['device_id'].nunique()}")
            report.append(f"Date Range: {sensor_df['timestamp'].min()} to {sensor_df['timestamp'].max()}")
            if 'water_level_cm' in sensor_df.columns:
                report.append(f"Water Level (cm): {sensor_df['water_level_cm'].describe().to_string()}")
        else:
            report.append("No sensor readings data available")
        report.append("")
        
        # Sensor Alerts Statistics
        report.append("🚨 SENSOR ALERTS")
        report.append("-" * 40)
        if not alert_df.empty:
            report.append(f"Total Alerts: {len(alert_df)}")
            if 'alert_type' in alert_df.columns:
                report.append(f"Alert Type Distribution:")
                for alert_type, count in alert_df['alert_type'].value_counts().items():
                    report.append(f"  - {alert_type}: {count}")
        else:
            report.append("No sensor alerts data available")
        report.append("")
        
        report.append("="*60)
        
        # Save report
        report_text = "\n".join(report)
        report_path = self.output_dir / "collection_report.txt"
        report_path.write_text(report_text)
        
        # Print to console
        print("\n" + report_text)
        logger.success(f"Report saved to {report_path}")
    
    def run(self):
        """Execute the complete data collection pipeline."""
        logger.info("Starting data collection pipeline...")
        
        try:
            # Collect data
            flood_df = self.collect_flood_events()
            sensor_df = self.collect_sensor_readings()
            alert_df = self.collect_sensor_alerts()
            
            # Clean data
            flood_df = self.clean_data(flood_df, "flood_events")
            sensor_df = self.clean_data(sensor_df, "sensor_readings")
            alert_df = self.clean_data(alert_df, "sensor_alerts")
            
            # Export to CSV
            self.export_to_csv(flood_df, "flood_events.csv")
            self.export_to_csv(sensor_df, "sensor_readings.csv")
            self.export_to_csv(alert_df, "sensor_alerts.csv")
            
            # Generate report
            self.generate_statistics_report(flood_df, sensor_df, alert_df)
            
            logger.success("✅ Data collection pipeline completed successfully!")
            
            if flood_df.empty and sensor_df.empty:
                logger.warning("")
                logger.warning("⚠️  No training data found in database!")
                logger.warning("📝 Next steps:")
                logger.warning("   1. Deploy ESP32 sensors and collect real data")
                logger.warning("   2. Import historical flood data from NEMA/other sources")
                logger.warning("   3. Use sample/synthetic data for initial model testing")
            
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Collect training data from PostgreSQL database"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Number of days of historical data to collect (default: 365)"
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
    
    # Run collector
    collector = DataCollector(days=args.days, output_dir=args.output)
    collector.run()


if __name__ == "__main__":
    main()
