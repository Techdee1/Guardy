#!/usr/bin/env python3
"""
Download ERA5 climate data (temperature, humidity) for Nigeria.

ERA5: ECMWF Reanalysis v5
- Hourly climate data
- Global coverage, 1950-present
- Variables: 2m temperature, relative humidity, precipitation

Prerequisites:
    1. Register at: https://cds.climate.copernicus.eu/user/register
    2. Get API key from: https://cds.climate.copernicus.eu/user
    3. Create ~/.cdsapirc with:
       url: https://cds.climate.copernicus.eu/api/v2
       key: YOUR_UID:YOUR_API_KEY
    4. Install: pip install cdsapi

Usage:
    python scripts/download_era5.py --start-year 2010 --end-year 2024
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List

import pandas as pd
import numpy as np
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

# Nigerian bounding box [North, West, South, East]
NIGERIA_AREA = [14, 2.5, 4, 15]

# Focus locations
FOCUS_LOCATIONS = [
    {'name': 'Lagos', 'state': 'Lagos', 'lat': 6.5244, 'lon': 3.3792},
    {'name': 'Port Harcourt', 'state': 'Rivers', 'lat': 4.8156, 'lon': 7.0498},
    {'name': 'Kano', 'state': 'Kano', 'lat': 12.0022, 'lon': 8.5919},
    {'name': 'Lokoja', 'state': 'Kogi', 'lat': 7.7989, 'lon': 6.7397},
    {'name': 'Makurdi', 'state': 'Benue', 'lat': 7.7336, 'lon': 8.5219},
    {'name': 'Warri', 'state': 'Delta', 'lat': 5.5160, 'lon': 5.7500},
    {'name': 'Bayelsa', 'state': 'Bayelsa', 'lat': 4.7719, 'lon': 6.0699},
    {'name': 'Adamawa', 'state': 'Adamawa', 'lat': 9.3265, 'lon': 12.3984},
    {'name': 'Ibadan', 'state': 'Oyo', 'lat': 7.3775, 'lon': 3.9470},
    {'name': 'Abuja', 'state': 'FCT', 'lat': 9.0765, 'lon': 7.4951},
]


class ERA5Downloader:
    """Download ERA5 climate data for Nigeria."""
    
    def __init__(self, output_dir: str = "data/external/era5"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if cdsapi is installed
        try:
            import cdsapi
            self.client = cdsapi.Client()
            self.cdsapi_available = True
            logger.success("CDS API client initialized")
        except ImportError:
            self.cdsapi_available = False
            logger.warning("cdsapi not installed")
        except Exception as e:
            self.cdsapi_available = False
            logger.error(f"CDS API setup error: {e}")
    
    def download_era5_data(
        self,
        start_year: int,
        end_year: int,
        variables: List[str] = None
    ) -> Path:
        """
        Download ERA5 data for Nigeria.
        
        Args:
            start_year: Start year
            end_year: End year
            variables: List of variables to download
                - '2m_temperature'
                - '2m_dewpoint_temperature' (for humidity calculation)
                - 'total_precipitation'
        
        Returns:
            Path to downloaded NetCDF file
        """
        if not self.cdsapi_available:
            logger.error("CDS API not available. See setup instructions.")
            return None
        
        if variables is None:
            variables = [
                '2m_temperature',
                '2m_dewpoint_temperature',  # For relative humidity
                'total_precipitation'
            ]
        
        # Generate year list
        years = [str(y) for y in range(start_year, end_year + 1)]
        months = [f'{m:02d}' for m in range(1, 13)]
        days = [f'{d:02d}' for d in range(1, 32)]
        
        output_file = self.output_dir / f'era5_nigeria_{start_year}_{end_year}.nc'
        
        if output_file.exists():
            logger.info(f"File already exists: {output_file}")
            return output_file
        
        logger.info(f"Downloading ERA5 data for {start_year}-{end_year}")
        logger.info(f"Variables: {', '.join(variables)}")
        logger.info("This may take several minutes...")
        
        try:
            import cdsapi
            
            self.client.retrieve(
                'reanalysis-era5-single-levels',
                {
                    'product_type': 'reanalysis',
                    'variable': variables,
                    'year': years,
                    'month': months,
                    'day': days,
                    'time': '12:00',  # Noon UTC (peak temperature)
                    'area': NIGERIA_AREA,  # [North, West, South, East]
                    'format': 'netcdf',
                },
                str(output_file)
            )
            
            logger.success(f"Downloaded: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
    
    def extract_for_locations(
        self,
        netcdf_file: Path,
        locations: List[dict]
    ) -> pd.DataFrame:
        """Extract climate data for specific locations from NetCDF."""
        try:
            import xarray as xr
            
            logger.info(f"Opening NetCDF: {netcdf_file}")
            ds = xr.open_dataset(netcdf_file)
            
            all_data = []
            
            for loc in locations:
                logger.info(f"Extracting data for {loc['name']}")
                
                # Select nearest grid point
                data_point = ds.sel(
                    latitude=loc['lat'],
                    longitude=loc['lon'],
                    method='nearest'
                )
                
                # Extract variables
                dates = pd.to_datetime(data_point['time'].values)
                
                # Temperature (convert from Kelvin to Celsius)
                if 't2m' in data_point:
                    temperature = data_point['t2m'].values - 273.15
                else:
                    temperature = np.full(len(dates), np.nan)
                
                # Dewpoint (for humidity calculation)
                if 'd2m' in data_point:
                    dewpoint = data_point['d2m'].values - 273.15
                    # Calculate relative humidity
                    # RH = 100 * exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T))
                    humidity = 100 * np.exp((17.625 * dewpoint) / (243.04 + dewpoint)) / \
                               np.exp((17.625 * temperature) / (243.04 + temperature))
                else:
                    humidity = np.full(len(dates), np.nan)
                
                # Precipitation (convert from m to mm)
                if 'tp' in data_point:
                    precipitation = data_point['tp'].values * 1000
                else:
                    precipitation = np.full(len(dates), np.nan)
                
                # Create records
                for i, date in enumerate(dates):
                    all_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'location': loc['name'],
                        'state': loc['state'],
                        'latitude': loc['lat'],
                        'longitude': loc['lon'],
                        'temperature': float(temperature[i]),
                        'humidity': float(humidity[i]),
                        'rainfall_mm': float(precipitation[i]),
                        'source': 'ERA5'
                    })
            
            ds.close()
            
            return pd.DataFrame(all_data)
            
        except ImportError:
            logger.error("xarray not installed: pip install xarray netCDF4")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return pd.DataFrame()
    
    def download_and_extract(
        self,
        start_year: int,
        end_year: int,
        locations: List[dict] = FOCUS_LOCATIONS
    ) -> pd.DataFrame:
        """Download ERA5 data and extract for locations."""
        
        # Download NetCDF
        netcdf_file = self.download_era5_data(start_year, end_year)
        
        if netcdf_file is None or not netcdf_file.exists():
            logger.error("Download failed")
            return pd.DataFrame()
        
        # Extract for locations
        df = self.extract_for_locations(netcdf_file, locations)
        
        return df


def show_setup_instructions():
    """Display setup instructions for ERA5 download."""
    logger.info("=" * 70)
    logger.info("ERA5 DATA DOWNLOAD SETUP")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Step 1: Register for CDS Account")
    logger.info("  Visit: https://cds.climate.copernicus.eu/user/register")
    logger.info("  - Create free account")
    logger.info("  - Verify email")
    logger.info("")
    logger.info("Step 2: Get API Key")
    logger.info("  Visit: https://cds.climate.copernicus.eu/user")
    logger.info("  - Login to your account")
    logger.info("  - Copy your UID and API key")
    logger.info("")
    logger.info("Step 3: Configure API")
    logger.info("  Create file: ~/.cdsapirc")
    logger.info("  Content:")
    logger.info("    url: https://cds.climate.copernicus.eu/api/v2")
    logger.info("    key: YOUR_UID:YOUR_API_KEY")
    logger.info("")
    logger.info("  OR set environment variables:")
    logger.info("    export CDSAPI_URL=https://cds.climate.copernicus.eu/api/v2")
    logger.info("    export CDSAPI_KEY=YOUR_UID:YOUR_API_KEY")
    logger.info("")
    logger.info("Step 4: Accept Terms & Conditions")
    logger.info("  Visit: https://cds.climate.copernicus.eu/cdsapp/#!/terms/licence-to-use-copernicus-products")
    logger.info("  - Read and accept the license")
    logger.info("")
    logger.info("Step 5: Install Python Package")
    logger.info("  pip install cdsapi xarray netCDF4")
    logger.info("")
    logger.info("Step 6: Run Download")
    logger.info("  python scripts/download_era5.py --start-year 2010 --end-year 2024")
    logger.info("")
    logger.info("=" * 70)
    logger.info("")
    logger.info("NOTE: First download may take 10-30 minutes depending on data size.")
    logger.info("Subsequent runs will use cached data.")
    logger.info("")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download ERA5 climate data for Nigeria"
    )
    parser.add_argument(
        '--start-year',
        type=int,
        help='Start year (e.g., 2010)'
    )
    parser.add_argument(
        '--end-year',
        type=int,
        help='End year (e.g., 2024)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/external/era5_nigeria.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Show setup instructions'
    )
    
    args = parser.parse_args()
    
    # Show setup instructions if requested
    if args.setup or not (args.start_year and args.end_year):
        show_setup_instructions()
        if not args.setup:
            logger.error("Missing required arguments: --start-year and --end-year")
        return 1 if not args.setup else 0
    
    # Validate years
    if args.start_year < 1950:
        logger.error("ERA5 data only available from 1950 onwards")
        return 1
    
    if args.end_year > datetime.now().year:
        logger.error(f"End year cannot be in the future")
        return 1
    
    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Download data
    downloader = ERA5Downloader()
    
    if not downloader.cdsapi_available:
        logger.error("CDS API not configured")
        show_setup_instructions()
        return 1
    
    logger.info("Starting ERA5 data download...")
    logger.info(f"Date range: {args.start_year} to {args.end_year}")
    logger.info(f"Output file: {output_path}")
    
    df = downloader.download_and_extract(
        args.start_year,
        args.end_year,
        FOCUS_LOCATIONS
    )
    
    if df.empty:
        logger.error("No data downloaded")
        return 1
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    logger.success(f"Saved {len(df)} records to {output_path}")
    logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
    logger.info(f"Locations: {df['location'].nunique()}")
    logger.info(f"Temperature: {df['temperature'].mean():.1f}°C (mean)")
    logger.info(f"Humidity: {df['humidity'].mean():.1f}% (mean)")
    logger.info(f"Rainfall: {df['rainfall_mm'].mean():.1f} mm (mean)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
